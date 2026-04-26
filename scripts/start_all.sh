#!/bin/bash
# Relance tous les services TradePilot après un sleep / redémarrage Mac.
#
# Usage : ./scripts/start_all.sh
# Ou : bash scripts/start_all.sh

cd "$(dirname "$0")/.."

echo "═══════════════════════════════════════════"
echo "  🚀 BILOK-TRADEPILOT — Démarrage services"
echo "═══════════════════════════════════════════"
echo ""

# ─── 1. Docker Desktop ───
echo "📦 [1/7] Docker Desktop..."
if ! docker info > /dev/null 2>&1; then
    open -a "Docker"
    echo "   Lancement Docker Desktop, attente du daemon..."
    for i in {1..30}; do
        if docker info > /dev/null 2>&1; then
            echo "   ✅ Docker prêt (${i}s)"
            break
        fi
        sleep 1
    done
else
    echo "   ✅ Docker déjà actif"
fi

# ─── 2. Containers Postgres + Redis ───
echo ""
echo "🐘 [2/7] Postgres + Redis (Docker)..."
docker start projet-trading-postgres-1 projet-trading-redis-1 > /dev/null 2>&1
sleep 3
if docker ps --format '{{.Names}}' | grep -q postgres; then
    echo "   ✅ Postgres + Redis up"
else
    echo "   ❌ Échec démarrage containers"
    exit 1
fi

# ─── 3. Test Redis ───
echo ""
echo "🔌 [3/7] Test Redis..."
if redis-cli ping 2>/dev/null | grep -q PONG; then
    echo "   ✅ Redis répond"
    # Libérer les locks au cas où
    redis-cli DEL tradepilot:pipeline_lock tradepilot:intraday_lock tradepilot:tp_sl_lock > /dev/null 2>&1
else
    echo "   ❌ Redis ne répond pas"
    exit 1
fi

# ─── 4. FastAPI ───
echo ""
echo "🌐 [4/7] FastAPI backend..."
pkill -f "uvicorn.*backend" 2>/dev/null
sleep 1
nohup .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
disown
sleep 3
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q 200; then
    echo "   ✅ FastAPI sur :8000"
else
    echo "   ❌ FastAPI ne répond pas"
fi

# ─── 5. Celery Worker + Beat ───
echo ""
echo "⚙️  [5/7] Celery Worker + Beat..."
pkill -f "celery.*worker" 2>/dev/null
pkill -f "celery.*beat" 2>/dev/null
sleep 1
nohup .venv/bin/celery -A backend.tasks.celery_app worker --loglevel=info --concurrency=4 > logs/worker.log 2>&1 &
disown
nohup .venv/bin/celery -A backend.tasks.celery_app beat --loglevel=info > logs/beat.log 2>&1 &
disown
sleep 3
pgrep -f "celery.*worker" > /dev/null && echo "   ✅ Celery Worker" || echo "   ❌ Celery Worker"
pgrep -f "celery.*beat" > /dev/null && echo "   ✅ Celery Beat" || echo "   ❌ Celery Beat"

# ─── 6. Tunnel Cloudflare ───
echo ""
echo "☁️  [6/7] Tunnel Cloudflare..."
pkill -f cloudflared 2>/dev/null
sleep 1
nohup cloudflared tunnel run > logs/tunnel_cloudflare.log 2>&1 &
disown
sleep 3
if pgrep -f cloudflared > /dev/null; then
    if curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://api.bilok-tradepilot.be/health | grep -q 200; then
        echo "   ✅ Tunnel + API publique OK"
    else
        echo "   ⚠️  Tunnel actif, mais API publique pas encore prête (attendre 10s)"
    fi
else
    echo "   ❌ Tunnel pas démarré"
fi

# ─── 7. caffeinate ───
echo ""
echo "☕ [7/7] caffeinate..."
pgrep -f caffeinate > /dev/null || nohup caffeinate -s > /dev/null 2>&1 &
disown 2>/dev/null
sleep 1
pgrep -f caffeinate > /dev/null && echo "   ✅ caffeinate actif" || echo "   ⚠️  caffeinate down"

# ─── Récap ───
echo ""
echo "═══════════════════════════════════════════"
echo "  📊 RÉCAPITULATIF"
echo "═══════════════════════════════════════════"
docker ps --format '   ✅ {{.Names}}' 2>/dev/null | grep -E "postgres|redis"
pgrep -f "uvicorn.*backend" > /dev/null && echo "   ✅ FastAPI"
pgrep -f "celery.*worker" > /dev/null && echo "   ✅ Celery Worker"
pgrep -f "celery.*beat" > /dev/null && echo "   ✅ Celery Beat"
pgrep -f cloudflared > /dev/null && echo "   ✅ Tunnel Cloudflare"
pgrep -f caffeinate > /dev/null && echo "   ✅ caffeinate"
echo ""
echo "🌐 Plateforme : https://app.bilok-tradepilot.be"
echo "🔌 API        : https://api.bilok-tradepilot.be/health"
echo ""
echo "Tout est prêt 🎉"
