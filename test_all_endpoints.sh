#!/bin/bash

# Скрипт для тестирования всех эндпоинтов
# Использование: ./test_all_endpoints.sh

API_BASE="http://localhost:8000"
TEST_USER="testuser_$(date +%s)"
TEST_PASS="testpass123"

echo "=========================================="
echo "Тестирование всех эндпоинтов API"
echo "=========================================="
echo ""

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_result() {
    local name=$1
    local response=$2
    local expected_code=$3
    
    http_code=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE/d')
    
    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ $name (HTTP $http_code)${NC}"
        echo "$body" | python3 -m json.tool 2>/dev/null | head -5 || echo "$body" | head -3
        return 0
    else
        echo -e "${RED}✗ $name (HTTP $http_code, ожидался $expected_code)${NC}"
        echo "$body" | head -3
        return 1
    fi
}

# 1. Регистрация
echo "1. POST /api/users/register"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$API_BASE/api/users/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASS\"}")
test_result "Регистрация пользователя" "$response" "200"
echo ""

# 2. Вход
echo "2. POST /api/users/login"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$API_BASE/api/users/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASS\"}")
TOKEN=$(echo "$response" | sed '/HTTP_CODE/d' | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
test_result "Вход пользователя" "$response" "200"
echo ""

if [ -z "$TOKEN" ]; then
    echo -e "${RED}Не удалось получить токен. Тестирование остановлено.${NC}"
    exit 1
fi

echo "Token: ${TOKEN:0:30}..."
echo ""

# 3. Получение информации о себе
echo "3. GET /api/users/me"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "$API_BASE/api/users/me" \
    -H "Authorization: Bearer $TOKEN")
test_result "Получение информации о текущем пользователе" "$response" "200"
echo ""

# 4. Список пользователей
echo "4. GET /api/users/"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "$API_BASE/api/users/" \
    -H "Authorization: Bearer $TOKEN")
test_result "Получение списка пользователей" "$response" "200"
echo ""

# 5. Поиск пользователей
echo "5. GET /api/users/search/test"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "$API_BASE/api/users/search/test" \
    -H "Authorization: Bearer $TOKEN")
test_result "Поиск пользователей" "$response" "200"
echo ""

# 6. Список чатов
echo "6. GET /api/chats/"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "$API_BASE/api/chats/" \
    -H "Authorization: Bearer $TOKEN")
test_result "Получение списка чатов" "$response" "200"
echo ""

# 7. Создание чата
echo "7. POST /api/chats/?name=TestChat"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$API_BASE/api/chats/?name=TestChat" \
    -H "Authorization: Bearer $TOKEN")
test_result "Создание публичного чата" "$response" "200"
CHAT_ID=$(echo "$response" | sed '/HTTP_CODE/d' | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', '1'))" 2>/dev/null)
echo ""

# 8. Отправка сообщения
if [ ! -z "$CHAT_ID" ] && [ "$CHAT_ID" != "None" ]; then
    echo "8. POST /api/messages/ (Chat ID: $CHAT_ID)"
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$API_BASE/api/messages/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\":$CHAT_ID,\"content\":\"Test message from script\"}")
    test_result "Отправка сообщения" "$response" "200"
    echo ""
    
    # 9. Получение сообщений
    echo "9. GET /api/messages/$CHAT_ID"
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "$API_BASE/api/messages/$CHAT_ID" \
        -H "Authorization: Bearer $TOKEN")
    test_result "Получение сообщений чата" "$response" "200"
    echo ""
fi

# 10. Тест ошибок
echo "10. Тестирование обработки ошибок"
echo "   - Без токена:"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "$API_BASE/api/users/me")
http_code=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$http_code" = "401" ]; then
    echo -e "${GREEN}✓ Корректная ошибка 401${NC}"
else
    echo -e "${RED}✗ Ожидалась ошибка 401, получен $http_code${NC}"
fi

echo ""
echo "=========================================="
echo "Тестирование завершено"
echo "=========================================="

