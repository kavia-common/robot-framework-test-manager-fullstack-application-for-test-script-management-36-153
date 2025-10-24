# syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS base

# Install system deps for psycopg2 and runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl wget && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application
COPY src /app/src

# Expose port and set env
ENV PYTHONUNBUFFERED=1 \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000

# Healthcheck endpoint is "/" already available in the app
EXPOSE 8000

# Run FastAPI with Uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
