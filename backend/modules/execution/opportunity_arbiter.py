"""Opportunity Arbiter — Arbitrage d'Opportunité entre positions et signaux GO

Concept : chaque position ouverte et chaque signal GO reçoit un score
d'Espérance de Valeur par Jour (EV/jour). Les positions dont l'EV/jour
est inférieure aux signaux en attente sont des candidats au swap.

EV/jour = (potentiel_restant × probabilité) / temps_estimé

Métriques par position :
- Potentiel restant : distance au TP en %
- Santé : exhaustion score (momentum, volume, RSI, narrative)
- Vélocité : vitesse de progression (rendement/jour depuis l'entrée)
- Friction : coût du swap (spread + commission estimée)

Métriques par signal GO :
- Score V2 : qualité du signal
- Potentiel estimé : distance entry → TP estimé
- Santé pré-entrée : pas déjà suracheté ?
- Fraîcheur : signal détecté récemment vs il y a longtemps

Le résultat : un classement unifié positions + signaux, trié par EV/jour.
Si un signal est au-dessus d'une position → swap recommandé.
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from backend.database.models import Asset, Position, PositionStatus, OHLCVDaily
from backend.modules.execution.exhaustion_checker import check_position_health

logger = logging.getLogger("tradepilot.opportunity_arbiter")

SWAP_FRICTION_PCT = 0.3  # Coût estimé d'un swap (spread + commission aller-retour)


def _compute_atr(db: Session, asset_id: int) -> float:
    """ATR 14 jours."""
    import pandas as pd
    rows = db.query(OHLCVDaily).filter_by(asset_id=asset_id).order_by(OHLCVDaily.date.desc()).limit(20).all()
    if len(rows) < 14:
        return 0
    highs = pd.Series([float(r.high) for r in reversed(rows)])
    lows = pd.Series([float(r.low) for r in reversed(rows)])
    closes = pd.Series([float(r.close) for r in reversed(rows)])
    tr = pd.concat([highs - lows, (highs - closes.shift(1)).abs(), (lows - closes.shift(1)).abs()], axis=1).max(axis=1)
    return float(tr.iloc[-14:].mean())


def evaluate_position(db: Session, position: Position, current_price: float) -> dict:
    """Évalue l'EV/jour d'une position ouverte."""
    asset = db.query(Asset).filter_by(id=position.asset_id).first()
    if not asset:
        return None

    entry = float(position.entry_price)
    qty = float(position.quantity)
    direction = position.direction.value
    tp = float(position.take_profit) if position.take_profit else None
    sl = float(position.stop_loss) if position.stop_loss else None

    # P&L actuel
    if direction == "LONG":
        pnl_pct = (current_price / entry - 1) * 100
        remaining_to_tp = ((tp / current_price - 1) * 100) if tp else 0
        remaining_to_sl = ((current_price / sl - 1) * 100) if sl else 0
    else:
        pnl_pct = (1 - current_price / entry) * 100
        remaining_to_tp = ((1 - tp / current_price) * 100) if tp else 0
        remaining_to_sl = ((1 - sl / current_price) * 100) if sl else 0

    # Santé (exhaustion)
    health = check_position_health(db, asset.symbol, direction, entry)
    health_score = health["score"]

    # Vélocité : rendement par jour depuis l'entrée
    days_held = 1
    if position.opened_at:
        delta = datetime.utcnow() - position.opened_at
        days_held = max(1, delta.days + delta.seconds / 86400)
    velocity = pnl_pct / days_held

    # Probabilité de succès basée sur la santé
    # Santé 80 → 70% de chances d'atteindre le TP
    # Santé 40 → 30% de chances
    prob_tp = min(0.85, max(0.15, health_score / 100 * 0.9))

    # Risque : probabilité de toucher le SL
    prob_sl = 1 - prob_tp

    # EV = (gain_potentiel × prob_gain) - (perte_potentielle × prob_perte)
    ev_pct = (remaining_to_tp * prob_tp) - (remaining_to_sl * prob_sl)

    # Temps estimé pour atteindre le TP (basé sur la vélocité actuelle)
    if velocity > 0 and remaining_to_tp > 0:
        days_to_tp = remaining_to_tp / velocity
    else:
        days_to_tp = 30  # Fallback conservateur

    days_to_tp = max(1, min(days_to_tp, 60))

    # EV par jour
    ev_per_day = ev_pct / days_to_tp

    # Signaux d'alerte
    alerts = []
    if health_score < 50:
        alerts.append("Essoufflé")
    if velocity < 0:
        alerts.append("Recule")
    if remaining_to_tp < 2:
        alerts.append("Proche TP")
    if pnl_pct < -5:
        alerts.append("Perte significative")

    return {
        "type": "POSITION",
        "symbol": asset.symbol,
        "direction": direction,
        "entry_price": round(entry, 2),
        "current_price": round(current_price, 2),
        "quantity": qty,
        "pnl_pct": round(pnl_pct, 2),
        "days_held": round(days_held, 1),
        "velocity": round(velocity, 3),
        "health_score": health_score,
        "remaining_to_tp_pct": round(remaining_to_tp, 2),
        "remaining_to_sl_pct": round(remaining_to_sl, 2),
        "prob_tp": round(prob_tp * 100, 1),
        "ev_pct": round(ev_pct, 3),
        "ev_per_day": round(ev_per_day, 3),
        "days_to_tp_est": round(days_to_tp, 1),
        "alerts": alerts,
        "health_signals": health["signals"],
    }


def evaluate_signal(db: Session, signal: dict) -> dict:
    """Évalue l'EV/jour d'un signal GO."""
    symbol = signal.get("symbol", "")
    score = signal.get("thesis_score", signal.get("score", 50))

    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return None

    last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
    if not last:
        return None

    entry_price = float(last.close)
    atr_val = _compute_atr(db, asset.id)
    if atr_val == 0:
        return None

    # SL/TP estimés
    tp = entry_price + 3 * atr_val
    sl = entry_price - 2 * atr_val
    remaining_to_tp = (tp / entry_price - 1) * 100
    remaining_to_sl = (entry_price / sl - 1) * 100 if sl > 0 else 10

    # Santé pré-entrée
    health = check_position_health(db, symbol, "LONG", entry_price)
    health_score = health["score"]

    # Probabilité basée sur score V2 + santé
    score_factor = min(1.0, score / 80)
    health_factor = min(1.0, health_score / 80)
    prob_tp = min(0.80, max(0.20, (score_factor * 0.6 + health_factor * 0.4) * 0.85))

    prob_sl = 1 - prob_tp

    # EV
    ev_pct = (remaining_to_tp * prob_tp) - (remaining_to_sl * prob_sl) - SWAP_FRICTION_PCT

    # Temps estimé basé sur l'ATR (plus volatile = plus rapide)
    atr_pct = atr_val / entry_price * 100
    days_to_tp = max(2, min(30, remaining_to_tp / max(atr_pct * 0.5, 0.1)))

    ev_per_day = ev_pct / days_to_tp

    return {
        "type": "SIGNAL_GO",
        "symbol": symbol,
        "direction": signal.get("direction", "LONG"),
        "entry_price": round(entry_price, 2),
        "current_price": round(entry_price, 2),
        "score_v2": round(score, 1),
        "health_score": health_score,
        "remaining_to_tp_pct": round(remaining_to_tp, 2),
        "remaining_to_sl_pct": round(remaining_to_sl, 2),
        "prob_tp": round(prob_tp * 100, 1),
        "ev_pct": round(ev_pct, 3),
        "ev_per_day": round(ev_per_day, 3),
        "days_to_tp_est": round(days_to_tp, 1),
        "swap_cost_pct": SWAP_FRICTION_PCT,
        "health_signals": health["signals"],
    }


def run_opportunity_arbitrage(db: Session) -> dict:
    """Compare toutes les positions IBKR vs tous les signaux GO.

    Retourne un classement unifié trié par EV/jour décroissant,
    avec les swaps recommandés.
    """
    import json
    from pathlib import Path
    from backend.database.models import Order

    # 1. Positions IBKR ouvertes
    ibkr_asset_ids = set()
    for o in db.query(Order).filter_by(broker="ibkr").all():
        ibkr_asset_ids.add(o.asset_id)

    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    ibkr_positions = [p for p in positions if p.asset_id in ibkr_asset_ids and float(p.quantity) <= 50]

    # 2. Signaux GO
    signals = []
    try:
        signals = json.loads(Path("data/signals_cache.json").read_text())
    except Exception:
        pass

    # Symboles déjà en position IBKR
    ibkr_symbols = set()
    for p in ibkr_positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if asset:
            ibkr_symbols.add(asset.symbol)

    # 3. Évaluer chaque position IBKR
    evaluated = []
    for p in ibkr_positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if not asset:
            continue
        last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
        current_price = float(last.close) if last else float(p.entry_price)

        ev = evaluate_position(db, p, current_price)
        if ev:
            evaluated.append(ev)

    # 4. Évaluer chaque signal GO (pas déjà en position IBKR)
    for sig in signals:
        if sig.get("symbol") in ibkr_symbols:
            continue
        ev = evaluate_signal(db, sig)
        if ev:
            evaluated.append(ev)

    # 5. Trier par EV/jour décroissant
    evaluated.sort(key=lambda x: x["ev_per_day"], reverse=True)

    # 6. Identifier les swaps recommandés
    swaps = []
    worst_positions = [e for e in evaluated if e["type"] == "POSITION"]
    best_signals = [e for e in evaluated if e["type"] == "SIGNAL_GO"]

    if worst_positions and best_signals:
        # La pire position vs le meilleur signal
        for pos in reversed(worst_positions):
            for sig in best_signals:
                if sig["ev_per_day"] > pos["ev_per_day"] + 0.1:  # Marge de 0.1 pour éviter le churn
                    gain_ev = round(sig["ev_per_day"] - pos["ev_per_day"], 3)
                    swaps.append({
                        "close": pos["symbol"],
                        "close_ev_day": pos["ev_per_day"],
                        "close_health": pos["health_score"],
                        "close_pnl_pct": pos["pnl_pct"],
                        "open": sig["symbol"],
                        "open_ev_day": sig["ev_per_day"],
                        "open_score": sig["score_v2"],
                        "open_health": sig["health_score"],
                        "ev_gain_per_day": gain_ev,
                        "rationale": f"Fermer {pos['symbol']} (EV/j={pos['ev_per_day']:.3f}, santé={pos['health_score']}) → Ouvrir {sig['symbol']} (EV/j={sig['ev_per_day']:.3f}, score={sig['score_v2']:.0f})",
                    })
                    break  # Un swap par position max

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "ibkr_positions": len(ibkr_positions),
        "signals_go": len([s for s in signals if s.get("symbol") not in ibkr_symbols]),
        "ranking": evaluated,
        "swaps_recommended": swaps,
        "summary": {
            "best_position": evaluated[0] if evaluated and evaluated[0]["type"] == "POSITION" else None,
            "worst_position": worst_positions[-1] if worst_positions else None,
            "best_signal": best_signals[0] if best_signals else None,
            "n_swaps": len(swaps),
        },
    }
