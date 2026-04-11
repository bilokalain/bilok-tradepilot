"""Détection probabiliste du régime de marché

5 régimes possibles avec probabilité pour chacun :
- BULL : tendance haussière soutenue
- BEAR : tendance baissière soutenue
- RANGE : marché latéral / consolidation
- CRISIS : chute brutale + volatilité extrême
- TRANSITION : changement de régime en cours

Méthode : combinaison de 4 signaux indépendants :
1. Tendance (SMA 50 vs 200 + pente)
2. Volatilité (ATR normalisé + expansion/contraction)
3. Momentum (RSI zone + MACD direction)
4. Structure (position du prix dans le range 52 semaines)
"""

import numpy as np
import pandas as pd

from backend.modules.scanner.indicators import sma, ema, rsi, macd, atr


REGIMES = ["BULL", "BEAR", "RANGE", "CRISIS", "TRANSITION"]


def _trend_signal(close: pd.Series) -> dict:
    """Signal de tendance basé sur SMA 50/200 et pente."""
    sma_50 = sma(close, 50)
    sma_200 = sma(close, 200)

    last_close = close.iloc[-1]
    last_sma50 = sma_50.iloc[-1]
    last_sma200 = sma_200.iloc[-1]

    if np.isnan(last_sma200):
        return {r: 0.2 for r in REGIMES}

    # Pente de la SMA 50 sur 20 jours
    sma50_slope = (sma_50.iloc[-1] - sma_50.iloc[-20]) / sma_50.iloc[-20] if not np.isnan(sma_50.iloc[-20]) and sma_50.iloc[-20] != 0 else 0

    probs = {"BULL": 0.0, "BEAR": 0.0, "RANGE": 0.0, "CRISIS": 0.0, "TRANSITION": 0.0}

    if last_close > last_sma50 > last_sma200:
        if sma50_slope > 0.02:
            probs["BULL"] = 0.8
            probs["RANGE"] = 0.1
            probs["TRANSITION"] = 0.1
        else:
            probs["BULL"] = 0.5
            probs["RANGE"] = 0.3
            probs["TRANSITION"] = 0.2
    elif last_close < last_sma50 < last_sma200:
        if sma50_slope < -0.02:
            probs["BEAR"] = 0.8
            probs["CRISIS"] = 0.1
            probs["TRANSITION"] = 0.1
        else:
            probs["BEAR"] = 0.5
            probs["RANGE"] = 0.3
            probs["TRANSITION"] = 0.2
    elif abs(last_sma50 - last_sma200) / last_sma200 < 0.02:
        probs["RANGE"] = 0.5
        probs["TRANSITION"] = 0.3
        probs["BULL"] = 0.1
        probs["BEAR"] = 0.1
    else:
        probs["TRANSITION"] = 0.5
        probs["RANGE"] = 0.2
        probs["BULL"] = 0.15
        probs["BEAR"] = 0.15

    return probs


def _volatility_signal(high: pd.Series, low: pd.Series, close: pd.Series) -> dict:
    """Signal de volatilité basé sur ATR normalisé."""
    atr_series = atr(high, low, close, 14)
    atr_current = atr_series.iloc[-1]
    atr_mean = atr_series.iloc[-60:].mean()  # moyenne 3 mois

    if np.isnan(atr_current) or np.isnan(atr_mean) or atr_mean == 0:
        return {r: 0.2 for r in REGIMES}

    atr_ratio = atr_current / atr_mean

    probs = {"BULL": 0.0, "BEAR": 0.0, "RANGE": 0.0, "CRISIS": 0.0, "TRANSITION": 0.0}

    if atr_ratio > 2.0:
        # Volatilité extrême
        probs["CRISIS"] = 0.7
        probs["BEAR"] = 0.15
        probs["TRANSITION"] = 0.15
    elif atr_ratio > 1.3:
        # Volatilité élevée
        probs["TRANSITION"] = 0.4
        probs["BEAR"] = 0.25
        probs["BULL"] = 0.15
        probs["CRISIS"] = 0.2
    elif atr_ratio < 0.7:
        # Volatilité faible — compression
        probs["RANGE"] = 0.6
        probs["TRANSITION"] = 0.25
        probs["BULL"] = 0.15
    else:
        # Volatilité normale
        probs["BULL"] = 0.3
        probs["RANGE"] = 0.3
        probs["BEAR"] = 0.2
        probs["TRANSITION"] = 0.2

    return probs


def _momentum_signal(close: pd.Series) -> dict:
    """Signal de momentum basé sur RSI et MACD."""
    rsi_series = rsi(close)
    macd_data = macd(close)

    rsi_val = rsi_series.iloc[-1]
    macd_hist = macd_data["histogram"].iloc[-1]

    if np.isnan(rsi_val):
        return {r: 0.2 for r in REGIMES}

    probs = {"BULL": 0.0, "BEAR": 0.0, "RANGE": 0.0, "CRISIS": 0.0, "TRANSITION": 0.0}

    # RSI zones
    if rsi_val > 65:
        probs["BULL"] = 0.6
        probs["TRANSITION"] = 0.2
        probs["RANGE"] = 0.2
    elif rsi_val < 35:
        probs["BEAR"] = 0.5
        probs["CRISIS"] = 0.2
        probs["TRANSITION"] = 0.2
        probs["RANGE"] = 0.1
    else:
        probs["RANGE"] = 0.4
        probs["TRANSITION"] = 0.3
        probs["BULL"] = 0.15
        probs["BEAR"] = 0.15

    # Ajustement MACD
    if not np.isnan(macd_hist):
        if macd_hist > 0:
            probs["BULL"] = min(1.0, probs["BULL"] + 0.1)
            probs["BEAR"] = max(0.0, probs["BEAR"] - 0.05)
        else:
            probs["BEAR"] = min(1.0, probs["BEAR"] + 0.1)
            probs["BULL"] = max(0.0, probs["BULL"] - 0.05)

    # Normaliser
    total = sum(probs.values())
    if total > 0:
        probs = {k: v / total for k, v in probs.items()}

    return probs


def _structure_signal(close: pd.Series) -> dict:
    """Signal de structure : position dans le range 52 semaines."""
    if len(close) < 252:
        return {r: 0.2 for r in REGIMES}

    high_52w = close.iloc[-252:].max()
    low_52w = close.iloc[-252:].min()
    last = close.iloc[-1]

    if high_52w == low_52w:
        return {r: 0.2 for r in REGIMES}

    position = (last - low_52w) / (high_52w - low_52w)  # 0 = plus bas, 1 = plus haut

    probs = {"BULL": 0.0, "BEAR": 0.0, "RANGE": 0.0, "CRISIS": 0.0, "TRANSITION": 0.0}

    if position > 0.85:
        probs["BULL"] = 0.7
        probs["TRANSITION"] = 0.2
        probs["RANGE"] = 0.1
    elif position > 0.6:
        probs["BULL"] = 0.4
        probs["RANGE"] = 0.35
        probs["TRANSITION"] = 0.25
    elif position > 0.4:
        probs["RANGE"] = 0.5
        probs["TRANSITION"] = 0.25
        probs["BULL"] = 0.1
        probs["BEAR"] = 0.15
    elif position > 0.15:
        probs["BEAR"] = 0.5
        probs["RANGE"] = 0.2
        probs["TRANSITION"] = 0.2
        probs["CRISIS"] = 0.1
    else:
        probs["BEAR"] = 0.4
        probs["CRISIS"] = 0.4
        probs["TRANSITION"] = 0.2

    return probs


def detect_regime(close: pd.Series, high: pd.Series, low: pd.Series) -> dict:
    """Détection probabiliste du régime de marché.

    Combine 4 signaux indépendants avec pondération égale.
    Retourne les probabilités pour chaque régime.
    """
    if len(close) < 200:
        return {
            "regime": "UNKNOWN",
            "probabilities": {r: 0.2 for r in REGIMES},
            "confidence": 0.0,
        }

    signals = [
        _trend_signal(close),
        _volatility_signal(high, low, close),
        _momentum_signal(close),
        _structure_signal(close),
    ]

    # Moyenne des probabilités
    combined = {r: 0.0 for r in REGIMES}
    weights = [0.30, 0.25, 0.25, 0.20]  # tendance pèse un peu plus

    for signal, weight in zip(signals, weights):
        for regime in REGIMES:
            combined[regime] += signal.get(regime, 0) * weight

    # Normaliser
    total = sum(combined.values())
    if total > 0:
        combined = {k: round(v / total, 3) for k, v in combined.items()}

    # Régime dominant
    dominant = max(combined, key=combined.get)
    confidence = combined[dominant]

    return {
        "regime": dominant,
        "probabilities": combined,
        "confidence": round(confidence, 3),
    }
