"""Test configuration to run without external dependencies"""
import os

# Disable database for unit tests
os.environ['SKIP_DB_INIT'] = 'true'

def use_mock_db():
    """Configure tests to use mock database"""
    os.environ['DATABASE_URL'] = 'postgresql://mock:mock@mock/mock'
