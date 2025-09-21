from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime
from app.db import SessionLocal
from app.models import Message, User, Chat
from app.schemas import MessageCreate
from app.auth import create_access_token
from jose import JWTError, jwt

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, "supersecret", algorithms=["HS256"])
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
def send_message(msg: MessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    message = Message(chat_id=msg.chat_id, user_id=current_user.id, content=msg.content)
    db.add(message)
    
    # Update chat's last_message_time
    chat = db.query(Chat).filter(Chat.id == msg.chat_id).first()
    if chat:
        chat.last_message_time = datetime.utcnow()
    
    db.commit()
    db.refresh(message)
    return message

@router.get("/{chat_id}")
def get_messages(chat_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Message).filter(Message.chat_id == chat_id).all()
