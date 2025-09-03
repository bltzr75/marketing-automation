#!/bin/bash

# Quick start script for the marketing automation platform

echo "🚀 Starting Marketing Automation Platform"

# Check for required environment variables
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  Warning: GEMINI_API_KEY not set, will use mock data"
fi

# Create necessary directories
mkdir -p data/logs data/reports

# Start services
echo "📦 Starting Docker services..."
docker-compose up -d postgres grafana

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
sleep 10

# Initialize database
echo "🗄️  Initializing database..."
python -c "from src.storage.db_manager import DatabaseManager; DatabaseManager()"

# Run initial data collection
echo "📊 Running initial data collection..."
python -c "from src.main import run_pipeline; run_pipeline()"

echo "✅ Platform ready!"
echo "   - Grafana: http://localhost:3000 (admin/admin)"
echo "   - n8n: http://localhost:5678 (admin/admin)"
echo "   - Logs: data/logs/"
echo "   - Reports: data/reports/"
