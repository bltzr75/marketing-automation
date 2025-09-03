"""
Shared API credit manager for marketing automation platform
Tracks Gemini usage across all components with rate limiting
Adapted for marketing campaign management
"""

import time
import threading
import json
import os
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CreditManager:
    """
    Singleton credit manager for API usage across all components
    Tracks usage, enforces rate limits for Gemini free tier
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Ensure only one instance exists"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize only once"""
        if self._initialized:
            return
            
        # Core tracking
        self.total_requests = 0
        self.total_tokens = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        
        # Rate limiting (15 RPM for Gemini free tier)
        self.rpm_limit = 15
        self.tpm_limit = 1_000_000  # 1M tokens per minute
        self.call_times = []
        self.token_times = []
        
        # Component-specific tracking
        self.component_usage = {
            'collector': {'calls': 0, 'tokens': 0, 'errors': 0},
            'insight_agent': {'calls': 0, 'tokens': 0, 'errors': 0},
            'optimizer': {'calls': 0, 'tokens': 0, 'errors': 0},
            'analyzer': {'calls': 0, 'tokens': 0, 'errors': 0},
            'dspy': {'calls': 0, 'tokens': 0, 'errors': 0}
        }
        
        # Cost tracking (Gemini pricing)
        self.cost_per_million_input = 0.075
        self.cost_per_million_output = 0.30
        
        # Persistence
        self.data_dir = Path("data/logs")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.persistence_file = self.data_dir / "api_usage.json"
        
        self._usage_lock = threading.RLock()
        self._initialized = True
        
        logger.info(f"CreditManager initialized (RPM limit: {self.rpm_limit})")
    
    def check_rate_limit(self) -> bool:
        """Check if we can make a request without hitting limits"""
        now = time.time()
        
        # Clean old call times
        self.call_times = [t for t in self.call_times if now - t < 60]
        
        # Check RPM
        if len(self.call_times) >= self.rpm_limit:
            wait_time = 60 - (now - self.call_times[0]) + 1
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                now = time.time()
                self.call_times = [t for t in self.call_times if now - t < 60]
        
        # Check TPM
        self.token_times = [(t, tokens) for t, tokens in self.token_times if now - t < 60]
        recent_tokens = sum(tokens for _, tokens in self.token_times)
        
        if recent_tokens >= self.tpm_limit * 0.9:  # 90% threshold
            oldest_time = min(t for t, _ in self.token_times) if self.token_times else now
            wait_time = 60 - (now - oldest_time) + 1
            logger.warning(f"Token limit approaching, waiting {wait_time:.1f}s")
            time.sleep(wait_time)
        
        return True
    
    def track_request_start(self) -> None:
        """Mark the start of a request"""
        with self._usage_lock:
            self.check_rate_limit()
            self.call_times.append(time.time())
    
    def track_usage(self, 
                   input_tokens: int = 0,
                   output_tokens: int = 0,
                   component: str = 'other',
                   success: bool = True) -> None:
        """Track API usage"""
        with self._usage_lock:
            if success:
                self.total_requests += 1
                self.total_tokens += input_tokens + output_tokens
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                
                # Track for TPM
                self.token_times.append((time.time(), input_tokens + output_tokens))
                
                # Update component stats
                if component in self.component_usage:
                    self.component_usage[component]['calls'] += 1
                    self.component_usage[component]['tokens'] += input_tokens + output_tokens
            else:
                if component in self.component_usage:
                    self.component_usage[component]['errors'] += 1
            
            # Periodic save
            if self.total_requests % 10 == 0:
                self._save_usage()
    
    def get_usage_stats(self) -> Dict:
        """Get comprehensive usage statistics"""
        with self._usage_lock:
            # Calculate costs
            input_cost = (self.total_input_tokens * self.cost_per_million_input) / 1_000_000
            output_cost = (self.total_output_tokens * self.cost_per_million_output) / 1_000_000
            
            return {
                'total_requests': self.total_requests,
                'total_tokens': self.total_tokens,
                'estimated_cost': input_cost + output_cost,
                'component_breakdown': self.component_usage,
                'current_rpm': len([t for t in self.call_times if time.time() - t < 60])
            }
    
    def _save_usage(self) -> None:
        """Save usage data to file"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'stats': self.get_usage_stats()
            }
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save usage data: {e}")

# Global singleton getter
def get_credit_manager() -> CreditManager:
    """Get the singleton instance"""
    return CreditManager()
