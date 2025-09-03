"""Test API endpoints"""

import unittest
import json
from unittest.mock import patch, Mock

class TestAPI(unittest.TestCase):
    
    def setUp(self):
        from src.api.endpoints import app
        self.app = app.test_client()
        self.app.testing = True
    
    def test_health_check(self):
        """Test health endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    @patch('src.api.endpoints.CampaignCollector')
    @patch('src.api.endpoints.DatabaseManager')
    def test_collect_endpoint(self, mock_db, mock_collector):
        """Test collection endpoint"""
        # Mock the collector
        mock_collector_instance = Mock()
        mock_collector_instance.collect_all.return_value = []
        mock_collector.return_value = mock_collector_instance
        
        # Mock the database
        mock_db_instance = Mock()
        mock_db_instance.insert_metrics.return_value = 0
        mock_db.return_value = mock_db_instance
        
        response = self.app.post('/api/collect')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
    
    @patch('src.api.endpoints.DatabaseManager')
    @patch('src.api.endpoints.AlertManager')
    def test_alerts_endpoint(self, mock_alert, mock_db):
        """Test alerts endpoint"""
        # Mock database
        mock_db_instance = Mock()
        mock_db_instance.get_recent_metrics.return_value = []
        mock_db.return_value = mock_db_instance
        
        # Mock alert manager
        mock_alert_instance = Mock()
        mock_alert_instance.check_metrics.return_value = []
        mock_alert.return_value = mock_alert_instance
        
        response = self.app.get('/api/alerts')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('alerts', data)

if __name__ == '__main__':
    unittest.main()
