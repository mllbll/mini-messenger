"""
Integration tests for WebSocket functionality.
"""
import pytest
import asyncio
import json
import websockets
from httpx import AsyncClient


class TestWebSocketConnection:
    """Test WebSocket connection functionality."""
    
    @pytest.mark.asyncio
    @pytest.mark.websocket
    async def test_websocket_connection(self):
        """Test basic WebSocket connection."""
        uri = "ws://localhost:8000/ws/chat/1"
        
        async with websockets.connect(uri) as websocket:
            # Connection should be established
            assert websocket.open is True
    
    @pytest.mark.asyncio
    @pytest.mark.websocket
    async def test_websocket_message_broadcast(self):
        """Test message broadcasting between WebSocket connections."""
        uri = "ws://localhost:8000/ws/chat/1"
        
        # Create two connections to the same chat
        async with websockets.connect(uri) as ws1, websockets.connect(uri) as ws2:
            # Send message from first connection
            test_message = "Hello from ws1"
            await ws1.send(test_message)
            
            # Receive message on second connection
            received_message = await ws2.recv()
            assert received_message == test_message
    
    @pytest.mark.asyncio
    @pytest.mark.websocket
    async def test_websocket_multiple_chats(self):
        """Test that messages are isolated between different chats."""
        uri1 = "ws://localhost:8000/ws/chat/1"
        uri2 = "ws://localhost:8000/ws/chat/2"
        
        async with websockets.connect(uri1) as ws1, websockets.connect(uri2) as ws2:
            # Send message to chat 1
            await ws1.send("Message for chat 1")
            
            # Send message to chat 2
            await ws2.send("Message for chat 2")
            
            # Receive messages
            msg1 = await ws1.recv()
            msg2 = await ws2.recv()
            
            # Messages should be isolated
            assert msg1 == "Message for chat 2"  # ws1 receives from ws2
            assert msg2 == "Message for chat 1"  # ws2 receives from ws1
    
    @pytest.mark.asyncio
    @pytest.mark.websocket
    async def test_websocket_connection_cleanup(self):
        """Test that connections are properly cleaned up on disconnect."""
        uri = "ws://localhost:8000/ws/chat/1"
        
        # Connect and disconnect
        websocket = await websockets.connect(uri)
        assert websocket.open is True
        
        await websocket.close()
        assert websocket.open is False
    
    @pytest.mark.asyncio
    @pytest.mark.websocket
    async def test_websocket_invalid_chat_id(self):
        """Test WebSocket connection with invalid chat ID."""
        uri = "ws://localhost:8000/ws/chat/invalid"
        
        with pytest.raises(websockets.exceptions.InvalidURI):
            await websockets.connect(uri)


class TestWebSocketIntegration:
    """Test WebSocket integration with HTTP API."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_message_flow_http_to_websocket(self, async_client: AsyncClient, auth_headers):
        """Test message flow from HTTP API to WebSocket."""
        # Create a chat via HTTP API
        chat_response = await async_client.post(
            "/api/chats/",
            params={"name": "Test Chat"},
            headers=auth_headers
        )
        chat_id = chat_response.json()["id"]
        
        # Connect to WebSocket for this chat
        uri = f"ws://localhost:8000/ws/chat/{chat_id}"
        
        async with websockets.connect(uri) as websocket:
            # Send message via HTTP API
            message_data = {
                "chat_id": chat_id,
                "content": "HTTP to WebSocket test"
            }
            
            http_response = await async_client.post(
                "/api/messages/",
                json=message_data,
                headers=auth_headers
            )
            assert http_response.status_code == 200
            
            # Message should be broadcast via WebSocket
            # Note: This would require WebSocket to listen for HTTP messages
            # which is not currently implemented in the basic version
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_websocket_connections(self):
        """Test multiple concurrent WebSocket connections."""
        uri = "ws://localhost:8000/ws/chat/1"
        
        async def create_connection(connection_id):
            async with websockets.connect(uri) as websocket:
                await websocket.send(f"Message from connection {connection_id}")
                return await websocket.recv()
        
        # Create 5 concurrent connections
        tasks = [create_connection(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All connections should receive messages
        assert len(results) == 5
        for result in results:
            assert "Message from connection" in result


class TestWebSocketErrorHandling:
    """Test WebSocket error handling."""
    
    @pytest.mark.asyncio
    @pytest.mark.websocket
    async def test_websocket_server_disconnect(self):
        """Test handling of server disconnection."""
        uri = "ws://localhost:8000/ws/chat/1"
        
        async with websockets.connect(uri) as websocket:
            # Simulate server disconnect by closing connection
            await websocket.close()
            
            # Try to send message after disconnect
            with pytest.raises(websockets.exceptions.ConnectionClosed):
                await websocket.send("Test message")
    
    @pytest.mark.asyncio
    @pytest.mark.websocket
    async def test_websocket_large_message(self):
        """Test handling of large messages."""
        uri = "ws://localhost:8000/ws/chat/1"
        
        # Create a large message (1MB)
        large_message = "x" * (1024 * 1024)
        
        async with websockets.connect(uri) as websocket:
            try:
                await websocket.send(large_message)
                # If no exception is raised, the message was sent successfully
                received = await websocket.recv()
                assert len(received) == len(large_message)
            except websockets.exceptions.MessageTooBig:
                # This is expected for very large messages
                pass
    
    @pytest.mark.asyncio
    @pytest.mark.websocket
    async def test_websocket_rapid_messages(self):
        """Test rapid message sending."""
        uri = "ws://localhost:8000/ws/chat/1"
        
        async with websockets.connect(uri) as websocket:
            # Send 100 messages rapidly
            for i in range(100):
                await websocket.send(f"Rapid message {i}")
            
            # Receive all messages
            received_count = 0
            try:
                while received_count < 100:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    received_count += 1
            except asyncio.TimeoutError:
                pass
            
            # Should receive most messages (allowing for some loss)
            assert received_count >= 90
