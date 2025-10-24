# Backend API Deployment Guide

## Quick Start

### Prerequisites Check
- Python 3.11+
- PostgreSQL 15+ (running and accessible)
- MinIO or S3-compatible storage (running and accessible)

### Step 1: Environment Setup

```bash
cd BackendAPI

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Copy and configure the environment file:

```bash
cp .env.example .env
```

**Edit `.env` and set these REQUIRED variables:**

```bash
# Database - REQUIRED
DATABASE_URL=postgresql://username:password@host:port/database

# JWT Secret - REQUIRED (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your_secret_key_here

# MinIO Storage - REQUIRED
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### Step 3: Initialize Database

```bash
# Option 1: Using the init script (recommended for first-time setup)
python scripts/init_db.py

# Option 2: Using Alembic migrations
alembic upgrade head
```

**The init script will create:**
- All database tables
- Default roles (admin, tester, viewer)
- Default admin user:
  - Username: `admin`
  - Password: `admin123`
  - **⚠️ Change this password immediately in production!**

### Step 4: Start the Application

```bash
# Development mode with auto-reload
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 5: Verify Installation

Visit these URLs in your browser:
- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc
- Health Check: http://localhost:8000/

## Docker Deployment

### Using Docker Compose (Recommended)

This starts the backend, PostgreSQL, and MinIO together:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

Access points:
- Backend API: http://localhost:8000
- MinIO Console: http://localhost:9001
- PostgreSQL: localhost:5432

### Using Docker Only

```bash
# Build image
docker build -t testmanager-backend .

# Run (requires external PostgreSQL and MinIO)
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e JWT_SECRET_KEY=your_secret \
  -e MINIO_ENDPOINT=minio:9000 \
  -e MINIO_ACCESS_KEY=minioadmin \
  -e MINIO_SECRET_KEY=minioadmin \
  testmanager-backend
```

## Testing the API

### Get Authentication Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Use the Token

```bash
# Get current user info
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# List test scripts
curl -X GET http://localhost:8000/api/v1/tests \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create a test script
curl -X POST http://localhost:8000/api/v1/tests \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Test",
    "description": "Test script description",
    "meta_data": {"tags": ["smoke", "regression"]}
  }'
```

## Database Management

### Creating Migrations

When you modify models:

```bash
# Generate migration
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration in alembic/versions/

# Apply migration
alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# View migration history
alembic history
```

## Production Considerations

### Security Checklist

- [ ] Change default admin password
- [ ] Use strong JWT secret key (32+ characters, random)
- [ ] Set `MINIO_SECURE=True` for HTTPS MinIO
- [ ] Restrict `CORS_ORIGINS` to known frontends
- [ ] Use HTTPS/TLS for all connections
- [ ] Enable database SSL/TLS
- [ ] Use environment-specific secrets management
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Configure log retention policies

### Environment Variables for Production

```bash
# Application
APP_NAME=Robot Framework Test Manager API
APP_VERSION=1.0.0
DEBUG=False

# Database with SSL
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Strong JWT secret (generate new one!)
JWT_SECRET_KEY=<generate_with_openssl_rand_hex_32>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# MinIO with HTTPS
MINIO_ENDPOINT=minio.yourdomain.com:9000
MINIO_ACCESS_KEY=<your_production_key>
MINIO_SECRET_KEY=<your_production_secret>
MINIO_BUCKET_NAME=production-test-logs
MINIO_SECURE=True

# CORS - Restrict to your frontend domain
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Pagination
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
```

### Running with Systemd (Production)

Create `/etc/systemd/system/testmanager-backend.service`:

```ini
[Unit]
Description=Robot Framework Test Manager Backend
After=network.target postgresql.service

[Service]
Type=simple
User=testmanager
WorkingDirectory=/opt/testmanager/BackendAPI
Environment="PATH=/opt/testmanager/BackendAPI/venv/bin"
EnvironmentFile=/opt/testmanager/BackendAPI/.env
ExecStart=/opt/testmanager/BackendAPI/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable testmanager-backend
sudo systemctl start testmanager-backend
sudo systemctl status testmanager-backend
```

## Monitoring and Logs

### View Application Logs

```bash
# Docker Compose
docker-compose logs -f backend

# Systemd
sudo journalctl -u testmanager-backend -f

# Direct (if running with uvicorn)
# Logs are written to stdout/stderr
```

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/

# API health check
curl http://localhost:8000/api/v1/health
```

## Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql postgresql://user:pass@host:5432/db

# Check if PostgreSQL is running
sudo systemctl status postgresql

# View PostgreSQL logs
sudo journalctl -u postgresql -f
```

### MinIO Connection Issues

```bash
# Test MinIO connectivity
curl http://localhost:9000/minio/health/live

# Check MinIO logs
docker-compose logs minio
```

### Application Won't Start

```bash
# Check Python syntax
python -m py_compile src/api/main.py

# Test imports
python -c "from src.api.main import app; print('OK')"

# Verify all environment variables
python -c "from src.core.config import settings; print(settings.model_dump())"
```

### Authentication Issues

- Ensure JWT_SECRET_KEY is set
- Check token hasn't expired (default 30 minutes)
- Verify Authorization header format: `Bearer <token>`
- Check user exists and is active in database

## Performance Tuning

### Uvicorn Workers

```bash
# Calculate workers: (2 x CPU_CORES) + 1
# For 4 cores: 9 workers
uvicorn src.api.main:app --workers 9 --host 0.0.0.0 --port 8000
```

### Database Connection Pool

Edit `src/database/connection.py`:

```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,        # Adjust based on load
    max_overflow=40      # Adjust based on load
)
```

### Enable Gunicorn (Production)

```bash
pip install gunicorn

# Run with Gunicorn
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

## Backup and Recovery

### Database Backup

```bash
# Backup
pg_dump -U username -h localhost -d testmanager > backup_$(date +%Y%m%d).sql

# Restore
psql -U username -h localhost -d testmanager < backup_20250124.sql
```

### MinIO Backup

```bash
# Using mc (MinIO Client)
mc alias set myminio http://localhost:9000 minioadmin minioadmin
mc mirror myminio/test-logs /backup/minio/test-logs
```

## Support and Resources

- API Documentation: http://localhost:8000/docs
- OpenAPI Spec: http://localhost:8000/openapi.json
- Project README: See README.md
- Issue Tracker: [Your issue tracker URL]
