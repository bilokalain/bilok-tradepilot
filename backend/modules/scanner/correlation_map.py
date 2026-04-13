"""Corrélation rapide — trouve les actifs liés à un actif donné

Cas d'usage :
- "Le pétrole va exploser" → quels actifs en profitent ? lesquels souffrent ?
- "NVDA monte" → quels actifs suivent ? lesquels font l'inverse ?
- "L'or monte" → hedge contre quoi exactement ?

Calcule la corrélation de TOUS les 218 actifs avec l'actif cible
et les trie en 3 catégories :
1. Corrélation positive forte (> 0.5) → bougent ensemble
2. Corrélation négative forte (< -0.3) → bougent à l'inverse (hedge)
3. Pas de corrélation (-0.3 à 0.3) → indépendants

+ Analyse d'impact : si l'actif cible monte de X%, combien chaque
  actif corrélé devrait bouger (via le beta de corrélation).
"""

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily


def compute_correlation_map(db: Session, target_symbol: str,
                             lookback: int = 120) -> dict:
    """Calcule la corrélation de tous les actifs avec le symbole cible.

    Args:
        target_symbol: le symbole à analyser (ex: CL=F pour le pétrole)
        lookback: nombre de jours pour le calcul (120 = ~6 mois)
    """
    # Charger l'actif cible
    target_asset = db.query(Asset).filter_by(symbol=target_symbol).first()
    if not target_asset:
        # Essayer de trouver par alias
        from backend.modules.scanner.quick_analyse import resolve_symbol
        resolved = resolve_symbol(target_symbol)
        target_asset = db.query(Asset).filter_by(symbol=resolved).first()
        if not target_asset:
            return {"error": f"Actif '{target_symbol}' non trouvé en base. Essayez le symbole Yahoo Finance (ex: CL=F pour Oil, GC=F pour Gold)."}

    target_rows = (
        db.query(OHLCVDaily)
        .filter_by(asset_id=target_asset.id)
        .order_by(OHLCVDaily.date.desc())
        .limit(lookback)
        .all()
    )
    if len(target_rows) < 30:
        return {"error": f"Pas assez de données pour {target_symbol} ({len(target_rows)} jours)"}

    target_dates = {r.date: float(r.close) for r in target_rows}
    target_returns = pd.Series(
        [float(r.close) for r in reversed(target_rows)]
    ).pct_change().dropna()

    # Comparer avec tous les actifs
    all_assets = db.query(Asset).filter_by(is_active=True).all()
    correlations = []

    for asset in all_assets:
        if asset.id == target_asset.id:
            continue

        rows = (
            db.query(OHLCVDaily)
            .filter_by(asset_id=asset.id)
            .order_by(OHLCVDaily.date.desc())
            .limit(lookback)
            .all()
        )
        if len(rows) < 30:
            continue

        asset_returns = pd.Series(
            [float(r.close) for r in reversed(rows)]
        ).pct_change().dropna()

        # Aligner les longueurs
        min_len = min(len(target_returns), len(asset_returns))
        if min_len < 20:
            continue

        corr = float(np.corrcoef(
            target_returns.iloc[:min_len].values,
            asset_returns.iloc[:min_len].values
        )[0, 1])

        if np.isnan(corr):
            continue

        # Beta : combien l'actif bouge pour 1% de mouvement du target
        target_std = float(target_returns.iloc[:min_len].std())
        asset_std = float(asset_returns.iloc[:min_len].std())
        beta = corr * (asset_std / target_std) if target_std > 0 else 0

        # Dernier prix
        last_price = float(rows[0].close) if rows else 0

        correlations.append({
            "symbol": asset.symbol,
            "name": asset.name,
            "asset_class": asset.asset_class.value,
            "correlation": round(corr, 3),
            "beta": round(beta, 3),
            "last_price": round(last_price, 2),
            "abs_correlation": round(abs(corr), 3),
        })

    # Trier par corrélation absolue décroissante
    correlations.sort(key=lambda x: x["abs_correlation"], reverse=True)

    # Catégoriser
    positive = [c for c in correlations if c["correlation"] > 0.4]
    negative = [c for c in correlations if c["correlation"] < -0.2]
    neutral = [c for c in correlations if -0.2 <= c["correlation"] <= 0.4]

    # Top corrélés
    positive.sort(key=lambda x: x["correlation"], reverse=True)
    negative.sort(key=lambda x: x["correlation"])

    return {
        "target": {
            "symbol": target_asset.symbol,
            "name": target_asset.name,
            "asset_class": target_asset.asset_class.value,
            "last_price": round(float(target_rows[0].close), 2),
        },
        "lookback_days": lookback,
        "total_compared": len(correlations),
        "positive_correlated": positive[:20],
        "negative_correlated": negative[:15],
        "num_positive": len(positive),
        "num_negative": len(negative),
        "num_neutral": len(neutral),
    }


def simulate_impact(db: Session, target_symbol: str,
                     move_pct: float, lookback: int = 120) -> dict:
    """Simule l'impact d'un mouvement du target sur tous les actifs corrélés.

    Ex: si Oil (CL=F) monte de +20%, combien chaque actif corrélé bouge ?
    """
    corr_map = compute_correlation_map(db, target_symbol, lookback)
    if "error" in corr_map:
        return corr_map

    target = corr_map["target"]
    impacts = []

    all_correlated = corr_map["positive_correlated"] + corr_map["negative_correlated"]

    for c in all_correlated:
        expected_move = move_pct * c["beta"]
        expected_price = c["last_price"] * (1 + expected_move / 100)

        impacts.append({
            "symbol": c["symbol"],
            "name": c["name"],
            "asset_class": c["asset_class"],
            "correlation": c["correlation"],
            "beta": c["beta"],
            "current_price": c["last_price"],
            "expected_move_pct": round(expected_move, 2),
            "expected_price": round(expected_price, 2),
            "impact": "BENEFICIE" if expected_move > 0 else "SOUFFRE",
        })

    impacts.sort(key=lambda x: x["expected_move_pct"], reverse=True)

    beneficiaires = [i for i in impacts if i["expected_move_pct"] > 1]
    victimes = [i for i in impacts if i["expected_move_pct"] < -1]

    return {
        "scenario": f"{target['symbol']} ({target['name']}) fait {move_pct:+.0f}%",
        "target": target,
        "move_pct": move_pct,
        "beneficiaires": beneficiaires,
        "victimes": victimes,
        "all_impacts": impacts,
        "summary": {
            "actifs_qui_montent": len(beneficiaires),
            "actifs_qui_baissent": len(victimes),
            "plus_gros_impact_positif": beneficiaires[0] if beneficiaires else None,
            "plus_gros_impact_negatif": victimes[-1] if victimes else None,
        },
    }
