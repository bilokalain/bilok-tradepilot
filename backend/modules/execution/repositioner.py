"""Module de repositionnement — étape finale du pipeline.

Compare les GO du jour avec les positions ouvertes.
Ferme les positions fatiguées (perte + scanner faiblissant + signal inverse).
Ouvre les positions pour les nouveaux GO non couverts.

Appelé à la fin du pipeline complet, après run_performance.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger("tradepilot.repositioner")


# ─────────────────────── CONFIGURATION ───────────────────────

# Seuils de détection "fatigué"
LOSS_THRESHOLD_PCT = -3.0           # Perte > -3% = candidat à fermer (assoupli de -5)
LOSS_CRITICAL_PCT = -8.0            # Perte > -8% = fermeture forcée
SCANNER_LOW_LONG = 55               # LONG avec scanner < 55 = perd son edge (assoupli de 45)
SCANNER_HIGH_SHORT = 55             # SHORT avec scanner > 55 = perd son edge (assoupli de 60)
TECH_LOW = 50                       # Tech < 50 = technique défavorable (assoupli de 40)
INVERSE_SIGNAL_MIN_SCORE = 65       # Signal inverse avec score >= 65 = retournement confirmé

# Rotation par OPPORTUNITÉ (nouveau)
OPPORTUNITY_GAP = 10                # Position à fermer si score_GO - scanner_position >= 10

# Protection des gagnants
PROTECT_PROFIT_PCT = 3.0            # Ne jamais fermer une position en profit > +3%


# ─────────────────────── DÉTECTION FATIGUÉS ───────────────────────

def is_position_fatigued(
    symbol: str, direction: str, pnl_pct: float,
    scanner_score: float, tech_score: float,
    inverse_signal_score: float | None = None,
    worst_go_score: float | None = None,
) -> tuple[bool, list[str]]:
    """Détermine si une position est "fatiguée" (à fermer).

    Returns: (is_fatigued, reasons)
    """
    reasons = []

    # Protection : position en bon profit = NE PAS fermer
    if pnl_pct >= PROTECT_PROFIT_PCT:
        return False, []

    # Perte critique : fermeture forcée
    if pnl_pct <= LOSS_CRITICAL_PCT:
        reasons.append(f"perte critique ({pnl_pct:.1f}%)")
        return True, reasons

    # Scanner contre nous
    if direction == "LONG" and scanner_score < SCANNER_LOW_LONG:
        reasons.append(f"scanner baissier ({scanner_score:.0f})")
    elif direction == "SHORT" and scanner_score > SCANNER_HIGH_SHORT:
        reasons.append(f"scanner haussier ({scanner_score:.0f})")

    # Tech faible
    if direction == "LONG" and tech_score < TECH_LOW:
        reasons.append(f"tech faible ({tech_score:.0f})")

    # Perte modérée + raisons scanner
    if pnl_pct <= LOSS_THRESHOLD_PCT and reasons:
        return True, [f"perte {pnl_pct:.1f}%"] + reasons

    # RÈGLE D'OPPORTUNITÉ : perte quelconque + position nettement inférieure au pire GO
    # → on libère pour ouvrir un meilleur signal
    if pnl_pct < 0 and worst_go_score is not None and scanner_score + OPPORTUNITY_GAP < worst_go_score:
        gap = worst_go_score - scanner_score
        reasons.append(f"opportunité : GO disponibles ont +{gap:.0f} vs scanner position ({scanner_score:.0f})")
        return True, [f"perte {pnl_pct:.1f}%"] + reasons

    # Signal inverse fort
    if inverse_signal_score is not None and inverse_signal_score >= INVERSE_SIGNAL_MIN_SCORE:
        reasons.append(f"signal inverse fort ({inverse_signal_score:.0f})")
        return True, reasons

    return False, reasons


# ─────────────────────── REPOSITIONNEMENT ───────────────────────

def run_repositioning(db: Session) -> dict:
    """Exécute le repositionnement : ferme les fatigués + ouvre les nouveaux GO.

    Étapes :
    1. Charger signaux GO du jour + cache scanner
    2. Récupérer positions Alpaca live
    3. Analyser chaque position (fatigué ou pas)
    4. Fermer les fatigués (sauf si gain > +3%)
    5. Ouvrir les nouveaux GO non couverts
    """
    from backend.modules.execution.broker_alpaca import alpaca_broker
    from backend.database.models import Position, PositionStatus, Asset

    result = {
        "started_at": datetime.utcnow().isoformat(),
        "closed": [],
        "opened": [],
        "skipped": [],
        "errors": [],
    }

    if not alpaca_broker.is_configured:
        result["error"] = "Alpaca non configuré"
        return result

    # 1. Charger signaux GO
    try:
        fp = Path("data/signals_cache.json")
        if not fp.exists():
            result["error"] = "Aucun signal cache trouvé"
            return result
        raw = json.loads(fp.read_text())
        signals = raw if isinstance(raw, list) else raw.get("signals", raw.get("data", []))
        go_signals = [s for s in signals if s.get("action") == "GO"]
        go_by_sym = {s["symbol"]: s for s in go_signals}
    except Exception as e:
        result["error"] = f"Erreur lecture signaux : {e}"
        return result

    # 2. Charger cache scanner
    scanner = {}
    try:
        fp_s = Path("data/scanner_cache.json")
        if fp_s.exists():
            scanner = {r["symbol"]: r for r in json.loads(fp_s.read_text()).get("results", [])}
    except Exception as e:
        logger.warning(f"[REPOSITION] Scanner cache indispo: {e}")

    # 3. Positions Alpaca live
    try:
        alpaca_positions = alpaca_broker.get_positions()
    except Exception as e:
        result["error"] = f"Erreur Alpaca positions : {e}"
        return result

    alpaca_syms = {p["symbol"] for p in alpaca_positions}

    # Calculer le "worst GO score" pour la règle d'opportunité
    worst_go_score = None
    if go_signals:
        go_scores = [s.get("score_v2", s.get("score", 0)) for s in go_signals]
        worst_go_score = min(go_scores) if go_scores else None
        logger.info(f"[REPOSITION] GO scores : min={min(go_scores):.1f}, max={max(go_scores):.1f}")

    # 4. Analyser et fermer les fatigués
    logger.info(f"[REPOSITION] Analyse de {len(alpaca_positions)} positions Alpaca")

    for pos in alpaca_positions:
        sym = pos["symbol"]
        side = pos.get("side", "long")
        direction = "LONG" if side.lower() == "long" else "SHORT"
        pnl_pct = float(pos.get("pnl_pct", 0))

        sc = scanner.get(sym, {})
        scanner_score = sc.get("scores", {}).get("final", 50)
        tech_score = sc.get("scores", {}).get("technical", 50)

        # Signal inverse ?
        inverse_score = None
        new_sig = go_by_sym.get(sym)
        if new_sig and new_sig.get("direction") != direction:
            inverse_score = new_sig.get("score_v2", new_sig.get("score", 0))

        fatigued, reasons = is_position_fatigued(
            sym, direction, pnl_pct, scanner_score, tech_score, inverse_score,
            worst_go_score=worst_go_score,
        )

        if fatigued:
            try:
                # Annuler d'abord les ordres pending (OCO/brackets) qui bloquent la qty
                try:
                    from alpaca.trading.client import TradingClient
                    from alpaca.trading.requests import GetOrdersRequest
                    from alpaca.trading.enums import QueryOrderStatus
                    from backend.config.settings import settings
                    client = TradingClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY, paper=True)
                    pending = client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN, symbols=[sym], limit=20))
                    for o in pending:
                        try: client.cancel_order_by_id(o.id)
                        except: pass
                    import time; time.sleep(1)  # laisser propager
                except Exception as e:
                    logger.debug(f"[REPOSITION] Cancel pending {sym} échoué: {e}")

                close_res = alpaca_broker.close_position(sym)
                if close_res and "error" not in close_res:
                    # Fermer en BDD
                    asset = db.query(Asset).filter_by(symbol=sym).first()
                    if asset:
                        for p in db.query(Position).filter_by(
                            asset_id=asset.id, status=PositionStatus.OPEN
                        ).all():
                            p.status = PositionStatus.CLOSED
                            p.closed_at = datetime.utcnow()
                        db.commit()
                    result["closed"].append({
                        "symbol": sym, "direction": direction,
                        "pnl_pct": pnl_pct, "reasons": reasons,
                    })
                    logger.info(f"[REPOSITION] Fermé {sym} {direction} pnl={pnl_pct:.1f}% — {', '.join(reasons)}")
                else:
                    err = close_res.get("error", "unknown") if close_res else "no response"
                    result["errors"].append(f"Close {sym}: {err}")
            except Exception as e:
                result["errors"].append(f"Close {sym}: {e}")
        else:
            result["skipped"].append({
                "symbol": sym, "direction": direction,
                "pnl_pct": pnl_pct, "reason": "gardée (pas fatiguée)",
            })

    # 5. Ouvrir les nouveaux GO non couverts
    # Attendre que les fermetures se propagent avant de recompter
    if result["closed"]:
        import time
        time.sleep(3)

    try:
        alpaca_positions = alpaca_broker.get_positions()
        alpaca_syms_after = {p["symbol"] for p in alpaca_positions}
    except Exception:
        alpaca_syms_after = alpaca_syms

    # Compter les slots disponibles — basé sur le REAL post-close count
    from backend.modules.execution.position_manager_v2 import MAX_POSITIONS_ALPACA
    # Si on vient de fermer N positions, on a au moins N slots libres
    closed_count = len(result["closed"])
    slots_available = max(MAX_POSITIONS_ALPACA - len(alpaca_syms_after), closed_count)

    if slots_available <= 0:
        result["opened_skipped"] = f"Slots Alpaca pleins ({len(alpaca_syms_after)}/{MAX_POSITIONS_ALPACA})"
        logger.info(f"[REPOSITION] Slots Alpaca pleins — pas d'ouverture")
    else:
        # Prendre les top GO non déjà en position
        gos_to_open = [s for s in go_signals if s["symbol"] not in alpaca_syms_after]
        gos_to_open.sort(key=lambda x: x.get("score_v2", x.get("score", 0)), reverse=True)
        gos_to_open = gos_to_open[:slots_available]

        logger.info(f"[REPOSITION] Tentative ouverture {len(gos_to_open)} nouveaux GO (slots={slots_available})")

        # Appeler execute_all via le même endpoint (capital = buying_power disponible)
        try:
            account = alpaca_broker.get_account() if hasattr(alpaca_broker, 'get_account') else None
            capital = float(account.get("buying_power", 20000)) if account else 20000
        except Exception:
            capital = 20000

        # Per-position sizing : buying_power / nb_go
        per_position = min(capital / max(len(gos_to_open), 1), capital * 0.10)

        for sig in gos_to_open:
            sym = sig["symbol"]
            direction = sig["direction"]
            try:
                from backend.modules.execution.router import _place_bracket_order, _get_price_and_atr
                asset = db.query(Asset).filter_by(symbol=sym).first()
                if not asset:
                    result["errors"].append(f"Open {sym}: asset non trouvé")
                    continue

                entry_price, atr_val = _get_price_and_atr(db, asset.id)
                if not entry_price or not atr_val:
                    result["errors"].append(f"Open {sym}: pas de données OHLCV")
                    continue

                # SL/TP via ATR 2x/3x
                if direction == "LONG":
                    sl = round(entry_price - 2 * atr_val, 2)
                    tp = round(entry_price + 3 * atr_val, 2)
                else:
                    sl = round(entry_price + 2 * atr_val, 2)
                    tp = round(entry_price - 3 * atr_val, 2)

                qty = max(1, int(per_position / entry_price))

                bracket_res = _place_bracket_order(
                    sym, "buy" if direction == "LONG" else "sell",
                    float(qty), sl, tp,
                )
                if "error" in bracket_res:
                    result["errors"].append(f"Open {sym}: {bracket_res['error']}")
                    continue

                # Enregistrer en BDD
                from backend.database.models import Order, SignalDirection, PositionStatus
                from backend.database.models import OrderSide as DBOrderSide, OrderStatus as DBOrderStatus
                db.add(Order(
                    asset_id=asset.id,
                    side=DBOrderSide.BUY if direction == "LONG" else DBOrderSide.SELL,
                    quantity=float(qty), price=entry_price, filled_price=entry_price,
                    status=DBOrderStatus.FILLED, tranche=1, broker="alpaca_bracket",
                ))
                db.add(Position(
                    asset_id=asset.id,
                    direction=SignalDirection.LONG if direction == "LONG" else SignalDirection.SHORT,
                    entry_price=entry_price, quantity=float(qty),
                    stop_loss=sl, take_profit=tp, status=PositionStatus.OPEN,
                ))
                db.commit()

                result["opened"].append({
                    "symbol": sym, "direction": direction,
                    "score": sig.get("score_v2", sig.get("score", 0)),
                    "qty": qty, "entry": entry_price, "sl": sl, "tp": tp,
                })
                logger.info(f"[REPOSITION] Ouvert {sym} {direction} × {qty} @ ${entry_price}")
            except Exception as e:
                logger.warning(f"[REPOSITION] Erreur ouverture {sym}: {e}")
                result["errors"].append(f"Open {sym}: {str(e)[:100]}")

    # ═════════════════════════════════════════════════════════════
    # 6. PHASE REBALANCE — rééquilibrage LONG/SHORT
    # ═════════════════════════════════════════════════════════════
    result["rebalance"] = _auto_rebalance(db, go_signals, scanner)

    result["finished_at"] = datetime.utcnow().isoformat()
    result["summary"] = {
        "closed_count": len(result["closed"]),
        "opened_count": len(result["opened"]),
        "skipped_count": len(result["skipped"]),
        "errors_count": len(result["errors"]),
        "rebalance_closed": len(result["rebalance"].get("closed", [])),
        "rebalance_opened": len(result["rebalance"].get("opened", [])),
    }

    logger.info(
        f"[REPOSITION] Terminé — "
        f"Fermé: {len(result['closed'])}, Ouvert: {len(result['opened'])}, "
        f"Rebal-Fermé: {len(result['rebalance'].get('closed', []))}, "
        f"Rebal-Ouvert: {len(result['rebalance'].get('opened', []))}, "
        f"Erreurs: {len(result['errors'])}"
    )

    return result


# ─────────────────────── REBALANCE LONG/SHORT ───────────────────────

# Cibles de risque
REBAL_NET_MAX_PCT = 80        # Si net > 80% equity → rebalance forcé
REBAL_SHORT_MIN_RATIO = 0.20  # Si < 20% du gross en SHORT → ouvrir SHORT
REBAL_MAX_CLOSURES = 3        # Max 3 fermetures par cycle de rebalance (progressif)
REBAL_MAX_OPENINGS = 3        # Max 3 ouvertures SHORT par cycle


def _auto_rebalance(db: Session, go_signals: list, scanner: dict) -> dict:
    """Rééquilibrage automatique LONG/SHORT basé sur l'exposition nette.

    Si net exposure > seuil critique :
    1. Ferme les LONG les plus faibles (bas scanner + faible profit)
    2. Ouvre les meilleurs GO SHORT disponibles
    """
    out = {"closed": [], "opened": [], "errors": [], "triggered": False}

    try:
        from backend.modules.execution.broker_alpaca import alpaca_broker
        from backend.database.models import Asset, Position, PositionStatus
        from backend.database.models import Order, SignalDirection
        from backend.database.models import OrderSide as DBOrderSide, OrderStatus as DBOrderStatus

        positions = alpaca_broker.get_positions()
        if not positions:
            return out

        # Calculer expositions
        long_pos = [p for p in positions if p.get("side", "long").lower() == "long"]
        short_pos = [p for p in positions if p.get("side", "long").lower() != "long"]
        long_mv = sum(abs(float(p.get("market_value", 0))) for p in long_pos)
        short_mv = sum(abs(float(p.get("market_value", 0))) for p in short_pos)
        gross = long_mv + short_mv
        net = long_mv - short_mv

        account = alpaca_broker.get_account()
        equity = float(account.get("equity", 100_000)) if account else 100_000

        net_pct = (net / equity * 100) if equity else 0
        short_ratio = (short_mv / gross) if gross else 0

        out["metrics"] = {
            "net_pct": round(net_pct, 1),
            "short_ratio": round(short_ratio, 3),
            "gross_mv": round(gross, 0),
            "net_mv": round(net, 0),
        }

        need_rebalance = net_pct > REBAL_NET_MAX_PCT or short_ratio < REBAL_SHORT_MIN_RATIO
        if not need_rebalance:
            logger.info(f"[REBAL] Pas de rebalance nécessaire (net={net_pct:.0f}%, short_ratio={short_ratio*100:.0f}%)")
            return out

        out["triggered"] = True
        logger.info(
            f"[REBAL] DÉCLENCHÉ — net={net_pct:.0f}% (max {REBAL_NET_MAX_PCT}), "
            f"short_ratio={short_ratio*100:.0f}% (min {REBAL_SHORT_MIN_RATIO*100:.0f}%)"
        )

        # 1. FERMER les LONG les plus faibles (bas scanner + faible profit/perte légère)
        #    Protection : jamais de gain > PROTECT_PROFIT_PCT
        candidates_close = []
        for p in long_pos:
            sym = p["symbol"]
            pnl_pct = float(p.get("pnl_pct", 0))
            if pnl_pct >= PROTECT_PROFIT_PCT:
                continue
            sc = scanner.get(sym, {})
            score = sc.get("scores", {}).get("final", 50)
            candidates_close.append((sym, score, pnl_pct, abs(float(p.get("market_value", 0)))))

        # Trier : scanner ASC (pires d'abord), puis pnl ASC
        candidates_close.sort(key=lambda x: (x[1], x[2]))

        closed_here = 0
        for sym, score, pnl_pct, mv in candidates_close[:REBAL_MAX_CLOSURES]:
            # Annuler tous les ordres pending (OCO/brackets) qui retiennent la qty
            try:
                from alpaca.trading.client import TradingClient
                from alpaca.trading.requests import GetOrdersRequest
                from alpaca.trading.enums import QueryOrderStatus
                from backend.config.settings import settings
                client = TradingClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY, paper=True)
                pending = client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN, symbols=[sym], limit=20))
                cancelled_n = 0
                for o in pending:
                    try:
                        client.cancel_order_by_id(o.id)
                        cancelled_n += 1
                    except: pass
                if cancelled_n:
                    import time; time.sleep(3)  # laisser propager (OCO peut être lent)
            except Exception as e:
                logger.debug(f"[REBAL] Cancel pending {sym} échoué: {e}")

            # Retry close_position : 1ère tentative + 1 retry après wait
            close_res = alpaca_broker.close_position(sym)
            if not close_res or "error" in (close_res or {}):
                # Retry après 3s supplémentaires (au cas où OCO pas encore annulés)
                import time; time.sleep(3)
                close_res = alpaca_broker.close_position(sym)

            if close_res and "error" not in close_res:
                asset = db.query(Asset).filter_by(symbol=sym).first()
                if asset:
                    for po in db.query(Position).filter_by(asset_id=asset.id, status=PositionStatus.OPEN).all():
                        po.status = PositionStatus.CLOSED
                        po.closed_at = datetime.utcnow()
                    db.commit()
                out["closed"].append({
                    "symbol": sym, "direction": "LONG",
                    "pnl_pct": round(pnl_pct, 2), "scanner": round(score, 1),
                    "mv_usd": round(mv, 0),
                    "reason": f"rebalance LONG (scanner {score:.0f}, pnl {pnl_pct:+.1f}%)",
                })
                logger.info(f"[REBAL] Fermé LONG {sym} scanner={score:.0f} pnl={pnl_pct:.1f}%")
                closed_here += 1
            else:
                err = close_res.get("error", "unknown") if close_res else "no response"
                out["errors"].append(f"Rebal close {sym}: {err}")

        # 2. OUVRIR les meilleurs GO SHORT
        if closed_here > 0:
            import time; time.sleep(3)  # laisser propager

        # Symboles déjà pris
        alpaca_syms_now = {p["symbol"] for p in alpaca_broker.get_positions()}
        go_shorts = sorted(
            [s for s in go_signals if s.get("direction") == "SHORT" and s["symbol"] not in alpaca_syms_now],
            key=lambda x: -x.get("score_v2", x.get("score", 0))
        )[:REBAL_MAX_OPENINGS]

        if not go_shorts:
            logger.info("[REBAL] Aucun GO SHORT disponible")
            return out

        # Sizing : répartir le capital libéré
        capital_freed = sum(c["mv_usd"] for c in out["closed"])
        per_position = max(capital_freed / max(len(go_shorts), 1), 1000)  # min $1000
        per_position = min(per_position, equity * 0.05)  # max 5% equity

        for sig in go_shorts:
            sym = sig["symbol"]
            try:
                from backend.modules.execution.router import _place_bracket_order, _get_price_and_atr
                asset = db.query(Asset).filter_by(symbol=sym).first()
                if not asset:
                    out["errors"].append(f"Rebal open {sym}: asset non trouvé")
                    continue

                entry_price, atr_val = _get_price_and_atr(db, asset.id)
                if not entry_price or not atr_val:
                    out["errors"].append(f"Rebal open {sym}: pas de données OHLCV")
                    continue

                # SHORT : SL > entry, TP < entry
                sl = round(entry_price + 2 * atr_val, 2)
                tp = round(entry_price - 3 * atr_val, 2)

                qty = max(1, int(per_position / entry_price))

                bracket_res = _place_bracket_order(sym, "sell", float(qty), sl, tp)
                if "error" in bracket_res:
                    out["errors"].append(f"Rebal open {sym}: {bracket_res['error']}")
                    continue

                db.add(Order(
                    asset_id=asset.id, side=DBOrderSide.SELL,
                    quantity=float(qty), price=entry_price, filled_price=entry_price,
                    status=DBOrderStatus.FILLED, tranche=1, broker="alpaca_bracket",
                ))
                db.add(Position(
                    asset_id=asset.id, direction=SignalDirection.SHORT,
                    entry_price=entry_price, quantity=float(qty),
                    stop_loss=sl, take_profit=tp, status=PositionStatus.OPEN,
                ))
                db.commit()

                out["opened"].append({
                    "symbol": sym, "direction": "SHORT",
                    "score": sig.get("score_v2", sig.get("score", 0)),
                    "qty": qty, "entry": entry_price, "sl": sl, "tp": tp,
                })
                logger.info(f"[REBAL] Ouvert SHORT {sym} × {qty} @ ${entry_price}")
            except Exception as e:
                out["errors"].append(f"Rebal open {sym}: {str(e)[:100]}")
                logger.warning(f"[REBAL] Erreur ouverture {sym}: {e}")

    except Exception as e:
        logger.error(f"[REBAL] Erreur globale: {e}")
        out["errors"].append(f"Rebalance global: {e}")

    return out
