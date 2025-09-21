"""
Load testing with Locust for mini-messenger API.
"""
import json
import random
import time
from locust import HttpUser, task, between
from locust.exception import RescheduleTask


class MessengerUser(HttpUser):
    """Simulate a user interacting with the messenger API."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts. Register and login."""
        self.username = f"loadtest_user_{random.randint(1000, 9999)}"
        self.password = "loadtest_password_123"
        self.token = None
        self.chat_id = None
        
        # Register user
        response = self.client.post("/api/users/register", json={
            "username": self.username,
            "password": self.password
        })
        
        if response.status_code == 200:
            # Login to get token
            response = self.client.post("/api/users/login", json={
                "username": self.username,
                "password": self.password
            })
            
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
            else:
                raise RescheduleTask()
        else:
            raise RescheduleTask()
    
    @task(3)
    def send_message(self):
        """Send a message to a chat."""
        if not self.token:
            return
        
        # Create a chat if we don't have one
        if not self.chat_id:
            response = self.client.post(
                "/api/chats/",
                params={"name": f"Load Test Chat {self.username}"},
                headers=self.headers
            )
            if response.status_code == 200:
                self.chat_id = response.json()["id"]
            else:
                return
        
        # Send a message
        message_content = f"Load test message {random.randint(1, 1000)}"
        response = self.client.post(
            "/api/messages/",
            json={
                "chat_id": self.chat_id,
                "content": message_content
            },
            headers=self.headers
        )
        
        if response.status_code != 200:
            print(f"Failed to send message: {response.status_code}")
    
    @task(2)
    def get_messages(self):
        """Get messages from a chat."""
        if not self.token or not self.chat_id:
            return
        
        response = self.client.get(
            f"/api/messages/{self.chat_id}",
            headers=self.headers
        )
        
        if response.status_code != 200:
            print(f"Failed to get messages: {response.status_code}")
    
    @task(1)
    def get_chats(self):
        """Get user's chats."""
        if not self.token:
            return
        
        response = self.client.get("/api/chats/", headers=self.headers)
        
        if response.status_code != 200:
            print(f"Failed to get chats: {response.status_code}")
    
    @task(1)
    def search_users(self):
        """Search for users."""
        if not self.token:
            return
        
        search_terms = ["test", "user", "load", "alice", "bob"]
        search_term = random.choice(search_terms)
        
        response = self.client.get(
            f"/api/users/search/{search_term}",
            headers=self.headers
        )
        
        if response.status_code != 200:
            print(f"Failed to search users: {response.status_code}")
    
    @task(1)
    def create_chat(self):
        """Create a new chat."""
        if not self.token:
            return
        
        chat_name = f"Load Test Chat {random.randint(1, 1000)}"
        response = self.client.post(
            "/api/chats/",
            params={"name": chat_name},
            headers=self.headers
        )
        
        if response.status_code == 200:
            self.chat_id = response.json()["id"]
        else:
            print(f"Failed to create chat: {response.status_code}")


class HighFrequencyUser(HttpUser):
    """Simulate a high-frequency user (bot-like behavior)."""
    
    wait_time = between(0.1, 0.5)  # Very short wait time
    
    def on_start(self):
        """Register and login quickly."""
        self.username = f"bot_user_{random.randint(1000, 9999)}"
        self.password = "bot_password_123"
        self.token = None
        self.chat_id = None
        
        # Register and login
        self.client.post("/api/users/register", json={
            "username": self.username,
            "password": self.password
        })
        
        response = self.client.post("/api/users/login", json={
            "username": self.username,
            "password": self.password
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            
            # Create a chat immediately
            response = self.client.post(
                "/api/chats/",
                params={"name": f"Bot Chat {self.username}"},
                headers=self.headers
            )
            if response.status_code == 200:
                self.chat_id = response.json()["id"]
    
    @task(10)
    def rapid_messaging(self):
        """Send messages rapidly."""
        if not self.token or not self.chat_id:
            return
        
        message_content = f"Bot message {random.randint(1, 10000)}"
        self.client.post(
            "/api/messages/",
            json={
                "chat_id": self.chat_id,
                "content": message_content
            },
            headers=self.headers
        )
    
    @task(5)
    def rapid_message_retrieval(self):
        """Get messages rapidly."""
        if not self.token or not self.chat_id:
            return
        
        self.client.get(
            f"/api/messages/{self.chat_id}",
            headers=self.headers
        )


class WebSocketUser(HttpUser):
    """Simulate WebSocket connections for load testing."""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Set up WebSocket connection."""
        # Note: This is a simplified version. Real WebSocket testing
        # would require a custom Locust client or additional setup
        self.chat_id = random.randint(1, 100)
    
    @task(1)
    def websocket_connection(self):
        """Simulate WebSocket connection (placeholder)."""
        # In a real implementation, this would establish WebSocket connections
        # and send/receive messages
        pass


# Load test configurations
class LightLoadTest(MessengerUser):
    """Light load test configuration."""
    wait_time = between(2, 5)
    weight = 10


class MediumLoadTest(MessengerUser):
    """Medium load test configuration."""
    wait_time = between(1, 3)
    weight = 5


class HeavyLoadTest(HighFrequencyUser):
    """Heavy load test configuration."""
    wait_time = between(0.1, 0.5)
    weight = 1
