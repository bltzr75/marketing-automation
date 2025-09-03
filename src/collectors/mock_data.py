"""
Mock data generator for testing
Single responsibility: Generate realistic test data
"""

import random
from datetime import datetime, timedelta
from typing import List
from src.models.schemas import CampaignMetrics

def generate_mock_campaigns(platform: str, count: int = 5) -> List[CampaignMetrics]:
    """Generate mock campaign metrics"""
    campaigns = []
    
    for i in range(count):
        impressions = random.randint(1000, 50000)
        clicks = int(impressions * random.uniform(0.01, 0.05))  # 1-5% CTR
        conversions = int(clicks * random.uniform(0.02, 0.10))  # 2-10% conversion
        
        daily_spend = clicks * random.uniform(0.5, 5.0)  # CPC between $0.50-$5
        revenue = conversions * random.uniform(50, 500)  # Value per conversion
        
        campaign = CampaignMetrics(
            campaign_id=f"{platform}_camp_{i+1:03d}",
            platform=platform,
            timestamp=datetime.now() - timedelta(hours=random.randint(0, 24)),
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            cpc=daily_spend / clicks if clicks > 0 else 0,
            daily_spend=daily_spend,
            daily_budget_limit=daily_spend * random.uniform(1.2, 2.0),
            revenue=revenue
        )
        campaigns.append(campaign)
    
    return campaigns
