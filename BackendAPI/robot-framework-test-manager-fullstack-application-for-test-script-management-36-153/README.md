# Robot Framework Test Manager - Fullstack Application

This repository contains the Backend API and deployment scaffolding for a full-stack application that manages Robot Framework test scripts, cases, execution queue, run history, and logs.

Primary services:
- BackendAPI (FastAPI + SQLAlchemy)
- FrontendUI (React + TypeScript) [lives in sibling workspace path: robot-framework-test-manager-fullstack-application-for-test-script-management-36-154/FrontendUI]
- PostgreSQL (database)
- Minio (S3-compatible object storage) — used for storing execution logs and artifacts

Note: ObjectStorage is provided via the Minio Docker service bundled in docker-compose. There is no separate UI container; Minio Console is available at http://localhost:9001.

## Quick Start (Docker Compose)

1. Copy env file
   cp .env.example .env

2. Start all services
   docker compose up -d --build

3. Service endpoints
- Backend API: http://localhost:${BACKEND_PORT:-8000}
  - Health: GET /
- Frontend UI: http://localhost:${FRONTEND_PORT:-3000}
- PostgreSQL: localhost:${POSTGRES_PORT:-5432}
- Minio API: http://localhost:${MINIO_PORT_API:-9000}
- Minio Console: http://localhost:${MINIO_PORT_CONSOLE:-9001}
  - Login with MINIO_ACCESS_KEY/MINIO_SECRET_KEY (from .env)

The compose file waits for DB and Minio with healthchecks before starting Backend.

## Environment Variables

See .env.example for all supported variables. Key settings:
- DATABASE_URL (SQLAlchemy URL for PostgreSQL)
- JWT_SECRET, JWT_EXPIRES_IN
- MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET
- CORS_ALLOW_ORIGINS (comma-separated list)
- REACT_APP_API_BASE (Frontend -> Backend endpoint)

You can also use the scoped .env.example files in:
- BackendAPI/.env.example
- FrontendUI/.env.example

## Local Development (Backend)

Inside BackendAPI:
- Install deps: pip install -r requirements.txt
- Run: uvicorn src.api.main:app --reload
- Tests: pytest
- Lint: flake8 src

## CI/CD

GitHub Actions included:
- Backend: Lint (flake8), Tests (pytest), Docker build
- Frontend: Install, optional Lint, Build, Docker build

Workflows live in:
- .github/workflows/backend-ci.yml (in this repo)
- robot-framework-test-manager-fullstack-application-for-test-script-management-36-154/FrontendUI/.github/workflows/frontend-ci.yml (in Frontend repo path)

## Security and Configuration

Do not hardcode secrets. Use environment variables and rotate JWT_SECRET for production. Configure CORS appropriately for your deployment domains.

## Notes

- On first run, the Backend will auto-create DB tables and ensure the Minio bucket exists.
- For production, consider building a static frontend and serving it behind a reverse proxy, and use managed PostgreSQL and object storage or hardened Minio deployment.
