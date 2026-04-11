"""Module 4 — Exécution des Ordres : API endpoints"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.database.models import Asset, OHLCVDaily, Order, Position
from backend.database.models import OrderSide as DBOrderSide, OrderStatus as DBOrderStatus
from backend.database.models import SignalDirection, PositionStatus
from backend.modules.execution.order_engine import (
    create_scaling_orders, simulate_fill,
    ExecutionMode, OrderType, OrderSide,
)
from backend.modules.execution.bias_detector import run_full_bias_check
from backend.modules.execution.broker_alpaca import alpaca_broker
from backend.modules.scanner.live_data import is_alpaca_symbol

router = APIRouter()


@router.post("/execute/{symbol}")
def execute_trade(
    symbol: str,
    direction: str = Query("LONG"),
    capital: float = Query(100_000),
    db: Session = Depends(get_sync_db),
):
    """Exécute un trade rapidement (paper trading)."""
    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return {"symbol": symbol, "executed": False, "reason": "Actif non trouvé"}

    # Dernier prix
    last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
    if not last:
        return {"symbol": symbol, "executed": False, "reason": "Pas de données"}

    entry_price = float(last.close)

    # Récupérer les 10 derniers prix pour le bias check
    recent_rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(10).all()
    recent_prices = [float(r.close) for r in reversed(recent_rows)]

    # Bias check
    bias_check = run_full_bias_check([], entry_price=entry_price, recent_prices=recent_prices)
    if not bias_check["can_execute"]:
        return {
            "symbol": symbol,
            "executed": False,
            "reason": bias_check["message"],
            "bias_check": bias_check,
        }

    # Calculer SL/TP simples basés sur ATR
    import pandas as pd
    from backend.modules.scanner.indicators import atr
    rows_50 = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(50).all()
    highs = pd.Series([float(r.high) for r in reversed(rows_50)])
    lows = pd.Series([float(r.low) for r in reversed(rows_50)])
    closes = pd.Series([float(r.close) for r in reversed(rows_50)])
    atr_val = float(atr(highs, lows, closes, 14).iloc[-1])

    if direction == "LONG":
        stop_loss = round(entry_price - 2 * atr_val, 2)
        take_profit = round(entry_price + 3 * atr_val, 2)
        side = OrderSide.BUY
    else:
        stop_loss = round(entry_price + 2 * atr_val, 2)
        take_profit = round(entry_price - 3 * atr_val, 2)
        side = OrderSide.SELL

    # Sizing : 5% du capital
    position_size = capital * 0.05
    quantity = round(position_size / entry_price, 4)

    # Quantité entière pour Alpaca (pas de fractions pour les actions)
    if "-USD" not in symbol:
        quantity = max(1, int(quantity))

    # === ENVOI À ALPACA si le symbole est supporté ===
    alpaca_executed = False
    alpaca_result = None
    broker_used = "local_paper"

    if alpaca_broker.is_configured and is_alpaca_symbol(symbol):
        alpaca_side = "buy" if direction == "LONG" else "sell"
        alpaca_result = alpaca_broker.place_order(
            symbol=symbol,
            side=alpaca_side,
            quantity=float(quantity),
            order_type="market",
        )
        if alpaca_result and "error" not in alpaca_result:
            alpaca_executed = True
            broker_used = "alpaca_paper"

    # === Sauvegarde en BDD ===
    filled_price = entry_price
    db_order = Order(
        asset_id=asset.id,
        side=DBOrderSide.BUY if direction == "LONG" else DBOrderSide.SELL,
        quantity=float(quantity),
        price=entry_price,
        filled_price=filled_price,
        status=DBOrderStatus.FILLED,
        tranche=1,
        broker=broker_used,
        broker_order_id=alpaca_result.get("broker_order_id") if alpaca_result else None,
    )
    db.add(db_order)

    db_position = Position(
        asset_id=asset.id,
        direction=SignalDirection.LONG if direction == "LONG" else SignalDirection.SHORT,
        entry_price=filled_price,
        quantity=float(quantity),
        stop_loss=stop_loss,
        take_profit=take_profit,
        status=PositionStatus.OPEN,
    )
    db.add(db_position)
    db.commit()

    return {
        "symbol": symbol,
        "executed": True,
        "alpaca_executed": alpaca_executed,
        "broker": broker_used,
        "direction": direction,
        "entry_price": filled_price,
        "quantity": float(quantity),
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "position_size": round(position_size, 2),
        "bias_check": bias_check,
        "alpaca_order": alpaca_result,
    }


@router.post("/execute-all")
def execute_all(
    capital: float = Query(100_000),
    db: Session = Depends(get_sync_db),
):
    """Exécute tous les signaux GO (paper trading)."""
    # Utiliser le cache des signaux
    from backend.modules.scoring.router import _signals_cache

    signals = _signals_cache.get("data", [])
    if not signals:
        return {"total_signals": 0, "executed": 0, "skipped": 0, "results": [],
                "message": "Aucun signal en cache. Attendez que le scan se termine."}

    results = []
    remaining = capital

    for signal in signals:
        sym = signal.get("symbol", "")
        direction = signal.get("direction", "LONG")

        asset = db.query(Asset).filter_by(symbol=sym).first()
        if not asset:
            continue

        last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
        if not last:
            continue

        entry_price = float(last.close)
        recent_rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(10).all()
        recent_prices = [float(r.close) for r in reversed(recent_rows)]

        bias = run_full_bias_check([], entry_price=entry_price, recent_prices=recent_prices)
        if not bias["can_execute"]:
            results.append({"symbol": sym, "executed": False, "reason": bias["message"]})
            continue

        # Sizing 5% du remaining
        size = remaining * 0.05
        qty = round(size / entry_price, 4)

        import pandas as pd
        from backend.modules.scanner.indicators import atr
        rows_50 = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(50).all()
        h = pd.Series([float(r.high) for r in reversed(rows_50)])
        l = pd.Series([float(r.low) for r in reversed(rows_50)])
        c = pd.Series([float(r.close) for r in reversed(rows_50)])
        atr_val = float(atr(h, l, c, 14).iloc[-1])

        sl = round(entry_price - 2 * atr_val, 2) if direction == "LONG" else round(entry_price + 2 * atr_val, 2)
        tp = round(entry_price + 3 * atr_val, 2) if direction == "LONG" else round(entry_price - 3 * atr_val, 2)

        orders = create_scaling_orders(sym, OrderSide.BUY if direction == "LONG" else OrderSide.SELL, qty, entry_price, OrderType.MARKET)
        orders[0] = simulate_fill(orders[0], entry_price)

        if orders[0].status.value == "FILLED":
            db.add(Order(
                asset_id=asset.id,
                side=DBOrderSide.BUY if direction == "LONG" else DBOrderSide.SELL,
                quantity=float(orders[0].quantity),
                price=entry_price,
                filled_price=float(orders[0].filled_price),
                status=DBOrderStatus.FILLED, tranche=1, broker="paper",
            ))
            db.add(Position(
                asset_id=asset.id,
                direction=SignalDirection.LONG if direction == "LONG" else SignalDirection.SHORT,
                entry_price=float(orders[0].filled_price),
                quantity=float(orders[0].quantity),
                stop_loss=sl, take_profit=tp, status=PositionStatus.OPEN,
            ))
            db.commit()
            remaining -= size

        results.append({
            "symbol": sym, "executed": orders[0].status.value == "FILLED",
            "direction": direction, "entry_price": entry_price, "quantity": float(orders[0].quantity),
        })

    executed = [r for r in results if r.get("executed")]
    return {
        "total_signals": len(signals),
        "executed": len(executed),
        "skipped": len(results) - len(executed),
        "capital_deployed": round(capital - remaining, 2),
        "capital_remaining": round(remaining, 2),
        "results": results,
    }


@router.get("/positions")
def list_positions(db: Session = Depends(get_sync_db)):
    """Positions ouvertes."""
    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    result = []
    for p in positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first() if asset else None
        current = float(last.close) if last else float(p.entry_price)
        pnl = (current - p.entry_price) * p.quantity if p.direction == SignalDirection.LONG else (p.entry_price - current) * p.quantity
        pnl_pct = (current / p.entry_price - 1) * 100 if p.direction == SignalDirection.LONG else (1 - current / p.entry_price) * 100

        result.append({
            "id": p.id, "symbol": asset.symbol if asset else "?", "name": asset.name if asset else "?",
            "direction": p.direction.value, "entry_price": float(p.entry_price), "current_price": current,
            "quantity": float(p.quantity), "stop_loss": float(p.stop_loss), "take_profit": float(p.take_profit),
            "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2), "status": p.status.value,
            "opened_at": p.opened_at.isoformat() if p.opened_at else None,
        })
    return result


@router.get("/orders")
def list_orders(db: Session = Depends(get_sync_db)):
    """Ordres récents."""
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(50).all()
    result = []
    for o in orders:
        asset = db.query(Asset).filter_by(id=o.asset_id).first()
        result.append({
            "id": o.id, "symbol": asset.symbol if asset else "?", "side": o.side.value,
            "quantity": float(o.quantity), "price": float(o.price) if o.price else None,
            "filled_price": float(o.filled_price) if o.filled_price else None,
            "status": o.status.value, "tranche": o.tranche, "broker": o.broker,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        })
    return result


@router.get("/bias-check")
def check_bias():
    return run_full_bias_check([], entry_price=0, recent_prices=[])
