"""
Bid optimization engine
Single responsibility: Calculate optimal bid adjustments based on performance
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np

from src.models.schemas import CampaignMetrics
from src.storage.db_manager import DatabaseManager

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class BidOptimizer:
    """Optimizes bids based on campaign performance"""
    
    def __init__(self):
        self.db = DatabaseManager()
        
        # Optimization parameters
        self.target_roas = 3.0
        self.max_bid_change = 0.25  # 25% max change per adjustment
        self.min_data_points = 7  # Minimum history needed
        
    def calculate_adjustments(self, metrics: List[CampaignMetrics]) -> List[Dict]:
        """Calculate bid adjustments for campaigns"""
        adjustments = []
        
        for metric in metrics:
            # Get historical data
            history = self.db.get_campaign_history(metric.campaign_id, days=7)
            
            if len(history) < self.min_data_points:
                logger.info(f"Insufficient data for {metric.campaign_id}")
                continue
            
            # Calculate adjustment
            adjustment = self._calculate_single_adjustment(metric, history)
            if adjustment:
                adjustments.append(adjustment)
        
        return adjustments
    
    def _calculate_single_adjustment(self, current: CampaignMetrics, 
                                    history: List[Dict]) -> Optional[Dict]:
        """Calculate adjustment for single campaign"""
        
        # Calculate average historical performance
        avg_roas = np.mean([h['roas'] for h in history])
        avg_ctr = np.mean([h['ctr'] for h in history])
        trend = self._calculate_trend(history)
        
        # Determine adjustment factor
        adjustment_factor = 0.0
        reason = []
        
        # ROAS-based adjustment
        if current.roas < self.target_roas * 0.7:
            # Poor performance - decrease bid
            adjustment_factor -= 0.15
            reason.append(f"ROAS below target ({current.roas:.2f} < {self.target_roas * 0.7:.2f})")
        elif current.roas > self.target_roas * 1.3:
            # Excellent performance - increase bid
            adjustment_factor += 0.20
            reason.append(f"ROAS exceeding target ({current.roas:.2f} > {self.target_roas * 1.3:.2f})")
        
        # CTR-based adjustment
        if current.ctr < avg_ctr * 0.8:
            adjustment_factor -= 0.10
            reason.append(f"CTR declining ({current.ctr:.2f}% < {avg_ctr * 0.8:.2f}%)")
        elif current.ctr > avg_ctr * 1.2:
            adjustment_factor += 0.10
            reason.append(f"CTR improving ({current.ctr:.2f}% > {avg_ctr * 1.2:.2f}%)")
        
        # Trend-based adjustment
        if trend < -0.2:
            adjustment_factor -= 0.05
            reason.append("Negative performance trend")
        elif trend > 0.2:
            adjustment_factor += 0.05
            reason.append("Positive performance trend")
        
        # Clamp adjustment
        adjustment_factor = max(-self.max_bid_change, min(adjustment_factor, self.max_bid_change))
        
        if abs(adjustment_factor) < 0.05:
            return None  # No significant adjustment needed
        
        # Calculate new bid
        current_bid = current.cpc * 1.2  # Estimate max bid from CPC
        new_bid = current_bid * (1 + adjustment_factor)
        
        return {
            'campaign_id': current.campaign_id,
            'platform': current.platform,
            'current_bid': round(current_bid, 2),
            'new_bid': round(new_bid, 2),
            'adjustment_percent': round(adjustment_factor * 100, 1),
            'reasons': reason,
            'current_roas': round(current.roas, 2),
            'target_roas': self.target_roas,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_trend(self, history: List[Dict]) -> float:
        """Calculate performance trend (-1 to 1)"""
        if len(history) < 2:
            return 0.0
        
        # Simple linear regression on ROAS
        x = np.arange(len(history))
        y = np.array([h['roas'] for h in history])
        
        # Normalize
        if np.std(y) == 0:
            return 0.0
        
        z = np.polyfit(x, y, 1)
        slope = z[0]
        
        # Normalize slope to -1 to 1 range
        max_slope = np.std(y) / len(history)
        if max_slope == 0:
            return 0.0
        
        return np.clip(slope / max_slope, -1, 1)
    
    def get_budget_reallocation(self, metrics: List[CampaignMetrics], 
                                total_budget: float) -> Dict:
        """Suggest budget reallocation across campaigns"""
        
        if not metrics:
            return {}
        
        # Calculate performance scores
        scores = {}
        for m in metrics:
            # Weighted score based on ROAS and volume
            volume_weight = min(m.daily_spend / 100, 1.0)  # Normalize by $100
            performance_weight = m.roas / self.target_roas
            scores[m.campaign_id] = performance_weight * (0.7 + 0.3 * volume_weight)
        
        # Calculate budget allocation
        total_score = sum(scores.values())
        if total_score == 0:
            return {}
        
        allocations = {}
        for campaign_id, score in scores.items():
            allocation = (score / total_score) * total_budget
            current = next((m.daily_spend for m in metrics if m.campaign_id == campaign_id), 0)
            
            allocations[campaign_id] = {
                'current_budget': round(current, 2),
                'recommended_budget': round(allocation, 2),
                'change': round(allocation - current, 2),
                'change_percent': round(((allocation - current) / current * 100) if current > 0 else 0, 1),
                'performance_score': round(score, 2)
            }
        
        return {
            'total_budget': total_budget,
            'allocations': allocations,
            'timestamp': datetime.now().isoformat()
        }
