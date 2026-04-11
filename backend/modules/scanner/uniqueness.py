"""Critère 9 — Unicité du Signal (SUS)

Mesure si le signal est unique ou si tout le monde voit la même chose :
1. Crowding Score — combien d'actifs ont le même signal ?
2. Novelty Score — le signal est-il inhabituel historiquement ?
3. Timeframe Neglect — le signal est-il visible sur les TF populaires ?
4. Complexity Premium — le signal nécessite-t-il une analyse complexe ?

Score 0-100 : signal unique et non-crowdé = haute valeur.
Un signal que tout le monde voit est déjà dans le prix.
"""

import numpy as np
import pandas as pd

from backend.modules.scanner.indicators import rsi, macd, sma


def compute_crowding_score(all_scores: dict[str, float], current_symbol: str) -> float:
    """Crowding — combien d'autres actifs ont un score similaire ?

    Si beaucoup d'actifs ont le même signal, c'est crowdé (mauvais).
    """
    if not all_scores or current_symbol not in all_scores:
        return 50.0

    current = all_scores[current_symbol]
    similar = 0
    total = len(all_scores) - 1

    if total <= 0:
        return 50.0

    for sym, score in all_scores.items():
        if sym == current_symbol:
            continue
        if abs(score - current) < 10:  # Score à ±10 points
            similar += 1

    crowding_pct = similar / total

    # Moins c'est crowdé, mieux c'est
    if crowding_pct > 0.6:
        return 15.0  # Très crowdé
    elif crowding_pct > 0.4:
        return 30.0
    elif crowding_pct > 0.2:
        return 55.0
    elif crowding_pct > 0.1:
        return 75.0
    else:
        return 90.0  # Signal très unique


def compute_novelty_score(close: pd.Series) -> float:
    """Novelty — le comportement actuel est-il inhabituel ?

    Compare la distribution récente des rendements à l'historique.
    Un comportement inédit a plus de valeur informationnelle.
    """
    if len(close) < 252:
        return 50.0

    # Rendements récents (20j) vs historiques (252j)
    recent_returns = close.pct_change().iloc[-20:].dropna()
    hist_returns = close.pct_change().iloc[-252:-20].dropna()

    if recent_returns.empty or hist_returns.empty:
        return 50.0

    # Z-score du rendement moyen récent
    hist_mean = hist_returns.mean()
    hist_std = hist_returns.std()

    if hist_std == 0:
        return 50.0

    z_score = abs((recent_returns.mean() - hist_mean) / hist_std)

    # Z-score élevé = comportement inhabituel = haute novelty
    if z_score > 3.0:
        return 92.0
    elif z_score > 2.0:
        return 78.0
    elif z_score > 1.5:
        return 65.0
    elif z_score > 1.0:
        return 52.0
    else:
        return 35.0  # Comportement normal, rien de nouveau


def compute_timeframe_neglect(close: pd.Series) -> float:
    """Timeframe Neglect — le signal est-il visible uniquement sur des TF non-populaires ?

    La plupart des traders regardent daily et 1H.
    Un signal visible uniquement sur weekly ou 5min est négligé = avantage.
    """
    if len(close) < 100:
        return 50.0

    # Comparer les signaux daily vs weekly (agrégé)
    daily_rsi = rsi(close, 14).iloc[-1]
    daily_macd = macd(close)["histogram"].iloc[-1]

    # Simuler weekly en prenant chaque 5ème barre
    weekly_close = close.iloc[::5]
    if len(weekly_close) < 30:
        return 50.0

    weekly_rsi = rsi(weekly_close, 14).iloc[-1]
    weekly_macd = macd(weekly_close)["histogram"].iloc[-1]

    if any(np.isnan(v) for v in [daily_rsi, daily_macd, weekly_rsi, weekly_macd]):
        return 50.0

    # Divergence entre timeframes = signal négligé
    rsi_divergence = abs(daily_rsi - weekly_rsi)
    macd_sign_diff = (daily_macd > 0) != (weekly_macd > 0)

    score = 50.0
    if rsi_divergence > 20:
        score += 20  # RSI dit des choses différentes selon le TF
    if macd_sign_diff:
        score += 15  # MACD inversé entre TF

    # Si le weekly montre quelque chose que le daily ne montre pas encore
    if weekly_rsi > 60 and daily_rsi < 50:
        score += 15  # Weekly bullish mais daily pas encore → opportunité

    return min(100, score)


def compute_complexity_premium(close: pd.Series, high: pd.Series,
                                low: pd.Series) -> float:
    """Complexity Premium — le signal nécessite-t-il une analyse avancée ?

    Signaux simples (SMA crossover) = tout le monde les voit.
    Signaux complexes (fractals, divergences multi-indicateurs) = avantage.
    """
    if len(close) < 50:
        return 50.0

    complexity_points = 0

    # 1. Divergence RSI/Prix (complexe)
    rsi_series = rsi(close, 14)
    if len(rsi_series) >= 20:
        price_trend = close.iloc[-1] > close.iloc[-20]
        rsi_trend = rsi_series.iloc[-1] > rsi_series.iloc[-20]
        if price_trend != rsi_trend:
            complexity_points += 2  # Divergence = analyse complexe

    # 2. SMA crossover (simple, tout le monde le voit)
    sma_20 = sma(close, 20).iloc[-1]
    sma_50 = sma(close, 50).iloc[-1]
    if not np.isnan(sma_20) and not np.isnan(sma_50):
        if abs(sma_20 - sma_50) / sma_50 < 0.01:
            complexity_points -= 1  # Trop évident

    # 3. Multiple timeframes alignés mais avec nuance
    macd_data = macd(close)
    macd_hist = macd_data["histogram"].iloc[-1]
    macd_signal_val = macd_data["signal"].iloc[-1]
    if not np.isnan(macd_hist) and not np.isnan(macd_signal_val):
        if abs(macd_hist) < abs(macd_signal_val) * 0.3:
            complexity_points += 1  # Signal subtil dans le MACD

    # Normaliser
    if complexity_points >= 3:
        return 85.0
    elif complexity_points >= 2:
        return 72.0
    elif complexity_points >= 1:
        return 58.0
    elif complexity_points == 0:
        return 45.0
    else:
        return 30.0  # Signal trop simple, tout le monde l'a vu


def compute_sus_score(close: pd.Series, high: pd.Series, low: pd.Series,
                       all_technical_scores: dict[str, float],
                       symbol: str) -> dict:
    """Score Unicité du Signal (SUS) composite.

    Combine : Crowding (30%) + Novelty (25%) + TF Neglect (20%) + Complexity (25%)
    """
    crowding = compute_crowding_score(all_technical_scores, symbol)
    novelty = compute_novelty_score(close)
    neglect = compute_timeframe_neglect(close)
    complexity = compute_complexity_premium(close, high, low)

    score = (
        crowding * 0.30 +
        novelty * 0.25 +
        neglect * 0.20 +
        complexity * 0.25
    )

    return {
        "score": round(min(100, max(0, score)), 2),
        "crowding": round(crowding, 1),
        "novelty": round(novelty, 1),
        "timeframe_neglect": round(neglect, 1),
        "complexity_premium": round(complexity, 1),
    }
