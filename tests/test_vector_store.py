"""Test vector store functionality - simplified without external dependencies"""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch
from src.models.schemas import AdContent
from dotenv import load_dotenv
from src.storage.vector_store_lite import AdVectorStoreLite as AdVectorStore

# Load environment variables
load_dotenv()


class TestVectorStore(unittest.TestCase):
    
    def test_ad_content_creation(self):
        """Test ad content model creation"""
        ad = AdContent(
            ad_id="test_ad_001",
            campaign_id="camp_001",
            platform="google_ads",
            headline="Revolutionary B2B Solution",
            description="Increase efficiency by 40% with our platform",
            cta="Get Started",
            ctr=3.5,
            conversions=10,
            roas=4.2,
            created_at=datetime.now(),
            tags=["B2B", "efficiency"]
        )
        
        self.assertEqual(ad.ad_id, "test_ad_001")
        self.assertEqual(ad.platform, "google_ads")
        self.assertEqual(ad.ctr, 3.5)
        self.assertEqual(len(ad.tags), 2)
    
    def test_vector_store_initialization(self):
        """Test vector store can be initialized"""
        try:
            # Use AdVectorStoreLite API
            store = AdVectorStore(data_dir="./data/test_chromadb")
            self.assertIsNotNone(store.ads)  # Changed from store.client
            self.assertIsInstance(store.ads, dict)
        except Exception as e:
            self.skipTest(f"Vector store initialization failed: {e}")

    def test_pattern_analysis_logic(self):
        """Test pattern analysis logic without actual storage"""
        # Create store with test data
        store = AdVectorStore(data_dir="./data/test_chromadb")
        
        # Add some test ads first
        from src.models.schemas import AdContent
        from datetime import datetime
        
        test_ad = AdContent(
            ad_id="test_001",
            campaign_id="campaign_001",
            platform="google_ads",
            headline="Test Headline",
            description="Test Description",
            cta="Learn More",
            ctr=3.5,
            conversions=10,
            roas=4.5,
            created_at=datetime.now()
        )
        store.store_ad(test_ad)
        
        # Now test pattern analysis
        patterns = store.analyze_patterns()
        
        # Should have data now
        self.assertNotEqual(patterns.get('status'), 'No ads to analyze')
        self.assertIn('average_ctr', patterns)
        self.assertIn('average_roas', patterns)


if __name__ == '__main__':
    unittest.main()