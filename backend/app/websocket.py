from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()
active_connections = {}

@router.websocket("/chat/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int):
    await websocket.accept()
    if chat_id not in active_connections:
        active_connections[chat_id] = []
    active_connections[chat_id].append(websocket)
    
    print(f"WebSocket connected for chat {chat_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received message for chat {chat_id}: {data}")
            
            # Broadcast message to all connections in this chat
            for conn in active_connections[chat_id]:
                if conn != websocket:
                    await conn.send_text(data)
    except WebSocketDisconnect:
        if chat_id in active_connections:
            active_connections[chat_id].remove(websocket)
            if not active_connections[chat_id]:
                del active_connections[chat_id]
        print(f"WebSocket disconnected for chat {chat_id}")
