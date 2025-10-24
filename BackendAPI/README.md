# Robot Framework Test Manager - Backend API

FastAPI backend for managing Robot Framework test scripts, test cases, execution, and logs.

## Features

- **JWT Authentication** with role-based access control (RBAC)
- **Test Script Management** - Create, read, update, delete test scripts
- **Test Case Management** - Manage test cases with variables and configuration
- **Execution Management** - Execute tests ad-hoc or via queue
- **Queue Management** - Priority-based execution queue
- **Run History** - Complete execution history with logs
- **MinIO Integration** - Object storage for large log files
- **PostgreSQL** - Relational database for metadata
- **OpenAPI Documentation** - Auto-generated API documentation

## Architecture

```
BackendAPI/
├── src/
│   ├── api/
│   │   ├── routers/        # API route handlers
│   │   └── main.py         # FastAPI application
│   ├── core/
│   │   ├── config.py       # Configuration management
│   │   └── security.py     # Security utilities
│   ├── database/
│   │   ├── models.py       # SQLAlchemy models
│   │   └── connection.py   # Database connection
│   ├── schemas/            # Pydantic schemas
│   └── services/           # Business logic services
├── alembic/                # Database migrations
├── Dockerfile              # Container definition
├── docker-compose.yml      # Multi-container setup
└── requirements.txt        # Python dependencies
```

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- MinIO (or S3-compatible storage)

## Setup

### 1. Clone and Navigate

```bash
cd BackendAPI
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Required variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret key for JWT (generate random string)
- `MINIO_ENDPOINT` - MinIO server endpoint
- `MINIO_ACCESS_KEY` - MinIO access key
- `MINIO_SECRET_KEY` - MinIO secret key

### 5. Initialize Database

```bash
# Run migrations
alembic upgrade head
```

### 6. Run Application

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker Deployment

### Using Docker Compose (Recommended for Development)

```bash
# Start all services (backend, PostgreSQL, MinIO)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Using Dockerfile Only

```bash
# Build image
docker build -t testmanager-backend .

# Run container (requires external database and MinIO)
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e JWT_SECRET_KEY=your-secret \
  -e MINIO_ENDPOINT=minio:9000 \
  -e MINIO_ACCESS_KEY=minioadmin \
  -e MINIO_SECRET_KEY=minioadmin \
  testmanager-backend
```

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Authentication

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the Authorization header:

```bash
curl -X GET http://localhost:8000/api/v1/tests \
  -H "Authorization: Bearer eyJ..."
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/logout` - Logout (invalidate token)

### Test Scripts
- `POST /api/v1/tests` - Create test script
- `GET /api/v1/tests` - List all test scripts (paginated)
- `GET /api/v1/tests/{test_id}` - Get test script details
- `PUT /api/v1/tests/{test_id}` - Update test script
- `DELETE /api/v1/tests/{test_id}` - Delete test script

### Test Cases
- `POST /api/v1/cases` - Create test case
- `GET /api/v1/cases` - List all test cases (with filters)
- `GET /api/v1/cases/{case_id}` - Get test case details
- `PUT /api/v1/cases/{case_id}` - Update test case
- `DELETE /api/v1/cases/{case_id}` - Delete test case

### Execution
- `POST /api/v1/execute` - Execute test cases

### Queue
- `GET /api/v1/queue` - Get execution queue
- `POST /api/v1/queue` - Add test cases to queue
- `DELETE /api/v1/queue/{case_id}` - Remove from queue

### Run History
- `GET /api/v1/history` - List run history (with filters)
- `GET /api/v1/history/{run_id}` - Get run details

### Logs
- `GET /api/v1/logs/{run_id}` - Get execution logs

## Database Migrations

### Create a New Migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback Migration

```bash
alembic downgrade -1
```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src tests/
```

## Code Quality

```bash
# Run pylint
pylint src/

# Run flake8
flake8 src/
```

## Default Roles

The system initializes with three default roles:

- **admin** - Full access to all operations
- **tester** - Can create and execute tests
- **viewer** - Read-only access

## Security Best Practices

1. **Always use HTTPS in production**
2. **Generate a strong JWT secret key** (use `openssl rand -hex 32`)
3. **Use environment variables** for sensitive data
4. **Enable MinIO security** (MINIO_SECURE=True) in production
5. **Restrict CORS origins** to known frontends
6. **Use strong database passwords**
7. **Regularly update dependencies**

## Troubleshooting

### Database Connection Issues

- Verify DATABASE_URL format: `postgresql://user:password@host:port/database`
- Ensure PostgreSQL is running and accessible
- Check firewall rules

### MinIO Connection Issues

- Verify MinIO endpoint (without http://)
- Check MinIO access credentials
- Ensure MinIO bucket permissions are correct

### Authentication Issues

- Verify JWT_SECRET_KEY is set
- Check token expiration (default 30 minutes)
- Ensure Authorization header format: `Bearer <token>`

## Support

For issues and questions, please refer to the project documentation or contact the development team.
