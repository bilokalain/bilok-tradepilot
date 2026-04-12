"""Module 6 — Suivi de Rentabilité V2 : API endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.modules.performance.service import PerformanceService
from backend.modules.performance.performance_v2 import (
    compute_benchmarks, record_equity, get_equity_curve,
    compute_trading_stats, compute_performance_by_class,
    compute_live_ratios, generate_full_report,
)

router = APIRouter()


@router.get("/report")
def get_full_report(db: Session = Depends(get_sync_db)):
    """Rapport V1 (compatibilité)."""
    return PerformanceService(db).get_full_report()


@router.get("/report-v2")
def get_full_report_v2(db: Session = Depends(get_sync_db)):
    """Rapport V2 complet — benchmarks, stats, equity curve, ratios."""
    return generate_full_report(db)


@router.get("/meta-score")
def get_meta_score(db: Session = Depends(get_sync_db)):
    """Meta-Score santé du système."""
    return PerformanceService(db).get_meta_score()


@router.get("/ews")
def get_ews(db: Session = Depends(get_sync_db)):
    """Early Warning System."""
    return PerformanceService(db).get_ews()


@router.get("/feedback")
def get_feedback(db: Session = Depends(get_sync_db)):
    """Feedback loop vers le Module 1."""
    return PerformanceService(db).get_feedback()


@router.get("/attribution")
def get_attribution(db: Session = Depends(get_sync_db)):
    """Attribution causale P&L."""
    report = PerformanceService(db).get_full_report()
    return report["attribution"]


@router.get("/benchmarks")
def get_benchmarks(db: Session = Depends(get_sync_db)):
    """Performance vs benchmarks (SPY, 60/40)."""
    return compute_benchmarks(db)


@router.get("/equity-curve")
def get_equity(db: Session = Depends(get_sync_db)):
    """Equity curve live."""
    record_equity(db)
    return get_equity_curve()


@router.get("/stats")
def get_trading_stats(db: Session = Depends(get_sync_db)):
    """Statistiques de trading détaillées."""
    return compute_trading_stats(db)


@router.get("/by-class")
def get_perf_by_class(db: Session = Depends(get_sync_db)):
    """Performance par classe d'actif."""
    return compute_performance_by_class(db)


@router.get("/ratios")
def get_live_ratios():
    """Sharpe, Sortino, Calmar live."""
    return compute_live_ratios()
