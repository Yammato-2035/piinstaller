# PI-Installer Backend - Dockerfile
FROM python:3.13-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY backend/ .

# Install core dependencies first (without pydantic issues)
RUN pip install --upgrade pip && \
    pip install starlette==0.27.0 && \
    pip install fastapi==0.104.1 && \
    pip install uvicorn[standard]==0.24.0 && \
    pip install python-dotenv python-multipart aiofiles requests click psutil

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "app.py"]
