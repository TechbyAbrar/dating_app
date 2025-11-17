#!/bin/bash

# =========================================
# Professional Dev Startup Script
# Project: Django Dating App
# Services: Redis + Django ASGI (Gunicorn+Uvicorn) + Celery Worker + Celery Beat
# Using Django's own logging system (NO extra Django log files)
# =========================================

# ------------------------
# CONFIGURATION
# ------------------------
PROJECT_ROOT=$(pwd)
VENV_PATH="$PROJECT_ROOT/env/bin/activate"
DJANGO_PORT=8000
REDIS_PORT=6379
LOG_ROOT="$PROJECT_ROOT/logs"

# Only logs for external services (Celery + Redis)
CELERY_WORKER_LOG="$LOG_ROOT/celery_worker.log"
CELERY_BEAT_LOG="$LOG_ROOT/celery_beat.log"
REDIS_LOG="$LOG_ROOT/redis.log"

# ------------------------
# Utility functions
# ------------------------
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

kill_port() {
    PORT=$1
    if lsof -i :$PORT > /dev/null; then
        PIDS=$(lsof -t -i :$PORT)
        log "Port $PORT in use. Killing process(es): $PIDS"
        kill -9 $PIDS
        sleep 1
    fi
}

check_binary() {
    command -v $1 >/dev/null 2>&1 || { log "ERROR: $1 not found. Aborting."; exit 1; }
}

# ------------------------
# Prepare log folder (Celery + Redis only)
# ------------------------
mkdir -p "$LOG_ROOT"
touch "$CELERY_WORKER_LOG" "$CELERY_BEAT_LOG" "$REDIS_LOG"

# ------------------------
# Activate virtual environment
# ------------------------
log "Activating virtual environment..."
if [ -f "$VENV_PATH" ]; then
    source "$VENV_PATH"
else
    log "ERROR: Virtual environment not found at $VENV_PATH"
    exit 1
fi

# ------------------------
# Check required binaries
# ------------------------
check_binary redis-server
check_binary gunicorn
check_binary celery

# ------------------------
# Start Redis
# ------------------------
if lsof -i :$REDIS_PORT > /dev/null; then
    log "Redis already running on port $REDIS_PORT"
else
    log "Starting Redis..."
    redis-server --port $REDIS_PORT --daemonize yes --logfile "$REDIS_LOG"
    sleep 2

    if lsof -i :$REDIS_PORT > /dev/null; then
        log "Redis started successfully."
    else
        log "ERROR: Redis failed to start."
        exit 1
    fi
fi

# ------------------------
# Stop existing Django server if any
# ------------------------
kill_port $DJANGO_PORT

# ------------------------
# Start Django ASGI (Gunicorn + Uvicorn)
# Let Django handle logs (NO extra log files here)
# ------------------------
log "Starting Django ASGI server on port $DJANGO_PORT..."
nohup gunicorn core.asgi:application \
    -k uvicorn.workers.UvicornWorker \
    --workers 2 \
    --bind 0.0.0.0:$DJANGO_PORT \
    --log-level info \
    >/dev/null 2>&1 &

DJANGO_PID=$!
log "Django PID: $DJANGO_PID"

# ------------------------
# Start Celery Worker
# ------------------------
log "Starting Celery worker..."
nohup celery -A core worker -l info \
    > "$CELERY_WORKER_LOG" 2>&1 &
CELERY_WORKER_PID=$!
log "Celery Worker PID: $CELERY_WORKER_PID"

# ------------------------
# Start Celery Beat
# ------------------------
log "Starting Celery Beat..."
nohup celery -A core beat -l info \
    > "$CELERY_BEAT_LOG" 2>&1 &
CELERY_BEAT_PID=$!
log "Celery Beat PID: $CELERY_BEAT_PID"

# ------------------------
# Final Status
# ------------------------
log "===================================="
log "[SUCCESS] All services started successfully!"
log "[INFO] Django ASGI: http://127.0.0.1:$DJANGO_PORT"
log ""
log "Logs:"
log "  Celery Worker: $CELERY_WORKER_LOG"
log "  Celery Beat:   $CELERY_BEAT_LOG"
log "  Redis:         $REDIS_LOG"
log ""
log "Django logs are handled internally via settings.py logging config."
log "===================================="
