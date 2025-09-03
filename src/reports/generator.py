"""
Report generator for stakeholder distribution
Single responsibility: Transform metrics and insights into formatted reports
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import jinja2

from src.storage.db_manager import DatabaseManager
from src.models.schemas import InsightReport
from src.generators.ad_copy_generator import AdCopyGenerator

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates HTML/PDF reports from campaign data"""
    
    def __init__(self, template_dir: str = "src/reports/templates"):
        self.template_dir = Path(template_dir)
        self.output_dir = Path("data/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir))
        )
    
    def generate_html_report(self, 
                           insights: InsightReport,
                           metrics: List[Dict],
                           optimizations: Optional[Dict] = None) -> str:
        """Generate HTML report from data"""
        
        # Load template
        template = self.jinja_env.get_template('report_template.html')
        
        # Generate ad copy suggestions
        ad_generator = AdCopyGenerator()
        top_performer = self._get_top_performer(metrics)
        platform = top_performer.get('platform', 'google_ads') if top_performer else 'google_ads'
        ad_suggestions = ad_generator.generate_variations({'platform': platform})
        
        # Prepare data
        context = {
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'period_start': insights.period_start.strftime('%Y-%m-%d'),
            'period_end': insights.period_end.strftime('%Y-%m-%d'),
            'summary': insights.summary,
            'key_metrics': insights.key_metrics,
            'recommendations': insights.recommendations,
            'patterns': insights.patterns,
            'recent_campaigns': self._format_campaigns(metrics),
            'optimizations': optimizations,
            'total_spend': sum(m.get('daily_spend', 0) for m in metrics),
            'avg_roas': self._calculate_avg_roas(metrics),
            'top_performer': self._get_top_performer(metrics),
            'ad_suggestions': ad_suggestions
        }
        
        # Render HTML
        html_content = template.render(**context)
        
        # Save to file
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Generated HTML report: {filepath}")
        return str(filepath)
    
    def generate_summary_json(self, 
                            insights: InsightReport,
                            metrics: List[Dict]) -> Dict:
        """Generate JSON summary for API consumption"""
        
        summary = {
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start': insights.period_start.isoformat(),
                'end': insights.period_end.isoformat()
            },
            'executive_summary': insights.summary,
            'kpis': {
                'total_campaigns': len(metrics),
                'total_spend': sum(m.get('daily_spend', 0) for m in metrics),
                'avg_roas': self._calculate_avg_roas(metrics),
                'avg_ctr': sum(m.get('ctr', 0) for m in metrics) / len(metrics) if metrics else 0
            },
            'top_recommendations': insights.recommendations[:3],
            'platform_breakdown': self._get_platform_breakdown(metrics),
            'alerts_summary': self._get_alerts_summary(metrics)
        }
        
        # Save JSON
        filename = f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary
    
    def _format_campaigns(self, metrics: List[Dict]) -> List[Dict]:
        """Format campaign data for display"""
        formatted = []
        for m in metrics[:10]:  # Top 10
            formatted.append({
                'campaign_id': m.get('campaign_id', 'N/A'),
                'platform': m.get('platform', 'N/A'),
                'ctr': f"{m.get('ctr', 0):.2f}%",
                'roas': f"{m.get('roas', 0):.2f}",
                'spend': f"${m.get('daily_spend', 0):.2f}",
                'status': self._get_campaign_status(m)
            })
        return formatted
    
    def _get_campaign_status(self, metric: Dict) -> str:
        """Determine campaign status"""
        roas = metric.get('roas', 0)
        if roas >= 4:
            return 'excellent'
        elif roas >= 3:
            return 'good'
        elif roas >= 2:
            return 'fair'
        else:
            return 'needs_attention'
    
    def _calculate_avg_roas(self, metrics: List[Dict]) -> float:
        """Calculate average ROAS"""
        if not metrics:
            return 0
        total_revenue = sum(m.get('revenue', 0) for m in metrics)
        total_spend = sum(m.get('daily_spend', 0) for m in metrics)
        return total_revenue / total_spend if total_spend > 0 else 0
    
    def _get_top_performer(self, metrics: List[Dict]) -> Dict:
        """Get best performing campaign"""
        if not metrics:
            return {}
        return max(metrics, key=lambda x: x.get('roas', 0))
    
    def _get_platform_breakdown(self, metrics: List[Dict]) -> Dict:
        """Get performance by platform"""
        platforms = {}
        for m in metrics:
            platform = m.get('platform', 'unknown')
            if platform not in platforms:
                platforms[platform] = {
                    'count': 0,
                    'spend': 0,
                    'revenue': 0
                }
            platforms[platform]['count'] += 1
            platforms[platform]['spend'] += m.get('daily_spend', 0)
            platforms[platform]['revenue'] += m.get('revenue', 0)
        
        # Calculate ROAS per platform
        for p in platforms:
            spend = platforms[p]['spend']
            platforms[p]['roas'] = platforms[p]['revenue'] / spend if spend > 0 else 0
        
        return platforms
    
    def _get_alerts_summary(self, metrics: List[Dict]) -> Dict:
        """Summarize alert conditions"""
        alerts = {
            'high_spend': [],
            'low_roas': [],
            'low_ctr': []
        }
        
        for m in metrics:
            if m.get('budget_utilization', 0) > 80:
                alerts['high_spend'].append(m.get('campaign_id'))
            if m.get('roas', 0) < 2:
                alerts['low_roas'].append(m.get('campaign_id'))
            if m.get('ctr', 0) < 1:
                alerts['low_ctr'].append(m.get('campaign_id'))
        
        return {
            'total_alerts': sum(len(v) for v in alerts.values()),
            'by_type': alerts
        }


    def generate_pdf_report(self, html_path: str) -> str:
        """Convert HTML report to PDF using weasyprint"""
        # Install: pip install weasyprint
        import weasyprint
        
        pdf_path = html_path.replace('.html', '.pdf')
        weasyprint.HTML(filename=html_path).write_pdf(pdf_path)
        
        logger.info(f"Generated PDF: {pdf_path}")
        return pdf_path