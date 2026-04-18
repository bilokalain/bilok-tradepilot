"""Anti-corrélation portefeuille — éviter de concentrer le risque

Avant d'ajouter une position, vérifie que le nouvel actif
ne corrèle pas trop avec les positions existantes.

Si corrélation > 0.7 avec une position existante :
- Réduire la taille (pas doubler le même risque)
- Avertir l'utilisateur
- Suggérer un actif alternatif moins corrélé

Si corrélation < 0.3 :
- Bonus de diversification
- Le portefeuille est mieux protégé
"""

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily, Position, PositionStatus


def compute_correlation(db: Session, symbol_a: str, symbol_b: str,
                        lookback: int = 60) -> float | None:
    """Corrélation entre deux actifs — lit depuis le cache disque si disponible."""
    # Essayer le cache d'abord (instantané)
    try:
        from backend.modules.scanner.correlation_cache import get_pairwise_correlation
        cached = get_pairwise_correlation(symbol_a, symbol_b, str(lookback) if lookback in (60, 252) else "60")
        if cached is not None:
            return cached
    except Exception:
        pass

    # Fallback : calcul direct depuis la BDD
    asset_a = db.query(Asset).filter_by(symbol=symbol_a).first()
    asset_b = db.query(Asset).filter_by(symbol=symbol_b).first()
    if not asset_a or not asset_b:
        return None

    rows_a = db.query(OHLCVDaily).filter_by(asset_id=asset_a.id).order_by(OHLCVDaily.date.desc()).limit(lookback).all()
    rows_b = db.query(OHLCVDaily).filter_by(asset_id=asset_b.id).order_by(OHLCVDaily.date.desc()).limit(lookback).all()

    if len(rows_a) < 20 or len(rows_b) < 20:
        return None

    closes_a = pd.Series([float(r.close) for r in reversed(rows_a)])
    closes_b = pd.Series([float(r.close) for r in reversed(rows_b)])

    min_len = min(len(closes_a), len(closes_b))
    ret_a = closes_a.iloc[:min_len].pct_change().dropna()
    ret_b = closes_b.iloc[:min_len].pct_change().dropna()

    if len(ret_a) < 10 or len(ret_b) < 10:
        return None

    min_len2 = min(len(ret_a), len(ret_b))
    corr = float(ret_a.iloc[:min_len2].corr(ret_b.iloc[:min_len2]))
    return corr if not np.isnan(corr) else None


def check_portfolio_correlation(db: Session, new_symbol: str) -> dict:
    """Vérifie la corrélation du nouvel actif avec les positions existantes.

    Retourne :
    - can_add : bool
    - sizing_modifier : 0.5 à 1.2
    - correlations : liste des corrélations avec chaque position
    """
    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    if not positions:
        return {
            "can_add": True,
            "sizing_modifier": 1.0,
            "diversification_bonus": True,
            "correlations": [],
            "reason": "Première position — aucune corrélation à vérifier",
        }

    correlations = []
    max_corr = 0
    high_corr_count = 0

    for pos in positions:
        asset = db.query(Asset).filter_by(id=pos.asset_id).first()
        if not asset or asset.symbol == new_symbol:
            continue

        corr = compute_correlation(db, new_symbol, asset.symbol)
        if corr is not None:
            correlations.append({
                "symbol": asset.symbol,
                "correlation": round(corr, 3),
                "level": "HIGH" if abs(corr) > 0.7 else "MEDIUM" if abs(corr) > 0.4 else "LOW",
            })
            if abs(corr) > max_corr:
                max_corr = abs(corr)
            if abs(corr) > 0.7:
                high_corr_count += 1

    # Décision
    if max_corr > 0.85:
        sizing_modifier = 0.3
        reason = f"Corrélation très forte ({max_corr:.2f}) — position fortement réduite"
    elif max_corr > 0.7:
        sizing_modifier = 0.5
        reason = f"Corrélation forte ({max_corr:.2f}) — position réduite de moitié"
    elif max_corr > 0.5:
        sizing_modifier = 0.8
        reason = f"Corrélation modérée ({max_corr:.2f}) — légère réduction"
    elif max_corr < 0.3:
        sizing_modifier = 1.1  # Bonus diversification
        reason = "Faible corrélation — bonus de diversification (+10%)"
    else:
        sizing_modifier = 1.0
        reason = "Corrélation acceptable"

    # Bloquer si trop de positions corrélées
    can_add = True
    if high_corr_count >= 3:
        can_add = False
        reason = f"{high_corr_count} positions fortement corrélées — risque de concentration trop élevé"

    return {
        "can_add": can_add,
        "sizing_modifier": round(sizing_modifier, 2),
        "max_correlation": round(max_corr, 3),
        "high_corr_count": high_corr_count,
        "diversification_bonus": sizing_modifier > 1.0,
        "correlations": correlations,
        "reason": reason,
    }
