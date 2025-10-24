# Backend API Quick Reference

## 🚀 Quick Start Commands

```bash
# Setup
cd BackendAPI
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database and MinIO settings

# Initialize database
python scripts/init_db.py

# Run development server
uvicorn src.api.main:app --reload

# Run with Docker
docker-compose up -d
```

## 🔑 Default Credentials

**Admin User (after init_db.py):**
- Username: `admin`
- Password: `admin123`
- ⚠️ Change immediately in production!

## 📍 API Endpoints at a Glance

### Authentication
```
POST   /api/v1/auth/login      # Get JWT token
GET    /api/v1/auth/me         # Get user info
POST   /api/v1/auth/logout     # Logout
```

### Test Scripts
```
POST   /api/v1/tests           # Create
GET    /api/v1/tests           # List (paginated)
GET    /api/v1/tests/{id}      # Get one
PUT    /api/v1/tests/{id}      # Update
DELETE /api/v1/tests/{id}      # Delete
```

### Test Cases
```
POST   /api/v1/cases           # Create
GET    /api/v1/cases           # List (paginated, filterable)
GET    /api/v1/cases/{id}      # Get one
PUT    /api/v1/cases/{id}      # Update
DELETE /api/v1/cases/{id}      # Delete
```

### Execution
```
POST   /api/v1/execute         # Execute test cases
GET    /api/v1/queue           # List queue
POST   /api/v1/queue           # Add to queue
DELETE /api/v1/queue/{id}      # Remove from queue
GET    /api/v1/history         # List run history
GET    /api/v1/history/{id}    # Get run details
GET    /api/v1/logs/{id}       # Get log URL
```

### Health & Docs
```
GET    /                       # Health check
GET    /api/v1/health          # API health
GET    /docs                   # Swagger UI
GET    /redoc                  # ReDoc UI
GET    /openapi.json           # OpenAPI spec
```

## 🔐 Authentication Example

```bash
# 1. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Response: {"access_token":"eyJ...","token_type":"bearer"}

# 2. Use token
export TOKEN="eyJ..."

curl -X GET http://localhost:8000/api/v1/tests \
  -H "Authorization: Bearer $TOKEN"
```

## 📊 Database Quick Commands

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View history
alembic history
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Restart backend
docker-compose restart backend

# Stop all
docker-compose down

# Clean everything
docker-compose down -v
```

## 🔍 Troubleshooting

### Check application can start
```bash
python -c "from src.api.main import app; print('OK')"
```

### Verify environment variables
```bash
python -c "from src.core.config import settings; print(settings.model_dump())"
```

### Test database connection
```bash
psql $DATABASE_URL
```

### Check routes
```bash
python -c "
from src.api.main import app
for route in app.routes:
    if hasattr(route, 'path'):
        print(route.path)
"
```

## 📁 Project Structure

```
BackendAPI/
├── src/
│   ├── api/
│   │   ├── routers/      # API endpoints
│   │   └── main.py       # FastAPI app
│   ├── core/             # Config & security
│   ├── database/         # Models & connection
│   ├── schemas/          # Pydantic schemas
│   └── services/         # Business logic
├── alembic/              # DB migrations
├── scripts/              # Utility scripts
├── tests/                # Test files
├── .env                  # Environment vars (create from .env.example)
├── requirements.txt      # Dependencies
└── docker-compose.yml    # Docker setup
```

## 🌐 Access Points

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001
- **PostgreSQL**: localhost:5432

## 🔧 Common Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/db
JWT_SECRET_KEY=your_32_char_secret_key
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
CORS_ORIGINS=http://localhost:3000
```

## 💡 Tips

- Always activate virtual environment: `source venv/bin/activate`
- Check logs with: `docker-compose logs -f`
- Regenerate OpenAPI spec: `python src/api/generate_openapi.py`
- Run tests: `pytest`
- Check code quality: `flake8 src/`

## 📚 Documentation Files

- `README.md` - Full user guide
- `DEPLOYMENT.md` - Deployment guide
- `IMPLEMENTATION_SUMMARY.md` - Technical details
- `QUICK_REFERENCE.md` - This file
