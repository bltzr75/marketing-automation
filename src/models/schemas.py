"""
Pydantic models for data validation across the platform
"""

from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CampaignMetrics(BaseModel):
    """Campaign performance metrics"""
    campaign_id: str
    platform: str = Field(..., pattern="^(google_ads|meta|linkedin)$")
    timestamp: datetime
    
    # Performance metrics
    impressions: int = Field(ge=0)
    clicks: int = Field(ge=0)
    conversions: int = Field(ge=0)
    
    # Budget tracking
    daily_spend: float = Field(ge=0)
    daily_budget_limit: float = Field(ge=0)
    revenue: float = Field(default=0, ge=0)
    cpc: float = Field(ge=0)
    
    # Calculated fields - will be set by validators
    ctr: float = Field(default=0, ge=0, le=100)
    roas: float = Field(default=0, ge=0)
    budget_utilization: float = Field(default=0, ge=0, le=100)
    
    @model_validator(mode='after')
    def calculate_metrics(self):
        """Calculate derived metrics after all fields are set"""
        # Calculate CTR
        if self.impressions > 0:
            self.ctr = (self.clicks / self.impressions) * 100
        else:
            self.ctr = 0
        
        # Calculate ROAS
        if self.daily_spend > 0:
            self.roas = self.revenue / self.daily_spend
        else:
            self.roas = 0
        
        # Calculate budget utilization
        if self.daily_budget_limit > 0:
            self.budget_utilization = (self.daily_spend / self.daily_budget_limit) * 100
        else:
            self.budget_utilization = 0
        
        return self
    


class SystemHealth(BaseModel):
    """System health monitoring"""
    service: str
    status: str = Field(..., pattern="^(healthy|degraded|down)$")
    last_check: datetime
    success_rate: float = Field(ge=0, le=100)
    error_message: Optional[str] = None
    
class Alert(BaseModel):
    """Alert configuration and tracking"""
    alert_type: str = Field(..., pattern="^(budget|performance|system|anomaly)$")
    severity: str = Field(..., pattern="^(info|warning|critical)$")
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    

# Also update InsightReport to handle nested dicts properly:
class InsightReport(BaseModel):
    """Performance insight report structure"""
    report_id: str
    timestamp: datetime
    period_start: datetime
    period_end: datetime
    
    # Key findings - Changed to Any to accept nested dicts
    summary: str
    key_metrics: Dict[str, Any]  # Changed from Dict[str, float]
    trends: List[Dict[str, Any]]
    
    # Recommendations
    recommendations: List[str]
    action_items: List[Dict[str, str]]
    
    # Platform-specific insights
    platform_insights: Dict[str, str]
    
    # Cross-platform patterns
    patterns: List[str]
    anomalies: List[str]

class AdContent(BaseModel):
    """Ad content for similarity search"""
    ad_id: str
    campaign_id: str
    platform: str
    
    # Content
    headline: str
    description: str
    cta: str
    
    # Performance
    ctr: float
    conversions: int
    roas: float
    
    # Metadata
    created_at: datetime
    tags: List[str] = []
    
    model_config = ConfigDict(
        json_serializers={
            datetime: lambda v: v.isoformat()
        }
    )