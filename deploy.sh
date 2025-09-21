#!/bin/bash

# Mini-Messenger Deployment Script
# Скрипт для развертывания на сервере

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="mini-messenger"
BACKUP_DIR="/opt/backups/${PROJECT_NAME}"
LOG_FILE="/var/log/${PROJECT_NAME}/deploy.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    # Check available disk space (at least 2GB)
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 2097152 ]; then  # 2GB in KB
        warning "Low disk space. At least 2GB recommended."
    fi
    
    # Check available memory (at least 1GB)
    available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [ "$available_memory" -lt 1024 ]; then
        warning "Low available memory. At least 1GB recommended."
    fi
    
    success "System requirements check passed"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    sudo mkdir -p "$BACKUP_DIR"
    sudo mkdir -p "/var/log/${PROJECT_NAME}"
    sudo mkdir -p "/opt/${PROJECT_NAME}"
    
    # Set proper permissions
    sudo chown -R $USER:$USER "$BACKUP_DIR"
    sudo chown -R $USER:$USER "/var/log/${PROJECT_NAME}"
    sudo chown -R $USER:$USER "/opt/${PROJECT_NAME}"
    
    success "Directories created"
}

# Backup existing deployment
backup_existing() {
    if [ -d "/opt/${PROJECT_NAME}" ] && [ "$(ls -A /opt/${PROJECT_NAME})" ]; then
        log "Backing up existing deployment..."
        
        backup_timestamp=$(date +'%Y%m%d_%H%M%S')
        backup_path="${BACKUP_DIR}/backup_${backup_timestamp}"
        
        sudo cp -r "/opt/${PROJECT_NAME}" "$backup_path"
        sudo chown -R $USER:$USER "$backup_path"
        
        success "Backup created at $backup_path"
    fi
}

# Deploy application
deploy_application() {
    log "Deploying application..."
    
    # Copy application files
    sudo cp -r . "/opt/${PROJECT_NAME}/"
    sudo chown -R $USER:$USER "/opt/${PROJECT_NAME}"
    
    cd "/opt/${PROJECT_NAME}"
    
    # Build and start services
    log "Building Docker images..."
    docker-compose build --no-cache
    
    log "Starting services..."
    docker-compose up -d
    
    success "Application deployed"
}

# Run health checks
health_check() {
    log "Running health checks..."
    
    # Wait for services to start
    sleep 30
    
    # Check backend health
    if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
        success "Backend is healthy"
    else
        error "Backend health check failed"
    fi
    
    # Check frontend health
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        success "Frontend is healthy"
    else
        error "Frontend health check failed"
    fi
    
    # Check database connection
    if docker-compose exec -T db pg_isready -U user -d messenger > /dev/null 2>&1; then
        success "Database is healthy"
    else
        error "Database health check failed"
    fi
}

# Run tests
run_tests() {
    log "Running deployment tests..."
    
    cd "/opt/${PROJECT_NAME}"
    
    # Run basic smoke tests
    python3 -c "
import requests
import time

# Wait for services to be ready
time.sleep(10)

# Test backend API
try:
    response = requests.get('http://localhost:8000/docs', timeout=10)
    if response.status_code == 200:
        print('Backend API: OK')
    else:
        print(f'Backend API: FAILED ({response.status_code})')
        exit(1)
except Exception as e:
    print(f'Backend API: ERROR ({e})')
    exit(1)

# Test frontend
try:
    response = requests.get('http://localhost:3000', timeout=10)
    if response.status_code == 200:
        print('Frontend: OK')
    else:
        print(f'Frontend: FAILED ({response.status_code})')
        exit(1)
except Exception as e:
    print(f'Frontend: ERROR ({e})')
    exit(1)

print('All smoke tests passed!')
"
    
    success "Deployment tests passed"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Create systemd service for monitoring
    sudo tee /etc/systemd/system/${PROJECT_NAME}-monitor.service > /dev/null <<EOF
[Unit]
Description=Mini-Messenger Health Monitor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/${PROJECT_NAME}
ExecStart=/bin/bash -c 'while true; do docker-compose ps | grep -q "Up" || systemctl restart ${PROJECT_NAME}; sleep 60; done'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Create systemd service for the application
    sudo tee /etc/systemd/system/${PROJECT_NAME}.service > /dev/null <<EOF
[Unit]
Description=Mini-Messenger Application
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$USER
WorkingDirectory=/opt/${PROJECT_NAME}
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable services
    sudo systemctl daemon-reload
    sudo systemctl enable ${PROJECT_NAME}.service
    sudo systemctl enable ${PROJECT_NAME}-monitor.service
    
    success "Monitoring setup completed"
}

# Setup log rotation
setup_log_rotation() {
    log "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/${PROJECT_NAME} > /dev/null <<EOF
/var/log/${PROJECT_NAME}/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        docker-compose -f /opt/${PROJECT_NAME}/docker-compose.yml restart backend frontend
    endscript
}
EOF
    
    success "Log rotation setup completed"
}

# Setup firewall
setup_firewall() {
    log "Setting up firewall..."
    
    # Check if ufw is available
    if command -v ufw &> /dev/null; then
        # Allow necessary ports
        sudo ufw allow 22/tcp    # SSH
        sudo ufw allow 80/tcp    # HTTP
        sudo ufw allow 443/tcp   # HTTPS
        sudo ufw allow 3000/tcp  # Frontend
        sudo ufw allow 8000/tcp  # Backend
        
        # Enable firewall if not already enabled
        if ! sudo ufw status | grep -q "Status: active"; then
            sudo ufw --force enable
        fi
        
        success "Firewall configured"
    else
        warning "UFW not available. Please configure firewall manually."
    fi
}

# Setup SSL (optional)
setup_ssl() {
    if [ "$1" = "--ssl" ]; then
        log "Setting up SSL with Let's Encrypt..."
        
        # Install certbot if not available
        if ! command -v certbot &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y certbot
        fi
        
        # Get domain name
        read -p "Enter your domain name: " domain_name
        
        if [ -n "$domain_name" ]; then
            # Generate SSL certificate
            sudo certbot certonly --standalone -d "$domain_name" --non-interactive --agree-tos --email admin@$domain_name
            
            # Create nginx config for SSL
            sudo tee /etc/nginx/sites-available/${PROJECT_NAME} > /dev/null <<EOF
server {
    listen 80;
    server_name $domain_name;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl;
    server_name $domain_name;
    
    ssl_certificate /etc/letsencrypt/live/$domain_name/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$domain_name/privkey.pem;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
            
            # Enable site
            sudo ln -sf /etc/nginx/sites-available/${PROJECT_NAME} /etc/nginx/sites-enabled/
            sudo nginx -t && sudo systemctl reload nginx
            
            success "SSL setup completed for $domain_name"
        fi
    fi
}

# Main deployment function
main() {
    log "Starting Mini-Messenger deployment..."
    
    check_root
    check_requirements
    create_directories
    backup_existing
    deploy_application
    health_check
    run_tests
    setup_monitoring
    setup_log_rotation
    setup_firewall
    setup_ssl "$@"
    
    success "Deployment completed successfully!"
    
    echo ""
    echo "=========================================="
    echo "Mini-Messenger is now running!"
    echo "=========================================="
    echo "Frontend: http://localhost:3000"
    echo "Backend API: http://localhost:8000"
    echo "API Documentation: http://localhost:8000/docs"
    echo ""
    echo "Useful commands:"
    echo "  View logs: docker-compose -f /opt/${PROJECT_NAME}/docker-compose.yml logs -f"
    echo "  Restart: sudo systemctl restart ${PROJECT_NAME}"
    echo "  Stop: sudo systemctl stop ${PROJECT_NAME}"
    echo "  Status: sudo systemctl status ${PROJECT_NAME}"
    echo ""
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--ssl]"
        echo ""
        echo "Options:"
        echo "  --ssl    Setup SSL with Let's Encrypt"
        echo "  --help   Show this help message"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
