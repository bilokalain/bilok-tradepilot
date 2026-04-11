"""Module 3 — Moteur de Scoring : API endpoints (avec cache)"""

import time
import threading

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.modules.scoring.service import ScoringService

router = APIRouter()

# Cache pour les signaux (même principe que le scanner)
_signals_cache: dict = {"data": [], "last_updated": 0, "updating": False}
_theses_cache: dict = {"data": [], "last_updated": 0, "updating": False}
CACHE_TTL = 300  # 5 minutes


def _update_signals_bg(db_url: str, capital: float):
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session as SyncSession
        engine = create_engine(db_url)
        with SyncSession(engine) as db:
            svc = ScoringService(db)
            signals = svc.get_active_signals(capital)
            _signals_cache["data"] = signals
            _signals_cache["last_updated"] = time.time()
    except Exception as e:
        print(f"[SCORING] Erreur cache signaux: {e}")
    finally:
        _signals_cache["updating"] = False


def _update_theses_bg(db_url: str, capital: float):
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session as SyncSession
        engine = create_engine(db_url)
        with SyncSession(engine) as db:
            svc = ScoringService(db)
            theses = svc.generate_all_theses(capital)
            _theses_cache["data"] = theses
            _theses_cache["last_updated"] = time.time()
    except Exception as e:
        print(f"[SCORING] Erreur cache thèses: {e}")
    finally:
        _theses_cache["updating"] = False


@router.get("/thesis/{symbol}")
def get_trade_thesis(
    symbol: str,
    capital: float = Query(100_000),
    db: Session = Depends(get_sync_db),
):
    """Thèse de Trade complète pour un actif."""
    service = ScoringService(db)
    return service.generate_thesis(symbol, capital)


@router.get("/theses")
def get_all_theses(
    capital: float = Query(100_000),
    db: Session = Depends(get_sync_db),
):
    """Thèses de Trade pour tous les actifs (avec cache)."""
    now = time.time()
    if (now - _theses_cache["last_updated"]) < CACHE_TTL and _theses_cache["data"]:
        return _theses_cache["data"]

    if not _theses_cache["updating"]:
        _theses_cache["updating"] = True
        from backend.config.settings import settings
        threading.Thread(target=_update_theses_bg, args=(settings.DATABASE_URL, capital), daemon=True).start()

    if _theses_cache["data"]:
        return _theses_cache["data"]

    # Premier appel — calcul direct sur quelques actifs
    service = ScoringService(db)
    from backend.database.models import Asset
    assets = db.query(Asset).filter_by(is_active=True).limit(10).all()
    results = []
    for asset in assets:
        t = service.generate_thesis(asset.symbol, capital)
        if "error" not in t:
            results.append(t)
    return results


@router.get("/signals")
def get_active_signals(
    capital: float = Query(100_000),
    db: Session = Depends(get_sync_db),
):
    """Signaux actifs (avec cache)."""
    now = time.time()
    if (now - _signals_cache["last_updated"]) < CACHE_TTL and _signals_cache["data"]:
        return _signals_cache["data"]

    if not _signals_cache["updating"]:
        _signals_cache["updating"] = True
        from backend.config.settings import settings
        threading.Thread(target=_update_signals_bg, args=(settings.DATABASE_URL, capital), daemon=True).start()

    if _signals_cache["data"]:
        return _signals_cache["data"]

    # Premier appel — calcul direct rapide
    service = ScoringService(db)
    from backend.database.models import Asset
    assets = db.query(Asset).filter_by(is_active=True).limit(10).all()
    results = []
    for asset in assets:
        t = service.generate_thesis(asset.symbol, capital)
        if "error" not in t and t.get("action") == "GO":
            results.append(t)
    return results
