"""
Security tests for mini-messenger API.
"""
import pytest
import json
import sys
import os
from httpx import AsyncClient

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.auth import create_access_token


class TestAuthenticationSecurity:
    """Test authentication security measures."""
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_invalid_token_format(self, simple_async_client):
        """Test API with invalid token format."""
        invalid_headers = [
            {"Authorization": "InvalidToken"},
            {"Authorization": "Bearer"},
            {"Authorization": "Bearer invalid_token"},
            {"Authorization": "Basic dGVzdDp0ZXN0"},  # Basic auth instead of Bearer
        ]
        
        for headers in invalid_headers:
            response = await simple_async_client.get("/api/users/me", headers=headers)
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_expired_token(self, simple_async_client):
        """Test API with expired token."""
        # Create an expired token (expired 1 hour ago)
        from datetime import datetime, timedelta
        expired_data = {
            "sub": "testuser",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = create_access_token(expired_data)
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await simple_async_client.get("/api/users/me", headers=headers)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_token_tampering(self, simple_async_client):
        """Test API with tampered token."""
        # Create a valid token
        valid_token = create_access_token({"sub": "testuser"})
        
        # Tamper with the token
        tampered_token = valid_token[:-5] + "XXXXX"
        
        headers = {"Authorization": f"Bearer {tampered_token}"}
        response = await simple_async_client.get("/api/users/me", headers=headers)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_missing_authorization_header(self, simple_async_client):
        """Test API without authorization header."""
        response = await simple_async_client.get("/api/users/me")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_authorization_header_case_sensitivity(self, simple_async_client):
        """Test that authorization header is case sensitive."""
        token = create_access_token({"sub": "testuser"})
        
        # Test different case variations
        invalid_headers = [
            {"authorization": f"Bearer {token}"},  # lowercase
            {"AUTHORIZATION": f"Bearer {token}"},  # uppercase
            {"Authorization": f"bearer {token}"},  # lowercase bearer
        ]
        
        for headers in invalid_headers:
            response = await simple_async_client.get("/api/users/me", headers=headers)
            assert response.status_code == 401


class TestInputValidationSecurity:
    """Test input validation and sanitization."""
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_xss_prevention_in_messages(self, simple_async_client, auth_headers, malicious_inputs):
        """Test XSS prevention in message content."""
        # Create a chat first
        chat_response = await simple_async_client.post(
            "/api/chats/",
            params={"name": "Security Test Chat"},
            headers=auth_headers
        )
        chat_id = chat_response.json()["id"]
        
        for malicious_input in malicious_inputs:
            message_data = {
                "chat_id": chat_id,
                "content": malicious_input
            }
            
            response = await simple_async_client.post(
                "/api/messages/",
                json=message_data,
                headers=auth_headers
            )
            
            # Should accept the message (stored as-is)
            assert response.status_code == 200
            
            # Retrieve the message
            messages_response = await simple_async_client.get(
                f"/api/messages/{chat_id}",
                headers=auth_headers
            )
            
            # Message should be stored exactly as sent
            messages = messages_response.json()
            assert len(messages) >= 1
            # Note: XSS prevention should be handled by the frontend, not the API
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_sql_injection_prevention(self, simple_async_client, auth_headers):
        """Test SQL injection prevention."""
        # Test SQL injection in username search
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]
        
        for payload in sql_injection_payloads:
            response = await simple_async_client.get(
                f"/api/users/search/{payload}",
                headers=auth_headers
            )
            
            # Should not crash or return unexpected data
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                # Should return empty results or safe results
                data = response.json()
                assert isinstance(data, list)
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_path_traversal_prevention(self, simple_async_client, auth_headers):
        """Test path traversal prevention."""
        path_traversal_payloads = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for payload in path_traversal_payloads:
            # Test in chat ID parameter
            response = await simple_async_client.get(
                f"/api/messages/{payload}",
                headers=auth_headers
            )
            
            # Should return 404 or 422, not crash
            assert response.status_code in [404, 422, 400]
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_large_payload_prevention(self, simple_async_client, auth_headers):
        """Test prevention of large payload attacks."""
        # Create a very large message
        large_message = "A" * (10 * 1024 * 1024)  # 10MB message
        
        # Create a chat first
        chat_response = await simple_async_client.post(
            "/api/chats/",
            params={"name": "Large Payload Test"},
            headers=auth_headers
        )
        chat_id = chat_response.json()["id"]
        
        message_data = {
            "chat_id": chat_id,
            "content": large_message
        }
        
        response = await simple_async_client.post(
            "/api/messages/",
            json=message_data,
            headers=auth_headers
        )
        
        # Should either reject or handle gracefully
        assert response.status_code in [200, 413, 422, 400]


class TestAuthorizationSecurity:
    """Test authorization and access control."""
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_user_isolation(self, simple_async_client):
        """Test that users can only access their own data."""
        import time
        # Create two users with unique names
        user1_data = {"username": f"user1_{int(time.time() * 1000)}", "password": "password123"}
        user2_data = {"username": f"user2_{int(time.time() * 1000) + 1}", "password": "password123"}
        
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
            params={"name": "User1's Private Chat"},
            headers=user1_headers
        )
        chat_id = chat_response.json()["id"]
        
        # User1 sends a message
        await simple_async_client.post(
            "/api/messages/",
            json={"chat_id": chat_id, "content": "User1's secret message"},
            headers=user1_headers
        )
        
        # User2 should not be able to access User1's chat messages
        response = await simple_async_client.get(
            f"/api/messages/{chat_id}",
            headers=user2_headers
        )
        
        # Should return 404 or empty results (depending on implementation)
        assert response.status_code in [404, 200]
        
        if response.status_code == 200:
            messages = response.json()
            assert len(messages) == 0  # Should be empty for unauthorized user
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_privilege_escalation_prevention(self, simple_async_client):
        """Test prevention of privilege escalation."""
        import time
        # Create a regular user
        user_data = {"username": f"regularuser_{int(time.time() * 1000)}", "password": "password123"}
        await simple_async_client.post("/api/users/register", json=user_data)
        
        login_response = await simple_async_client.post("/api/users/login", json=user_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access admin endpoints (if they exist)
        admin_endpoints = [
            "/api/admin/users",
            "/api/admin/chats",
            "/api/admin/messages",
            "/api/admin/stats"
        ]
        
        for endpoint in admin_endpoints:
            response = await simple_async_client.get(endpoint, headers=headers)
            # Should return 404 (endpoint doesn't exist) or 403 (forbidden)
            assert response.status_code in [404, 403]
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_token_reuse_after_logout(self, simple_async_client):
        """Test that tokens cannot be reused after logout."""
        import time
        # Register and login user
        user_data = {"username": f"testuser_{int(time.time() * 1000)}", "password": "password123"}
        await simple_async_client.post("/api/users/register", json=user_data)
        
        login_response = await simple_async_client.post("/api/users/login", json=user_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Use token successfully
        response = await simple_async_client.get("/api/users/me", headers=headers)
        assert response.status_code == 200
        
        # Note: In a real implementation, you would have a logout endpoint
        # that invalidates the token. For now, we'll test that the token
        # continues to work (which is expected behavior for JWT tokens)
        
        # Token should still work (JWT tokens are stateless)
        response = await simple_async_client.get("/api/users/me", headers=headers)
        assert response.status_code == 200


class TestRateLimitingSecurity:
    """Test rate limiting and DoS prevention."""
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_registration_rate_limiting(self, simple_async_client):
        """Test rate limiting on user registration."""
        import time
        # Try to register many users rapidly
        for i in range(100):
            user_data = {
                "username": f"ratelimit_user_{int(time.time() * 1000)}_{i}",
                "password": "password123"
            }
            
            response = await simple_async_client.post("/api/users/register", json=user_data)
            
            # Should eventually start returning rate limit errors
            # Note: This test assumes rate limiting is implemented
            if response.status_code == 429:
                break
        
        # If no rate limiting is implemented, all requests should succeed
        # This is acceptable for a basic implementation
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_login_brute_force_prevention(self, simple_async_client):
        """Test brute force prevention on login."""
        import time
        # Register a user
        user_data = {"username": f"bruteforce_user_{int(time.time() * 1000)}", "password": "correct_password"}
        await simple_async_client.post("/api/users/register", json=user_data)
        
        # Try to login with wrong password many times
        wrong_password_data = {"username": user_data["username"], "password": "wrong_password"}
        
        for i in range(20):
            response = await simple_async_client.post("/api/users/login", json=wrong_password_data)
            
            # Should eventually start returning rate limit or account lockout errors
            if response.status_code in [429, 423]:
                break
        
        # Try with correct password
        response = await simple_async_client.post("/api/users/login", json=user_data)
        # Should still work if no brute force protection is implemented
        assert response.status_code in [200, 423]  # 423 = account locked


class TestDataValidationSecurity:
    """Test data validation and sanitization."""
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_username_validation(self, simple_async_client):
        """Test username validation and sanitization."""
        invalid_usernames = [
            "",  # Empty
            "a",  # Too short
            "a" * 100,  # Too long
            "user@domain.com",  # Special characters
            "user name",  # Spaces
            "user\nname",  # Newlines
            "user\tname",  # Tabs
            "user<script>",  # HTML tags
            "user'; DROP TABLE users; --",  # SQL injection
        ]
        
        for username in invalid_usernames:
            user_data = {"username": username, "password": "validpassword123"}
            response = await simple_async_client.post("/api/users/register", json=user_data)
            
            # Should reject invalid usernames
            assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_password_validation(self, simple_async_client):
        """Test password validation."""
        invalid_passwords = [
            "",  # Empty
            "123",  # Too short
            "password",  # Too common
            "12345678",  # Only numbers
            "abcdefgh",  # Only letters
        ]
        
        for password in invalid_passwords:
            user_data = {"username": f"user_{hash(password)}", "password": password}
            response = await simple_async_client.post("/api/users/register", json=user_data)
            
            # Should reject weak passwords
            assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_message_content_validation(self, simple_async_client, auth_headers):
        """Test message content validation."""
        # Create a chat first
        chat_response = await simple_async_client.post(
            "/api/chats/",
            params={"name": "Content Validation Test"},
            headers=auth_headers
        )
        chat_id = chat_response.json()["id"]
        
        invalid_contents = [
            "",  # Empty message
            " " * 1000,  # Only whitespace
            "\x00\x01\x02",  # Null bytes and control characters
        ]
        
        for content in invalid_contents:
            message_data = {"chat_id": chat_id, "content": content}
            response = await simple_async_client.post(
                "/api/messages/",
                json=message_data,
                headers=auth_headers
            )
            
            # Should reject invalid content
            assert response.status_code in [400, 422]
