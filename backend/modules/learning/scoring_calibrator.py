"""Scoring Calibrator — Ajuste les poids du Score V2 en se basant sur les top movers réels

Logique :
1. Chaque jour, enregistre les top movers du marché (les actifs qui ont le plus bougé)
2. Pour chaque top mover, enregistre s'il était en GO, WAIT ou NO_TRADE
3. Calcule le taux de capture : combien de top movers étaient en GO ?
4. Si le taux est bas → ajuste les poids pour mieux capturer
5. Simule différents poids et trouve l'optimal

L'objectif : maximiser le nombre de top performers détectés SANS augmenter les faux positifs.

Persisté dans data/scoring_calibration.json
"""

import json
import logging
import time
from datetime import date, datetime
from pathlib import Path

import numpy as np

logger = logging.getLogger("tradepilot.scoring_calibrator")

CALIBRATION_FILE = Path("data/scoring_calibration.json")
CALIBRATION_FILE.parent.mkdir(exist_ok=True)

# Poids actuels du scoring V2
DEFAULT_WEIGHTS = {
    "bayesian": 0.30,
    "sqc": 0.20,
    "conviction": 0.35,
    "scanner": 0.15,
}


def _load_state() -> dict:
    if CALIBRATION_FILE.exists():
        try:
            return json.loads(CALIBRATION_FILE.read_text())
        except Exception:
            pass
    return {
        "current_weights": DEFAULT_WEIGHTS.copy(),
        "daily_records": [],  # [{date, top_movers, detected, missed, weights_used}]
        "optimization_history": [],
        "version": 1,
    }


def _save_state(state: dict):
    CALIBRATION_FILE.write_text(json.dumps(state, default=str, indent=1))


def get_current_weights() -> dict:
    """Retourne les poids optimaux actuels du scoring V2."""
    state = _load_state()
    return state.get("current_weights", DEFAULT_WEIGHTS.copy())


def record_daily_performance(db) -> dict:
    """Enregistre les top movers du jour et évalue notre taux de détection.

    Appelé par le pipeline nocturne.
    """
    from backend.database.models import Asset, OHLCVDaily

    state = _load_state()
    today = date.today().isoformat()

    # Déjà enregistré aujourd'hui ?
    if state["daily_records"] and state["daily_records"][-1].get("date") == today:
        return state["daily_records"][-1]

    # Calculer les top movers depuis la BDD
    assets = db.query(Asset).filter_by(is_active=True).all()
    movers = []

    for asset in assets:
        rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(2).all()
        if len(rows) < 2:
            continue
        prev = float(rows[1].close)
        curr = float(rows[0].close)
        if prev <= 0:
            continue
        change = (curr / prev - 1) * 100
        movers.append({"symbol": asset.symbol, "change_pct": round(change, 2)})

    # Top 20 hausse
    top_gainers = sorted([m for m in movers if m["change_pct"] > 2], key=lambda x: -x["change_pct"])[:20]

    if not top_gainers:
        return {"date": today, "message": "Pas assez de movers > 2%"}

    # Vérifier combien étaient en GO dans les signaux
    try:
        signals_file = Path("data/signals_cache.json")
        if signals_file.exists():
            signals = json.loads(signals_file.read_text())
            go_symbols = {s["symbol"] for s in signals if s.get("action") == "GO"}
        else:
            go_symbols = set()
    except Exception:
        go_symbols = set()

    detected = []
    missed = []
    for m in top_gainers:
        sym = m["symbol"]
        if sym in go_symbols:
            detected.append({"symbol": sym, "change_pct": m["change_pct"], "was_go": True})
        else:
            missed.append({"symbol": sym, "change_pct": m["change_pct"], "was_go": False})

    detection_rate = round(len(detected) / len(top_gainers) * 100, 1) if top_gainers else 0

    record = {
        "date": today,
        "top_gainers_count": len(top_gainers),
        "detected": len(detected),
        "missed": len(missed),
        "detection_rate": detection_rate,
        "weights_used": state["current_weights"],
        "top_detected": detected[:5],
        "top_missed": missed[:5],
    }

    state["daily_records"].append(record)
    state["daily_records"] = state["daily_records"][-90:]  # Garder 90 jours

    # Optimiser les poids si assez de données (> 5 jours)
    if len(state["daily_records"]) >= 5:
        _optimize_weights(state, db)

    _save_state(state)
    logger.info(f"[CALIBRATOR] Détection: {detection_rate}% ({len(detected)}/{len(top_gainers)} top movers)")

    return record


def _optimize_weights(state: dict, db):
    """Ajuste les poids en se basant sur les performances passées.

    Stratégie :
    - Si le taux de détection moyen < 30% → augmenter scanner + conviction, réduire bayesian
    - Si le taux > 50% → garder les poids actuels
    - Ajustement progressif (max ±5% par itération)
    """
    records = state["daily_records"][-14:]  # 2 dernières semaines
    if not records:
        return

    avg_rate = np.mean([r["detection_rate"] for r in records])
    current = state["current_weights"]

    if avg_rate >= 50:
        # Bon taux — pas de changement
        logger.info(f"[CALIBRATOR] Taux moyen {avg_rate:.0f}% — poids maintenus")
        return

    if avg_rate < 20:
        # Très mauvais — ajustement fort
        step = 0.05
    elif avg_rate < 30:
        # Mauvais — ajustement modéré
        step = 0.03
    else:
        # Moyen — ajustement léger
        step = 0.02

    # Réduire bayesian, augmenter scanner + conviction
    new_weights = {
        "bayesian": max(0.15, current["bayesian"] - step),
        "sqc": current["sqc"],  # Stable
        "conviction": min(0.45, current["conviction"] + step * 0.6),
        "scanner": min(0.30, current["scanner"] + step * 0.4),
    }

    # Normaliser pour total = 1.0
    total = sum(new_weights.values())
    new_weights = {k: round(v / total, 4) for k, v in new_weights.items()}

    state["current_weights"] = new_weights
    state["optimization_history"].append({
        "date": date.today().isoformat(),
        "avg_detection_rate": round(avg_rate, 1),
        "old_weights": current,
        "new_weights": new_weights,
        "adjustment": step,
    })
    state["optimization_history"] = state["optimization_history"][-30:]

    logger.info(f"[CALIBRATOR] Poids ajustés: Bay {current['bayesian']}→{new_weights['bayesian']}, "
                f"Conv {current['conviction']}→{new_weights['conviction']}, "
                f"Scan {current['scanner']}→{new_weights['scanner']}")


def get_calibration_status() -> dict:
    """Statut complet du calibrage."""
    state = _load_state()
    records = state.get("daily_records", [])

    rates = [r["detection_rate"] for r in records]

    return {
        "current_weights": state.get("current_weights", DEFAULT_WEIGHTS),
        "days_tracked": len(records),
        "avg_detection_rate": round(np.mean(rates), 1) if rates else 0,
        "best_rate": max(rates) if rates else 0,
        "worst_rate": min(rates) if rates else 0,
        "last_optimization": state["optimization_history"][-1] if state.get("optimization_history") else None,
        "recent_records": records[-7:],
    }
