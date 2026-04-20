"""Module 4 — Exécution des Ordres : Logique métier

Orchestre :
1. Vérification biais comportementaux (pré-exécution)
2. Création des ordres avec scaling 3 tranches
3. Simulation d'exécution (paper trading)
4. Gestion dynamique des positions ouvertes
"""

import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily, Order, Position
from backend.database.models import OrderSide as DBOrderSide, OrderStatus as DBOrderStatus
from backend.database.models import SignalDirection, PositionStatus
from backend.modules.scoring.service import ScoringService
from backend.modules.execution.order_engine import (
    create_scaling_orders, simulate_fill,
    ExecutionMode, OrderType, OrderSide, ExecutionOrder,
)
from backend.modules.execution.position_manager import ActivePosition
from backend.modules.execution.bias_detector import run_full_bias_check


class ExecutionService:
    """Gère l'exécution des ordres et le suivi des positions."""

    def __init__(self, db: Session):
        self.db = db
        self.scoring = ScoringService(db)
        # Positions actives en mémoire (paper trading)
        self._active_positions: dict[str, ActivePosition] = {}
        # Historique des trades pour la détection de biais
        self._trade_history: list[dict] = []

    def _get_last_price(self, symbol: str) -> float | None:
        asset = self.db.query(Asset).filter_by(symbol=symbol).first()
        if not asset:
            return None
        last = (
            self.db.query(OHLCVDaily)
            .filter_by(asset_id=asset.id)
            .order_by(OHLCVDaily.date.desc())
            .first()
        )
        return float(last.close) if last else None

    def _get_recent_prices(self, symbol: str, n: int = 10) -> list[float]:
        asset = self.db.query(Asset).filter_by(symbol=symbol).first()
        if not asset:
            return []
        rows = (
            self.db.query(OHLCVDaily)
            .filter_by(asset_id=asset.id)
            .order_by(OHLCVDaily.date.desc())
            .limit(n)
            .all()
        )
        return [float(r.close) for r in reversed(rows)]

    def execute_thesis(self, symbol: str, capital: float = 100_000) -> dict:
        """Exécute une thèse de trade : biais check → ordres → fill."""
        # 0a. Vérifier si une position est déjà ouverte sur cet actif
        asset = self.db.query(Asset).filter_by(symbol=symbol).first()
        if asset:
            existing = (
                self.db.query(Position)
                .filter_by(asset_id=asset.id, status=PositionStatus.OPEN)
                .first()
            )
            if existing:
                return {
                    "symbol": symbol,
                    "executed": False,
                    "reason": f"Position déjà ouverte sur {symbol} (id={existing.id})",
                }

            # 0b. Cooldown — pas de nouveau trade si fermé dans les dernières 24h
            from datetime import datetime, timedelta
            recent_close = (
                self.db.query(Position)
                .filter_by(asset_id=asset.id, status=PositionStatus.CLOSED)
                .filter(Position.closed_at >= datetime.utcnow() - timedelta(hours=24))
                .first()
            )
            if recent_close:
                return {
                    "symbol": symbol,
                    "executed": False,
                    "reason": f"Cooldown 24h — {symbol} fermé récemment (id={recent_close.id})",
                }

        # 1. Générer la thèse
        thesis = self.scoring.generate_thesis(symbol, capital)
        if "error" in thesis:
            return thesis
        if thesis["action"] != "GO":
            return {
                "symbol": symbol,
                "executed": False,
                "reason": f"Action = {thesis['action']} (score {thesis['thesis_score']:.1f})",
            }

        # 2. Vérifier les biais
        recent_prices = self._get_recent_prices(symbol)
        bias_check = run_full_bias_check(
            self._trade_history,
            entry_price=thesis["entry"],
            recent_prices=recent_prices,
        )

        if not bias_check["can_execute"]:
            return {
                "symbol": symbol,
                "executed": False,
                "reason": bias_check["message"],
                "bias_check": bias_check,
            }

        # 3. Créer les ordres scaling
        side = OrderSide.BUY if thesis["direction"] == "LONG" else OrderSide.SELL
        order_type_str = thesis["shelf_life"]["order_type"]
        order_type = OrderType.LIMIT if order_type_str == "LIMIT" else OrderType.MARKET

        orders = create_scaling_orders(
            symbol=symbol,
            side=side,
            total_quantity=thesis["sizing"]["quantity"],
            entry_price=thesis["entry"],
            order_type=order_type,
        )

        # 4. Simuler le fill (tranche 1 immédiate)
        current_price = self._get_last_price(symbol) or thesis["entry"]
        orders[0] = simulate_fill(orders[0], current_price)

        # 5. Créer la position active
        if orders[0].status.value == "FILLED":
            position = ActivePosition(
                symbol=symbol,
                direction=thesis["direction"],
                entry_price=orders[0].filled_price,
                current_price=current_price,
                quantity=orders[0].quantity,
                stop_loss=thesis["stop_loss"],
                take_profit=thesis["take_profit_1"],
            )
            self._active_positions[symbol] = position

        # 6. Sauvegarder en BDD
        asset = self.db.query(Asset).filter_by(symbol=symbol).first()
        if asset and orders[0].status.value == "FILLED":
            db_order = Order(
                asset_id=asset.id,
                side=DBOrderSide.BUY if side == OrderSide.BUY else DBOrderSide.SELL,
                quantity=float(orders[0].quantity),
                price=float(thesis["entry"]),
                filled_price=float(orders[0].filled_price),
                status=DBOrderStatus.FILLED,
                tranche=1,
                broker="paper",
            )
            self.db.add(db_order)

            db_position = Position(
                asset_id=asset.id,
                direction=SignalDirection.LONG if thesis["direction"] == "LONG" else SignalDirection.SHORT,
                entry_price=float(orders[0].filled_price),
                quantity=float(orders[0].quantity),
                stop_loss=float(thesis["stop_loss"]),
                take_profit=float(thesis["take_profit_1"]),
                status=PositionStatus.OPEN,
            )
            self.db.add(db_position)
            self.db.commit()

        return {
            "symbol": symbol,
            "executed": orders[0].status.value == "FILLED",
            "thesis_score": thesis["thesis_score"],
            "direction": thesis["direction"],
            "strategy": thesis["strategy"],
            "orders": [o.to_dict() for o in orders],
            "bias_check": bias_check,
            "sizing": thesis["sizing"],
            "position": position.to_dict() if orders[0].status.value == "FILLED" else None,
        }

    def execute_all_signals(self, capital: float = 100_000) -> dict:
        """Exécute toutes les thèses GO."""
        signals = self.scoring.get_active_signals(capital)
        results = []
        remaining_capital = capital

        for signal in signals:
            if remaining_capital <= 0:
                break
            result = self.execute_thesis(signal["symbol"], remaining_capital)
            results.append(result)
            if result.get("executed") and result.get("sizing"):
                remaining_capital -= result["sizing"]["position_size_usd"]

        executed = [r for r in results if r.get("executed")]
        return {
            "total_signals": len(signals),
            "executed": len(executed),
            "skipped": len(results) - len(executed),
            "capital_deployed": round(capital - remaining_capital, 2),
            "capital_remaining": round(remaining_capital, 2),
            "results": results,
        }

    def get_positions(self) -> list[dict]:
        """Liste les positions ouvertes."""
        positions = (
            self.db.query(Position)
            .filter_by(status=PositionStatus.OPEN)
            .all()
        )
        result = []
        for p in positions:
            asset = self.db.query(Asset).filter_by(id=p.asset_id).first()
            last_price = self._get_last_price(asset.symbol) if asset else None
            pnl = 0
            pnl_pct = 0
            if last_price and p.entry_price:
                if p.direction == SignalDirection.LONG:
                    pnl = (last_price - p.entry_price) * p.quantity
                    pnl_pct = (last_price / p.entry_price - 1) * 100
                else:
                    pnl = (p.entry_price - last_price) * p.quantity
                    pnl_pct = (1 - last_price / p.entry_price) * 100

            result.append({
                "id": p.id,
                "symbol": asset.symbol if asset else "?",
                "name": asset.name if asset else "?",
                "direction": p.direction.value,
                "entry_price": p.entry_price,
                "current_price": last_price,
                "quantity": p.quantity,
                "stop_loss": p.stop_loss,
                "take_profit": p.take_profit,
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "status": p.status.value,
                "opened_at": p.opened_at.isoformat() if p.opened_at else None,
            })

        return result

    def get_orders(self) -> list[dict]:
        """Liste les ordres récents."""
        orders = (
            self.db.query(Order)
            .order_by(Order.created_at.desc())
            .limit(50)
            .all()
        )
        result = []
        for o in orders:
            asset = self.db.query(Asset).filter_by(id=o.asset_id).first()
            result.append({
                "id": o.id,
                "symbol": asset.symbol if asset else "?",
                "side": o.side.value,
                "quantity": o.quantity,
                "price": o.price,
                "filled_price": o.filled_price,
                "status": o.status.value,
                "tranche": o.tranche,
                "broker": o.broker,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            })

        return result
