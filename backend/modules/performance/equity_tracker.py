"""Equity Tracker — Enregistre l'equity chaque jour pour construire la courbe

Sauvegardé dans data/equity_history.json
Comparé à SPY buy & hold sur la même période.
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path

logger = logging.getLogger("tradepilot.equity_tracker")

EQUITY_FILE = Path("data/equity_history.json")
EQUITY_FILE.parent.mkdir(exist_ok=True)


def _load_history() -> list:
    if EQUITY_FILE.exists():
        try:
            return json.loads(EQUITY_FILE.read_text())
        except Exception:
            return []
    return []


def _save_history(history: list):
    EQUITY_FILE.write_text(json.dumps(history, default=str))


def record_daily_equity():
    """Enregistre l'equity du jour. Appelé par le pipeline nocturne."""
    try:
        from backend.modules.execution.broker_alpaca import alpaca_broker
        if not alpaca_broker.is_configured:
            return

        acct = alpaca_broker.get_account()
        equity = float(acct["equity"])
        cash = float(acct["cash"])
        positions = alpaca_broker.get_positions()

        # SPY benchmark
        spy_price = None
        try:
            spy_price = alpaca_broker.get_last_price("SPY")
        except Exception:
            pass

        history = _load_history()
        today = date.today().isoformat()

        # Ne pas enregistrer deux fois le même jour
        if history and history[-1].get("date") == today:
            history[-1] = {
                "date": today,
                "equity": round(equity, 2),
                "cash": round(cash, 2),
                "invested": round(equity - cash, 2),
                "positions": len(positions),
                "pnl_day": round(sum(float(p.get("pnl", 0)) for p in positions), 2),
                "spy_price": round(spy_price, 2) if spy_price else None,
            }
        else:
            history.append({
                "date": today,
                "equity": round(equity, 2),
                "cash": round(cash, 2),
                "invested": round(equity - cash, 2),
                "positions": len(positions),
                "pnl_day": round(sum(float(p.get("pnl", 0)) for p in positions), 2),
                "spy_price": round(spy_price, 2) if spy_price else None,
            })

        _save_history(history)
        logger.info(f"[EQUITY] Enregistré: ${equity:,.2f} ({len(positions)} positions)")

    except Exception as e:
        logger.warning(f"[EQUITY] Erreur: {e}")


def get_equity_curve() -> dict:
    """Retourne la courbe d'equity + comparaison SPY."""
    history = _load_history()
    if not history:
        # Essayer d'enregistrer maintenant
        record_daily_equity()
        history = _load_history()

    if not history:
        return {"status": "no_data", "history": []}

    initial_equity = 100_000
    first_spy = None

    curve = []
    for h in history:
        equity = h["equity"]
        ret_pct = round((equity / initial_equity - 1) * 100, 3)

        spy_ret = None
        if h.get("spy_price"):
            if first_spy is None:
                first_spy = h["spy_price"]
            spy_ret = round((h["spy_price"] / first_spy - 1) * 100, 3)

        curve.append({
            "date": h["date"],
            "equity": equity,
            "return_pct": ret_pct,
            "spy_return_pct": spy_ret,
            "alpha": round(ret_pct - spy_ret, 3) if spy_ret is not None else None,
            "cash_pct": round(h.get("cash", 0) / equity * 100, 1) if equity > 0 else 0,
            "positions": h.get("positions", 0),
            "pnl_day": h.get("pnl_day", 0),
        })

    # Stats
    current = curve[-1] if curve else {}
    max_equity = max(c["equity"] for c in curve) if curve else initial_equity
    drawdown = round((current.get("equity", initial_equity) / max_equity - 1) * 100, 2)

    return {
        "status": "ok",
        "history": curve,
        "summary": {
            "days": len(curve),
            "current_equity": current.get("equity", initial_equity),
            "total_return": current.get("return_pct", 0),
            "spy_return": current.get("spy_return_pct", 0),
            "alpha": current.get("alpha", 0),
            "max_drawdown": drawdown,
            "best_day": max(curve, key=lambda c: c.get("pnl_day", 0)) if curve else None,
            "worst_day": min(curve, key=lambda c: c.get("pnl_day", 0)) if curve else None,
        },
    }
