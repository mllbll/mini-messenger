from pydantic import BaseModel, validator
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    
    @validator('username')
    def username_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        return v
    
    @validator('password')
    def password_must_be_long_enough(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        # Bcrypt has a maximum password length of 72 bytes
        # Truncate if necessary
        if len(v.encode('utf-8')) > 72:
            v = v.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        return v

class UserOut(BaseModel):
    id: int
    username: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChatOut(BaseModel):
    id: int
    name: str
    last_message_time: datetime
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    chat_id: int
    content: str
    
    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Message content cannot be empty')
        return v

class MessageOut(BaseModel):
    id: int
    chat_id: int
    user_id: int
    content: str
    timestamp: datetime
    class Config:
        from_attributes = True
