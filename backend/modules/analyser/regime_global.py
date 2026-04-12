"""Régime Multi-Assets — détection du régime GLOBAL du marché

Au lieu de détecter le régime PAR actif, on analyse les relations
entre les grandes classes d'actifs pour comprendre le contexte global :

SPY (actions) + TLT (obligations) + GLD (or) + VIX + DXY (dollar)

4 régimes globaux :
- RISK-ON : SPY↑ TLT↓ GLD↓ VIX↓ → Tout va bien, prendre des risques
- RISK-OFF : SPY↓ TLT↑ GLD↑ VIX↑ → Peur, se protéger
- STAGFLATION : SPY↓ TLT↓ GLD↑ → Inflation + récession = le pire
- GOLDILOCKS : SPY↑ TLT↑ VIX↓ → Croissance + taux bas = idéal

Le régime global modifie les poids de TOUS les actifs.
"""

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily


# Assets clés pour le régime global
REGIME_ASSETS = {
    "equity": "SPY",
    "bonds": "TLT",
    "gold": "GLD",
    "volatility": "VIX",  # Pas en BDD directement — on utilise un proxy
}


def _load_recent_closes(db: Session, symbol: str, days: int = 60) -> pd.Series | None:
    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return None
    rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(days).all()
    if len(rows) < 20:
        return None
    return pd.Series([float(r.close) for r in reversed(rows)])


def _compute_momentum(closes: pd.Series, period: int = 21) -> float:
    """Rendement sur N jours en %."""
    if len(closes) < period:
        return 0
    return (closes.iloc[-1] / closes.iloc[-period] - 1) * 100


def _compute_trend(closes: pd.Series) -> str:
    """UP / DOWN / FLAT basé sur SMA 20 vs SMA 50."""
    if len(closes) < 50:
        return "FLAT"
    sma20 = closes.rolling(20).mean().iloc[-1]
    sma50 = closes.rolling(50).mean().iloc[-1]
    last = closes.iloc[-1]

    if np.isnan(sma20) or np.isnan(sma50):
        return "FLAT"

    if last > sma20 > sma50:
        return "UP"
    elif last < sma20 < sma50:
        return "DOWN"
    return "FLAT"


def detect_global_regime(db: Session) -> dict:
    """Détecte le régime global du marché.

    Analyse les relations inter-assets pour produire un régime global
    qui s'applique à TOUS les actifs.
    """
    spy = _load_recent_closes(db, "SPY")
    tlt = _load_recent_closes(db, "TLT")
    gld = _load_recent_closes(db, "GLD")

    if spy is None:
        return {
            "regime": "UNKNOWN",
            "confidence": 0,
            "description": "Données insuffisantes pour le régime global",
            "signals": {},
        }

    signals = {}

    # SPY — Actions
    spy_mom = _compute_momentum(spy)
    spy_trend = _compute_trend(spy)
    signals["equity"] = {
        "symbol": "SPY",
        "momentum_1m": round(spy_mom, 2),
        "trend": spy_trend,
    }

    # TLT — Obligations
    if tlt is not None:
        tlt_mom = _compute_momentum(tlt)
        tlt_trend = _compute_trend(tlt)
        signals["bonds"] = {
            "symbol": "TLT",
            "momentum_1m": round(tlt_mom, 2),
            "trend": tlt_trend,
        }

    # GLD — Or
    if gld is not None:
        gld_mom = _compute_momentum(gld)
        gld_trend = _compute_trend(gld)
        signals["gold"] = {
            "symbol": "GLD",
            "momentum_1m": round(gld_mom, 2),
            "trend": gld_trend,
        }

    # Proxy VIX : volatilité du SPY sur 20 jours vs 60 jours
    if spy is not None and len(spy) >= 60:
        vol_20 = spy.pct_change().iloc[-20:].std() * np.sqrt(252) * 100
        vol_60 = spy.pct_change().iloc[-60:].std() * np.sqrt(252) * 100
        vol_ratio = vol_20 / vol_60 if vol_60 > 0 else 1
        signals["volatility"] = {
            "vol_20d": round(vol_20, 1),
            "vol_60d": round(vol_60, 1),
            "ratio": round(vol_ratio, 2),
            "level": "HIGH" if vol_ratio > 1.3 else "LOW" if vol_ratio < 0.7 else "NORMAL",
        }

    # Corrélation SPY/TLT (négative = normal, positive = problème)
    if spy is not None and tlt is not None:
        min_len = min(len(spy), len(tlt))
        corr = spy.iloc[-min_len:].pct_change().corr(tlt.iloc[-min_len:].pct_change())
        signals["spy_tlt_correlation"] = round(float(corr), 3) if not np.isnan(corr) else 0

    # === Détection du régime ===
    spy_up = spy_trend == "UP" or spy_mom > 2
    spy_down = spy_trend == "DOWN" or spy_mom < -2
    tlt_up = signals.get("bonds", {}).get("trend") == "UP"
    tlt_down = signals.get("bonds", {}).get("trend") == "DOWN"
    gld_up = signals.get("gold", {}).get("trend") == "UP"
    gld_down = signals.get("gold", {}).get("trend") == "DOWN"
    vol_high = signals.get("volatility", {}).get("level") == "HIGH"
    vol_low = signals.get("volatility", {}).get("level") == "LOW"

    # Scores pour chaque régime
    scores = {
        "RISK_ON": 0,
        "RISK_OFF": 0,
        "STAGFLATION": 0,
        "GOLDILOCKS": 0,
    }

    # RISK-ON : SPY↑ TLT↓ GLD↓ VIX↓
    if spy_up:
        scores["RISK_ON"] += 3
    if tlt_down:
        scores["RISK_ON"] += 1
    if gld_down:
        scores["RISK_ON"] += 1
    if vol_low:
        scores["RISK_ON"] += 2

    # RISK-OFF : SPY↓ TLT↑ GLD↑ VIX↑
    if spy_down:
        scores["RISK_OFF"] += 3
    if tlt_up:
        scores["RISK_OFF"] += 1
    if gld_up:
        scores["RISK_OFF"] += 1
    if vol_high:
        scores["RISK_OFF"] += 2

    # STAGFLATION : SPY↓ TLT↓ GLD↑
    if spy_down:
        scores["STAGFLATION"] += 2
    if tlt_down:
        scores["STAGFLATION"] += 2
    if gld_up:
        scores["STAGFLATION"] += 3

    # GOLDILOCKS : SPY↑ TLT↑ VIX↓
    if spy_up:
        scores["GOLDILOCKS"] += 2
    if tlt_up:
        scores["GOLDILOCKS"] += 3
    if vol_low:
        scores["GOLDILOCKS"] += 2

    # Régime dominant
    total = sum(scores.values())
    if total == 0:
        regime = "NEUTRAL"
        confidence = 0
    else:
        regime = max(scores, key=scores.get)
        confidence = scores[regime] / total

    descriptions = {
        "RISK_ON": "Appétit pour le risque — actions favorisées, obligations et or délaissés",
        "RISK_OFF": "Fuite vers la sécurité — obligations et or favorisés, actions sous pression",
        "STAGFLATION": "Inflation + ralentissement — or seul refuge, actions et obligations baissent",
        "GOLDILOCKS": "Conditions idéales — croissance + taux bas = favorable à tout",
        "NEUTRAL": "Pas de signal clair — marché sans direction dominante",
    }

    # Impact sur les classes d'actifs
    asset_class_modifiers = {
        "RISK_ON": {"ACTION_US": 1.2, "ACTION_EU": 1.1, "ETF": 1.15, "CRYPTO": 1.3, "COMMODITY": 0.9, "FOREX": 1.0},
        "RISK_OFF": {"ACTION_US": 0.7, "ACTION_EU": 0.7, "ETF": 0.8, "CRYPTO": 0.5, "COMMODITY": 1.2, "FOREX": 1.0},
        "STAGFLATION": {"ACTION_US": 0.6, "ACTION_EU": 0.6, "ETF": 0.7, "CRYPTO": 0.7, "COMMODITY": 1.4, "FOREX": 1.1},
        "GOLDILOCKS": {"ACTION_US": 1.3, "ACTION_EU": 1.2, "ETF": 1.2, "CRYPTO": 1.2, "COMMODITY": 1.0, "FOREX": 0.9},
        "NEUTRAL": {"ACTION_US": 1.0, "ACTION_EU": 1.0, "ETF": 1.0, "CRYPTO": 1.0, "COMMODITY": 1.0, "FOREX": 1.0},
    }

    return {
        "regime": regime,
        "confidence": round(confidence, 3),
        "description": descriptions.get(regime, ""),
        "scores": {k: round(v / total, 3) if total > 0 else 0 for k, v in scores.items()},
        "signals": signals,
        "asset_class_modifiers": asset_class_modifiers.get(regime, asset_class_modifiers["NEUTRAL"]),
    }
