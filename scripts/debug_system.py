#!/usr/bin/env python3
"""
System debug script - identifies issues without fixing them
Run this to understand what's working and what's not
"""

import subprocess
import os
import sys
import json
import psycopg2
import requests
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check environment variables"""
    print("\n=== Environment Variables ===")
    env_vars = ['DATABASE_URL', 'GEMINI_API_KEY', 'SLACK_WEBHOOK_URL']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive data
            if 'KEY' in var or 'WEBHOOK' in var:
                print(f"✓ {var}: ***SET***")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: NOT SET")

def check_local_postgres():
    """Check if local PostgreSQL is running"""
    print("\n=== Local PostgreSQL Check ===")
    try:
        result = subprocess.run(['systemctl', 'status', 'postgresql'], 
                              capture_output=True, text=True)
        if 'active (running)' in result.stdout:
            print("⚠️  Local PostgreSQL is running on port 5432")
            print("   This will conflict with Docker PostgreSQL")
            print("   Run: sudo systemctl stop postgresql")
        else:
            print("✓ Local PostgreSQL is not running")
    except:
        print("? Could not check systemctl (may not be systemd)")
    
    # Check port 5432
    try:
        result = subprocess.run(['ss', '-tulpn'], capture_output=True, text=True)
        if ':5432' in result.stdout:
            print("⚠️  Something is listening on port 5432")
        else:
            print("✓ Port 5432 is free")
    except:
        print("? Could not check port status")

def check_docker_services():
    """Check Docker containers"""
    print("\n=== Docker Services ===")
    try:
        result = subprocess.run(['sudo', 'docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'], 
                              capture_output=True, text=True)
        print(result.stdout)
        
        # Check specific services
        services = ['postgres', 'grafana', 'n8n']

        for service in services:
            if service in result.stdout:
                print(f"✓ {service} is running")
            else:
                print(f"✗ {service} is not running")
    except Exception as e:
        print(f"✗ Docker check failed: {e}")

def check_database():
    """Check database connection and tables"""
    print("\n=== Database Check ===")
    try:
        conn = psycopg2.connect("postgresql://user:pass@localhost/campaigns")
        cur = conn.cursor()
        
        # Check tables
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print(f"✓ Connected to database")
        print(f"  Tables: {[t[0] for t in tables]}")
        
        # Check data
        cur.execute("SELECT COUNT(*) FROM campaign_metrics")
        count = cur.fetchone()[0]
        print(f"  Campaign metrics: {count} rows")
        
        conn.close()
    except Exception as e:
        print(f"✗ Database error: {e}")

def check_api():
    """Check API endpoints"""
    print("\n=== API Check ===")
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        print(f"✓ API is running on port 8000")
        print(f"  Health check: {response.status_code}")
        
        # Check each endpoint
        endpoints = [
            ('GET', '/'),
            ('GET', '/api/alerts'),
            ('GET', '/api/usage'),
        ]
        
        for method, endpoint in endpoints:
            try:
                if method == 'GET':
                    r = requests.get(f"http://localhost:8000{endpoint}", timeout=2)
                print(f"  {method} {endpoint}: {r.status_code}")
            except:
                print(f"  {method} {endpoint}: FAILED")
                
    except requests.exceptions.ConnectionError:
        print("✗ API is not running")
        print("  Start with: python3 -m src.api.endpoints")

def check_grafana():
    """Check Grafana status"""
    print("\n=== Grafana Check ===")
    try:
        response = requests.get("http://localhost:3000", timeout=2)
        print(f"✓ Grafana is running on port 3000")
        
        # Check dashboard file
        dashboard_file = Path("dashboards/campaign_performance.json")
        if dashboard_file.exists():
            with open(dashboard_file) as f:
                dashboard = json.load(f)
                # Check structure
                if 'title' in dashboard:
                    print(f"  Dashboard title: {dashboard['title']}")
                elif 'dashboard' in dashboard and 'title' in dashboard['dashboard']:
                    print(f"  Dashboard title: {dashboard['dashboard']['title']}")
                    print("  ⚠️  Dashboard wrapped in 'dashboard' object (provisioning issue)")
                else:
                    print("  ⚠️  Dashboard title not found")
        else:
            print("✗ Dashboard file not found")
            
    except requests.exceptions.ConnectionError:
        print("✗ Grafana is not running")

def check_pydantic_version():
    """Check Pydantic version and potential issues"""
    print("\n=== Pydantic Version ===")
    try:
        import pydantic
        print(f"  Version: {pydantic.__version__}")
        
        # Check for v1 vs v2 issues
        if pydantic.__version__.startswith('2'):
            print("  ✓ Using Pydantic v2")
            print("  Note: Use model_dump() instead of dict()")
            print("  Note: Use ConfigDict instead of Config class")
        else:
            print("  Using Pydantic v1")
    except:
        print("✗ Pydantic not installed")

def check_reports():
    """Check report generation"""
    print("\n=== Report Generation ===")
    reports_dir = Path("data/reports")
    if reports_dir.exists():
        reports = list(reports_dir.glob("*.html"))
        print(f"✓ Reports directory exists")
        print(f"  HTML reports: {len(reports)}")
        if reports:
            latest = max(reports, key=lambda p: p.stat().st_mtime)
            print(f"  Latest: {latest.name}")
    else:
        print("✗ Reports directory not found")

def main():
    print("=" * 50)
    print("Marketing Automation Platform - System Debug")
    print("=" * 50)
    
    check_environment()
    check_local_postgres()
    check_docker_services()
    check_database()
    check_api()
    check_grafana()
    check_pydantic_version()
    check_reports()
    
    print("\n" + "=" * 50)
    print("Debug complete. Check ⚠️ warnings and ✗ errors above.")
    print("\nRecommended startup order:")
    print("1. sudo systemctl stop postgresql  # Stop local PostgreSQL")
    print("2. sudo docker-compose up -d postgres grafana n8n")
    print("3. python3 -c 'from src.storage.db_manager import DatabaseManager; DatabaseManager()'")
    print("4. python3 -m src.api.endpoints  # In one terminal")
    print("5. python3 run_tests.py  # In another terminal")

if __name__ == "__main__":
    main()
