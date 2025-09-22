"""
Unit tests for API endpoints.
"""
import pytest
import json
import sys
import os
from httpx import AsyncClient

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.models import User, Chat, Message
from app.auth import hash_password

async def get_auth_headers(simple_async_client, test_user_data):
    """Helper function to get authentication headers."""
    # Register and login to get token
    await simple_async_client.post("/api/users/register", json=test_user_data)
    login_response = await simple_async_client.post("/api/users/login", json=test_user_data)
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestUserEndpoints:
    """Test user-related API endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_user(self, simple_async_client):
        """Test user registration."""
        user_data = {
            "username": "testuser_api_1",
            "password": "testpassword123"
        }
        
        response = await simple_async_client.post("/api/users/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser_api_1"
        assert "id" in data
        assert "password_hash" not in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, simple_async_client):
        """Test registration with duplicate username."""
        user_data = {
            "username": "testuser_api_2",
            "password": "testpassword123"
        }
        
        # Register first user
        await simple_async_client.post("/api/users/register", json=user_data)
        
        # Try to register with same username
        response = await simple_async_client.post("/api/users/register", json=user_data)
        
        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_valid_credentials(self, simple_async_client):
        """Test login with valid credentials."""
        user_data = {
            "username": "testuser_api_3",
            "password": "testpassword123"
        }
        
        # Register user
        await simple_async_client.post("/api/users/register", json=user_data)
        
        # Login
        response = await simple_async_client.post("/api/users/login", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, simple_async_client):
        """Test login with invalid credentials."""
        user_data = {
            "username": "testuser_api_4",
            "password": "testpassword123"
        }
        
        # Register user
        await simple_async_client.post("/api/users/register", json=user_data)
        
        # Try to login with wrong password
        invalid_data = {
            "username": "testuser_api_4",
            "password": "wrongpassword"
        }
        
        response = await simple_async_client.post("/api/users/login", json=invalid_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, simple_async_client, test_user_data):
        """Test getting current user info."""
        headers = await get_auth_headers(simple_async_client, test_user_data)
        response = await simple_async_client.get("/api/users/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "password_hash" not in data
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, simple_async_client):
        """Test getting current user without authentication."""
        response = await simple_async_client.get("/api/users/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_search_users(self, simple_async_client, test_user_data):
        """Test user search functionality."""
        # Create test users
        users_data = [
            {"username": "alice", "password": "password123"},
            {"username": "alex", "password": "password123"},
            {"username": "bob", "password": "password123"}
        ]
        
        for user_data in users_data:
            await simple_async_client.post("/api/users/register", json=user_data)
        
        # Get auth headers
        headers = await get_auth_headers(simple_async_client, test_user_data)
        
        # Search for users with "al"
        response = await simple_async_client.get("/api/users/search/al", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        usernames = [user["username"] for user in data]
        assert "alice" in usernames
        assert "alex" in usernames


class TestChatEndpoints:
    """Test chat-related API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_public_chat(self, simple_async_client, test_user_data):
        """Test creating a public chat."""
        headers = await get_auth_headers(simple_async_client, test_user_data)
        chat_data = {"name": "Test Chat"}
        
        response = await simple_async_client.post(
            "/api/chats/",
            params=chat_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Chat"
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_create_private_chat(self, simple_async_client, test_user_data):
        """Test creating a private chat."""
        headers = await get_auth_headers(simple_async_client, test_user_data)
        
        # Create another user
        user_data = {"username": "otheruser", "password": "password123"}
        await simple_async_client.post("/api/users/register", json=user_data)
        
        # Search for the user to get their ID
        search_response = await simple_async_client.get("/api/users/search/otheruser", headers=headers)
        assert search_response.status_code == 200
        users = search_response.json()
        assert len(users) == 1
        other_user_id = users[0]["id"]
        
        # Create private chat with the other user
        response = await simple_async_client.post(
            "/api/chats/",
            params={"user_id": other_user_id},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Chat with otheruser" in data["name"]
    
    @pytest.mark.asyncio
    async def test_get_chats(self, simple_async_client, test_user_data):
        """Test getting user's chats."""
        headers = await get_auth_headers(simple_async_client, test_user_data)
        
        # Create a chat
        await simple_async_client.post(
            "/api/chats/",
            params={"name": "Test Chat"},
            headers=headers
        )
        
        response = await simple_async_client.get("/api/chats/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Test Chat"
    
    @pytest.mark.asyncio
    async def test_get_chats_unauthorized(self, simple_async_client):
        """Test getting chats without authentication."""
        response = await simple_async_client.get("/api/chats/")
        
        assert response.status_code == 401


class TestMessageEndpoints:
    """Test message-related API endpoints."""
    
    @pytest.mark.asyncio
    async def test_send_message(self, simple_async_client, test_user_data):
        """Test sending a message."""
        headers = await get_auth_headers(simple_async_client, test_user_data)
        
        # Create a chat first
        chat_response = await simple_async_client.post(
            "/api/chats/",
            params={"name": "Test Chat"},
            headers=headers
        )
        chat_id = chat_response.json()["id"]
        
        message_data = {
            "chat_id": chat_id,
            "content": "Hello, world!"
        }
        
        response = await simple_async_client.post(
            "/api/messages/",
            json=message_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hello, world!"
        assert data["chat_id"] == chat_id
        assert "id" in data
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_get_messages(self, simple_async_client, test_user_data):
        """Test getting messages from a chat."""
        headers = await get_auth_headers(simple_async_client, test_user_data)
        
        # Create a chat and send a message
        chat_response = await simple_async_client.post(
            "/api/chats/",
            params={"name": "Test Chat"},
            headers=headers
        )
        chat_id = chat_response.json()["id"]
        
        message_data = {
            "chat_id": chat_id,
            "content": "Test message"
        }
        await simple_async_client.post(
            "/api/messages/",
            json=message_data,
            headers=headers
        )
        
        # Get messages
        response = await simple_async_client.get(
            f"/api/messages/{chat_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Test message"
    
    @pytest.mark.asyncio
    async def test_send_message_unauthorized(self, simple_async_client):
        """Test sending message without authentication."""
        message_data = {
            "chat_id": 1,
            "content": "Hello, world!"
        }
        
        response = await simple_async_client.post("/api/messages/", json=message_data)
        
        assert response.status_code == 401


class TestInputValidation:
    """Test input validation for API endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_empty_username(self, simple_async_client):
        """Test registration with empty username."""
        user_data = {
            "username": "",
            "password": "testpassword123"
        }
        
        response = await simple_async_client.post("/api/users/register", json=user_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_register_short_password(self, simple_async_client):
        """Test registration with short password."""
        user_data = {
            "username": "testuser_api_4",
            "password": "123"
        }
        
        response = await simple_async_client.post("/api/users/register", json=user_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_send_empty_message(self, simple_async_client, test_user_data):
        """Test sending empty message."""
        headers = await get_auth_headers(simple_async_client, test_user_data)
        
        # Create a chat first
        chat_response = await simple_async_client.post(
            "/api/chats/",
            params={"name": "Test Chat"},
            headers=headers
        )
        chat_id = chat_response.json()["id"]
        
        message_data = {
            "chat_id": chat_id,
            "content": ""
        }
        
        response = await simple_async_client.post(
            "/api/messages/",
            json=message_data,
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error
