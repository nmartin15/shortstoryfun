#!/bin/bash
# Production startup script for Short Story Pipeline
#
# This script:
# 1. Validates that .env file exists (creates from env.example if missing)
# 2. Loads environment variables selectively (principle of least privilege)
# 3. Validates required configuration (GOOGLE_API_KEY)
# 4. Sets production environment variables
# 5. Starts the application with Gunicorn
#
# Error Handling:
# - Exits with code 1 if .env file is missing or invalid
# - Warns if GOOGLE_API_KEY is not set (app will work but AI features disabled)
# - Uses 'set -e' to exit immediately on any command failure
#
# .env File Structure:
# - See env.example for required and optional variables
# - Required: GOOGLE_API_KEY (for AI generation)
# - Optional: LLM_MODEL, FLASK_ENV, PORT, HOST, Redis/DB config, Gunicorn settings
# - Sensitive variables (like SECRET_KEY) are NOT exported to subprocesses

set -e

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating from env.example..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "Please edit .env and set your configuration before running in production."
    else
        echo "Error: env.example not found. Cannot create .env file."
        exit 1
    fi
    exit 1
fi

# Load environment variables selectively (principle of least privilege)
# Only export variables that are actually needed by the application
# This prevents accidental exposure of sensitive data (like SECRET_KEY) to subprocesses
if [ -f .env ]; then
    # Source the .env file WITHOUT exporting (variables loaded but not exported)
    # This ensures sensitive variables like SECRET_KEY are not exposed to subprocesses
    source .env
    
    # Explicitly export only the required variables
    # Application variables
    if [ -n "$GOOGLE_API_KEY" ]; then
        export GOOGLE_API_KEY
    fi
    if [ -n "$LLM_MODEL" ]; then
        export LLM_MODEL
    fi
    if [ -n "$LLM_TEMPERATURE" ]; then
        export LLM_TEMPERATURE
    fi
    if [ -n "$FLASK_ENV" ]; then
        export FLASK_ENV
    fi
    if [ -n "$FLASK_DEBUG" ]; then
        export FLASK_DEBUG
    fi
    if [ -n "$PORT" ]; then
        export PORT
    fi
    if [ -n "$HOST" ]; then
        export HOST
    fi
    if [ -n "$REDIS_URL" ]; then
        export REDIS_URL
    fi
    if [ -n "$USE_DB_STORAGE" ]; then
        export USE_DB_STORAGE
    fi
    if [ -n "$USE_REDIS_CACHE" ]; then
        export USE_REDIS_CACHE
    fi
    # Gunicorn-specific variables
    if [ -n "$GUNICORN_WORKERS" ]; then
        export GUNICORN_WORKERS
    fi
    if [ -n "$GUNICORN_TIMEOUT" ]; then
        export GUNICORN_TIMEOUT
    fi
    if [ -n "$GUNICORN_BIND" ]; then
        export GUNICORN_BIND
    fi
    if [ -n "$GUNICORN_LOG_LEVEL" ]; then
        export GUNICORN_LOG_LEVEL
    fi
    if [ -n "$GUNICORN_ACCESS_LOG" ]; then
        export GUNICORN_ACCESS_LOG
    fi
    if [ -n "$GUNICORN_ERROR_LOG" ]; then
        export GUNICORN_ERROR_LOG
    fi
    if [ -n "$GUNICORN_PIDFILE" ]; then
        export GUNICORN_PIDFILE
    fi
    if [ -n "$GUNICORN_USER" ]; then
        export GUNICORN_USER
    fi
    if [ -n "$GUNICORN_GROUP" ]; then
        export GUNICORN_GROUP
    fi
    if [ -n "$GUNICORN_KEYFILE" ]; then
        export GUNICORN_KEYFILE
    fi
    if [ -n "$GUNICORN_CERTFILE" ]; then
        export GUNICORN_CERTFILE
    fi
else
    echo "Error: .env file not found"
    exit 1
fi

# Check for required variables
if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_google_api_key_here" ]; then
    echo "Warning: GOOGLE_API_KEY not set. AI generation will not work."
fi

# Set production environment
export FLASK_ENV=production
export FLASK_DEBUG=False

# Create logs directory if it doesn't exist
mkdir -p logs

# Start Gunicorn
echo "Starting Short Story Pipeline in production mode..."
gunicorn -c gunicorn_config.py app:app

