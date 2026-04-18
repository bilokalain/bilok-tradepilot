"""Multi-Timeframe Analysis (MTA) V2

Compare les signaux sur 4 timeframes hiérarchiques :
- Weekly  (tendance de fond, poids 35%)
- Daily   (tendance principale, poids 30%)
- 4H      (tendance intermédiaire, poids 20%) — construit depuis les barres 1H
- 1H      (timing d'entrée, poids 15%)

Principe : un signal est fort quand TOUS les timeframes s'alignent.
Le weekly donne la direction, le 1H donne le timing.

Score MTA (0-100) :
- 90+ : 4/4 timeframes alignés → signal très fort
- 75+ : 3/4 alignés → signal fort
- 60+ : 2/4 alignés → signal modéré
- 50  : mixte → pas de conviction
- <40 : divergence multi-TF → contre-signal / prudence

Indicateurs par timeframe :
- Tendance : SMA 20/50 + position du prix
- Momentum : RSI(14) + MACD histogram
- Volume   : ratio volume récent vs moyen
- Structure : plus haut/bas 20 périodes
"""

import numpy as np
import pandas as pd

from backend.modules.scanner.indicators import sma, ema, rsi, macd, atr, bollinger_bands


# Poids hiérarchiques par timeframe
TF_WEIGHTS = {
    "weekly": 0.35,
    "daily": 0.30,
    "4h": 0.20,
    "1h": 0.15,
}

TF_LABELS = {
    "weekly": "Hebdomadaire",
    "daily": "Journalier",
    "4h": "4 Heures",
    "1h": "1 Heure",
}


def _resample_to_4h(df_1h: pd.DataFrame) -> pd.DataFrame:
    """Construit des barres 4H à partir des barres 1H."""
    if df_1h.empty or len(df_1h) < 4:
        return pd.DataFrame()

    df = df_1h.copy()
    if "datetime" in df.columns:
        df.index = pd.to_datetime(df["datetime"])
    elif not isinstance(df.index, pd.DatetimeIndex):
        return pd.DataFrame()

    resampled = df.resample("4h").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna()

    return resampled


def _resample_to_weekly(df_daily: pd.DataFrame) -> pd.DataFrame:
    """Construit des barres Weekly à partir des barres Daily."""
    if df_daily.empty or len(df_daily) < 5:
        return pd.DataFrame()

    df = df_daily.copy()
    if "date" in df.columns:
        df.index = pd.to_datetime(df["date"])
    elif not isinstance(df.index, pd.DatetimeIndex):
        return pd.DataFrame()

    resampled = df.resample("W").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna()

    return resampled


def analyse_timeframe_v2(close: pd.Series, high: pd.Series, low: pd.Series,
                          volume: pd.Series, tf_name: str) -> dict:
    """Analyse complète d'un timeframe avec 6 indicateurs."""
    if len(close) < 30:
        return {
            "direction": "NEUTRAL", "strength": 0, "score": 50,
            "timeframe": tf_name, "label": TF_LABELS.get(tf_name, tf_name),
            "indicators": {}, "signals": {},
        }

    last = float(close.iloc[-1])

    # 1. Tendance (SMA 20/50)
    sma_20 = float(sma(close, 20).iloc[-1])
    sma_50 = float(sma(close, min(50, len(close) - 1)).iloc[-1]) if len(close) > 50 else float(sma(close, 20).iloc[-1])

    trend = 0
    trend_signal = "Neutre"
    if last > sma_20 > sma_50:
        trend = 2
        trend_signal = "Haussier fort"
    elif last > sma_20:
        trend = 1
        trend_signal = "Haussier"
    elif last < sma_20 < sma_50:
        trend = -2
        trend_signal = "Baissier fort"
    elif last < sma_20:
        trend = -1
        trend_signal = "Baissier"

    # 2. RSI
    rsi_val = float(rsi(close, 14).iloc[-1]) if len(close) >= 14 else 50
    rsi_signal = "Suracheté" if rsi_val > 70 else "Survendu" if rsi_val < 30 else "Haussier" if rsi_val > 55 else "Baissier" if rsi_val < 45 else "Neutre"
    rsi_score = 1 if rsi_val > 55 else (-1 if rsi_val < 45 else 0)

    # 3. MACD
    macd_data = macd(close)
    macd_hist = float(macd_data["histogram"].iloc[-1]) if not np.isnan(macd_data["histogram"].iloc[-1]) else 0
    macd_line = float(macd_data["macd"].iloc[-1]) if not np.isnan(macd_data["macd"].iloc[-1]) else 0
    macd_signal_line = float(macd_data["signal"].iloc[-1]) if not np.isnan(macd_data["signal"].iloc[-1]) else 0
    macd_score = 1 if macd_hist > 0 else -1
    macd_signal = "Haussier" if macd_hist > 0 else "Baissier"

    # 4. Volume
    vol_avg = float(volume.iloc[-20:].mean()) if len(volume) >= 20 else float(volume.mean())
    vol_current = float(volume.iloc[-1])
    vol_ratio = vol_current / vol_avg if vol_avg > 0 else 1
    vol_signal = "Fort" if vol_ratio > 1.5 else "Normal" if vol_ratio > 0.8 else "Faible"

    # 5. Structure (breakout)
    high_20 = float(high.iloc[-20:].max()) if len(high) >= 20 else float(high.max())
    low_20 = float(low.iloc[-20:].min()) if len(low) >= 20 else float(low.min())
    position_in_range = (last - low_20) / (high_20 - low_20) if high_20 != low_20 else 0.5
    structure_signal = "Breakout haut" if position_in_range > 0.9 else "Haut de range" if position_in_range > 0.7 else "Milieu" if position_in_range > 0.3 else "Bas de range" if position_in_range > 0.1 else "Breakout bas"
    structure_score = 1 if position_in_range > 0.7 else (-1 if position_in_range < 0.3 else 0)

    # 6. ATR (volatilité)
    atr_val = float(atr(high, low, close, 14).iloc[-1]) if len(close) >= 14 else 0
    atr_pct = (atr_val / last * 100) if last > 0 else 0

    # Score composite
    total_bullish = max(0, trend) + max(0, rsi_score) + max(0, macd_score) + max(0, structure_score)
    total_bearish = abs(min(0, trend)) + abs(min(0, rsi_score)) + abs(min(0, macd_score)) + abs(min(0, structure_score))
    total_signals = total_bullish + total_bearish

    if total_signals == 0:
        direction = "NEUTRAL"
        strength = 0
        score = 50
    elif total_bullish > total_bearish:
        direction = "BULLISH"
        strength = round(total_bullish / total_signals * 100, 1)
        score = 50 + strength * 0.45
    else:
        direction = "BEARISH"
        strength = round(total_bearish / total_signals * 100, 1)
        score = 50 - strength * 0.45

    score = max(0, min(100, score))

    return {
        "direction": direction,
        "strength": strength,
        "score": round(score, 1),
        "timeframe": tf_name,
        "label": TF_LABELS.get(tf_name, tf_name),
        "bullish_count": total_bullish,
        "bearish_count": total_bearish,
        "indicators": {
            "price": round(last, 2),
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "rsi": round(rsi_val, 1),
            "macd_hist": round(macd_hist, 4),
            "macd_line": round(macd_line, 4),
            "macd_signal": round(macd_signal_line, 4),
            "volume_ratio": round(vol_ratio, 2),
            "high_20": round(high_20, 2),
            "low_20": round(low_20, 2),
            "position_in_range": round(position_in_range * 100, 1),
            "atr": round(atr_val, 2),
            "atr_pct": round(atr_pct, 2),
        },
        "signals": {
            "trend": trend_signal,
            "rsi": rsi_signal,
            "macd": macd_signal,
            "volume": vol_signal,
            "structure": structure_signal,
        },
    }


def compute_mta_score(daily_close: pd.Series,
                      hourly_close: pd.Series | None = None,
                      daily_high: pd.Series | None = None,
                      daily_low: pd.Series | None = None,
                      daily_volume: pd.Series | None = None,
                      hourly_high: pd.Series | None = None,
                      hourly_low: pd.Series | None = None,
                      hourly_volume: pd.Series | None = None,
                      daily_df: pd.DataFrame | None = None,
                      hourly_df: pd.DataFrame | None = None) -> dict:
    """Score Multi-Timeframe V2 — 4 timeframes hiérarchiques.

    Args:
        daily_close/high/low/volume: séries daily
        hourly_close/high/low/volume: séries 1H
        daily_df: DataFrame daily complet (pour resample weekly)
        hourly_df: DataFrame 1H complet (pour resample 4H)
    """
    # Fallback pour high/low/volume si pas fournis
    if daily_high is None:
        daily_high = daily_close
    if daily_low is None:
        daily_low = daily_close
    if daily_volume is None:
        daily_volume = pd.Series(np.ones(len(daily_close)))

    timeframes = {}

    # 1. Weekly (depuis daily)
    if daily_df is not None and len(daily_df) >= 100:
        weekly_df = _resample_to_weekly(daily_df)
        if len(weekly_df) >= 30:
            timeframes["weekly"] = analyse_timeframe_v2(
                weekly_df["close"], weekly_df["high"], weekly_df["low"],
                weekly_df["volume"], "weekly"
            )

    if "weekly" not in timeframes and len(daily_close) >= 200:
        # Approximation : prendre 1 barre sur 5
        weekly_close = daily_close.iloc[::5].reset_index(drop=True)
        weekly_high = daily_high.iloc[::5].reset_index(drop=True)
        weekly_low = daily_low.iloc[::5].reset_index(drop=True)
        weekly_vol = daily_volume.iloc[::5].reset_index(drop=True)
        if len(weekly_close) >= 30:
            timeframes["weekly"] = analyse_timeframe_v2(
                weekly_close, weekly_high, weekly_low, weekly_vol, "weekly"
            )

    # 2. Daily
    timeframes["daily"] = analyse_timeframe_v2(
        daily_close, daily_high, daily_low, daily_volume, "daily"
    )

    # 3. 4H (depuis 1H)
    if hourly_df is not None and len(hourly_df) >= 20:
        h4_df = _resample_to_4h(hourly_df)
        if len(h4_df) >= 30:
            timeframes["4h"] = analyse_timeframe_v2(
                h4_df["close"], h4_df["high"], h4_df["low"],
                h4_df["volume"], "4h"
            )

    # 4. 1H
    if hourly_close is not None and len(hourly_close) >= 30:
        if hourly_high is None:
            hourly_high = hourly_close
        if hourly_low is None:
            hourly_low = hourly_close
        if hourly_volume is None:
            hourly_volume = pd.Series(np.ones(len(hourly_close)))
        timeframes["1h"] = analyse_timeframe_v2(
            hourly_close, hourly_high, hourly_low, hourly_volume, "1h"
        )

    # Score d'alignement pondéré
    n_tf = len(timeframes)
    if n_tf == 0:
        return {"mta_score": 50, "alignment": "NO_DATA", "timeframes": {}}

    bullish_weight = 0
    bearish_weight = 0
    total_weight = 0

    for tf_name, tf_data in timeframes.items():
        w = TF_WEIGHTS.get(tf_name, 0.1)
        total_weight += w
        if tf_data["direction"] == "BULLISH":
            bullish_weight += w * (tf_data["strength"] / 100)
        elif tf_data["direction"] == "BEARISH":
            bearish_weight += w * (tf_data["strength"] / 100)

    if total_weight > 0:
        bullish_weight /= total_weight
        bearish_weight /= total_weight

    net = bullish_weight - bearish_weight  # -1 à +1

    # Score final : 50 + net * 45
    score = 50 + net * 45
    score = max(0, min(100, score))

    # Alignement
    directions = [tf["direction"] for tf in timeframes.values() if tf["direction"] != "NEUTRAL"]
    if len(directions) == 0:
        alignment = "NEUTRAL"
    elif all(d == directions[0] for d in directions):
        alignment = "ALIGNED"
    elif len(set(directions)) == 1:
        alignment = "MOSTLY_ALIGNED"
    else:
        n_bull = sum(1 for d in directions if d == "BULLISH")
        n_bear = sum(1 for d in directions if d == "BEARISH")
        if n_bull > n_bear:
            alignment = "MOSTLY_BULLISH"
        elif n_bear > n_bull:
            alignment = "MOSTLY_BEARISH"
        else:
            alignment = "DIVERGENT"

    # Convergence : combien de TF sont d'accord
    convergence = max(
        sum(1 for tf in timeframes.values() if tf["direction"] == "BULLISH"),
        sum(1 for tf in timeframes.values() if tf["direction"] == "BEARISH"),
    )

    return {
        "mta_score": round(score, 2),
        "alignment": alignment,
        "convergence": f"{convergence}/{n_tf}",
        "direction": "BULLISH" if net > 0.1 else "BEARISH" if net < -0.1 else "NEUTRAL",
        "n_timeframes": n_tf,
        "timeframes": timeframes,
    }
