"""Test data collector"""

import unittest
from src.collectors.collector import CampaignCollector

class TestCollector(unittest.TestCase):
    
    def test_mock_collection(self):
        """Test mock data collection"""
        collector = CampaignCollector(use_mock=True)
        metrics = collector.collect_all(time_range_hours=24)
        
        # Should have data from 3 platforms
        self.assertGreater(len(metrics), 0)
        
        # Check platform diversity
        platforms = set(m.platform for m in metrics)
        self.assertEqual(len(platforms), 3)
    
    def test_data_validation(self):
        """Test that collected data passes validation"""
        collector = CampaignCollector(use_mock=True)
        metrics = collector.collect_all()
        
        for metric in metrics:
            # Check calculated fields
            self.assertGreaterEqual(metric.ctr, 0)
            self.assertLessEqual(metric.ctr, 100)
            self.assertGreaterEqual(metric.roas, 0)
            self.assertGreaterEqual(metric.budget_utilization, 0)

if __name__ == '__main__':
    unittest.main()
