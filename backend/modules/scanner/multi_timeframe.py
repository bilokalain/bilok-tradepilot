"""Multi-Timeframe Analysis (MTA)

Compare les signaux sur plusieurs timeframes :
- Daily (tendance long terme)
- 1H (tendance court terme)

Alignement des timeframes = signal plus fort.
Divergence = prudence.

Score MTA (0-100) :
- 90+ : tous les timeframes alignés dans la même direction
- 70+ : majorité alignée
- 50  : neutre / mixte
- <30 : divergence forte (contre-signal)
"""

import numpy as np
import pandas as pd

from backend.modules.scanner.indicators import sma, rsi, macd


def analyse_timeframe(close: pd.Series) -> dict:
    """Analyse un timeframe unique et retourne un signal."""
    if len(close) < 50:
        return {"direction": "NEUTRAL", "strength": 0}

    last = close.iloc[-1]
    sma_20 = sma(close, 20).iloc[-1]
    sma_50 = sma(close, 50).iloc[-1]
    rsi_val = rsi(close).iloc[-1]
    macd_data = macd(close)
    macd_hist = macd_data["histogram"].iloc[-1]

    bullish = 0
    bearish = 0

    # Tendance
    if not np.isnan(sma_50):
        if last > sma_20 > sma_50:
            bullish += 2
        elif last > sma_20:
            bullish += 1
        elif last < sma_20 < sma_50:
            bearish += 2
        elif last < sma_20:
            bearish += 1

    # Momentum
    if not np.isnan(rsi_val):
        if rsi_val > 60:
            bullish += 1
        elif rsi_val < 40:
            bearish += 1

    # MACD
    if not np.isnan(macd_hist):
        if macd_hist > 0:
            bullish += 1
        else:
            bearish += 1

    total = bullish + bearish
    if total == 0:
        return {"direction": "NEUTRAL", "strength": 0}

    if bullish > bearish:
        direction = "BULLISH"
        strength = bullish / total * 100
    elif bearish > bullish:
        direction = "BEARISH"
        strength = bearish / total * 100
    else:
        direction = "NEUTRAL"
        strength = 50

    return {"direction": direction, "strength": round(strength, 1)}


def compute_mta_score(daily_close: pd.Series,
                      hourly_close: pd.Series | None = None) -> dict:
    """Score Multi-Timeframe Analysis.

    Compare les signaux daily et 1H.
    """
    daily = analyse_timeframe(daily_close)
    timeframes = {"daily": daily}

    if hourly_close is not None and len(hourly_close) >= 50:
        hourly = analyse_timeframe(hourly_close)
        timeframes["1h"] = hourly
    else:
        hourly = None

    # Score d'alignement
    if hourly is None:
        # Seulement le daily disponible
        if daily["direction"] == "BULLISH":
            score = 50 + daily["strength"] * 0.4
        elif daily["direction"] == "BEARISH":
            score = 50 - daily["strength"] * 0.4
        else:
            score = 50
    else:
        # Deux timeframes
        if daily["direction"] == hourly["direction"]:
            # Alignés → score fort
            base_strength = (daily["strength"] + hourly["strength"]) / 2
            if daily["direction"] == "BULLISH":
                score = 60 + base_strength * 0.35
            else:
                score = 40 - base_strength * 0.35
        elif daily["direction"] == "NEUTRAL" or hourly["direction"] == "NEUTRAL":
            # Un neutre → modéré
            active = daily if daily["direction"] != "NEUTRAL" else hourly
            if active["direction"] == "BULLISH":
                score = 55 + active["strength"] * 0.15
            else:
                score = 45 - active["strength"] * 0.15
        else:
            # Divergence → score vers 50 (incertitude)
            score = 50
            # Pondérer vers le daily (plus fiable)
            if daily["direction"] == "BULLISH":
                score += 5
            else:
                score -= 5

    score = max(0, min(100, score))

    alignment = "ALIGNED" if hourly and daily["direction"] == hourly["direction"] and daily["direction"] != "NEUTRAL" else \
                "DIVERGENT" if hourly and daily["direction"] != hourly["direction"] and daily["direction"] != "NEUTRAL" and hourly["direction"] != "NEUTRAL" else \
                "PARTIAL"

    return {
        "mta_score": round(score, 2),
        "alignment": alignment,
        "timeframes": timeframes,
    }
