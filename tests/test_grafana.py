"""Test Grafana dashboard configuration"""

import unittest
import json
import yaml
from pathlib import Path

class TestGrafanaDashboard(unittest.TestCase):
    
    def test_dashboard_json_valid(self):
        """Test dashboard JSON is valid"""
        dashboard_path = Path('dashboards/campaign_performance.json')
        self.assertTrue(dashboard_path.exists())
        
        with open(dashboard_path, 'r') as f:
            dashboard = json.load(f)
        
        # Check required fields (dashboard at root level now)
        self.assertIn('panels', dashboard)
        self.assertIn('title', dashboard)
        self.assertGreater(len(dashboard['panels']), 0)


    
    def test_datasource_yaml_valid(self):
        """Test datasource YAML is valid"""
        datasource_path = Path('dashboards/datasource.yaml')
        self.assertTrue(datasource_path.exists())
        
        with open(datasource_path, 'r') as f:
            datasource = yaml.safe_load(f)
        
        # Check required fields
        self.assertEqual(datasource['apiVersion'], 1)
        self.assertIn('datasources', datasource)
        self.assertEqual(datasource['datasources'][0]['type'], 'postgres')
    
    def test_all_panels_have_queries(self):
        """Test all panels have SQL queries"""
        with open('dashboards/campaign_performance.json', 'r') as f:
            dashboard = json.load(f)
        
        # Panels are at root level now
        for panel in dashboard['panels']:
            self.assertIn('targets', panel)
            self.assertGreater(len(panel['targets']), 0)
            self.assertIn('rawSql', panel['targets'][0])

if __name__ == '__main__':
    unittest.main()
