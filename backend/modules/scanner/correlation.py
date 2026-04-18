"""Critère 1 — Corrélation multi-temporelle

Matrice de corrélation sur 5 horizons : jour, semaine, mois, trimestre, année.
Détecte les décrochages sectoriels et ruptures de corrélation.
"""

import numpy as np
import pandas as pd


HORIZONS = {
    "1d": 1,
    "1w": 5,
    "1m": 21,
    "3m": 63,
    "1y": 252,
}


def compute_returns(closes: pd.Series, horizon: int) -> pd.Series:
    """Calcule les rendements sur un horizon donné."""
    return closes.pct_change(periods=horizon).dropna()


def compute_correlation_matrix(closes_dict: dict[str, pd.Series], horizon: int) -> pd.DataFrame:
    """Matrice de corrélation entre actifs pour un horizon donné.

    Args:
        closes_dict: {symbol: pd.Series de close prices}
        horizon: nombre de jours pour le calcul des rendements
    """
    returns = {}
    for symbol, closes in closes_dict.items():
        ret = compute_returns(closes, horizon)
        if len(ret) > 0:
            returns[symbol] = ret

    if len(returns) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(returns)
    return df.corr()


def detect_correlation_break(closes_dict: dict[str, pd.Series],
                              symbol: str,
                              lookback_short: int = 21,
                              lookback_long: int = 252) -> dict:
    """Détecte les ruptures de corrélation pour un actif.

    Compare la corrélation récente (21j) vs historique (252j).
    Une rupture = divergence soudaine par rapport au comportement habituel.
    """
    if symbol not in closes_dict or len(closes_dict) < 2:
        return {"score": 50.0, "breaks": []}

    target = closes_dict[symbol]
    breaks = []

    for other_symbol, other_closes in closes_dict.items():
        if other_symbol == symbol:
            continue

        # Aligner les séries
        aligned = pd.DataFrame({"target": target, "other": other_closes}).dropna()
        if len(aligned) < lookback_long:
            continue

        ret_target = aligned["target"].pct_change().dropna()
        ret_other = aligned["other"].pct_change().dropna()

        # Corrélation historique (long terme)
        corr_long = ret_target.iloc[-lookback_long:].corr(ret_other.iloc[-lookback_long:])
        # Corrélation récente (court terme)
        corr_short = ret_target.iloc[-lookback_short:].corr(ret_other.iloc[-lookback_short:])

        if np.isnan(corr_long) or np.isnan(corr_short):
            continue

        delta = abs(corr_short - corr_long)
        if delta > 0.3:  # Rupture significative
            breaks.append({
                "symbol": other_symbol,
                "corr_long": round(corr_long, 3),
                "corr_short": round(corr_short, 3),
                "delta": round(delta, 3),
            })

    # Score : plus de ruptures = signal plus intéressant
    if not breaks:
        score = 50.0
    else:
        avg_delta = np.mean([b["delta"] for b in breaks])
        score = min(100, 50 + avg_delta * 100)

    return {"score": round(score, 2), "breaks": breaks}


def compute_correlation_score(closes_dict: dict[str, pd.Series], symbol: str) -> float:
    """Score de corrélation composite (0-100) pour un actif.

    Utilise le cache disque si disponible (instantané).
    Sinon fallback sur le calcul direct.
    """
    # Essayer le cache d'abord
    try:
        from backend.modules.scanner.correlation_cache import get_correlation_cache
        cache = get_correlation_cache()
        if cache and symbol in cache.get("corr_60", {}):
            row = cache["corr_60"][symbol]
            row_long = cache.get("corr_252", {}).get(symbol, {})
            breaks = []
            for other, corr_short in row.items():
                if other == symbol:
                    continue
                corr_long = row_long.get(other, corr_short)
                delta = abs(corr_short - corr_long)
                if delta > 0.3:
                    breaks.append(delta)
            if not breaks:
                return 50.0
            avg_delta = np.mean(breaks)
            return round(min(100, 50 + avg_delta * 100), 2)
    except Exception:
        pass

    # Fallback : calcul direct
    result = detect_correlation_break(closes_dict, symbol)
    return result["score"]
