"""Module 1 — Scanner de Marché : API endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.database.models import Asset, OHLCVDaily
from backend.modules.scanner.service import ScannerService
from backend.modules.scanner.sentiment import fetch_reddit_mentions, compute_sentiment_score
from backend.modules.scanner.multi_timeframe import compute_mta_score
from backend.modules.scanner.cache import (
    get_cached_results, is_cache_fresh, is_updating,
    update_cache, set_updating,
)
from backend.database.models import OHLCV1H

import threading

router = APIRouter()


def _run_scan_background(db_url: str):
    """Exécute le scan en arrière-plan et met à jour le cache."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SyncSession
    try:
        engine = create_engine(db_url)
        with SyncSession(engine) as db:
            service = ScannerService(db)
            results = service.scan_all()
            update_cache(results)
    except Exception as e:
        from backend.modules.scanner.cache import _cache
        _cache["updating"] = False
        print(f"[SCANNER] Erreur scan background: {e}")


@router.get("/scan")
def scan_market(db: Session = Depends(get_sync_db)):
    """Retourne les résultats du scanner (avec cache 5min)."""
    if is_cache_fresh():
        return get_cached_results()

    # Si un scan tourne déjà, retourner le cache même périmé
    if is_updating():
        cached = get_cached_results()
        if cached:
            return cached

    # Lancer le scan en arrière-plan
    set_updating()
    from backend.config.settings import settings
    thread = threading.Thread(
        target=_run_scan_background,
        args=(settings.DATABASE_URL,),
        daemon=True,
    )
    thread.start()

    # Retourner le cache existant ou un message
    cached = get_cached_results()
    if cached:
        return cached

    # Premier scan — retourner les actifs sans score en attendant
    assets = db.query(Asset).filter_by(is_active=True).all()
    quick_results = []
    for asset in assets:
        last = (
            db.query(OHLCVDaily)
            .filter_by(asset_id=asset.id)
            .order_by(OHLCVDaily.date.desc())
            .first()
        )
        quick_results.append({
            "symbol": asset.symbol,
            "name": asset.name,
            "asset_class": asset.asset_class.value,
            "scores": {
                "correlation": 50, "sentiment": 50, "technical": 50,
                "genome": 50, "ipi": 50, "ivf": 50,
                "mts": 50, "sgi": 50, "sus": 50, "final": 50,
            },
            "weights": {},
            "vetoed": False,
            "veto_reasons": [],
            "last_close": float(last.close) if last else 0,
            "data_points": 0,
            "details": {},
            "_loading": True,
        })
    return quick_results


@router.get("/analyse")
def analyse_any_asset(q: str):
    """Analyse complète d'un actif quelconque (pas besoin d'être en BDD).

    Exemples : ?q=PLTR, ?q=S&P 500, ?q=COIN, ?q=AMC, ?q=CAC 40
    """
    from backend.modules.scanner.quick_analyse import quick_analyse
    return quick_analyse(q)


@router.get("/correlation-map")
def get_correlation_map(q: str = "", lookback: int = 120, db: Session = Depends(get_sync_db)):
    """Carte de corrélation — accepte noms en français.

    Exemples : ?q=petrole, ?q=or, ?q=bitcoin, ?q=CL=F, ?q=NVDA
    """
    from backend.modules.scanner.correlation_map import compute_correlation_map
    from backend.modules.scanner.quick_analyse import resolve_symbol
    resolved = resolve_symbol(q)
    return compute_correlation_map(db, resolved, lookback)


@router.get("/impact-simulation")
def simulate_impact_endpoint(q: str = "", move_pct: float = 10, lookback: int = 120, db: Session = Depends(get_sync_db)):
    """Simule l'impact d'un mouvement sur les actifs corrélés.

    Exemple : ?q=petrole&move_pct=20
    """
    from backend.modules.scanner.correlation_map import simulate_impact
    from backend.modules.scanner.quick_analyse import resolve_symbol
    resolved = resolve_symbol(q)
    return simulate_impact(db, resolved, move_pct, lookback)


@router.get("/fundamental/{symbol}")
def get_fundamentals(symbol: str):
    """Analyse fondamentale complète d'un actif."""
    from backend.modules.scanner.fundamental import compute_fundamental_score
    return compute_fundamental_score(symbol)


@router.get("/results/{symbol}")
def get_scan_result(symbol: str, db: Session = Depends(get_sync_db)):
    """Retourne le résultat de scan pour un actif donné."""
    service = ScannerService(db)
    return service.scan_asset(symbol)


@router.get("/assets")
def list_assets(db: Session = Depends(get_sync_db)):
    """Liste tous les actifs en base."""
    assets = db.query(Asset).filter_by(is_active=True).all()
    return [
        {
            "id": a.id,
            "symbol": a.symbol,
            "name": a.name,
            "asset_class": a.asset_class.value,
        }
        for a in assets
    ]


@router.get("/ohlcv/{symbol}")
def get_ohlcv(symbol: str, limit: int = 100, db: Session = Depends(get_sync_db)):
    """Retourne les données OHLCV daily d'un actif."""
    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return {"error": f"Actif {symbol} non trouvé"}

    rows = (
        db.query(OHLCVDaily)
        .filter_by(asset_id=asset.id)
        .order_by(OHLCVDaily.date.desc())
        .limit(limit)
        .all()
    )

    return {
        "symbol": symbol,
        "name": asset.name,
        "count": len(rows),
        "data": [
            {
                "date": str(r.date),
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            }
            for r in reversed(rows)
        ],
    }


@router.get("/sentiment/{symbol}")
async def get_sentiment(symbol: str):
    """Score de sentiment pour un actif (Reddit + simulation)."""
    mentions = await fetch_reddit_mentions(symbol)
    result = compute_sentiment_score(mentions)
    result["symbol"] = symbol
    return result


@router.get("/ohlcv-1h/{symbol}")
def get_ohlcv_1h(symbol: str, limit: int = 168, db: Session = Depends(get_sync_db)):
    """Données OHLCV intraday 1H d'un actif."""
    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return {"error": f"Actif {symbol} non trouvé"}

    rows = (
        db.query(OHLCV1H)
        .filter_by(asset_id=asset.id)
        .order_by(OHLCV1H.datetime.desc())
        .limit(limit)
        .all()
    )

    return {
        "symbol": symbol,
        "timeframe": "1h",
        "count": len(rows),
        "data": [
            {
                "datetime": r.datetime.isoformat(),
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            }
            for r in reversed(rows)
        ],
    }


@router.get("/mta/{symbol}")
def get_multi_timeframe(symbol: str, db: Session = Depends(get_sync_db)):
    """Analyse Multi-Timeframe (Daily + 1H) pour un actif."""
    import pandas as pd

    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return {"error": f"Actif {symbol} non trouvé"}

    # Daily
    daily_rows = (
        db.query(OHLCVDaily).filter_by(asset_id=asset.id)
        .order_by(OHLCVDaily.date.asc()).all()
    )
    daily_close = pd.Series([float(r.close) for r in daily_rows]) if daily_rows else pd.Series()

    # 1H
    hourly_rows = (
        db.query(OHLCV1H).filter_by(asset_id=asset.id)
        .order_by(OHLCV1H.datetime.asc()).all()
    )
    hourly_close = pd.Series([float(r.close) for r in hourly_rows]) if hourly_rows else None

    result = compute_mta_score(daily_close, hourly_close)
    result["symbol"] = symbol
    return result


# ============================================================
# Endpoints LIVE (Alpaca temps réel)
# ============================================================

from backend.modules.scanner.live_data import get_live_quote, get_live_bars, is_alpaca_symbol


@router.get("/live/quote/{symbol}")
def live_quote(symbol: str):
    """Prix temps réel via Alpaca."""
    quote = get_live_quote(symbol)
    if quote:
        return quote
    return {"symbol": symbol, "error": "Pas de données live pour cet actif", "source": "unavailable"}


@router.get("/live/quotes")
def live_quotes_all(db: Session = Depends(get_sync_db)):
    """Prix temps réel pour tous les actifs supportés par Alpaca."""
    assets = db.query(Asset).filter_by(is_active=True).all()
    results = []
    for asset in assets:
        quote = get_live_quote(asset.symbol)
        if quote:
            quote["name"] = asset.name
            quote["asset_class"] = asset.asset_class.value
            results.append(quote)
        else:
            # Fallback BDD
            last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
            results.append({
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_class": asset.asset_class.value,
                "price": float(last.close) if last else 0,
                "source": "database",
            })
    return results


@router.get("/live/bars/{symbol}")
def live_bars(symbol: str, timeframe: str = "1Day", limit: int = 100):
    """Barres OHLCV live via Alpaca."""
    bars = get_live_bars(symbol, timeframe, limit)
    if bars:
        return {"symbol": symbol, "timeframe": timeframe, "count": len(bars), "data": bars, "source": "alpaca_live"}
    return {"symbol": symbol, "error": "Pas de données live", "source": "unavailable"}
