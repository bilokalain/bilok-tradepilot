"""Module 6 — Suivi de Rentabilité : API endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.modules.performance.service import PerformanceService

router = APIRouter()


@router.get("/report")
def get_full_report(db: Session = Depends(get_sync_db)):
    """Rapport de performance complet."""
    return PerformanceService(db).get_full_report()


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
