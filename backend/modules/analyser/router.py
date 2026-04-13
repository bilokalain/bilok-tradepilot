"""Module 2 — Analyseur de Stratégies : API endpoints"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.modules.analyser.service import AnalyserService

router = APIRouter()


@router.get("/analyse")
def analyse_all(db: Session = Depends(get_sync_db)):
    """Retourne les analyses depuis le cache. Calcul live en fallback."""
    from backend.cache_global import get_analyser_cache
    cached = get_analyser_cache()
    if cached.get("analyses"):
        return cached["analyses"]
    # Fallback live (lent)
    service = AnalyserService(db)
    return service.analyse_all()


@router.get("/analyse/{symbol}")
def analyse_asset(symbol: str, db: Session = Depends(get_sync_db)):
    """Analyse d'un seul actif — toujours en live (rapide)."""
    service = AnalyserService(db)
    return service.analyse_asset(symbol)


@router.get("/regime")
def get_market_regime(db: Session = Depends(get_sync_db)):
    """Régime depuis le cache, fallback live."""
    from backend.cache_global import get_analyser_cache
    cached = get_analyser_cache()
    if cached.get("regime"):
        return cached["regime"]
    service = AnalyserService(db)
    return service.get_regime_summary()


# ============================================================
# THÈSES MANUELLES
# ============================================================

class ThesisRequest(BaseModel):
    theme: str
    direction: str = "HAUSSE"
    conviction: str = "MOYENNE"
    reason: str = ""
    horizon_days: int = 30
    custom_symbols_long: list[str] | None = None
    custom_symbols_short: list[str] | None = None


@router.post("/thesis")
def create_thesis(req: ThesisRequest):
    """Créer une thèse manuelle."""
    from backend.modules.analyser.manual_thesis import add_thesis
    return add_thesis(
        theme=req.theme, direction=req.direction, conviction=req.conviction,
        reason=req.reason, horizon_days=req.horizon_days,
        custom_symbols_long=req.custom_symbols_long,
        custom_symbols_short=req.custom_symbols_short,
    )


@router.get("/theses")
def list_theses():
    """Liste les thèses actives."""
    from backend.modules.analyser.manual_thesis import get_active_theses
    return get_active_theses()


@router.get("/theses/all")
def list_all_theses():
    """Liste toutes les thèses (actives et expirées)."""
    from backend.modules.analyser.manual_thesis import _load_theses
    return _load_theses()


@router.delete("/thesis/{thesis_id}")
def delete_thesis(thesis_id: str):
    """Supprimer une thèse."""
    from backend.modules.analyser.manual_thesis import remove_thesis
    remove_thesis(thesis_id)
    return {"deleted": thesis_id}


@router.post("/thesis/{thesis_id}/deactivate")
def deactivate_thesis_endpoint(thesis_id: str):
    """Désactiver une thèse sans la supprimer."""
    from backend.modules.analyser.manual_thesis import deactivate_thesis
    deactivate_thesis(thesis_id)
    return {"deactivated": thesis_id}


@router.get("/thesis/{thesis_id}/plan")
def get_trade_plan(thesis_id: str, db: Session = Depends(get_sync_db)):
    """Génère le plan de trade pour une thèse."""
    from backend.modules.analyser.manual_thesis import generate_trade_plan
    return generate_trade_plan(db, thesis_id)


@router.get("/thesis/boost/{symbol}")
def get_thesis_boost(symbol: str):
    """Vérifie si un actif est boosté par une thèse active."""
    from backend.modules.analyser.manual_thesis import compute_thesis_boost
    return compute_thesis_boost(symbol)


@router.get("/thesis/themes")
def list_available_themes():
    """Liste les thèmes disponibles avec leurs actifs."""
    from backend.modules.analyser.manual_thesis import THEME_ASSETS
    return {
        theme: {
            "long": data["long"],
            "short": data["short"],
            "description": data["description"],
        }
        for theme, data in THEME_ASSETS.items()
    }
