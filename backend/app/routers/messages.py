from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime
import json
from app.db import get_db
from app.models import Message, User, Chat
from app.schemas import MessageCreate
from app.auth import SECRET_KEY
from app.websocket import active_connections, connection_users
from jose import JWTError, jwt

router = APIRouter()

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/")
async def send_message(msg: MessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # Check if chat exists
        chat = db.query(Chat).filter(Chat.id == msg.chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        message = Message(chat_id=msg.chat_id, user_id=current_user.id, content=msg.content)
        db.add(message)
        
        # Update chat's last_message_time
        chat.last_message_time = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        
        # Broadcast message to all WebSocket connections in this chat
        print(f"Checking WebSocket connections for chat {msg.chat_id}")
        print(f"Active connections: {list(active_connections.keys())}")
        if msg.chat_id in active_connections:
            print(f"Chat {msg.chat_id} has {len(active_connections[msg.chat_id])} connections")
        
        if msg.chat_id in active_connections and len(active_connections[msg.chat_id]) > 0:
            message_data = {
                "id": message.id,
                "chat_id": message.chat_id,
                "user_id": message.user_id,
                "content": message.content,
                "timestamp": message.timestamp.isoformat()
            }
            # Get username for the message
            user = db.query(User).filter(User.id == message.user_id).first()
            if user:
                message_data["username"] = user.username
            
            message_json = json.dumps(message_data)
            # Send to all connected clients in this chat, EXCEPT the sender
            # (sender already sees the message locally)
            disconnected = []
            sender_user_id = current_user.id
            connections_to_notify = [conn for conn in active_connections[msg.chat_id] 
                                   if connection_users.get(conn) != sender_user_id]
            
            print(f"Broadcasting message {message.id} to {len(connections_to_notify)} connections (excluding sender {sender_user_id})")
            
            for conn in connections_to_notify:
                try:
                    await conn.send_text(message_json)
                    print(f"Message sent to connection (user_id: {connection_users.get(conn)})")
                except Exception as e:
                    print(f"Error broadcasting message to WebSocket: {e}")
                    disconnected.append(conn)
            
            # Remove disconnected connections
            for conn in disconnected:
                if msg.chat_id in active_connections:
                    active_connections[msg.chat_id].remove(conn)
                    if not active_connections[msg.chat_id]:
                        del active_connections[msg.chat_id]
                    if conn in connection_users:
                        del connection_users[conn]
        else:
            print(f"No active WebSocket connections for chat {msg.chat_id}")
        
        return message
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@router.get("/{chat_id}")
def get_messages(chat_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if chat exists
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.timestamp).all()
    return messages
