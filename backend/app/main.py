from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import users, chats, messages
from app.websocket import router as ws_router

app = FastAPI(title="Mini Messenger API")

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(chats.router, prefix="/api/chats", tags=["chats"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(ws_router, prefix="/ws")
