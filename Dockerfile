# ==============================================================================
# Tower Serving Stack - Production Dockerfile
# Base Image: Python 3.11 Slim for minimal attack surface and low image size
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code, trained model artifact, and datasets
COPY src/ ./src/
COPY artifacts/ ./artifacts/
COPY project2_tower_serving/ ./project2_tower_serving/

# Expose FastAPI HTTP serving port
EXPOSE 8000

# Healthcheck probe using built-in curl
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn ASGI server with production concurrency workers
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--app-dir", "src"]
