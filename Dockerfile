FROM python:3.9-slim-buster

WORKDIR /app

# Install system dependencies: ffmpeg, aria2c for video downloading
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    aria2 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install yt-dlp
RUN pip install --no-cache-dir yt-dlp

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run server setup
RUN python serverV3.py

# Start both Flask health check and the bot
CMD gunicorn app:app & python3 main.py
