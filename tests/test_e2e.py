"""End-to-end integration test"""

import unittest
import time
import requests
import psycopg2
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestE2EIntegration(unittest.TestCase):
    
    def setUp(self):
        self.api_url = "http://localhost:8000"
        try:
            self.db_conn = psycopg2.connect(
                "postgresql://user:pass@localhost/campaigns"
            )
        except:
            self.skipTest("Database not available")
    
    def tearDown(self):
        if hasattr(self, 'db_conn'):
            self.db_conn.close()
    
    def test_full_pipeline(self):
        """Test complete data flow"""
        
        # Check if API is running
        try:
            response = requests.get(f"{self.api_url}/health", timeout=2)
        except requests.exceptions.ConnectionError:
            self.skipTest("API server not running. Start with: python3 -m src.api.endpoints")
        
        # 1. Collect data
        response = requests.post(f"{self.api_url}/api/collect")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        campaigns_collected = data['campaigns_collected']
        
        # 2. Verify data in database
        cur = self.db_conn.cursor()
        cur.execute("SELECT COUNT(*) FROM campaign_metrics")
        count = cur.fetchone()[0]
        self.assertGreater(count, 0)
        
        # 3. Check alerts
        response = requests.get(f"{self.api_url}/api/alerts")
        self.assertEqual(response.status_code, 200)
        alerts = response.json()
        self.assertEqual(alerts['status'], 'success')
        
        # 4. Get insights
        response = requests.get(f"{self.api_url}/api/insights")
        self.assertEqual(response.status_code, 200)
        insights = response.json()
        self.assertEqual(insights['status'], 'success')
        self.assertIn('summary', insights)
        
        # 5. Optimize
        response = requests.post(
            f"{self.api_url}/api/optimize",
            json={"total_budget": 5000}
        )
        self.assertEqual(response.status_code, 200)
        optimization = response.json()
        self.assertEqual(optimization['status'], 'success')
        
        # 6. Check usage
        response = requests.get(f"{self.api_url}/api/usage")
        self.assertEqual(response.status_code, 200)
        usage = response.json()
        self.assertIn('total_requests', usage['usage'])
    
    def test_grafana_queries(self):
        """Test Grafana SQL queries work"""
        cur = self.db_conn.cursor()
        
        # Ensure tables exist
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'campaign_metrics'
        """)
        if not cur.fetchone():
            self.skipTest("campaign_metrics table not found")
        
        # Test each dashboard query with COALESCE for empty results
        queries = [
            "SELECT COALESCE(AVG(ctr), 0) as ctr FROM campaign_metrics WHERE timestamp > NOW() - INTERVAL '24 hours'",
            "SELECT COALESCE(SUM(daily_spend), 0) FROM campaign_metrics WHERE DATE(timestamp) = CURRENT_DATE",
            "SELECT COALESCE(AVG(budget_utilization), 0) FROM campaign_metrics WHERE timestamp > NOW() - INTERVAL '1 hour'"
        ]
        
        for query in queries:
            try:
                cur.execute(query)
                result = cur.fetchall()
                # Query should execute without error
                self.assertIsNotNone(result)
            except Exception as e:
                self.fail(f"Query failed: {query}\nError: {e}")

if __name__ == '__main__':
    unittest.main()
