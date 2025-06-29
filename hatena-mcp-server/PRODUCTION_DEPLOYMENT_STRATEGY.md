# 🏭 本格運用サーバー展開戦略

## 📋 展開戦略概要

### Phase 1: テスト環境検証（完了後）
### Phase 2: 運用サーバー展開（本項目）
### Phase 3: 監視・保守体制

## 🔒 セキュリティ考慮事項

### 1. 認証・認可
```yaml
Authentication:
  - API Key rotation schedule: Monthly
  - Environment variable encryption: Required
  - Access log monitoring: Enabled
  - Rate limiting: 100 requests/hour per blog

Authorization:
  - Multi-user support: Planned
  - Role-based access: Admin/User
  - Blog-specific permissions: Implemented
```

### 2. ネットワークセキュリティ
```yaml
Network Security:
  - HTTPS enforcement: Required
  - Certificate management: Auto-renewal
  - Firewall rules: Restrictive
  - VPN access: Recommended

API Security:
  - Request validation: Strict
  - Input sanitization: XML/JSON
  - Output encoding: UTF-8
  - Error message filtering: Enabled
```

### 3. データ保護
```yaml
Data Protection:
  - Sensitive data encryption: AES-256
  - Backup encryption: Enabled
  - Log data retention: 90 days
  - PII handling: Minimal collection

File Security:
  - Configuration file permissions: 600
  - Log file permissions: 640
  - Executable permissions: 755
  - Directory permissions: 750
```

## 🏗️ 運用サーバー構成

### Option A: 軽量単一サーバー（推奨）
```yaml
Hardware Requirements:
  - CPU: 2 cores minimum
  - RAM: 4GB minimum
  - Storage: 50GB SSD
  - Network: 100Mbps

Software Stack:
  - OS: Ubuntu 22.04 LTS / Windows Server 2022
  - Python: 3.11+
  - Reverse Proxy: Nginx
  - Process Manager: systemd / Windows Service
  - Monitoring: Basic logging
```

### Option B: Docker化運用
```yaml
Container Architecture:
  - Application Container: Python app
  - Database Container: PostgreSQL (optional)
  - Cache Container: Redis (optional)
  - Proxy Container: Nginx
  - Monitoring Container: Prometheus + Grafana

Resource Allocation:
  - App Container: 1GB RAM, 1 CPU
  - Database: 2GB RAM, 1 CPU
  - Cache: 512MB RAM, 0.5 CPU
  - Total: 4GB RAM, 3 CPU cores
```

### Option C: クラウド運用
```yaml
AWS/Azure/GCP:
  - Compute: t3.medium (2 vCPU, 4GB RAM)
  - Storage: 50GB GP3 SSD
  - Network: VPC with security groups
  - Load Balancer: Application Load Balancer
  - Auto Scaling: Enabled

Managed Services:
  - Database: RDS PostgreSQL (optional)
  - Cache: ElastiCache Redis (optional)
  - Monitoring: CloudWatch
  - Secrets: AWS Secrets Manager
```

## 📊 本格運用設定項目

### 1. アプリケーション設定
```python
# production_config.py
PRODUCTION_CONFIG = {
    # Performance
    "MAX_CONCURRENT_REQUESTS": 10,
    "REQUEST_TIMEOUT": 30,
    "RETRY_ATTEMPTS": 3,
    "BACKOFF_FACTOR": 2,
    
    # Security
    "API_KEY_ROTATION_DAYS": 30,
    "SESSION_TIMEOUT": 3600,
    "MAX_LOGIN_ATTEMPTS": 5,
    "IP_WHITELIST_ENABLED": True,
    
    # Monitoring
    "LOG_LEVEL": "INFO",
    "METRICS_ENABLED": True,
    "HEALTH_CHECK_INTERVAL": 60,
    "ALERT_THRESHOLD_ERROR_RATE": 0.05,
    
    # Data Management
    "BACKUP_INTERVAL_HOURS": 24,
    "LOG_RETENTION_DAYS": 90,
    "CACHE_TTL_SECONDS": 3600,
    "DATABASE_POOL_SIZE": 10
}
```

### 2. 環境変数（本格運用）
```env
# Production Environment Configuration

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Security
SECRET_KEY=production_secret_key_256_bit
API_KEY_ROTATION_ENABLED=true
RATE_LIMITING_ENABLED=true

# Database (if using)
DATABASE_URL=postgresql://user:pass@host:5432/hatena_prod
DATABASE_POOL_MIN=5
DATABASE_POOL_MAX=20

# Cache (if using)
REDIS_URL=redis://cache-server:6379/0
CACHE_DEFAULT_TIMEOUT=3600

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true
ALERT_EMAIL=admin@company.com

# External Services
HATENA_BLOG_ATOMPUB_KEY_1=${VAULT_API_KEY_1}
HATENA_BLOG_ATOMPUB_KEY_2=${VAULT_API_KEY_2}
```

### 3. システムサービス設定
```ini
# /etc/systemd/system/hatena-blog-agent.service
[Unit]
Description=Hatena Multi-Blog Agent
After=network.target

[Service]
Type=simple
User=hatena-agent
Group=hatena-agent
WorkingDirectory=/opt/hatena-blog-agent
Environment=PYTHONPATH=/opt/hatena-blog-agent
ExecStart=/opt/hatena-blog-agent/venv/bin/python enhanced_hatena_agent.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=hatena-blog-agent

[Install]
WantedBy=multi-user.target
```

## 📈 監視・ログ設定

### 1. ログ設定
```python
# logging_config.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/hatena-blog-agent/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed'
        },
        'security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/hatena-blog-agent/security.log',
            'maxBytes': 10485760,
            'backupCount': 10,
            'formatter': 'detailed'
        }
    },
    'loggers': {
        'hatena_blog_agent': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False
        },
        'security': {
            'handlers': ['security'],
            'level': 'WARNING',
            'propagate': False
        }
    }
}
```

### 2. ヘルスチェック設定
```python
# health_check.py
def health_check():
    """Comprehensive health check for production monitoring"""
    checks = {
        "database": check_database_connection(),
        "cache": check_cache_connection(),
        "external_apis": check_hatena_api_connectivity(),
        "disk_space": check_disk_space(),
        "memory_usage": check_memory_usage(),
        "cpu_usage": check_cpu_usage()
    }
    
    overall_health = all(checks.values())
    
    return {
        "status": "healthy" if overall_health else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "version": "1.0.0"
    }
```

## 🔄 デプロイメント手順

### 自動デプロイメントスクリプト
```bash
#!/bin/bash
# deploy_production.sh

set -e

echo "🚀 Starting Hatena Blog Agent Production Deployment"

# 1. Environment setup
echo "📝 Setting up environment..."
sudo useradd -r -s /bin/false hatena-agent || true
sudo mkdir -p /opt/hatena-blog-agent/{logs,data,backup}
sudo chown -R hatena-agent:hatena-agent /opt/hatena-blog-agent

# 2. Application deployment
echo "📦 Deploying application..."
sudo cp -r . /opt/hatena-blog-agent/
cd /opt/hatena-blog-agent

# 3. Python environment
echo "🐍 Setting up Python environment..."
sudo -u hatena-agent python3 -m venv venv
sudo -u hatena-agent ./venv/bin/pip install -r requirements-windows.txt

# 4. Configuration
echo "⚙️ Configuring application..."
sudo -u hatena-agent cp .env.template .env
echo "⚠️ Please edit /opt/hatena-blog-agent/.env with production settings"

# 5. Service installation
echo "🔧 Installing system service..."
sudo cp deployment/hatena-blog-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hatena-blog-agent

# 6. Nginx configuration (optional)
echo "🌐 Configuring reverse proxy..."
sudo cp deployment/nginx.conf /etc/nginx/sites-available/hatena-blog-agent
sudo ln -sf /etc/nginx/sites-available/hatena-blog-agent /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 7. Security setup
echo "🔒 Applying security settings..."
sudo chmod 600 /opt/hatena-blog-agent/.env
sudo chmod 755 /opt/hatena-blog-agent/*.py
sudo chown -R hatena-agent:hatena-agent /opt/hatena-blog-agent

# 8. Startup
echo "🎉 Starting service..."
sudo systemctl start hatena-blog-agent
sudo systemctl status hatena-blog-agent

echo "✅ Production deployment complete!"
echo "📊 Monitor logs: sudo journalctl -u hatena-blog-agent -f"
echo "🔍 Health check: curl http://localhost:8083/health"
```

## 🚨 運用チェックリスト

### 展開前チェック
- [ ] セキュリティ設定確認
- [ ] バックアップ戦略決定
- [ ] 監視アラート設定
- [ ] ログローテーション設定
- [ ] SSL証明書準備
- [ ] ファイアウォール設定
- [ ] ユーザー権限設定

### 展開後チェック
- [ ] サービス起動確認
- [ ] ヘルスチェック確認
- [ ] ログ出力確認
- [ ] 認証テスト実行
- [ ] パフォーマンステスト
- [ ] セキュリティスキャン
- [ ] バックアップテスト

### 日常運用チェック
- [ ] ログ監視（毎日）
- [ ] パフォーマンス監視（毎日）
- [ ] セキュリティアップデート（週次）
- [ ] バックアップ確認（週次）
- [ ] APIキーローテーション（月次）
- [ ] システムアップデート（月次）

---
**運用開始準備**: テスト環境検証完了後、本戦略に基づいて段階的に本格運用環境を構築