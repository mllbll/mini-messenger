from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import get_db
from app.models import Chat, User, ChatMember
from app.schemas import ChatOut
from jose import JWTError, jwt
from app.auth import SECRET_KEY

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

@router.get("/", response_model=list[ChatOut])
def get_chats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get only chats where the current user is a member
    chats = db.query(Chat).join(ChatMember).filter(
        ChatMember.user_id == current_user.id
    ).order_by(desc(Chat.last_message_time)).all()
    
    # Format chat names based on chat type and other members
    result = []
    for chat in chats:
        # Get all members of this chat
        members = db.query(ChatMember).filter(ChatMember.chat_id == chat.id).all()
        member_ids = [m.user_id for m in members]
        
        # If it's a private chat (2 members), show the other user's name
        if len(member_ids) == 2:
            # Find the other user (not current_user)
            other_user_id = [uid for uid in member_ids if uid != current_user.id][0]
            other_user = db.query(User).filter(User.id == other_user_id).first()
            if other_user:
                # Create a copy of chat data with modified name
                chat_dict = {
                    "id": chat.id,
                    "name": f"Chat with {other_user.username}",
                    "last_message_time": chat.last_message_time
                }
                result.append(chat_dict)
            else:
                result.append(chat)
        else:
            # Public chat - use original name
            result.append(chat)
    
    return result

@router.post("/", response_model=ChatOut)
def create_chat(name: str = None, user_id: int = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if user_id:
            # Create private chat with specific user
            if user_id == current_user.id:
                raise HTTPException(status_code=400, detail="Cannot create chat with yourself")
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            chat = Chat(name=f"Chat with {user.username}")
        else:
            # Create public chat
            if not name or not name.strip():
                raise HTTPException(status_code=400, detail="Chat name cannot be empty")
            chat = Chat(name=name.strip())
        
        db.add(chat)
        db.commit()
        db.refresh(chat)
        
        # Add current user as a member of the chat
        member = ChatMember(chat_id=chat.id, user_id=current_user.id)
        db.add(member)
        
        # If it's a private chat, add the other user as well
        if user_id:
            other_member = ChatMember(chat_id=chat.id, user_id=user_id)
            db.add(other_member)
        
        db.commit()
        return chat
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create chat: {str(e)}")
