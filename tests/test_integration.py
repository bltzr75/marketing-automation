"""Integration test for the complete pipeline"""

import unittest
import os
from unittest.mock import patch

from src.collectors.collector import CampaignCollector
from src.storage.db_manager import DatabaseManager
from src.agents.insight_agent import PerformanceInsightAgent
from src.alerts.alert import AlertManager

class TestIntegration(unittest.TestCase):
    
    def setUp(self):
        """Setup test environment"""
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost/test_campaigns'
    
    def test_complete_pipeline(self):
        """Test the complete data pipeline"""
        
        # Initialize components
        collector = CampaignCollector(use_mock=True)
        db = DatabaseManager()
        insight_agent = PerformanceInsightAgent()
        alert_manager = AlertManager()
        
        # Collect data
        metrics = collector.collect_all(time_range_hours=1)
        self.assertGreater(len(metrics), 0)
        
        # Check alerts
        alerts = alert_manager.check_metrics(metrics)
        self.assertIsInstance(alerts, list)
        
        # Generate insights
        report = insight_agent.analyze_performance(metrics)
        self.assertIsNotNone(report.report_id)
        self.assertIsNotNone(report.summary)
        self.assertGreater(len(report.recommendations), 0)

if __name__ == '__main__':
    unittest.main()
