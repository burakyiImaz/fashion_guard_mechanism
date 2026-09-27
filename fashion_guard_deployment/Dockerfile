# Use official Python runtime as base image
FROM python:3.10-slim

# Set working directory in container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies (with optimizations for GPU)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY runpod_handler.py .
COPY config.yaml .
COPY fashion_guard/ ./fashion_guard/

# Set environment variables for optimal performance
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HF_HUB_ENABLE_HF_TRANSFER=0
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV MODEL_NAME=Qwen/Qwen3-4B-Instruct-2507
ENV ACCELERATOR=auto
ENV QUANTIZATION=none

# Create cache directory
RUN mkdir -p /app/.cache/huggingface

# Expose port (optional - RunPod uses HTTP/WebSocket)
EXPOSE 8000

# Health check (optional but recommended)
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Start the handler with unbuffered output
CMD ["python", "-u", "runpod_handler.py"]
