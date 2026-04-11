"""Critère 7 — Macro Tailwind Score (MTS)

Évalue si l'environnement macro est favorable à l'actif :
1. Phase du cycle économique (expansion/pic/contraction/creux)
2. Régime de taux (proxy via TLT — obligations long terme)
3. Force du dollar (proxy via DXY ou UUP)
4. Liquidité globale (proxy via volume de marché total)

Phase 1 : basé sur les données des ETF en base (SPY, TLT, GLD).
Phase 2 : FRED API (taux Fed, M2, VIX, DXY).
Score 0-100 : > 60 = vent macro favorable, < 40 = vent contraire.
"""

import numpy as np
import pandas as pd

from backend.modules.scanner.indicators import sma, rsi


def detect_economic_cycle(spy_close: pd.Series) -> dict:
    """Détecte la phase du cycle via SPY comme proxy de l'économie.

    Expansion : SPY > SMA200 et pente positive
    Pic : SPY > SMA200 mais pente qui s'aplatit
    Contraction : SPY < SMA200 et pente négative
    Creux : SPY < SMA200 mais pente qui remonte
    """
    if len(spy_close) < 200:
        return {"phase": "unknown", "score": 50}

    sma_200 = sma(spy_close, 200)
    last = spy_close.iloc[-1]
    s200 = sma_200.iloc[-1]

    if np.isnan(s200):
        return {"phase": "unknown", "score": 50}

    # Pente SMA200 sur 40j
    s200_40ago = sma_200.iloc[-40] if len(sma_200) >= 40 and not np.isnan(sma_200.iloc[-40]) else s200
    slope = (s200 - s200_40ago) / s200_40ago if s200_40ago != 0 else 0

    above = last > s200

    if above and slope > 0.01:
        return {"phase": "expansion", "score": 80}
    elif above and slope <= 0.01:
        return {"phase": "pic", "score": 60}
    elif not above and slope < -0.01:
        return {"phase": "contraction", "score": 25}
    elif not above and slope >= -0.01:
        return {"phase": "creux", "score": 45}
    else:
        return {"phase": "unknown", "score": 50}


def detect_rate_regime(tlt_close: pd.Series) -> dict:
    """Régime de taux via TLT (ETF obligations 20+ ans).

    TLT monte = taux baissent = favorable pour les actions (surtout growth)
    TLT baisse = taux montent = défavorable
    """
    if len(tlt_close) < 50:
        return {"regime": "neutral", "score": 50}

    ret_30 = (tlt_close.iloc[-1] / tlt_close.iloc[-30] - 1) * 100 if len(tlt_close) >= 30 else 0
    ret_90 = (tlt_close.iloc[-1] / tlt_close.iloc[-90] - 1) * 100 if len(tlt_close) >= 90 else 0

    if ret_30 > 3 and ret_90 > 5:
        return {"regime": "dovish", "score": 80}  # Taux en forte baisse
    elif ret_30 > 1:
        return {"regime": "easing", "score": 65}
    elif ret_30 < -3 and ret_90 < -5:
        return {"regime": "hawkish", "score": 20}  # Taux en forte hausse
    elif ret_30 < -1:
        return {"regime": "tightening", "score": 35}
    else:
        return {"regime": "neutral", "score": 50}


def detect_risk_appetite(spy_close: pd.Series, gld_close: pd.Series) -> dict:
    """Appétit pour le risque via ratio SPY/GLD.

    SPY surperforme GLD = risk-on (favorable actions)
    GLD surperforme SPY = risk-off (défavorable actions)
    """
    if len(spy_close) < 30 or len(gld_close) < 30:
        return {"regime": "neutral", "score": 50}

    spy_ret = (spy_close.iloc[-1] / spy_close.iloc[-30] - 1) * 100
    gld_ret = (gld_close.iloc[-1] / gld_close.iloc[-30] - 1) * 100
    spread = spy_ret - gld_ret

    if spread > 5:
        return {"regime": "risk_on", "score": 80}
    elif spread > 2:
        return {"regime": "risk_on_moderate", "score": 65}
    elif spread < -5:
        return {"regime": "risk_off", "score": 20}
    elif spread < -2:
        return {"regime": "risk_off_moderate", "score": 35}
    else:
        return {"regime": "neutral", "score": 50}


def compute_mts_score(asset_class: str,
                       spy_close: pd.Series | None = None,
                       tlt_close: pd.Series | None = None,
                       gld_close: pd.Series | None = None) -> dict:
    """Score Macro Tailwind (MTS) composite.

    Adapté par classe d'actif :
    - Actions : cycle (40%) + taux (30%) + risk appetite (30%)
    - Crypto : risk appetite (50%) + cycle (30%) + taux (20%)
    - Commodities : inversé risk appetite
    """
    cycle = detect_economic_cycle(spy_close) if spy_close is not None else {"phase": "unknown", "score": 50}
    rates = detect_rate_regime(tlt_close) if tlt_close is not None else {"regime": "neutral", "score": 50}
    risk = detect_risk_appetite(spy_close, gld_close) if spy_close is not None and gld_close is not None else {"regime": "neutral", "score": 50}

    if asset_class in ("ACTION_US", "ACTION_EU", "ETF"):
        score = cycle["score"] * 0.40 + rates["score"] * 0.30 + risk["score"] * 0.30
    elif asset_class == "CRYPTO":
        score = risk["score"] * 0.50 + cycle["score"] * 0.30 + rates["score"] * 0.20
    elif asset_class == "COMMODITY":
        # Commodities bénéficient du risk-off et des taux bas
        inverted_risk = 100 - risk["score"]
        score = inverted_risk * 0.40 + rates["score"] * 0.35 + cycle["score"] * 0.25
    else:
        score = cycle["score"] * 0.34 + rates["score"] * 0.33 + risk["score"] * 0.33

    return {
        "score": round(min(100, max(0, score)), 2),
        "cycle": cycle,
        "rates": rates,
        "risk_appetite": risk,
    }
