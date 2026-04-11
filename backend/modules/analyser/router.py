"""Module 2 — Analyseur de Stratégies : API endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.modules.analyser.service import AnalyserService

router = APIRouter()


@router.get("/analyse")
def analyse_all(db: Session = Depends(get_sync_db)):
    """Analyse tous les actifs : régime + stratégies."""
    service = AnalyserService(db)
    return service.analyse_all()


@router.get("/analyse/{symbol}")
def analyse_asset(symbol: str, db: Session = Depends(get_sync_db)):
    """Analyse complète d'un actif."""
    service = AnalyserService(db)
    return service.analyse_asset(symbol)


@router.get("/regime")
def get_market_regime(db: Session = Depends(get_sync_db)):
    """Résumé des régimes de marché détectés."""
    service = AnalyserService(db)
    return service.get_regime_summary()
