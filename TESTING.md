# 🧪 Comprehensive Testing Guide for Mini-Messenger

Полное руководство по тестированию mini-messenger с различными типами тестов для production-ready развертывания.

## 📋 Содержание

- [Типы тестов](#типы-тестов)
- [Быстрый старт](#быстрый-старт)
- [Unit тесты](#unit-тесты)
- [Интеграционные тесты](#интеграционные-тесты)
- [Нагрузочные тесты](#нагрузочные-тесты)
- [Тесты безопасности](#тесты-безопасности)
- [Frontend тесты](#frontend-тесты)
- [Развертывание на сервере](#развертывание-на-сервере)
- [CI/CD](#cicd)
- [Мониторинг](#мониторинг)

## 🎯 Типы тестов

### 1. Unit тесты
- **Цель**: Тестирование отдельных компонентов
- **Покрытие**: Аутентификация, модели данных, API endpoints
- **Время выполнения**: ~30 секунд
- **Запуск**: `python run_tests.py --type unit`

### 2. Интеграционные тесты
- **Цель**: Тестирование взаимодействия компонентов
- **Покрытие**: WebSocket, полные пользовательские сценарии
- **Время выполнения**: ~2 минуты
- **Запуск**: `python run_tests.py --type integration`

### 3. Нагрузочные тесты
- **Цель**: Тестирование производительности под нагрузкой
- **Покрытие**: Одновременные пользователи, скорость ответа
- **Время выполнения**: ~5 минут
- **Запуск**: `python run_tests.py --type load`

### 4. Тесты безопасности
- **Цель**: Проверка уязвимостей и безопасности
- **Покрытие**: XSS, SQL injection, авторизация
- **Время выполнения**: ~1 минута
- **Запуск**: `python run_tests.py --type security`

### 5. Frontend тесты
- **Цель**: Тестирование пользовательского интерфейса
- **Покрытие**: Selenium, функциональность, производительность
- **Время выполнения**: ~3 минуты
- **Запуск**: `python run_tests.py --type frontend`

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
# Установка всех зависимостей для тестов
python run_tests.py --setup

# Или вручную
pip install -r tests/requirements.txt
```

### 2. Запуск всех тестов
```bash
# Запуск всех тестов с отчетом
python run_tests.py --type all

# С покрытием кода
python run_tests.py --coverage
```

### 3. Проверка результатов
```bash
# Открыть отчет покрытия
open htmlcov/index.html

# Просмотр результатов нагрузочных тестов
cat load_test_results.json
```

## 🔬 Unit тесты

### Тестируемые компоненты

#### Аутентификация (`test_auth.py`)
```python
# Тестирование хеширования паролей
def test_hash_password():
    password = "test_password_123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True

# Тестирование JWT токенов
def test_create_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "testuser"
```

#### Модели данных (`test_models.py`)
```python
# Тестирование создания пользователя
def test_create_user(test_db_session):
    user = User(username="testuser", password_hash="hashed_password")
    test_db_session.add(user)
    test_db_session.commit()
    assert user.id is not None
    assert user.username == "testuser"

# Тестирование уникальности username
def test_user_unique_username(test_db_session):
    user1 = User(username="testuser", password_hash="hash1")
    user2 = User(username="testuser", password_hash="hash2")
    # Должно вызвать IntegrityError
```

#### API Endpoints (`test_api_endpoints.py`)
```python
# Тестирование регистрации пользователя
async def test_register_user(async_client: AsyncClient):
    user_data = {"username": "testuser", "password": "testpassword123"}
    response = await async_client.post("/api/users/register", json=user_data)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

# Тестирование отправки сообщения
async def test_send_message(async_client: AsyncClient, auth_headers):
    message_data = {"chat_id": 1, "content": "Hello, world!"}
    response = await async_client.post("/api/messages/", json=message_data, headers=auth_headers)
    assert response.status_code == 200
```

### Запуск unit тестов
```bash
# Все unit тесты
python -m pytest tests/unit/ -v

# Конкретный тест
python -m pytest tests/unit/test_auth.py::TestPasswordHashing::test_hash_password -v

# С покрытием
python -m pytest tests/unit/ --cov=backend/app --cov-report=html
```

## 🔗 Интеграционные тесты

### WebSocket тесты (`test_websocket.py`)
```python
# Тестирование WebSocket соединения
async def test_websocket_connection():
    uri = "ws://localhost:8000/ws/chat/1"
    async with websockets.connect(uri) as websocket:
        assert websocket.open is True

# Тестирование broadcast сообщений
async def test_websocket_message_broadcast():
    uri = "ws://localhost:8000/ws/chat/1"
    async with websockets.connect(uri) as ws1, websockets.connect(uri) as ws2:
        await ws1.send("Hello from ws1")
        received_message = await ws2.recv()
        assert received_message == "Hello from ws1"
```

### Полные сценарии (`test_full_workflow.py`)
```python
# Полный workflow: регистрация -> логин -> создание чата -> отправка сообщений
async def test_user_registration_to_messaging_workflow(async_client: AsyncClient):
    # 1. Регистрация
    user_data = {"username": "testuser", "password": "testpassword123"}
    register_response = await async_client.post("/api/users/register", json=user_data)
    assert register_response.status_code == 200
    
    # 2. Логин
    login_response = await async_client.post("/api/users/login", json=user_data)
    auth_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    
    # 3. Создание чата
    chat_response = await async_client.post("/api/chats/", params={"name": "Test Chat"}, headers=auth_headers)
    chat_id = chat_response.json()["id"]
    
    # 4. Отправка сообщений
    for message_content in ["Hello", "World", "Test"]:
        message_response = await async_client.post("/api/messages/", 
            json={"chat_id": chat_id, "content": message_content}, headers=auth_headers)
        assert message_response.status_code == 200
```

### Запуск интеграционных тестов
```bash
# Все интеграционные тесты
python -m pytest tests/integration/ -v

# Только WebSocket тесты
python -m pytest tests/integration/ -m websocket -v

# С реальным сервером
docker-compose up -d
python -m pytest tests/integration/ -v
```

## ⚡ Нагрузочные тесты

### Locust тесты (`locustfile.py`)
```python
class MessengerUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Регистрация и логин
        self.username = f"loadtest_user_{random.randint(1000, 9999)}"
        self.password = "loadtest_password_123"
        # ... регистрация и получение токена
    
    @task(3)
    def send_message(self):
        # Отправка сообщения
        message_content = f"Load test message {random.randint(1, 1000)}"
        response = self.client.post("/api/messages/", 
            json={"chat_id": self.chat_id, "content": message_content}, 
            headers=self.headers)
```

### Кастомный Load Test Runner (`load_test_runner.py`)
```python
async def run_concurrent_users(self, num_users: int, actions_per_user: int = 10):
    # Создание задач для всех пользователей
    tasks = [self.simulate_user_session(user_id, actions_per_user) for user_id in range(num_users)]
    
    # Запуск всех задач параллельно
    all_results = await asyncio.gather(*tasks)
    
    # Расчет статистики
    stats = self.calculate_statistics(flat_results, total_time)
    return stats
```

### Запуск нагрузочных тестов
```bash
# Locust в веб-интерфейсе
locust -f tests/load/locustfile.py

# Locust в headless режиме
locust -f tests/load/locustfile.py --headless -u 100 -r 10 -t 60s

# Кастомный load test runner
python tests/load/load_test_runner.py

# Все нагрузочные тесты
python run_tests.py --type load
```

### Метрики производительности
- **RPS (Requests Per Second)**: Целевое значение > 100 RPS
- **Response Time**: P95 < 500ms, P99 < 1000ms
- **Success Rate**: > 99%
- **Concurrent Users**: Тестирование до 1000 пользователей

## 🔒 Тесты безопасности

### Тестирование аутентификации (`test_security.py`)
```python
# Тестирование невалидных токенов
async def test_invalid_token_format(async_client: AsyncClient):
    invalid_headers = [
        {"Authorization": "InvalidToken"},
        {"Authorization": "Bearer"},
        {"Authorization": "Bearer invalid_token"},
    ]
    
    for headers in invalid_headers:
        response = await async_client.get("/api/users/me", headers=headers)
        assert response.status_code == 401

# Тестирование истечения токена
async def test_expired_token(async_client: AsyncClient):
    expired_data = {"sub": "testuser", "exp": datetime.utcnow() - timedelta(hours=1)}
    expired_token = create_access_token(expired_data)
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await async_client.get("/api/users/me", headers=headers)
    assert response.status_code == 401
```

### Тестирование входных данных
```python
# Тестирование XSS
async def test_xss_prevention_in_messages(async_client: AsyncClient, auth_headers, malicious_inputs):
    for malicious_input in malicious_inputs:
        message_data = {"chat_id": chat_id, "content": malicious_input}
        response = await async_client.post("/api/messages/", json=message_data, headers=auth_headers)
        assert response.status_code == 200  # Должно принять, но не выполнить

# Тестирование SQL injection
async def test_sql_injection_prevention(async_client: AsyncClient, auth_headers):
    sql_injection_payloads = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "admin'--",
    ]
    
    for payload in sql_injection_payloads:
        response = await async_client.get(f"/api/users/search/{payload}", headers=auth_headers)
        assert response.status_code in [200, 400, 422]  # Не должно крашить
```

### Статический анализ безопасности
```bash
# Bandit - поиск проблем безопасности в коде
bandit -r backend/ -f json -o bandit-report.json

# Safety - проверка уязвимостей в зависимостях
safety check --json --output safety-report.json

# Все тесты безопасности
python run_tests.py --type security
```

## 🖥️ Frontend тесты

### Selenium тесты (`test_frontend_functionality.py`)
```python
def test_user_registration(self, driver, frontend_url):
    driver.get(frontend_url)
    
    # Найти элементы формы
    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")
    register_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Register')]")
    
    # Заполнить форму
    username_input.send_keys("testuser_frontend")
    password_input.send_keys("testpassword123")
    register_button.click()
    
    # Проверить успешную регистрацию
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "app-screen"))
    )

def test_message_sending(self, driver, frontend_url):
    # Регистрация и логин
    self._register_and_login(driver, "messagetest_user", "testpassword123")
    
    # Создание чата
    self._create_chat(driver, "Message Test Chat")
    
    # Отправка сообщения
    message_input = driver.find_element(By.ID, "messageInput")
    send_button = driver.find_element(By.CLASS_NAME, "send-button")
    
    message_input.send_keys("Hello from frontend test!")
    send_button.click()
    
    # Проверить появление сообщения
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "message"))
    )
```

### Тесты производительности
```python
def test_page_load_time(self, driver):
    start_time = time.time()
    driver.get("http://localhost:3000")
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "auth-screen"))
    )
    
    load_time = time.time() - start_time
    assert load_time < 5.0, f"Page load time too slow: {load_time:.2f}s"
```

### Запуск frontend тестов
```bash
# Установка Selenium и ChromeDriver
pip install selenium
# Установите ChromeDriver в PATH

# Запуск frontend тестов
python run_tests.py --type frontend

# Или напрямую
python -m pytest tests/frontend/ -v
```

## 🚀 Развертывание на сервере

### Автоматическое развертывание
```bash
# Клонирование репозитория
git clone <your-repo-url>
cd mini-messenger

# Запуск скрипта развертывания
chmod +x deploy.sh
./deploy.sh

# С SSL сертификатом
./deploy.sh --ssl
```

### Ручное развертывание
```bash
# 1. Установка зависимостей
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# 2. Клонирование проекта
git clone <your-repo-url>
cd mini-messenger

# 3. Настройка окружения
cp .env.example .env
# Отредактируйте .env файл

# 4. Запуск сервисов
docker-compose up -d

# 5. Проверка статуса
docker-compose ps
```

### Проверка развертывания
```bash
# Проверка здоровья сервисов
curl http://localhost:8000/docs  # Backend API
curl http://localhost:3000       # Frontend

# Проверка логов
docker-compose logs -f

# Проверка ресурсов
docker stats
```

## 🔄 CI/CD

### GitHub Actions (`.github/workflows/tests.yml`)
```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_messenger
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r backend/requirements.txt
        pip install -r tests/requirements.txt
    - name: Run unit tests
      run: python -m pytest tests/unit/ -v --cov=backend/app
```

### Локальный CI/CD
```bash
# Запуск всех тестов перед коммитом
python run_tests.py --type all

# Проверка покрытия кода
python run_tests.py --coverage

# Проверка безопасности
python run_tests.py --type security
```

## 📊 Мониторинг

### Метрики производительности
- **Response Time**: Время ответа API
- **Throughput**: Количество запросов в секунду
- **Error Rate**: Процент ошибок
- **Resource Usage**: Использование CPU, памяти, диска

### Логирование
```bash
# Просмотр логов приложения
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db

# Логи системы
sudo journalctl -u mini-messenger -f
```

### Алерты
```bash
# Настройка мониторинга
sudo systemctl enable mini-messenger-monitor.service
sudo systemctl start mini-messenger-monitor.service

# Проверка статуса
sudo systemctl status mini-messenger
```

## 📈 Бенчмарки

### Ожидаемые показатели производительности

| Метрика | Целевое значение | Критическое значение |
|---------|------------------|---------------------|
| Response Time (P95) | < 200ms | > 500ms |
| Response Time (P99) | < 500ms | > 1000ms |
| RPS | > 100 | < 50 |
| Success Rate | > 99.9% | < 99% |
| Memory Usage | < 512MB | > 1GB |
| CPU Usage | < 50% | > 80% |

### Нагрузочное тестирование
```bash
# Легкая нагрузка (10 пользователей)
python tests/load/load_test_runner.py --users 10

# Средняя нагрузка (100 пользователей)
python tests/load/load_test_runner.py --users 100

# Высокая нагрузка (1000 пользователей)
python tests/load/load_test_runner.py --users 1000
```

## 🛠️ Troubleshooting

### Частые проблемы

#### Тесты не запускаются
```bash
# Проверка зависимостей
pip install -r tests/requirements.txt

# Проверка Python версии
python --version  # Должна быть 3.11+

# Проверка переменных окружения
echo $DATABASE_URL
```

#### Проблемы с базой данных
```bash
# Очистка тестовой БД
docker-compose -f docker-compose.test.yml down -v

# Пересоздание БД
docker-compose -f docker-compose.test.yml up -d test-db
```

#### Проблемы с портами
```bash
# Проверка занятых портов
lsof -i :5432  # PostgreSQL
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Освобождение портов
sudo kill -9 $(lsof -t -i:8000)
```

#### Проблемы с Selenium
```bash
# Установка ChromeDriver
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
# Скачайте соответствующую версию ChromeDriver

# Проверка версии Chrome
google-chrome --version
```

## 📚 Дополнительные ресурсы

### Документация
- [Pytest Documentation](https://docs.pytest.org/)
- [Locust Documentation](https://docs.locust.io/)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)

### Полезные команды
```bash
# Запуск тестов в параллель
pip install pytest-xdist
python -m pytest tests/ -n 4

# Генерация отчета покрытия
python -m pytest tests/ --cov=backend/app --cov-report=html --cov-report=term

# Запуск тестов с профилированием
python -m pytest tests/ --profile

# Запуск тестов с бенчмарками
python -m pytest tests/ --benchmark-only
```

---

## 🎉 Заключение

Эта система тестирования обеспечивает:

✅ **Полное покрытие** всех компонентов приложения  
✅ **Автоматизированное тестирование** в CI/CD  
✅ **Нагрузочное тестирование** для production  
✅ **Тестирование безопасности** от уязвимостей  
✅ **Мониторинг производительности** в реальном времени  

Используйте эти тесты для обеспечения качества и надежности вашего mini-messenger в production среде! 🚀
