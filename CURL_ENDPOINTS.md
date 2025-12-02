# CURL команды для всех эндпоинтов API

## Базовый URL
```bash
API_BASE="http://localhost:8000"
```

---

## 1. Users Endpoints

### 1.1 Регистрация пользователя
```bash
curl -X POST "$API_BASE/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

**Ответ:**
```json
{
  "id": 1,
  "username": "testuser"
}
```

### 1.2 Вход пользователя
```bash
curl -X POST "$API_BASE/api/users/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Сохранение токена:**
```bash
TOKEN=$(curl -s -X POST "$API_BASE/api/users/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

### 1.3 Получение информации о текущем пользователе
```bash
curl -X GET "$API_BASE/api/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ:**
```json
{
  "id": 1,
  "username": "testuser"
}
```

### 1.4 Получение списка всех пользователей
```bash
curl -X GET "$API_BASE/api/users/" \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ:**
```json
[
  {
    "id": 1,
    "username": "testuser"
  },
  {
    "id": 2,
    "username": "anotheruser"
  }
]
```

### 1.5 Поиск пользователей
```bash
curl -X GET "$API_BASE/api/users/search/test" \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ:**
```json
[
  {
    "id": 1,
    "username": "testuser"
  }
]
```

---

## 2. Chats Endpoints

### 2.1 Получение списка чатов
```bash
curl -X GET "$API_BASE/api/chats/" \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ:**
```json
[
  {
    "id": 1,
    "name": "Test Chat",
    "last_message_time": "2024-01-01T12:00:00"
  }
]
```

### 2.2 Создание публичного чата
```bash
curl -X POST "$API_BASE/api/chats/?name=My%20Chat" \
  -H "Authorization: Bearer $TOKEN"
```

**Или с JSON:**
```bash
curl -X POST "$API_BASE/api/chats/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Chat"}'
```

**Ответ:**
```json
{
  "id": 1,
  "name": "My Chat",
  "last_message_time": "2024-01-01T12:00:00"
}
```

### 2.3 Создание приватного чата
```bash
curl -X POST "$API_BASE/api/chats/?user_id=2" \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ:**
```json
{
  "id": 2,
  "name": "Chat with anotheruser",
  "last_message_time": "2024-01-01T12:00:00"
}
```

---

## 3. Messages Endpoints

### 3.1 Отправка сообщения
```bash
curl -X POST "$API_BASE/api/messages/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": 1,
    "content": "Hello, this is a test message!"
  }'
```

**Ответ:**
```json
{
  "id": 1,
  "chat_id": 1,
  "user_id": 1,
  "content": "Hello, this is a test message!",
  "timestamp": "2024-01-01T12:00:00"
}
```

### 3.2 Получение сообщений чата
```bash
curl -X GET "$API_BASE/api/messages/1" \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ:**
```json
[
  {
    "id": 1,
    "chat_id": 1,
    "user_id": 1,
    "content": "Hello, this is a test message!",
    "timestamp": "2024-01-01T12:00:00"
  }
]
```

---

## 4. WebSocket Endpoint

### 4.1 Подключение к WebSocket
```bash
# Используйте wscat или другой WebSocket клиент
wscat -c "ws://localhost:8000/ws/chat/1?token=$TOKEN"
```

**Или через Python:**
```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = f"ws://localhost:8000/ws/chat/1?token={TOKEN}"
    async with websockets.connect(uri) as websocket:
        # Отправка сообщения
        await websocket.send(json.dumps({
            "content": "Hello via WebSocket!"
        }))
        # Получение ответа
        response = await websocket.recv()
        print(response)

asyncio.run(test_websocket())
```

---

## Полный пример тестирования всех эндпоинтов

```bash
#!/bin/bash

API_BASE="http://localhost:8000"

# 1. Регистрация
echo "1. Регистрация пользователя"
curl -X POST "$API_BASE/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
echo -e "\n"

# 2. Вход и получение токена
echo "2. Вход пользователя"
TOKEN=$(curl -s -X POST "$API_BASE/api/users/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "Token: ${TOKEN:0:30}..."
echo -e "\n"

# 3. Получение информации о себе
echo "3. Получение информации о текущем пользователе"
curl -X GET "$API_BASE/api/users/me" \
  -H "Authorization: Bearer $TOKEN"
echo -e "\n\n"

# 4. Получение списка пользователей
echo "4. Получение списка пользователей"
curl -X GET "$API_BASE/api/users/" \
  -H "Authorization: Bearer $TOKEN"
echo -e "\n\n"

# 5. Поиск пользователей
echo "5. Поиск пользователей"
curl -X GET "$API_BASE/api/users/search/test" \
  -H "Authorization: Bearer $TOKEN"
echo -e "\n\n"

# 6. Получение списка чатов
echo "6. Получение списка чатов"
curl -X GET "$API_BASE/api/chats/" \
  -H "Authorization: Bearer $TOKEN"
echo -e "\n\n"

# 7. Создание чата
echo "7. Создание публичного чата"
curl -X POST "$API_BASE/api/chats/?name=Test%20Chat" \
  -H "Authorization: Bearer $TOKEN"
echo -e "\n\n"

# 8. Получение ID чата
CHAT_ID=$(curl -s -X GET "$API_BASE/api/chats/" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -c "import sys, json; chats=json.load(sys.stdin); print(chats[0]['id'] if chats else '1')")
echo "Chat ID: $CHAT_ID"
echo -e "\n"

# 9. Отправка сообщения
echo "9. Отправка сообщения"
curl -X POST "$API_BASE/api/messages/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\":$CHAT_ID,\"content\":\"Test message from curl\"}"
echo -e "\n\n"

# 10. Получение сообщений
echo "10. Получение сообщений чата"
curl -X GET "$API_BASE/api/messages/$CHAT_ID" \
  -H "Authorization: Bearer $TOKEN"
echo -e "\n\n"
```

---

## Обработка ошибок

### 401 Unauthorized
```bash
# Неверный токен или отсутствие токена
curl -X GET "$API_BASE/api/users/me"
# Ответ: {"detail":"Not authenticated"}
```

### 400 Bad Request
```bash
# Пустое имя чата
curl -X POST "$API_BASE/api/chats/?name=" \
  -H "Authorization: Bearer $TOKEN"
# Ответ: {"detail":"Chat name cannot be empty"}
```

### 404 Not Found
```bash
# Несуществующий чат
curl -X GET "$API_BASE/api/messages/999" \
  -H "Authorization: Bearer $TOKEN"
# Ответ: {"detail":"Chat not found"}
```

---

## Форматированный вывод JSON

Для красивого вывода используйте `jq`:
```bash
curl -s -X GET "$API_BASE/api/chats/" \
  -H "Authorization: Bearer $TOKEN" | jq
```

Или `python3 -m json.tool`:
```bash
curl -s -X GET "$API_BASE/api/chats/" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

