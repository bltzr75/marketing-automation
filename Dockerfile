FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/

# Create data directories
RUN mkdir -p data/logs data/reports

CMD ["python", "-m", "src.api.endpoints"]