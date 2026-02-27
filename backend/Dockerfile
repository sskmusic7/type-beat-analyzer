# Backend Dockerfile for Google Cloud Run
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Copy ml directory for training (hybrid_trainer, etc.)
COPY ml/ /app/ml

# Expose port (Cloud Run sets PORT env var)
ENV PORT=8080
EXPOSE 8080

# Run with uvicorn
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
