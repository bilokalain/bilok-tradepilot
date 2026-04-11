"""Module 5 — Gestion du Portefeuille : Logique métier"""

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily, Position, PositionStatus, SignalDirection
from backend.modules.portfolio.risk_parity import (
    compute_risk_parity_weights, compute_portfolio_volatility,
    run_stress_test, STRESS_SCENARIOS, detect_portfolio_regime,
    compute_liquidation_score,
)


class PortfolioService:
    def __init__(self, db: Session):
        self.db = db

    def _get_positions_data(self) -> list[dict]:
        """Charge les positions ouvertes avec données de marché."""
        positions = self.db.query(Position).filter_by(status=PositionStatus.OPEN).all()
        result = []
        for p in positions:
            asset = self.db.query(Asset).filter_by(id=p.asset_id).first()
            if not asset:
                continue
            last = (
                self.db.query(OHLCVDaily)
                .filter_by(asset_id=asset.id)
                .order_by(OHLCVDaily.date.desc())
                .first()
            )
            current_price = float(last.close) if last else p.entry_price
            market_value = current_price * p.quantity

            # Volume moyen 20j
            recent_vol = (
                self.db.query(OHLCVDaily)
                .filter_by(asset_id=asset.id)
                .order_by(OHLCVDaily.date.desc())
                .limit(20)
                .all()
            )
            avg_volume_usd = 0
            if recent_vol:
                avg_volume_usd = np.mean([float(r.volume) * float(r.close) for r in recent_vol])

            pnl = (current_price - p.entry_price) * p.quantity if p.direction == SignalDirection.LONG else (p.entry_price - current_price) * p.quantity
            pnl_pct = (current_price / p.entry_price - 1) * 100 if p.direction == SignalDirection.LONG else (1 - current_price / p.entry_price) * 100

            result.append({
                "id": p.id,
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_class": asset.asset_class.value,
                "direction": p.direction.value,
                "entry_price": float(p.entry_price),
                "current_price": current_price,
                "quantity": float(p.quantity),
                "market_value": round(market_value, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "avg_volume_usd": round(avg_volume_usd, 2),
            })
        return result

    def get_portfolio_summary(self) -> dict:
        """Résumé complet du portefeuille."""
        positions = self._get_positions_data()
        total_value = sum(p["market_value"] for p in positions)
        total_pnl = sum(p["pnl"] for p in positions)

        # Allocation par classe d'actifs
        allocation = {}
        for p in positions:
            ac = p["asset_class"]
            allocation[ac] = allocation.get(ac, 0) + p["market_value"]

        allocation_pct = {k: round(v / total_value * 100, 1) if total_value else 0 for k, v in allocation.items()}

        # Liquidation scores
        for p in positions:
            p["liquidation_score"] = compute_liquidation_score(
                p["avg_volume_usd"], p["market_value"]
            )

        # Régime portefeuille (simplifié sans equity curve historique)
        regime = detect_portfolio_regime(positions, [])

        return {
            "total_value": round(total_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl / total_value * 100, 2) if total_value else 0,
            "num_positions": len(positions),
            "positions": positions,
            "allocation": allocation_pct,
            "regime": regime,
        }

    def get_risk_parity(self) -> dict:
        """Calcule l'allocation Risk Parity optimale."""
        positions = self._get_positions_data()
        if len(positions) < 2:
            return {
                "status": "need_more_positions",
                "message": f"Minimum 2 positions requises ({len(positions)} actuellement)",
                "current_weights": {p["symbol"]: 1.0 for p in positions},
            }

        # Construire la matrice de covariance
        symbols = [p["symbol"] for p in positions]
        returns_data = {}
        for p in positions:
            asset = self.db.query(Asset).filter_by(symbol=p["symbol"]).first()
            if not asset:
                continue
            rows = (
                self.db.query(OHLCVDaily)
                .filter_by(asset_id=asset.id)
                .order_by(OHLCVDaily.date.desc())
                .limit(252)
                .all()
            )
            closes = pd.Series([float(r.close) for r in reversed(rows)])
            returns_data[p["symbol"]] = closes.pct_change().dropna()

        df = pd.DataFrame(returns_data).dropna()
        if len(df) < 20:
            return {"status": "insufficient_data", "message": "Pas assez de données communes"}

        cov_matrix = df.cov().values

        # Poids Risk Parity
        rp_weights = compute_risk_parity_weights(cov_matrix)
        portfolio_vol = compute_portfolio_volatility(rp_weights, cov_matrix)

        # Poids actuels (equal weight)
        total_value = sum(p["market_value"] for p in positions)
        current_weights = {p["symbol"]: round(p["market_value"] / total_value, 4) if total_value else 0 for p in positions}

        optimal_weights = {s: round(float(w), 4) for s, w in zip(symbols, rp_weights)}

        # Ajustements suggérés
        adjustments = []
        for s in symbols:
            current = current_weights.get(s, 0)
            optimal = optimal_weights.get(s, 0)
            diff = optimal - current
            if abs(diff) > 0.02:
                action = "INCREASE" if diff > 0 else "DECREASE"
                adjustments.append({
                    "symbol": s,
                    "current_weight": round(current * 100, 1),
                    "optimal_weight": round(optimal * 100, 1),
                    "action": action,
                    "diff_pct": round(diff * 100, 1),
                })

        return {
            "status": "ok",
            "current_weights": current_weights,
            "optimal_weights": optimal_weights,
            "portfolio_volatility": round(portfolio_vol * 100, 2),
            "adjustments": adjustments,
        }

    def run_stress_tests(self) -> list[dict]:
        """Exécute tous les scénarios de stress test."""
        positions = self._get_positions_data()
        if not positions:
            return [{"scenario": "N/A", "message": "Aucune position ouverte"}]

        results = []
        for key in STRESS_SCENARIOS:
            result = run_stress_test(positions, key)
            results.append(result)

        return results
