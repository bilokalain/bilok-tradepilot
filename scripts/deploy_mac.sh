#!/bin/bash
# ============================================================
# Bilok-TradePilot — Déploiement local MacBook
#
# Ce script installe les services Bilok-TradePilot pour qu'ils tournent
# automatiquement au démarrage du Mac.
#
# Usage : bash scripts/deploy_mac.sh
# ============================================================

set -e

PROJECT_DIR="/Users/alainbilok/Projects/projet-trading"
VENV="$PROJECT_DIR/.venv"
LAUNCH_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$PROJECT_DIR/logs"

echo ""
echo "======================================================"
echo "  Bilok-TradePilot — Déploiement local Mac"
echo "======================================================"

# Créer le dossier de logs
mkdir -p "$LOG_DIR"
echo "  [OK] Dossier logs créé : $LOG_DIR"

# ============================================================
# 1. Script de démarrage principal
# ============================================================
cat > "$PROJECT_DIR/scripts/start_all.sh" << 'STARTUP'
#!/bin/bash
# Bilok-TradePilot — Script de démarrage complet

PROJECT_DIR="/Users/alainbilok/Projects/projet-trading"
VENV="$PROJECT_DIR/.venv"
LOG_DIR="$PROJECT_DIR/logs"

cd "$PROJECT_DIR"

# Empêcher la mise en veille
caffeinate -s &
echo $! > "$LOG_DIR/caffeinate.pid"

# Docker (PostgreSQL + Redis + InfluxDB)
docker compose up -d 2>> "$LOG_DIR/docker.log"
sleep 5

# Backend FastAPI
source "$VENV/bin/activate"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 \
  >> "$LOG_DIR/backend.log" 2>&1 &
echo $! > "$LOG_DIR/backend.pid"

# Celery Worker
celery -A backend.tasks.celery_app worker --loglevel=info --concurrency=4 \
  >> "$LOG_DIR/worker.log" 2>&1 &
echo $! > "$LOG_DIR/worker.pid"

# Celery Beat
celery -A backend.tasks.celery_app beat --loglevel=info \
  >> "$LOG_DIR/beat.log" 2>&1 &
echo $! > "$LOG_DIR/beat.pid"

# Frontend (Vite)
cd "$PROJECT_DIR/frontend"
npm run dev >> "$LOG_DIR/frontend.log" 2>&1 &
echo $! > "$LOG_DIR/frontend.pid"

echo "[$(date)] Bilok-TradePilot démarré" >> "$LOG_DIR/startup.log"
STARTUP
chmod +x "$PROJECT_DIR/scripts/start_all.sh"
echo "  [OK] Script de démarrage créé"

# ============================================================
# 2. Script d'arrêt
# ============================================================
cat > "$PROJECT_DIR/scripts/stop_all.sh" << 'STOP'
#!/bin/bash
# Bilok-TradePilot — Arrêt propre

PROJECT_DIR="/Users/alainbilok/Projects/projet-trading"
LOG_DIR="$PROJECT_DIR/logs"

echo "Arrêt de Bilok-TradePilot..."

for pidfile in backend.pid worker.pid beat.pid frontend.pid caffeinate.pid; do
  if [ -f "$LOG_DIR/$pidfile" ]; then
    pid=$(cat "$LOG_DIR/$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid"
      echo "  [OK] Arrêté : $pidfile (PID $pid)"
    fi
    rm "$LOG_DIR/$pidfile"
  fi
done

docker compose -f "$PROJECT_DIR/docker-compose.yml" down 2>/dev/null
echo "  [OK] Docker arrêté"
echo "[$(date)] Bilok-TradePilot arrêté" >> "$LOG_DIR/startup.log"
STOP
chmod +x "$PROJECT_DIR/scripts/stop_all.sh"
echo "  [OK] Script d'arrêt créé"

# ============================================================
# 3. Script de statut
# ============================================================
cat > "$PROJECT_DIR/scripts/status.sh" << 'STATUS'
#!/bin/bash
# Bilok-TradePilot — Statut des services

PROJECT_DIR="/Users/alainbilok/Projects/projet-trading"
LOG_DIR="$PROJECT_DIR/logs"

echo ""
echo "======================================================"
echo "  Bilok-TradePilot — Statut des services"
echo "======================================================"

check_service() {
  local name=$1
  local pidfile="$LOG_DIR/$2"
  if [ -f "$pidfile" ]; then
    local pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      echo "  ✓ $name (PID $pid)"
      return 0
    fi
  fi
  echo "  ✗ $name (arrêté)"
  return 1
}

check_service "Backend FastAPI  " "backend.pid"
check_service "Celery Worker    " "worker.pid"
check_service "Celery Beat      " "beat.pid"
check_service "Frontend Vite    " "frontend.pid"
check_service "Caffeinate       " "caffeinate.pid"

echo ""
echo "  Docker :"
docker compose -f "$PROJECT_DIR/docker-compose.yml" ps --format "  {{.Name}}: {{.Status}}" 2>/dev/null || echo "  Docker non disponible"

echo ""
echo "  URLs :"
echo "  Frontend  : http://localhost:5173"
echo "  Backend   : http://localhost:8000"
echo "  API Docs  : http://localhost:8000/docs"
echo ""

# Vérifier la santé
health=$(curl -s http://localhost:8000/health 2>/dev/null)
if echo "$health" | grep -q '"ok"'; then
  echo "  Santé API : OK"
else
  echo "  Santé API : ERREUR"
fi
echo "======================================================"
STATUS
chmod +x "$PROJECT_DIR/scripts/status.sh"
echo "  [OK] Script de statut créé"

# ============================================================
# 4. LaunchAgent (démarrage auto au login)
# ============================================================
mkdir -p "$LAUNCH_DIR"
cat > "$LAUNCH_DIR/com.tradepilot.startup.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tradepilot.startup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${PROJECT_DIR}/scripts/start_all.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/launchd_error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
PLIST
echo "  [OK] LaunchAgent créé : com.tradepilot.startup"

echo ""
echo "======================================================"
echo "  Commandes disponibles :"
echo ""
echo "  Démarrer  : bash scripts/start_all.sh"
echo "  Arrêter   : bash scripts/stop_all.sh"
echo "  Statut    : bash scripts/status.sh"
echo ""
echo "  Auto-start au login : activé"
echo "  Pour désactiver :"
echo "    launchctl unload ~/Library/LaunchAgents/com.tradepilot.startup.plist"
echo "======================================================"
echo ""
