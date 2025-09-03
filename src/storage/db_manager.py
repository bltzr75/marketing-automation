"""
PostgreSQL database manager
Single responsibility: Store and retrieve campaign metrics
"""

import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from src.models.schemas import CampaignMetrics
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL operations"""
    
    # Add at the beginning of __init__ method:
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or os.getenv(
            'DATABASE_URL',
            'postgresql://user:pass@localhost/campaigns'
        )
        
        # Skip DB init if in test mode without DB
        if os.getenv('SKIP_DB_INIT') == 'true':
            logger.info("Skipping database initialization (test mode)")
            return
            
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        conn = psycopg2.connect(self.connection_string)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    

    def _init_database(self):
        """Initialize database schema"""
        schema = """
        CREATE TABLE IF NOT EXISTS campaign_metrics (
            id SERIAL PRIMARY KEY,
            campaign_id VARCHAR(255),
            platform VARCHAR(50),
            timestamp TIMESTAMP,
            impressions INTEGER,
            clicks INTEGER,
            conversions INTEGER,
            ctr FLOAT,
            cpc FLOAT,
            roas FLOAT,
            daily_spend FLOAT,
            daily_budget_limit FLOAT,
            budget_utilization FLOAT,
            revenue FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
        ON campaign_metrics(timestamp);
        
        CREATE INDEX IF NOT EXISTS idx_metrics_campaign 
        ON campaign_metrics(campaign_id);
        
        CREATE TABLE IF NOT EXISTS system_health (
            id SERIAL PRIMARY KEY,
            service VARCHAR(100),
            status VARCHAR(20),
            last_check TIMESTAMP,
            success_rate FLOAT,
            error_message TEXT
        );
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(schema)
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

        


    def insert_metrics(self, metrics: List[CampaignMetrics]) -> int:
        """Insert campaign metrics"""
        if not metrics:
            return 0
        
        query = """
        INSERT INTO campaign_metrics (
            campaign_id, platform, timestamp, impressions, clicks, 
            conversions, ctr, cpc, roas, daily_spend, 
            daily_budget_limit, budget_utilization, revenue
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for metric in metrics:
                    cur.execute(query, (
                        metric.campaign_id,
                        metric.platform,
                        metric.timestamp,
                        metric.impressions,
                        metric.clicks,
                        metric.conversions,
                        metric.ctr,
                        metric.cpc,
                        metric.roas,
                        metric.daily_spend,
                        metric.daily_budget_limit,
                        metric.budget_utilization,
                        metric.revenue
                    ))
        
        logger.info(f"Inserted {len(metrics)} metrics")
        return len(metrics)
    
    def get_recent_metrics(self, hours: int = 24) -> List[Dict]:
        """Get recent metrics"""
        query = """
        SELECT * FROM campaign_metrics 
        WHERE timestamp > %s 
        ORDER BY timestamp DESC
        """
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (cutoff,))
                return cur.fetchall()
    
    def get_campaign_history(self, campaign_id: str, days: int = 7) -> List[Dict]:
        """Get campaign history"""
        query = """
        SELECT * FROM campaign_metrics 
        WHERE campaign_id = %s AND timestamp > %s
        ORDER BY timestamp
        """
        
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (campaign_id, cutoff))
                return cur.fetchall()
