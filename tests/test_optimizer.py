"""Test bid optimizer"""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch
from src.processors.optimizer import BidOptimizer
from src.collectors.mock_data import generate_mock_campaigns

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestOptimizer(unittest.TestCase):
    
    def setUp(self):
        # Mock the database manager
        with patch('src.processors.optimizer.DatabaseManager') as MockDB:
            self.mock_db = MockDB.return_value
            self.optimizer = BidOptimizer()
            self.optimizer.db = self.mock_db
    
    def test_bid_adjustments(self):
        """Test bid adjustment calculations"""
        # Generate mock data
        metrics = generate_mock_campaigns('google_ads', 5)
        
        # Mock database history response
        mock_history = [
            {'roas': 3.5, 'ctr': 2.5, 'campaign_id': 'test'},
            {'roas': 3.2, 'ctr': 2.3, 'campaign_id': 'test'},
            {'roas': 3.8, 'ctr': 2.7, 'campaign_id': 'test'},
            {'roas': 3.1, 'ctr': 2.4, 'campaign_id': 'test'},
            {'roas': 3.6, 'ctr': 2.6, 'campaign_id': 'test'},
            {'roas': 3.3, 'ctr': 2.2, 'campaign_id': 'test'},
            {'roas': 3.7, 'ctr': 2.8, 'campaign_id': 'test'},
        ]
        self.mock_db.get_campaign_history.return_value = mock_history
        
        # Calculate adjustments
        adjustments = self.optimizer.calculate_adjustments(metrics)
        
        # Verify structure
        if adjustments:  # May be empty if performance is on target
            adj = adjustments[0]
            self.assertIn('campaign_id', adj)
            self.assertIn('new_bid', adj)
            self.assertIn('adjustment_percent', adj)
            self.assertIn('reasons', adj)
    
    def test_budget_reallocation(self):
        """Test budget reallocation logic"""
        metrics = generate_mock_campaigns('google_ads', 3)
        total_budget = 1000
        
        reallocation = self.optimizer.get_budget_reallocation(metrics, total_budget)
        
        self.assertIn('allocations', reallocation)
        self.assertEqual(reallocation['total_budget'], total_budget)
        
        # Verify allocations sum to total budget (approximately)
        if reallocation['allocations']:
            total_allocated = sum(
                a['recommended_budget'] 
                for a in reallocation['allocations'].values()
            )
            self.assertAlmostEqual(total_allocated, total_budget, delta=1)

if __name__ == '__main__':
    unittest.main()
