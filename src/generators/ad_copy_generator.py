"""
Ad copy generator using templates and AI
Single responsibility: Generate ad variations for different platforms
"""

import json
from typing import Dict, List
from src.core.credit_manager import get_credit_manager

class AdCopyGenerator:
    def __init__(self):
        self.credit_manager = get_credit_manager()
        
    def generate_variations(self, campaign_metrics: Dict) -> Dict:
        """Generate platform-specific ad copy based on performance data"""
        
        platform = campaign_metrics.get('platform', 'google_ads')
        roas = campaign_metrics.get('roas', 0)
        
        # Template-based generation (no API needed)
        if platform == 'linkedin':
            return {
                'headlines': [
                    "Reduce Project Delays by 30%",
                    "Smart Monitoring for Construction Sites",
                    "1000+ Sites Trust Our Solution"
                ],
                'descriptions': [
                    "Real-time insights. Instant alerts. Zero training needed.",
                    "Cut waiting times. Improve safety. Boost productivity.",
                    "Professional IoT solution for modern construction."
                ],
                'ctas': ["Get Demo", "Learn More", "See Results"]
            }
        elif platform == 'google_ads':
            return {
                'headlines': [
                    "Construction Site Efficiency",
                    "Smart Elevator Monitoring", 
                    "30% Less Waiting Time"
                ],
                'descriptions': [
                    "Quick setup. Immediate results.",
                    "Install in 10 minutes. See results today.",
                    "Trusted by major contractors."
                ],
                'ctas': ["Start Free Trial", "Get Quote", "Learn More"]
            }
        else:  # meta/facebook
            return {
                'headlines': [
                    "Still Using Paper Logs?",
                    "Construction Just Got Smarter",
                    "Join 1000+ Smart Sites"
                ],
                'descriptions': [
                    "Transform your site operations with one simple device.",
                    "See why contractors are switching to smart monitoring.",
                    "Real results from real construction sites."
                ],
                'ctas': ["See How", "Watch Demo", "Get Started"]
            }
    
    def generate_by_performance(self, top_performers: List[Dict]) -> Dict:
        """Generate copy based on what's working"""
        
        # Analyze top performers
        best_keywords = []
        for campaign in top_performers:
            if campaign.get('roas', 0) > 5:
                best_keywords.append(campaign.get('campaign_id', '').split('_')[1])
        
        return {
            'recommendation': "Focus on efficiency and time-saving messaging",
            'winning_themes': best_keywords[:5],
            'suggested_headlines': [
                f"Proven {kw.title()} Solution" for kw in best_keywords[:3]
            ]
        }
