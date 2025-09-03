"""
Performance Insight Agent using LangChain
Single responsibility: Generate actionable insights from metrics
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

import google.generativeai as genai

from src.models.schemas import InsightReport, CampaignMetrics
from src.core.credit_manager import get_credit_manager
from src.storage.db_manager import DatabaseManager

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class PerformanceInsightAgent:
    """Generates performance insights using LLM"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.credit_manager = get_credit_manager()
        self.db_manager = DatabaseManager()
        
        # Debug logging
        if self.api_key:
            logger.info(f"Gemini API key loaded: {self.api_key[:10]}...")  # Show first 10 chars
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            logger.warning("No API key, using template insights")
            self.model = None

    def analyze_performance(self, metrics: List[CampaignMetrics]) -> InsightReport:
        """Analyze campaign performance and generate insights"""
        
        # Calculate aggregate statistics
        stats = self._calculate_statistics(metrics)
        
        # Generate insights
        if self.model:
            logger.info("Using Gemini API for insights")
            insights = self._generate_llm_insights(stats, metrics)
        else:
            logger.info("Using template insights (no API key)")
            insights = self._generate_template_insights(stats)
        
        return insights


    
    def _calculate_statistics(self, metrics: List[CampaignMetrics]) -> Dict:
        """Calculate aggregate statistics"""
        if not metrics:
            return {}
        
        total_spend = sum(m.daily_spend for m in metrics)
        total_revenue = sum(m.revenue for m in metrics)
        avg_ctr = sum(m.ctr for m in metrics) / len(metrics)
        avg_roas = sum(m.roas for m in metrics) / len(metrics)
        
        # Platform breakdown
        platform_stats = {}
        for platform in ['google_ads', 'meta', 'linkedin']:
            platform_metrics = [m for m in metrics if m.platform == platform]
            if platform_metrics:
                platform_stats[platform] = {
                    'spend': sum(m.daily_spend for m in platform_metrics),
                    'revenue': sum(m.revenue for m in platform_metrics),
                    'avg_ctr': sum(m.ctr for m in platform_metrics) / len(platform_metrics),
                    'campaigns': len(platform_metrics)
                }
        
        return {
            'total_spend': total_spend,
            'total_revenue': total_revenue,
            'overall_roas': total_revenue / total_spend if total_spend > 0 else 0,
            'avg_ctr': avg_ctr,
            'avg_roas': avg_roas,
            'platform_breakdown': platform_stats,
            'total_campaigns': len(metrics)
        }
    

    def _generate_llm_insights(self, stats: Dict, metrics: List[CampaignMetrics]) -> InsightReport:
        """Generate insights using Gemini"""
        
        # Check rate limit
        self.credit_manager.track_request_start()
        
        prompt = f"""Analyze these B2B campaign metrics and provide actionable insights:

    Statistics:
    {json.dumps(stats, indent=2)}

    Requirements:
    1. Identify the best and worst performing platforms
    2. Find patterns in high-performing campaigns
    3. Suggest 3 specific optimization actions
    4. Note any concerning trends

    Keep insights specific to B2B tech companies with long sales cycles.

    Return ONLY a valid JSON object with these exact keys (no markdown, no extra text):
    {{
    "summary": "one line summary of performance",
    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"],
    "platform_insights": {{"google_ads": "insight", "meta": "insight", "linkedin": "insight"}},
    "patterns": ["pattern 1", "pattern 2"]
    }}"""
        
        try:
            response = self.model.generate_content(prompt)
            
            # Check if response exists and has text
            if not response or not response.text:
                logger.error("Empty response from Gemini API")
                self.credit_manager.track_usage(component='insight_agent', success=False)
                return self._generate_template_insights(stats)
            
            # Debug: log the raw response
            logger.debug(f"Gemini raw response: {response.text[:500]}")
            
            # Clean response text (remove markdown formatting if present)
            response_text = response.text.strip()
            
            # Remove markdown code blocks
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.rfind('```')
                if end > start:
                    response_text = response_text[start:end].strip()
            elif '```' in response_text:
                # Generic code block
                start = response_text.find('```') + 3
                end = response_text.rfind('```')
                if end > start:
                    response_text = response_text[start:end].strip()
            
            # Remove any leading/trailing whitespace or newlines
            response_text = response_text.strip()
            
            # Parse JSON
            try:
                insights_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                logger.error(f"Cleaned response was: {response_text[:500]}")
                
                # Try to extract JSON from the response if it's embedded
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        insights_data = json.loads(json_match.group())
                        logger.info("Successfully extracted JSON from response")
                    except:
                        logger.error("Failed to extract valid JSON from response")
                        self.credit_manager.track_usage(component='insight_agent', success=False)
                        return self._generate_template_insights(stats)
                else:
                    self.credit_manager.track_usage(component='insight_agent', success=False)
                    return self._generate_template_insights(stats)
            
            # Track usage
            self.credit_manager.track_usage(
                input_tokens=len(prompt.split()) * 2,
                output_tokens=len(response.text.split()) * 2,
                component='insight_agent',
                success=True
            )
            
            # Validate required fields exist
            if not insights_data.get('summary'):
                insights_data['summary'] = f"Analyzed {stats.get('total_campaigns', 0)} campaigns"
            if not insights_data.get('recommendations'):
                insights_data['recommendations'] = []
            if not insights_data.get('patterns'):
                insights_data['patterns'] = []
            if not insights_data.get('platform_insights'):
                insights_data['platform_insights'] = {}
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.credit_manager.track_usage(component='insight_agent', success=False)
            return self._generate_template_insights(stats)
        
        # Create InsightReport
        return InsightReport(
            report_id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            period_start=min(m.timestamp for m in metrics) if metrics else datetime.now(),
            period_end=max(m.timestamp for m in metrics) if metrics else datetime.now(),
            summary=insights_data.get('summary', 'Performance analysis complete'),
            key_metrics=stats,
            trends=[],
            recommendations=insights_data.get('recommendations', []),
            action_items=[],
            platform_insights=insights_data.get('platform_insights', {}),
            patterns=insights_data.get('patterns', []),
            anomalies=[]
        )




    def _generate_template_insights(self, stats: Dict) -> InsightReport:
        """Generate template-based insights"""
        
        recommendations = []
        patterns = []
        
        # Analyze platform performance
        if 'platform_breakdown' in stats:
            best_platform = max(
                stats['platform_breakdown'].items(),
                key=lambda x: x[1].get('revenue', 0) / max(x[1].get('spend', 1), 1)
            )[0] if stats['platform_breakdown'] else None
            
            if best_platform:
                recommendations.append(f"Increase budget allocation to {best_platform} - highest ROAS")
                patterns.append(f"{best_platform} shows strongest performance")
        
        # CTR analysis
        if stats.get('avg_ctr', 0) < 2.0:
            recommendations.append("CTR below 2% - test new ad creatives and headlines")
        
        # ROAS analysis
        if stats.get('overall_roas', 0) < 3.0:
            recommendations.append("ROAS below target - review targeting and bidding strategy")
        
        return InsightReport(
            report_id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            period_start=datetime.now(),
            period_end=datetime.now(),
            summary=f"Analyzed {stats.get('total_campaigns', 0)} campaigns with ${stats.get('total_spend', 0):.2f} spend",
            key_metrics=stats,
            trends=[],
            recommendations=recommendations[:3],
            action_items=[],
            platform_insights={},
            patterns=patterns,
            anomalies=[]
        )
