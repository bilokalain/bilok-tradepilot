"""Cache centralisé de la matrice de corrélation — calculée UNE SEULE FOIS.

Tous les modules (scanner, analyseur, scoring, exécution) lisent depuis ce cache
au lieu de recalculer la matrice 218×218 à chaque fois.

Calculée par le pipeline nocturne après le scanner, avant l'analyseur.
TTL : 12 heures (recalculée chaque nuit).
"""

import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily

logger = logging.getLogger("tradepilot.correlation_cache")

CACHE_FILE = Path("data/correlation_cache.json")
CACHE_TTL_SECONDS = 12 * 3600  # 12 heures


def build_correlation_cache(db: Session) -> dict:
    """Calcule la matrice de corrélation complète et la persiste sur disque.

    Appelée UNE FOIS par le pipeline nocturne.
    Retourne le dict sauvegardé.
    """
    logger.info("[CORR CACHE] Calcul de la matrice de corrélation complète...")
    start = time.time()

    assets = db.query(Asset).filter_by(is_active=True).all()

    # Charger les closes pour tous les actifs (60 jours)
    closes_dict = {}
    for asset in assets:
        rows = (
            db.query(OHLCVDaily)
            .filter_by(asset_id=asset.id)
            .order_by(OHLCVDaily.date.desc())
            .limit(252)
            .all()
        )
        if len(rows) >= 20:
            closes_dict[asset.symbol] = pd.Series(
                [float(r.close) for r in reversed(rows)],
                index=[r.date for r in reversed(rows)],
            )

    if len(closes_dict) < 2:
        logger.warning("[CORR CACHE] Pas assez d'actifs pour calculer les corrélations")
        return {}

    # Calculer les rendements et la matrice de corrélation
    returns_df = pd.DataFrame(
        {sym: closes.pct_change().dropna() for sym, closes in closes_dict.items()}
    )

    # Matrice 60 jours (court terme — utilisée par exécution/scoring)
    corr_60 = returns_df.iloc[-60:].corr() if len(returns_df) >= 60 else returns_df.corr()

    # Matrice 252 jours (long terme — utilisée par scanner/analyseur)
    corr_252 = returns_df.corr()

    # Convertir en dict sérialisable
    symbols = list(corr_60.columns)
    cache_data = {
        "symbols": symbols,
        "corr_60": {
            sym: {
                other: round(float(corr_60.loc[sym, other]), 4)
                if not np.isnan(corr_60.loc[sym, other]) else 0.0
                for other in symbols
            }
            for sym in symbols
        },
        "corr_252": {
            sym: {
                other: round(float(corr_252.loc[sym, other]), 4)
                if not np.isnan(corr_252.loc[sym, other]) else 0.0
                for other in symbols
            }
            for sym in symbols
        },
        "timestamp": time.time(),
        "n_assets": len(symbols),
    }

    # Sauvegarder
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache_data, ensure_ascii=False))

    elapsed = round(time.time() - start, 1)
    logger.info(f"[CORR CACHE] Matrice {len(symbols)}×{len(symbols)} calculée en {elapsed}s — sauvée sur disque")

    return cache_data


def get_correlation_cache() -> dict | None:
    """Lit le cache de corrélation depuis le disque.

    Retourne None si le cache n'existe pas ou est expiré.
    """
    if not CACHE_FILE.exists():
        return None

    try:
        data = json.loads(CACHE_FILE.read_text())
        age = time.time() - data.get("timestamp", 0)
        if age > CACHE_TTL_SECONDS:
            logger.warning(f"[CORR CACHE] Cache expiré ({age/3600:.1f}h)")
            return None
        return data
    except Exception:
        return None


def get_pairwise_correlation(symbol_a: str, symbol_b: str,
                              lookback: str = "60") -> float | None:
    """Récupère la corrélation entre deux actifs depuis le cache.

    Args:
        lookback: "60" ou "252"
    """
    cache = get_correlation_cache()
    if not cache:
        return None

    key = f"corr_{lookback}"
    corr_matrix = cache.get(key, {})
    row = corr_matrix.get(symbol_a, {})
    val = row.get(symbol_b)

    if val is not None and val != 0.0:
        return val
    return None


def get_correlated_assets(symbol: str, threshold: float = 0.4,
                           lookback: str = "60") -> list[dict]:
    """Liste les actifs corrélés au-dessus du seuil depuis le cache."""
    cache = get_correlation_cache()
    if not cache:
        return []

    key = f"corr_{lookback}"
    corr_matrix = cache.get(key, {})
    row = corr_matrix.get(symbol, {})

    results = []
    for other, corr in row.items():
        if other != symbol and abs(corr) >= threshold:
            results.append({"symbol": other, "correlation": corr})

    return sorted(results, key=lambda x: abs(x["correlation"]), reverse=True)
