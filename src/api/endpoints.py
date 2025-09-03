"""
REST API endpoints for automation integration
Single responsibility: HTTP interface for all components
"""

import json
import logging
from flask import Flask, request, jsonify
from datetime import datetime

from src.collectors.collector import CampaignCollector
from src.storage.db_manager import DatabaseManager
from src.agents.insight_agent import PerformanceInsightAgent
from src.alerts.alert import AlertManager
from src.processors.optimizer import BidOptimizer
from src.core.credit_manager import get_credit_manager

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


app = Flask(__name__)
logger = logging.getLogger(__name__)


# Initialize database on startup
def init_db():
    try:
        db = DatabaseManager()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
# Call initialization
init_db()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API info"""
    return jsonify({
        'name': 'Marketing Automation API',
        'version': '1.0',
        'endpoints': [
            '/health',
            '/api/collect',
            '/api/alerts', 
            '/api/optimize',
            '/api/insights',
            '/api/usage'
        ]
    })

@app.route('/api/collect', methods=['POST'])
def collect_campaigns():
    """Trigger campaign data collection"""
    try:
        collector = CampaignCollector(use_mock=True)
        metrics = collector.collect_all()
        
        # Store in database
        db = DatabaseManager()
        db.insert_metrics(metrics)
        
        return jsonify({
            'status': 'success',
            'campaigns_collected': len(metrics),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def check_alerts():
    """Check for campaign alerts"""
    try:
        db = DatabaseManager()
        alert_manager = AlertManager()
        
        # Get recent metrics
        recent = db.get_recent_metrics(hours=1)
        
        # Convert to CampaignMetrics
        from src.models.schemas import CampaignMetrics
        metrics = []
        for m in recent:
            metrics.append(CampaignMetrics(
                campaign_id=m['campaign_id'],
                platform=m['platform'],
                timestamp=m['timestamp'],
                impressions=m['impressions'],
                clicks=m['clicks'],
                conversions=m['conversions'],
                cpc=m['cpc'],
                daily_spend=m['daily_spend'],
                daily_budget_limit=m['daily_budget_limit'],
                revenue=m['revenue']
            ))
        
        alerts = alert_manager.check_metrics(metrics)
        
        return jsonify({
            'status': 'success',
            'alerts': [
                {
                    'type': a.alert_type,
                    'severity': a.severity,
                    'message': a.message,
                    'metric': a.metric_name,
                    'value': a.current_value
                } for a in alerts
            ],
            'total_alerts': len(alerts)
        })
    except Exception as e:
        logger.error(f"Alert check failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/optimize', methods=['POST'])
def optimize_bids():
    """Get bid optimization recommendations"""
    try:
        db = DatabaseManager()
        optimizer = BidOptimizer()
        
        # Get metrics
        recent = db.get_recent_metrics(hours=24)
        
        # Convert to CampaignMetrics
        from src.models.schemas import CampaignMetrics
        metrics = []
        for m in recent:
            metrics.append(CampaignMetrics(
                campaign_id=m['campaign_id'],
                platform=m['platform'],
                timestamp=m['timestamp'],
                impressions=m['impressions'],
                clicks=m['clicks'],
                conversions=m['conversions'],
                cpc=m['cpc'],
                daily_spend=m['daily_spend'],
                daily_budget_limit=m['daily_budget_limit'],
                revenue=m['revenue']
            ))
        
        adjustments = optimizer.calculate_adjustments(metrics)
        
        # Calculate budget reallocation
        total_budget = request.json.get('total_budget', 
                                       sum(m.daily_budget_limit for m in metrics))
        reallocation = optimizer.get_budget_reallocation(metrics, total_budget)
        
        return jsonify({
            'status': 'success',
            'adjustments': adjustments,
            'reallocation': reallocation
        })
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/insights', methods=['GET'])
def get_insights():
    """Generate performance insights"""
    try:
        db = DatabaseManager()
        agent = PerformanceInsightAgent()
        
        # Get metrics
        recent = db.get_recent_metrics(hours=24)
        
        # Convert to CampaignMetrics
        from src.models.schemas import CampaignMetrics
        metrics = []
        for m in recent:
            metrics.append(CampaignMetrics(
                campaign_id=m['campaign_id'],
                platform=m['platform'],
                timestamp=m['timestamp'],
                impressions=m['impressions'],
                clicks=m['clicks'],
                conversions=m['conversions'],
                cpc=m['cpc'],
                daily_spend=m['daily_spend'],
                daily_budget_limit=m['daily_budget_limit'],
                revenue=m['revenue']
            ))
        
        report = agent.analyze_performance(metrics)
        
        return jsonify({
            'status': 'success',
            'report_id': report.report_id,
            'summary': report.summary,
            'key_metrics': report.key_metrics,
            'recommendations': report.recommendations,
            'patterns': report.patterns
        })
    except Exception as e:
        logger.error(f"Insight generation failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/usage', methods=['GET'])
def get_usage():
    """Get API usage statistics"""
    try:
        manager = get_credit_manager()
        stats = manager.get_usage_stats()
        
        return jsonify({
            'status': 'success',
            'usage': stats
        })
    except Exception as e:
        logger.error(f"Usage stats failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/debug', methods=['GET'])
def debug_status():
    """Debug endpoint to check system status"""
    from src.agents.insight_agent import PerformanceInsightAgent
    
    agent = PerformanceInsightAgent()
    gemini_status = "Active" if agent.model else "Using Template Fallback"
    api_key_present = "Yes" if agent.api_key else "No"
    
    return jsonify({
        'gemini_status': gemini_status,
        'api_key_loaded': api_key_present,
        'api_key_preview': agent.api_key[:10] + '...' if agent.api_key else 'None',
        'credit_manager_stats': get_credit_manager().get_usage_stats()
    })

@app.route('/api/report', methods=['POST'])
def generate_report():
    """Generate a report from current data"""
    try:
        from src.reports.generator import ReportGenerator
        
        db = DatabaseManager()
        agent = PerformanceInsightAgent()
        optimizer = BidOptimizer()
        
        # Get recent metrics
        recent = db.get_recent_metrics(hours=24)
        
        # Convert to CampaignMetrics
        from src.models.schemas import CampaignMetrics
        metrics = []
        for m in recent:
            metrics.append(CampaignMetrics(
                campaign_id=m['campaign_id'],
                platform=m['platform'],
                timestamp=m['timestamp'],
                impressions=m['impressions'],
                clicks=m['clicks'],
                conversions=m['conversions'],
                cpc=m['cpc'],
                daily_spend=m['daily_spend'],
                daily_budget_limit=m['daily_budget_limit'],
                revenue=m['revenue']
            ))
        
        # Generate insights
        insights = agent.analyze_performance(metrics)
        
        # Get optimizations
        total_budget = request.json.get('total_budget', 5000)
        reallocation = optimizer.get_budget_reallocation(metrics, total_budget)
        
        # Generate report
        generator = ReportGenerator()
        
        # Convert metrics back to dict for report
        metrics_dict = [m.model_dump() for m in metrics]
        
        html_path = generator.generate_html_report(
            insights, 
            metrics_dict,
            reallocation
        )
        
        # Generate PDF version
        pdf_path = None
        try:
            pdf_path = generator.generate_pdf_report(html_path)
            logger.info(f"PDF report generated: {pdf_path}")
        except ImportError:
            logger.warning("PDF generation library not installed, skipping PDF")
        except Exception as e:
            logger.warning(f"PDF generation failed: {e}, HTML report still available")
        
        json_summary = generator.generate_summary_json(
            insights,
            metrics_dict
        )
        
        return jsonify({
            'status': 'success',
            'html_report': html_path,
            'pdf_report': pdf_path,
            'summary': json_summary
        })
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

@app.route('/api/generate-copy', methods=['POST'])
def generate_ad_copy():
    """Generate ad copy variations"""
    try:
        from src.generators.ad_copy_generator import AdCopyGenerator
        
        generator = AdCopyGenerator()
        
        # Get request data
        data = request.json or {}
        platform = data.get('platform', 'google_ads')
        
        # Generate variations
        variations = generator.generate_variations({'platform': platform})
        
        return jsonify({
            'status': 'success',
            'platform': platform,
            'variations': variations,
            'count': len(variations.get('headlines', []))
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def run_api(host='0.0.0.0', port=8000, debug=False):
    """Run the API server"""
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_api(debug=True)
