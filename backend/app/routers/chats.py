from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import SessionLocal
from app.models import Chat, User
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

@router.get("/")
def get_chats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Chat).order_by(desc(Chat.last_message_time)).all()

@router.post("/")
def create_chat(name: str = None, user_id: int = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id:
        # Create private chat with specific user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        chat = Chat(name=f"Chat with {user.username}")
    else:
        # Create public chat
        chat = Chat(name=name or "New Chat")
    
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat
