"""Sizing Kelly Généralisé inter-actifs

Le critère de Kelly détermine la fraction optimale du capital à risquer.

Formule classique :
  f* = (p * b - q) / b
  avec p = probabilité de gain, q = 1-p, b = ratio gain/perte

Extensions :
- Fractional Kelly (fraction du Kelly optimal pour réduire le risque)
- Kelly Généralisé inter-actifs (corrélations portefeuille)
- Plafond de position (jamais > 20% du capital sur un trade)
"""

import numpy as np
import pandas as pd


# Paramètres de sécurité
MAX_POSITION_PCT = 0.20      # Max 20% du capital par trade
KELLY_FRACTION = 0.25        # Fractional Kelly (1/4 = conservateur)
MIN_WIN_RATE = 0.35          # Minimum pour considérer un signal
MIN_RR_RATIO = 1.0           # Minimum ratio Risk:Reward


def compute_win_rate_estimate(bayesian_score: float, conviction: float) -> float:
    """Estime le taux de réussite à partir du score bayésien et de la conviction.

    En Phase 1, pas de trades historiques → estimation statistique.
    En Phase 2+, on utilisera le win rate réel de la stratégie.
    """
    # Mapping score → win rate estimé
    # Score 50 → ~45% (neutre, léger biais négatif dû aux frais)
    # Score 70 → ~55%
    # Score 90 → ~65%
    base = 0.30 + (bayesian_score / 100) * 0.40  # entre 30% et 70%

    # La conviction ajuste légèrement
    conviction_adj = (conviction - 50) / 500  # entre -0.10 et +0.10
    win_rate = base + conviction_adj

    return np.clip(win_rate, 0.20, 0.75)


def compute_kelly_fraction(win_rate: float, risk_reward_ratio: float) -> float:
    """Calcule la fraction de Kelly optimale.

    f* = (p * b - q) / b
    avec p = win_rate, b = risk_reward_ratio, q = 1 - p
    """
    if risk_reward_ratio <= 0:
        return 0.0

    p = win_rate
    q = 1 - p
    b = risk_reward_ratio

    kelly = (p * b - q) / b

    if kelly <= 0:
        return 0.0

    # Fractional Kelly
    fractional = kelly * KELLY_FRACTION

    # Plafond
    return min(fractional, MAX_POSITION_PCT)


def compute_risk_reward(entry: float, stop_loss: float, take_profit: float) -> float:
    """Calcule le ratio Risk:Reward."""
    if entry is None or stop_loss is None or take_profit is None:
        return 0.0

    risk = abs(entry - stop_loss)
    reward = abs(take_profit - entry)

    if risk == 0:
        return 0.0

    return reward / risk


def compute_position_sizing(capital: float, entry: float, stop_loss: float,
                            take_profit: float, bayesian_score: float,
                            conviction: float) -> dict:
    """Calcule le sizing de position complet.

    Retourne :
    - kelly_fraction : fraction optimale du capital
    - position_size : taille en $
    - quantity : nombre d'unités à acheter
    - risk_per_trade : montant risqué en $
    - risk_reward_ratio : ratio R:R
    """
    rr_ratio = compute_risk_reward(entry, stop_loss, take_profit)

    if rr_ratio < MIN_RR_RATIO:
        return {
            "kelly_fraction": 0.0,
            "position_size_usd": 0.0,
            "quantity": 0.0,
            "risk_per_trade_usd": 0.0,
            "risk_reward_ratio": round(rr_ratio, 2),
            "win_rate_estimate": 0.0,
            "reject_reason": f"R:R trop bas ({rr_ratio:.2f} < {MIN_RR_RATIO})",
        }

    win_rate = compute_win_rate_estimate(bayesian_score, conviction)

    if win_rate < MIN_WIN_RATE:
        return {
            "kelly_fraction": 0.0,
            "position_size_usd": 0.0,
            "quantity": 0.0,
            "risk_per_trade_usd": 0.0,
            "risk_reward_ratio": round(rr_ratio, 2),
            "win_rate_estimate": round(win_rate, 3),
            "reject_reason": f"Win rate estimé trop bas ({win_rate:.1%} < {MIN_WIN_RATE:.0%})",
        }

    kelly = compute_kelly_fraction(win_rate, rr_ratio)

    position_size = capital * kelly
    risk_per_unit = abs(entry - stop_loss)
    quantity = position_size / entry if entry > 0 else 0
    risk_total = quantity * risk_per_unit

    return {
        "kelly_fraction": round(kelly, 4),
        "position_size_usd": round(position_size, 2),
        "quantity": round(quantity, 4),
        "risk_per_trade_usd": round(risk_total, 2),
        "risk_pct_of_capital": round(risk_total / capital * 100, 2) if capital > 0 else 0,
        "risk_reward_ratio": round(rr_ratio, 2),
        "win_rate_estimate": round(win_rate, 3),
        "expected_value": round(win_rate * rr_ratio - (1 - win_rate), 3),
        "reject_reason": None,
    }


def prioritize_signals(signals: list[dict], capital: float) -> list[dict]:
    """Priorise et size plusieurs signaux en tenant compte du capital disponible.

    Les signaux sont triés par expected value décroissante.
    Le capital restant diminue après chaque allocation.
    """
    # Calculer l'EV pour chaque signal
    for signal in signals:
        rr = signal.get("risk_reward_ratio", 0)
        wr = signal.get("win_rate_estimate", 0)
        signal["expected_value"] = wr * rr - (1 - wr) if rr > 0 else -1

    # Trier par EV décroissante
    signals.sort(key=lambda x: x["expected_value"], reverse=True)

    remaining_capital = capital
    total_allocated = 0.0

    for signal in signals:
        if remaining_capital <= 0 or signal["expected_value"] <= 0:
            signal["allocated"] = False
            signal["allocation_usd"] = 0.0
            continue

        sizing = compute_position_sizing(
            remaining_capital,
            signal.get("entry", 0),
            signal.get("stop_loss", 0),
            signal.get("take_profit", 0),
            signal.get("bayesian_score", 50),
            signal.get("conviction", 50),
        )

        if sizing["position_size_usd"] > 0:
            signal["allocated"] = True
            signal["allocation_usd"] = sizing["position_size_usd"]
            signal["sizing"] = sizing
            remaining_capital -= sizing["position_size_usd"]
            total_allocated += sizing["position_size_usd"]
        else:
            signal["allocated"] = False
            signal["allocation_usd"] = 0.0

    return signals
