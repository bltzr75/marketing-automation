"""
Alert monitoring and notification system
Single responsibility: Monitor thresholds and send alerts
"""

import os
import json
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime

from src.models.schemas import CampaignMetrics, Alert
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AlertManager:
    """Manages threshold monitoring and alerts"""
    
    def __init__(self, slack_webhook: Optional[str] = None):
        self.slack_webhook = slack_webhook or os.getenv('SLACK_WEBHOOK_URL')
        
        # Configurable thresholds
        self.thresholds = {
            'budget_utilization': 80,  # %
            'ctr_drop': 20,  # % decrease
            'daily_spend_spike': 150,  # % of average
            'low_roas': 2.0  # Minimum ROAS
        }
        
        self.alerts_sent = []
    
    def check_metrics(self, current: List[CampaignMetrics], 
                     historical: Optional[List[CampaignMetrics]] = None) -> List[Alert]:
        """Check metrics against thresholds"""
        alerts = []
        
        for metric in current:
            # Budget alert
            if metric.budget_utilization > self.thresholds['budget_utilization']:
                alerts.append(Alert(
                    alert_type='budget',
                    severity='warning',
                    metric_name='budget_utilization',
                    current_value=metric.budget_utilization,
                    threshold_value=self.thresholds['budget_utilization'],
                    message=f"Campaign {metric.campaign_id} at {metric.budget_utilization:.1f}% budget"
                ))
            
            # ROAS alert
            if metric.roas < self.thresholds['low_roas']:
                alerts.append(Alert(
                    alert_type='performance',
                    severity='warning',
                    metric_name='roas',
                    current_value=metric.roas,
                    threshold_value=self.thresholds['low_roas'],
                    message=f"Campaign {metric.campaign_id} ROAS below target: {metric.roas:.2f}"
                ))
        
        # Send notifications for new alerts
        self._send_notifications(alerts)
        
        return alerts
    
    def _send_notifications(self, alerts: List[Alert]):
        """Send alert notifications"""
        if not self.slack_webhook:
            logger.info(f"No Slack webhook configured, {len(alerts)} alerts logged only")
            return
        
        for alert in alerts:
            # Avoid duplicate alerts
            alert_key = f"{alert.alert_type}_{alert.metric_name}_{alert.current_value}"
            if alert_key in self.alerts_sent:
                continue
            
            # Send to Slack
            self._send_slack_alert(alert)
            self.alerts_sent.append(alert_key)
            
            # Keep list size manageable
            if len(self.alerts_sent) > 100:
                self.alerts_sent = self.alerts_sent[-50:]
    
    def _send_slack_alert(self, alert: Alert):
        """Send alert to Slack"""
        icon = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'critical': '🔴'
        }.get(alert.severity, '📊')
        
        message = {
            'text': f"{icon} {alert.message}",
            'attachments': [{
                'color': {'info': 'good', 'warning': 'warning', 'critical': 'danger'}.get(alert.severity),
                'fields': [
                    {'title': 'Metric', 'value': alert.metric_name, 'short': True},
                    {'title': 'Current', 'value': f"{alert.current_value:.2f}", 'short': True},
                    {'title': 'Threshold', 'value': f"{alert.threshold_value:.2f}", 'short': True},
                    {'title': 'Type', 'value': alert.alert_type, 'short': True}
                ]
            }]
        }
        
        try:
            response = requests.post(self.slack_webhook, json=message)
            if response.status_code == 200:
                logger.info(f"Alert sent to Slack: {alert.message}")
            else:
                logger.error(f"Failed to send Slack alert: {response.status_code}")
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
