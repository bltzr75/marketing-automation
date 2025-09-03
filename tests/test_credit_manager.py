"""Test credit manager functionality"""

import unittest
import time
import threading
from src.core.credit_manager import get_credit_manager, CreditManager

class TestCreditManager(unittest.TestCase):
    
    def setUp(self):
        """Reset singleton for tests"""
        CreditManager._instance = None
        self.manager = get_credit_manager()
    
    def test_singleton_pattern(self):
        """Test that only one instance exists"""
        manager1 = get_credit_manager()
        manager2 = get_credit_manager()
        self.assertIs(manager1, manager2)
    
    def test_rate_limiting(self):
        """Test RPM rate limiting"""
        # Track initial state
        initial_requests = self.manager.total_requests
        
        # Make a request
        self.manager.track_request_start()
        self.manager.track_usage(100, 50, 'test', True)
        
        # Verify tracking
        self.assertEqual(self.manager.total_requests, initial_requests + 1)
        self.assertEqual(self.manager.total_tokens, 150)
    
    def test_component_tracking(self):
        """Test component-specific tracking"""
        self.manager.track_usage(100, 100, 'collector', True)
        self.manager.track_usage(50, 50, 'insight_agent', True)
        
        stats = self.manager.get_usage_stats()
        self.assertEqual(stats['component_breakdown']['collector']['calls'], 1)
        self.assertEqual(stats['component_breakdown']['insight_agent']['calls'], 1)
    
    def test_cost_calculation(self):
        """Test cost calculation"""
        self.manager.track_usage(1000, 500, 'test', True)
        stats = self.manager.get_usage_stats()
        
        # Expected: (1000 * 0.075 + 500 * 0.30) / 1_000_000
        expected_cost = (1000 * 0.075 + 500 * 0.30) / 1_000_000
        self.assertAlmostEqual(stats['estimated_cost'], expected_cost, places=8)
    
    def test_thread_safety(self):
        """Test thread-safe access"""
        def make_requests():
            for _ in range(5):
                self.manager.track_usage(10, 10, 'test', True)
        
        threads = [threading.Thread(target=make_requests) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 15 total requests (3 threads * 5 requests)
        self.assertEqual(self.manager.total_requests, 15)

if __name__ == '__main__':
    unittest.main()
