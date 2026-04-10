## File 5: `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Docker in Docker
RUN apt-get update && apt-get install -y \
    docker.io \
    docker-compose \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create volume for persistent database
VOLUME ["/app/data"]

# Expose port
EXPOSE 10000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DOCKER_HOST=unix:///var/run/docker.sock

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
