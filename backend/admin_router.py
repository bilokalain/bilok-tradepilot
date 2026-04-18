"""Admin API — Statut services, cache, positions, utilisateurs, logs."""

import os
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.database.models import Asset, Position, PositionStatus, Order

router = APIRouter()

DATA_DIR = Path("data")
LOG_DIR = Path("logs")


@router.get("/status")
def system_status():
    """Statut de tous les services."""
    services = {}

    # Backend
    services["backend"] = {"status": "ok", "pid": os.getpid()}

    # PostgreSQL
    try:
        result = subprocess.run(["pg_isready"], capture_output=True, timeout=3)
        services["postgresql"] = {"status": "ok" if result.returncode == 0 else "down"}
    except Exception:
        services["postgresql"] = {"status": "unknown"}

    # Redis
    try:
        result = subprocess.run(["redis-cli", "ping"], capture_output=True, timeout=3)
        services["redis"] = {"status": "ok" if b"PONG" in result.stdout else "down"}
    except Exception:
        services["redis"] = {"status": "unknown"}

    # Celery workers
    try:
        result = subprocess.run(
            ["celery", "-A", "backend.tasks.celery_app", "inspect", "ping", "--timeout=2"],
            capture_output=True, timeout=5,
        )
        services["celery"] = {"status": "ok" if result.returncode == 0 else "down"}
    except Exception:
        services["celery"] = {"status": "unknown"}

    # Alpaca
    try:
        from backend.modules.execution.broker_alpaca import alpaca_broker
        if alpaca_broker.is_configured:
            acct = alpaca_broker.get_account()
            services["alpaca"] = {
                "status": "ok",
                "equity": float(acct.get("equity", 0)),
                "cash": float(acct.get("cash", 0)),
                "positions": len(alpaca_broker.get_positions()),
            }
        else:
            services["alpaca"] = {"status": "not_configured"}
    except Exception as e:
        services["alpaca"] = {"status": "error", "error": str(e)[:100]}

    # Cloudflare Tunnel
    try:
        result = subprocess.run(["pgrep", "-f", "cloudflared"], capture_output=True, timeout=2)
        tunnel_url = ""
        for log in ["tunnel_api.log", "tunnel.log"]:
            log_path = LOG_DIR / log
            if log_path.exists():
                content = log_path.read_text()
                import re
                urls = re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", content)
                if urls:
                    tunnel_url = urls[-1]
                    break
        services["tunnel"] = {
            "status": "ok" if result.returncode == 0 else "down",
            "url": tunnel_url,
        }
    except Exception:
        services["tunnel"] = {"status": "unknown"}

    # Caches
    caches = {}
    for name in ["scanner", "analyser", "signals", "performance", "portfolio", "global_regime"]:
        path = DATA_DIR / f"{name}_cache.json"
        if path.exists():
            stat = path.stat()
            age_min = int((time.time() - stat.st_mtime) / 60)
            size_kb = round(stat.st_size / 1024, 1)
            caches[name] = {"exists": True, "age_minutes": age_min, "size_kb": size_kb}
        else:
            caches[name] = {"exists": False}

    return {
        "services": services,
        "caches": caches,
        "uptime_seconds": int(time.time() - _start_time),
    }


@router.post("/cache/clear/{name}")
def clear_cache(name: str):
    """Vide un cache spécifique."""
    if name == "all":
        cleared = []
        for f in DATA_DIR.glob("*_cache.json"):
            f.unlink()
            cleared.append(f.stem)
        return {"cleared": cleared}

    path = DATA_DIR / f"{name}_cache.json"
    if path.exists():
        path.unlink()
        return {"cleared": name}
    return {"error": f"Cache '{name}' non trouvé"}


@router.post("/cache/rebuild")
def rebuild_cache():
    """Lance le recalcul complet des caches (precompute_all)."""
    try:
        subprocess.Popen(
            ["python", "scripts/precompute_all.py"],
            stdout=open(LOG_DIR / "rebuild.log", "w"),
            stderr=subprocess.STDOUT,
        )
        return {"status": "started", "message": "Recalcul lancé en arrière-plan. Consultez logs/rebuild.log."}
    except Exception as e:
        return {"error": str(e)}


@router.get("/positions")
def admin_positions(db: Session = Depends(get_sync_db)):
    """Toutes les positions (ouvertes et fermées)."""
    positions = db.query(Position).order_by(Position.opened_at.desc()).limit(50).all()
    result = []
    for p in positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        result.append({
            "id": p.id,
            "symbol": asset.symbol if asset else "?",
            "direction": p.direction.value,
            "quantity": float(p.quantity),
            "entry_price": float(p.entry_price),
            "status": p.status.value,
            "opened_at": p.opened_at.isoformat() if p.opened_at else None,
            "closed_at": p.closed_at.isoformat() if p.closed_at else None,
        })
    return result


@router.delete("/positions/{position_id}")
def close_position(position_id: int, db: Session = Depends(get_sync_db)):
    """Ferme une position en BDD."""
    p = db.query(Position).filter_by(id=position_id).first()
    if not p:
        return {"error": "Position non trouvée"}
    p.status = PositionStatus.CLOSED
    p.closed_at = datetime.utcnow()
    db.commit()
    return {"closed": position_id}


@router.delete("/positions/clean/phantoms")
def clean_phantom_positions(db: Session = Depends(get_sync_db)):
    """Ferme les positions fantômes (pas sur Alpaca)."""
    try:
        from backend.modules.execution.broker_alpaca import alpaca_broker
        alpaca_symbols = set()
        if alpaca_broker.is_configured:
            for ap in alpaca_broker.get_positions():
                alpaca_symbols.add(ap["symbol"])
    except Exception:
        return {"error": "Impossible de récupérer les positions Alpaca"}

    closed = 0
    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    for p in positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if asset and asset.symbol not in alpaca_symbols:
            p.status = PositionStatus.CLOSED
            p.closed_at = datetime.utcnow()
            closed += 1
    db.commit()
    return {"closed": closed, "alpaca_positions": len(alpaca_symbols)}


@router.get("/users")
def list_users():
    """Liste les utilisateurs."""
    from backend.auth import get_all_users
    return get_all_users()


@router.put("/users/{email}/admin")
def toggle_admin(email: str, body: dict):
    """Définit ou retire le statut admin d'un utilisateur."""
    from backend.auth import set_user_admin
    is_admin = body.get("is_admin", False)
    return set_user_admin(email, is_admin)


@router.delete("/users/{email}")
def delete_user(email: str):
    """Supprime un utilisateur."""
    users_file = DATA_DIR / "users.json"
    if not users_file.exists():
        return {"error": "Fichier utilisateurs non trouvé"}
    users = json.loads(users_file.read_text())
    before = len(users)
    users = {k: v for k, v in users.items() if k != email} if isinstance(users, dict) else [u for u in users if u["email"] != email]
    if (isinstance(users, dict) and len(users) == before) or (isinstance(users, list) and len(users) == before):
        return {"error": f"Utilisateur {email} non trouvé"}
    users_file.write_text(json.dumps(users, indent=2))
    return {"deleted": email, "remaining": len(users)}


@router.get("/logs")
def get_logs(name: str = "backend", lines: int = 100):
    """Dernières lignes d'un fichier log."""
    log_path = LOG_DIR / f"{name}.log"
    if not log_path.exists():
        available = [f.stem for f in LOG_DIR.glob("*.log")]
        return {"error": f"Log '{name}' non trouvé", "available": available}

    content = log_path.read_text()
    log_lines = content.strip().split("\n")
    return {
        "name": name,
        "total_lines": len(log_lines),
        "lines": log_lines[-lines:],
    }


@router.get("/logs/list")
def list_logs():
    """Liste les fichiers log disponibles."""
    logs = []
    if LOG_DIR.exists():
        for f in sorted(LOG_DIR.glob("*.log")):
            stat = f.stat()
            logs.append({
                "name": f.stem,
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    return logs


@router.get("/db/stats")
def db_stats(db: Session = Depends(get_sync_db)):
    """Statistiques de la base de données."""
    from backend.database.models import OHLCVDaily, OHLCV1H, FeaturesDaily, Signal
    return {
        "assets": db.query(Asset).count(),
        "assets_active": db.query(Asset).filter_by(is_active=True).count(),
        "ohlcv_daily": db.query(OHLCVDaily).count(),
        "ohlcv_1h": db.query(OHLCV1H).count(),
        "features": db.query(FeaturesDaily).count(),
        "signals": db.query(Signal).count(),
        "orders": db.query(Order).count(),
        "positions_open": db.query(Position).filter_by(status=PositionStatus.OPEN).count(),
        "positions_closed": db.query(Position).filter_by(status=PositionStatus.CLOSED).count(),
    }


_start_time = time.time()
