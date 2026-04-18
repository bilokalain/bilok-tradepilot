"""Exhaustion Checker — Détecte les trades qui s'essoufflent

Un trade s'essouffle quand :
1. Le momentum ralentit (vitesse de progression diminue)
2. Le volume sèche (plus personne ne pousse)
3. Le Narrative score chute (la narrative est épuisée)
4. Le RSI entre en zone extrême (suracheté/survendu)
5. Le P/L stagne depuis plusieurs jours

Niveaux :
- FORT    : Le trade a encore du jus — garder
- MODÉRÉ  : Ça ralentit — resserrer le trailing stop
- FAIBLE  : Essoufflé — considérer la fermeture
- ÉPUISÉ  : Le mouvement est fini — fermer
"""

import logging
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from backend.database.models import Asset, Position, PositionStatus, OHLCVDaily

logger = logging.getLogger("tradepilot.exhaustion")


def check_position_health(db: Session, symbol: str, direction: str,
                           entry_price: float) -> dict:
    """Évalue la santé d'une position ouverte."""
    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return {"score": 50, "level": "MODÉRÉ", "signals": []}

    rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(
        OHLCVDaily.date.desc()).limit(60).all()
    if len(rows) < 20:
        return {"score": 50, "level": "MODÉRÉ", "signals": []}

    close = pd.Series([float(r.close) for r in reversed(rows)])
    high = pd.Series([float(r.high) for r in reversed(rows)])
    low = pd.Series([float(r.low) for r in reversed(rows)])
    volume = pd.Series([float(r.volume) for r in reversed(rows)])
    current = float(close.iloc[-1])

    signals = []
    scores = []

    # 1. Momentum (rendement 5j vs 20j)
    ret_5 = float((close.iloc[-1] / close.iloc[-5] - 1) * 100) if len(close) >= 5 else 0
    ret_20 = float((close.iloc[-1] / close.iloc[-20] - 1) * 100) if len(close) >= 20 else 0

    if direction == "LONG":
        if ret_5 > 0 and ret_5 > ret_20 * 0.5:
            scores.append(80)
            signals.append({"name": "Momentum", "value": f"+{ret_5:.1f}% (5j)", "status": "FORT"})
        elif ret_5 > 0:
            scores.append(60)
            signals.append({"name": "Momentum", "value": f"+{ret_5:.1f}% (5j) ralentit", "status": "MODÉRÉ"})
        else:
            scores.append(30)
            signals.append({"name": "Momentum", "value": f"{ret_5:.1f}% (5j) négatif", "status": "FAIBLE"})
    else:  # SHORT
        if ret_5 < 0 and abs(ret_5) > abs(ret_20) * 0.5:
            scores.append(80)
            signals.append({"name": "Momentum", "value": f"{ret_5:.1f}% (5j)", "status": "FORT"})
        elif ret_5 < 0:
            scores.append(60)
            signals.append({"name": "Momentum", "value": f"{ret_5:.1f}% (5j) ralentit", "status": "MODÉRÉ"})
        else:
            scores.append(30)
            signals.append({"name": "Momentum", "value": f"+{ret_5:.1f}% (5j) contre vous", "status": "FAIBLE"})

    # 2. Volume (5j vs 20j)
    vol_5 = float(volume.iloc[-5:].mean())
    vol_20 = float(volume.iloc[-20:].mean())
    vol_ratio = vol_5 / vol_20 if vol_20 > 0 else 1

    if vol_ratio > 1.2:
        scores.append(80)
        signals.append({"name": "Volume", "value": f"{vol_ratio:.1f}x la moyenne", "status": "FORT"})
    elif vol_ratio > 0.8:
        scores.append(55)
        signals.append({"name": "Volume", "value": f"{vol_ratio:.1f}x normal", "status": "MODÉRÉ"})
    else:
        scores.append(25)
        signals.append({"name": "Volume", "value": f"{vol_ratio:.1f}x — sèche", "status": "FAIBLE"})

    # 3. Narrative Momentum
    try:
        from backend.modules.scanner.narrative import compute_narrative_score
        narrative = compute_narrative_score(close, high, low, volume)
        narr_score = narrative["score"]
        if narr_score >= 65:
            scores.append(85)
            signals.append({"name": "Narrative", "value": f"{narr_score:.0f}/100 — {narrative['signal']}", "status": "FORT"})
        elif narr_score >= 50:
            scores.append(55)
            signals.append({"name": "Narrative", "value": f"{narr_score:.0f}/100 — {narrative['signal']}", "status": "MODÉRÉ"})
        else:
            scores.append(25)
            signals.append({"name": "Narrative", "value": f"{narr_score:.0f}/100 — ÉPUISÉE", "status": "FAIBLE"})
    except Exception as e:
        logger.warning(f"[EXHAUSTION] Narrative score échoué pour {symbol}: {e}")
        scores.append(50)

    # 4. RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = float(100 - (100 / (1 + rs.iloc[-1]))) if not pd.isna(rs.iloc[-1]) else 50

    if direction == "LONG":
        if rsi > 75:
            scores.append(25)
            signals.append({"name": "RSI", "value": f"{rsi:.0f} — suracheté", "status": "FAIBLE"})
        elif rsi > 60:
            scores.append(70)
            signals.append({"name": "RSI", "value": f"{rsi:.0f} — haussier", "status": "FORT"})
        else:
            scores.append(45)
            signals.append({"name": "RSI", "value": f"{rsi:.0f} — momentum faible", "status": "MODÉRÉ"})
    else:
        if rsi < 25:
            scores.append(25)
            signals.append({"name": "RSI", "value": f"{rsi:.0f} — survendu", "status": "FAIBLE"})
        elif rsi < 40:
            scores.append(70)
            signals.append({"name": "RSI", "value": f"{rsi:.0f} — baissier", "status": "FORT"})
        else:
            scores.append(45)
            signals.append({"name": "RSI", "value": f"{rsi:.0f} — pas de pression baissière", "status": "MODÉRÉ"})

    # 5. Distance au TP/SL (progression)
    pnl_pct = ((current / entry_price) - 1) * 100 if direction == "LONG" else ((entry_price / current) - 1) * 100
    if pnl_pct > 5:
        scores.append(60)
        signals.append({"name": "P/L", "value": f"+{pnl_pct:.1f}% — beau gain", "status": "FORT"})
    elif pnl_pct > 0:
        scores.append(70)
        signals.append({"name": "P/L", "value": f"+{pnl_pct:.1f}% — en progression", "status": "FORT"})
    elif pnl_pct > -2:
        scores.append(50)
        signals.append({"name": "P/L", "value": f"{pnl_pct:.1f}% — zone neutre", "status": "MODÉRÉ"})
    else:
        scores.append(25)
        signals.append({"name": "P/L", "value": f"{pnl_pct:.1f}% — en perte", "status": "FAIBLE"})

    # Score final
    final_score = int(np.mean(scores))
    if final_score >= 70:
        level = "FORT"
    elif final_score >= 50:
        level = "MODÉRÉ"
    elif final_score >= 35:
        level = "FAIBLE"
    else:
        level = "ÉPUISÉ"

    return {
        "symbol": symbol,
        "direction": direction,
        "score": final_score,
        "level": level,
        "pnl_pct": round(pnl_pct, 2),
        "signals": signals,
    }


def check_all_positions_health(db: Session) -> list[dict]:
    """Vérifie la santé de toutes les positions ouvertes."""
    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    results = []

    for pos in positions:
        asset = db.query(Asset).filter_by(id=pos.asset_id).first()
        if not asset:
            continue
        health = check_position_health(
            db, asset.symbol, pos.direction.value, float(pos.entry_price)
        )
        results.append(health)

    results.sort(key=lambda x: x["score"])
    return results
