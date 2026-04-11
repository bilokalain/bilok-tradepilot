"""Critère 5 — Capital Institutionnel (IPI)

Détecte l'activité institutionnelle via des proxies accessibles :
1. Volume anormal (proxy dark pools) — gros blocs invisibles sur le marché
2. Short Interest estimé (via put/call ratio implicite du volume)
3. Accumulation/Distribution (A/D Line)
4. Smart Money Flow (gros volumes sans mouvement de prix = accumulation)

Phase 2 : SEC 13F, Unusual Whales, options flow réels.
Score -100 à +100 : négatif = distribution institutionnelle, positif = accumulation.
"""

import numpy as np
import pandas as pd

from backend.modules.scanner.indicators import sma, obv


def compute_accumulation_distribution(high: pd.Series, low: pd.Series,
                                       close: pd.Series, volume: pd.Series) -> pd.Series:
    """Ligne d'Accumulation/Distribution (A/D).

    MFM = ((Close - Low) - (High - Close)) / (High - Low)
    MFV = MFM * Volume
    A/D = cumsum(MFV)
    """
    hl_range = high - low
    hl_range = hl_range.replace(0, np.nan)
    mfm = ((close - low) - (high - close)) / hl_range
    mfv = mfm * volume
    return mfv.cumsum()


def detect_smart_money_flow(close: pd.Series, volume: pd.Series,
                             lookback: int = 20) -> float:
    """Détecte le Smart Money Flow.

    Gros volume avec peu de mouvement de prix = accumulation silencieuse.
    Petit volume avec gros mouvement = retail / manipulation.
    """
    if len(close) < lookback:
        return 50.0

    recent = pd.DataFrame({
        "returns": close.pct_change().abs(),
        "volume": volume,
    }).iloc[-lookback:].dropna()

    if recent.empty or recent["returns"].sum() == 0:
        return 50.0

    # Ratio : volume / mouvement de prix
    # Haut ratio = gros volume, petit mouvement = smart money
    avg_vol = recent["volume"].mean()
    avg_move = recent["returns"].mean()

    if avg_move == 0:
        return 50.0

    efficiency = avg_vol / (avg_move * avg_vol.max()) if avg_vol.max() > 0 else 0

    # Comparer aux 60 derniers jours
    if len(close) >= 60:
        hist = pd.DataFrame({
            "returns": close.pct_change().abs(),
            "volume": volume,
        }).iloc[-60:-20].dropna()

        if not hist.empty and hist["returns"].mean() > 0:
            hist_efficiency = hist["volume"].mean() / (hist["returns"].mean() * hist["volume"].max()) if hist["volume"].max() > 0 else 0
            ratio = efficiency / hist_efficiency if hist_efficiency > 0 else 1
        else:
            ratio = 1
    else:
        ratio = 1

    # Ratio > 1.5 = accumulation probable
    if ratio > 2.0:
        return 85.0
    elif ratio > 1.5:
        return 72.0
    elif ratio > 1.0:
        return 58.0
    elif ratio > 0.7:
        return 42.0
    else:
        return 25.0  # Distribution probable


def detect_volume_anomaly(volume: pd.Series, lookback: int = 20) -> dict:
    """Détecte les anomalies de volume (proxy dark pools).

    Volume > 2x la moyenne = activité institutionnelle probable.
    """
    if len(volume) < lookback + 5:
        return {"anomaly": False, "ratio": 1.0, "score": 50}

    avg = volume.iloc[-lookback - 5:-5].mean()
    recent_max = volume.iloc[-5:].max()

    if avg == 0:
        return {"anomaly": False, "ratio": 1.0, "score": 50}

    ratio = recent_max / avg
    anomaly = ratio > 2.0

    if ratio > 3.0:
        score = 90
    elif ratio > 2.0:
        score = 75
    elif ratio > 1.5:
        score = 60
    else:
        score = 45

    return {"anomaly": anomaly, "ratio": round(ratio, 2), "score": score}


def compute_ipi_score(close: pd.Series, high: pd.Series,
                       low: pd.Series, volume: pd.Series) -> dict:
    """Score Capital Institutionnel (IPI) composite.

    Combine : A/D trend (30%) + Smart Money (35%) + Volume anomaly (35%)
    Score 0-100 (centré à 50, > 50 = accumulation, < 50 = distribution)
    """
    # A/D Line trend
    ad_line = compute_accumulation_distribution(high, low, close, volume)
    if len(ad_line) >= 20:
        ad_recent = ad_line.iloc[-1]
        ad_20ago = ad_line.iloc[-20]
        ad_trend = "UP" if ad_recent > ad_20ago else "DOWN"
        ad_score = 70 if ad_trend == "UP" else 30
    else:
        ad_trend = "FLAT"
        ad_score = 50

    # Smart Money Flow
    smart_money = detect_smart_money_flow(close, volume)

    # Volume anomaly
    vol_anomaly = detect_volume_anomaly(volume)

    score = (
        ad_score * 0.30 +
        smart_money * 0.35 +
        vol_anomaly["score"] * 0.35
    )

    return {
        "score": round(min(100, max(0, score)), 2),
        "ad_trend": ad_trend,
        "ad_score": ad_score,
        "smart_money_score": round(smart_money, 1),
        "volume_anomaly": vol_anomaly,
    }
