# PI-Installer Backend - Dockerfile
# Image pinned for supply-chain security. Update digest after pull: docker pull python:3.13-slim && docker inspect --format='{{index .RepoDigests 0}}' python:3.13-slim
FROM python:3.13-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY backend/ .

# Abhängigkeiten wie lokal/CI (backend/requirements.txt)
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "app.py"]
