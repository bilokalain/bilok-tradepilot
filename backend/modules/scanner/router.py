"""Module 1 — Scanner de Marché : API endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.database.models import Asset, OHLCVDaily
from backend.modules.scanner.service import ScannerService
from backend.modules.scanner.sentiment import fetch_reddit_mentions, compute_sentiment_score
from backend.modules.scanner.multi_timeframe import compute_mta_score
from backend.database.models import OHLCV1H

router = APIRouter()


@router.get("/scan")
def scan_market(db: Session = Depends(get_sync_db)):
    """Lance un scan complet de tous les actifs."""
    service = ScannerService(db)
    return service.scan_all()


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
