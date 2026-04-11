"""Module 5 — Gestion du Portefeuille : API endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.modules.portfolio.service import PortfolioService

router = APIRouter()


@router.get("/summary")
def get_portfolio_summary(db: Session = Depends(get_sync_db)):
    """Résumé complet du portefeuille."""
    return PortfolioService(db).get_portfolio_summary()


@router.get("/risk-parity")
def get_risk_parity(db: Session = Depends(get_sync_db)):
    """Allocation Risk Parity optimale."""
    return PortfolioService(db).get_risk_parity()


@router.get("/stress-test")
def run_stress_tests(db: Session = Depends(get_sync_db)):
    """Stress tests sur tous les scénarios."""
    return PortfolioService(db).run_stress_tests()


@router.get("/positions")
def list_positions(db: Session = Depends(get_sync_db)):
    """Positions ouvertes avec données enrichies."""
    return PortfolioService(db).get_portfolio_summary()["positions"]
