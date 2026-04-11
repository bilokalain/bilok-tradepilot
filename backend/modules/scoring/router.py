"""Module 3 — Moteur de Scoring : API endpoints"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.modules.scoring.service import ScoringService

router = APIRouter()


@router.get("/thesis/{symbol}")
def get_trade_thesis(
    symbol: str,
    capital: float = Query(100_000, description="Capital disponible en $"),
    db: Session = Depends(get_sync_db),
):
    """Thèse de Trade complète pour un actif."""
    service = ScoringService(db)
    return service.generate_thesis(symbol, capital)


@router.get("/theses")
def get_all_theses(
    capital: float = Query(100_000, description="Capital disponible en $"),
    db: Session = Depends(get_sync_db),
):
    """Thèses de Trade pour tous les actifs (triées par action + score)."""
    service = ScoringService(db)
    return service.generate_all_theses(capital)


@router.get("/signals")
def get_active_signals(
    capital: float = Query(100_000, description="Capital disponible en $"),
    db: Session = Depends(get_sync_db),
):
    """Signaux actifs uniquement (action = GO)."""
    service = ScoringService(db)
    return service.get_active_signals(capital)
