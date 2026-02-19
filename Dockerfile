# Use Python 3.12 slim image
FROM python:3.12-slim

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for OCR (Tesseract, OpenCV, Poppler)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-san \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project context
COPY . .

# Create the jobs directory (permissions fix for volume)
RUN mkdir -p jobs

# Expose application port
EXPOSE 8000

# ⚠️ CORRECTED: This must match 'main.py' in the root, not 'app/main.py'
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}