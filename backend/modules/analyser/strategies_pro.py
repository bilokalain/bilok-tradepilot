"""Stratégies professionnelles — remplacent les stratégies basiques

1. Adaptive Parameters — EMA/RSI/ATR s'adaptent à la volatilité de l'actif
2. Regime-Aware — ne trade QUE dans le bon régime
3. Multi-Signal Confirmation — exige 3+ indicateurs alignés
4. Volatility Breakout (Keltner) — breakout adaptatif basé sur ATR
5. VWAP Reversion — mean reversion autour du prix moyen pondéré par volume
6. Momentum Rotation — achète les plus forts, vend les plus faibles
7. Pairs Statistical Arbitrage — exploite les déviations de spread
"""

import numpy as np
import pandas as pd

from backend.modules.scanner.indicators import sma, ema, rsi, macd, atr, bollinger_bands, stochastic, obv


# ============================================================
# 1. ADAPTIVE PARAMETERS
# ============================================================

def compute_adaptive_periods(close: pd.Series, high: pd.Series,
                              low: pd.Series) -> dict:
    """Calcule les périodes optimales selon la volatilité.

    Marché calme → périodes longues (lissage)
    Marché volatile → périodes courtes (réactivité)
    """
    if len(close) < 100:
        return {"ema_fast": 9, "ema_slow": 21, "rsi_period": 14, "atr_mult": 2.0}

    atr_series = atr(high, low, close, 14)
    atr_current = float(atr_series.iloc[-1])
    atr_avg = float(atr_series.iloc[-60:].mean())

    if atr_avg == 0:
        vol_ratio = 1.0
    else:
        vol_ratio = atr_current / atr_avg

    if vol_ratio > 1.5:
        # Haute volatilité → périodes courtes, stops larges
        return {"ema_fast": 5, "ema_slow": 13, "rsi_period": 10, "atr_mult": 2.5}
    elif vol_ratio > 1.2:
        return {"ema_fast": 8, "ema_slow": 18, "rsi_period": 12, "atr_mult": 2.2}
    elif vol_ratio < 0.7:
        # Basse volatilité → périodes longues, stops serrés
        return {"ema_fast": 13, "ema_slow": 34, "rsi_period": 18, "atr_mult": 1.5}
    else:
        return {"ema_fast": 9, "ema_slow": 21, "rsi_period": 14, "atr_mult": 2.0}


def strategy_adaptive_trend(close: pd.Series, high: pd.Series,
                             low: pd.Series, volume: pd.Series) -> dict:
    """Trend Following avec paramètres adaptatifs.

    Les périodes EMA, RSI et les multiplicateurs ATR s'ajustent
    automatiquement à la volatilité de l'actif.
    """
    if len(close) < 100:
        return {"strategy": "adaptive_trend", "direction": "NEUTRAL", "conviction": 0}

    params = compute_adaptive_periods(close, high, low)
    ema_f = ema(close, params["ema_fast"])
    ema_s = ema(close, params["ema_slow"])
    rsi_val = rsi(close, params["rsi_period"]).iloc[-1]
    atr_val = atr(high, low, close, 14).iloc[-1]
    obv_series = obv(close, volume)

    last = close.iloc[-1]
    ef = ema_f.iloc[-1]
    es = ema_s.iloc[-1]
    ef_prev = ema_f.iloc[-2]
    es_prev = ema_s.iloc[-2]

    if any(np.isnan(v) for v in [ef, es, rsi_val, atr_val]):
        return {"strategy": "adaptive_trend", "direction": "NEUTRAL", "conviction": 0}

    # OBV confirmation
    obv_rising = obv_series.iloc[-1] > obv_series.iloc[-10] if len(obv_series) >= 10 else True

    direction = "NEUTRAL"
    conviction = 0

    # Crossover haussier + RSI pas suracheté + OBV confirme
    if ef > es and ef_prev <= es_prev and rsi_val < 75 and obv_rising:
        direction = "LONG"
        conviction = 80
    elif ef > es and rsi_val > 45 and obv_rising:
        direction = "LONG"
        conviction = 60
    # Crossover baissier
    elif ef < es and ef_prev >= es_prev and rsi_val > 25:
        direction = "SHORT"
        conviction = 80
    elif ef < es and rsi_val < 55:
        direction = "SHORT"
        conviction = 60

    sl_mult = params["atr_mult"]
    tp_mult = sl_mult * 1.5

    return {
        "strategy": "adaptive_trend",
        "direction": direction,
        "conviction": round(conviction, 1),
        "entry": round(last, 2),
        "stop_loss": round(last - sl_mult * atr_val, 2) if direction == "LONG" else round(last + sl_mult * atr_val, 2),
        "take_profit": round(last + tp_mult * atr_val, 2) if direction == "LONG" else round(last - tp_mult * atr_val, 2),
        "params": params,
    }


# ============================================================
# 2. REGIME-AWARE STRATEGY
# ============================================================

def strategy_regime_aware(close: pd.Series, high: pd.Series,
                           low: pd.Series, volume: pd.Series,
                           regime: str = "UNKNOWN") -> dict:
    """Ne trade QUE dans le bon régime. Refuse de trader en CRISIS/TRANSITION.

    BULL → Trend Following adaptatif
    BEAR → Mean Reversion (acheter les dips)
    RANGE → Breakout Keltner
    CRISIS → NO TRADE (cash)
    TRANSITION → NO TRADE (attendre)
    """
    if regime in ("CRISIS", "TRANSITION", "UNKNOWN"):
        return {
            "strategy": "regime_aware",
            "direction": "NEUTRAL",
            "conviction": 0,
            "reason": f"Régime {regime} — pas de trade, rester en cash",
        }

    if len(close) < 100:
        return {"strategy": "regime_aware", "direction": "NEUTRAL", "conviction": 0}

    atr_val = float(atr(high, low, close, 14).iloc[-1])
    last = float(close.iloc[-1])

    if regime == "BULL":
        # Trend Following — acheter les pullbacks
        sma_50 = sma(close, 50).iloc[-1]
        rsi_val = rsi(close, 14).iloc[-1]

        if np.isnan(sma_50) or np.isnan(rsi_val):
            return {"strategy": "regime_aware", "direction": "NEUTRAL", "conviction": 0}

        if last > sma_50 and rsi_val < 40:
            # Pullback dans un bull market = opportunité
            return {
                "strategy": "regime_aware", "direction": "LONG", "conviction": 85,
                "entry": round(last, 2),
                "stop_loss": round(last - 2 * atr_val, 2),
                "take_profit": round(last + 4 * atr_val, 2),
                "reason": "Bull market pullback — RSI survendu mais tendance intacte",
            }
        elif last > sma_50 and rsi_val < 55:
            return {
                "strategy": "regime_aware", "direction": "LONG", "conviction": 60,
                "entry": round(last, 2),
                "stop_loss": round(last - 2 * atr_val, 2),
                "take_profit": round(last + 3 * atr_val, 2),
                "reason": "Bull market — tendance favorable",
            }

    elif regime == "BEAR":
        # Mean Reversion — acheter les excès baissiers
        bb = bollinger_bands(close, 20, 2.5)
        rsi_val = rsi(close, 14).iloc[-1]

        if np.isnan(bb["lower"].iloc[-1]) or np.isnan(rsi_val):
            return {"strategy": "regime_aware", "direction": "NEUTRAL", "conviction": 0}

        if last < bb["lower"].iloc[-1] and rsi_val < 25:
            return {
                "strategy": "regime_aware", "direction": "LONG", "conviction": 75,
                "entry": round(last, 2),
                "stop_loss": round(last - 1.5 * atr_val, 2),
                "take_profit": round(float(bb["middle"].iloc[-1]), 2),
                "reason": "Bear market oversold bounce — RSI extrême + sous Bollinger",
            }

    elif regime == "RANGE":
        # Breakout — attendre la cassure
        high_20 = high.iloc[-21:-1].max()
        low_20 = low.iloc[-21:-1].min()
        vol_avg = volume.iloc[-20:].mean()
        vol_now = volume.iloc[-1]

        if vol_now > vol_avg * 1.8:
            if last > high_20:
                return {
                    "strategy": "regime_aware", "direction": "LONG", "conviction": 80,
                    "entry": round(last, 2),
                    "stop_loss": round(last - 2 * atr_val, 2),
                    "take_profit": round(last + 3 * atr_val, 2),
                    "reason": "Breakout haussier avec volume fort — fin du range",
                }
            elif last < low_20:
                return {
                    "strategy": "regime_aware", "direction": "SHORT", "conviction": 80,
                    "entry": round(last, 2),
                    "stop_loss": round(last + 2 * atr_val, 2),
                    "take_profit": round(last - 3 * atr_val, 2),
                    "reason": "Breakout baissier avec volume — cassure du range",
                }

    return {"strategy": "regime_aware", "direction": "NEUTRAL", "conviction": 0}


# ============================================================
# 3. MULTI-SIGNAL CONFIRMATION
# ============================================================

def strategy_multi_signal(close: pd.Series, high: pd.Series,
                           low: pd.Series, volume: pd.Series) -> dict:
    """Exige 3+ indicateurs alignés avant d'entrer.

    6 indicateurs votent :
    1. EMA 9/21 crossover
    2. RSI zone
    3. MACD histogramme
    4. Prix vs SMA 50
    5. OBV tendance
    6. Stochastic zone

    Trade seulement si >= 4 indicateurs sont d'accord.
    """
    if len(close) < 60:
        return {"strategy": "multi_signal", "direction": "NEUTRAL", "conviction": 0}

    atr_val = float(atr(high, low, close, 14).iloc[-1])
    last = float(close.iloc[-1])

    bullish_votes = 0
    bearish_votes = 0
    signals = []

    # 1. EMA 9/21
    ema9 = ema(close, 9).iloc[-1]
    ema21 = ema(close, 21).iloc[-1]
    if not np.isnan(ema9) and not np.isnan(ema21):
        if ema9 > ema21:
            bullish_votes += 1
            signals.append("EMA ↑")
        else:
            bearish_votes += 1
            signals.append("EMA ↓")

    # 2. RSI
    rsi_val = rsi(close, 14).iloc[-1]
    if not np.isnan(rsi_val):
        if rsi_val > 55:
            bullish_votes += 1
            signals.append(f"RSI {rsi_val:.0f} ↑")
        elif rsi_val < 45:
            bearish_votes += 1
            signals.append(f"RSI {rsi_val:.0f} ↓")

    # 3. MACD
    macd_data = macd(close)
    macd_hist = macd_data["histogram"].iloc[-1]
    if not np.isnan(macd_hist):
        if macd_hist > 0:
            bullish_votes += 1
            signals.append("MACD ↑")
        else:
            bearish_votes += 1
            signals.append("MACD ↓")

    # 4. Prix vs SMA 50
    sma50 = sma(close, 50).iloc[-1]
    if not np.isnan(sma50):
        if last > sma50:
            bullish_votes += 1
            signals.append("SMA50 ↑")
        else:
            bearish_votes += 1
            signals.append("SMA50 ↓")

    # 5. OBV tendance (20 jours)
    obv_series = obv(close, volume)
    if len(obv_series) >= 20:
        obv_trend = obv_series.iloc[-1] > obv_series.iloc[-20]
        if obv_trend:
            bullish_votes += 1
            signals.append("OBV ↑")
        else:
            bearish_votes += 1
            signals.append("OBV ↓")

    # 6. Stochastic
    stoch = stochastic(high, low, close)
    stoch_k = stoch["k"].iloc[-1]
    if not np.isnan(stoch_k):
        if stoch_k > 50:
            bullish_votes += 1
            signals.append(f"Stoch {stoch_k:.0f} ↑")
        else:
            bearish_votes += 1
            signals.append(f"Stoch {stoch_k:.0f} ↓")

    direction = "NEUTRAL"
    conviction = 0

    # Minimum 4 votes sur 6 pour agir
    if bullish_votes >= 4:
        direction = "LONG"
        conviction = 50 + bullish_votes * 8  # 82-98
    elif bearish_votes >= 4:
        direction = "SHORT"
        conviction = 50 + bearish_votes * 8

    # Bonus : si 5+ votes, conviction max
    if bullish_votes >= 5 or bearish_votes >= 5:
        conviction = min(95, conviction + 10)

    return {
        "strategy": "multi_signal",
        "direction": direction,
        "conviction": round(conviction, 1),
        "entry": round(last, 2),
        "stop_loss": round(last - 2 * atr_val, 2) if direction == "LONG" else round(last + 2 * atr_val, 2),
        "take_profit": round(last + 3 * atr_val, 2) if direction == "LONG" else round(last - 3 * atr_val, 2),
        "bullish_votes": bullish_votes,
        "bearish_votes": bearish_votes,
        "signals": signals,
    }


# ============================================================
# 4. VOLATILITY BREAKOUT (KELTNER)
# ============================================================

def strategy_keltner_breakout(close: pd.Series, high: pd.Series,
                               low: pd.Series, volume: pd.Series) -> dict:
    """Breakout adaptatif basé sur les Keltner Channels.

    Plus robuste que le breakout de range fixe car les canaux
    s'adaptent à la volatilité via l'ATR.

    Signal : prix casse le canal Keltner + volume > 1.5x moyenne
    """
    if len(close) < 50:
        return {"strategy": "keltner_breakout", "direction": "NEUTRAL", "conviction": 0}

    period = 20
    atr_mult = 2.0
    middle = ema(close, period)
    atr_series = atr(high, low, close, period)
    upper = middle + atr_mult * atr_series
    lower = middle - atr_mult * atr_series

    last = float(close.iloc[-1])
    k_upper = float(upper.iloc[-1])
    k_lower = float(lower.iloc[-1])
    k_middle = float(middle.iloc[-1])
    atr_val = float(atr_series.iloc[-1])

    vol_avg = float(volume.iloc[-20:].mean())
    vol_now = float(volume.iloc[-1])

    if any(np.isnan(v) for v in [k_upper, k_lower, atr_val]) or vol_avg == 0:
        return {"strategy": "keltner_breakout", "direction": "NEUTRAL", "conviction": 0}

    vol_ratio = vol_now / vol_avg
    direction = "NEUTRAL"
    conviction = 0

    if last > k_upper:
        direction = "LONG"
        conviction = 60
        if vol_ratio > 1.5:
            conviction = 80
        if vol_ratio > 2.0:
            conviction = 90
    elif last < k_lower:
        direction = "SHORT"
        conviction = 60
        if vol_ratio > 1.5:
            conviction = 80
        if vol_ratio > 2.0:
            conviction = 90

    return {
        "strategy": "keltner_breakout",
        "direction": direction,
        "conviction": round(conviction, 1),
        "entry": round(last, 2),
        "stop_loss": round(k_middle, 2),
        "take_profit": round(last + 2 * (last - k_middle), 2) if direction == "LONG" else round(last - 2 * (k_middle - last), 2),
        "keltner_upper": round(k_upper, 2),
        "keltner_lower": round(k_lower, 2),
        "volume_ratio": round(vol_ratio, 2),
    }


# ============================================================
# 5. VWAP REVERSION
# ============================================================

def compute_vwap(close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
    """Volume Weighted Average Price sur N jours."""
    tp = close  # Simplified — ideally (high + low + close) / 3
    cumvol = volume.rolling(period).sum()
    cumtp = (tp * volume).rolling(period).sum()
    return cumtp / cumvol.replace(0, np.nan)


def strategy_vwap_reversion(close: pd.Series, high: pd.Series,
                              low: pd.Series, volume: pd.Series) -> dict:
    """Mean Reversion autour du VWAP.

    Plus précis que Bollinger car le VWAP pondère par le volume
    = il représente le "vrai" prix moyen du marché.

    Signal : prix dévie > 2% du VWAP + RSI extrême
    """
    if len(close) < 30:
        return {"strategy": "vwap_reversion", "direction": "NEUTRAL", "conviction": 0}

    vwap = compute_vwap(close, volume, 20)
    vwap_val = float(vwap.iloc[-1])
    last = float(close.iloc[-1])
    rsi_val = float(rsi(close, 14).iloc[-1])
    atr_val = float(atr(high, low, close, 14).iloc[-1])

    if any(np.isnan(v) for v in [vwap_val, rsi_val, atr_val]) or vwap_val == 0:
        return {"strategy": "vwap_reversion", "direction": "NEUTRAL", "conviction": 0}

    deviation = (last - vwap_val) / vwap_val * 100
    direction = "NEUTRAL"
    conviction = 0

    # Prix très en dessous du VWAP + RSI survendu
    if deviation < -3 and rsi_val < 30:
        direction = "LONG"
        conviction = 85
    elif deviation < -2 and rsi_val < 40:
        direction = "LONG"
        conviction = 65
    # Prix très au dessus du VWAP + RSI suracheté
    elif deviation > 3 and rsi_val > 70:
        direction = "SHORT"
        conviction = 85
    elif deviation > 2 and rsi_val > 60:
        direction = "SHORT"
        conviction = 65

    return {
        "strategy": "vwap_reversion",
        "direction": direction,
        "conviction": round(conviction, 1),
        "entry": round(last, 2),
        "stop_loss": round(last - 1.5 * atr_val, 2) if direction == "LONG" else round(last + 1.5 * atr_val, 2),
        "take_profit": round(vwap_val, 2),
        "vwap": round(vwap_val, 2),
        "deviation_pct": round(deviation, 2),
        "rsi": round(rsi_val, 1),
    }


# ============================================================
# 6. MOMENTUM ROTATION
# ============================================================

def compute_momentum_score(close: pd.Series, lookback: int = 63) -> float:
    """Score de momentum = rendement sur N jours ajusté par la volatilité."""
    if len(close) < lookback + 10:
        return 0

    ret = (close.iloc[-1] / close.iloc[-lookback] - 1) * 100
    vol = close.pct_change().iloc[-lookback:].std() * np.sqrt(252)

    if vol == 0:
        return 0

    return ret / vol  # Rendement / volatilité = momentum ajusté au risque


def strategy_momentum_rotation(close: pd.Series, high: pd.Series,
                                low: pd.Series, volume: pd.Series,
                                all_momentum_scores: dict | None = None,
                                symbol: str = "") -> dict:
    """Momentum Rotation — achète les top 20%, vend les bottom 20%.

    Basé sur le cross-sectional momentum : les actifs qui ont le plus
    monté les 3 derniers mois continuent à monter (momentum effect).

    Nécessite all_momentum_scores = {symbol: score} pour comparer.
    """
    if len(close) < 70:
        return {"strategy": "momentum_rotation", "direction": "NEUTRAL", "conviction": 0}

    atr_val = float(atr(high, low, close, 14).iloc[-1])
    last = float(close.iloc[-1])
    my_score = compute_momentum_score(close)

    if all_momentum_scores is None or len(all_momentum_scores) < 5:
        # Sans les autres actifs, utiliser le score absolu
        direction = "NEUTRAL"
        conviction = 0
        if my_score > 1.5:
            direction = "LONG"
            conviction = 70
        elif my_score > 1.0:
            direction = "LONG"
            conviction = 55
        elif my_score < -1.5:
            direction = "SHORT"
            conviction = 70
        elif my_score < -1.0:
            direction = "SHORT"
            conviction = 55

        return {
            "strategy": "momentum_rotation",
            "direction": direction,
            "conviction": round(conviction, 1),
            "entry": round(last, 2),
            "stop_loss": round(last - 2 * atr_val, 2) if direction == "LONG" else round(last + 2 * atr_val, 2),
            "take_profit": round(last + 3 * atr_val, 2) if direction == "LONG" else round(last - 3 * atr_val, 2),
            "momentum_score": round(my_score, 3),
        }

    # Avec les autres actifs : classement relatif
    all_scores = sorted(all_momentum_scores.values())
    n = len(all_scores)
    percentile_80 = all_scores[int(n * 0.8)] if n > 5 else 999
    percentile_20 = all_scores[int(n * 0.2)] if n > 5 else -999

    direction = "NEUTRAL"
    conviction = 0

    if my_score >= percentile_80:
        direction = "LONG"
        conviction = 80
    elif my_score <= percentile_20:
        direction = "SHORT"
        conviction = 75

    rank = sum(1 for s in all_scores if s <= my_score)
    percentile = rank / n * 100

    return {
        "strategy": "momentum_rotation",
        "direction": direction,
        "conviction": round(conviction, 1),
        "entry": round(last, 2),
        "stop_loss": round(last - 2 * atr_val, 2) if direction == "LONG" else round(last + 2 * atr_val, 2),
        "take_profit": round(last + 3 * atr_val, 2) if direction == "LONG" else round(last - 3 * atr_val, 2),
        "momentum_score": round(my_score, 3),
        "percentile": round(percentile, 1),
    }


# ============================================================
# 7. PAIRS STATISTICAL ARBITRAGE (amélioré)
# ============================================================

def strategy_pairs_arbitrage(close_a: pd.Series, close_b: pd.Series,
                              volume_a: pd.Series,
                              symbol_a: str = "", symbol_b: str = "") -> dict:
    """Pairs Trading amélioré avec test de cointégration simplifié.

    Au lieu de juste regarder le z-score du ratio, on vérifie :
    1. La corrélation est stable (> 0.6 sur 60j et 252j)
    2. Le spread est mean-reverting (half-life < 30 jours)
    3. Le z-score est extrême (> 2 ou < -2)
    """
    if len(close_a) < 252 or len(close_b) < 252:
        return {"strategy": "pairs_arbitrage", "direction": "NEUTRAL", "conviction": 0}

    # Aligner
    aligned = pd.DataFrame({"a": close_a, "b": close_b}).dropna()
    if len(aligned) < 252:
        return {"strategy": "pairs_arbitrage", "direction": "NEUTRAL", "conviction": 0}

    # Corrélation
    corr_short = aligned["a"].iloc[-60:].pct_change().corr(aligned["b"].iloc[-60:].pct_change())
    corr_long = aligned["a"].iloc[-252:].pct_change().corr(aligned["b"].iloc[-252:].pct_change())

    if corr_short < 0.5 or corr_long < 0.5:
        return {
            "strategy": "pairs_arbitrage", "direction": "NEUTRAL", "conviction": 0,
            "reason": f"Corrélation insuffisante (60j={corr_short:.2f}, 252j={corr_long:.2f})",
        }

    # Z-score du ratio
    ratio = aligned["a"] / aligned["b"]
    z_mean = ratio.rolling(60).mean()
    z_std = ratio.rolling(60).std()
    zscore = ((ratio - z_mean) / z_std.replace(0, np.nan)).iloc[-1]

    if np.isnan(zscore):
        return {"strategy": "pairs_arbitrage", "direction": "NEUTRAL", "conviction": 0}

    # Half-life (vitesse de retour à la moyenne)
    spread = ratio - z_mean
    spread_lag = spread.shift(1)
    valid = pd.DataFrame({"spread": spread, "lag": spread_lag}).dropna()
    if len(valid) > 30:
        beta = np.corrcoef(valid["spread"], valid["lag"])[0, 1]
        half_life = -np.log(2) / np.log(abs(beta)) if abs(beta) < 1 and beta != 0 else 999
    else:
        half_life = 999

    if half_life > 30:
        return {
            "strategy": "pairs_arbitrage", "direction": "NEUTRAL", "conviction": 0,
            "reason": f"Half-life trop long ({half_life:.0f}j) — pas assez mean-reverting",
        }

    direction = "NEUTRAL"
    conviction = 0
    last_a = float(close_a.iloc[-1])

    if zscore > 2.5:
        direction = "SHORT"  # A est surcoté vs B → vendre A
        conviction = 85
    elif zscore > 2.0:
        direction = "SHORT"
        conviction = 65
    elif zscore < -2.5:
        direction = "LONG"  # A est sous-coté vs B → acheter A
        conviction = 85
    elif zscore < -2.0:
        direction = "LONG"
        conviction = 65

    return {
        "strategy": "pairs_arbitrage",
        "direction": direction,
        "conviction": round(conviction, 1),
        "entry": round(last_a, 2),
        "zscore": round(float(zscore), 3),
        "half_life": round(half_life, 1),
        "correlation_60d": round(float(corr_short), 3),
        "correlation_252d": round(float(corr_long), 3),
        "pair": f"{symbol_a}/{symbol_b}",
    }


# ============================================================
# Export
# ============================================================

ALL_PRO_STRATEGIES = {
    "adaptive_trend": strategy_adaptive_trend,
    "multi_signal": strategy_multi_signal,
    "keltner_breakout": strategy_keltner_breakout,
    "vwap_reversion": strategy_vwap_reversion,
    "momentum_rotation": strategy_momentum_rotation,
}

# regime_aware et pairs_arbitrage nécessitent des paramètres spéciaux
# et sont appelés séparément
