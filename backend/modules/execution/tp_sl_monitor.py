"""TP/SL Monitor — Vérifie et ferme les positions qui ont atteint leur cible

Problème résolu : les bracket orders Alpaca échouent parfois silencieusement,
laissant des positions sans SL ni TP chez le broker. Ce monitor vérifie
le prix actuel vs SL/TP en BDD et ferme les positions automatiquement.

Exécuté :
- Par Celery Beat toutes les 5 minutes pendant les heures de marché
- Manuellement via POST /api/execution/check-tp-sl
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from backend.database.models import Asset, Position, PositionStatus, SignalDirection, Order, OrderStatus as DBOrderStatus, OrderSide as DBOrderSide

logger = logging.getLogger("tradepilot.tp_sl_monitor")


def check_and_close_positions(db: Session) -> dict:
    """Vérifie toutes les positions ouvertes et ferme celles qui ont atteint SL/TP."""
    from backend.modules.execution.broker_alpaca import alpaca_broker

    if not alpaca_broker.is_configured:
        return {"checked": 0, "closed": [], "message": "Alpaca non configuré"}

    # Nettoyage préventif : zombies + doublons (garanti propre avant le check)
    try:
        from backend.modules.execution.data_cleaner import full_clean
        clean_result = full_clean(db)
        if clean_result["zombies_removed"] > 0 or clean_result["duplicates_cancelled"] > 0:
            logger.info(f"[TP/SL] Auto-clean: {clean_result['zombies_removed']} zombies, {clean_result['duplicates_cancelled']} doublons")
    except Exception as e:
        logger.warning(f"[TP/SL] Auto-clean échoué: {e}")

    # Trailing stops d'abord — remonter les SL avant de vérifier
    trailing_result = {"updated": 0}
    try:
        from backend.modules.execution.trailing_stop import update_trailing_stops
        trailing_result = update_trailing_stops(db)
    except Exception as e:
        logger.warning(f"[TP/SL] Erreur trailing stop: {e}")

    # Positions ouvertes en BDD avec SL/TP
    open_positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    if not open_positions:
        return {"checked": 0, "closed": [], "trailing": trailing_result, "message": "Aucune position ouverte"}

    # Prix live depuis Alpaca
    alpaca_positions = {p["symbol"]: p for p in alpaca_broker.get_positions()}

    checked = 0
    closed = []

    for pos in open_positions:
        asset = db.query(Asset).filter_by(id=pos.asset_id).first()
        if not asset:
            continue

        symbol = asset.symbol
        checked += 1

        # Prix actuel
        live = alpaca_positions.get(symbol)
        if live:
            current_price = float(live["current_price"])
        else:
            # Pas chez Alpaca — essayer le dernier prix en BDD
            current_price = alpaca_broker.get_last_price(symbol)
            if not current_price:
                continue

        entry = float(pos.entry_price)
        sl = float(pos.stop_loss) if pos.stop_loss else None
        tp = float(pos.take_profit) if pos.take_profit else None
        direction = pos.direction.value

        reason = None

        # Vérifier Take Profit
        if tp:
            if direction == "LONG" and current_price >= tp:
                reason = f"TP atteint (${current_price:.2f} >= ${tp:.2f})"
            elif direction == "SHORT" and current_price <= tp:
                reason = f"TP atteint (${current_price:.2f} <= ${tp:.2f})"

        # Vérifier Stop Loss
        if sl and not reason:
            if direction == "LONG" and current_price <= sl:
                reason = f"SL touché (${current_price:.2f} <= ${sl:.2f})"
            elif direction == "SHORT" and current_price >= sl:
                reason = f"SL touché (${current_price:.2f} >= ${sl:.2f})"

        # Vérifier les règles breakeven (fermer dès retour au prix d'entrée)
        if not reason:
            try:
                from pathlib import Path as _P
                import json as _json
                _be_file = _P("data/breakeven_rules.json")
                if _be_file.exists():
                    _be_rules = _json.loads(_be_file.read_text())
                    for rule in _be_rules:
                        if rule.get("symbol") == symbol and rule.get("active"):
                            be_price = rule["breakeven_price"]
                            if direction == "LONG" and current_price >= be_price:
                                reason = f"Breakeven atteint (${current_price:.2f} >= ${be_price:.2f})"
                            elif direction == "SHORT" and current_price <= be_price:
                                reason = f"Breakeven atteint (${current_price:.2f} <= ${be_price:.2f})"
            except Exception as e:
                logger.warning(f"[TP/SL] Erreur check breakeven {symbol}: {e}")

        # Vérifier essoufflement
        if not reason:
            try:
                from backend.modules.execution.exhaustion_checker import check_position_health
                pnl_check = (current_price - entry) if direction == "LONG" else (entry - current_price)
                pnl_pct_check = ((current_price / entry) - 1) * 100 if direction == "LONG" else ((entry / current_price) - 1) * 100

                # Protection urgente : perte > 10% → fermer immédiatement
                if pnl_pct_check < -10:
                    reason = f"Perte critique ({pnl_pct_check:.1f}% > -10%)"
                else:
                    health = check_position_health(db, symbol, direction, entry)
                    if health["score"] < 40:
                        # ÉPUISÉ → fermer dans tous les cas
                        reason = f"Épuisé (score santé {health['score']}/100)"
                    elif health["score"] < 50 and pnl_check < 0:
                        # FAIBLE + en perte → fermer
                        reason = f"Faible + en perte (score santé {health['score']}/100)"
                    elif health["score"] < 50 and pnl_check > 0:
                        # FAIBLE + en profit → resserrer le trailing stop à 1×ATR
                        try:
                            from backend.database.models import OHLCVDaily
                            import pandas as pd
                            rows_ts = db.query(OHLCVDaily).filter_by(asset_id=pos.asset_id).order_by(OHLCVDaily.date.desc()).limit(20).all()
                            if len(rows_ts) >= 14:
                                highs_ts = pd.Series([float(r.high) for r in reversed(rows_ts)])
                                lows_ts = pd.Series([float(r.low) for r in reversed(rows_ts)])
                                closes_ts = pd.Series([float(r.close) for r in reversed(rows_ts)])
                                tr = pd.concat([highs_ts - lows_ts, (highs_ts - closes_ts.shift(1)).abs(), (lows_ts - closes_ts.shift(1)).abs()], axis=1).max(axis=1)
                                atr_val = float(tr.iloc[-14:].mean())
                                tight_sl = round(current_price - 1 * atr_val, 2) if direction == "LONG" else round(current_price + 1 * atr_val, 2)
                                old_sl_val = float(pos.stop_loss) if pos.stop_loss else 0
                                if direction == "LONG" and tight_sl > old_sl_val:
                                    pos.stop_loss = tight_sl
                                    db.commit()
                                    logger.info(f"[TP/SL] {symbol} FAIBLE+profit → SL resserré à ${tight_sl:.2f} (1×ATR)")
                                elif direction == "SHORT" and tight_sl < old_sl_val:
                                    pos.stop_loss = tight_sl
                                    db.commit()
                                    logger.info(f"[TP/SL] {symbol} FAIBLE+profit → SL resserré à ${tight_sl:.2f} (1×ATR)")
                        except Exception as e:
                            logger.warning(f"[TP/SL] Erreur resserrement SL {symbol}: {e}")
            except Exception as e:
                logger.warning(f"[TP/SL] Erreur vérification essoufflement {symbol}: {e}")

        # Vérifier signal GO inverse (retournement)
        if not reason:
            try:
                import json
                from pathlib import Path
                signals_file = Path("data/signals_cache.json")
                if signals_file.exists():
                    signals = json.loads(signals_file.read_text())
                    for sig in signals:
                        if sig.get("symbol") == symbol and sig.get("action") == "GO":
                            sig_dir = sig.get("direction", "LONG")
                            if sig_dir != direction:
                                reason = f"Signal GO inverse ({direction} → {sig_dir}, score {sig.get('thesis_score', 0):.1f})"
                                break
            except Exception as e:
                logger.warning(f"[TP/SL] Erreur lecture signal GO inverse {symbol}: {e}")

        if not reason:
            continue

        # Fermer la position
        logger.info(f"[TP/SL] {symbol} — {reason}")

        broker_result = None
        if live:
            try:
                # Annuler les ordres ouverts
                open_orders = alpaca_broker.get_orders(status="open")
                for o in open_orders:
                    if o["symbol"] == symbol:
                        alpaca_broker.cancel_order(o["id"])
                # Fermer chez Alpaca
                broker_result = alpaca_broker.close_position(symbol)
            except Exception as e:
                logger.error(f"[TP/SL] Erreur fermeture Alpaca {symbol}: {e}")

        # Fermer aussi chez IBKR si configuré
        try:
            from backend.modules.execution.broker_ibkr import ibkr_broker
            if ibkr_broker.is_configured:
                ibkr_broker.close_position(symbol)
        except Exception as e:
            logger.error(f"[TP/SL] Erreur fermeture IBKR {symbol}: {e}")

        # Fermer en BDD
        pos.status = PositionStatus.CLOSED
        pos.closed_at = datetime.utcnow()
        pos.exit_price = current_price

        pnl = (current_price - entry) * float(pos.quantity) if direction == "LONG" else (entry - current_price) * float(pos.quantity)
        pnl_pct = ((current_price / entry) - 1) * 100 if direction == "LONG" else ((entry / current_price) - 1) * 100

        # Apprentissage qualité d'entrée
        try:
            from backend.modules.learning.entry_quality_tracker import record_exit
            record_exit(symbol, pnl, pnl_pct)
        except Exception as e:
            logger.warning(f"[TP/SL] Erreur apprentissage qualité entrée {symbol}: {e}")

        # Apprentissage — enregistrer le résultat du trade avec les scores scanner
        try:
            from backend.modules.learning.adaptive_engine import record_trade_result
            # Récupérer les scores scanner depuis le cache
            entry_scores = {}
            try:
                from backend.modules.scanner.cache import get_cached_results
                cached = get_cached_results()
                for r in cached:
                    if r["symbol"] == symbol:
                        entry_scores = r.get("scores", {})
                        break
            except Exception as e:
                logger.warning(f"[TP/SL] Erreur lecture cache scanner {symbol}: {e}")
            record_trade_result(
                symbol=symbol,
                strategy="auto",
                direction=direction,
                pnl=pnl,
                pnl_pct=pnl_pct,
                entry_scores=entry_scores,
            )
        except Exception as e:
            logger.warning(f"[TP/SL] Erreur apprentissage adaptatif {symbol}: {e}")

        # Si fermeture pour signal inverse → ouvrir dans le nouveau sens
        new_direction = None
        if "Signal GO inverse" in reason:
            new_dir = "SHORT" if direction == "LONG" else "LONG"
            try:
                from backend.modules.scanner.live_data import is_alpaca_symbol
                from backend.database.models import OHLCVDaily
                import pandas as pd
                from backend.modules.scanner.indicators import atr as compute_atr

                rows = db.query(OHLCVDaily).filter_by(asset_id=pos.asset_id).order_by(OHLCVDaily.date.desc()).limit(50).all()
                if len(rows) >= 14:
                    closes = pd.Series([float(r.close) for r in reversed(rows)])
                    highs = pd.Series([float(r.high) for r in reversed(rows)])
                    lows = pd.Series([float(r.low) for r in reversed(rows)])
                    atr_val = float(compute_atr(highs, lows, closes, 14).iloc[-1])

                    new_sl = round(current_price + 2 * atr_val, 2) if new_dir == "SHORT" else round(current_price - 2 * atr_val, 2)
                    new_tp = round(current_price - 3 * atr_val, 2) if new_dir == "SHORT" else round(current_price + 3 * atr_val, 2)
                    new_qty = max(1, int(7000 / current_price))

                    # Ouvrir chez Alpaca
                    if alpaca_broker.is_configured and is_alpaca_symbol(symbol):
                        side = "BUY" if new_dir == "LONG" else "SELL"
                        alpaca_broker.place_order(symbol, side, new_qty, "market")

                    # Ouvrir en BDD
                    db.add(Position(
                        asset_id=pos.asset_id,
                        direction=SignalDirection.LONG if new_dir == "LONG" else SignalDirection.SHORT,
                        entry_price=current_price, quantity=float(new_qty),
                        stop_loss=new_sl, take_profit=new_tp, status=PositionStatus.OPEN,
                    ))
                    new_direction = new_dir
                    logger.info(f"[TP/SL] Retournement {symbol}: {direction} → {new_dir} à ${current_price:.2f}")
            except Exception as e:
                logger.warning(f"[TP/SL] Erreur retournement {symbol}: {e}")

        closed.append({
            "symbol": symbol,
            "reason": reason,
            "entry": entry,
            "exit": current_price,
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "broker_closed": broker_result is not None and "error" not in (broker_result or {}),
            "reversed_to": new_direction,
        })

    db.commit()

    if closed:
        logger.info(f"[TP/SL] {len(closed)} positions fermées: {', '.join(c['symbol'] for c in closed)}")

    # ============================================================
    # Remplir les slots — IBKR D'ABORD (argent réel), puis Alpaca
    # ============================================================
    queue_filled = []
    try:
        from backend.modules.execution.position_manager_v2 import (
            get_next_in_queue, remove_from_queue, MAX_POSITIONS, get_queue,
        )
        from backend.modules.scanner.live_data import is_alpaca_symbol

        # Symboles déjà en position (tous brokers)
        open_symbols = set()
        alpaca_symbols = set()
        ibkr_symbols = set()

        if alpaca_broker.is_configured:
            for p in alpaca_broker.get_positions():
                open_symbols.add(p["symbol"])
                alpaca_symbols.add(p["symbol"])

        # IBKR positions
        ibkr_count = 0
        MAX_IBKR = 10
        try:
            from backend.config.settings import settings as _settings
            if _settings.IBKR_ACCOUNT_ID:
                import concurrent.futures as _cf
                import asyncio as _aio
                def _get_ibkr_syms():
                    loop = _aio.new_event_loop()
                    _aio.set_event_loop(loop)
                    from ib_insync import IB
                    ib = IB()
                    ib.connect(_settings.IBKR_HOST, _settings.IBKR_PORT, clientId=51, timeout=10)
                    syms = set()
                    for p in ib.positions(_settings.IBKR_ACCOUNT_ID):
                        if p.position != 0:
                            syms.add(p.contract.symbol)
                    ib.disconnect()
                    loop.close()
                    return syms
                try:
                    with _cf.ThreadPoolExecutor() as ex:
                        ibkr_symbols = ex.submit(_get_ibkr_syms).result(timeout=15)
                    ibkr_count = len(ibkr_symbols)
                    open_symbols.update(ibkr_symbols)
                except Exception as e:
                    logger.error(f"[TP/SL] Erreur connexion IBKR positions: {e}")
        except Exception as e:
            logger.warning(f"[TP/SL] Erreur config IBKR: {e}")

        for p in db.query(Position).filter_by(status=PositionStatus.OPEN).all():
            a = db.query(Asset).filter_by(id=p.asset_id).first()
            if a:
                open_symbols.add(a.symbol)

        alpaca_count = len(alpaca_symbols)
        db_open = db.query(Position).filter_by(status=PositionStatus.OPEN).count()
        current_positions = max(alpaca_count, db_open)

        # PHASE 1 : IBKR prend les meilleurs signaux en premier
        queue = get_queue()
        ibkr_filled = []
        if ibkr_count < MAX_IBKR:
            for q in queue:
                if ibkr_count >= MAX_IBKR:
                    break
                sym = q.get("symbol", "")
                if sym in ibkr_symbols or sym in [f["symbol"] for f in ibkr_filled]:
                    continue
                if not is_alpaca_symbol(sym):  # Actifs non-US skip
                    continue
                if any(s in sym for s in ['.PA', '.DE', '.SW', '.L', '.MI', '.AS', '=F', '=X', '-USD']):
                    continue

                direction = q.get("direction", "LONG")
                score = q.get("score", 50)

                try:
                    from backend.modules.execution.router import _get_price_and_atr
                    asset = db.query(Asset).filter_by(symbol=sym).first()
                    if not asset:
                        continue
                    entry_price, atr_val = _get_price_and_atr(db, asset.id)
                    if not entry_price:
                        continue

                    # Vérifier la santé AVANT d'acheter — seuil appris automatiquement
                    try:
                        from backend.modules.execution.exhaustion_checker import check_position_health
                        from backend.modules.learning.entry_quality_tracker import get_optimal_threshold, record_entry
                        min_health = get_optimal_threshold()
                        pre_health = check_position_health(db, sym, direction, entry_price)
                        if pre_health["score"] < min_health:
                            logger.info(f"[TP/SL] IBKR skip {sym} — santé {pre_health['score']}/100 < seuil {min_health}")
                            continue
                        # Enregistrer la santé à l'entrée pour l'apprentissage
                        record_entry(sym, direction, pre_health["score"], pre_health.get("signals", []))
                    except Exception as e:
                        logger.warning(f"[TP/SL] Erreur vérification santé IBKR {sym}: {e}")

                    # Sizing IBKR
                    import concurrent.futures as cf2
                    import asyncio as aio2
                    def _ibkr_buy(s=sym, d=direction, ep=entry_price):
                        loop = aio2.new_event_loop()
                        aio2.set_event_loop(loop)
                        from ib_insync import IB, Stock, MarketOrder
                        from backend.modules.execution.broker_ibkr import IBKR_CLIENT_IDS
                        ib = IB()
                        ib.connect(_settings.IBKR_HOST, _settings.IBKR_PORT, clientId=IBKR_CLIENT_IDS["queue_buy"], timeout=15)
                        acct = ib.accountSummary(_settings.IBKR_ACCOUNT_ID)
                        equity = _settings.IBKR_DEFAULT_EQUITY
                        for item in acct:
                            if item.tag == 'NetLiquidation':
                                equity = float(item.value)
                        from backend.modules.execution.sizing import compute_position_size, quantize
                        ibkr_sizing = compute_position_size(capital=equity, entry_price=ep, score=score)
                        qty = quantize(ibkr_sizing["quantity"], s)

                        # SL/TP pour bracket order
                        sl_price = round(ep - 2 * atr_val, 2) if d == "LONG" else round(ep + 2 * atr_val, 2)
                        tp_price = round(ep + 3 * atr_val, 2) if d == "LONG" else round(ep - 3 * atr_val, 2)

                        # Bracket order : entry + SL + TP serveur-side
                        from ib_insync import LimitOrder, StopOrder
                        contract = Stock(s, 'SMART', 'USD')
                        ib.qualifyContracts(contract)
                        action = "BUY" if d == "LONG" else "SELL"
                        reverse = "SELL" if action == "BUY" else "BUY"

                        parent = MarketOrder(action, qty)
                        parent.orderId = ib.client.getReqId()
                        parent.transmit = False

                        tp_order = LimitOrder(reverse, qty, tp_price)
                        tp_order.orderId = ib.client.getReqId()
                        tp_order.parentId = parent.orderId
                        tp_order.transmit = False

                        sl_order = StopOrder(reverse, qty, sl_price)
                        sl_order.orderId = ib.client.getReqId()
                        sl_order.parentId = parent.orderId
                        sl_order.transmit = True

                        parent_trade = ib.placeOrder(contract, parent)
                        ib.placeOrder(contract, tp_order)
                        ib.placeOrder(contract, sl_order)
                        ib.sleep(2)
                        status = parent_trade.orderStatus.status
                        logger.info(f"[TP/SL] IBKR bracket: {action} {qty} {s} SL=${sl_price} TP=${tp_price}")

                        try:
                            ib.disconnect()
                        except Exception:
                            pass
                        loop.close()
                        return status, qty
                    with cf2.ThreadPoolExecutor() as ex:
                        status, qty = ex.submit(_ibkr_buy).result(timeout=30)

                    if status in ('Filled', 'Submitted', 'PreSubmitted'):
                        ibkr_filled.append({"symbol": sym, "direction": direction, "qty": qty, "broker": "ibkr"})
                        ibkr_symbols.add(sym)
                        open_symbols.add(sym)
                        ibkr_count += 1

                        # Enregistrer en BDD pour l'historique
                        sl = round(entry_price - 2 * atr_val, 2) if direction == "LONG" else round(entry_price + 2 * atr_val, 2)
                        tp = round(entry_price + 3 * atr_val, 2) if direction == "LONG" else round(entry_price - 3 * atr_val, 2)
                        from backend.database.models import Order as OrderModel, OrderSide as OrdSide, OrderStatus as OrdStatus
                        db.add(OrderModel(
                            asset_id=asset.id,
                            side=OrdSide.BUY if direction == "LONG" else OrdSide.SELL,
                            quantity=float(qty), price=entry_price, filled_price=entry_price,
                            status=OrdStatus.FILLED, tranche=1, broker="ibkr",
                        ))
                        db.add(Position(
                            asset_id=asset.id,
                            direction=SignalDirection.LONG if direction == "LONG" else SignalDirection.SHORT,
                            entry_price=entry_price, quantity=float(qty),
                            stop_loss=sl, take_profit=tp, status=PositionStatus.OPEN,
                        ))
                        db.commit()
                        logger.info(f"[TP/SL] IBKR PRIORITAIRE → {sym} {direction} qty={qty} SL=${sl} TP=${tp} (score={score:.0f}) — enregistré BDD")
                except Exception as e:
                    logger.warning(f"[TP/SL] IBKR erreur {sym}: {e}")

        queue_filled.extend(ibkr_filled)

        # PHASE 2 : Alpaca remplit ses slots
        # Logique : IBKR a la priorité sur les meilleurs signaux.
        # Alpaca prend tout signal que IBKR a déjà pris OU que IBKR ne peut pas prendre (slots pleins)
        queue_for_alpaca = get_queue()
        alpaca_queue = []
        ibkr_slots_remaining = MAX_IBKR - ibkr_count

        for q in queue_for_alpaca:
            sym = q.get("symbol", "")
            if sym in ibkr_symbols:
                # IBKR l'a déjà → Alpaca peut aussi le prendre
                alpaca_queue.append(q)
            elif ibkr_slots_remaining > 0:
                # Encore des slots IBKR → réservé pour IBKR, Alpaca skip
                ibkr_slots_remaining -= 1
                continue
            else:
                # Plus de slots IBKR → Alpaca peut prendre
                alpaca_queue.append(q)

        alpaca_idx = 0
        while current_positions < MAX_POSITIONS and alpaca_idx < len(alpaca_queue):
            next_signal = alpaca_queue[alpaca_idx]
            alpaca_idx += 1
            sym = next_signal.get("symbol", "")
            direction = next_signal.get("direction", "LONG")
            score = next_signal.get("score", 50)

            # Skip si déjà en position
            if sym in open_symbols:
                remove_from_queue(sym)
                continue

            # Skip si pas supporté par Alpaca
            if not is_alpaca_symbol(sym):
                remove_from_queue(sym)
                continue

            try:
                from backend.modules.execution.router import _get_price_and_atr
                asset = db.query(Asset).filter_by(symbol=sym).first()
                if not asset:
                    remove_from_queue(sym)
                    continue
                entry_price, atr_val = _get_price_and_atr(db, asset.id)
                if not entry_price:
                    remove_from_queue(sym)
                    continue

                # Vérifier la santé AVANT d'acheter — seuil appris automatiquement
                try:
                    from backend.modules.execution.exhaustion_checker import check_position_health
                    from backend.modules.learning.entry_quality_tracker import get_optimal_threshold, record_entry
                    min_health = get_optimal_threshold()
                    pre_health = check_position_health(db, sym, direction, entry_price)
                    if pre_health["score"] < min_health:
                        logger.info(f"[TP/SL] Alpaca skip {sym} — santé {pre_health['score']}/100 < seuil {min_health}")
                        remove_from_queue(sym)
                        continue
                    record_entry(sym, direction, pre_health["score"], pre_health.get("signals", []))
                except Exception as e:
                    logger.warning(f"[TP/SL] Erreur vérification santé Alpaca {sym}: {e}")

                sl = round(entry_price - 2 * atr_val, 2) if direction == "LONG" else round(entry_price + 2 * atr_val, 2)
                tp = round(entry_price + 3 * atr_val, 2) if direction == "LONG" else round(entry_price - 3 * atr_val, 2)

                # Sizing centralisé
                from backend.modules.execution.sizing import compute_position_size, quantize
                alpaca_capital = 100_000
                if alpaca_broker.is_configured:
                    try:
                        acct = alpaca_broker.get_account()
                        alpaca_capital = acct.get("equity", 100_000)
                    except Exception as e:
                        logger.warning(f"[TP/SL] Erreur récupération equity Alpaca: {e}")
                sizing = compute_position_size(capital=alpaca_capital, entry_price=entry_price, score=score)
                qty = quantize(sizing["quantity"], sym)
                side = "buy" if direction == "LONG" else "sell"

                # Envoyer chez Alpaca avec BRACKET ORDER (entry + SL + TP)
                if alpaca_broker.is_configured and is_alpaca_symbol(sym):
                    try:
                        from backend.modules.execution.router import _place_bracket_order
                        result = _place_bracket_order(sym, side, qty, sl, tp)
                        if result and "error" in result:
                            # Fallback market order si bracket échoue
                            result = alpaca_broker.place_order(sym, side, qty, "market")
                    except Exception as e:
                        logger.error(f"[TP/SL] Erreur bracket order Alpaca {sym}, fallback market: {e}")
                        result = alpaca_broker.place_order(sym, side, qty, "market")
                    if "error" in (result or {}):
                        logger.warning(f"[TP/SL] Alpaca erreur {sym}: {(result or {}).get('error','')[:60]}")
                        remove_from_queue(sym)
                        continue
                    logger.info(f"[TP/SL] Alpaca BRACKET → {sym} {direction} qty={qty} SL=${sl} TP=${tp}")

                # Envoyer chez IBKR (réel, fractional shares)
                try:
                    from backend.modules.execution.broker_ibkr import ibkr_broker
                    if ibkr_broker.is_configured:
                        import asyncio, concurrent.futures
                        def _ibkr_order():
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            from backend.config.settings import settings as _ibkr_settings
                            ibkr_equity = _ibkr_settings.IBKR_DEFAULT_EQUITY
                            try:
                                acct = ibkr_broker.get_account()
                                ibkr_equity = max(acct.get("equity", _ibkr_settings.IBKR_DEFAULT_EQUITY), 1)
                            except Exception as e:
                                logger.warning(f"[TP/SL] Erreur lecture compte IBKR {sym}: {e}")
                            from backend.modules.execution.sizing import compute_position_size
                            ibkr_sizing = compute_position_size(capital=ibkr_equity, entry_price=entry_price, score=score)
                            ibkr_size = ibkr_sizing["position_size"]
                            ibkr_result = ibkr_broker.place_order(sym, side, 0, "market", cash_qty=ibkr_size)
                            loop.close()
                            return ibkr_result, ibkr_size
                        with concurrent.futures.ThreadPoolExecutor() as ex:
                            ibkr_result, ibkr_size = ex.submit(_ibkr_order).result(timeout=15)
                        if "error" not in ibkr_result:
                            logger.info(f"[TP/SL] IBKR → {sym} {direction} €{ibkr_size:.2f} fractional")
                        else:
                            logger.warning(f"[TP/SL] IBKR erreur {sym}: {ibkr_result.get('error','')[:60]}")
                except Exception as e:
                    logger.warning(f"[TP/SL] IBKR skip {sym}: {e}")

                # Enregistrer en BDD
                db.add(Position(
                    asset_id=asset.id,
                    direction=SignalDirection.LONG if direction == "LONG" else SignalDirection.SHORT,
                    entry_price=entry_price, quantity=float(qty),
                    stop_loss=sl, take_profit=tp, status=PositionStatus.OPEN,
                ))
                db.commit()
                remove_from_queue(sym)
                open_symbols.add(sym)
                current_positions += 1
                queue_filled.append({"symbol": sym, "direction": direction, "entry": entry_price, "qty": qty, "score": score, "ibkr": True})
                logger.info(f"[TP/SL] Queue → {sym} {direction} qty={qty} à ${entry_price:.2f} (score={score:.0f}, slot {current_positions}/{MAX_POSITIONS})")
            except Exception as e:
                logger.warning(f"[TP/SL] Erreur queue {sym}: {e}")
                remove_from_queue(sym)
    except Exception as e:
        logger.warning(f"[TP/SL] Erreur traitement queue: {e}")

    # ============================================================
    # IBKR — Surveiller et protéger les positions réelles
    # Fixes appliqués :
    # - Engine DB partagé (pas de create_engine en boucle)
    # - Prix IBKR natifs + fallback Alpaca
    # - SYMBOL_MAPPING pour les contrats EU
    # - Client ID centralisé (IBKR_CLIENT_IDS["monitor"])
    # - Timeout 90s au lieu de 30s + déconnexion propre
    # ============================================================
    ibkr_closed = []
    try:
        from backend.config.settings import settings
        if settings.IBKR_ACCOUNT_ID:
            import concurrent.futures as cf
            import asyncio as aio

            def _monitor_ibkr():
                loop = aio.new_event_loop()
                aio.set_event_loop(loop)
                from ib_insync import IB, MarketOrder
                from backend.modules.execution.broker_ibkr import IBKR_CLIENT_IDS, SYMBOL_MAPPING
                from backend.database.sync_session import engine as _db_engine

                ib = IB()
                try:
                    ib.connect(settings.IBKR_HOST, settings.IBKR_PORT,
                               clientId=IBKR_CLIENT_IDS["monitor"], timeout=15)
                except Exception as e:
                    logger.warning(f"[TP/SL] IBKR monitor connexion échouée: {e}")
                    loop.close()
                    return []

                ib.reqMarketDataType(3)  # Données différées

                ibkr_positions = ib.positions(settings.IBKR_ACCOUNT_ID)
                results = []

                from sqlalchemy.orm import Session as SyncSession
                import pandas as pd
                from backend.database.models import OHLCVDaily as OHLCV

                for pos in ibkr_positions:
                    if pos.position == 0:
                        continue

                    sym = pos.contract.symbol
                    entry = float(pos.avgCost)
                    qty = abs(float(pos.position))
                    direction = "LONG" if pos.position > 0 else "SHORT"

                    # Prix : IBKR natif d'abord, Alpaca en fallback
                    current = None
                    try:
                        [ticker] = ib.reqTickers(pos.contract)
                        if ticker.marketPrice():
                            current = float(ticker.marketPrice())
                        elif ticker.close:
                            current = float(ticker.close)
                    except Exception as e:
                        logger.warning(f"[TP/SL] IBKR prix natif échoué {sym}: {e}")

                    # Fallback Alpaca
                    alpaca_price = None
                    if not current:
                        try:
                            alpaca_price = alpaca_broker.get_last_price(sym)
                            current = alpaca_price
                        except Exception as e:
                            logger.warning(f"[TP/SL] Alpaca prix fallback échoué {sym}: {e}")

                    if not current:
                        logger.warning(f"[TP/SL] IBKR {sym} ignoré — aucun prix disponible")
                        continue

                    # Validation croisée : si le prix dévie de > 50% de l'entrée, c'est suspect
                    # (protège contre les prix aberrants post-split d'Alpaca)
                    deviation = abs(current - entry) / entry if entry > 0 else 0
                    if deviation > 0.5:
                        # Chercher le dernier close en BDD comme arbitre
                        with SyncSession(_db_engine) as db_check_price:
                            asset_check = db_check_price.query(Asset).filter_by(symbol=sym).first()
                            if asset_check:
                                last_ohlcv = db_check_price.query(OHLCV).filter_by(asset_id=asset_check.id).order_by(OHLCV.date.desc()).first()
                                if last_ohlcv:
                                    db_price = float(last_ohlcv.close)
                                    if abs(db_price - entry) / entry < deviation:
                                        logger.warning(f"[TP/SL] IBKR {sym} prix suspect {current:.2f} → fallback BDD {db_price:.2f}")
                                        current = db_price

                    # ATR depuis la BDD (engine partagé, pas create_engine)
                    with SyncSession(_db_engine) as db_ibkr:
                        # Convertir symbole IBKR → TradePilot pour la BDD
                        tp_symbol = sym
                        for tp_sym, (ibkr_sym, sec_type, _, _) in SYMBOL_MAPPING.items():
                            if pos.contract.symbol == ibkr_sym and pos.contract.secType == sec_type:
                                tp_symbol = tp_sym
                                break

                        asset = db_ibkr.query(Asset).filter_by(symbol=tp_symbol).first()
                        if not asset:
                            asset = db_ibkr.query(Asset).filter_by(symbol=sym).first()
                        if not asset:
                            continue
                        rows = db_ibkr.query(OHLCV).filter_by(asset_id=asset.id).order_by(OHLCV.date.desc()).limit(20).all()
                        if len(rows) < 14:
                            continue

                        highs = pd.Series([float(r.high) for r in reversed(rows)])
                        lows = pd.Series([float(r.low) for r in reversed(rows)])
                        closes = pd.Series([float(r.close) for r in reversed(rows)])
                        tr = pd.concat([highs - lows, (highs - closes.shift(1)).abs(), (lows - closes.shift(1)).abs()], axis=1).max(axis=1)
                        atr_val = float(tr.iloc[-14:].mean())

                    sl = round(entry - 2 * atr_val, 2) if direction == "LONG" else round(entry + 2 * atr_val, 2)
                    tp = round(entry + 3 * atr_val, 2) if direction == "LONG" else round(entry - 3 * atr_val, 2)

                    reason = None

                    # TP atteint
                    if direction == "LONG" and current >= tp:
                        reason = f"TP (${current:.2f} >= ${tp:.2f})"
                    elif direction == "SHORT" and current <= tp:
                        reason = f"TP (${current:.2f} <= ${tp:.2f})"

                    # SL touché
                    if not reason:
                        if direction == "LONG" and current <= sl:
                            reason = f"SL (${current:.2f} <= ${sl:.2f})"
                        elif direction == "SHORT" and current >= sl:
                            reason = f"SL (${current:.2f} >= ${sl:.2f})"

                    # Essoufflement
                    if not reason:
                        try:
                            from backend.modules.execution.exhaustion_checker import check_position_health
                            with SyncSession(_db_engine) as db_exhaust:
                                health = check_position_health(db_exhaust, tp_symbol, direction, entry)
                                pnl_check = (current - entry) if direction == "LONG" else (entry - current)
                                if health["score"] < 35:
                                    reason = f"Épuisé (santé {health['score']}/100)"
                                elif health["score"] < 50 and pnl_check < 0:
                                    reason = f"Faible+perte (santé {health['score']}/100)"
                        except Exception as e:
                            logger.warning(f"[TP/SL] Erreur essoufflement IBKR {sym}: {e}")

                    if not reason:
                        continue

                    # Fermer la position IBKR — utiliser le contrat original (supporte EU)
                    try:
                        ib.qualifyContracts(pos.contract)
                        action = "SELL" if direction == "LONG" else "BUY"
                        order = MarketOrder(action, qty)
                        trade = ib.placeOrder(pos.contract, order)
                        ib.sleep(2)
                        pnl = (current - entry) * qty if direction == "LONG" else (entry - current) * qty
                        results.append({
                            "symbol": tp_symbol, "broker": "ibkr", "reason": reason,
                            "entry": entry, "exit": current,
                            "pnl": round(pnl, 2), "status": trade.orderStatus.status,
                        })
                        logger.info(f"[TP/SL] IBKR fermé {tp_symbol}: {reason} P/L=${pnl:.2f}")

                        # Sync BDD
                        try:
                            from datetime import datetime as dt
                            with SyncSession(_db_engine) as db_close:
                                asset_close = db_close.query(Asset).filter_by(symbol=tp_symbol).first()
                                if not asset_close:
                                    asset_close = db_close.query(Asset).filter_by(symbol=sym).first()
                                if asset_close:
                                    for pos_db in db_close.query(Position).filter_by(
                                        asset_id=asset_close.id, status=PositionStatus.OPEN
                                    ).all():
                                        pos_db.status = PositionStatus.CLOSED
                                        pos_db.closed_at = dt.utcnow()
                                        pos_db.exit_price = current
                                        pos_db.pnl = round(pnl, 2)
                                    db_close.commit()
                        except Exception as e:
                            logger.error(f"[TP/SL] Erreur fermeture BDD IBKR {tp_symbol}: {e}")

                        # Apprentissage
                        try:
                            from backend.modules.learning.adaptive_engine import record_trade_result
                            pnl_pct = ((current / entry) - 1) * 100 if direction == "LONG" else ((entry / current) - 1) * 100
                            record_trade_result(symbol=tp_symbol, strategy="auto", direction=direction, pnl=pnl, pnl_pct=pnl_pct)
                        except Exception as e:
                            logger.warning(f"[TP/SL] Erreur apprentissage IBKR {tp_symbol}: {e}")
                    except Exception as e:
                        logger.warning(f"[TP/SL] IBKR erreur fermeture {sym}: {e}")

                # Déconnexion propre
                try:
                    ib.disconnect()
                except Exception:
                    pass
                loop.close()
                return results

            try:
                with cf.ThreadPoolExecutor() as ex:
                    ibkr_closed = ex.submit(_monitor_ibkr).result(timeout=90)
            except Exception as e:
                logger.warning(f"[TP/SL] IBKR monitor erreur (timeout 90s): {e}")
    except Exception as e:
        logger.warning(f"[TP/SL] Erreur monitoring IBKR: {e}")

    return {
        "checked": checked,
        "closed": closed,
        "ibkr_closed": ibkr_closed,
        "queue_filled": queue_filled,
        "message": f"{len(closed)} fermées, {len(ibkr_closed)} IBKR fermées, {len(queue_filled)} ouvertes",
        "checked_at": datetime.utcnow().isoformat(),
    }
