"""
Multi-platform campaign data collector
Single responsibility: Fetch and normalize campaign data
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from src.models.schemas import CampaignMetrics
from src.core.credit_manager import get_credit_manager

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


logger = logging.getLogger(__name__)

class CampaignCollector:
    """Collects campaign data from multiple platforms"""
    
    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock
        self.credit_manager = get_credit_manager()
        
        # API credentials from env
        self.google_ads_key = os.getenv('GOOGLE_ADS_API_KEY')
        self.meta_token = os.getenv('META_ACCESS_TOKEN')
        self.linkedin_token = os.getenv('LINKEDIN_API_TOKEN')
        
        if not use_mock and not any([self.google_ads_key, self.meta_token, self.linkedin_token]):
            logger.warning("No API credentials found, using mock data")
            self.use_mock = True
    
    def collect_all(self, time_range_hours: int = 24) -> List[CampaignMetrics]:
        """Collect from all platforms"""
        all_metrics = []
        
        # Collect from each platform
        for platform, collector in [
            ('google_ads', self._collect_google_ads),
            ('meta', self._collect_meta),
            ('linkedin', self._collect_linkedin)
        ]:
            try:
                metrics = collector(time_range_hours)
                all_metrics.extend(metrics)
                logger.info(f"Collected {len(metrics)} campaigns from {platform}")
            except Exception as e:
                logger.error(f"Failed to collect from {platform}: {e}")
        
        return all_metrics
    
    def _collect_google_ads(self, hours: int) -> List[CampaignMetrics]:
        """Collect Google Ads data"""
        if self.use_mock:
            return self._get_mock_data('google_ads', hours)
        
        # Real API implementation would go here
        # For now, return mock data
        return self._get_mock_data('google_ads', hours)
    
    def _collect_meta(self, hours: int) -> List[CampaignMetrics]:
        """Collect Meta/Facebook data"""
        if self.use_mock:
            return self._get_mock_data('meta', hours)
        
        # Real API implementation
        return self._get_mock_data('meta', hours)
    
    def _collect_linkedin(self, hours: int) -> List[CampaignMetrics]:
        """Collect LinkedIn data"""
        if self.use_mock:
            return self._get_mock_data('linkedin', hours)
        
        # Real API implementation
        return self._get_mock_data('linkedin', hours)
    
    def _get_mock_data(self, platform: str, hours: int) -> List[CampaignMetrics]:
        """Generate mock campaign data"""
        from src.collectors.mock_data import generate_mock_campaigns
        return generate_mock_campaigns(platform, count=3)
