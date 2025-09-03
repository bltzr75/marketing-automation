"""
Main orchestration script
Single responsibility: Coordinate all components
"""

import logging
import time
from datetime import datetime
from pathlib import Path

from src.collectors.collector import CampaignCollector
from src.storage.db_manager import DatabaseManager
from src.agents.insight_agent import PerformanceInsightAgent
from src.alerts.alert import AlertManager
from src.core.credit_manager import get_credit_manager

# New imports
from src.processors.optimizer import BidOptimizer
from src.storage.vector_store_lite import AdVectorStoreLite as AdVectorStore

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_pipeline():
    """Run the complete data pipeline"""
    
    logger.info("Starting marketing automation pipeline")
    
    # Initialize components
    collector = CampaignCollector(use_mock=True)
    db_manager = DatabaseManager()
    insight_agent = PerformanceInsightAgent()
    alert_manager = AlertManager()
    credit_manager = get_credit_manager()
    
    try:
        # Step 1: Collect data
        logger.info("Step 1: Collecting campaign data...")
        metrics = collector.collect_all(time_range_hours=24)
        logger.info(f"Collected {len(metrics)} campaign metrics")
        
        # Step 2: Store in database
        logger.info("Step 2: Storing metrics...")
        db_manager.insert_metrics(metrics)
        
        # Step 3: Check alerts
        logger.info("Step 3: Checking alerts...")
        alerts = alert_manager.check_metrics(metrics)
        logger.info(f"Generated {len(alerts)} alerts")
        
        # Step 4: Generate insights (less frequent)
        if datetime.now().hour % 4 == 0:  # Every 4 hours
            logger.info("Step 4: Generating insights...")
            report = insight_agent.analyze_performance(metrics)
            logger.info(f"Generated report: {report.report_id}")
            
            # Save report
            report_dir = Path("data/reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            report_file = report_dir / f"{report.report_id}.json"
            
            with open(report_file, 'w') as f:
                f.write(report.json(indent=2))
            logger.info(f"Report saved to {report_file}")
        
        # Log usage stats
        stats = credit_manager.get_usage_stats()
        logger.info(f"API usage: {stats['total_requests']} requests, ${stats['estimated_cost']:.4f}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


def run_optimization_pipeline():
    """Run optimization pipeline (less frequent)"""
    
    logger.info("Starting optimization pipeline")
    
    # Initialize components
    db_manager = DatabaseManager()
    optimizer = BidOptimizer()
    vector_store = AdVectorStore()
    
    try:
        # Get recent metrics
        recent_metrics = db_manager.get_recent_metrics(hours=24)
        
        if not recent_metrics:
            logger.info("No recent metrics for optimization")
            return
        
        # Convert to CampaignMetrics objects
        from src.models.schemas import CampaignMetrics
        metrics = []
        for m in recent_metrics:
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
        
        # Calculate bid adjustments
        adjustments = optimizer.calculate_adjustments(metrics)
        logger.info(f"Calculated {len(adjustments)} bid adjustments")
        
        for adj in adjustments:
            logger.info(f"  {adj['campaign_id']}: {adj['adjustment_percent']:+.1f}% - {', '.join(adj['reasons'])}")
        
        # Calculate budget reallocation
        total_budget = sum(m.daily_budget_limit for m in metrics)
        reallocation = optimizer.get_budget_reallocation(metrics, total_budget)
        logger.info(f"Budget reallocation: {reallocation}")
        
        # Store high-performing ads in vector store
        for m in metrics:
            if m.ctr > 3.0 and m.roas > 3.0:  # High performers
                from src.models.schemas import AdContent
                ad = AdContent(
                    ad_id=f"{m.campaign_id}_ad",
                    campaign_id=m.campaign_id,
                    platform=m.platform,
                    headline="High Performing Ad",  # Would get from API
                    description="Ad description",
                    cta="Learn More",
                    ctr=m.ctr,
                    conversions=m.conversions,
                    roas=m.roas,
                    created_at=datetime.now()
                )
                vector_store.store_ad(ad)
        
        # Analyze patterns
        patterns = vector_store.analyze_patterns()
        logger.info(f"Pattern analysis: {patterns}")
        
    except Exception as e:
        logger.error(f"Optimization pipeline failed: {e}", exc_info=True)


def main():
    """Main entry point with scheduling"""
    iteration = 0
    while True:
        try:
            # Run main pipeline every 30 minutes
            run_pipeline()
            
            # Run optimization every 2 hours (every 4th iteration)
            if iteration % 4 == 0:
                run_optimization_pipeline()
            
            iteration += 1
            logger.info(f"Iteration {iteration} complete, sleeping for 30 minutes...")
            time.sleep(1800)  # 30 minutes
            
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            time.sleep(300)  # 5 minutes on error


if __name__ == "__main__":
    main()
