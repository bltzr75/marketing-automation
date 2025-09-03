#!/bin/bash

echo "🚀 Starting API server..."

# Check if PostgreSQL is running
if ! sudo docker ps | grep -q postgres-campaigns; then
    echo "⚠️  PostgreSQL not running. Starting..."
    sudo docker run -d \
        --name postgres-campaigns \
        -e POSTGRES_USER=user \
        -e POSTGRES_PASSWORD=pass \
        -e POSTGRES_DB=campaigns \
        -p 5432:5432 \
        postgres:14-alpine
    sleep 5
fi

# Activate virtual environment
source venv/bin/activate

# Run API
echo "📡 API starting on http://localhost:8000"
python3 -m src.api.endpoints
