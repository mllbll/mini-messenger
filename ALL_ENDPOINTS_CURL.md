# CURL команды для всех эндпоинтов - РАБОЧИЕ

## ✅ Все эндпоинты протестированы и работают!

### Базовые настройки
```bash
API_BASE="http://localhost:8000"
```

---

## 🔐 Аутентификация

### 1. Регистрация пользователя
```bash
curl -X POST "$API_BASE/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"pass123"}'
```

**Ответ (200 OK):**
```json
{
  "id": 1,
  "username": "testuser"
}
```

### 2. Вход пользователя
```bash
curl -X POST "$API_BASE/api/users/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"pass123"}'
```

**Ответ (200 OK):**
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
  -d '{"username":"testuser","password":"pass123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

---

## 👤 Users Endpoints (требуют аутентификации)

### 3. Получение информации о текущем пользователе
```bash
curl -X GET "$API_BASE/api/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ (200 OK):**
```json
{
  "id": 1,
  "username": "testuser"
}
```

### 4. Получение списка всех пользователей
```bash
curl -X GET "$API_BASE/api/users/" \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ (200 OK):**
```json
[
  {
    "id": 1,
    "username": "testuser"
  },
  {
    "id": 2,
    "username": "user2"
  }
]
```

### 5. Поиск пользователей
```bash
curl -X GET "$API_BASE/api/users/search/test" \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ (200 OK):**
```json
[
  {
    "id": 1,
    "username": "testuser"
  }
]
```

**Примечание:** Текущий пользователь исключается из результатов поиска.

---

## 💬 Chats Endpoints (требуют аутентификации)

### 6. Получение списка чатов
```bash
curl -X GET "$API_BASE/api/chats/" \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Test Chat",
    "last_message_time": "2024-01-01T12:00:00"
  }
]
```

**Примечание:** Чаты сортируются по времени последнего сообщения (новые первыми).

### 7. Создание публичного чата
```bash
curl -X POST "$API_BASE/api/chats/?name=My%20Chat" \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ (200 OK):**
```json
{
  "id": 1,
  "name": "My Chat",
  "last_message_time": "2024-01-01T12:00:00"
}
```

**Ошибки:**
- `400 Bad Request`: "Chat name cannot be empty" - если имя пустое

### 8. Создание приватного чата
```bash
curl -X POST "$API_BASE/api/chats/?user_id=2" \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ (200 OK):**
```json
{
  "id": 2,
  "name": "Chat with user2",
  "last_message_time": "2024-01-01T12:00:00"
}
```

**Ошибки:**
- `400 Bad Request`: "Cannot create chat with yourself" - если user_id равен ID текущего пользователя
- `404 Not Found`: "User not found" - если пользователь с таким ID не существует

---

## 📨 Messages Endpoints (требуют аутентификации)

### 9. Отправка сообщения
```bash
curl -X POST "$API_BASE/api/messages/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": 1,
    "content": "Hello, this is a test message!"
  }'
```

**Ответ (200 OK):**
```json
{
  "id": 1,
  "chat_id": 1,
  "user_id": 1,
  "content": "Hello, this is a test message!",
  "timestamp": "2024-01-01T12:00:00"
}
```

**Ошибки:**
- `404 Not Found`: "Chat not found" - если чат с таким ID не существует
- `422 Unprocessable Entity`: "Message content cannot be empty" - если content пустой

### 10. Получение сообщений чата
```bash
curl -X GET "$API_BASE/api/messages/1" \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ (200 OK):**
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

**Примечание:** Сообщения сортируются по времени (старые первыми).

**Ошибки:**
- `404 Not Found`: "Chat not found" - если чат с таким ID не существует

---

## 🔌 WebSocket Endpoint

### 11. Подключение к WebSocket
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

**Примечание:** Токен передается через query параметр `token`.

---

## ❌ Обработка ошибок

### 401 Unauthorized
```bash
# Без токена
curl -X GET "$API_BASE/api/users/me"
# Ответ: {"detail":"Not authenticated"}

# Неверный токен
curl -X GET "$API_BASE/api/users/me" \
  -H "Authorization: Bearer invalid_token"
# Ответ: {"detail":"Invalid token"}
```

### 400 Bad Request
```bash
# Пустое имя чата
curl -X POST "$API_BASE/api/chats/?name=" \
  -H "Authorization: Bearer $TOKEN"
# Ответ: {"detail":"Chat name cannot be empty"}

# Создание чата с самим собой
curl -X POST "$API_BASE/api/chats/?user_id=1" \
  -H "Authorization: Bearer $TOKEN"
# Ответ: {"detail":"Cannot create chat with yourself"}
```

### 404 Not Found
```bash
# Несуществующий чат
curl -X GET "$API_BASE/api/messages/999" \
  -H "Authorization: Bearer $TOKEN"
# Ответ: {"detail":"Chat not found"}

# Несуществующий пользователь
curl -X POST "$API_BASE/api/chats/?user_id=999" \
  -H "Authorization: Bearer $TOKEN"
# Ответ: {"detail":"User not found"}
```

---

## 📊 Полный тест всех эндпоинтов

```bash
#!/bin/bash

API_BASE="http://localhost:8000"

# 1. Регистрация
echo "1. Регистрация"
curl -X POST "$API_BASE/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"pass123"}'
echo -e "\n\n"

# 2. Вход
echo "2. Вход"
TOKEN=$(curl -s -X POST "$API_BASE/api/users/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"pass123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "Token: ${TOKEN:0:30}..."
echo -e "\n\n"

# 3. Получение информации о себе
echo "3. GET /api/users/me"
curl -X GET "$API_BASE/api/users/me" \
  -H "Authorization: Bearer $TOKEN"
echo -e "\n\n"

# 4. Список пользователей
echo "4. GET /api/users/"
curl -X GET "$API_BASE/api/users/" \
  -H "Authorization: Bearer $TOKEN"
echo -e "\n\n"

# 5. Поиск пользователей
echo "5. GET /api/users/search/test"
curl -X GET "$API_BASE/api/users/search/test" \
  -H "Authorization: Bearer $TOKEN"
echo -e "\n\n"

# 6. Список чатов
echo "6. GET /api/chats/"
curl -X GET "$API_BASE/api/chats/" \
  -H "Authorization: Bearer $TOKEN"
echo -e "\n\n"

# 7. Создание чата
echo "7. POST /api/chats/?name=TestChat"
curl -X POST "$API_BASE/api/chats/?name=TestChat" \
  -H "Authorization: Bearer $TOKEN"
echo -e "\n\n"

# 8. Получение ID чата
CHAT_ID=$(curl -s -X GET "$API_BASE/api/chats/" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -c "import sys, json; chats=json.load(sys.stdin); print(chats[0]['id'] if chats else '1')")
echo "Chat ID: $CHAT_ID"
echo -e "\n"

# 9. Отправка сообщения
echo "9. POST /api/messages/"
curl -X POST "$API_BASE/api/messages/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\":$CHAT_ID,\"content\":\"Test message\"}"
echo -e "\n\n"

# 10. Получение сообщений
echo "10. GET /api/messages/$CHAT_ID"
curl -X GET "$API_BASE/api/messages/$CHAT_ID" \
  -H "Authorization: Bearer $TOKEN"
echo -e "\n\n"
```

---

## ✅ Статус всех эндпоинтов

| Эндпоинт | Метод | Статус | Описание |
|----------|-------|--------|----------|
| `/api/users/register` | POST | ✅ Работает | Регистрация пользователя |
| `/api/users/login` | POST | ✅ Работает | Вход пользователя |
| `/api/users/me` | GET | ✅ Работает | Информация о текущем пользователе |
| `/api/users/` | GET | ✅ Работает | Список всех пользователей |
| `/api/users/search/{username}` | GET | ✅ Работает | Поиск пользователей |
| `/api/chats/` | GET | ✅ Работает | Список чатов |
| `/api/chats/` | POST | ✅ Работает | Создание чата |
| `/api/messages/` | POST | ✅ Работает | Отправка сообщения |
| `/api/messages/{chat_id}` | GET | ✅ Работает | Получение сообщений |
| `/ws/chat/{chat_id}` | WebSocket | ✅ Работает | WebSocket соединение |

**Все эндпоинты протестированы и работают корректно!** 🎉

