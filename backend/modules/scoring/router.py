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
    """Thèses de Trade depuis le cache disque."""
    from backend.cache_global import get_signals_cache
    cached = get_signals_cache()
    if cached:
        return cached
    if _theses_cache["data"]:
        return _theses_cache["data"]
    results = []
    return results


@router.get("/signals")
def get_active_signals(
    capital: float = Query(100_000),
    db: Session = Depends(get_sync_db),
):
    """Signaux actifs depuis le cache disque."""
    from backend.cache_global import get_signals_cache
    cached = get_signals_cache()
    if cached:
        return cached
    # Fallback mémoire
    if _signals_cache["data"]:
        return _signals_cache["data"]
    return []


@router.get("/v2/{symbol}")
def get_score_v2(symbol: str, db: Session = Depends(get_sync_db)):
    """Score V2 complet — intègre les 8 sources d'information."""
    from backend.modules.scoring.scorer_v2 import compute_score_v2
    from backend.modules.scanner.cache import get_cached_results
    from backend.modules.scanner.fundamental import compute_fundamental_score
    from backend.modules.analyser.regime_global import detect_global_regime
    from backend.modules.analyser.catalysts import compute_catalyst_adjustment
    from backend.modules.analyser.correlation_filter import check_portfolio_correlation
    from backend.modules.analyser.sector_rotation import detect_rotation, get_sector_score
    from backend.modules.analyser.lead_lag import detect_lead_lag
    from backend.modules.analyser.performance_matrix import get_best_strategy, get_strategy_sharpe
    from backend.database.models import Asset

    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return {"error": f"Actif {symbol} non trouvé"}

    # 1. Scanner score
    cached = get_cached_results()
    scan = next((r for r in cached if r.get("symbol") == symbol), None)
    scanner_score = scan["scores"]["final"] if scan else 50

    # 2. Stratégie + backtest
    best_strat = get_best_strategy(symbol) or "momentum"
    backtest_sharpe = get_strategy_sharpe(symbol, best_strat)
    conviction = min(90, max(30, 50 + backtest_sharpe * 20))

    # 3. Régime global
    regime_global = detect_global_regime(db)

    # 4. Fondamentaux
    fund = compute_fundamental_score(symbol)
    fundamental_score = fund.get("score") if fund.get("applicable") else None

    # 5. Catalyseurs
    catalyst = compute_catalyst_adjustment(symbol)

    # 6. Corrélation
    corr_check = check_portfolio_correlation(db, symbol)

    # 7. Sector rotation
    rotation = detect_rotation(db)
    sector = get_sector_score(symbol, rotation)

    # 8. Lead-lag
    lead_lag = detect_lead_lag(db, symbol)

    # Score V2
    result = compute_score_v2(
        scanner_score=scanner_score,
        strategy_conviction=conviction,
        backtest_sharpe=backtest_sharpe,
        regime_global=regime_global,
        fundamental_score=fundamental_score,
        catalyst_adjustment=catalyst,
        correlation_check=corr_check,
        sector_rotation_score=sector.get("score", 50),
        lead_lag_signal=lead_lag,
        asset_class=asset.asset_class.value,
    )

    result["symbol"] = symbol
    result["name"] = asset.name
    result["asset_class"] = asset.asset_class.value
    result["strategy"] = best_strat
    result["sector_rotation"] = sector
    result["regime_global"] = {
        "regime": regime_global.get("regime"),
        "confidence": regime_global.get("confidence"),
    }

    return result


@router.post("/ml/train")
def train_ml_model(db: Session = Depends(get_sync_db)):
    """Entraîne le modèle XGBoost sur les données historiques."""
    from backend.modules.scoring.ml_scorer import get_ml_scorer, generate_training_data
    scorer = get_ml_scorer()
    training_data = generate_training_data(db)
    if training_data.empty:
        return {"status": "error", "message": "Pas de données d'entraînement"}
    result = scorer.train(training_data)
    return result


@router.get("/ml/predict/{symbol}")
def ml_predict(symbol: str, db: Session = Depends(get_sync_db)):
    """Score ML pour un actif."""
    from backend.modules.scoring.ml_scorer import get_ml_scorer
    from backend.modules.scanner.cache import get_cached_results

    scorer = get_ml_scorer()
    cached = get_cached_results()
    scan = next((r for r in cached if r.get("symbol") == symbol), None)

    if not scan:
        return {"symbol": symbol, "error": "Pas de scan en cache"}

    scores = scan.get("scores", {})
    result = scorer.predict(scores, regime="BULL")
    result["symbol"] = symbol
    return result
