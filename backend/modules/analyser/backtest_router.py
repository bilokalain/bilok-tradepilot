"""Backtesting : API endpoints"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import pandas as pd

from backend.database.sync_session import get_sync_db
from backend.database.models import Asset, OHLCVDaily
from backend.modules.analyser.backtester import run_backtest, run_walk_forward

router = APIRouter()

STRATEGIES = [
    "trend_following", "mean_reversion", "breakout", "momentum",
    "adaptive_trend", "multi_signal", "keltner_breakout",
    "vwap_reversion", "momentum_rotation",
    "mean_reversion_v2", "fibonacci", "ichimoku",
    "regime_cascade", "volatility_explosion", "anti_consensus",
]


def _load_ohlcv(db: Session, symbol: str) -> pd.DataFrame:
    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return pd.DataFrame()
    rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.asc()).all()
    if not rows:
        return pd.DataFrame()
    data = [{"date": r.date, "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume} for r in rows]
    df = pd.DataFrame(data)
    df.set_index("date", inplace=True)
    return df


@router.get("/run/{symbol}")
def backtest_symbol(
    symbol: str,
    strategy: str = Query("momentum", description="Stratégie à tester"),
    capital: float = Query(100_000),
    db: Session = Depends(get_sync_db),
):
    """Backtest une stratégie sur un actif."""
    df = _load_ohlcv(db, symbol)
    if df.empty:
        return {"error": f"Pas de données pour {symbol}"}
    result = run_backtest(df, strategy, symbol, capital)
    return result.to_dict()


@router.get("/compare/{symbol}")
def compare_strategies(
    symbol: str,
    db: Session = Depends(get_sync_db),
):
    """Compare toutes les stratégies sur un actif."""
    df = _load_ohlcv(db, symbol)
    if df.empty:
        return {"error": f"Pas de données pour {symbol}"}

    results = []
    for strat in STRATEGIES:
        result = run_backtest(df, strat, symbol)
        results.append(result.to_dict())

    results.sort(key=lambda r: r["sharpe_ratio"], reverse=True)
    return {"symbol": symbol, "strategies": results}


@router.get("/walk-forward/{symbol}")
def walk_forward(
    symbol: str,
    strategy: str = Query("momentum"),
    db: Session = Depends(get_sync_db),
):
    """Walk-forward testing sur un actif."""
    df = _load_ohlcv(db, symbol)
    if df.empty:
        return {"error": f"Pas de données pour {symbol}"}
    return run_walk_forward(df, strategy, symbol)
