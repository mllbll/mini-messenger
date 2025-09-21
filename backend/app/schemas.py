from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    class Config:
        orm_mode = True

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

class MessageOut(BaseModel):
    id: int
    chat_id: int
    user_id: int
    content: str
    timestamp: datetime
    class Config:
        orm_mode = True
