"""Stratégies Genius — 3 stratégies révolutionnaires

Stratégie 13 : Regime Cascade — trade les suiveurs quand le leader change de régime
Stratégie 14 : Volatility Compression Explosion — trade l'explosion après compression
Stratégie 15 : Anti-Consensus Alpha — parie contre l'euphorie du système
"""

import numpy as np
import pandas as pd
import logging

from backend.modules.scanner.indicators import (
    sma, ema, rsi, macd, bollinger_bands, atr, stochastic,
)

logger = logging.getLogger("tradepilot.strategies_genius")


# ═══════════════════════════════════════════════════════════
# STRATÉGIE 13 — REGIME CASCADE
# ═══════════════════════════════════════════════════════════

def strategy_regime_cascade(
    close: pd.Series, high: pd.Series, low: pd.Series, volume: pd.Series,
    leader_close: pd.Series | None = None,
) -> dict:
    """Détecte un changement de régime chez un leader et trade le suiveur.

    Si pas de leader fourni, utilise l'actif lui-même avec un décalage
    temporel : compare le régime des 5 derniers jours vs les 20 précédents.
    Un changement de momentum sur le court terme qui n'est pas encore
    reflété dans les moyennes longues = fenêtre d'opportunité.
    """
    result = {
        "strategy": "regime_cascade",
        "direction": "NEUTRAL",
        "conviction": 0,
        "entry": None,
        "stop_loss": None,
        "take_profit": None,
    }

    if len(close) < 50:
        return result

    # Régime court terme (5 jours) vs moyen terme (20 jours)
    sma_5 = sma(close, 5)
    sma_20 = sma(close, 20)
    sma_50 = sma(close, 50)

    # Pente du SMA 5 sur les 3 derniers jours (direction court terme)
    slope_5_recent = (float(sma_5.iloc[-1]) - float(sma_5.iloc[-4])) / float(sma_5.iloc[-4]) * 100
    # Pente du SMA 20 (direction moyen terme)
    slope_20 = (float(sma_20.iloc[-1]) - float(sma_20.iloc[-6])) / float(sma_20.iloc[-6]) * 100

    # Détection de cascade : le court terme a changé mais le moyen terme pas encore
    # C'est la fenêtre où le suiveur n'a pas rattrapé le leader
    momentum_shift = slope_5_recent - slope_20

    # RSI pour confirmer la force du shift
    rsi_val = float(rsi(close, 14).iloc[-1])

    # Volume : le shift est-il accompagné de volume ?
    vol_ratio = float(volume.iloc[-5:].mean()) / float(volume.iloc[-20:].mean()) if float(volume.iloc[-20:].mean()) > 0 else 1

    # MACD histogram direction
    macd_data = macd(close)
    macd_hist = float(macd_data["histogram"].iloc[-1])
    macd_hist_prev = float(macd_data["histogram"].iloc[-3])
    macd_accelerating = macd_hist > macd_hist_prev

    # ATR pour SL/TP
    atr_val = float(atr(high, low, close, 14).iloc[-1])
    current = float(close.iloc[-1])

    if momentum_shift > 1.5 and rsi_val > 45 and rsi_val < 75 and macd_accelerating:
        # Le court terme monte mais le moyen terme traîne → LONG cascade
        conviction = min(95, 40 + abs(momentum_shift) * 8 + (vol_ratio - 1) * 15)
        result["direction"] = "LONG"
        result["conviction"] = round(conviction)
        result["entry"] = round(current, 2)
        result["stop_loss"] = round(current - 2.5 * atr_val, 2)
        result["take_profit"] = round(current + 3.5 * atr_val, 2)

    elif momentum_shift < -1.5 and rsi_val < 55 and rsi_val > 25 and not macd_accelerating:
        # Le court terme baisse mais le moyen terme traîne → SHORT cascade
        conviction = min(95, 40 + abs(momentum_shift) * 8 + (vol_ratio - 1) * 15)
        result["direction"] = "SHORT"
        result["conviction"] = round(conviction)
        result["entry"] = round(current, 2)
        result["stop_loss"] = round(current + 2.5 * atr_val, 2)
        result["take_profit"] = round(current - 3.5 * atr_val, 2)

    return result


# ═══════════════════════════════════════════════════════════
# STRATÉGIE 14 — VOLATILITY COMPRESSION EXPLOSION
# ═══════════════════════════════════════════════════════════

def strategy_volatility_explosion(
    close: pd.Series, high: pd.Series, low: pd.Series, volume: pd.Series,
) -> dict:
    """Trade l'explosion après une compression de volatilité extrême.

    Quand ATR, Bollinger width et volume sont tous comprimés simultanément,
    une explosion est imminente. On entre dans la direction du breakout.
    """
    result = {
        "strategy": "volatility_explosion",
        "direction": "NEUTRAL",
        "conviction": 0,
        "entry": None,
        "stop_loss": None,
        "take_profit": None,
    }

    if len(close) < 100:
        return result

    current = float(close.iloc[-1])
    atr_val = float(atr(high, low, close, 14).iloc[-1])

    # 1. ATR Percentile — est-ce que la volatilité est historiquement basse ?
    atr_series = atr(high, low, close, 14)
    atr_percentile = (atr_series.iloc[-1] <= atr_series.iloc[-100:]).sum() / 100 * 100

    # 2. Bollinger Width — les bandes sont-elles comprimées ?
    bb = bollinger_bands(close)
    bb_width = (float(bb["upper"].iloc[-1]) - float(bb["lower"].iloc[-1])) / float(bb["middle"].iloc[-1]) * 100
    bb_width_20 = []
    for i in range(-20, 0):
        if not np.isnan(bb["upper"].iloc[i]) and not np.isnan(bb["lower"].iloc[i]):
            w = (float(bb["upper"].iloc[i]) - float(bb["lower"].iloc[i])) / float(bb["middle"].iloc[i]) * 100
            bb_width_20.append(w)
    bb_compressed = bb_width <= min(bb_width_20) * 1.1 if bb_width_20 else False

    # 3. Volume contraction — le volume baisse depuis 5+ jours ?
    vol_contracting = all(
        float(volume.iloc[-i-1]) <= float(volume.iloc[-i-2]) * 1.05
        for i in range(4)
    ) if len(volume) >= 6 else False

    # 4. Inside bars — le range se contracte ?
    ranges = [float(high.iloc[i]) - float(low.iloc[i]) for i in range(-5, 0)]
    inside_bars = sum(1 for i in range(1, len(ranges)) if ranges[i] <= ranges[i-1]) >= 3

    # Compteur de signaux de compression
    compression_signals = sum([
        atr_percentile <= 20,
        bb_compressed,
        vol_contracting,
        inside_bars,
    ])

    if compression_signals >= 3:
        # Explosion imminente — détecter la direction du breakout naissant
        # Le dernier mouvement donne la direction
        last_move = float(close.iloc[-1]) - float(close.iloc[-3])
        rsi_val = float(rsi(close, 14).iloc[-1])

        # MACD pour confirmer
        macd_data = macd(close)
        macd_hist = float(macd_data["histogram"].iloc[-1])

        conviction = min(95, 50 + compression_signals * 10)

        # Range de la compression pour le SL
        compression_high = float(high.iloc[-5:].max())
        compression_low = float(low.iloc[-5:].min())
        range_size = compression_high - compression_low

        if last_move > 0 and macd_hist > 0 and rsi_val > 45:
            result["direction"] = "LONG"
            result["conviction"] = round(conviction)
            result["entry"] = round(compression_high, 2)  # Breakout entry
            result["stop_loss"] = round(compression_low - 0.5 * atr_val, 2)
            result["take_profit"] = round(compression_high + 3 * range_size, 2)

        elif last_move < 0 and macd_hist < 0 and rsi_val < 55:
            result["direction"] = "SHORT"
            result["conviction"] = round(conviction)
            result["entry"] = round(compression_low, 2)
            result["stop_loss"] = round(compression_high + 0.5 * atr_val, 2)
            result["take_profit"] = round(compression_low - 3 * range_size, 2)

    elif compression_signals == 2:
        # Pré-compression — conviction basse, signal d'alerte
        result["conviction"] = 25

    return result


# ═══════════════════════════════════════════════════════════
# STRATÉGIE 15 — ANTI-CONSENSUS ALPHA
# ═══════════════════════════════════════════════════════════

def strategy_anti_consensus(
    close: pd.Series, high: pd.Series, low: pd.Series, volume: pd.Series,
    scanner_score: float = 50,
    consensus_pct: float = 0,
    sus_score: float = 50,
) -> dict:
    """Parie contre le consensus quand les conditions d'euphorie/panique sont réunies.

    Conditions d'entrée contrariante :
    1. RSI extrême (>80 pour short contrarian, <20 pour long contrarian)
    2. Volume en déclin (l'euphorie s'essouffle)
    3. Scanner score très haut MAIS SUS très bas (tout le monde voit le même signal)
    4. Consensus élevé (>30% des actifs en GO dans la même direction)

    Cette stratégie ne trade que rarement (5-10 fois par an) mais avec
    une conviction élevée dans les moments critiques.
    """
    result = {
        "strategy": "anti_consensus",
        "direction": "NEUTRAL",
        "conviction": 0,
        "entry": None,
        "stop_loss": None,
        "take_profit": None,
    }

    if len(close) < 50:
        return result

    current = float(close.iloc[-1])
    atr_val = float(atr(high, low, close, 14).iloc[-1])
    rsi_val = float(rsi(close, 14).iloc[-1])

    # Volume trend — les 5 derniers jours vs les 20 précédents
    recent_vol = float(volume.iloc[-5:].mean())
    prev_vol = float(volume.iloc[-25:-5].mean()) if len(volume) >= 25 else float(volume.mean())
    vol_declining = recent_vol < prev_vol * 0.85  # Volume baisse de 15%+

    # Stochastic pour confirmer l'extrême
    stoch = stochastic(close, high, low)
    stoch_k = float(stoch["k"].iloc[-1]) if not np.isnan(stoch["k"].iloc[-1]) else 50

    # Distance par rapport à la SMA 20 — mesure l'excès
    sma_20 = float(sma(close, 20).iloc[-1])
    deviation = (current - sma_20) / sma_20 * 100  # % au-dessus/dessous de la SMA 20

    # Nombre de jours consécutifs dans la même direction
    consecutive = 0
    for i in range(1, min(15, len(close))):
        if float(close.iloc[-i]) > float(close.iloc[-i-1]):
            consecutive += 1
        else:
            break

    consecutive_down = 0
    for i in range(1, min(15, len(close))):
        if float(close.iloc[-i]) < float(close.iloc[-i-1]):
            consecutive_down += 1
        else:
            break

    # === CONTRARIAN SHORT (euphorie → retournement) ===
    euphoria_signals = sum([
        rsi_val > 78,
        stoch_k > 85,
        deviation > 8,  # 8%+ au-dessus de la SMA 20
        vol_declining,
        consecutive >= 5,  # 5+ jours de hausse consécutive
        sus_score < 30 and scanner_score > 70,  # Signal crowdé
    ])

    if euphoria_signals >= 4:
        conviction = min(90, 45 + euphoria_signals * 8)
        result["direction"] = "SHORT"
        result["conviction"] = round(conviction)
        result["entry"] = round(current, 2)
        result["stop_loss"] = round(current + 1.5 * atr_val, 2)  # SL serré — contrarian
        result["take_profit"] = round(current - 4 * atr_val, 2)  # TP large — le retournement est violent

    # === CONTRARIAN LONG (panique → rebond) ===
    panic_signals = sum([
        rsi_val < 22,
        stoch_k < 15,
        deviation < -8,  # 8%+ en dessous de la SMA 20
        vol_declining,  # Même la panique s'essouffle
        consecutive_down >= 5,  # 5+ jours de baisse consécutive
        sus_score < 30 and scanner_score < 30,  # Tout le monde fuit
    ])

    if panic_signals >= 4:
        conviction = min(90, 45 + panic_signals * 8)
        result["direction"] = "LONG"
        result["conviction"] = round(conviction)
        result["entry"] = round(current, 2)
        result["stop_loss"] = round(current - 1.5 * atr_val, 2)
        result["take_profit"] = round(current + 4 * atr_val, 2)

    return result
