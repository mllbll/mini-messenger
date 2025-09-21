"""
Unit tests for API endpoints.
"""
import pytest
import json
from httpx import AsyncClient
from backend.app.models import User, Chat, Message
from backend.app.auth import hash_password


class TestUserEndpoints:
    """Test user-related API endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_user(self, async_client: AsyncClient):
        """Test user registration."""
        user_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        response = await async_client.post("/api/users/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert "id" in data
        assert "password_hash" not in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, async_client: AsyncClient):
        """Test registration with duplicate username."""
        user_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        # Register first user
        await async_client.post("/api/users/register", json=user_data)
        
        # Try to register with same username
        response = await async_client.post("/api/users/register", json=user_data)
        
        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_valid_credentials(self, async_client: AsyncClient):
        """Test login with valid credentials."""
        user_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        # Register user
        await async_client.post("/api/users/register", json=user_data)
        
        # Login
        response = await async_client.post("/api/users/login", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client: AsyncClient):
        """Test login with invalid credentials."""
        user_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        # Register user
        await async_client.post("/api/users/register", json=user_data)
        
        # Try to login with wrong password
        invalid_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = await async_client.post("/api/users/login", json=invalid_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, async_client: AsyncClient, auth_headers):
        """Test getting current user info."""
        response = await async_client.get("/api/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "password_hash" not in data
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, async_client: AsyncClient):
        """Test getting current user without authentication."""
        response = await async_client.get("/api/users/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_search_users(self, async_client: AsyncClient, auth_headers):
        """Test user search functionality."""
        # Create test users
        users_data = [
            {"username": "alice", "password": "password123"},
            {"username": "alex", "password": "password123"},
            {"username": "bob", "password": "password123"}
        ]
        
        for user_data in users_data:
            await async_client.post("/api/users/register", json=user_data)
        
        # Search for users with "al"
        response = await async_client.get("/api/users/search/al", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        usernames = [user["username"] for user in data]
        assert "alice" in usernames
        assert "alex" in usernames


class TestChatEndpoints:
    """Test chat-related API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_public_chat(self, async_client: AsyncClient, auth_headers):
        """Test creating a public chat."""
        chat_data = {"name": "Test Chat"}
        
        response = await async_client.post(
            "/api/chats/",
            params=chat_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Chat"
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_create_private_chat(self, async_client: AsyncClient, auth_headers):
        """Test creating a private chat."""
        # Create another user
        user_data = {"username": "otheruser", "password": "password123"}
        await async_client.post("/api/users/register", json=user_data)
        
        # Get the user ID (we'll need to implement this endpoint)
        # For now, we'll assume user_id=2
        response = await async_client.post(
            "/api/chats/",
            params={"user_id": 2},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Chat with otheruser" in data["name"]
    
    @pytest.mark.asyncio
    async def test_get_chats(self, async_client: AsyncClient, auth_headers):
        """Test getting user's chats."""
        # Create a chat
        await async_client.post(
            "/api/chats/",
            params={"name": "Test Chat"},
            headers=auth_headers
        )
        
        response = await async_client.get("/api/chats/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Test Chat"
    
    @pytest.mark.asyncio
    async def test_get_chats_unauthorized(self, async_client: AsyncClient):
        """Test getting chats without authentication."""
        response = await async_client.get("/api/chats/")
        
        assert response.status_code == 401


class TestMessageEndpoints:
    """Test message-related API endpoints."""
    
    @pytest.mark.asyncio
    async def test_send_message(self, async_client: AsyncClient, auth_headers):
        """Test sending a message."""
        # Create a chat first
        chat_response = await async_client.post(
            "/api/chats/",
            params={"name": "Test Chat"},
            headers=auth_headers
        )
        chat_id = chat_response.json()["id"]
        
        message_data = {
            "chat_id": chat_id,
            "content": "Hello, world!"
        }
        
        response = await async_client.post(
            "/api/messages/",
            json=message_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hello, world!"
        assert data["chat_id"] == chat_id
        assert "id" in data
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_get_messages(self, async_client: AsyncClient, auth_headers):
        """Test getting messages from a chat."""
        # Create a chat and send a message
        chat_response = await async_client.post(
            "/api/chats/",
            params={"name": "Test Chat"},
            headers=auth_headers
        )
        chat_id = chat_response.json()["id"]
        
        message_data = {
            "chat_id": chat_id,
            "content": "Test message"
        }
        await async_client.post(
            "/api/messages/",
            json=message_data,
            headers=auth_headers
        )
        
        # Get messages
        response = await async_client.get(
            f"/api/messages/{chat_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Test message"
    
    @pytest.mark.asyncio
    async def test_send_message_unauthorized(self, async_client: AsyncClient):
        """Test sending message without authentication."""
        message_data = {
            "chat_id": 1,
            "content": "Hello, world!"
        }
        
        response = await async_client.post("/api/messages/", json=message_data)
        
        assert response.status_code == 401


class TestInputValidation:
    """Test input validation for API endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_empty_username(self, async_client: AsyncClient):
        """Test registration with empty username."""
        user_data = {
            "username": "",
            "password": "testpassword123"
        }
        
        response = await async_client.post("/api/users/register", json=user_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_register_short_password(self, async_client: AsyncClient):
        """Test registration with short password."""
        user_data = {
            "username": "testuser",
            "password": "123"
        }
        
        response = await async_client.post("/api/users/register", json=user_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_send_empty_message(self, async_client: AsyncClient, auth_headers):
        """Test sending empty message."""
        # Create a chat first
        chat_response = await async_client.post(
            "/api/chats/",
            params={"name": "Test Chat"},
            headers=auth_headers
        )
        chat_id = chat_response.json()["id"]
        
        message_data = {
            "chat_id": chat_id,
            "content": ""
        }
        
        response = await async_client.post(
            "/api/messages/",
            json=message_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
