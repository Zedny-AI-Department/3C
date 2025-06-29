# Use official Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Upgrade pip and install dependencies with retries and increased timeout
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 --retries=10 -r requirements.txt

# Copy application files
COPY . .

# Copy .env file
COPY .env /app/.env

# Expose FastAPI port
EXPOSE 7001

# Run the app using uvicorn with correct host and port
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7001"]
