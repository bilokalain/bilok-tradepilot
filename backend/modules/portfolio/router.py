"""Module 5 — Gestion du Portefeuille V2 : API endpoints"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.modules.portfolio.service import PortfolioService
from backend.modules.portfolio.portfolio_v2 import (
    compute_rebalancing, check_drawdown_control, compute_risk_budget,
    compute_var, compute_exposure, compute_portfolio_beta,
    compute_regime_allocation,
)

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


@router.get("/rebalancing")
def get_rebalancing(db: Session = Depends(get_sync_db)):
    """Calcule les ajustements de rebalancing nécessaires."""
    return compute_rebalancing(db)


@router.get("/drawdown-control")
def get_drawdown_control(
    capital: float = Query(100_000),
    db: Session = Depends(get_sync_db),
):
    """Vérifie le drawdown et recommande des actions."""
    return check_drawdown_control(db, initial_capital=capital)


@router.get("/risk-budget")
def get_risk_budget(
    max_loss_pct: float = Query(15.0),
    capital: float = Query(100_000),
    db: Session = Depends(get_sync_db),
):
    """Budget de risque restant."""
    return compute_risk_budget(db, max_loss_pct=max_loss_pct, initial_capital=capital)


@router.get("/var")
def get_var(
    confidence: float = Query(0.95),
    db: Session = Depends(get_sync_db),
):
    """Value at Risk — perte max à N% de confiance."""
    return compute_var(db, confidence=confidence)


@router.get("/exposure")
def get_exposure(db: Session = Depends(get_sync_db)):
    """Exposition par secteur, classe d'actif et devise."""
    return compute_exposure(db)


@router.get("/beta")
def get_beta(db: Session = Depends(get_sync_db)):
    """Beta du portefeuille vs SPY."""
    return compute_portfolio_beta(db)


@router.get("/regime-allocation")
def get_regime_allocation(db: Session = Depends(get_sync_db)):
    """Allocation ajustée selon le régime global."""
    from backend.modules.analyser.regime_global import detect_global_regime

    regime = detect_global_regime(db)
    summary = PortfolioService(db).get_portfolio_summary()
    allocation = summary.get("allocation", {})

    return compute_regime_allocation(regime, allocation)


@router.get("/dashboard")
def get_portfolio_dashboard(db: Session = Depends(get_sync_db)):
    """Dashboard complet du portefeuille — toutes les métriques en un appel."""
    summary = PortfolioService(db).get_portfolio_summary()
    dd = check_drawdown_control(db)
    budget = compute_risk_budget(db)
    var = compute_var(db)
    exposure = compute_exposure(db)
    beta = compute_portfolio_beta(db)
    rebal = compute_rebalancing(db)

    return {
        "summary": {
            "total_value": summary["total_value"],
            "total_pnl": summary["total_pnl"],
            "num_positions": summary["num_positions"],
            "regime": summary["regime"],
        },
        "risk": {
            "drawdown": dd,
            "risk_budget": budget,
            "var": var,
            "beta": beta,
        },
        "allocation": {
            "exposure": exposure,
            "rebalancing": rebal,
        },
    }


@router.get("/reversal")
def check_reversal(db: Session = Depends(get_sync_db)):
    """Vérifie les signaux de retournement de marché."""
    from backend.modules.portfolio.reversal_guard import check_reversal_signals
    return check_reversal_signals(db)


@router.post("/reversal/protect")
def execute_protection(db: Session = Depends(get_sync_db)):
    """Exécute les actions de protection (réduction ou clôture des positions)."""
    from backend.modules.portfolio.reversal_guard import auto_protect
    return auto_protect(db)


@router.get("/balance/analysis")
def balance_analysis():
    """Analyse l'équilibre actuel du portefeuille (LONG/SHORT, secteurs, levier)."""
    from backend.modules.portfolio.balancer import analyze_portfolio
    return analyze_portfolio()


@router.get("/balance/recommend")
def balance_recommend():
    """Recommande des ajustements LONG/SHORT pour rééquilibrer."""
    from backend.modules.portfolio.balancer import recommend_rebalance
    return recommend_rebalance()
