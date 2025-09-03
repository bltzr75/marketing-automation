"""
Lightweight vector store without external dependencies
Single responsibility: Store and search ads using simple text matching
"""

import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class AdVectorStoreLite:
    """Lightweight ad storage without vector embeddings"""
    
    def __init__(self, data_dir: str = "./data/ads"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ads_file = self.data_dir / "ads.json"
        self.ads = self._load_ads()
    
    def _load_ads(self) -> Dict:
        """Load ads from file"""
        if self.ads_file.exists():
            with open(self.ads_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_ads(self):
        """Save ads to file"""
        with open(self.ads_file, 'w') as f:
            json.dump(self.ads, f, indent=2)
    
    def store_ad(self, ad) -> None:
        """Store ad content"""
        self.ads[ad.ad_id] = {
            'ad_id': ad.ad_id,
            'campaign_id': ad.campaign_id,
            'platform': ad.platform,
            'headline': ad.headline,
            'description': ad.description,
            'cta': ad.cta,
            'ctr': ad.ctr,
            'conversions': ad.conversions,
            'roas': ad.roas,
            'created_at': ad.created_at.isoformat(),
            'text': f"{ad.headline} {ad.description} {ad.cta}".lower()
        }
        self._save_ads()
        logger.info(f"Stored ad {ad.ad_id}")
    
    def find_similar_ads(self, query: str, 
                        min_performance: Optional[Dict] = None,
                        limit: int = 5) -> List[Dict]:
        """Find similar ads using keyword matching"""
        query_words = set(query.lower().split())
        scores = []
        
        for ad_id, ad in self.ads.items():
            # Check performance filters
            if min_performance:
                if 'min_ctr' in min_performance and ad['ctr'] < min_performance['min_ctr']:
                    continue
                if 'min_roas' in min_performance and ad['roas'] < min_performance['min_roas']:
                    continue
            
            # Calculate similarity (simple word overlap)
            ad_words = set(ad['text'].split())
            overlap = len(query_words.intersection(ad_words))
            if overlap > 0:
                score = overlap / len(query_words)
                scores.append((score, ad))
        
        # Sort by score and return top results
        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, ad in scores[:limit]:
            result = ad.copy()
            result['similarity_score'] = score
            del result['text']  # Remove internal field
            results.append(result)
        
        return results
    
    def get_top_performers(self, platform: Optional[str] = None, 
                          limit: int = 10) -> List[Dict]:
        """Get top performing ads"""
        ads = list(self.ads.values())
        
        if platform:
            ads = [a for a in ads if a['platform'] == platform]
        
        # Sort by combined metric (ROAS * CTR)
        ads.sort(key=lambda x: x['roas'] * x['ctr'], reverse=True)
        
        # Remove internal text field
        for ad in ads[:limit]:
            if 'text' in ad:
                del ad['text']
        
        return ads[:limit]
    
    def analyze_patterns(self) -> Dict:
        """Analyze patterns in successful ads"""
        if not self.ads:
            return {'status': 'No ads to analyze'}
        
        top_ads = self.get_top_performers(limit=20)
        
        if not top_ads:
            return {'status': 'No top performers found'}
        
        # Word frequency analysis
        word_freq = {}
        cta_freq = {}
        
        for ad in top_ads:
            # Headline words
            for word in ad.get('headline', '').lower().split():
                if len(word) > 3:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # CTAs
            cta = ad.get('cta', '')
            if cta:
                cta_freq[cta] = cta_freq.get(cta, 0) + 1
        
        # Calculate averages
        avg_ctr = sum(ad['ctr'] for ad in top_ads) / len(top_ads) if top_ads else 0
        avg_roas = sum(ad['roas'] for ad in top_ads) / len(top_ads) if top_ads else 0
        
        # Platform breakdown
        platforms = {}
        for ad in top_ads:
            p = ad['platform']
            if p not in platforms:
                platforms[p] = {'count': 0, 'total_ctr': 0, 'total_roas': 0}
            platforms[p]['count'] += 1
            platforms[p]['total_ctr'] += ad['ctr']
            platforms[p]['total_roas'] += ad['roas']
        
        for p in platforms:
            platforms[p]['avg_ctr'] = platforms[p]['total_ctr'] / platforms[p]['count']
            platforms[p]['avg_roas'] = platforms[p]['total_roas'] / platforms[p]['count']
            del platforms[p]['total_ctr']
            del platforms[p]['total_roas']
        
        return {
            'total_ads_analyzed': len(top_ads),
            'average_ctr': round(avg_ctr, 2),
            'average_roas': round(avg_roas, 2),
            'top_headline_words': sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10],
            'top_ctas': sorted(cta_freq.items(), key=lambda x: x[1], reverse=True)[:5],
            'platform_breakdown': platforms
        }
