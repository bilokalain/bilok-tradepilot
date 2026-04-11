"""Module 4 — Exécution des Ordres : API endpoints"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.modules.execution.service import ExecutionService

router = APIRouter()


@router.post("/execute/{symbol}")
def execute_trade(
    symbol: str,
    capital: float = Query(100_000, description="Capital disponible"),
    db: Session = Depends(get_sync_db),
):
    """Exécute une thèse de trade pour un actif (paper trading)."""
    service = ExecutionService(db)
    return service.execute_thesis(symbol, capital)


@router.post("/execute-all")
def execute_all(
    capital: float = Query(100_000, description="Capital total"),
    db: Session = Depends(get_sync_db),
):
    """Exécute toutes les thèses GO (paper trading)."""
    service = ExecutionService(db)
    return service.execute_all_signals(capital)


@router.get("/positions")
def list_positions(db: Session = Depends(get_sync_db)):
    """Liste les positions ouvertes."""
    service = ExecutionService(db)
    return service.get_positions()


@router.get("/orders")
def list_orders(db: Session = Depends(get_sync_db)):
    """Liste les ordres récents."""
    service = ExecutionService(db)
    return service.get_orders()


@router.get("/bias-check")
def check_bias(db: Session = Depends(get_sync_db)):
    """Vérifie les biais comportementaux actuels."""
    from backend.modules.execution.bias_detector import run_full_bias_check
    # En Phase 1, pas de trades historiques → check neutre
    return run_full_bias_check([], entry_price=0, recent_prices=[])
