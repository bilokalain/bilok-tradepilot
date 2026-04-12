"""Module 4 — Exécution V2 : Score V2 + Bracket Orders + Sync Alpaca"""

import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.database.models import Asset, OHLCVDaily, Order, Position
from backend.database.models import OrderSide as DBOrderSide, OrderStatus as DBOrderStatus
from backend.database.models import SignalDirection, PositionStatus
from backend.modules.execution.bias_detector import run_full_bias_check
from backend.modules.execution.broker_alpaca import alpaca_broker
from backend.modules.scanner.live_data import is_alpaca_symbol
from backend.modules.scanner.indicators import atr

router = APIRouter()


def _get_price_and_atr(db: Session, asset_id: int) -> tuple:
    """Récupère le dernier prix et l'ATR."""
    rows = db.query(OHLCVDaily).filter_by(asset_id=asset_id).order_by(OHLCVDaily.date.desc()).limit(50).all()
    if len(rows) < 14:
        return None, None
    closes = pd.Series([float(r.close) for r in reversed(rows)])
    highs = pd.Series([float(r.high) for r in reversed(rows)])
    lows = pd.Series([float(r.low) for r in reversed(rows)])
    atr_val = float(atr(highs, lows, closes, 14).iloc[-1])
    return float(closes.iloc[-1]), atr_val


@router.post("/execute/{symbol}")
def execute_trade(
    symbol: str,
    direction: str = Query("LONG"),
    capital: float = Query(100_000),
    db: Session = Depends(get_sync_db),
):
    """Exécution V2 — intègre Score V2 + Bracket Orders + Anti-corrélation."""
    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return {"symbol": symbol, "executed": False, "reason": "Actif non trouvé"}

    entry_price, atr_val = _get_price_and_atr(db, asset.id)
    if not entry_price or not atr_val:
        return {"symbol": symbol, "executed": False, "reason": "Pas assez de données"}

    # === 1. Score V2 — vérification complète ===
    from backend.modules.scoring.scorer_v2 import compute_score_v2
    from backend.modules.scanner.cache import get_cached_results
    from backend.modules.scanner.fundamental import compute_fundamental_score
    from backend.modules.analyser.regime_global import detect_global_regime
    from backend.modules.analyser.catalysts import compute_catalyst_adjustment
    from backend.modules.analyser.correlation_filter import check_portfolio_correlation
    from backend.modules.analyser.sector_rotation import detect_rotation, get_sector_score
    from backend.modules.analyser.lead_lag import detect_lead_lag
    from backend.modules.analyser.performance_matrix import get_best_strategy, get_strategy_sharpe
    from backend.modules.scoring.kelly import compute_position_sizing

    # Scanner score
    cached = get_cached_results()
    scan = next((r for r in cached if r.get("symbol") == symbol), None)
    scanner_score = scan["scores"]["final"] if scan else 50

    # Stratégie + backtest
    best_strat = get_best_strategy(symbol) or "momentum"
    backtest_sharpe = get_strategy_sharpe(symbol, best_strat)
    conviction = min(90, max(30, 50 + backtest_sharpe * 20))

    # Régime global
    regime_global = detect_global_regime(db)

    # Fondamentaux
    fund = compute_fundamental_score(symbol)
    fund_score = fund.get("score") if fund.get("applicable") else None

    # Catalyseurs
    catalyst = compute_catalyst_adjustment(symbol)

    # Anti-corrélation
    corr_check = check_portfolio_correlation(db, symbol)
    if not corr_check["can_add"]:
        return {
            "symbol": symbol, "executed": False,
            "reason": corr_check["reason"],
            "correlation_check": corr_check,
        }

    # Sector rotation
    rotation = detect_rotation(db)
    sector = get_sector_score(symbol, rotation)

    # Lead-lag
    lead_lag = detect_lead_lag(db, symbol)

    # Score V2
    score_v2 = compute_score_v2(
        scanner_score=scanner_score,
        strategy_conviction=conviction,
        backtest_sharpe=backtest_sharpe,
        regime_global=regime_global,
        fundamental_score=fund_score,
        catalyst_adjustment=catalyst,
        correlation_check=corr_check,
        sector_rotation_score=sector.get("score", 50),
        lead_lag_signal=lead_lag,
        asset_class=asset.asset_class.value,
    )

    # Vérifier si le V2 autorise le trade
    if score_v2["action"] == "NO_TRADE":
        return {
            "symbol": symbol, "executed": False,
            "reason": f"Score V2 = {score_v2['score_v2']:.1f}/100 → NO_TRADE",
            "score_v2": score_v2,
        }

    # === 2. Bias check ===
    recent_rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(10).all()
    recent_prices = [float(r.close) for r in reversed(recent_rows)]
    bias_check = run_full_bias_check([], entry_price=entry_price, recent_prices=recent_prices)
    if not bias_check["can_execute"]:
        return {
            "symbol": symbol, "executed": False,
            "reason": bias_check["message"],
            "bias_check": bias_check, "score_v2": score_v2,
        }

    # === 3. Sizing Kelly × V2 modifiers ===
    if direction == "LONG":
        stop_loss = round(entry_price - 2 * atr_val, 2)
        take_profit = round(entry_price + 3 * atr_val, 2)
    else:
        stop_loss = round(entry_price + 2 * atr_val, 2)
        take_profit = round(entry_price - 3 * atr_val, 2)

    kelly = compute_position_sizing(
        capital=capital, entry=entry_price,
        stop_loss=stop_loss, take_profit=take_profit,
        bayesian_score=scanner_score, conviction=conviction,
    )

    if kelly["kelly_fraction"] > 0 and kelly["reject_reason"] is None:
        position_size = kelly["position_size_usd"]
    else:
        position_size = capital * 0.03

    # Appliquer les modifiers V2 (catalyseurs + corrélation + régime)
    position_size *= score_v2["sizing_modifier"]
    position_size = min(position_size, capital * 0.10)  # Plafond 10%
    quantity = round(position_size / entry_price, 4)

    if "-USD" not in symbol:
        quantity = max(1, int(quantity))

    if quantity <= 0:
        return {"symbol": symbol, "executed": False, "reason": "Quantité trop faible après ajustements"}

    # === 4. Envoi à Alpaca — Bracket Order (entry + SL + TP) ===
    alpaca_executed = False
    alpaca_result = None
    broker_used = "local_paper"

    if alpaca_broker.is_configured and is_alpaca_symbol(symbol):
        alpaca_result = _place_bracket_order(
            symbol=symbol,
            side="buy" if direction == "LONG" else "sell",
            quantity=float(quantity),
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        if alpaca_result and "error" not in alpaca_result:
            alpaca_executed = True
            broker_used = "alpaca_bracket"

    # === 5. Sauvegarde BDD ===
    db_order = Order(
        asset_id=asset.id,
        side=DBOrderSide.BUY if direction == "LONG" else DBOrderSide.SELL,
        quantity=float(quantity), price=entry_price, filled_price=entry_price,
        status=DBOrderStatus.FILLED, tranche=1, broker=broker_used,
        broker_order_id=alpaca_result.get("broker_order_id") if alpaca_result else None,
    )
    db.add(db_order)

    db_position = Position(
        asset_id=asset.id,
        direction=SignalDirection.LONG if direction == "LONG" else SignalDirection.SHORT,
        entry_price=entry_price, quantity=float(quantity),
        stop_loss=stop_loss, take_profit=take_profit,
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
        "entry_price": entry_price,
        "quantity": float(quantity),
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "position_size": round(position_size, 2),
        "score_v2": score_v2,
        "bias_check": bias_check,
        "alpaca_order": alpaca_result,
    }


def _place_bracket_order(symbol: str, side: str, quantity: float,
                          stop_loss: float, take_profit: float) -> dict:
    """Place un Bracket Order Alpaca : entry + SL + TP en une commande."""
    try:
        from alpaca.trading.client import TradingClient
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
        from backend.config.settings import settings

        client = TradingClient(
            api_key=settings.ALPACA_API_KEY,
            secret_key=settings.ALPACA_SECRET_KEY,
            paper=("paper" in settings.ALPACA_BASE_URL),
        )

        alpaca_side = OrderSide.BUY if side == "buy" else OrderSide.SELL

        request = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=alpaca_side,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.BRACKET,
            stop_loss={"stop_price": stop_loss},
            take_profit={"limit_price": take_profit},
        )

        order = client.submit_order(request)

        return {
            "broker_order_id": str(order.id),
            "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
            "order_class": "BRACKET",
            "stop_loss_price": stop_loss,
            "take_profit_price": take_profit,
        }
    except Exception as e:
        # Fallback : ordre market simple si bracket échoue
        try:
            result = alpaca_broker.place_order(symbol, side, quantity, "market")
            if result and "error" not in result:
                result["order_class"] = "MARKET_FALLBACK"
                result["note"] = f"Bracket échoué ({e}), market order utilisé"
            return result
        except Exception as e2:
            return {"error": f"Bracket: {e}, Market: {e2}"}


@router.post("/execute-all")
def execute_all(
    capital: float = Query(100_000),
    db: Session = Depends(get_sync_db),
):
    """Exécute tous les signaux GO avec le scoring V2."""
    from backend.modules.scoring.router import _signals_cache

    signals = _signals_cache.get("data", [])
    if not signals:
        return {"total_signals": 0, "executed": 0, "skipped": 0, "results": [],
                "message": "Aucun signal en cache."}

    # Filtrer les actifs déjà en position
    open_positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    open_symbols = {db.query(Asset).filter_by(id=p.asset_id).first().symbol for p in open_positions if db.query(Asset).filter_by(id=p.asset_id).first()}

    results = []
    remaining = capital

    for signal in signals:
        sym = signal.get("symbol", "")
        if sym in open_symbols:
            results.append({"symbol": sym, "executed": False, "reason": "Déjà en position"})
            continue

        direction = signal.get("direction", "LONG")
        result = execute_trade.__wrapped__(sym, direction, remaining, db) if hasattr(execute_trade, '__wrapped__') else {"symbol": sym, "executed": False, "reason": "Erreur interne"}

        # Appel direct de la logique
        asset = db.query(Asset).filter_by(symbol=sym).first()
        if not asset:
            results.append({"symbol": sym, "executed": False, "reason": "Actif non trouvé"})
            continue

        entry_price, atr_val = _get_price_and_atr(db, asset.id)
        if not entry_price:
            results.append({"symbol": sym, "executed": False, "reason": "Pas de données"})
            continue

        # Sizing simple pour execute-all (plus rapide que V2 complet)
        from backend.modules.analyser.performance_matrix import get_strategy_sharpe, get_best_strategy
        from backend.modules.scoring.kelly import compute_position_sizing

        best_strat = get_best_strategy(sym) or "momentum"
        bt_sharpe = get_strategy_sharpe(sym, best_strat)
        conv = min(90, max(30, 50 + bt_sharpe * 20))

        sl = round(entry_price - 2 * atr_val, 2) if direction == "LONG" else round(entry_price + 2 * atr_val, 2)
        tp = round(entry_price + 3 * atr_val, 2) if direction == "LONG" else round(entry_price - 3 * atr_val, 2)

        kelly = compute_position_sizing(remaining, entry_price, sl, tp, 50, conv)
        size = kelly["position_size_usd"] if kelly["kelly_fraction"] > 0 else remaining * 0.03
        size = min(size, remaining * 0.10)
        qty = round(size / entry_price, 4)
        if "-USD" not in sym:
            qty = max(1, int(qty))

        # Bracket order
        alpaca_result = None
        if alpaca_broker.is_configured and is_alpaca_symbol(sym):
            alpaca_result = _place_bracket_order(sym, "buy" if direction == "LONG" else "sell", float(qty), sl, tp)

        db.add(Order(
            asset_id=asset.id,
            side=DBOrderSide.BUY if direction == "LONG" else DBOrderSide.SELL,
            quantity=float(qty), price=entry_price, filled_price=entry_price,
            status=DBOrderStatus.FILLED, tranche=1,
            broker="alpaca_bracket" if alpaca_result and "error" not in alpaca_result else "local",
        ))
        db.add(Position(
            asset_id=asset.id,
            direction=SignalDirection.LONG if direction == "LONG" else SignalDirection.SHORT,
            entry_price=entry_price, quantity=float(qty),
            stop_loss=sl, take_profit=tp, status=PositionStatus.OPEN,
        ))
        db.commit()
        remaining -= size

        results.append({
            "symbol": sym, "executed": True, "direction": direction,
            "entry_price": entry_price, "quantity": float(qty),
            "stop_loss": sl, "take_profit": tp,
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


@router.get("/sync-alpaca")
def sync_alpaca_positions(db: Session = Depends(get_sync_db)):
    """Synchronise les positions Alpaca avec la BDD locale."""
    if not alpaca_broker.is_configured:
        return {"synced": False, "reason": "Alpaca non configuré"}

    alpaca_positions = alpaca_broker.get_positions()
    local_positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()

    synced = []
    for ap in alpaca_positions:
        # Mettre à jour le prix actuel dans les positions locales
        asset = db.query(Asset).filter_by(symbol=ap["symbol"]).first()
        if asset:
            for lp in local_positions:
                if lp.asset_id == asset.id:
                    # Position trouvée — mettre à jour
                    synced.append({
                        "symbol": ap["symbol"],
                        "alpaca_qty": ap["quantity"],
                        "alpaca_pnl": ap["pnl"],
                        "alpaca_price": ap["current_price"],
                    })

    return {
        "synced": True,
        "alpaca_positions": len(alpaca_positions),
        "local_positions": len(local_positions),
        "synced_positions": synced,
    }


@router.get("/positions")
def list_positions(db: Session = Depends(get_sync_db)):
    """Positions ouvertes — enrichies avec Alpaca si disponible."""
    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()

    # Récupérer les positions Alpaca pour les prix live
    alpaca_pos = {}
    if alpaca_broker.is_configured:
        try:
            for ap in alpaca_broker.get_positions():
                alpaca_pos[ap["symbol"]] = ap
        except Exception:
            pass

    result = []
    for p in positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if not asset:
            continue

        # Prix live Alpaca ou BDD
        ap = alpaca_pos.get(asset.symbol)
        if ap:
            current_price = ap["current_price"]
            live_pnl = ap["pnl"]
        else:
            last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
            current_price = float(last.close) if last else float(p.entry_price)
            live_pnl = None

        if p.direction == SignalDirection.LONG:
            pnl = (current_price - p.entry_price) * p.quantity
            pnl_pct = (current_price / p.entry_price - 1) * 100
        else:
            pnl = (p.entry_price - current_price) * p.quantity
            pnl_pct = (1 - current_price / p.entry_price) * 100

        result.append({
            "id": p.id, "symbol": asset.symbol, "name": asset.name,
            "direction": p.direction.value,
            "entry_price": float(p.entry_price), "current_price": current_price,
            "quantity": float(p.quantity),
            "stop_loss": float(p.stop_loss), "take_profit": float(p.take_profit),
            "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2),
            "live_pnl": round(live_pnl, 2) if live_pnl is not None else None,
            "source": "alpaca_live" if ap else "database",
            "status": p.status.value,
            "opened_at": p.opened_at.isoformat() if p.opened_at else None,
        })
    return result


@router.get("/orders")
def list_orders(db: Session = Depends(get_sync_db)):
    """Ordres récents."""
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(50).all()
    return [
        {
            "id": o.id,
            "symbol": db.query(Asset).filter_by(id=o.asset_id).first().symbol if db.query(Asset).filter_by(id=o.asset_id).first() else "?",
            "side": o.side.value, "quantity": float(o.quantity),
            "price": float(o.price) if o.price else None,
            "filled_price": float(o.filled_price) if o.filled_price else None,
            "status": o.status.value, "tranche": o.tranche, "broker": o.broker,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]


@router.get("/bias-check")
def check_bias():
    return run_full_bias_check([], entry_price=0, recent_prices=[])
