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
LOSS_THRESHOLD_PCT = -5.0           # Perte > -5% = candidat à fermer
LOSS_CRITICAL_PCT = -8.0            # Perte > -8% = fermeture forcée
SCANNER_LOW_LONG = 45               # LONG avec scanner < 45 = baissier contre nous
SCANNER_HIGH_SHORT = 60             # SHORT avec scanner > 60 = haussier contre nous
TECH_LOW = 40                       # Tech < 40 = technique défavorable
INVERSE_SIGNAL_MIN_SCORE = 65       # Signal inverse avec score >= 65 = retournement confirmé

# Protection des gagnants
PROTECT_PROFIT_PCT = 3.0            # Ne jamais fermer une position en profit > +3%


# ─────────────────────── DÉTECTION FATIGUÉS ───────────────────────

def is_position_fatigued(
    symbol: str, direction: str, pnl_pct: float,
    scanner_score: float, tech_score: float,
    inverse_signal_score: float | None = None,
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

    # 4. Analyser et fermer les fatigués
    logger.info(f"[REPOSITION] Analyse de {len(alpaca_positions)} positions Alpaca")

    for pos in alpaca_positions:
        sym = pos["symbol"]
        direction = pos["direction"]
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
            sym, direction, pnl_pct, scanner_score, tech_score, inverse_score
        )

        if fatigued:
            try:
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
    # Re-récupérer positions après les fermetures
    try:
        alpaca_positions = alpaca_broker.get_positions()
        alpaca_syms_after = {p["symbol"] for p in alpaca_positions}
    except Exception:
        alpaca_syms_after = alpaca_syms

    # Compter les slots disponibles
    from backend.modules.execution.position_manager_v2 import MAX_POSITIONS_ALPACA
    slots_available = MAX_POSITIONS_ALPACA - len(alpaca_syms_after)

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

    result["finished_at"] = datetime.utcnow().isoformat()
    result["summary"] = {
        "closed_count": len(result["closed"]),
        "opened_count": len(result["opened"]),
        "skipped_count": len(result["skipped"]),
        "errors_count": len(result["errors"]),
    }

    logger.info(
        f"[REPOSITION] Terminé — "
        f"Fermé: {len(result['closed'])}, Ouvert: {len(result['opened'])}, "
        f"Gardé: {len(result['skipped'])}, Erreurs: {len(result['errors'])}"
    )

    return result
