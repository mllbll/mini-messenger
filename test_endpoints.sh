#!/bin/bash

# Скрипт для тестирования всех эндпоинтов API
# Использование: ./test_endpoints.sh

API_BASE="http://localhost:8000"
TOKEN_FILE="/tmp/messenger_token.txt"

echo "=========================================="
echo "Тестирование всех эндпоинтов Mini Messenger"
echo "=========================================="
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для получения токена
get_token() {
    if [ -f "$TOKEN_FILE" ]; then
        cat "$TOKEN_FILE"
    else
        TOKEN=$(curl -s -X POST "$API_BASE/api/users/login" \
            -H "Content-Type: application/json" \
            -d '{"username":"curluser","password":"curlpass123"}' | \
            python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
        if [ ! -z "$TOKEN" ]; then
            echo "$TOKEN" > "$TOKEN_FILE"
        fi
        echo "$TOKEN"
    fi
}

# Функция для выполнения запроса
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "${YELLOW}Тест: $description${NC}"
    echo "Запрос: $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        if [ -z "$data" ]; then
            response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "$API_BASE$endpoint" \
                -H "Authorization: Bearer $(get_token)")
        else
            response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "$API_BASE$endpoint" \
                -H "Authorization: Bearer $(get_token)" \
                -H "Content-Type: application/json")
        fi
    else
        response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X $method "$API_BASE$endpoint" \
            -H "Authorization: Bearer $(get_token)" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE/d')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ Успешно (HTTP $http_code)${NC}"
        echo "Ответ: $body" | head -5
    else
        echo -e "${RED}✗ Ошибка (HTTP $http_code)${NC}"
        echo "Ответ: $body"
    fi
    echo ""
}

# Создаем тестового пользователя если его нет
echo "1. Регистрация пользователя"
echo "POST /api/users/register"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$API_BASE/api/users/register" \
    -H "Content-Type: application/json" \
    -d '{"username":"curluser","password":"curlpass123"}')
http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_CODE/d')

if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
    echo -e "${GREEN}✓ Пользователь создан (HTTP $http_code)${NC}"
    echo "Ответ: $body"
elif echo "$body" | grep -q "already exists"; then
    echo -e "${YELLOW}⚠ Пользователь уже существует${NC}"
else
    echo -e "${RED}✗ Ошибка регистрации (HTTP $http_code)${NC}"
    echo "Ответ: $body"
fi
echo ""

# Получаем токен
echo "2. Вход пользователя"
echo "POST /api/users/login"
TOKEN=$(curl -s -X POST "$API_BASE/api/users/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"curluser","password":"curlpass123"}' | \
    python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ ! -z "$TOKEN" ]; then
    echo "$TOKEN" > "$TOKEN_FILE"
    echo -e "${GREEN}✓ Токен получен${NC}"
    echo "Token: ${TOKEN:0:30}..."
else
    echo -e "${RED}✗ Не удалось получить токен${NC}"
    exit 1
fi
echo ""

# Тестируем все эндпоинты
echo "=========================================="
echo "Тестирование защищенных эндпоинтов"
echo "=========================================="
echo ""

test_endpoint "GET" "/api/users/me" "" "Получение информации о текущем пользователе"

test_endpoint "GET" "/api/users/" "" "Получение списка всех пользователей"

test_endpoint "GET" "/api/users/search/curl" "" "Поиск пользователей"

test_endpoint "GET" "/api/chats/" "" "Получение списка чатов"

test_endpoint "POST" "/api/chats/" '{"name":"Test Chat from curl"}' "Создание публичного чата"

# Получаем ID чата для тестирования сообщений
CHAT_ID=$(curl -s -X GET "$API_BASE/api/chats/" \
    -H "Authorization: Bearer $(get_token)" | \
    python3 -c "import sys, json; chats=json.load(sys.stdin); print(chats[0]['id'] if chats else '1')" 2>/dev/null)

if [ ! -z "$CHAT_ID" ] && [ "$CHAT_ID" != "None" ]; then
    echo -e "${YELLOW}Используем чат ID: $CHAT_ID${NC}"
    echo ""
    
    test_endpoint "POST" "/api/messages/" "{\"chat_id\":$CHAT_ID,\"content\":\"Test message from curl script\"}" "Отправка сообщения"
    
    test_endpoint "GET" "/api/messages/$CHAT_ID" "" "Получение сообщений чата"
else
    echo -e "${RED}✗ Не удалось получить ID чата${NC}"
fi

echo "=========================================="
echo "Тестирование завершено"
echo "=========================================="

