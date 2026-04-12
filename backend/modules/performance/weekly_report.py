"""Rapport hebdomadaire automatique

Génère un rapport complet chaque dimanche qui résume :
1. Performance de la semaine (P&L, rendement, vs benchmarks)
2. Trades de la semaine (ouverts, fermés, win rate)
3. Meilleures et pires positions
4. Analyse des risques (VaR, drawdown, corrélation)
5. Signaux de la semaine (GO exécutés, ignorés)
6. Recommandations d'amélioration (feedback loop)
7. Score de santé du système (Meta-Score + EWS)

Le rapport est sauvegardé dans data/weekly_reports/ et peut être
consulté via l'API.
"""

import json
from pathlib import Path
from datetime import datetime, date, timedelta

from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily, Position, Order, PositionStatus, SignalDirection
from backend.modules.performance.performance_v2 import (
    compute_benchmarks, compute_trading_stats, compute_performance_by_class,
    compute_live_ratios, get_equity_curve, record_equity,
)
from backend.modules.portfolio.portfolio_v2 import (
    compute_var, check_drawdown_control, compute_risk_budget,
    compute_exposure, compute_portfolio_beta,
)

REPORTS_DIR = Path("data/weekly_reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_weekly_report(db: Session, initial_capital: float = 100_000) -> dict:
    """Génère le rapport hebdomadaire complet."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday() + 7)  # Lundi dernier
    week_end = week_start + timedelta(days=6)

    # Enregistrer l'equity
    record_equity(db, initial_capital)

    # === 1. Performance de la semaine ===
    benchmarks = compute_benchmarks(db, initial_capital=initial_capital)
    equity = get_equity_curve()
    live_ratios = compute_live_ratios(initial_capital)

    # P&L de la semaine (ouvert)
    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    weekly_pnl = 0
    best_position = {"symbol": "-", "pnl": 0}
    worst_position = {"symbol": "-", "pnl": 0}
    positions_detail = []

    for p in positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if not asset:
            continue
        last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
        if not last:
            continue
        price = float(last.close)
        if p.direction == SignalDirection.LONG:
            pnl = (price - p.entry_price) * p.quantity
            pnl_pct = (price / p.entry_price - 1) * 100
        else:
            pnl = (p.entry_price - price) * p.quantity
            pnl_pct = (1 - price / p.entry_price) * 100

        weekly_pnl += pnl
        detail = {
            "symbol": asset.symbol,
            "direction": p.direction.value,
            "entry": float(p.entry_price),
            "current": price,
            "pnl": round(float(pnl), 2),
            "pnl_pct": round(float(pnl_pct), 2),
        }
        positions_detail.append(detail)

        if pnl > best_position["pnl"]:
            best_position = {"symbol": asset.symbol, "pnl": round(float(pnl), 2), "pnl_pct": round(float(pnl_pct), 2)}
        if pnl < worst_position["pnl"]:
            worst_position = {"symbol": asset.symbol, "pnl": round(float(pnl), 2), "pnl_pct": round(float(pnl_pct), 2)}

    # === 2. Trades de la semaine ===
    stats = compute_trading_stats(db)

    # Ordres de la semaine
    week_orders = db.query(Order).filter(
        Order.created_at >= datetime.combine(week_start, datetime.min.time())
    ).all() if week_start else []

    # === 3. Risques ===
    var = compute_var(db)
    dd = check_drawdown_control(db, initial_capital=initial_capital)
    budget = compute_risk_budget(db, initial_capital=initial_capital)
    exposure = compute_exposure(db)
    beta = compute_portfolio_beta(db)

    # === 4. Recommandations ===
    recommendations = []

    if dd["level"] in ("WARNING", "ALERT", "CRITICAL"):
        recommendations.append({
            "priority": "HIGH",
            "action": dd["action"],
            "reason": dd["message"],
        })

    if exposure.get("concentration_risk") in ("HIGH", "CRITICAL"):
        recommendations.append({
            "priority": "MEDIUM",
            "action": "DIVERSIFIER",
            "reason": f"Concentration sectorielle {exposure['max_sector_exposure']} — diversifier",
        })

    if beta.get("beta", 1) > 1.3:
        recommendations.append({
            "priority": "MEDIUM",
            "action": "RÉDUIRE_BETA",
            "reason": f"Beta {beta['beta']:.2f} — portefeuille trop agressif",
        })

    if budget.get("budget_remaining_pct", 100) < 50:
        recommendations.append({
            "priority": "HIGH",
            "action": "RÉDUIRE_RISQUE",
            "reason": f"Budget risque à {budget['budget_remaining_pct']:.0f}% — réduire les positions",
        })

    if not recommendations:
        recommendations.append({
            "priority": "LOW",
            "action": "CONTINUER",
            "reason": "Pas de problème détecté — maintenir la stratégie",
        })

    # === 5. Score de santé ===
    from backend.modules.performance.service import PerformanceService
    perf_service = PerformanceService(db)
    meta = perf_service.get_meta_score()
    ews = perf_service.get_ews()

    # === Rapport final ===
    report = {
        "period": {
            "week_start": str(week_start),
            "week_end": str(week_end),
            "generated_at": datetime.utcnow().isoformat(),
        },
        "summary": {
            "equity": round(initial_capital + weekly_pnl, 2),
            "weekly_pnl": round(weekly_pnl, 2),
            "weekly_return_pct": round(weekly_pnl / initial_capital * 100, 3),
            "total_positions": len(positions),
            "orders_this_week": len(week_orders),
        },
        "vs_benchmarks": benchmarks,
        "best_position": best_position,
        "worst_position": worst_position,
        "positions": sorted(positions_detail, key=lambda x: x["pnl"], reverse=True),
        "trading_stats": stats,
        "by_asset_class": compute_performance_by_class(db),
        "risk": {
            "drawdown": dd,
            "var": var,
            "risk_budget": budget,
            "beta": beta,
            "exposure": exposure,
        },
        "live_ratios": live_ratios,
        "meta_score": meta,
        "ews": ews,
        "recommendations": recommendations,
    }

    # Sauvegarder
    filename = f"week_{week_start}_{week_end}.json"
    filepath = REPORTS_DIR / filename
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    report["saved_to"] = str(filepath)
    return report


def list_weekly_reports() -> list[dict]:
    """Liste les rapports hebdomadaires disponibles."""
    reports = []
    for f in sorted(REPORTS_DIR.glob("week_*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
            reports.append({
                "filename": f.name,
                "period": data.get("period", {}),
                "weekly_pnl": data.get("summary", {}).get("weekly_pnl", 0),
                "meta_score": data.get("meta_score", {}).get("meta_score", 0),
            })
        except Exception:
            pass
    return reports


def get_weekly_report(filename: str) -> dict | None:
    """Récupère un rapport hebdomadaire spécifique."""
    filepath = REPORTS_DIR / filename
    if filepath.exists():
        return json.loads(filepath.read_text())
    return None
