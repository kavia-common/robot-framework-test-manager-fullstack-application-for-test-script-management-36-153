# Robot Framework Test Manager - Fullstack Application

A comprehensive fullstack application for managing Robot Framework test scripts, test cases, execution, queuing, run history, and logs.

## Architecture Overview

This application consists of multiple services orchestrated via Docker Compose:

- **FrontendUI**: React-based web interface (Port 3000)
- **BackendAPI**: FastAPI REST API (Port 3001)
- **PostgreSQL**: Database for metadata storage (Port 5432)
- **MinIO**: Object storage for execution logs (Ports 9000, 9001)

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- Git (for cloning the repository)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd code-generation
```

### 2. Environment Configuration

The application comes with default configuration in `.env` file. For production deployments, review and update the following variables:

```bash
# Review and edit .env file
nano .env
```

Key variables to configure:
- `JWT_SECRET_KEY`: Change this for production (use a strong random string)
- `POSTGRES_PASSWORD`: Change default password for production
- `MINIO_SECRET_KEY`: Change default secret for production
- `CORS_ORIGINS`: Update to match your frontend domain in production

### 3. Start All Services

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up --build -d
```

This will:
1. Start PostgreSQL database
2. Start MinIO object storage
3. Create the required MinIO bucket for logs
4. Start the Backend API
5. Start the Frontend UI

### 4. Access the Application

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:3001
- **API Documentation**: http://localhost:3001/docs (Swagger UI)
- **MinIO Console**: http://localhost:9001

### 5. Default Credentials

The system will create default users on first startup. Check the backend logs for credentials or consult the backend documentation.

## Service-Specific Commands

### Backend API Only

```bash
cd robot-framework-test-manager-fullstack-application-for-test-script-management-36-153/BackendAPI

# Run locally (requires Python 3.9+)
pip install -r requirements.txt
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### Frontend UI Only

```bash
cd robot-framework-test-manager-fullstack-application-for-test-script-management-36-154/FrontendUI

# Install dependencies
npm install

# Run locally
npm start

# Run tests
npm test

# Build for production
npm run build
```

## Docker Compose Commands

```bash
# Start services
docker-compose up

# Start services in background
docker-compose up -d

# Stop services
docker-compose down

# Stop services and remove volumes (WARNING: deletes all data)
docker-compose down -v

# View logs
docker-compose logs

# View logs for specific service
docker-compose logs backend
docker-compose logs frontend

# Restart a specific service
docker-compose restart backend

# Rebuild and restart services
docker-compose up --build
```

## Health Checks

All services include health checks to ensure proper startup order:

- **PostgreSQL**: Ready check on port 5432
- **MinIO**: HTTP health check on port 9000
- **Backend API**: HTTP health check on root endpoint

Check service health:
```bash
docker-compose ps
```

## Networking

All services communicate via the `testmanager-network` Docker bridge network:

- Frontend → Backend: Via `http://localhost:3001` (host) or `http://backend:8000` (internal)
- Backend → PostgreSQL: Via `postgres:5432`
- Backend → MinIO: Via `minio:9000`

## Volumes and Data Persistence

Data is persisted in Docker volumes:

- `postgres_data`: PostgreSQL database files
- `minio_data`: MinIO object storage files

To backup data:
```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U testuser testdb > backup.sql

# Restore PostgreSQL
cat backup.sql | docker-compose exec -T postgres psql -U testuser testdb
```

## Environment Variables Reference

### Database Variables
- `POSTGRES_USER`: Database username (default: testuser)
- `POSTGRES_PASSWORD`: Database password (default: testpass)
- `POSTGRES_DB`: Database name (default: testdb)

### MinIO Variables
- `MINIO_ACCESS_KEY`: MinIO access key (default: minioadmin)
- `MINIO_SECRET_KEY`: MinIO secret key (default: minioadmin)
- `MINIO_BUCKET_NAME`: Bucket name for logs (default: test-logs)

### Backend Variables
- `JWT_SECRET_KEY`: Secret key for JWT token signing
- `CORS_ORIGINS`: Allowed CORS origins (default: http://localhost:3000)

### Frontend Variables
- `REACT_APP_API_URL`: Backend API URL (default: http://localhost:3001/api/v1)
- `REACT_APP_SITE_URL`: Frontend site URL (default: http://localhost:3000)

## Troubleshooting

### Service fails to start

1. Check logs:
   ```bash
   docker-compose logs <service-name>
   ```

2. Verify all ports are available:
   - 3000 (Frontend)
   - 3001 (Backend - mapped from 8000 internal)
   - 5432 (PostgreSQL)
   - 9000, 9001 (MinIO)

3. Ensure Docker daemon is running and has sufficient resources

### Database connection errors

1. Wait for PostgreSQL health check to pass:
   ```bash
   docker-compose ps
   ```

2. Check database logs:
   ```bash
   docker-compose logs postgres
   ```

### CORS errors in browser

1. Verify `CORS_ORIGINS` in `.env` includes your frontend URL
2. Restart backend service:
   ```bash
   docker-compose restart backend
   ```

### MinIO bucket not found

The `minio-init` service should create the bucket automatically. If issues persist:

1. Access MinIO console: http://localhost:9001
2. Login with `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`
3. Manually create bucket named `test-logs` (or value of `MINIO_BUCKET_NAME`)

## Development vs Production

### Development Mode
- Uses `.env` file with default credentials
- CORS allows `http://localhost:3000`
- Debug logging enabled
- Hot reload enabled for both frontend and backend

### Production Deployment

1. Update `.env` with production values:
   - Strong passwords and secrets
   - Production domain for CORS
   - Production database connection

2. Use production-grade setup:
   - Deploy behind reverse proxy (nginx, traefik)
   - Enable HTTPS/TLS
   - Use managed database services
   - Configure proper backup strategies
   - Enable monitoring and alerting

3. Build optimized frontend:
   ```bash
   cd robot-framework-test-manager-fullstack-application-for-test-script-management-36-154/FrontendUI
   npm run build
   # Serve the build folder with a web server
   ```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:3001/docs
- **ReDoc**: http://localhost:3001/redoc
- **OpenAPI JSON**: http://localhost:3001/openapi.json

## Testing

### Backend Tests
```bash
cd robot-framework-test-manager-fullstack-application-for-test-script-management-36-153/BackendAPI
pytest --cov=src --cov-report=html --cov-report=term
```

### Frontend Tests
```bash
cd robot-framework-test-manager-fullstack-application-for-test-script-management-36-154/FrontendUI
npm test -- --coverage
```

## Code Quality

### Backend
- **Linting**: pylint (configured in CI/CD)
- **Type Checking**: Built-in Python type hints
- **Coverage Target**: 70%+

### Frontend
- **Linting**: ESLint (configured in package.json)
- **Testing**: Jest + React Testing Library
- **Coverage Target**: 70%+

## Contributing

1. Follow the existing code style and conventions
2. Write tests for new features
3. Ensure all tests pass before submitting changes
4. Update documentation as needed

## License

[Specify your license here]

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review service logs
3. Consult API documentation
4. Open an issue in the repository

## Version

- **Application Version**: 1.0.0
- **Backend API**: v1
- **Frontend UI**: v1.0.0
