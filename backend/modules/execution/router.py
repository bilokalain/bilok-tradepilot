"""Module 4 — Exécution V2 : Score V2 + Bracket Orders + Sync Alpaca"""

import logging
import pandas as pd

logger = logging.getLogger("tradepilot.execution")
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


def _place_bracket_order(symbol: str, side: str, quantity: float,
                          stop_loss: float, take_profit: float) -> dict:
    """Place un Bracket Order Alpaca : entry + SL + TP en une commande.

    Même si le Mac s'éteint, Alpaca exécutera le SL et TP automatiquement.
    """
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
            time_in_force=TimeInForce.GTC,
            order_class=OrderClass.BRACKET,
            stop_loss={"stop_price": stop_loss},
            take_profit={"limit_price": take_profit},
        )

        order = client.submit_order(request)
        logger.info(f"[BRACKET] {side} {quantity} {symbol} SL=${stop_loss} TP=${take_profit} → {order.id}")

        return {
            "broker_order_id": str(order.id),
            "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
            "order_class": "BRACKET",
            "stop_loss_price": stop_loss,
            "take_profit_price": take_profit,
        }
    except Exception as e:
        logger.warning(f"[BRACKET] Erreur {symbol}: {e}")
        # Fallback : ordre market simple
        try:
            result = alpaca_broker.place_order(symbol, side, quantity, "market")
            if result and "error" not in result:
                logger.warning(f"[BRACKET] Fallback market pour {symbol}")
                return result
        except Exception as e:
            logger.error(f"[BRACKET] Fallback market aussi échoué pour {symbol}: {e}")
        return {"error": str(e)}


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

    # === 0. Vérifier max positions ===
    from backend.modules.execution.position_manager_v2 import can_open_position, add_to_queue
    if not can_open_position(db):
        add_to_queue({"symbol": symbol, "direction": direction, "score": 50})
        return {
            "symbol": symbol, "executed": False,
            "reason": "Maximum 10 positions atteint — ajouté à la file d'attente",
            "queued": True,
        }

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

    kelly_size = kelly["position_size_usd"] if kelly["kelly_fraction"] > 0 and kelly["reject_reason"] is None else None

    from backend.modules.execution.sizing import compute_position_size, quantize
    sizing = compute_position_size(
        capital=capital, entry_price=entry_price,
        score=score_v2["score_v2"], kelly_size=kelly_size,
        sizing_modifier=score_v2["sizing_modifier"],
    )
    position_size = sizing["position_size"]
    quantity = quantize(sizing["quantity"], symbol)

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

    # Filtrer les actifs déjà en position RÉELLE (Alpaca + IBKR uniquement, pas les locaux)
    open_symbols = set()
    if alpaca_broker.is_configured:
        try:
            for p in alpaca_broker.get_positions():
                open_symbols.add(p["symbol"])
        except Exception as e:
            logger.warning(f"[EXEC] Impossible de récupérer les positions Alpaca: {e}")
    # IBKR aussi
    try:
        from backend.config.settings import settings as _s
        if _s.IBKR_ACCOUNT_ID:
            import concurrent.futures as _cf, asyncio as _aio
            def _get_ibkr_syms():
                loop = _aio.new_event_loop()
                _aio.set_event_loop(loop)
                from ib_insync import IB
                ib = IB()
                ib.connect(_s.IBKR_HOST, _s.IBKR_PORT, clientId=70, timeout=10)
                syms = {p.contract.symbol for p in ib.positions(_s.IBKR_ACCOUNT_ID) if p.position != 0}
                ib.disconnect()
                loop.close()
                return syms
            try:
                with _cf.ThreadPoolExecutor() as ex:
                    open_symbols.update(ex.submit(_get_ibkr_syms).result(timeout=15))
            except Exception as e:
                logger.warning(f"[EXEC] IBKR symbols fetch échoué: {e}")
    except Exception as e:
        logger.warning(f"[EXEC] IBKR config check échoué: {e}")

    results = []
    remaining = capital

    # Mapping position ouverte → direction
    open_positions_map = {}
    for p in open_positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if asset:
            open_positions_map[asset.symbol] = p.direction.value

    for signal in signals:
        sym = signal.get("symbol", "")
        direction = signal.get("direction", "LONG")

        if sym in open_symbols:
            current_dir = open_positions_map.get(sym, "LONG")
            if current_dir == direction:
                results.append({"symbol": sym, "executed": False, "reason": "Déjà en position"})
                continue
            # Direction opposée → fermer la position existante et ouvrir la nouvelle
            try:
                if alpaca_broker.is_configured and is_alpaca_symbol(sym):
                    alpaca_broker.close_position(sym)
                # Fermer en BDD
                asset_to_close = db.query(Asset).filter_by(symbol=sym).first()
                if asset_to_close:
                    from datetime import datetime
                    for pos in db.query(Position).filter_by(asset_id=asset_to_close.id, status=PositionStatus.OPEN).all():
                        pos.status = PositionStatus.CLOSED
                        pos.closed_at = datetime.utcnow()
                    db.commit()
                open_symbols.discard(sym)
                logger.info(f"[EXEC] {sym} retourné: {current_dir} → {direction}")
            except Exception as e:
                results.append({"symbol": sym, "executed": False, "reason": f"Erreur fermeture: {e}"})
                continue
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

        # Sizing centralisé
        signal_score = signal.get("score", signal.get("thesis_score", 50))
        kelly = compute_position_sizing(remaining, entry_price, sl, tp, 50, conv)
        kelly_size = kelly["position_size_usd"] if kelly["kelly_fraction"] > 0 else None

        from backend.modules.execution.sizing import compute_position_size, quantize
        sizing = compute_position_size(
            capital=remaining, entry_price=entry_price,
            score=signal_score, kelly_size=kelly_size,
        )
        size = sizing["position_size"]
        qty = quantize(sizing["quantity"], sym)

        # Bracket order
        alpaca_result = None
        if alpaca_broker.is_configured and is_alpaca_symbol(sym):
            alpaca_result = _place_bracket_order(sym, "buy" if direction == "LONG" else "sell", float(qty), sl, tp)

        # Enregistrer en BDD UNIQUEMENT si envoyé à un broker réel
        broker_used = None
        if alpaca_result and "error" not in alpaca_result:
            broker_used = "alpaca_bracket"

        if broker_used:
            db.add(Order(
                asset_id=asset.id,
                side=DBOrderSide.BUY if direction == "LONG" else DBOrderSide.SELL,
                quantity=float(qty), price=entry_price, filled_price=entry_price,
                status=DBOrderStatus.FILLED, tranche=1,
                broker=broker_used,
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
        except Exception as e:
            logger.warning(f"[POSITIONS] Impossible de récupérer les positions Alpaca: {e}")

    # Identifier les positions IBKR via les ordres
    from backend.database.models import Order as OrderModel
    ibkr_asset_ids = set()
    for o in db.query(OrderModel).filter_by(broker="ibkr").all():
        ibkr_asset_ids.add(o.asset_id)

    result = []
    for p in positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if not asset:
            continue

        # Déterminer la source : ibkr > alpaca_live > database
        is_ibkr = p.asset_id in ibkr_asset_ids and float(p.quantity) <= 50  # IBKR = petites qty réelles
        ap = alpaca_pos.get(asset.symbol)

        # Prix : Alpaca live si disponible (avec validation), sinon BDD
        if ap and not is_ibkr:
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

        if is_ibkr:
            source = "ibkr_live"
        elif ap:
            source = "alpaca_live"
        else:
            source = "database"

        result.append({
            "id": p.id, "symbol": asset.symbol, "name": asset.name,
            "direction": p.direction.value,
            "entry_price": float(p.entry_price), "current_price": current_price,
            "quantity": float(p.quantity),
            "stop_loss": float(p.stop_loss) if p.stop_loss else 0,
            "take_profit": float(p.take_profit) if p.take_profit else 0,
            "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2),
            "live_pnl": round(live_pnl, 2) if live_pnl is not None else None,
            "source": source,
            "status": p.status.value,
            "opened_at": p.opened_at.isoformat() if p.opened_at else None,
        })

    # Les positions IBKR sont déjà synchronisées en BDD.
    # Le TP/SL monitor met à jour les prix toutes les 5 min.
    # Pas de connexion IBKR live ici — ça bloque la page (timeout 15s+ par position).

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


@router.get("/queue")
def get_signal_queue():
    """File d'attente des signaux en attente d'exécution."""
    from backend.modules.execution.position_manager_v2 import get_queue, MAX_POSITIONS, count_open_positions
    from backend.database.sync_session import get_sync_db
    db = next(get_sync_db())
    try:
        return {
            "queue": get_queue(),
            "queue_size": len(get_queue()),
            "open_positions": count_open_positions(db),
            "max_positions": MAX_POSITIONS,
            "slots_available": MAX_POSITIONS - count_open_positions(db),
        }
    finally:
        db.close()


@router.post("/close/{symbol}")
def close_position_endpoint(symbol: str, db: Session = Depends(get_sync_db)):
    """Ferme une position chez le broker ET en BDD."""
    results = {}

    # 1. Fermer chez Alpaca (annuler les ordres ouverts d'abord)
    if alpaca_broker.is_configured:
        try:
            # Annuler les ordres ouverts qui bloquent les actions
            open_orders = alpaca_broker.get_orders(status="open")
            for o in open_orders:
                if o["symbol"] == symbol:
                    alpaca_broker.cancel_order(o["id"])
            # Fermer la position
            alpaca_result = alpaca_broker.close_position(symbol)
            results["alpaca"] = alpaca_result
        except Exception as e:
            results["alpaca"] = {"error": str(e)}

    # 2. Fermer chez IBKR si configuré
    try:
        from backend.modules.execution.broker_ibkr import ibkr_broker
        if ibkr_broker.is_configured:
            try:
                ibkr_result = ibkr_broker.close_position(symbol)
                results["ibkr"] = ibkr_result
            except Exception as e:
                results["ibkr"] = {"error": str(e)}
    except Exception as e:
        logger.warning(f"[CLOSE] IBKR import/check échoué pour {symbol}: {e}")

    # 3. Fermer en BDD
    from datetime import datetime
    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if asset:
        open_positions = db.query(Position).filter_by(
            asset_id=asset.id, status=PositionStatus.OPEN
        ).all()
        for p in open_positions:
            p.status = PositionStatus.CLOSED
            p.closed_at = datetime.utcnow()
            # Récupérer le prix actuel pour le P&L
            try:
                if alpaca_broker.is_configured:
                    price = alpaca_broker.get_last_price(symbol)
                    if price:
                        p.exit_price = price
            except Exception as e:
                logger.warning(f"[CLOSE] Impossible de récupérer le prix de sortie pour {symbol}: {e}")
        db.commit()
        results["db_closed"] = len(open_positions)

    return {"status": "closed", "symbol": symbol, "results": results}


@router.get("/health-check")
def positions_health_check(db: Session = Depends(get_sync_db)):
    """Évalue la santé de chaque position — détecte l'essoufflement."""
    from backend.modules.execution.exhaustion_checker import check_all_positions_health
    return check_all_positions_health(db)


@router.post("/check-tp-sl")
def check_tp_sl(db: Session = Depends(get_sync_db)):
    """Vérifie et ferme les positions qui ont atteint leur TP ou SL."""
    from backend.modules.execution.tp_sl_monitor import check_and_close_positions
    return check_and_close_positions(db)


@router.get("/broker/status")
def broker_status():
    """Statut des brokers connectés (IBKR + Alpaca)."""
    from backend.modules.execution.broker_multi import multi_broker
    # Forcer la tentative de connexion IBKR si configuré
    if multi_broker.ibkr.is_configured and not multi_broker.ibkr_live:
        try:
            multi_broker.ibkr._connect()
        except Exception as e:
            logger.warning(f"[BROKER] IBKR connexion échouée: {e}")
    return multi_broker.get_status()


@router.get("/notifications")
def get_notifications():
    """Historique des notifications envoyées."""
    from pathlib import Path
    notif_file = Path("data/notifications.log")
    if notif_file.exists():
        content = notif_file.read_text()
        # Dernières 20 notifications
        blocks = content.split("=" * 60)
        recent = blocks[-40:]  # 2 blocs par notif (séparateur + contenu)
        return {"notifications": "".join(recent).strip(), "total": len(blocks) // 2}
    return {"notifications": "Aucune notification", "total": 0}


@router.get("/ibkr-candidates")
def ibkr_candidates(db: Session = Depends(get_sync_db)):
    """Positions Alpaca validées qu'IBKR peut copier.

    Retourne les positions Alpaca en profit avec un bon score,
    qui ne sont pas déjà en position chez IBKR.
    """
    from backend.modules.execution.position_manager_v2 import get_ibkr_candidates
    candidates = get_ibkr_candidates(db)
    eligible = [c for c in candidates if c["eligible"]]
    return {
        "candidates": candidates,
        "eligible_count": len(eligible),
        "total_count": len(candidates),
        "message": f"{len(eligible)} positions Alpaca éligibles pour IBKR live",
    }


@router.get("/opportunity-arbiter")
def opportunity_arbiter(db: Session = Depends(get_sync_db)):
    """Arbitrage d'opportunité — compare les positions IBKR vs signaux GO.

    Classe chaque position et signal par EV/jour (espérance de valeur par jour).
    Recommande des swaps quand un signal GO a plus de potentiel qu'une position fatiguée.
    """
    from backend.modules.execution.opportunity_arbiter import run_opportunity_arbitrage
    return run_opportunity_arbitrage(db)


@router.get("/ibkr-analysis")
def ibkr_analysis(db: Session = Depends(get_sync_db)):
    """Analyse des positions IBKR live — croise avec scanner + signaux pour donner un verdict.

    Retourne pour chaque position IBKR : prix actuel, P&L, scanner score, verdict (solide/surveiller/fermer)
    et raison du verdict.
    """
    import json
    from pathlib import Path
    from backend.database.models import Order as OrderModel

    # 1. Charger les caches
    scanner_data = {}
    try:
        with open(Path("data/scanner_cache.json")) as f:
            scanner_data = {r["symbol"]: r for r in json.load(f).get("results", [])}
    except Exception as e:
        logger.warning(f"[IBKR-ANALYSIS] Scanner cache unavailable: {e}")

    signals_data = {}
    try:
        with open(Path("data/signals_cache.json")) as f:
            raw = json.load(f)
            signals_list = raw if isinstance(raw, list) else raw.get("signals", [])
            signals_data = {s["symbol"]: s for s in signals_list}
    except Exception as e:
        logger.warning(f"[IBKR-ANALYSIS] Signals cache unavailable: {e}")

    # 2. Identifier les positions IBKR (via ordres broker=ibkr OR qty petites)
    ibkr_asset_ids = set()
    for o in db.query(OrderModel).filter_by(broker="ibkr").all():
        ibkr_asset_ids.add(o.asset_id)

    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()

    results = []
    totals = {"invested": 0.0, "pnl": 0.0, "count": 0}
    verdict_counts = {"solide": 0, "surveiller": 0, "fermer": 0}

    for p in positions:
        is_ibkr = p.asset_id in ibkr_asset_ids and float(p.quantity) <= 50
        if not is_ibkr:
            continue

        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if not asset:
            continue

        # Prix actuel depuis OHLCV daily
        last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
        cur = float(last.close) if last else float(p.entry_price)
        entry = float(p.entry_price)
        qty = float(p.quantity)
        direction = p.direction.value

        if direction == "LONG":
            pnl_pct = (cur - entry) / entry * 100 if entry else 0
            pnl_usd = (cur - entry) * qty
        else:
            pnl_pct = (entry - cur) / entry * 100 if entry else 0
            pnl_usd = (entry - cur) * qty

        # Données scanner
        sc = scanner_data.get(asset.symbol, {})
        sc_scores = sc.get("scores", {})
        sc_final = sc_scores.get("final", 50)
        sc_tech = sc_scores.get("technical", 50)
        sc_sus = sc_scores.get("sus", 50)
        vetoed = sc.get("vetoed", False)

        # Signal inverse ?
        sig = signals_data.get(asset.symbol, {})
        new_direction = sig.get("direction")
        new_score = sig.get("score_v2", sig.get("score"))
        has_opposite = (new_direction and new_direction != direction and new_score and new_score >= 65)

        # Verdict
        reasons = []
        if vetoed:
            reasons.append("VETO scanner")
        if direction == "LONG" and sc_final < 45:
            reasons.append(f"scanner baissier ({sc_final:.0f})")
        elif direction == "SHORT" and sc_final > 60:
            reasons.append(f"scanner haussier ({sc_final:.0f})")
        if pnl_pct < -8:
            reasons.append(f"perte importante ({pnl_pct:.1f}%)")
        elif pnl_pct < -5:
            reasons.append(f"perte notable ({pnl_pct:.1f}%)")
        if has_opposite:
            reasons.append(f"signal inverse {new_direction} ({new_score:.0f})")
        if sc_tech < 45 and direction == "LONG":
            reasons.append(f"technique faible ({sc_tech:.0f})")

        # Classification
        if vetoed or pnl_pct < -8 or (direction == "LONG" and sc_final < 45) or has_opposite:
            verdict = "fermer"
        elif reasons:
            verdict = "surveiller"
        else:
            verdict = "solide"

        verdict_counts[verdict] += 1
        totals["invested"] += entry * qty
        totals["pnl"] += pnl_usd
        totals["count"] += 1

        results.append({
            "symbol": asset.symbol,
            "name": asset.name,
            "direction": direction,
            "quantity": qty,
            "entry_price": entry,
            "current_price": cur,
            "pnl_usd": round(pnl_usd, 2),
            "pnl_pct": round(pnl_pct, 2),
            "stop_loss": float(p.stop_loss) if p.stop_loss else 0,
            "take_profit": float(p.take_profit) if p.take_profit else 0,
            "scanner_score": round(sc_final, 1),
            "technical_score": round(sc_tech, 1),
            "sus_score": round(sc_sus, 1),
            "vetoed": vetoed,
            "new_signal": {
                "direction": new_direction,
                "score": round(new_score, 1) if new_score else None,
                "action": sig.get("action"),
            } if sig else None,
            "verdict": verdict,
            "reasons": reasons,
            "opened_at": p.opened_at.isoformat() if p.opened_at else None,
        })

    # Trier par verdict (fermer > surveiller > solide) puis par pnl
    verdict_order = {"fermer": 0, "surveiller": 1, "solide": 2}
    results.sort(key=lambda x: (verdict_order.get(x["verdict"], 3), -x["pnl_pct"]))

    return {
        "count": totals["count"],
        "total_invested": round(totals["invested"], 2),
        "total_pnl": round(totals["pnl"], 2),
        "total_pnl_pct": round(totals["pnl"] / totals["invested"] * 100, 2) if totals["invested"] > 0 else 0,
        "verdicts": verdict_counts,
        "positions": results,
    }
