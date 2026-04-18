"""Module 6 — Suivi de Rentabilité : Logique métier"""

import logging
from sqlalchemy.orm import Session

logger = logging.getLogger("tradepilot.performance.service")

from backend.database.models import Position, PositionStatus
from backend.modules.portfolio.service import PortfolioService
from backend.modules.performance.analytics import (
    compute_pnl_attribution, run_monte_carlo, compute_ews,
    compute_meta_score, generate_feedback,
)


class PerformanceService:
    def __init__(self, db: Session):
        self.db = db
        self.portfolio = PortfolioService(db)

    def _get_closed_trades(self) -> list[dict]:
        """Récupère les trades fermés."""
        positions = self.db.query(Position).filter_by(status=PositionStatus.CLOSED).all()
        return [
            {
                "pnl": float(p.pnl or 0),
                "pnl_pct": float(p.pnl_percent or 0) if p.pnl_percent else 0,
                "entry_price": float(p.entry_price),
                "exit_price": float(p.exit_price) if p.exit_price else float(p.entry_price),
                "direction": p.direction.value,
                "scanner_score": 50,  # Phase 1 : pas encore de lien signal→trade
                "slippage_cost": 0,
                "commission": 0,
            }
            for p in positions
        ]

    def _get_equity_curve(self) -> list[float]:
        """Construit la courbe d'equity."""
        # Phase 1 : equity = capital initial + P&L des positions ouvertes
        portfolio = self.portfolio.get_portfolio_summary()
        initial_capital = 100_000
        current_equity = initial_capital + portfolio["total_pnl"]
        # Simuler quelques points pour que les analytics fonctionnent
        return [initial_capital, current_equity]

    def get_full_report(self) -> dict:
        """Rapport de performance complet."""
        trades = self._get_closed_trades()
        equity_curve = self._get_equity_curve()
        portfolio_summary = self.portfolio.get_portfolio_summary()

        # Attribution P&L
        attribution = compute_pnl_attribution(trades)

        # Monte Carlo
        if len(equity_curve) >= 20:
            monte_carlo = run_monte_carlo(equity_curve)
        else:
            monte_carlo = {
                "status": "insufficient_data",
                "message": f"Minimum 20 points ({len(equity_curve)} disponibles). Se remplit avec le temps.",
            }

        # EWS
        ews = compute_ews(equity_curve, trades)

        # Métriques de base — inclure les positions live Alpaca
        win_rate = 0
        trades_with_pnl = [t for t in trades if t["pnl"] != 0]
        if trades_with_pnl:
            win_rate = sum(1 for t in trades_with_pnl if t["pnl"] > 0) / len(trades_with_pnl)

        # Si pas assez de trades fermés avec P&L, utiliser les positions live Alpaca
        if len(trades_with_pnl) < 5:
            try:
                from backend.modules.execution.broker_alpaca import alpaca_broker
                if alpaca_broker.is_configured:
                    live_positions = alpaca_broker.get_positions()
                    if live_positions:
                        live_winners = sum(1 for p in live_positions if float(p.get("pnl", 0)) >= 0)
                        win_rate = live_winners / len(live_positions)
            except Exception as e:
                logger.warning(f"[PERFORMANCE] Alpaca live positions fetch failed: {e}")

        sharpe = portfolio_summary["regime"]["metrics"]["sharpe_ratio"] if "metrics" in portfolio_summary.get("regime", {}) else 0

        # Meta-Score
        meta = compute_meta_score(
            ews, portfolio_summary["regime"]["regime"], win_rate, sharpe
        )

        # Feedback Loop → Module 1
        feedback = generate_feedback(meta, ews, attribution)

        return {
            "equity": {
                "initial": 100_000,
                "current": round(equity_curve[-1], 2),
                "pnl": round(equity_curve[-1] - 100_000, 2),
                "pnl_pct": round((equity_curve[-1] / 100_000 - 1) * 100, 2),
            },
            "trades": {
                "total": len(trades),
                "winning": sum(1 for t in trades if t["pnl"] > 0),
                "losing": sum(1 for t in trades if t["pnl"] < 0),
                "win_rate": round(win_rate * 100, 1),
            },
            "attribution": attribution,
            "monte_carlo": monte_carlo,
            "ews": ews,
            "meta_score": meta,
            "feedback_loop": feedback,
            "portfolio_regime": portfolio_summary["regime"],
            "benchmarks": _compute_benchmarks(equity_curve),
        }

    def get_meta_score(self) -> dict:
        """Meta-Score seul."""
        report = self.get_full_report()
        return report["meta_score"]

    def get_ews(self) -> dict:
        """Early Warning System seul."""
        trades = self._get_closed_trades()
        equity_curve = self._get_equity_curve()
        return compute_ews(equity_curve, trades)

    def get_feedback(self) -> dict:
        """Feedback loop pour le Module 1."""
        report = self.get_full_report()
        return report["feedback_loop"]


def _compute_benchmarks(equity_curve: list[float]) -> dict:
    """Comparaison vs benchmarks simples."""
    if len(equity_curve) < 2:
        return {"status": "insufficient_data"}

    total_return = (equity_curve[-1] / equity_curve[0] - 1) * 100

    return {
        "strategy_return": round(total_return, 2),
        "benchmarks": {
            "buy_hold_sp500": "N/A — données benchmark non chargées",
            "sixty_forty": "N/A — données benchmark non chargées",
            "momentum_simple": "N/A — données benchmark non chargées",
        },
        "note": "Les benchmarks seront connectés quand l'historique de trades sera suffisant",
    }
