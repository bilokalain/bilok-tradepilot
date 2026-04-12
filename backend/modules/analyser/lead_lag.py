"""Lead-Lag Detection — un actif bouge, les autres suivent avec un délai

Quand un secteur/actif leader bouge, les actifs corrélés suivent
typiquement avec 1-5 jours de retard. Détecter ce délai = entrer en avance.

Exemples historiques :
- Semi-conducteurs (NVDA) → Tech (QQQ) avec 1-2j de retard
- Cuivre (HG=F) → Industriels (CAT, DE) avec 2-3j
- BTC → Altcoins avec 1-3j
- Pétrole (CL=F) → Énergie (XOM, CVX) avec 1j

Méthode : cross-corrélation avec décalage temporel (lag).
On cherche le lag qui maximise la corrélation.
"""

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily


# Paires lead-lag connues
KNOWN_PAIRS = [
    # (leader, follower, lag_attendu_jours)
    ("NVDA", "AMD", 1),
    ("NVDA", "AVGO", 1),
    ("NVDA", "QQQ", 2),
    ("BTC-USD", "ETH-USD", 1),
    ("BTC-USD", "SOL-USD", 2),
    ("BTC-USD", "COIN", 1),
    ("CL=F", "XOM", 1),
    ("CL=F", "CVX", 1),
    ("GC=F", "GLD", 0),
    ("GC=F", "SI=F", 1),
    ("SPY", "IWM", 1),
    ("SPY", "VTI", 0),
    ("HG=F", "CAT", 2),
    ("HG=F", "XLI", 2),
    ("EURUSD=X", "EURGBP=X", 1),
    ("MC.PA", "OR.PA", 1),  # Luxe français
    ("SAP.DE", "SIE.DE", 1),  # Tech allemand
]


def compute_cross_correlation(series_a: pd.Series, series_b: pd.Series,
                               max_lag: int = 5) -> dict:
    """Calcule la cross-corrélation avec différents décalages.

    Retourne le lag optimal et la corrélation correspondante.
    Un lag positif signifie que B suit A avec ce retard.
    """
    ret_a = series_a.pct_change().dropna()
    ret_b = series_b.pct_change().dropna()

    min_len = min(len(ret_a), len(ret_b))
    if min_len < 30:
        return {"best_lag": 0, "best_corr": 0, "all_lags": {}}

    ret_a = ret_a.iloc[:min_len].values
    ret_b = ret_b.iloc[:min_len].values

    correlations = {}
    best_lag = 0
    best_corr = 0

    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            a = ret_a[:min_len - lag]
            b = ret_b[lag:min_len]
        else:
            a = ret_a[-lag:min_len]
            b = ret_b[:min_len + lag]

        if len(a) < 20:
            continue

        corr = float(np.corrcoef(a, b)[0, 1])
        if not np.isnan(corr):
            correlations[lag] = round(corr, 4)
            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag

    return {
        "best_lag": best_lag,
        "best_corr": round(best_corr, 4),
        "all_lags": correlations,
    }


def detect_lead_lag(db: Session, symbol: str, max_lag: int = 5) -> dict:
    """Détecte les relations lead-lag pour un actif.

    Cherche :
    1. L'actif est-il un LEADER (les autres le suivent) ?
    2. L'actif est-il un FOLLOWER (il suit quelqu'un d'autre) ?
    3. Y a-t-il un signal lead-lag exploitable maintenant ?
    """
    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return {"symbol": symbol, "leaders": [], "followers": [], "signal": None}

    rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(120).all()
    if len(rows) < 30:
        return {"symbol": symbol, "leaders": [], "followers": [], "signal": None}

    my_closes = pd.Series([float(r.close) for r in reversed(rows)])

    leaders = []   # Actifs qui mènent (mon actif les suit)
    followers = [] # Actifs qui suivent (mon actif les mène)

    # Chercher dans les paires connues
    relevant_pairs = [p for p in KNOWN_PAIRS if symbol in (p[0], p[1])]

    for leader_sym, follower_sym, expected_lag in relevant_pairs:
        other_sym = follower_sym if symbol == leader_sym else leader_sym
        other_asset = db.query(Asset).filter_by(symbol=other_sym).first()
        if not other_asset:
            continue

        other_rows = db.query(OHLCVDaily).filter_by(asset_id=other_asset.id).order_by(OHLCVDaily.date.desc()).limit(120).all()
        if len(other_rows) < 30:
            continue

        other_closes = pd.Series([float(r.close) for r in reversed(other_rows)])
        cc = compute_cross_correlation(other_closes, my_closes, max_lag)

        if abs(cc["best_corr"]) > 0.3:
            entry = {
                "symbol": other_sym,
                "lag": cc["best_lag"],
                "correlation": cc["best_corr"],
                "expected_lag": expected_lag,
            }

            if cc["best_lag"] > 0:
                # Positive lag = mon actif suit l'autre → l'autre est leader
                leaders.append(entry)
            elif cc["best_lag"] < 0:
                # Negative lag = l'autre suit mon actif → mon actif est leader
                followers.append(entry)

    # Chercher un signal exploitable
    signal = None
    for leader in leaders:
        leader_sym = leader["symbol"]
        leader_asset = db.query(Asset).filter_by(symbol=leader_sym).first()
        if not leader_asset:
            continue

        leader_rows = db.query(OHLCVDaily).filter_by(asset_id=leader_asset.id).order_by(OHLCVDaily.date.desc()).limit(10).all()
        if len(leader_rows) < 5:
            continue

        leader_closes = [float(r.close) for r in reversed(leader_rows)]

        # Le leader a-t-il bougé récemment ?
        leader_move = (leader_closes[-1] / leader_closes[-leader["lag"] - 1] - 1) * 100 if leader["lag"] > 0 and len(leader_closes) > leader["lag"] + 1 else 0

        if abs(leader_move) > 2:
            direction = "LONG" if leader_move > 0 else "SHORT"
            signal = {
                "leader": leader_sym,
                "leader_move": round(leader_move, 2),
                "lag_days": leader["lag"],
                "correlation": leader["correlation"],
                "predicted_direction": direction,
                "confidence": min(90, abs(leader_move) * 10 + abs(leader["correlation"]) * 30),
                "reason": f"{leader_sym} a bougé de {leader_move:+.1f}% il y a {leader['lag']}j — {symbol} devrait suivre",
            }
            break  # Prendre le premier signal

    return {
        "symbol": symbol,
        "leaders": leaders,
        "followers": followers,
        "signal": signal,
        "is_leader": len(followers) > len(leaders),
        "is_follower": len(leaders) > len(followers),
    }


def scan_lead_lag_signals(db: Session) -> list[dict]:
    """Scanne tous les actifs pour trouver des signaux lead-lag exploitables."""
    # Collecter tous les symboles des paires connues
    symbols = set()
    for leader, follower, _ in KNOWN_PAIRS:
        symbols.add(leader)
        symbols.add(follower)

    signals = []
    for symbol in symbols:
        result = detect_lead_lag(db, symbol)
        if result.get("signal"):
            signals.append(result)

    signals.sort(key=lambda x: x["signal"]["confidence"], reverse=True)
    return signals
