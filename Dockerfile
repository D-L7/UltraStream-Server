FROM python:3.11-slim

# Install ffmpeg, aria2, nodejs (JS runtime for yt-dlp), and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    aria2 \
    nodejs \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port 8080 for web server
ENV PORT=8080
EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "wsgi:application"]

