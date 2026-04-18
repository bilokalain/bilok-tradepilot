"""Critère 11 — Narrative Momentum

Mesure la vitesse de propagation d'une narrative sur un actif.
Les marchés bougent sur les narratives, pas les fondamentaux à court terme.

5 composantes :
1. Volume Acceleration — le volume explose avant le prix (smart money)
2. Price Momentum Shift — changement de régime de momentum (de flat → directionnel)
3. Breakout Freshness — cassure récente d'un range (dans les 5 derniers jours)
4. Cross-Timeframe Alignment — daily, weekly, monthly pointent dans la même direction
5. Anomaly Score — comportement statistiquement inhabituel (Z-score)

Score 0-100 :
- > 80 : Narrative en explosion — le mouvement commence
- 60-80 : Narrative en construction — accumulation en cours
- 40-60 : Pas de narrative claire
- < 40 : Narrative épuisée ou contraire
"""

import numpy as np
import pandas as pd


def compute_narrative_score(close: pd.Series, high: pd.Series,
                             low: pd.Series, volume: pd.Series) -> dict:
    """Score Narrative Momentum composite (0-100)."""
    if len(close) < 60:
        return {"score": 50.0, "components": {}, "signal": "NEUTRAL"}

    components = {}

    # 1. Volume Acceleration (0-100)
    # Le volume des 5 derniers jours vs moyenne 20j vs moyenne 60j
    vol_5 = float(volume.iloc[-5:].mean())
    vol_20 = float(volume.iloc[-20:].mean())
    vol_60 = float(volume.iloc[-60:].mean())

    if vol_60 > 0 and vol_20 > 0:
        # Accélération = volume récent vs historique
        vol_ratio_short = vol_5 / vol_20
        vol_ratio_long = vol_20 / vol_60
        # Double accélération = volume accélère ET cette accélération accélère
        vol_accel = (vol_ratio_short - 1) * 50 + (vol_ratio_long - 1) * 30
        vol_score = max(0, min(100, 50 + vol_accel))
    else:
        vol_score = 50.0
    components["volume_acceleration"] = round(vol_score, 1)

    # 2. Price Momentum Shift (0-100)
    # Changement de régime : de flat → directionnel
    returns = close.pct_change().dropna()
    if len(returns) >= 20:
        # Momentum court terme vs long terme
        mom_5 = float(returns.iloc[-5:].mean()) * 252  # Annualisé
        mom_20 = float(returns.iloc[-20:].mean()) * 252
        mom_60 = float(returns.iloc[-60:].mean()) * 252 if len(returns) >= 60 else mom_20

        # Shift = momentum court accélère par rapport au long
        shift = (mom_5 - mom_60) * 10  # Amplifier
        mom_score = max(0, min(100, 50 + shift))

        # Bonus si le momentum court est dans la même direction que le moyen
        if (mom_5 > 0 and mom_20 > 0) or (mom_5 < 0 and mom_20 < 0):
            mom_score = min(100, mom_score + 10)
    else:
        mom_score = 50.0
    components["momentum_shift"] = round(mom_score, 1)

    # 3. Breakout Freshness (0-100)
    # Cassure récente d'un range (Donchian 20j)
    if len(close) >= 25:
        high_20 = float(high.iloc[-25:-5].max())
        low_20 = float(low.iloc[-25:-5].min())
        current = float(close.iloc[-1])
        recent_high = float(high.iloc[-5:].max())
        recent_low = float(low.iloc[-5:].min())

        range_size = high_20 - low_20
        if range_size > 0:
            # Breakout haussier
            if recent_high > high_20:
                breakout_strength = (recent_high - high_20) / range_size
                breakout_score = min(100, 60 + breakout_strength * 100)
            # Breakout baissier
            elif recent_low < low_20:
                breakout_strength = (low_20 - recent_low) / range_size
                breakout_score = min(100, 60 + breakout_strength * 100)
            else:
                # Pas de breakout — distance au bord du range
                dist_to_high = (high_20 - current) / range_size
                dist_to_low = (current - low_20) / range_size
                breakout_score = 50 - min(dist_to_high, dist_to_low) * 30
        else:
            breakout_score = 50.0
    else:
        breakout_score = 50.0
    components["breakout_freshness"] = round(max(0, min(100, breakout_score)), 1)

    # 4. Cross-Timeframe Alignment (0-100)
    # Daily, weekly (5j), monthly (21j) dans la même direction
    if len(close) >= 21:
        ret_1d = float(close.iloc[-1] / close.iloc[-2] - 1) if len(close) >= 2 else 0
        ret_5d = float(close.iloc[-1] / close.iloc[-5] - 1) if len(close) >= 5 else 0
        ret_21d = float(close.iloc[-1] / close.iloc[-21] - 1)

        # Compter l'alignement
        directions = [1 if r > 0 else -1 if r < 0 else 0 for r in [ret_1d, ret_5d, ret_21d]]
        alignment = abs(sum(directions)) / 3  # 1.0 = parfait alignement

        # Force de l'alignement
        avg_magnitude = (abs(ret_1d) + abs(ret_5d) + abs(ret_21d)) / 3
        align_score = 50 + alignment * 30 + avg_magnitude * 500
        align_score = max(0, min(100, align_score))
    else:
        align_score = 50.0
    components["cross_tf_alignment"] = round(align_score, 1)

    # 5. Anomaly Score (0-100)
    # Comportement statistiquement inhabituel = narrative en cours
    if len(returns) >= 60:
        # Z-score du rendement récent
        mean_60 = float(returns.iloc[-60:].mean())
        std_60 = float(returns.iloc[-60:].std())
        if std_60 > 0:
            z_return = abs(float(returns.iloc[-5:].mean()) - mean_60) / std_60
        else:
            z_return = 0

        # Z-score du volume
        vol_mean = float(volume.iloc[-60:].mean())
        vol_std = float(volume.iloc[-60:].std())
        if vol_std > 0:
            z_volume = abs(vol_5 - vol_mean) / vol_std
        else:
            z_volume = 0

        # Anomalie combinée
        anomaly = (z_return + z_volume) / 2
        anomaly_score = min(100, 40 + anomaly * 20)
    else:
        anomaly_score = 50.0
    components["anomaly"] = round(max(0, anomaly_score), 1)

    # Score final — pondération
    weights = {
        "volume_acceleration": 0.25,
        "momentum_shift": 0.25,
        "breakout_freshness": 0.20,
        "cross_tf_alignment": 0.15,
        "anomaly": 0.15,
    }

    final_score = sum(components[k] * weights[k] for k in weights)
    final_score = max(0, min(100, final_score))

    # Signal directionnel
    if len(close) >= 5:
        recent_return = float(close.iloc[-1] / close.iloc[-5] - 1)
        if final_score >= 65 and recent_return > 0:
            signal = "BULLISH_NARRATIVE"
        elif final_score >= 65 and recent_return < 0:
            signal = "BEARISH_NARRATIVE"
        elif final_score >= 50:
            signal = "BUILDING"
        else:
            signal = "EXHAUSTED"
    else:
        signal = "NEUTRAL"

    return {
        "score": round(final_score, 2),
        "components": components,
        "signal": signal,
    }
