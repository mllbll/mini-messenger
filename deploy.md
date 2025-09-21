# 🚀 Пошаговое развертывание Mini-Messenger на Ubuntu сервер

Полное руководство по развертыванию mini-messenger на пустой Ubuntu сервер.

## 📋 Содержание

- [Подготовка сервера](#подготовка-сервера)
- [Установка Docker](#установка-docker-и-docker-compose)
- [Загрузка проекта](#загрузка-проекта)
- [Настройка окружения](#настройка-окружения)
- [Развертывание](#развертывание)
- [Проверка развертывания](#проверка-развертывания)
- [Настройка безопасности](#настройка-безопасности)
- [Настройка SSL](#настройка-ssl-опционально)
- [Мониторинг и логирование](#мониторинг-и-логирование)
- [Запуск тестов](#запуск-тестов)
- [Полезные команды](#полезные-команды)
- [Доступ к приложению](#доступ-к-приложению)
- [Финальная проверка](#финальная-проверка)

## 🖥️ Подготовка сервера

### 1. Подключение к серверу
```bash
# Подключение по SSH
ssh username@your-server-ip

# Или если используете ключи
ssh -i your-key.pem ubuntu@your-server-ip
```

### 2. Обновление системы
```bash
# Обновление пакетов
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y curl wget git vim htop
```

## 🐳 Установка Docker и Docker Compose

### 3. Установка Docker
```bash
# Удаление старых версий Docker
sudo apt remove -y docker docker-engine docker.io containerd runc

# Установка зависимостей
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Добавление официального GPG ключа Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавление репозитория Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Обновление списка пакетов
sudo apt update

# Установка Docker
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Включение автозапуска Docker
sudo systemctl enable docker
sudo systemctl start docker
```

### 4. Установка Docker Compose
```bash
# Скачивание Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Установка прав на выполнение
sudo chmod +x /usr/local/bin/docker-compose

# Проверка установки
docker-compose --version
```

### 5. Перезагрузка для применения изменений
```bash
# Выход из SSH сессии
exit

# Повторное подключение
ssh username@your-server-ip

# Проверка Docker без sudo
docker --version
docker-compose --version
```

## 📁 Загрузка проекта

### 6. Клонирование репозитория
```bash
# Переход в домашнюю директорию
cd ~

# Клонирование проекта (замените на ваш репозиторий)
git clone https://github.com/your-username/mini-messenger.git

# Или если у вас нет Git репозитория, создайте архив локально и загрузите
# На локальной машине:
# tar -czf mini-messenger.tar.gz mini-messenger/
# scp mini-messenger.tar.gz username@your-server-ip:~/

# На сервере (если загружали архив):
# tar -xzf mini-messenger.tar.gz
```

### 7. Переход в директорию проекта
```bash
cd mini-messenger

# Проверка файлов
ls -la
```

## ⚙️ Настройка окружения

### 8. Создание файла окружения
```bash
# Создание .env файла
cat > .env << EOF
# Database
POSTGRES_USER=user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=messenger

# Backend
SECRET_KEY=your_super_secret_key_here_change_this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend
VITE_API_URL=http://localhost:8000
EOF

# Установка правильных прав
chmod 600 .env
```

### 9. Настройка прав на файлы
```bash
# Установка прав на скрипт развертывания
chmod +x deploy.sh
chmod +x run_tests.py
```

## 🚀 Развертывание

### 10. Автоматическое развертывание (рекомендуется)
```bash
# Запуск скрипта развертывания
./deploy.sh

# Или с SSL сертификатом (если у вас есть домен)
# ./deploy.sh --ssl
```

### 11. Ручное развертывание (альтернатива)
```bash
# Сборка и запуск контейнеров
docker-compose build --no-cache
docker-compose up -d

# Проверка статуса
docker-compose ps
```

## 🔍 Проверка развертывания

### 12. Проверка работы сервисов
```bash
# Проверка статуса контейнеров
docker-compose ps

# Проверка логов
docker-compose logs -f

# Проверка доступности API
curl http://localhost:8000/docs

# Проверка frontend
curl http://localhost:3000
```

### 13. Проверка портов
```bash
# Проверка открытых портов
sudo netstat -tlnp | grep -E ':(3000|8000|5432)'

# Или с ss
ss -tlnp | grep -E ':(3000|8000|5432)'
```

## 🔒 Настройка безопасности

### 14. Настройка файрвола
```bash
# Установка UFW
sudo apt install -y ufw

# Настройка правил
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Разрешение SSH
sudo ufw allow ssh

# Разрешение HTTP и HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Разрешение портов приложения (только для локального доступа)
sudo ufw allow from 127.0.0.1 to any port 3000
sudo ufw allow from 127.0.0.1 to any port 8000

# Включение файрвола
sudo ufw --force enable

# Проверка статуса
sudo ufw status
```

### 15. Настройка Nginx (для внешнего доступа)
```bash
# Установка Nginx
sudo apt install -y nginx

# Создание конфигурации
sudo tee /etc/nginx/sites-available/mini-messenger > /dev/null << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # Замените на ваш домен или IP

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Включение сайта
sudo ln -s /etc/nginx/sites-available/mini-messenger /etc/nginx/sites-enabled/

# Удаление дефолтного сайта
sudo rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации
sudo nginx -t

# Перезапуск Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## 🔐 Настройка SSL (опционально)

### 16. Установка SSL сертификата
```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение SSL сертификата (замените на ваш домен)
sudo certbot --nginx -d your-domain.com

# Проверка автообновления
sudo certbot renew --dry-run
```

## 📊 Мониторинг и логирование

### 17. Настройка мониторинга
```bash
# Проверка статуса сервисов
sudo systemctl status mini-messenger
sudo systemctl status mini-messenger-monitor

# Просмотр логов
sudo journalctl -u mini-messenger -f

# Логи Docker
docker-compose logs -f
```

### 18. Настройка ротации логов
```bash
# Проверка конфигурации logrotate
sudo logrotate -d /etc/logrotate.d/mini-messenger

# Принудительная ротация
sudo logrotate -f /etc/logrotate.d/mini-messenger
```

## 🧪 Запуск тестов

### 19. Тестирование развертывания
```bash
# Установка зависимостей для тестов
pip3 install -r tests/requirements.txt

# Запуск тестов
python3 run_tests.py --type all

# Или конкретные тесты
python3 run_tests.py --type unit
python3 run_tests.py --type integration
```

## 🛠️ Полезные команды

### 20. Управление сервисами
```bash
# Перезапуск приложения
sudo systemctl restart mini-messenger

# Остановка приложения
sudo systemctl stop mini-messenger

# Запуск приложения
sudo systemctl start mini-messenger

# Проверка статуса
sudo systemctl status mini-messenger

# Просмотр логов
sudo journalctl -u mini-messenger -f
```

### 21. Управление Docker
```bash
# Перезапуск контейнеров
docker-compose restart

# Остановка контейнеров
docker-compose down

# Запуск контейнеров
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Обновление образов
docker-compose pull
docker-compose up -d
```

### 22. Резервное копирование
```bash
# Создание бэкапа базы данных
docker-compose exec db pg_dump -U user messenger > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из бэкапа
docker-compose exec -T db psql -U user messenger < backup_file.sql
```

## 🌐 Доступ к приложению

### 23. Проверка доступности
```bash
# Локальный доступ
curl http://localhost:3000
curl http://localhost:8000/docs

# Внешний доступ (если настроен Nginx)
curl http://your-domain.com
curl http://your-domain.com/api/docs
```

## ✅ Финальная проверка

### 24. Полная проверка системы
```bash
# Проверка всех сервисов
sudo systemctl status mini-messenger
sudo systemctl status nginx
sudo systemctl status docker

# Проверка портов
sudo netstat -tlnp | grep -E ':(80|443|3000|8000|5432)'

# Проверка дискового пространства
df -h

# Проверка памяти
free -h

# Проверка нагрузки
htop
```

## 🎉 Готово!

После выполнения всех шагов ваше приложение будет доступно по адресу:
- **Frontend**: `http://your-domain.com` или `http://your-server-ip`
- **Backend API**: `http://your-domain.com/api` или `http://your-server-ip:8000`
- **API Documentation**: `http://your-domain.com/api/docs`

### 📋 Чек-лист развертывания:
- ✅ Docker и Docker Compose установлены
- ✅ Проект загружен на сервер
- ✅ Контейнеры запущены и работают
- ✅ Файрвол настроен
- ✅ Nginx настроен для внешнего доступа
- ✅ SSL сертификат установлен (если нужно)
- ✅ Мониторинг настроен
- ✅ Тесты пройдены
- ✅ Резервное копирование настроено

## 🚨 Troubleshooting

### Проблемы с Docker
```bash
# Проверка статуса Docker
sudo systemctl status docker

# Перезапуск Docker
sudo systemctl restart docker

# Проверка логов Docker
sudo journalctl -u docker -f
```

### Проблемы с портами
```bash
# Проверка занятых портов
sudo lsof -i :3000
sudo lsof -i :8000
sudo lsof -i :5432

# Освобождение портов
sudo kill -9 $(sudo lsof -t -i:8000)
```

### Проблемы с базой данных
```bash
# Проверка подключения к БД
docker-compose exec db pg_isready -U user -d messenger

# Перезапуск БД
docker-compose restart db

# Просмотр логов БД
docker-compose logs db
```

### Проблемы с Nginx
```bash
# Проверка конфигурации
sudo nginx -t

# Перезапуск Nginx
sudo systemctl restart nginx

# Просмотр логов Nginx
sudo tail -f /var/log/nginx/error.log
```

## 📞 Поддержка

Если у вас возникли проблемы:

1. Проверьте логи: `docker-compose logs -f`
2. Проверьте статус сервисов: `sudo systemctl status mini-messenger`
3. Проверьте порты: `sudo netstat -tlnp`
4. Запустите тесты: `python3 run_tests.py --type all`

Теперь ваш mini-messenger готов к использованию в production! 🚀
