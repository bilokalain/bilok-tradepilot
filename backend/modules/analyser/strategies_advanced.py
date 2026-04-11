"""Stratégies avancées — Phase 2

1. Pairs Trading — exploiter la relation entre deux actifs corrélés
2. Mean Reversion Améliorée — z-score + Keltner Channels + volume profile
3. Fibonacci Retracement — niveaux de support/résistance naturels
4. Ichimoku Cloud — système complet japonais (tendance + support + timing)
"""

import numpy as np
import pandas as pd

from backend.modules.scanner.indicators import sma, ema, rsi, atr, bollinger_bands


# ============================================================
# 1. Pairs Trading
# ============================================================

def compute_spread(close_a: pd.Series, close_b: pd.Series) -> pd.Series:
    """Calcule le spread normalisé entre deux actifs."""
    # Normaliser les prix (ratio)
    ratio = close_a / close_b
    # Z-score du ratio
    mean = ratio.rolling(60).mean()
    std = ratio.rolling(60).std()
    zscore = (ratio - mean) / std.replace(0, np.nan)
    return zscore


def strategy_pairs_trading(close_a: pd.Series, close_b: pd.Series,
                            symbol_a: str, symbol_b: str) -> dict:
    """Pairs Trading — entre quand le spread est extrême.

    Z-score > 2 : vendre A, acheter B (le spread va se resserrer)
    Z-score < -2 : acheter A, vendre B
    """
    if len(close_a) < 60 or len(close_b) < 60:
        return {"strategy": "pairs_trading", "direction": "NEUTRAL", "conviction": 0}

    # Aligner les séries
    aligned = pd.DataFrame({"a": close_a, "b": close_b}).dropna()
    if len(aligned) < 60:
        return {"strategy": "pairs_trading", "direction": "NEUTRAL", "conviction": 0}

    zscore = compute_spread(aligned["a"], aligned["b"])
    current_z = zscore.iloc[-1]

    if np.isnan(current_z):
        return {"strategy": "pairs_trading", "direction": "NEUTRAL", "conviction": 0}

    # Corrélation (le pairs trading ne marche que si les actifs sont corrélés)
    corr = aligned["a"].pct_change().corr(aligned["b"].pct_change())
    if abs(corr) < 0.5:
        return {
            "strategy": "pairs_trading",
            "direction": "NEUTRAL",
            "conviction": 0,
            "reason": f"Corrélation trop faible ({corr:.2f})",
        }

    direction = "NEUTRAL"
    conviction = 0

    if current_z > 2.5:
        direction = "SHORT"  # Vendre A (surévalué vs B)
        conviction = min(95, 60 + abs(current_z) * 10)
    elif current_z > 2.0:
        direction = "SHORT"
        conviction = 55
    elif current_z < -2.5:
        direction = "LONG"  # Acheter A (sous-évalué vs B)
        conviction = min(95, 60 + abs(current_z) * 10)
    elif current_z < -2.0:
        direction = "LONG"
        conviction = 55

    return {
        "strategy": "pairs_trading",
        "direction": direction,
        "conviction": round(conviction, 1),
        "zscore": round(current_z, 3),
        "correlation": round(corr, 3),
        "pair": f"{symbol_a}/{symbol_b}",
    }


# ============================================================
# 2. Mean Reversion Améliorée
# ============================================================

def keltner_channels(close: pd.Series, high: pd.Series,
                      low: pd.Series, period: int = 20,
                      atr_mult: float = 1.5) -> dict:
    """Keltner Channels — bandes basées sur ATR (plus robuste que Bollinger)."""
    middle = ema(close, period)
    atr_val = atr(high, low, close, period)
    upper = middle + atr_mult * atr_val
    lower = middle - atr_mult * atr_val
    return {"upper": upper, "middle": middle, "lower": lower}


def compute_zscore(close: pd.Series, period: int = 60) -> pd.Series:
    """Z-score du prix par rapport à sa moyenne mobile."""
    mean = close.rolling(period).mean()
    std = close.rolling(period).std()
    return (close - mean) / std.replace(0, np.nan)


def strategy_mean_reversion_v2(close: pd.Series, high: pd.Series,
                                low: pd.Series, volume: pd.Series) -> dict:
    """Mean Reversion Améliorée.

    Combine :
    - Z-score (> 2 = suracheté, < -2 = survendu)
    - Keltner Channels (confirmation)
    - Volume profile (volume en baisse = épuisement du mouvement)
    - RSI divergence
    """
    if len(close) < 60:
        return {"strategy": "mean_reversion_v2", "direction": "NEUTRAL", "conviction": 0}

    last = close.iloc[-1]
    z = compute_zscore(close).iloc[-1]
    rsi_val = rsi(close, 14).iloc[-1]
    kc = keltner_channels(close, high, low)
    kc_upper = kc["upper"].iloc[-1]
    kc_lower = kc["lower"].iloc[-1]
    atr_val = atr(high, low, close, 14).iloc[-1]

    if any(np.isnan(v) for v in [z, rsi_val, kc_upper, kc_lower, atr_val]):
        return {"strategy": "mean_reversion_v2", "direction": "NEUTRAL", "conviction": 0}

    # Volume en déclin (3 derniers jours < moyenne)
    vol_avg = volume.iloc[-20:].mean()
    vol_recent = volume.iloc[-3:].mean()
    volume_exhaustion = vol_recent < vol_avg * 0.7

    signals_bull = 0
    signals_bear = 0

    # Z-score
    if z < -2.0:
        signals_bull += 2
    elif z < -1.5:
        signals_bull += 1
    elif z > 2.0:
        signals_bear += 2
    elif z > 1.5:
        signals_bear += 1

    # Keltner
    if last < kc_lower:
        signals_bull += 1
    elif last > kc_upper:
        signals_bear += 1

    # RSI extrême
    if rsi_val < 25:
        signals_bull += 2
    elif rsi_val < 35:
        signals_bull += 1
    elif rsi_val > 75:
        signals_bear += 2
    elif rsi_val > 65:
        signals_bear += 1

    # Volume exhaustion (confirme le retournement)
    if volume_exhaustion:
        if signals_bull > 0:
            signals_bull += 1
        if signals_bear > 0:
            signals_bear += 1

    direction = "NEUTRAL"
    conviction = 0

    if signals_bull >= 3:
        direction = "LONG"
        conviction = min(95, 50 + signals_bull * 10)
    elif signals_bear >= 3:
        direction = "SHORT"
        conviction = min(95, 50 + signals_bear * 10)

    return {
        "strategy": "mean_reversion_v2",
        "direction": direction,
        "conviction": round(conviction, 1),
        "zscore": round(z, 3),
        "rsi": round(rsi_val, 1),
        "volume_exhaustion": volume_exhaustion,
        "entry": round(last, 2),
        "stop_loss": round(last - 2 * atr_val, 2) if direction == "LONG" else round(last + 2 * atr_val, 2),
        "take_profit": round(kc["middle"].iloc[-1], 2),  # Retour à la moyenne
    }


# ============================================================
# 3. Fibonacci Retracement
# ============================================================

FIBONACCI_LEVELS = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]


def compute_fibonacci_levels(high_price: float, low_price: float,
                              trend: str = "up") -> dict:
    """Calcule les niveaux de Fibonacci entre un haut et un bas.

    Trend up : retracement depuis le haut
    Trend down : retracement depuis le bas
    """
    diff = high_price - low_price
    levels = {}

    for fib in FIBONACCI_LEVELS:
        if trend == "up":
            price = high_price - diff * fib
        else:
            price = low_price + diff * fib
        levels[f"{fib:.3f}"] = round(price, 2)

    return levels


def strategy_fibonacci(close: pd.Series, high: pd.Series,
                        low: pd.Series) -> dict:
    """Fibonacci Retracement Strategy.

    Détecte le swing high/low récent et entre sur les niveaux de Fibonacci.
    Les niveaux 0.382, 0.5 et 0.618 sont les plus importants.
    """
    if len(close) < 60:
        return {"strategy": "fibonacci", "direction": "NEUTRAL", "conviction": 0}

    last = close.iloc[-1]
    atr_val = atr(high, low, close, 14).iloc[-1]

    if np.isnan(atr_val):
        return {"strategy": "fibonacci", "direction": "NEUTRAL", "conviction": 0}

    # Trouver le swing high et low des 60 derniers jours
    swing_high = high.iloc[-60:].max()
    swing_low = low.iloc[-60:].min()
    swing_range = swing_high - swing_low

    if swing_range == 0:
        return {"strategy": "fibonacci", "direction": "NEUTRAL", "conviction": 0}

    # Déterminer la tendance (le dernier swing est-il un high ou un low ?)
    high_idx = high.iloc[-60:].idxmax()
    low_idx = low.iloc[-60:].idxmin()
    trend = "up" if low_idx < high_idx else "down"

    levels = compute_fibonacci_levels(swing_high, swing_low, trend)

    # Position du prix par rapport aux niveaux
    fib_382 = swing_high - swing_range * 0.382 if trend == "up" else swing_low + swing_range * 0.382
    fib_500 = swing_high - swing_range * 0.500 if trend == "up" else swing_low + swing_range * 0.500
    fib_618 = swing_high - swing_range * 0.618 if trend == "up" else swing_low + swing_range * 0.618

    direction = "NEUTRAL"
    conviction = 0
    nearest_level = ""

    if trend == "up":
        # Tendance haussière — chercher un rebond sur support Fibonacci
        if abs(last - fib_618) / last < 0.01:
            direction = "LONG"
            conviction = 80
            nearest_level = "0.618 (Golden Ratio)"
        elif abs(last - fib_500) / last < 0.01:
            direction = "LONG"
            conviction = 70
            nearest_level = "0.500"
        elif abs(last - fib_382) / last < 0.01:
            direction = "LONG"
            conviction = 60
            nearest_level = "0.382"
        elif last > fib_382 and last < swing_high:
            direction = "LONG"
            conviction = 45  # Au-dessus du 38.2% = tendance intacte
            nearest_level = "au-dessus de 0.382"
    else:
        # Tendance baissière — chercher un rejet sur résistance Fibonacci
        if abs(last - fib_618) / last < 0.01:
            direction = "SHORT"
            conviction = 80
            nearest_level = "0.618 (Golden Ratio)"
        elif abs(last - fib_500) / last < 0.01:
            direction = "SHORT"
            conviction = 70
            nearest_level = "0.500"
        elif abs(last - fib_382) / last < 0.01:
            direction = "SHORT"
            conviction = 60
            nearest_level = "0.382"

    return {
        "strategy": "fibonacci",
        "direction": direction,
        "conviction": round(conviction, 1),
        "trend": trend,
        "swing_high": round(swing_high, 2),
        "swing_low": round(swing_low, 2),
        "nearest_level": nearest_level,
        "levels": levels,
        "entry": round(last, 2),
        "stop_loss": round(last - 2 * atr_val, 2) if direction == "LONG" else round(last + 2 * atr_val, 2),
        "take_profit": round(swing_high, 2) if direction == "LONG" else round(swing_low, 2),
    }


# ============================================================
# 4. Ichimoku Cloud
# ============================================================

def compute_ichimoku(high: pd.Series, low: pd.Series, close: pd.Series) -> dict:
    """Calcule les composantes Ichimoku.

    - Tenkan-sen (conversion line) : (9-period high + 9-period low) / 2
    - Kijun-sen (base line) : (26-period high + 26-period low) / 2
    - Senkou Span A : (Tenkan + Kijun) / 2, projeté 26 périodes en avant
    - Senkou Span B : (52-period high + 52-period low) / 2, projeté 26
    - Chikou Span : close projeté 26 périodes en arrière
    """
    tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
    kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
    chikou = close.shift(-26)

    return {
        "tenkan": tenkan,
        "kijun": kijun,
        "senkou_a": senkou_a,
        "senkou_b": senkou_b,
        "chikou": chikou,
    }


def strategy_ichimoku(close: pd.Series, high: pd.Series, low: pd.Series) -> dict:
    """Ichimoku Cloud Strategy.

    Signaux :
    - Prix au-dessus du cloud = bullish
    - Tenkan > Kijun = bullish crossover
    - Chikou au-dessus du prix d'il y a 26 périodes = confirmation
    """
    if len(close) < 80:
        return {"strategy": "ichimoku", "direction": "NEUTRAL", "conviction": 0}

    ichi = compute_ichimoku(high, low, close)
    last = close.iloc[-1]
    atr_val = atr(high, low, close, 14).iloc[-1]

    tenkan_val = ichi["tenkan"].iloc[-1]
    kijun_val = ichi["kijun"].iloc[-1]
    span_a = ichi["senkou_a"].iloc[-1]
    span_b = ichi["senkou_b"].iloc[-1]

    if any(np.isnan(v) for v in [tenkan_val, kijun_val, span_a, span_b, atr_val]):
        return {"strategy": "ichimoku", "direction": "NEUTRAL", "conviction": 0}

    cloud_top = max(span_a, span_b)
    cloud_bottom = min(span_a, span_b)

    bullish = 0
    bearish = 0

    # Prix vs Cloud
    if last > cloud_top:
        bullish += 2
    elif last < cloud_bottom:
        bearish += 2
    # Dans le cloud = neutre

    # Tenkan vs Kijun
    if tenkan_val > kijun_val:
        bullish += 1
    elif tenkan_val < kijun_val:
        bearish += 1

    # Cloud future (span_a vs span_b)
    if span_a > span_b:
        bullish += 1  # Cloud vert
    else:
        bearish += 1  # Cloud rouge

    direction = "NEUTRAL"
    conviction = 0

    if bullish >= 3:
        direction = "LONG"
        conviction = min(90, 50 + bullish * 10)
    elif bearish >= 3:
        direction = "SHORT"
        conviction = min(90, 50 + bearish * 10)

    return {
        "strategy": "ichimoku",
        "direction": direction,
        "conviction": round(conviction, 1),
        "price_vs_cloud": "above" if last > cloud_top else "below" if last < cloud_bottom else "inside",
        "tenkan_kijun": "bullish" if tenkan_val > kijun_val else "bearish",
        "cloud_color": "green" if span_a > span_b else "red",
        "entry": round(last, 2),
        "stop_loss": round(last - 2 * atr_val, 2) if direction == "LONG" else round(last + 2 * atr_val, 2),
        "take_profit": round(last + 3 * atr_val, 2) if direction == "LONG" else round(last - 3 * atr_val, 2),
    }
