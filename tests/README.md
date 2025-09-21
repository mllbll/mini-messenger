# Mini-Messenger Test Suite

Комплексная система тестирования для mini-messenger, включающая unit тесты, интеграционные тесты, нагрузочные тесты и тесты безопасности.

## Структура тестов

```
tests/
├── unit/                    # Unit тесты
│   ├── test_auth.py        # Тесты аутентификации
│   ├── test_models.py      # Тесты моделей данных
│   └── test_api_endpoints.py # Тесты API endpoints
├── integration/            # Интеграционные тесты
│   ├── test_websocket.py   # Тесты WebSocket
│   └── test_full_workflow.py # Тесты полных сценариев
├── load/                   # Нагрузочные тесты
│   ├── locustfile.py       # Locust тесты
│   └── load_test_runner.py # Кастомный load test runner
├── security/               # Тесты безопасности
│   └── test_security.py    # Тесты безопасности
├── frontend/               # Тесты frontend
│   └── test_frontend_functionality.py # Selenium тесты
├── fixtures/               # Тестовые данные
├── data/                   # Данные для тестов
├── conftest.py            # Pytest конфигурация
└── requirements.txt       # Зависимости для тестов
```

## Установка зависимостей

```bash
# Установка всех зависимостей для тестов
pip install -r tests/requirements.txt

# Или используйте скрипт
python run_tests.py --setup
```

## Запуск тестов

### Все тесты
```bash
python run_tests.py --type all
```

### Unit тесты
```bash
python run_tests.py --type unit
# или
python -m pytest tests/unit/ -v
```

### Интеграционные тесты
```bash
python run_tests.py --type integration
# или
python -m pytest tests/integration/ -v
```

### Тесты безопасности
```bash
python run_tests.py --type security
# или
python -m pytest tests/security/ -v
```

### Нагрузочные тесты
```bash
python run_tests.py --type load
# или
python tests/load/load_test_runner.py
```

### Frontend тесты
```bash
python run_tests.py --type frontend
# или
python -m pytest tests/frontend/ -v
```

### С покрытием кода
```bash
python run_tests.py --coverage
# или
python -m pytest tests/ --cov=backend/app --cov-report=html
```

## Нагрузочные тесты

### Locust
```bash
# Запуск в веб-интерфейсе
locust -f tests/load/locustfile.py

# Запуск в headless режиме
locust -f tests/load/locustfile.py --headless -u 100 -r 10 -t 60s
```

### Кастомный Load Test Runner
```bash
python tests/load/load_test_runner.py
```

## Тесты безопасности

### Bandit (статический анализ)
```bash
bandit -r backend/ -f json -o bandit-report.json
```

### Safety (проверка уязвимостей)
```bash
safety check --json --output safety-report.json
```

## Frontend тесты

Требуется установка Selenium и ChromeDriver:

```bash
pip install selenium
# Установите ChromeDriver в PATH
```

## Docker тестирование

```bash
# Запуск всех тестов в Docker
docker-compose -f docker-compose.test.yml up --build

# Запуск конкретных тестов
docker-compose -f docker-compose.test.yml run test-backend python -m pytest tests/unit/ -v
```

## CI/CD

Тесты автоматически запускаются в GitHub Actions при push и pull request.

Конфигурация: `.github/workflows/tests.yml`

## Метрики и отчеты

### Покрытие кода
- HTML отчет: `htmlcov/index.html`
- XML отчет: `coverage.xml`

### Нагрузочные тесты
- Locust отчет: `load_test_report.html`
- JSON отчет: `load_test_results.json`

### Безопасность
- Bandit отчет: `bandit-report.json`
- Safety отчет: `safety-report.json`

## Конфигурация

### pytest.ini
Основная конфигурация pytest с маркерами и настройками покрытия.

### conftest.py
Общие фикстуры для всех тестов:
- Тестовая база данных
- HTTP клиенты
- Тестовые пользователи
- WebSocket URL

## Маркеры тестов

- `@pytest.mark.unit` - Unit тесты
- `@pytest.mark.integration` - Интеграционные тесты
- `@pytest.mark.load` - Нагрузочные тесты
- `@pytest.mark.security` - Тесты безопасности
- `@pytest.mark.slow` - Медленные тесты
- `@pytest.mark.websocket` - WebSocket тесты
- `@pytest.mark.database` - Тесты базы данных

## Примеры использования

### Запуск только быстрых тестов
```bash
python -m pytest tests/ -m "not slow" -v
```

### Запуск тестов с определенным маркером
```bash
python -m pytest tests/ -m "websocket" -v
```

### Запуск тестов в параллель
```bash
pip install pytest-xdist
python -m pytest tests/ -n 4
```

## Отладка тестов

### Подробный вывод
```bash
python -m pytest tests/ -v -s
```

### Остановка на первой ошибке
```bash
python -m pytest tests/ -x
```

### Запуск конкретного теста
```bash
python -m pytest tests/unit/test_auth.py::TestPasswordHashing::test_hash_password -v
```

## Производительность

### Бенчмарки
```bash
python -m pytest tests/ --benchmark-only
```

### Профилирование
```bash
python -m pytest tests/ --profile
```

## Мониторинг

Тесты включают метрики:
- Время ответа API
- Использование памяти
- Нагрузка на CPU
- Количество подключений к БД
- WebSocket соединения

## Troubleshooting

### Проблемы с базой данных
```bash
# Очистка тестовой БД
docker-compose -f docker-compose.test.yml down -v
```

### Проблемы с портами
```bash
# Проверка занятых портов
lsof -i :5432
lsof -i :8000
```

### Проблемы с зависимостями
```bash
# Переустановка зависимостей
pip install -r tests/requirements.txt --force-reinstall
```
