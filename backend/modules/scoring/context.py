"""Score de Qualité du Contexte (SQC) + Signal Shelf Life

SQC évalue si les conditions actuelles sont favorables à un trade :
- Liquidité (volume relatif)
- Heure de marché (ouverture/clôture = plus liquide)
- Proximité d'événement (earnings, FOMC → prudence)
- Spread implicite (via la volatilité intraday)

Signal Shelf Life : durée de vie estimée du signal
→ détermine le type d'ordre optimal (market, limit, stop)
"""

from datetime import datetime, time

import numpy as np
import pandas as pd


def compute_liquidity_score(volume: pd.Series) -> float:
    """Score de liquidité basé sur le volume relatif.

    Compare le volume récent à la moyenne 20 jours.
    Volume élevé = meilleure exécution = score plus haut.
    """
    if len(volume) < 20:
        return 50.0

    avg_vol = volume.iloc[-20:].mean()
    current_vol = volume.iloc[-1]

    if avg_vol == 0:
        return 50.0

    ratio = current_vol / avg_vol

    if ratio > 2.0:
        return 95.0  # Volume exceptionnel
    elif ratio > 1.5:
        return 85.0
    elif ratio > 1.0:
        return 70.0
    elif ratio > 0.7:
        return 55.0
    elif ratio > 0.5:
        return 40.0
    else:
        return 25.0  # Volume très faible — mauvais contexte


def compute_time_score() -> float:
    """Score basé sur l'heure de marché (EST).

    Meilleurs moments : ouverture (9h30-10h30) et clôture (15h-16h)
    Pire moment : lunch (12h-14h)
    """
    now = datetime.utcnow()
    # Approximation EST = UTC-5
    est_hour = (now.hour - 5) % 24

    if 9 <= est_hour <= 10:  # Ouverture
        return 85.0
    elif 15 <= est_hour <= 16:  # Clôture
        return 80.0
    elif 10 < est_hour < 12:  # Mid-morning
        return 70.0
    elif 14 <= est_hour < 15:  # Pré-clôture
        return 70.0
    elif 12 <= est_hour < 14:  # Lunch
        return 45.0
    else:  # Hors marché
        return 30.0


def compute_volatility_context(high: pd.Series, low: pd.Series,
                                close: pd.Series) -> float:
    """Score de contexte basé sur la volatilité intraday récente.

    Volatilité trop haute = risque élevé = score bas
    Volatilité trop basse = marché mort = score moyen
    Volatilité normale = bon contexte = score haut
    """
    if len(close) < 20:
        return 50.0

    # Range intraday normalisé (high-low) / close
    intraday_range = ((high - low) / close).iloc[-20:]
    avg_range = intraday_range.mean()
    current_range = intraday_range.iloc[-1]

    if avg_range == 0:
        return 50.0

    ratio = current_range / avg_range

    if ratio > 2.5:
        return 20.0  # Volatilité extrême — danger
    elif ratio > 1.5:
        return 40.0  # Volatilité élevée
    elif ratio > 0.8:
        return 80.0  # Volatilité normale — bon
    elif ratio > 0.5:
        return 65.0  # Volatilité faible
    else:
        return 45.0  # Volatilité très faible — marché mort


def compute_sqc(volume: pd.Series, high: pd.Series,
                low: pd.Series, close: pd.Series) -> dict:
    """Score de Qualité du Contexte (SQC) composite.

    Combine liquidité (40%), heure (20%), volatilité (40%).
    """
    liquidity = compute_liquidity_score(volume)
    time_score = compute_time_score()
    volatility = compute_volatility_context(high, low, close)

    sqc = liquidity * 0.40 + time_score * 0.20 + volatility * 0.40

    return {
        "sqc": round(np.clip(sqc, 0, 100), 2),
        "components": {
            "liquidity": round(liquidity, 1),
            "time": round(time_score, 1),
            "volatility_context": round(volatility, 1),
        },
    }


def estimate_shelf_life(strategy: str, regime: str,
                        conviction: float, sqc: float) -> dict:
    """Estime la durée de vie du signal et le type d'ordre optimal.

    Facteurs :
    - Stratégie (trend = long, breakout = court)
    - Régime (stable = long, transition = court)
    - Conviction (haute = confiance pour attendre)
    - SQC (haut = exécution rapide possible)
    """
    # Durée de base par stratégie (en heures)
    base_hours = {
        "trend_following": 72,    # 3 jours
        "mean_reversion": 24,     # 1 jour
        "breakout": 8,            # 8 heures
        "momentum": 48,           # 2 jours
        "microstructure": 2,      # 2 heures
        "cnn_pattern": 24,        # 1 jour
    }

    # Multiplicateur régime
    regime_mult = {
        "BULL": 1.2,
        "BEAR": 0.8,
        "RANGE": 1.0,
        "CRISIS": 0.5,       # Tout va vite en crise
        "TRANSITION": 0.7,   # Instable
    }

    hours = base_hours.get(strategy, 24)
    hours *= regime_mult.get(regime, 1.0)

    # Conviction haute → on peut attendre plus
    if conviction > 80:
        hours *= 1.3
    elif conviction < 40:
        hours *= 0.6

    hours = max(1, round(hours))

    # Type d'ordre optimal
    if hours <= 4:
        order_type = "MARKET"
        reason = "Signal court — exécution immédiate"
    elif hours <= 24 and sqc > 70:
        order_type = "LIMIT"
        reason = "Bon contexte — ordre limit pour meilleur prix"
    elif hours <= 24:
        order_type = "MARKET"
        reason = "Signal court + contexte moyen — market order"
    else:
        order_type = "LIMIT"
        reason = "Signal long — patience pour le bon prix"

    return {
        "shelf_life_hours": hours,
        "shelf_life_label": _hours_to_label(hours),
        "order_type": order_type,
        "order_reason": reason,
    }


def _hours_to_label(hours: int) -> str:
    if hours < 4:
        return "Très court (< 4h)"
    elif hours < 12:
        return f"Court ({hours}h)"
    elif hours < 48:
        return f"Moyen ({hours // 24}j {hours % 24}h)"
    else:
        days = hours // 24
        return f"Long ({days} jours)"
