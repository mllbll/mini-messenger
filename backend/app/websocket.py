from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt
from app.auth import SECRET_KEY

router = APIRouter()
active_connections = {}  # chat_id -> list of WebSocket connections
connection_users = {}  # WebSocket -> user_id (to identify which user owns which connection)

def verify_websocket_token(token: str):
    """Verify JWT token from WebSocket query parameter"""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None

@router.websocket("/chat/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int, token: str = Query(None)):
    # Verify token
    username = verify_websocket_token(token)
    if not username:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    await websocket.accept()
    if chat_id not in active_connections:
        active_connections[chat_id] = []
    active_connections[chat_id].append(websocket)
    
    # Get user_id for this connection
    from app.db import SessionLocal
    from app.models import User
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if user:
        connection_users[websocket] = user.id
        print(f"WebSocket connected for chat {chat_id} by user {username} (ID: {user.id})")
        print(f"Total connections for chat {chat_id}: {len(active_connections[chat_id])}")
        print(f"Total tracked users: {len(connection_users)}")
    else:
        print(f"Warning: User {username} not found in database")
    db.close()
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received message for chat {chat_id} from {username}: {data}")
            
            # Broadcast message to all connections in this chat
            for conn in active_connections[chat_id]:
                if conn != websocket:
                    try:
                        await conn.send_text(data)
                    except Exception as e:
                        print(f"Error sending message: {e}")
    except WebSocketDisconnect:
        if chat_id in active_connections:
            active_connections[chat_id].remove(websocket)
            if not active_connections[chat_id]:
                del active_connections[chat_id]
        if websocket in connection_users:
            del connection_users[websocket]
        print(f"WebSocket disconnected for chat {chat_id} by user {username}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        if chat_id in active_connections:
            active_connections[chat_id].remove(websocket)
            if not active_connections[chat_id]:
                del active_connections[chat_id]
        if websocket in connection_users:
            del connection_users[websocket]
