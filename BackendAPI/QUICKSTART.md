# Quick Start Guide - Robot Framework Test Manager API

## Prerequisites
- Python 3.11+
- pip

## Installation

1. **Install Dependencies**
   ```bash
   cd BackendAPI
   pip install -r requirements.txt
   ```

## Running the Application

### Start the Server (Without Database)
The application will start even without PostgreSQL or MinIO running:

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:   Started server process
INFO:   Waiting for application startup.
INFO:   Starting Robot Framework Test Manager API...
WARNING: Database initialization failed (this is expected if database is not running)
INFO:   API will start without database - some endpoints may not work
INFO:   Application startup complete.
INFO:   Uvicorn running on http://0.0.0.0:8000
```

### Alternative: Using start.py
```bash
python start.py --host 0.0.0.0 --port 8000
```

## Accessing the API

### Swagger Documentation
Open your browser to: http://localhost:8000/docs

### Health Check
```bash
curl http://localhost:8000/health
```

### API Endpoints (No Authentication Required)

All endpoints are now public and do not require authentication:

#### Authentication (Returns Dummy Data)
```bash
# Get current user info (returns dummy user)
curl http://localhost:8000/api/v1/auth/me

# Login (returns dummy token)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"any","password":"any"}'
```

#### Test Scripts
```bash
# List test scripts
curl http://localhost:8000/api/v1/tests/

# Create test script
curl -X POST http://localhost:8000/api/v1/tests/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Test Script",
    "description": "Test description",
    "content": "*** Test Cases ***\nMy Test\n    Log    Hello World"
  }'
```

#### Test Cases
```bash
# List test cases
curl http://localhost:8000/api/v1/cases/

# Create test case (requires valid test_script_id)
curl -X POST http://localhost:8000/api/v1/cases/ \
  -H "Content-Type: application/json" \
  -d '{
    "test_script_id": "some-uuid",
    "name": "My Test Case",
    "description": "Test case description",
    "variables": {}
  }'
```

## Running with Database (Optional)

If you want full functionality, set up PostgreSQL:

1. **Create .env file**
   ```bash
   cp .env.example .env
   ```

2. **Update DATABASE_URL in .env**
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/test_manager
   ```

3. **Initialize Database**
   ```bash
   python init_db.py
   ```

4. **Start Server**
   ```bash
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   ```

## Running with MinIO (Optional)

For file storage functionality:

1. **Start MinIO**
   ```bash
   docker run -p 9000:9000 -p 9001:9001 \
     -e "MINIO_ROOT_USER=minioadmin" \
     -e "MINIO_ROOT_PASSWORD=minioadmin" \
     minio/minio server /data --console-address ":9001"
   ```

2. **Update .env with MinIO settings**
   ```
   MINIO_ENDPOINT=localhost:9000
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=minioadmin
   ```

## Important Notes

✅ **No Authentication Required**: All endpoints are public. Authentication has been completely removed from the codebase.

✅ **Database Optional**: The API will start without a database. Some endpoints will return errors if you try to use them without a database.

✅ **MinIO Optional**: File storage features won't work without MinIO, but the API will still start.

✅ **System User**: All operations use a default "system" user ID internally.

## Development

### With Auto-Reload
```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Tests (when available)
```bash
pytest
```

### Code Quality
```bash
# Linting
flake8 src/

# Formatting
black src/
```

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Database Connection Errors
These are now warnings, not errors. The API will start anyway.

## Next Steps

1. Set up PostgreSQL for full database functionality
2. Set up MinIO for file storage
3. Connect your frontend application to the API
4. Deploy to production environment

For complete details on authentication removal, see NO_AUTH_CHANGES.md.
