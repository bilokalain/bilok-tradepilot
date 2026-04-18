"""Indicateurs techniques — 20 indicateurs, 7 familles

Tendance : SMA, EMA, ADX, Parabolic SAR, Donchian Channels
Momentum : RSI, MACD, Stochastique, Williams %R, CCI, ROC
Volatilité : Bollinger Bands, ATR
Volume : OBV, Volume SMA, Chaikin Money Flow, VWAP
Structure : Pivot Points
Divergences : Détection automatique RSI/MACD vs prix
"""

import numpy as np
import pandas as pd


# ============================================================
# TENDANCE
# ============================================================

def sma(closes: pd.Series, period: int = 20) -> pd.Series:
    """Simple Moving Average."""
    return closes.rolling(window=period).mean()


def ema(closes: pd.Series, period: int = 20) -> pd.Series:
    """Exponential Moving Average."""
    return closes.ewm(span=period, adjust=False).mean()


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average Directional Index — mesure la FORCE de la tendance.

    ADX > 25 = tendance forte (dans n'importe quelle direction)
    ADX < 20 = pas de tendance (range)
    ADX > 40 = tendance très forte
    """
    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

    atr_series = atr(high, low, close, period)
    atr_safe = atr_series.replace(0, np.nan)

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr_safe)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr_safe)

    di_sum = plus_di + minus_di
    di_sum = di_sum.replace(0, np.nan)
    dx = 100 * abs(plus_di - minus_di) / di_sum

    return dx.rolling(period).mean()


def parabolic_sar(high: pd.Series, low: pd.Series, af_start: float = 0.02,
                   af_step: float = 0.02, af_max: float = 0.20) -> pd.Series:
    """Parabolic SAR — points de retournement + trailing stop.

    Quand le prix croise le SAR, la tendance s'inverse.
    """
    n = len(high)
    sar = pd.Series(index=high.index, dtype=float)
    trend = 1  # 1 = up, -1 = down
    ep = float(low.iloc[0])  # Extreme point
    af = af_start
    sar_val = float(high.iloc[0])

    for i in range(1, n):
        prev_sar = sar_val
        sar_val = prev_sar + af * (ep - prev_sar)

        if trend == 1:
            if float(low.iloc[i]) < sar_val:
                trend = -1
                sar_val = ep
                ep = float(low.iloc[i])
                af = af_start
            else:
                if float(high.iloc[i]) > ep:
                    ep = float(high.iloc[i])
                    af = min(af + af_step, af_max)
        else:
            if float(high.iloc[i]) > sar_val:
                trend = 1
                sar_val = ep
                ep = float(high.iloc[i])
                af = af_start
            else:
                if float(low.iloc[i]) < ep:
                    ep = float(low.iloc[i])
                    af = min(af + af_step, af_max)

        sar.iloc[i] = sar_val

    return sar


def donchian_channels(high: pd.Series, low: pd.Series, period: int = 20) -> dict:
    """Donchian Channels — Turtle Trading.

    Upper = plus haut des N derniers jours
    Lower = plus bas des N derniers jours
    Middle = (Upper + Lower) / 2
    """
    upper = high.rolling(period).max()
    lower = low.rolling(period).min()
    middle = (upper + lower) / 2
    return {"upper": upper, "lower": lower, "middle": middle}


# ============================================================
# MOMENTUM
# ============================================================

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


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
               k_period: int = 14, d_period: int = 3) -> dict:
    """Oscillateur Stochastique (%K et %D)."""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    d = k.rolling(window=d_period).mean()
    return {"k": k, "d": d}


def williams_r(high: pd.Series, low: pd.Series, close: pd.Series,
               period: int = 14) -> pd.Series:
    """Williams %R — plus réactif que RSI, détecte les retournements tôt.

    -100 à 0 : < -80 = survendu (opportunité achat), > -20 = suracheté
    """
    highest = high.rolling(period).max()
    lowest = low.rolling(period).min()
    return -100 * (highest - close) / (highest - lowest).replace(0, np.nan)


def cci(high: pd.Series, low: pd.Series, close: pd.Series,
        period: int = 20) -> pd.Series:
    """Commodity Channel Index — identifie les cycles dans les prix.

    > +100 = surachat, < -100 = survente
    Bon pour les commodities et les actifs cycliques.
    """
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    return (tp - sma_tp) / (0.015 * mad).replace(0, np.nan)


def roc(close: pd.Series, period: int = 12) -> pd.Series:
    """Rate of Change — vitesse du mouvement en %.

    Positif = prix accélère à la hausse
    Négatif = prix accélère à la baisse
    """
    return ((close / close.shift(period)) - 1) * 100


# ============================================================
# VOLATILITÉ
# ============================================================

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


# ============================================================
# VOLUME
# ============================================================

def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume — confirmation par le volume."""
    direction = np.sign(close.diff())
    direction.iloc[0] = 0
    return (volume * direction).cumsum()


def volume_sma(volume: pd.Series, period: int = 20) -> pd.Series:
    """Moyenne mobile du volume."""
    return volume.rolling(window=period).mean()


def chaikin_money_flow(high: pd.Series, low: pd.Series, close: pd.Series,
                        volume: pd.Series, period: int = 20) -> pd.Series:
    """Chaikin Money Flow — pression acheteuse vs vendeuse.

    > 0 = pression acheteuse dominante
    < 0 = pression vendeuse dominante
    Plus c'est loin de 0, plus la pression est forte.
    """
    hl_range = high - low
    hl_range = hl_range.replace(0, np.nan)
    mfm = ((close - low) - (high - close)) / hl_range
    mfv = mfm * volume
    return mfv.rolling(period).sum() / volume.rolling(period).sum().replace(0, np.nan)


def vwap(high: pd.Series, low: pd.Series, close: pd.Series,
         volume: pd.Series, period: int = 20) -> pd.Series:
    """Volume Weighted Average Price — le "vrai" prix du marché.

    Prix moyen pondéré par le volume. Les institutionnels l'utilisent
    comme benchmark d'exécution.
    """
    tp = (high + low + close) / 3
    cumvol = volume.rolling(period).sum()
    cumtp = (tp * volume).rolling(period).sum()
    return cumtp / cumvol.replace(0, np.nan)


# ============================================================
# STRUCTURE DE PRIX
# ============================================================

def pivot_points(high: pd.Series, low: pd.Series, close: pd.Series) -> dict:
    """Pivot Points — niveaux de support/résistance institutionnels.

    Calculés sur la dernière barre complète.
    PP = (High + Low + Close) / 3
    R1/S1, R2/S2, R3/S3
    """
    h = float(high.iloc[-2]) if len(high) >= 2 else float(high.iloc[-1])
    l = float(low.iloc[-2]) if len(low) >= 2 else float(low.iloc[-1])
    c = float(close.iloc[-2]) if len(close) >= 2 else float(close.iloc[-1])

    pp = (h + l + c) / 3
    r1 = 2 * pp - l
    s1 = 2 * pp - h
    r2 = pp + (h - l)
    s2 = pp - (h - l)
    r3 = h + 2 * (pp - l)
    s3 = l - 2 * (h - pp)

    return {
        "pp": round(pp, 2), "r1": round(r1, 2), "r2": round(r2, 2), "r3": round(r3, 2),
        "s1": round(s1, 2), "s2": round(s2, 2), "s3": round(s3, 2),
    }


# ============================================================
# DIVERGENCES AUTOMATIQUES
# ============================================================

def detect_divergences(close: pd.Series, lookback: int = 20) -> dict:
    """Détecte les divergences RSI et MACD vs prix.

    Divergence haussière : prix fait un plus bas, RSI fait un plus haut → rebond probable
    Divergence baissière : prix fait un plus haut, RSI fait un plus bas → retournement probable
    """
    if len(close) < lookback + 14:
        return {"rsi_divergence": "none", "macd_divergence": "none", "score": 0}

    rsi_series = rsi(close, 14)
    macd_data = macd(close)
    macd_hist = macd_data["histogram"]

    # Comparer les 2 derniers "swings"
    price_now = float(close.iloc[-1])
    price_prev = float(close.iloc[-lookback])
    rsi_now = float(rsi_series.iloc[-1])
    rsi_prev = float(rsi_series.iloc[-lookback])
    macd_now = float(macd_hist.iloc[-1])
    macd_prev = float(macd_hist.iloc[-lookback])

    rsi_div = "none"
    macd_div = "none"
    score = 0

    if not any(np.isnan(v) for v in [rsi_now, rsi_prev, macd_now, macd_prev]):
        # RSI divergence
        if price_now < price_prev and rsi_now > rsi_prev:
            rsi_div = "bullish"
            score += 15
        elif price_now > price_prev and rsi_now < rsi_prev:
            rsi_div = "bearish"
            score -= 15

        # MACD divergence
        if price_now < price_prev and macd_now > macd_prev:
            macd_div = "bullish"
            score += 10
        elif price_now > price_prev and macd_now < macd_prev:
            macd_div = "bearish"
            score -= 10

    return {
        "rsi_divergence": rsi_div,
        "macd_divergence": macd_div,
        "score": score,
    }


# ============================================================
# SCORE TECHNIQUE COMPOSITE
# ============================================================

def compute_technical_score(close: pd.Series, high: pd.Series,
                            low: pd.Series, volume: pd.Series) -> float:
    """Score technique composite (0-100) basé sur 20 indicateurs.

    7 familles pondérées :
    - Tendance (SMA + ADX) : 20%
    - Momentum (RSI, MACD, Williams, CCI, ROC) : 25%
    - Volatilité (Bollinger, ATR) : 10%
    - Volume (OBV, CMF, VWAP) : 20%
    - Structure (Pivot Points) : 10%
    - Divergences : 10%
    - Force de tendance (ADX) : 5%
    """
    last = close.iloc[-1]

    # --- 1. Tendance (20%) ---
    sma_20 = sma(close, 20).iloc[-1]
    sma_50 = sma(close, 50).iloc[-1]
    sma_200 = sma(close, 200).iloc[-1]

    trend_score = 50.0
    if not np.isnan(sma_200):
        if last > sma_20 > sma_50 > sma_200:
            trend_score = 90.0
        elif last > sma_50 > sma_200:
            trend_score = 70.0
        elif last < sma_20 < sma_50 < sma_200:
            trend_score = 10.0
        elif last < sma_50 < sma_200:
            trend_score = 30.0

    # --- 2. Momentum (25%) — 5 indicateurs ---
    rsi_val = rsi(close).iloc[-1]
    macd_data_val = macd(close)
    macd_hist = macd_data_val["histogram"].iloc[-1]
    williams = williams_r(high, low, close).iloc[-1] if len(close) >= 14 else -50
    cci_val = cci(high, low, close).iloc[-1] if len(close) >= 20 else 0
    roc_val = roc(close).iloc[-1] if len(close) >= 12 else 0

    momentum_score = 50.0
    momentum_signals = 0

    if not np.isnan(rsi_val):
        if rsi_val > 60:
            momentum_signals += 1
        elif rsi_val < 40:
            momentum_signals -= 1

    if not np.isnan(macd_hist):
        if macd_hist > 0:
            momentum_signals += 1
        else:
            momentum_signals -= 1

    if not np.isnan(williams):
        if williams > -20:
            momentum_signals += 1  # Suracheté mais momentum fort
        elif williams < -80:
            momentum_signals -= 1

    if not np.isnan(cci_val):
        if cci_val > 100:
            momentum_signals += 1
        elif cci_val < -100:
            momentum_signals -= 1

    if not np.isnan(roc_val):
        if roc_val > 5:
            momentum_signals += 1
        elif roc_val < -5:
            momentum_signals -= 1

    momentum_score = 50 + momentum_signals * 10
    momentum_score = max(0, min(100, momentum_score))

    # --- 3. Volatilité (10%) ---
    bb = bollinger_bands(close)
    bb_upper = bb["upper"].iloc[-1]
    bb_lower = bb["lower"].iloc[-1]

    vol_score = 50.0
    if not np.isnan(bb_upper) and not np.isnan(bb_lower) and bb_upper != bb_lower:
        bb_position = (last - bb_lower) / (bb_upper - bb_lower)
        vol_score = max(0, min(100, bb_position * 100))

    # --- 4. Volume (20%) — 3 indicateurs ---
    obv_series = obv(close, volume)
    cmf = chaikin_money_flow(high, low, close, volume).iloc[-1] if len(close) >= 20 else 0
    vwap_val = vwap(high, low, close, volume).iloc[-1] if len(close) >= 20 else last

    volume_score = 50.0
    vol_signals = 0

    # OBV trend
    if len(obv_series) >= 20:
        if obv_series.iloc[-1] > obv_series.iloc[-20]:
            vol_signals += 1
        else:
            vol_signals -= 1

    # CMF
    if not np.isnan(cmf):
        if cmf > 0.1:
            vol_signals += 1  # Forte pression acheteuse
        elif cmf < -0.1:
            vol_signals -= 1

    # Prix vs VWAP
    if not np.isnan(vwap_val) and vwap_val > 0:
        if last > vwap_val:
            vol_signals += 1  # Au-dessus du prix institutionnel
        else:
            vol_signals -= 1

    # Volume ratio
    vol_sma_val = volume_sma(volume).iloc[-1]
    if not np.isnan(vol_sma_val) and vol_sma_val > 0:
        vol_ratio = volume.iloc[-1] / vol_sma_val
        if vol_ratio > 1.5:
            vol_signals += 1

    volume_score = 50 + vol_signals * 12
    volume_score = max(0, min(100, volume_score))

    # --- 5. Structure (10%) ---
    structure_score = 50.0
    if len(close) >= 2:
        pivots = pivot_points(high, low, close)
        if last > pivots["r1"]:
            structure_score = 80  # Au-dessus de R1 = fort
        elif last > pivots["pp"]:
            structure_score = 65  # Au-dessus du pivot = positif
        elif last > pivots["s1"]:
            structure_score = 45  # Entre pivot et S1 = neutre
        elif last > pivots["s2"]:
            structure_score = 30  # Sous S1 = faible
        else:
            structure_score = 15  # Sous S2 = très faible

    # --- 6. Divergences (10%) ---
    div_result = detect_divergences(close)
    div_score = 50 + div_result["score"]  # -25 à +25 autour de 50
    div_score = max(0, min(100, div_score))

    # --- 7. Force de tendance ADX (5%) ---
    adx_score = 50.0
    if len(close) >= 30:
        adx_val = adx(high, low, close).iloc[-1]
        if not np.isnan(adx_val):
            if adx_val > 40:
                adx_score = 90  # Tendance très forte
            elif adx_val > 25:
                adx_score = 70  # Tendance forte
            elif adx_val > 20:
                adx_score = 50  # Tendance faible
            else:
                adx_score = 30  # Pas de tendance (range)

    # --- Score final pondéré ---
    score = (
        trend_score * 0.20 +
        momentum_score * 0.25 +
        vol_score * 0.10 +
        volume_score * 0.20 +
        structure_score * 0.10 +
        div_score * 0.10 +
        adx_score * 0.05
    )

    return round(max(0, min(100, score)), 2)


def compute_technical_breakdown(close: pd.Series, high: pd.Series,
                                 low: pd.Series, volume: pd.Series) -> dict:
    """Retourne le détail complet de l'analyse technique avec tous les sous-scores."""
    last = close.iloc[-1]

    # Tendance
    sma_20 = sma(close, 20).iloc[-1]
    sma_50 = sma(close, 50).iloc[-1]
    sma_200 = sma(close, 200).iloc[-1] if len(close) >= 200 else float("nan")
    trend_score = 50.0
    trend_signal = "Neutre"
    if not np.isnan(sma_200):
        if last > sma_20 > sma_50 > sma_200:
            trend_score, trend_signal = 90.0, "Haussier fort (prix > SMA20 > SMA50 > SMA200)"
        elif last > sma_50 > sma_200:
            trend_score, trend_signal = 70.0, "Haussier (prix > SMA50 > SMA200)"
        elif last < sma_20 < sma_50 < sma_200:
            trend_score, trend_signal = 10.0, "Baissier fort (prix < SMA20 < SMA50 < SMA200)"
        elif last < sma_50 < sma_200:
            trend_score, trend_signal = 30.0, "Baissier (prix < SMA50 < SMA200)"

    # Momentum
    rsi_val = rsi(close).iloc[-1]
    macd_data_val = macd(close)
    macd_hist = macd_data_val["histogram"].iloc[-1]
    williams_val = williams_r(high, low, close).iloc[-1] if len(close) >= 14 else -50
    cci_val_r = cci(high, low, close).iloc[-1] if len(close) >= 20 else 0
    roc_val = roc(close).iloc[-1] if len(close) >= 12 else 0

    momentum_signals = 0
    if not np.isnan(rsi_val):
        momentum_signals += 1 if rsi_val > 60 else (-1 if rsi_val < 40 else 0)
    if not np.isnan(macd_hist):
        momentum_signals += 1 if macd_hist > 0 else -1
    if not np.isnan(williams_val):
        momentum_signals += 1 if williams_val > -20 else (-1 if williams_val < -80 else 0)
    if not np.isnan(cci_val_r):
        momentum_signals += 1 if cci_val_r > 100 else (-1 if cci_val_r < -100 else 0)
    if not np.isnan(roc_val):
        momentum_signals += 1 if roc_val > 5 else (-1 if roc_val < -5 else 0)
    momentum_score = max(0, min(100, 50 + momentum_signals * 10))

    # Volatilité
    bb = bollinger_bands(close)
    bb_upper = bb["upper"].iloc[-1]
    bb_lower = bb["lower"].iloc[-1]
    bb_position = 0.5
    vol_score = 50.0
    if not np.isnan(bb_upper) and not np.isnan(bb_lower) and bb_upper != bb_lower:
        bb_position = (last - bb_lower) / (bb_upper - bb_lower)
        vol_score = max(0, min(100, bb_position * 100))
    atr_val = atr(high, low, close).iloc[-1] if len(close) >= 14 else 0
    atr_pct = (atr_val / last * 100) if last > 0 else 0

    # Volume
    obv_series = obv(close, volume)
    cmf_val = chaikin_money_flow(high, low, close, volume).iloc[-1] if len(close) >= 20 else 0
    vwap_val = vwap(high, low, close, volume).iloc[-1] if len(close) >= 20 else last
    vol_sma_val = volume_sma(volume).iloc[-1] if len(volume) >= 20 else volume.iloc[-1]
    vol_ratio = float(volume.iloc[-1] / vol_sma_val) if vol_sma_val > 0 else 1

    vol_signals = 0
    if len(obv_series) >= 20:
        vol_signals += 1 if obv_series.iloc[-1] > obv_series.iloc[-20] else -1
    if not np.isnan(cmf_val):
        vol_signals += 1 if cmf_val > 0.1 else (-1 if cmf_val < -0.1 else 0)
    if not np.isnan(vwap_val) and vwap_val > 0:
        vol_signals += 1 if last > vwap_val else -1
    if vol_ratio > 1.5:
        vol_signals += 1
    volume_score = max(0, min(100, 50 + vol_signals * 12))

    # Structure
    structure_score = 50.0
    pivot_data = {}
    if len(close) >= 2:
        pivots = pivot_points(high, low, close)
        pivot_data = {k: round(float(v), 2) for k, v in pivots.items()}
        if last > pivots["r1"]:
            structure_score = 80
        elif last > pivots["pp"]:
            structure_score = 65
        elif last > pivots["s1"]:
            structure_score = 45
        elif last > pivots["s2"]:
            structure_score = 30
        else:
            structure_score = 15

    # Divergences
    div_result = detect_divergences(close)
    div_score = max(0, min(100, 50 + div_result["score"]))

    # ADX
    adx_score = 50.0
    adx_val = 0
    if len(close) >= 30:
        adx_val = float(adx(high, low, close).iloc[-1])
        if not np.isnan(adx_val):
            adx_score = 90 if adx_val > 40 else 70 if adx_val > 25 else 50 if adx_val > 20 else 30

    final = round(max(0, min(100,
        trend_score * 0.20 + momentum_score * 0.25 + vol_score * 0.10 +
        volume_score * 0.20 + structure_score * 0.10 + div_score * 0.10 + adx_score * 0.05
    )), 2)

    def _safe(v):
        if isinstance(v, (float, np.floating)):
            return None if np.isnan(v) else round(float(v), 2)
        return v

    return {
        "score": final,
        "families": [
            {"name": "Tendance", "score": round(trend_score, 1), "weight": 20, "signal": trend_signal,
             "indicators": [
                 {"name": "SMA 20", "value": _safe(sma_20), "signal": "Haussier" if last > sma_20 else "Baissier"},
                 {"name": "SMA 50", "value": _safe(sma_50), "signal": "Haussier" if last > sma_50 else "Baissier"},
                 {"name": "SMA 200", "value": _safe(sma_200), "signal": "Haussier" if not np.isnan(sma_200) and last > sma_200 else "Baissier" if not np.isnan(sma_200) else "N/A"},
             ]},
            {"name": "Momentum", "score": round(momentum_score, 1), "weight": 25, "signal": f"{momentum_signals} signaux sur 5",
             "indicators": [
                 {"name": "RSI (14)", "value": _safe(rsi_val), "signal": "Suracheté" if rsi_val > 70 else "Survendu" if rsi_val < 30 else "Haussier" if rsi_val > 60 else "Baissier" if rsi_val < 40 else "Neutre"},
                 {"name": "MACD Hist", "value": _safe(macd_hist), "signal": "Haussier" if macd_hist > 0 else "Baissier"},
                 {"name": "Williams %R", "value": _safe(williams_val), "signal": "Suracheté" if williams_val > -20 else "Survendu" if williams_val < -80 else "Neutre"},
                 {"name": "CCI", "value": _safe(cci_val_r), "signal": "Fort" if cci_val_r > 100 else "Faible" if cci_val_r < -100 else "Neutre"},
                 {"name": "ROC (12)", "value": _safe(roc_val), "signal": "Haussier" if roc_val > 5 else "Baissier" if roc_val < -5 else "Neutre"},
             ]},
            {"name": "Volatilité", "score": round(vol_score, 1), "weight": 10,
             "signal": f"BB position {bb_position:.0%}",
             "indicators": [
                 {"name": "Bollinger Haut", "value": _safe(bb_upper)},
                 {"name": "Bollinger Bas", "value": _safe(bb_lower)},
                 {"name": "ATR (14)", "value": _safe(atr_val), "signal": f"{atr_pct:.1f}% du prix"},
             ]},
            {"name": "Volume", "score": round(volume_score, 1), "weight": 20, "signal": f"{vol_signals} signaux sur 4",
             "indicators": [
                 {"name": "Volume Ratio", "value": round(vol_ratio, 2), "signal": "Fort" if vol_ratio > 1.5 else "Normal"},
                 {"name": "CMF", "value": _safe(cmf_val), "signal": "Acheteurs" if cmf_val > 0.1 else "Vendeurs" if cmf_val < -0.1 else "Neutre"},
                 {"name": "Prix vs VWAP", "value": _safe(vwap_val), "signal": "Au-dessus" if last > vwap_val else "En dessous"},
                 {"name": "OBV Trend", "signal": "Hausse" if len(obv_series) >= 20 and obv_series.iloc[-1] > obv_series.iloc[-20] else "Baisse"},
             ]},
            {"name": "Structure", "score": round(structure_score, 1), "weight": 10,
             "signal": "Au-dessus R1" if structure_score >= 80 else "Au-dessus Pivot" if structure_score >= 65 else "Sous Pivot",
             "indicators": [{"name": k.upper(), "value": v} for k, v in pivot_data.items()]},
            {"name": "Divergences", "score": round(div_score, 1), "weight": 10,
             "signal": div_result.get("type", "Aucune"),
             "indicators": [
                 {"name": "RSI Divergence", "signal": div_result.get("rsi_div", "Aucune")},
                 {"name": "MACD Divergence", "signal": div_result.get("macd_div", "Aucune")},
             ]},
            {"name": "Force Tendance", "score": round(adx_score, 1), "weight": 5,
             "signal": f"ADX={adx_val:.0f}" + (" Très fort" if adx_val > 40 else " Fort" if adx_val > 25 else " Faible" if adx_val > 20 else " Range"),
             "indicators": [{"name": "ADX (14)", "value": _safe(adx_val)}]},
        ],
    }
