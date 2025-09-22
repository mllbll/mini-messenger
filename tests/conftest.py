"""
Pytest configuration and fixtures for mini-messenger tests.
"""
import asyncio
import pytest
import httpx
import os
import sys
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from faker import Faker

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.db import Base, get_db
from app.main import app
from app.auth import create_access_token
from app.models import User, Chat, ChatMember, Message

fake = Faker()

# Test database URL
TEST_DATABASE_URL = "postgresql+psycopg2://test:test@localhost:5432/test_messenger"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for testing."""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def test_engine(postgres_container):
    """Create test database engine."""
    database_url = postgres_container.get_connection_url()
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_db_session(test_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # Clean up data after each test
        session.rollback()
        session.close()

@pytest.fixture(autouse=True)
def cleanup_database(test_db_session):
    """Clean up database after each test."""
    yield
    # Clean up all data after each test
    try:
        test_db_session.rollback()  # Rollback any pending transactions
        test_db_session.query(Message).delete()
        test_db_session.query(ChatMember).delete()
        test_db_session.query(Chat).delete()
        test_db_session.query(User).delete()
        test_db_session.commit()
    except Exception:
        test_db_session.rollback()  # Rollback on any error

@pytest.fixture
def client(test_db_session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with httpx.Client(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
async def async_client(test_db_session):
    """Create async test client."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
async def simple_async_client():
    """Create simple async test client without database dependency."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def test_user_data():
    """Generate test user data."""
    import time
    return {
        "username": f"testuser_{int(time.time() * 1000)}",
        "password": fake.password(length=12)
    }

@pytest.fixture
def test_user_token(test_user_data):
    """Create test user token."""
    return create_access_token({"sub": test_user_data["username"]})

@pytest.fixture
def auth_headers(test_user_token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {test_user_token}"}

@pytest.fixture
def sample_chat_data():
    """Generate sample chat data."""
    return {
        "name": fake.sentence(nb_words=3)
    }

@pytest.fixture
def sample_message_data():
    """Generate sample message data."""
    return {
        "content": fake.text(max_nb_chars=200)
    }

@pytest.fixture
def websocket_url():
    """WebSocket URL for testing."""
    return "ws://localhost:8000/ws/chat/1"

# Performance testing fixtures
@pytest.fixture
def performance_config():
    """Configuration for performance tests."""
    return {
        "concurrent_users": 100,
        "duration_seconds": 60,
        "ramp_up_seconds": 10,
        "message_rate_per_second": 10
    }

# Security testing fixtures
@pytest.fixture
def malicious_inputs():
    """Malicious inputs for security testing."""
    return [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "../../etc/passwd",
        "{{7*7}}",
        "javascript:alert(1)",
        "data:text/html,<script>alert('xss')</script>"
    ]
