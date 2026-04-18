"""Detection Tracker — Suivi du taux de détection dans le temps

Mesure combien de top movers du marché sont dans nos 308 actifs.
Sauvegardé quotidiennement pour suivre l'évolution.
"""

import json
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger("tradepilot.detection")

TRACKER_FILE = Path("data/detection_history.json")


def _load_history() -> list:
    if TRACKER_FILE.exists():
        try:
            return json.loads(TRACKER_FILE.read_text())
        except Exception:
            return []
    return []


def record_detection(total_market: int, detected: int, missed: list):
    """Enregistre le taux de détection du jour."""
    history = _load_history()
    today = date.today().isoformat()

    rate = round(detected / total_market * 100, 1) if total_market > 0 else 0

    entry = {
        "date": today,
        "total_market": total_market,
        "detected": detected,
        "rate": rate,
        "missed_symbols": [m.get("symbol", "") for m in missed[:5]],
    }

    # Remplacer si même jour
    history = [h for h in history if h["date"] != today]
    history.append(entry)
    history = history[-90:]  # Garder 90 jours

    TRACKER_FILE.parent.mkdir(exist_ok=True)
    TRACKER_FILE.write_text(json.dumps(history, indent=1))
    logger.info(f"[DETECTION] Taux: {rate}% ({detected}/{total_market})")


def get_detection_history() -> dict:
    """Retourne l'historique du taux de détection."""
    history = _load_history()
    if not history:
        return {"status": "no_data", "history": []}

    rates = [h["rate"] for h in history]
    return {
        "status": "ok",
        "history": history,
        "summary": {
            "days": len(history),
            "current_rate": history[-1]["rate"] if history else 0,
            "avg_rate": round(sum(rates) / len(rates), 1) if rates else 0,
            "best_rate": max(rates) if rates else 0,
            "worst_rate": min(rates) if rates else 0,
        },
    }
