"""Test report generator functionality"""

import unittest
import json
from pathlib import Path
from datetime import datetime
from src.reports.generator import ReportGenerator
from src.models.schemas import InsightReport

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestReportGenerator(unittest.TestCase):
    
    def setUp(self):
        self.generator = ReportGenerator()
        
        # Create test data
        self.test_insights = InsightReport(
            report_id="test_report_001",
            timestamp=datetime.now(),
            period_start=datetime.now(),
            period_end=datetime.now(),
            summary="Test summary",
            key_metrics={'total_campaigns': 5},
            trends=[],
            recommendations=["Test recommendation 1", "Test recommendation 2"],
            action_items=[],
            platform_insights={},
            patterns=["Pattern 1"],
            anomalies=[]
        )
        
        self.test_metrics = [
            {
                'campaign_id': 'test_001',
                'platform': 'google_ads',
                'ctr': 3.5,
                'roas': 4.2,
                'daily_spend': 100,
                'revenue': 420,
                'budget_utilization': 75
            },
            {
                'campaign_id': 'test_002',
                'platform': 'linkedin',
                'ctr': 2.1,
                'roas': 3.1,
                'daily_spend': 150,
                'revenue': 465,
                'budget_utilization': 85
            }
        ]
    
    def test_html_report_generation(self):
        """Test HTML report is generated"""
        filepath = self.generator.generate_html_report(
            self.test_insights,
            self.test_metrics
        )
        
        # Check file was created
        self.assertTrue(Path(filepath).exists())
        
        # Check content
        with open(filepath, 'r') as f:
            content = f.read()
            self.assertIn('Test summary', content)
            self.assertIn('test_001', content)
            self.assertIn('google_ads', content)
    
    def test_json_summary_generation(self):
        """Test JSON summary generation"""
        summary = self.generator.generate_summary_json(
            self.test_insights,
            self.test_metrics
        )
        
        # Check structure
        self.assertIn('executive_summary', summary)
        self.assertIn('kpis', summary)
        self.assertIn('platform_breakdown', summary)
        
        # Check calculations
        self.assertEqual(summary['kpis']['total_campaigns'], 2)
        self.assertEqual(summary['kpis']['total_spend'], 250)
    
    def test_platform_breakdown(self):
        """Test platform breakdown calculation"""
        breakdown = self.generator._get_platform_breakdown(self.test_metrics)
        
        self.assertIn('google_ads', breakdown)
        self.assertIn('linkedin', breakdown)
        self.assertEqual(breakdown['google_ads']['count'], 1)
        self.assertEqual(breakdown['google_ads']['roas'], 4.2)
    
    def test_alerts_summary(self):
        """Test alerts summary generation"""
        alerts = self.generator._get_alerts_summary(self.test_metrics)
        
        self.assertIn('total_alerts', alerts)
        self.assertIn('by_type', alerts)
        
        # test_002 has budget_utilization > 80
        self.assertIn('test_002', alerts['by_type']['high_spend'])

if __name__ == '__main__':
    unittest.main()
