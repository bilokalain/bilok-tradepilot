"""Indicateurs techniques — 6 familles d'analyse

Tendance : SMA, EMA
Momentum : RSI, MACD, Stochastique
Volatilité : Bollinger Bands, ATR
Volume : OBV, Volume SMA
Structure de Prix : Support/Résistance
Chandeliers : (à implémenter)
"""

import numpy as np
import pandas as pd


def sma(closes: pd.Series, period: int = 20) -> pd.Series:
    """Simple Moving Average."""
    return closes.rolling(window=period).mean()


def ema(closes: pd.Series, period: int = 20) -> pd.Series:
    """Exponential Moving Average."""
    return closes.ewm(span=period, adjust=False).mean()


def rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (0-100)."""
    delta = closes.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(closes: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """MACD — Moving Average Convergence Divergence."""
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def bollinger_bands(closes: pd.Series, period: int = 20, std_dev: float = 2.0) -> dict:
    """Bandes de Bollinger."""
    middle = sma(closes, period)
    std = closes.rolling(window=period).std()
    return {
        "upper": middle + std_dev * std,
        "middle": middle,
        "lower": middle - std_dev * std,
    }


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range — mesure de volatilité."""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
               k_period: int = 14, d_period: int = 3) -> dict:
    """Oscillateur Stochastique (%K et %D)."""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    d = k.rolling(window=d_period).mean()
    return {"k": k, "d": d}


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume — confirmation par le volume."""
    direction = np.sign(close.diff())
    direction.iloc[0] = 0
    return (volume * direction).cumsum()


def volume_sma(volume: pd.Series, period: int = 20) -> pd.Series:
    """Moyenne mobile du volume."""
    return volume.rolling(window=period).mean()


def compute_technical_score(close: pd.Series, high: pd.Series,
                            low: pd.Series, volume: pd.Series) -> float:
    """Score technique composite (0-100) basé sur les indicateurs.

    Combine :
    - Tendance (SMA 20/50/200) : 25%
    - Momentum (RSI, MACD) : 30%
    - Volatilité (Bollinger, ATR) : 20%
    - Volume (OBV trend) : 25%
    """
    score = 50.0  # neutre par défaut
    last = close.iloc[-1]

    # --- Tendance (25%) ---
    sma_20 = sma(close, 20).iloc[-1]
    sma_50 = sma(close, 50).iloc[-1]
    sma_200 = sma(close, 200).iloc[-1]

    trend_score = 50.0
    if not np.isnan(sma_200):
        if last > sma_20 > sma_50 > sma_200:
            trend_score = 90.0  # Tendance haussière forte
        elif last > sma_50 > sma_200:
            trend_score = 70.0
        elif last < sma_20 < sma_50 < sma_200:
            trend_score = 10.0  # Tendance baissière forte
        elif last < sma_50 < sma_200:
            trend_score = 30.0

    # --- Momentum (30%) ---
    rsi_val = rsi(close).iloc[-1]
    macd_data = macd(close)
    macd_hist = macd_data["histogram"].iloc[-1]

    momentum_score = 50.0
    if not np.isnan(rsi_val):
        if rsi_val > 70:
            momentum_score = 80.0  # Surachat (bullish momentum)
        elif rsi_val > 50:
            momentum_score = 60.0 + (rsi_val - 50) * 0.5
        elif rsi_val < 30:
            momentum_score = 20.0  # Survente
        else:
            momentum_score = 40.0 - (50 - rsi_val) * 0.5

        if not np.isnan(macd_hist):
            if macd_hist > 0:
                momentum_score = min(100, momentum_score + 10)
            else:
                momentum_score = max(0, momentum_score - 10)

    # --- Volatilité (20%) ---
    bb = bollinger_bands(close)
    bb_upper = bb["upper"].iloc[-1]
    bb_lower = bb["lower"].iloc[-1]

    vol_score = 50.0
    if not np.isnan(bb_upper) and not np.isnan(bb_lower) and bb_upper != bb_lower:
        bb_position = (last - bb_lower) / (bb_upper - bb_lower)
        vol_score = bb_position * 100
        vol_score = max(0, min(100, vol_score))

    # --- Volume (25%) ---
    obv_series = obv(close, volume)
    vol_sma_val = volume_sma(volume).iloc[-1]
    current_vol = volume.iloc[-1]

    volume_score = 50.0
    if not np.isnan(vol_sma_val) and vol_sma_val > 0:
        vol_ratio = current_vol / vol_sma_val
        if vol_ratio > 1.5:
            volume_score = 80.0  # Volume élevé
        elif vol_ratio > 1.0:
            volume_score = 60.0
        else:
            volume_score = 40.0

        # OBV trend
        if len(obv_series) >= 20:
            obv_trend = obv_series.iloc[-1] - obv_series.iloc[-20]
            if obv_trend > 0:
                volume_score = min(100, volume_score + 10)
            else:
                volume_score = max(0, volume_score - 10)

    # --- Score final pondéré ---
    score = (
        trend_score * 0.25 +
        momentum_score * 0.30 +
        vol_score * 0.20 +
        volume_score * 0.25
    )

    return round(max(0, min(100, score)), 2)
