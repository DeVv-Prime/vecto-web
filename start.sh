#!/bin/bash

# Create database directory if not exists
mkdir -p /app/data

# Set default port
export PORT=${PORT:-10000}

# Run database migrations (if any)
python -c "from app import init_db; init_db()"

# Start the application
gunicorn --bind 0.0.0.0:$PORT app:app
