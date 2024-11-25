FROM python:3.9-slim

WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements for caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV DJANGO_SETTINGS_MODULE=chat_connect.settings.settings_production
ENV PYTHONUNBUFFERED=1

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose the application port
EXPOSE 8000

# Add a health check
HEALTHCHECK --interval=30s --timeout=5s \
    CMD curl --fail http://localhost:8000/health || exit 1

# Switch to a non-root user
RUN useradd -m chatea-conecta
USER chatea-conecta

# Start the application
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "chat_connect.asgi:application"]
