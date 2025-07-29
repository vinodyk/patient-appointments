# Simple single-stage build for Patient Appointment System
# Author: Vinod Yadav
# Date: 7-25-2025

FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python source files
COPY main_simple.py .
COPY agents/ ./agents/
COPY models/ ./models/

# Copy frontend build files specifically
COPY frontend/dist/ ./frontend/dist/

# Create a simple test to verify files are copied
RUN echo "Checking frontend files..." && \
    ls -la frontend/dist/ && \
    echo "Contents of index.html:" && \
    head -5 frontend/dist/index.html || echo "index.html not found"

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start command
CMD ["python", "main_simple.py"]