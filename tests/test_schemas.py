"""Test Pydantic schemas"""

import unittest
from datetime import datetime
from src.models.schemas import CampaignMetrics, Alert, AdContent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TestSchemas(unittest.TestCase):
    
    def test_campaign_metrics_validation(self):
        """Test campaign metrics validation and calculation"""
        metrics = CampaignMetrics(
            campaign_id="camp_001",
            platform="google_ads",
            timestamp=datetime.now(),
            impressions=1000,
            clicks=50,
            conversions=5,
            cpc=2.5,
            daily_spend=125,
            daily_budget_limit=200,
            revenue=500
        )
        
        # Test calculated fields
        self.assertEqual(metrics.ctr, 5.0)  # 50/1000 * 100
        self.assertEqual(metrics.roas, 4.0)  # 500/125
        self.assertEqual(metrics.budget_utilization, 62.5)  # 125/200 * 100
    
    def test_platform_validation(self):
        """Test platform field validation"""
        with self.assertRaises(ValueError):
            CampaignMetrics(
                campaign_id="camp_001",
                platform="invalid_platform",  # Should fail
                timestamp=datetime.now(),
                impressions=100,
                clicks=10,
                conversions=1,
                cpc=1.0,
                daily_spend=10,
                daily_budget_limit=100
            )
    
    def test_alert_creation(self):
        """Test alert model creation"""
        alert = Alert(
            alert_type="budget",
            severity="warning",
            metric_name="daily_spend",
            current_value=180,
            threshold_value=150,
            message="Daily spend exceeds threshold"
        )
        
        self.assertEqual(alert.alert_type, "budget")
        self.assertEqual(alert.severity, "warning")
        self.assertIsNotNone(alert.timestamp)
    
    def test_ad_content_serialization(self):
        """Test ad content serialization"""
        ad = AdContent(
            ad_id="ad_001",
            campaign_id="camp_001",
            platform="linkedin",
            headline="Boost Your Construction Efficiency",
            description="AI-powered solutions for modern construction",
            cta="Learn More",
            ctr=3.5,
            conversions=10,
            roas=5.2,
            created_at=datetime.now(),
            tags=["construction", "AI", "B2B"]
        )
        
        # Test JSON serialization
        ad_dict = ad.model_dump()

        self.assertIn('headline', ad_dict)
        self.assertEqual(len(ad.tags), 3)

if __name__ == '__main__':
    unittest.main()
