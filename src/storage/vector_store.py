"""
Vector database for semantic ad similarity search
Single responsibility: Store and search ad content by similarity
"""

import logging
from typing import List, Dict, Optional
import chromadb
from chromadb.utils import embedding_functions

from src.models.schemas import AdContent

logger = logging.getLogger(__name__)

class AdVectorStore:
    """Manages ad content in vector database"""


    def __init__(self, persist_directory: str = "./data/chromadb"):
        try:
            # Try persistent client
            import chromadb.config
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=chromadb.config.Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        except Exception as e:
            # Fall back to in-memory
            logger.warning(f"Using in-memory ChromaDB: {e}")
            self.client = chromadb.Client()
        
        # Simple embedding function
        try:
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
            self.embedding_fn = DefaultEmbeddingFunction()
        except:
            logger.warning("No embedding function available")
            self.embedding_fn = None
        
        # Get or create collection
        try:
            self.collection = self.client.get_or_create_collection(
                name="campaign_ads",
                embedding_function=self.embedding_fn if self.embedding_fn else None
            )
            logger.info(f"Collection ready with {self.collection.count()} ads")
        except Exception as e:
            logger.error(f"Collection creation failed: {e}")
            # Create simple collection without embeddings
            self.collection = self.client.get_or_create_collection(
                name="campaign_ads"
            )
            



    def store_ad(self, ad: AdContent) -> None:
        """Store ad content with performance metadata"""
        
        # Combine text for embedding
        text = f"{ad.headline} {ad.description} {ad.cta}"
        
        # Store with metadata
        self.collection.add(
            documents=[text],
            metadatas=[{
                'ad_id': ad.ad_id,
                'campaign_id': ad.campaign_id,
                'platform': ad.platform,
                'headline': ad.headline,
                'description': ad.description,
                'cta': ad.cta,
                'ctr': ad.ctr,
                'conversions': ad.conversions,
                'roas': ad.roas,
                'created_at': ad.created_at.isoformat()
            }],
            ids=[ad.ad_id]
        )
        
        logger.info(f"Stored ad {ad.ad_id} with CTR={ad.ctr:.2f}%")
    
    def find_similar_ads(self, query: str, 
                        min_performance: Optional[Dict] = None,
                        limit: int = 5) -> List[Dict]:
        """Find similar high-performing ads"""
        
        # Build filter
        where = {}
        if min_performance:
            if 'min_ctr' in min_performance:
                where['ctr'] = {'$gte': min_performance['min_ctr']}
            if 'min_roas' in min_performance:
                where['roas'] = {'$gte': min_performance['min_roas']}
        
        # Search
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=where if where else None
        )
        
        if not results['metadatas'] or not results['metadatas'][0]:
            return []
        
        # Format results
        similar_ads = []
        for i, metadata in enumerate(results['metadatas'][0]):
            similar_ads.append({
                'ad_id': metadata['ad_id'],
                'campaign_id': metadata['campaign_id'],
                'platform': metadata['platform'],
                'headline': metadata['headline'],
                'description': metadata['description'],
                'cta': metadata['cta'],
                'ctr': metadata['ctr'],
                'roas': metadata['roas'],
                'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
            })
        
        return similar_ads
    
    def get_top_performers(self, platform: Optional[str] = None, 
                          limit: int = 10) -> List[Dict]:
        """Get top performing ads"""
        
        where = {'platform': platform} if platform else None
        
        # Get all ads (or filtered by platform)
        results = self.collection.get(
            where=where,
            limit=limit * 10  # Get more to sort
        )
        
        if not results['metadatas']:
            return []
        
        # Sort by performance (ROAS * CTR as combined metric)
        ads = results['metadatas']
        ads.sort(key=lambda x: x.get('roas', 0) * x.get('ctr', 0), reverse=True)
        
        return ads[:limit]
    
    def analyze_patterns(self) -> Dict:
        """Analyze patterns in successful ads"""
        
        # Get high performers
        top_ads = self.get_top_performers(limit=20)
        
        if not top_ads:
            return {'status': 'No ads to analyze'}
        
        # Analyze common elements
        headlines = [ad['headline'] for ad in top_ads]
        ctas = [ad['cta'] for ad in top_ads]
        
        # Find common words (simple frequency analysis)
        word_freq = {}
        for headline in headlines:
            for word in headline.lower().split():
                if len(word) > 3:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Calculate average performance
        avg_ctr = sum(ad['ctr'] for ad in top_ads) / len(top_ads)
        avg_roas = sum(ad['roas'] for ad in top_ads) / len(top_ads)
        
        # Most common CTAs
        cta_freq = {}
        for cta in ctas:
            cta_freq[cta] = cta_freq.get(cta, 0) + 1
        
        top_ctas = sorted(cta_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_ads_analyzed': len(top_ads),
            'average_ctr': round(avg_ctr, 2),
            'average_roas': round(avg_roas, 2),
            'top_headline_words': [{'word': w, 'frequency': f} for w, f in top_words],
            'top_ctas': [{'cta': c, 'frequency': f} for c, f in top_ctas],
            'platform_breakdown': self._get_platform_breakdown(top_ads)
        }
    
    def _get_platform_breakdown(self, ads: List[Dict]) -> Dict:
        """Get performance breakdown by platform"""
        platforms = {}
        
        for ad in ads:
            platform = ad['platform']
            if platform not in platforms:
                platforms[platform] = {
                    'count': 0,
                    'total_ctr': 0,
                    'total_roas': 0
                }
            
            platforms[platform]['count'] += 1
            platforms[platform]['total_ctr'] += ad['ctr']
            platforms[platform]['total_roas'] += ad['roas']
        
        # Calculate averages
        for platform, data in platforms.items():
            data['avg_ctr'] = round(data['total_ctr'] / data['count'], 2)
            data['avg_roas'] = round(data['total_roas'] / data['count'], 2)
            del data['total_ctr']
            del data['total_roas']
        
        return platforms
