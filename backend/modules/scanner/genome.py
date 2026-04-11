"""Critère 4 — Génome Explosif : ADN comportemental de l'actif

5 composantes :
1. Phase de cycle (accumulation → markup → distribution → markdown → capitulation)
2. Sismographe (6 micro-signaux de pré-explosion)
3. Mémoire fractale (cosine similarity avec patterns historiques explosifs)
4. Réseau de contagion inter-actifs
5. Score de compression (Bollinger squeeze + volume contraction)

Score 0-100 : probabilité que l'actif soit en phase pré-explosive.
"""

import numpy as np
import pandas as pd

from backend.modules.scanner.indicators import sma, ema, rsi, bollinger_bands, atr


def detect_cycle_phase(close: pd.Series, volume: pd.Series) -> dict:
    """Détecte la phase du cycle de Wyckoff.

    1=Accumulation, 2=Markup, 3=Distribution, 4=Markdown, 5=Capitulation
    """
    if len(close) < 100:
        return {"phase": 3, "score": 50}

    sma_50 = sma(close, 50)
    sma_200 = sma(close, 200)
    rsi_val = rsi(close, 14).iloc[-1]
    last = close.iloc[-1]
    s50 = sma_50.iloc[-1]
    s200 = sma_200.iloc[-1]

    if np.isnan(s200):
        return {"phase": 3, "score": 50}

    # Pente SMA 50 sur 20j
    slope_50 = (sma_50.iloc[-1] - sma_50.iloc[-20]) / sma_50.iloc[-20] if not np.isnan(sma_50.iloc[-20]) and sma_50.iloc[-20] != 0 else 0

    # Volume trend
    vol_recent = volume.iloc[-20:].mean()
    vol_hist = volume.iloc[-60:-20].mean() if len(volume) >= 60 else vol_recent
    vol_ratio = vol_recent / vol_hist if vol_hist > 0 else 1

    if last < s200 and slope_50 < -0.01 and rsi_val < 35:
        phase = 5  # Capitulation
        score = 85  # Souvent suivi d'un rebond
    elif last < s200 and slope_50 < 0:
        phase = 4  # Markdown
        score = 30
    elif last > s200 and slope_50 > 0.02 and vol_ratio > 1.2:
        phase = 2  # Markup
        score = 75
    elif last > s200 and slope_50 < 0.005 and vol_ratio < 0.8:
        phase = 3  # Distribution
        score = 35
    elif abs(slope_50) < 0.005 and last < s50 * 1.05 and last > s200:
        phase = 1  # Accumulation
        score = 70  # Phase intéressante
    else:
        phase = 2 if slope_50 > 0 else 4
        score = 55

    return {"phase": phase, "score": score}


def compute_seismograph(close: pd.Series, high: pd.Series,
                        low: pd.Series, volume: pd.Series) -> dict:
    """Sismographe — 6 micro-signaux de pré-explosion.

    1. Contraction de volatilité (Bollinger squeeze)
    2. Volume en déclin puis spike
    3. Inside bars consécutives
    4. Faux breakout récent
    5. Divergence RSI
    6. Compression ATR
    """
    signals = {}
    score = 0

    if len(close) < 50:
        return {"signals": {}, "active": 0, "score": 50}

    # 1. Bollinger Squeeze
    bb = bollinger_bands(close, 20, 2.0)
    bb_width = (bb["upper"] - bb["lower"]) / bb["middle"]
    current_width = bb_width.iloc[-1]
    avg_width = bb_width.iloc[-60:].mean() if len(bb_width) >= 60 else bb_width.mean()
    squeeze = current_width < avg_width * 0.6 if not np.isnan(current_width) and not np.isnan(avg_width) and avg_width > 0 else False
    signals["bollinger_squeeze"] = squeeze
    if squeeze:
        score += 18

    # 2. Volume contraction → expansion
    if len(volume) >= 30:
        vol_10 = volume.iloc[-10:].mean()
        vol_30 = volume.iloc[-30:].mean()
        vol_ratio = vol_10 / vol_30 if vol_30 > 0 else 1
        vol_contraction = vol_ratio < 0.7
        vol_spike = volume.iloc[-1] > vol_30 * 1.5
        signals["volume_contraction"] = vol_contraction
        signals["volume_spike"] = vol_spike
        if vol_contraction:
            score += 12
        if vol_spike:
            score += 10

    # 3. Inside bars (range contenu dans la barre précédente)
    inside_count = 0
    for i in range(-5, 0):
        if len(high) > abs(i) + 1:
            if high.iloc[i] <= high.iloc[i - 1] and low.iloc[i] >= low.iloc[i - 1]:
                inside_count += 1
    signals["inside_bars"] = inside_count
    if inside_count >= 2:
        score += 15

    # 4. ATR compression
    atr_series = atr(high, low, close, 14)
    if len(atr_series) >= 40:
        atr_current = atr_series.iloc[-1]
        atr_avg = atr_series.iloc[-40:].mean()
        atr_compressed = atr_current < atr_avg * 0.6 if not np.isnan(atr_current) and not np.isnan(atr_avg) and atr_avg > 0 else False
        signals["atr_compression"] = atr_compressed
        if atr_compressed:
            score += 15

    # 5. RSI divergence (prix fait un plus bas mais RSI fait un plus haut)
    rsi_series = rsi(close, 14)
    if len(rsi_series) >= 20:
        price_lower = close.iloc[-1] < close.iloc[-10]
        rsi_higher = rsi_series.iloc[-1] > rsi_series.iloc[-10]
        bullish_divergence = price_lower and rsi_higher
        signals["rsi_divergence"] = bullish_divergence
        if bullish_divergence:
            score += 15

    active = sum(1 for v in signals.values() if v is True or (isinstance(v, int) and v >= 2))

    return {
        "signals": signals,
        "active": active,
        "score": min(100, score),
    }


def compute_fractal_memory(close: pd.Series, lookback: int = 252) -> float:
    """Mémoire fractale — l'actif répète-t-il ses patterns ?

    Compare les rendements récents (20j) avec des fenêtres historiques
    via cosine similarity. Score élevé = comportement répétitif exploitable.
    """
    if len(close) < lookback + 20:
        return 50.0

    recent = close.pct_change().iloc[-20:].values
    recent = recent[~np.isnan(recent)]
    if len(recent) < 15 or np.linalg.norm(recent) == 0:
        return 50.0

    similarities = []
    for i in range(lookback - 20):
        window = close.pct_change().iloc[i:i + 20].values
        window = window[~np.isnan(window)]
        if len(window) < 15 or np.linalg.norm(window) == 0:
            continue
        # Cosine similarity
        min_len = min(len(recent), len(window))
        cos_sim = np.dot(recent[:min_len], window[:min_len]) / (np.linalg.norm(recent[:min_len]) * np.linalg.norm(window[:min_len]))
        similarities.append(abs(cos_sim))

    if not similarities:
        return 50.0

    max_sim = max(similarities)
    avg_sim = np.mean(similarities)

    # Score : haute similarité = pattern répétitif
    score = avg_sim * 50 + max_sim * 50
    return round(min(100, max(0, score * 100)), 2)


def compute_genome_score(close: pd.Series, high: pd.Series,
                          low: pd.Series, volume: pd.Series) -> dict:
    """Score Génome Explosif composite (0-100).

    Combine : Phase de cycle (30%) + Sismographe (40%) + Mémoire fractale (30%)
    """
    cycle = detect_cycle_phase(close, volume)
    seismo = compute_seismograph(close, high, low, volume)
    fractal = compute_fractal_memory(close)

    score = (
        cycle["score"] * 0.30 +
        seismo["score"] * 0.40 +
        fractal * 0.30
    )

    return {
        "score": round(min(100, max(0, score)), 2),
        "cycle_phase": cycle["phase"],
        "cycle_score": cycle["score"],
        "seismograph": seismo,
        "fractal_memory": round(fractal, 2),
    }
