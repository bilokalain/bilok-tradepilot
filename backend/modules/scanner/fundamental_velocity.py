"""Critère 6 — Vélocité Fondamentale (IVF)

Mesure l'accélération des fondamentaux via les données Yahoo Finance :
1. Accélération du prix (proxy CA) — momentum des rendements
2. Expansion des marges — proxy via la performance relative
3. Révisions analystes — proxy via la tendance des prix cibles
4. Surprise earnings répétée — proxy via les gaps post-earnings

Phase 1 : basé sur les données OHLCV + yfinance info quand disponible.
Phase 2 : données fondamentales réelles (API premium).
Score 0-100.
"""

import numpy as np
import pandas as pd


def compute_price_acceleration(close: pd.Series) -> float:
    """Accélération du momentum — dérivée seconde des rendements.

    Rendement qui accélère = fondamentaux qui s'améliorent.
    """
    if len(close) < 60:
        return 50.0

    # Rendement 20j glissant
    ret_20 = close.pct_change(20)
    if len(ret_20) < 40:
        return 50.0

    # Accélération = changement du rendement
    current_ret = ret_20.iloc[-1]
    prev_ret = ret_20.iloc[-20]

    if np.isnan(current_ret) or np.isnan(prev_ret):
        return 50.0

    acceleration = current_ret - prev_ret

    # Normaliser
    if acceleration > 0.10:
        return 90.0
    elif acceleration > 0.05:
        return 75.0
    elif acceleration > 0.02:
        return 62.0
    elif acceleration > -0.02:
        return 50.0
    elif acceleration > -0.05:
        return 38.0
    else:
        return 20.0


def compute_relative_strength(close: pd.Series, benchmark_close: pd.Series | None = None) -> float:
    """Force relative vs benchmark (proxy expansion des marges).

    Un actif qui surperforme son benchmark a probablement des marges en expansion.
    """
    if len(close) < 60:
        return 50.0

    # Rendement 60j de l'actif
    ret_60 = (close.iloc[-1] / close.iloc[-60] - 1) * 100

    if benchmark_close is not None and len(benchmark_close) >= 60:
        bench_ret = (benchmark_close.iloc[-1] / benchmark_close.iloc[-60] - 1) * 100
        relative = ret_60 - bench_ret
    else:
        # Sans benchmark, utiliser le rendement absolu
        relative = ret_60

    if relative > 15:
        return 90.0
    elif relative > 8:
        return 75.0
    elif relative > 3:
        return 62.0
    elif relative > -3:
        return 50.0
    elif relative > -8:
        return 38.0
    else:
        return 20.0


def detect_earnings_gaps(close: pd.Series, volume: pd.Series) -> dict:
    """Détecte les gaps post-earnings (proxy surprise).

    Un gap up avec fort volume = surprise positive.
    Gaps répétés dans la même direction = momentum fondamental.
    """
    if len(close) < 100:
        return {"gaps_up": 0, "gaps_down": 0, "score": 50}

    gaps_up = 0
    gaps_down = 0

    # Chercher les gaps avec volume anormal (> 2x moyenne)
    vol_avg = volume.rolling(20).mean()

    for i in range(1, min(len(close), 252)):
        if i >= len(vol_avg) or np.isnan(vol_avg.iloc[i]):
            continue

        gap_pct = (close.iloc[i] / close.iloc[i - 1] - 1) * 100
        vol_ratio = volume.iloc[i] / vol_avg.iloc[i] if vol_avg.iloc[i] > 0 else 1

        # Gap > 3% avec volume > 2x = probable earnings
        if abs(gap_pct) > 3 and vol_ratio > 2:
            if gap_pct > 0:
                gaps_up += 1
            else:
                gaps_down += 1

    net_gaps = gaps_up - gaps_down
    if net_gaps >= 3:
        score = 85
    elif net_gaps >= 1:
        score = 65
    elif net_gaps == 0:
        score = 50
    elif net_gaps >= -1:
        score = 35
    else:
        score = 15

    return {"gaps_up": gaps_up, "gaps_down": gaps_down, "score": score}


def compute_ivf_score(close: pd.Series, volume: pd.Series,
                       benchmark_close: pd.Series | None = None) -> dict:
    """Score Vélocité Fondamentale (IVF) composite.

    Combine : Accélération prix (35%) + Force relative (30%) + Gaps earnings (35%)
    """
    acceleration = compute_price_acceleration(close)
    relative = compute_relative_strength(close, benchmark_close)
    gaps = detect_earnings_gaps(close, volume)

    score = (
        acceleration * 0.35 +
        relative * 0.30 +
        gaps["score"] * 0.35
    )

    return {
        "score": round(min(100, max(0, score)), 2),
        "acceleration": round(acceleration, 1),
        "relative_strength": round(relative, 1),
        "earnings_gaps": gaps,
    }
