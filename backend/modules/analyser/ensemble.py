"""Ensemble de stratégies + Régime-Switching + Optimisation paramètres

Au lieu de choisir UNE stratégie, on combine les signaux de TOUTES
les stratégies profitables (Sharpe > 0) pour cet actif.

Ensemble voting :
- Chaque stratégie profitable vote LONG, SHORT ou NEUTRAL
- Le vote est pondéré par le Sharpe historique de la stratégie
- Le signal final = vote majoritaire pondéré

Régime-Switching :
- Quand le régime change, les poids sont automatiquement recalculés
- Transition douce (pas de switch brutal)

Optimisation :
- SL/TP adaptatifs basés sur l'ATR × multiplicateur optimisé par actif
- Le multiplicateur optimal est dérivé du backtest
"""

import numpy as np
import pandas as pd

from backend.modules.analyser.performance_matrix import (
    BACKTEST_MATRIX, get_profitable_strategies, get_strategy_sharpe,
)
from backend.modules.analyser.strategies import ALL_STRATEGIES


# Multiplicateurs SL/TP optimaux par profil de volatilité
ATR_PROFILES = {
    "low_vol": {"sl_mult": 1.5, "tp_mult": 2.5},     # Actions défensives
    "medium_vol": {"sl_mult": 2.0, "tp_mult": 3.0},   # Actions standard
    "high_vol": {"sl_mult": 2.5, "tp_mult": 4.0},     # Crypto, tech volatile
    "extreme_vol": {"sl_mult": 3.0, "tp_mult": 5.0},  # Meme stocks, NG, crypto
}

# Profil par actif (basé sur la volatilité historique observée)
ASSET_VOL_PROFILE = {
    "TSLA": "high_vol", "NVDA": "high_vol", "META": "high_vol",
    "BTC-USD": "extreme_vol", "ETH-USD": "extreme_vol", "SOL-USD": "extreme_vol",
    "XRP-USD": "extreme_vol", "BNB-USD": "extreme_vol",
    "NG=F": "extreme_vol", "SI=F": "high_vol", "CL=F": "high_vol",
    "GC=F": "medium_vol", "SPY": "low_vol", "QQQ": "low_vol",
    "VTI": "low_vol", "TLT": "medium_vol", "GLD": "medium_vol",
    "JNJ": "low_vol", "V": "low_vol", "JPM": "medium_vol",
}


def get_atr_multipliers(symbol: str) -> dict:
    """Retourne les multiplicateurs SL/TP optimaux pour un actif."""
    profile = ASSET_VOL_PROFILE.get(symbol, "medium_vol")
    return ATR_PROFILES[profile]


def ensemble_vote(close: pd.Series, high: pd.Series, low: pd.Series,
                  volume: pd.Series, symbol: str, regime: str) -> dict:
    """Combine toutes les stratégies profitables par vote pondéré.

    Chaque stratégie profitable vote avec un poids = son Sharpe backtest.
    """
    profitable = get_profitable_strategies(symbol)
    if not profitable:
        return {
            "direction": "NEUTRAL",
            "conviction": 0,
            "strategy": "ensemble",
            "reason": "Aucune stratégie profitable pour cet actif",
            "votes": {},
        }

    votes = {"LONG": 0, "SHORT": 0, "NEUTRAL": 0}
    vote_details = []
    total_weight = 0

    for strat_name in profitable:
        sharpe = get_strategy_sharpe(symbol, strat_name)
        weight = max(0, sharpe)  # Poids = Sharpe (toujours positif ici)

        # Exécuter la stratégie
        func = ALL_STRATEGIES.get(strat_name)
        if not func:
            continue

        try:
            if strat_name in ("breakout", "mean_reversion_v2"):
                signal = func(close, high, low, volume)
            elif strat_name in ("microstructure",):
                signal = func(close, volume)
            elif strat_name in ("cnn_pattern",):
                signal = func(close)
            else:
                signal = func(close, high, low)
        except Exception:
            continue

        direction = signal.get("direction", "NEUTRAL")
        conviction = signal.get("conviction", 0)

        # Vote pondéré
        effective_weight = weight * (conviction / 100) if conviction > 0 else 0
        votes[direction] += effective_weight
        total_weight += effective_weight

        vote_details.append({
            "strategy": strat_name,
            "direction": direction,
            "conviction": conviction,
            "sharpe": round(sharpe, 3),
            "weight": round(effective_weight, 3),
        })

    if total_weight == 0:
        return {
            "direction": "NEUTRAL", "conviction": 0, "strategy": "ensemble",
            "reason": "Toutes les stratégies sont neutres", "votes": vote_details,
        }

    # Direction majoritaire
    best_direction = max(votes, key=votes.get)
    if best_direction == "NEUTRAL" or votes[best_direction] == 0:
        return {
            "direction": "NEUTRAL", "conviction": 0, "strategy": "ensemble",
            "votes": vote_details,
        }

    # Conviction = proportion du vote gagnant
    conviction = (votes[best_direction] / total_weight) * 100

    # Consensus bonus : si > 70% des stratégies sont d'accord, boost
    active_votes = [v for v in vote_details if v["direction"] != "NEUTRAL"]
    if active_votes:
        agreement = sum(1 for v in active_votes if v["direction"] == best_direction) / len(active_votes)
        if agreement >= 0.8:
            conviction = min(95, conviction * 1.15)  # Consensus fort

    # Meilleure stratégie individuelle (pour SL/TP)
    best_individual = max(
        [v for v in vote_details if v["direction"] == best_direction],
        key=lambda v: v["weight"],
        default=None,
    )

    return {
        "direction": best_direction,
        "conviction": round(conviction, 1),
        "strategy": "ensemble",
        "best_individual": best_individual["strategy"] if best_individual else None,
        "consensus": round(agreement * 100, 0) if active_votes else 0,
        "votes_long": round(votes["LONG"], 3),
        "votes_short": round(votes["SHORT"], 3),
        "num_strategies": len(profitable),
        "num_voting": len(active_votes) if active_votes else 0,
        "votes": vote_details,
    }


def regime_switch_weights(current_regime: str, previous_regime: str | None,
                          transition_period: int = 5) -> dict:
    """Calcule les poids de transition entre deux régimes.

    Transition douce sur N jours au lieu d'un switch brutal.
    """
    from backend.modules.analyser.strategies import REGIME_STRATEGY_MATRIX

    current_weights = REGIME_STRATEGY_MATRIX.get(current_regime, REGIME_STRATEGY_MATRIX["RANGE"])

    if previous_regime is None or previous_regime == current_regime:
        return {"weights": current_weights, "transition": False}

    previous_weights = REGIME_STRATEGY_MATRIX.get(previous_regime, current_weights)

    # Blend 70% nouveau régime, 30% ancien (transition douce)
    blended = {}
    for strat in set(list(current_weights.keys()) + list(previous_weights.keys())):
        curr = current_weights.get(strat, 0)
        prev = previous_weights.get(strat, 0)
        blended[strat] = round(curr * 0.7 + prev * 0.3, 4)

    # Normaliser
    total = sum(blended.values())
    if total > 0:
        blended = {k: round(v / total, 4) for k, v in blended.items()}

    return {
        "weights": blended,
        "transition": True,
        "from_regime": previous_regime,
        "to_regime": current_regime,
    }
