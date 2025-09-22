"""
Integration tests for complete user workflows.
"""
import pytest
import asyncio
from httpx import AsyncClient


class TestCompleteUserWorkflow:
    """Test complete user workflows from registration to messaging."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_user_registration_to_messaging_workflow(self, simple_async_client: AsyncClient):
        """Test complete workflow: register -> login -> create chat -> send messages."""
        # Step 1: Register user
        user_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        register_response = await simple_async_client.post("/api/users/register", json=user_data)
        assert register_response.status_code == 200
        user_info = register_response.json()
        assert user_info["username"] == "testuser"
        
        # Step 2: Login
        login_response = await simple_async_client.post("/api/users/login", json=user_data)
        assert login_response.status_code == 200
        token_info = login_response.json()
        auth_headers = {"Authorization": f"Bearer {token_info['access_token']}"}
        
        # Step 3: Get current user info
        me_response = await simple_async_client.get("/api/users/me", headers=auth_headers)
        assert me_response.status_code == 200
        current_user = me_response.json()
        assert current_user["username"] == "testuser"
        
        # Step 4: Create a public chat
        chat_response = await simple_async_client.post(
            "/api/chats/",
            params={"name": "My Test Chat"},
            headers=auth_headers
        )
        assert chat_response.status_code == 200
        chat_info = chat_response.json()
        chat_id = chat_info["id"]
        assert chat_info["name"] == "My Test Chat"
        
        # Step 5: Send messages
        messages = [
            "Hello, world!",
            "This is a test message",
            "Testing the messaging system"
        ]
        
        for message_content in messages:
            message_response = await simple_async_client.post(
                "/api/messages/",
                json={"chat_id": chat_id, "content": message_content},
                headers=auth_headers
            )
            assert message_response.status_code == 200
            message_info = message_response.json()
            assert message_info["content"] == message_content
            assert message_info["chat_id"] == chat_id
        
        # Step 6: Retrieve messages
        messages_response = await simple_async_client.get(
            f"/api/messages/{chat_id}",
            headers=auth_headers
        )
        assert messages_response.status_code == 200
        retrieved_messages = messages_response.json()
        assert len(retrieved_messages) == 3
        
        # Verify message content
        message_contents = [msg["content"] for msg in retrieved_messages]
        for expected_content in messages:
            assert expected_content in message_contents
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_user_chat_workflow(self, simple_async_client: AsyncClient):
        """Test workflow with multiple users in the same chat."""
        # Create two users
        user1_data = {"username": "user1", "password": "password123"}
        user2_data = {"username": "user2", "password": "password123"}
        
        # Register both users
        await simple_async_client.post("/api/users/register", json=user1_data)
        await simple_async_client.post("/api/users/register", json=user2_data)
        
        # Login both users
        user1_login = await simple_async_client.post("/api/users/login", json=user1_data)
        user2_login = await simple_async_client.post("/api/users/login", json=user2_data)
        
        user1_token = user1_login.json()["access_token"]
        user2_token = user2_login.json()["access_token"]
        
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        # User1 creates a chat
        chat_response = await simple_async_client.post(
            "/api/chats/",
            params={"name": "Shared Chat"},
            headers=user1_headers
        )
        chat_id = chat_response.json()["id"]
        
        # Both users send messages
        user1_message = "Hello from user1!"
        user2_message = "Hello from user2!"
        
        # User1 sends message
        await simple_async_client.post(
            "/api/messages/",
            json={"chat_id": chat_id, "content": user1_message},
            headers=user1_headers
        )
        
        # User2 sends message
        await simple_async_client.post(
            "/api/messages/",
            json={"chat_id": chat_id, "content": user2_message},
            headers=user2_headers
        )
        
        # Both users should see all messages
        for headers in [user1_headers, user2_headers]:
            messages_response = await simple_async_client.get(
                f"/api/messages/{chat_id}",
                headers=headers
            )
            assert messages_response.status_code == 200
            messages = messages_response.json()
            assert len(messages) == 2
            
            message_contents = [msg["content"] for msg in messages]
            assert user1_message in message_contents
            assert user2_message in message_contents
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_private_chat_workflow(self, simple_async_client: AsyncClient):
        """Test private chat creation and messaging workflow."""
        # Create two users
        user1_data = {"username": "alice", "password": "password123"}
        user2_data = {"username": "bob", "password": "password123"}
        
        # Register both users
        await simple_async_client.post("/api/users/register", json=user1_data)
        await simple_async_client.post("/api/users/register", json=user2_data)
        
        # Login as user1
        user1_login = await simple_async_client.post("/api/users/login", json=user1_data)
        user1_token = user1_login.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        
        # User1 creates a private chat with user2
        # Note: This assumes user2 has ID 2 (after user1 with ID 1)
        private_chat_response = await simple_async_client.post(
            "/api/chats/",
            params={"user_id": 2},
            headers=user1_headers
        )
        assert private_chat_response.status_code == 200
        private_chat = private_chat_response.json()
        assert "Chat with bob" in private_chat["name"]
        
        # User1 sends a private message
        private_message = "This is a private message"
        message_response = await simple_async_client.post(
            "/api/messages/",
            json={"chat_id": private_chat["id"], "content": private_message},
            headers=user1_headers
        )
        assert message_response.status_code == 200
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_user_search_and_chat_creation_workflow(self, simple_async_client: AsyncClient):
        """Test workflow: search for user -> create chat -> send message."""
        # Create multiple users
        users_data = [
            {"username": "alice", "password": "password123"},
            {"username": "alex", "password": "password123"},
            {"username": "bob", "password": "password123"}
        ]
        
        for user_data in users_data:
            await simple_async_client.post("/api/users/register", json=user_data)
        
        # Login as alice
        alice_login = await simple_async_client.post("/api/users/login", json=users_data[0])
        alice_token = alice_login.json()["access_token"]
        alice_headers = {"Authorization": f"Bearer {alice_token}"}
        
        # Search for users with "al"
        search_response = await simple_async_client.get("/api/users/search/al", headers=alice_headers)
        assert search_response.status_code == 200
        search_results = search_response.json()
        
        # Should find alice and alex
        usernames = [user["username"] for user in search_results]
        assert "alice" in usernames
        assert "alex" in usernames
        assert "bob" not in usernames
        
        # Create a chat with alex (assuming alex has ID 2)
        chat_response = await simple_async_client.post(
            "/api/chats/",
            params={"user_id": 2},
            headers=alice_headers
        )
        assert chat_response.status_code == 200
        chat_info = chat_response.json()
        
        # Send a message in the chat
        message_response = await simple_async_client.post(
            "/api/messages/",
            json={"chat_id": chat_info["id"], "content": "Hello alex!"},
            headers=alice_headers
        )
        assert message_response.status_code == 200
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_chat_list_sorting_workflow(self, simple_async_client: AsyncClient):
        """Test that chats are sorted by last message time."""
        # Create user and login
        user_data = {"username": "testuser", "password": "password123"}
        await simple_async_client.post("/api/users/register", json=user_data)
        login_response = await simple_async_client.post("/api/users/login", json=user_data)
        auth_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        # Create multiple chats
        chat1_response = await simple_async_client.post(
            "/api/chats/",
            params={"name": "Chat 1"},
            headers=auth_headers
        )
        chat2_response = await simple_async_client.post(
            "/api/chats/",
            params={"name": "Chat 2"},
            headers=auth_headers
        )
        
        chat1_id = chat1_response.json()["id"]
        chat2_id = chat2_response.json()["id"]
        
        # Send message to chat1 first
        await simple_async_client.post(
            "/api/messages/",
            json={"chat_id": chat1_id, "content": "First message"},
            headers=auth_headers
        )
        
        # Wait a moment to ensure different timestamps
        await asyncio.sleep(0.1)
        
        # Send message to chat2
        await simple_async_client.post(
            "/api/messages/",
            json={"chat_id": chat2_id, "content": "Second message"},
            headers=auth_headers
        )
        
        # Get chats list
        chats_response = await simple_async_client.get("/api/chats/", headers=auth_headers)
        assert chats_response.status_code == 200
        chats = chats_response.json()
        
        # Chat2 should be first (most recent message)
        assert len(chats) >= 2
        assert chats[0]["name"] == "Chat 2"
        assert chats[1]["name"] == "Chat 1"
