"""6 stratégies adaptatives sélectionnées selon le régime de marché

1. Trend Following — suit la tendance avec EMA crossover
2. Mean Reversion — retour à la moyenne (Bollinger + RSI survente/surachat)
3. Breakout — cassure de range avec confirmation volume
4. Momentum Adaptatif — force relative avec rotation
5. Microstructure — analyse du carnet d'ordres (placeholder Phase 2)
6. CNN Pattern Recognition — patterns graphiques (placeholder Phase 2)

Chaque stratégie produit :
- direction : LONG / SHORT / NEUTRAL
- conviction : 0-100
- entry / stop_loss / take_profit suggérés
"""

import numpy as np
import pandas as pd

from backend.modules.scanner.indicators import (
    sma, ema, rsi, macd, bollinger_bands, atr, stochastic, obv,
)


# Matrice régime → stratégies recommandées (poids)
REGIME_STRATEGY_MATRIX = {
    "BULL": {
        "adaptive_trend": 0.18, "multi_signal": 0.15, "momentum_rotation": 0.12,
        "trend_following": 0.10, "keltner_breakout": 0.10, "ichimoku": 0.08,
        "momentum": 0.06, "fibonacci": 0.06, "breakout": 0.05,
        "vwap_reversion": 0.03, "mean_reversion": 0.02, "mean_reversion_v2": 0.02,
        "microstructure": 0.02, "cnn_pattern": 0.01,
    },
    "BEAR": {
        "vwap_reversion": 0.18, "multi_signal": 0.15, "mean_reversion_v2": 0.12,
        "adaptive_trend": 0.10, "mean_reversion": 0.10, "fibonacci": 0.08,
        "momentum_rotation": 0.06, "ichimoku": 0.06, "keltner_breakout": 0.05,
        "trend_following": 0.04, "momentum": 0.02, "breakout": 0.02,
        "microstructure": 0.01, "cnn_pattern": 0.01,
    },
    "RANGE": {
        "vwap_reversion": 0.18, "keltner_breakout": 0.15, "multi_signal": 0.12,
        "mean_reversion_v2": 0.12, "mean_reversion": 0.08, "fibonacci": 0.08,
        "momentum_rotation": 0.06, "ichimoku": 0.06, "adaptive_trend": 0.05,
        "breakout": 0.04, "trend_following": 0.02, "momentum": 0.02,
        "microstructure": 0.01, "cnn_pattern": 0.01,
    },
    "CRISIS": {
        "multi_signal": 0.20, "vwap_reversion": 0.15, "mean_reversion_v2": 0.12,
        "adaptive_trend": 0.10, "fibonacci": 0.10, "momentum_rotation": 0.08,
        "ichimoku": 0.06, "mean_reversion": 0.06, "keltner_breakout": 0.05,
        "trend_following": 0.03, "momentum": 0.02, "breakout": 0.02,
        "microstructure": 0.005, "cnn_pattern": 0.005,
    },
    "TRANSITION": {
        "multi_signal": 0.18, "keltner_breakout": 0.15, "adaptive_trend": 0.12,
        "momentum_rotation": 0.10, "vwap_reversion": 0.08, "ichimoku": 0.08,
        "fibonacci": 0.06, "breakout": 0.06, "trend_following": 0.05,
        "mean_reversion_v2": 0.04, "momentum": 0.04, "mean_reversion": 0.02,
        "microstructure": 0.01, "cnn_pattern": 0.01,
    },
}


def strategy_trend_following(close: pd.Series, high: pd.Series,
                              low: pd.Series) -> dict:
    """Trend Following — EMA 9/21 crossover + confirmation SMA 50."""
    ema_9 = ema(close, 9)
    ema_21 = ema(close, 21)
    sma_50 = sma(close, 50)
    atr_val = atr(high, low, close, 14).iloc[-1]

    last = close.iloc[-1]
    e9 = ema_9.iloc[-1]
    e21 = ema_21.iloc[-1]
    s50 = sma_50.iloc[-1]
    e9_prev = ema_9.iloc[-2]
    e21_prev = ema_21.iloc[-2]

    if any(np.isnan(v) for v in [e9, e21, s50, atr_val]):
        return {"direction": "NEUTRAL", "conviction": 0, "strategy": "trend_following"}

    direction = "NEUTRAL"
    conviction = 0

    # Crossover haussier
    if e9 > e21 and e9_prev <= e21_prev and last > s50:
        direction = "LONG"
        conviction = 75
        # Plus le prix est au-dessus de SMA 50, plus la conviction monte
        margin = (last - s50) / s50
        conviction = min(95, conviction + margin * 200)
    # Crossover baissier
    elif e9 < e21 and e9_prev >= e21_prev and last < s50:
        direction = "SHORT"
        conviction = 75
        margin = (s50 - last) / s50
        conviction = min(95, conviction + margin * 200)
    # Tendance en cours
    elif e9 > e21 and last > s50:
        direction = "LONG"
        conviction = 55
    elif e9 < e21 and last < s50:
        direction = "SHORT"
        conviction = 55

    return {
        "strategy": "trend_following",
        "direction": direction,
        "conviction": round(conviction, 1),
        "entry": round(last, 2),
        "stop_loss": round(last - 2 * atr_val, 2) if direction == "LONG" else round(last + 2 * atr_val, 2),
        "take_profit": round(last + 3 * atr_val, 2) if direction == "LONG" else round(last - 3 * atr_val, 2),
    }


def strategy_mean_reversion(close: pd.Series, high: pd.Series,
                             low: pd.Series) -> dict:
    """Mean Reversion — Bollinger Bands + RSI pour détecter les excès."""
    bb = bollinger_bands(close, 20, 2.0)
    rsi_val = rsi(close, 14).iloc[-1]
    atr_val = atr(high, low, close, 14).iloc[-1]

    last = close.iloc[-1]
    upper = bb["upper"].iloc[-1]
    lower = bb["lower"].iloc[-1]
    middle = bb["middle"].iloc[-1]

    if any(np.isnan(v) for v in [upper, lower, middle, rsi_val, atr_val]):
        return {"direction": "NEUTRAL", "conviction": 0, "strategy": "mean_reversion"}

    direction = "NEUTRAL"
    conviction = 0

    # Survente : prix sous la bande basse + RSI < 30
    if last < lower and rsi_val < 30:
        direction = "LONG"
        conviction = 80
        overshoot = (lower - last) / (upper - lower) * 100
        conviction = min(95, conviction + overshoot * 0.5)
    elif last < lower:
        direction = "LONG"
        conviction = 55
    # Surachat : prix au-dessus de la bande haute + RSI > 70
    elif last > upper and rsi_val > 70:
        direction = "SHORT"
        conviction = 80
        overshoot = (last - upper) / (upper - lower) * 100
        conviction = min(95, conviction + overshoot * 0.5)
    elif last > upper:
        direction = "SHORT"
        conviction = 55

    target = middle  # retour à la moyenne

    return {
        "strategy": "mean_reversion",
        "direction": direction,
        "conviction": round(conviction, 1),
        "entry": round(last, 2),
        "stop_loss": round(last - 1.5 * atr_val, 2) if direction == "LONG" else round(last + 1.5 * atr_val, 2),
        "take_profit": round(target, 2),
    }


def strategy_breakout(close: pd.Series, high: pd.Series,
                       low: pd.Series, volume: pd.Series) -> dict:
    """Breakout — cassure du range 20 jours avec confirmation volume."""
    if len(close) < 21:
        return {"direction": "NEUTRAL", "conviction": 0, "strategy": "breakout"}

    high_20 = high.iloc[-21:-1].max()
    low_20 = low.iloc[-21:-1].min()
    vol_avg = volume.iloc[-20:].mean()
    atr_val = atr(high, low, close, 14).iloc[-1]

    last = close.iloc[-1]
    current_vol = volume.iloc[-1]

    if any(np.isnan(v) for v in [high_20, low_20, vol_avg, atr_val]) or vol_avg == 0:
        return {"direction": "NEUTRAL", "conviction": 0, "strategy": "breakout"}

    direction = "NEUTRAL"
    conviction = 0
    vol_ratio = current_vol / vol_avg

    # Cassure haussière
    if last > high_20:
        direction = "LONG"
        conviction = 60
        if vol_ratio > 1.5:
            conviction = min(95, conviction + (vol_ratio - 1) * 20)
    # Cassure baissière
    elif last < low_20:
        direction = "SHORT"
        conviction = 60
        if vol_ratio > 1.5:
            conviction = min(95, conviction + (vol_ratio - 1) * 20)

    return {
        "strategy": "breakout",
        "direction": direction,
        "conviction": round(conviction, 1),
        "entry": round(last, 2),
        "stop_loss": round(last - 2 * atr_val, 2) if direction == "LONG" else round(last + 2 * atr_val, 2),
        "take_profit": round(last + 3 * atr_val, 2) if direction == "LONG" else round(last - 3 * atr_val, 2),
        "volume_ratio": round(vol_ratio, 2),
    }


def strategy_momentum(close: pd.Series, high: pd.Series,
                       low: pd.Series) -> dict:
    """Momentum Adaptatif — force relative + Stochastique + MACD."""
    rsi_val = rsi(close, 14).iloc[-1]
    stoch = stochastic(high, low, close)
    macd_data = macd(close)
    atr_val = atr(high, low, close, 14).iloc[-1]

    stoch_k = stoch["k"].iloc[-1]
    stoch_d = stoch["d"].iloc[-1]
    macd_hist = macd_data["histogram"].iloc[-1]
    last = close.iloc[-1]

    if any(np.isnan(v) for v in [rsi_val, stoch_k, macd_hist, atr_val]):
        return {"direction": "NEUTRAL", "conviction": 0, "strategy": "momentum"}

    # Compter les signaux haussiers / baissiers
    bullish = 0
    bearish = 0

    if rsi_val > 55:
        bullish += 1
    elif rsi_val < 45:
        bearish += 1

    if stoch_k > stoch_d and stoch_k > 20:
        bullish += 1
    elif stoch_k < stoch_d and stoch_k < 80:
        bearish += 1

    if macd_hist > 0:
        bullish += 1
    else:
        bearish += 1

    # Performance récente (20 jours)
    if len(close) >= 20:
        perf_20d = (close.iloc[-1] / close.iloc[-20] - 1) * 100
        if perf_20d > 5:
            bullish += 1
        elif perf_20d < -5:
            bearish += 1

    direction = "NEUTRAL"
    conviction = 0

    if bullish >= 3:
        direction = "LONG"
        conviction = 50 + bullish * 10
    elif bearish >= 3:
        direction = "SHORT"
        conviction = 50 + bearish * 10

    return {
        "strategy": "momentum",
        "direction": direction,
        "conviction": round(min(95, conviction), 1),
        "entry": round(last, 2),
        "stop_loss": round(last - 2 * atr_val, 2) if direction == "LONG" else round(last + 2 * atr_val, 2),
        "take_profit": round(last + 3 * atr_val, 2) if direction == "LONG" else round(last - 3 * atr_val, 2),
    }


def strategy_microstructure(close: pd.Series, volume: pd.Series) -> dict:
    """Microstructure carnet d'ordres — placeholder Phase 2.

    Nécessite des données Level 2 / orderbook non disponibles via Yahoo Finance.
    """
    return {
        "strategy": "microstructure",
        "direction": "NEUTRAL",
        "conviction": 0,
        "status": "Phase 2 — nécessite données Level 2",
    }


def strategy_cnn_pattern(close: pd.Series) -> dict:
    """CNN Pattern Recognition — placeholder Phase 2.

    Nécessite le modèle ResNet18 fine-tuné sur des graphiques de prix.
    """
    return {
        "strategy": "cnn_pattern",
        "direction": "NEUTRAL",
        "conviction": 0,
        "status": "Phase 2 — nécessite modèle CNN entraîné",
    }


from backend.modules.analyser.strategies_advanced import (
    strategy_mean_reversion_v2, strategy_fibonacci, strategy_ichimoku,
)
from backend.modules.analyser.strategies_pro import (
    strategy_adaptive_trend, strategy_multi_signal,
    strategy_keltner_breakout, strategy_vwap_reversion,
    strategy_momentum_rotation,
)

ALL_STRATEGIES = {
    # Basiques
    "trend_following": strategy_trend_following,
    "mean_reversion": strategy_mean_reversion,
    "breakout": strategy_breakout,
    "momentum": strategy_momentum,
    # Avancées
    "mean_reversion_v2": strategy_mean_reversion_v2,
    "fibonacci": strategy_fibonacci,
    "ichimoku": strategy_ichimoku,
    # Pro
    "adaptive_trend": strategy_adaptive_trend,
    "multi_signal": strategy_multi_signal,
    "keltner_breakout": strategy_keltner_breakout,
    "vwap_reversion": strategy_vwap_reversion,
    "momentum_rotation": strategy_momentum_rotation,
    # Placeholders
    "microstructure": strategy_microstructure,
    "cnn_pattern": strategy_cnn_pattern,
}


def run_all_strategies(close: pd.Series, high: pd.Series,
                       low: pd.Series, volume: pd.Series,
                       regime: str) -> list[dict]:
    """Exécute toutes les stratégies et pondère selon le régime.

    Retourne la liste des signaux triés par score pondéré.
    """
    weights = REGIME_STRATEGY_MATRIX.get(regime, REGIME_STRATEGY_MATRIX["RANGE"])
    results = []

    for name, func in ALL_STRATEGIES.items():
        # Appeler chaque stratégie avec les bons arguments
        if name == "microstructure":
            signal = func(close, volume)
        elif name == "cnn_pattern":
            signal = func(close)
        elif name in ("breakout", "mean_reversion_v2", "adaptive_trend",
                       "multi_signal", "keltner_breakout", "vwap_reversion",
                       "momentum_rotation"):
            signal = func(close, high, low, volume)
        else:
            signal = func(close, high, low)

        weight = weights.get(name, 0)
        weighted_score = signal.get("conviction", 0) * weight

        signal["weight"] = round(weight, 3)
        signal["weighted_score"] = round(weighted_score, 1)
        results.append(signal)

    # Trier par score pondéré
    results.sort(key=lambda x: x["weighted_score"], reverse=True)
    return results


def select_best_strategy(close: pd.Series, high: pd.Series,
                          low: pd.Series, volume: pd.Series,
                          regime: str) -> dict:
    """Sélectionne la meilleure stratégie pour le régime actuel."""
    all_results = run_all_strategies(close, high, low, volume, regime)

    # Filtrer les stratégies avec une direction
    active = [r for r in all_results if r["direction"] != "NEUTRAL" and r["conviction"] > 0]

    if not active:
        return {
            "best_strategy": None,
            "direction": "NEUTRAL",
            "conviction": 0,
            "all_strategies": all_results,
        }

    best = active[0]
    return {
        "best_strategy": best["strategy"],
        "direction": best["direction"],
        "conviction": best["conviction"],
        "entry": best.get("entry"),
        "stop_loss": best.get("stop_loss"),
        "take_profit": best.get("take_profit"),
        "all_strategies": all_results,
    }
