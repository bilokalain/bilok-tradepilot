"""Entry Quality Tracker — Apprend quels signaux de santé pré-trade prédisent le succès

Chaque trade est enregistré avec son état de santé AU MOMENT DE L'ENTRÉE.
Après la fermeture, on compare : est-ce que les trades avec un bon momentum pré-entrée
ont mieux performé que ceux avec un momentum faible ?

Le système apprend et ajuste :
1. Le seuil de santé minimum pour entrer (actuellement 45, peut monter à 55 ou baisser à 40)
2. Quels composantes de santé prédisent le mieux les trades gagnants
3. Les combinaisons dangereuses (RSI suracheté + volume en baisse = à éviter)

Persisté dans data/entry_quality.json
"""

import json
import logging
from datetime import date
from pathlib import Path

import numpy as np

logger = logging.getLogger("tradepilot.entry_quality")

QUALITY_FILE = Path("data/entry_quality.json")
QUALITY_FILE.parent.mkdir(exist_ok=True)


def _load_state() -> dict:
    if QUALITY_FILE.exists():
        try:
            return json.loads(QUALITY_FILE.read_text())
        except Exception:
            pass
    return {
        "trades": [],  # {symbol, entry_health, entry_signals, pnl, pnl_pct, won}
        "optimal_threshold": 45,
        "signal_accuracy": {},  # {signal_name: {fort_win, fort_total, faible_win, faible_total}}
        "dangerous_combos": [],
        "version": 1,
    }


def _save_state(state: dict):
    QUALITY_FILE.write_text(json.dumps(state, default=str, indent=1))


def record_entry(symbol: str, direction: str, health_score: int, signals: list):
    """Enregistre la santé au moment de l'entrée d'un trade."""
    state = _load_state()

    entry = {
        "symbol": symbol,
        "direction": direction,
        "date": date.today().isoformat(),
        "entry_health": health_score,
        "entry_signals": {s["name"]: s["status"] for s in signals},
        "pnl": None,
        "pnl_pct": None,
        "won": None,
        "closed": False,
    }

    state["trades"].append(entry)
    state["trades"] = state["trades"][-200:]  # Garder 200 derniers
    _save_state(state)

    logger.info(f"[ENTRY QUALITY] {symbol} enregistré — santé {health_score}")


def record_exit(symbol: str, pnl: float, pnl_pct: float):
    """Met à jour le trade avec le résultat après fermeture."""
    state = _load_state()
    won = pnl > 0

    # Trouver le dernier trade ouvert pour ce symbol
    for trade in reversed(state["trades"]):
        if trade["symbol"] == symbol and not trade["closed"]:
            trade["pnl"] = round(pnl, 2)
            trade["pnl_pct"] = round(pnl_pct, 2)
            trade["won"] = won
            trade["closed"] = True
            break

    # Recalculer les stats
    _update_stats(state)
    _save_state(state)

    logger.info(f"[ENTRY QUALITY] {symbol} fermé — P/L {pnl_pct:+.1f}%, won={won}")


def _update_stats(state: dict):
    """Recalcule les statistiques d'apprentissage."""
    closed_trades = [t for t in state["trades"] if t["closed"]]
    if len(closed_trades) < 5:
        return

    # 1. Accuracy par signal de santé
    signal_stats = {}
    for trade in closed_trades:
        for sig_name, sig_status in trade.get("entry_signals", {}).items():
            if sig_name not in signal_stats:
                signal_stats[sig_name] = {
                    "fort_win": 0, "fort_total": 0,
                    "modere_win": 0, "modere_total": 0,
                    "faible_win": 0, "faible_total": 0,
                }
            s = signal_stats[sig_name]
            if sig_status == "FORT":
                s["fort_total"] += 1
                if trade["won"]:
                    s["fort_win"] += 1
            elif sig_status == "MODÉRÉ":
                s["modere_total"] += 1
                if trade["won"]:
                    s["modere_win"] += 1
            else:
                s["faible_total"] += 1
                if trade["won"]:
                    s["faible_win"] += 1

    # Calculer les taux
    for sig_name, s in signal_stats.items():
        s["fort_winrate"] = round(s["fort_win"] / s["fort_total"] * 100, 1) if s["fort_total"] > 0 else 0
        s["faible_winrate"] = round(s["faible_win"] / s["faible_total"] * 100, 1) if s["faible_total"] > 0 else 0
        s["predictive_power"] = round(s["fort_winrate"] - s["faible_winrate"], 1)

    state["signal_accuracy"] = signal_stats

    # 2. Seuil optimal
    # Tester différents seuils et trouver le meilleur win rate
    best_threshold = 45
    best_score = 0

    for threshold in range(35, 65, 5):
        passed = [t for t in closed_trades if t["entry_health"] >= threshold]
        if len(passed) < 3:
            continue
        win_rate = sum(1 for t in passed if t["won"]) / len(passed) * 100
        # Score = win_rate * nombre de trades (on veut un bon taux ET assez de trades)
        score = win_rate * min(len(passed), 20) / 20
        if score > best_score:
            best_score = score
            best_threshold = threshold

    state["optimal_threshold"] = best_threshold

    # 3. Combinaisons dangereuses
    dangerous = []
    for trade in closed_trades:
        if not trade["won"]:
            signals = trade.get("entry_signals", {})
            faibles = [name for name, status in signals.items() if status == "FAIBLE"]
            if len(faibles) >= 2:
                combo = " + ".join(sorted(faibles))
                dangerous.append(combo)

    # Compter les combos les plus fréquentes
    from collections import Counter
    combo_counts = Counter(dangerous)
    state["dangerous_combos"] = [
        {"combo": combo, "count": count, "warning": f"Éviter quand {combo} sont FAIBLES"}
        for combo, count in combo_counts.most_common(5)
    ]


def get_optimal_threshold() -> int:
    """Retourne le seuil de santé optimal appris."""
    state = _load_state()
    return state.get("optimal_threshold", 45)


def get_entry_quality_status() -> dict:
    """Statut complet de l'apprentissage qualité d'entrée."""
    state = _load_state()
    closed = [t for t in state["trades"] if t["closed"]]
    open_trades = [t for t in state["trades"] if not t["closed"]]

    # Win rate par tranche de santé
    health_brackets = {}
    for t in closed:
        bracket = f"{(t['entry_health'] // 10) * 10}-{(t['entry_health'] // 10) * 10 + 9}"
        if bracket not in health_brackets:
            health_brackets[bracket] = {"wins": 0, "total": 0}
        health_brackets[bracket]["total"] += 1
        if t["won"]:
            health_brackets[bracket]["wins"] += 1

    for b in health_brackets.values():
        b["win_rate"] = round(b["wins"] / b["total"] * 100, 1) if b["total"] > 0 else 0

    return {
        "total_trades": len(state["trades"]),
        "closed_trades": len(closed),
        "open_trades": len(open_trades),
        "optimal_threshold": state.get("optimal_threshold", 45),
        "signal_accuracy": state.get("signal_accuracy", {}),
        "dangerous_combos": state.get("dangerous_combos", []),
        "health_brackets": health_brackets,
        "overall_win_rate": round(sum(1 for t in closed if t["won"]) / len(closed) * 100, 1) if closed else 0,
    }
