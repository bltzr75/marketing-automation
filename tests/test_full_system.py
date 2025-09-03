"""Full system integration test including reports"""

import unittest
import time
import json
from pathlib import Path

class TestFullSystem(unittest.TestCase):
    
    def test_complete_workflow(self):
        """Test the complete workflow from collection to report"""
        
        # 1. Import and run collection
        from src.collectors.collector import CampaignCollector
        from src.storage.db_manager import DatabaseManager
        
        collector = CampaignCollector(use_mock=True)
        db = DatabaseManager()
        
        metrics = collector.collect_all()
        self.assertGreater(len(metrics), 0)
        
        inserted = db.insert_metrics(metrics)
        self.assertEqual(inserted, len(metrics))
        
        # 2. Generate insights
        from src.agents.insight_agent import PerformanceInsightAgent
        
        agent = PerformanceInsightAgent()
        insights = agent.analyze_performance(metrics)
        self.assertIsNotNone(insights.summary)
        
        # 3. Generate report
        from src.reports.generator import ReportGenerator
        
        generator = ReportGenerator()
        
        # Convert metrics for report
        metrics_dict = []
        for m in metrics:
            metrics_dict.append({
                'campaign_id': m.campaign_id,
                'platform': m.platform,
                'ctr': m.ctr,
                'roas': m.roas,
                'daily_spend': m.daily_spend,
                'revenue': m.revenue,
                'budget_utilization': m.budget_utilization
            })
        
        html_path = generator.generate_html_report(insights, metrics_dict)
        self.assertTrue(Path(html_path).exists())
        
        json_summary = generator.generate_summary_json(insights, metrics_dict)
        self.assertIn('kpis', json_summary)
        
        print(f"\n✓ Full workflow complete")
        print(f"✓ HTML Report: {html_path}")
        print(f"✓ Total campaigns: {len(metrics)}")
        print(f"✓ Avg ROAS: {json_summary['kpis']['avg_roas']:.2f}")

if __name__ == '__main__':
    unittest.main()
