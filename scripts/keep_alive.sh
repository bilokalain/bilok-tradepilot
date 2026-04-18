#!/bin/bash
# Bilok-TradePilot — Keep Alive
# Vérifie et relance les services automatiquement toutes les 30 secondes

PROJECT="/Users/alainbilok/Projects/projet-trading"
cd "$PROJECT"
export PYTHONPATH="$PROJECT:$PYTHONPATH"

while true; do
    # Backend
    if ! curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
        echo "[$(date '+%H:%M:%S')] Backend DOWN — relance..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null
        sleep 1
        source .venv/bin/activate && uvicorn backend.main:app --host 0.0.0.0 --port 8000 >> logs/backend.log 2>&1 &
        sleep 3
    fi

    # Frontend
    if ! curl -s --max-time 2 http://localhost:5173 > /dev/null 2>&1; then
        echo "[$(date '+%H:%M:%S')] Frontend DOWN — relance..."
        lsof -ti:5173 | xargs kill -9 2>/dev/null
        sleep 1
        cd "$PROJECT/frontend" && npm run dev -- --host >> "$PROJECT/logs/frontend.log" 2>&1 &
        cd "$PROJECT"
        sleep 3
    fi

    # Celery Worker
    if ! pgrep -f "celery.*worker" > /dev/null 2>&1; then
        echo "[$(date '+%H:%M:%S')] Celery Worker DOWN — relance..."
        source .venv/bin/activate && cd "$PROJECT" && celery -A backend.tasks.celery_app worker --loglevel=info --concurrency=2 >> logs/worker.log 2>&1 &
        sleep 3
    fi

    # Celery Beat
    if ! pgrep -f "celery.*beat" > /dev/null 2>&1; then
        echo "[$(date '+%H:%M:%S')] Celery Beat DOWN — relance..."
        source .venv/bin/activate && cd "$PROJECT" && celery -A backend.tasks.celery_app beat --loglevel=info >> logs/beat.log 2>&1 &
        sleep 3
    fi

    # Tunnel (localhost.run via SSH)
    if ! pgrep -f "localhost.run" > /dev/null 2>&1; then
        echo "[$(date '+%H:%M:%S')] Tunnel DOWN — relance..."
        ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -R 80:localhost:8000 nokey@localhost.run >> logs/tunnel_api.log 2>&1 &
        sleep 5
        NEW_URL=$(grep -o "https://[a-z0-9]*\.lhr\.life" logs/tunnel_api.log | tail -1)
        echo "[$(date '+%H:%M:%S')] Nouveau tunnel: $NEW_URL"
    fi

    sleep 30
done
