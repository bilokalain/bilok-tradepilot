"""Sector Rotation — les secteurs tournent selon le cycle économique

Modèle classique de rotation sectorielle :

Expansion précoce : Tech, Consommation discrétionnaire, Industrie
Expansion tardive : Énergie, Matériaux, Finance
Pic/Ralentissement : Santé, Utilities, Consommation de base
Récession : Obligations (TLT), Or (GLD), Cash

On utilise les ETF sectoriels (XLK, XLF, XLE, XLV, etc.) pour détecter
quels secteurs accélèrent ou décélèrent.
"""

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily


# Mapping secteur → ETF → phase du cycle
SECTOR_ETF_MAP = {
    "XLK": {"sector": "Technology", "cycle_phase": "early_expansion", "weight_expansion": 0.9, "weight_recession": 0.3},
    "XLY": {"sector": "Consumer Discretionary", "cycle_phase": "early_expansion", "weight_expansion": 0.8, "weight_recession": 0.3},
    "XLI": {"sector": "Industrials", "cycle_phase": "early_expansion", "weight_expansion": 0.7, "weight_recession": 0.4},
    "XLF": {"sector": "Financials", "cycle_phase": "late_expansion", "weight_expansion": 0.7, "weight_recession": 0.4},
    "XLE": {"sector": "Energy", "cycle_phase": "late_expansion", "weight_expansion": 0.6, "weight_recession": 0.5},
    "XLB": {"sector": "Materials", "cycle_phase": "late_expansion", "weight_expansion": 0.6, "weight_recession": 0.4},
    "XLV": {"sector": "Health Care", "cycle_phase": "recession", "weight_expansion": 0.5, "weight_recession": 0.8},
    "XLP": {"sector": "Consumer Staples", "cycle_phase": "recession", "weight_expansion": 0.4, "weight_recession": 0.9},
    "XLU": {"sector": "Utilities", "cycle_phase": "recession", "weight_expansion": 0.3, "weight_recession": 0.9},
    "XLRE": {"sector": "Real Estate", "cycle_phase": "late_expansion", "weight_expansion": 0.5, "weight_recession": 0.5},
}

# Mapping actif → secteur
ASSET_SECTOR_MAP = {
    # Tech
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology", "AMZN": "Technology",
    "NVDA": "Technology", "META": "Technology", "AMD": "Technology", "INTC": "Technology",
    "AVGO": "Technology", "CRM": "Technology", "ORCL": "Technology", "ADBE": "Technology",
    "CSCO": "Technology", "QCOM": "Technology", "PLTR": "Technology", "COIN": "Technology",
    "NOW": "Technology", "PANW": "Technology", "CRWD": "Technology", "SNOW": "Technology",
    "NET": "Technology", "SHOP": "Technology", "DDOG": "Technology",
    # Finance
    "JPM": "Financials", "GS": "Financials", "MS": "Financials", "BAC": "Financials",
    "C": "Financials", "WFC": "Financials", "BLK": "Financials", "V": "Financials",
    "MA": "Financials", "PYPL": "Financials", "AXP": "Financials",
    # Santé
    "JNJ": "Health Care", "UNH": "Health Care", "LLY": "Health Care", "PFE": "Health Care",
    "ABBV": "Health Care", "MRK": "Health Care", "TMO": "Health Care", "ABT": "Health Care",
    "AMGN": "Health Care", "ISRG": "Health Care", "MRNA": "Health Care",
    # Consommation
    "WMT": "Consumer Staples", "COST": "Consumer Staples", "KO": "Consumer Staples",
    "PEP": "Consumer Staples", "PG": "Consumer Staples", "CL": "Consumer Staples",
    "TSLA": "Consumer Discretionary", "HD": "Consumer Discretionary", "NKE": "Consumer Discretionary",
    "SBUX": "Consumer Discretionary", "MCD": "Consumer Discretionary", "DIS": "Consumer Discretionary",
    "NFLX": "Consumer Discretionary", "ABNB": "Consumer Discretionary", "UBER": "Consumer Discretionary",
    # Énergie
    "XOM": "Energy", "CVX": "Energy", "COP": "Energy",
    # Industrie
    "BA": "Industrials", "CAT": "Industrials", "DE": "Industrials", "GE": "Industrials",
    "LMT": "Industrials", "RTX": "Industrials", "UPS": "Industrials", "FDX": "Industrials",
    # Utilities
    "NEE": "Utilities", "DUK": "Utilities", "SO": "Utilities",
    # Télécom
    "T": "Communication Services", "VZ": "Communication Services", "TMUS": "Communication Services",
    "CMCSA": "Communication Services",
}


def compute_sector_momentum(db: Session) -> dict:
    """Calcule le momentum de chaque secteur via les ETF sectoriels."""
    sector_perf = {}

    for etf_symbol, info in SECTOR_ETF_MAP.items():
        asset = db.query(Asset).filter_by(symbol=etf_symbol).first()
        if not asset:
            continue

        rows = (
            db.query(OHLCVDaily)
            .filter_by(asset_id=asset.id)
            .order_by(OHLCVDaily.date.desc())
            .limit(63)
            .all()
        )
        if len(rows) < 21:
            continue

        closes = [float(r.close) for r in reversed(rows)]

        perf_1m = (closes[-1] / closes[-21] - 1) * 100 if len(closes) >= 21 else 0
        perf_3m = (closes[-1] / closes[0] - 1) * 100 if len(closes) >= 63 else perf_1m

        sector_perf[info["sector"]] = {
            "etf": etf_symbol,
            "perf_1m": round(perf_1m, 2),
            "perf_3m": round(perf_3m, 2),
            "cycle_phase": info["cycle_phase"],
            "momentum_score": round((perf_1m * 0.6 + perf_3m * 0.4), 2),
        }

    return sector_perf


def detect_rotation(db: Session) -> dict:
    """Détecte la rotation sectorielle en cours.

    Quels secteurs accélèrent ? Quels secteurs décélèrent ?
    Ça indique où on en est dans le cycle.
    """
    perf = compute_sector_momentum(db)
    if not perf:
        return {"rotation": "unknown", "sectors": {}}

    # Trier par momentum
    sorted_sectors = sorted(perf.items(), key=lambda x: x[1]["momentum_score"], reverse=True)

    # Identifier les leaders et les retardataires
    leaders = sorted_sectors[:3]
    laggards = sorted_sectors[-3:]

    # Détecter la phase du cycle
    leader_phases = [s[1]["cycle_phase"] for s in leaders]
    if leader_phases.count("early_expansion") >= 2:
        cycle = "early_expansion"
        description = "Début d'expansion — Tech et Consommation discrétionnaire en tête"
    elif leader_phases.count("late_expansion") >= 2:
        cycle = "late_expansion"
        description = "Expansion tardive — Énergie et Finance accélèrent"
    elif leader_phases.count("recession") >= 2:
        cycle = "recession"
        description = "Phase défensive — Utilities et Santé en tête"
    else:
        cycle = "transition"
        description = "Rotation en cours — pas de phase dominante claire"

    # Secteurs à privilégier et à éviter
    favor = [s[0] for s in leaders]
    avoid = [s[0] for s in laggards]

    return {
        "cycle_phase": cycle,
        "description": description,
        "favor_sectors": favor,
        "avoid_sectors": avoid,
        "sectors": perf,
        "ranking": [(s[0], s[1]["momentum_score"]) for s in sorted_sectors],
    }


def get_sector_score(symbol: str, rotation: dict) -> dict:
    """Score de rotation sectorielle pour un actif donné.

    L'actif est-il dans un secteur en accélération ou en décélération ?
    """
    sector = ASSET_SECTOR_MAP.get(symbol)
    if not sector:
        return {"score": 50, "sector": None, "reason": "Secteur non identifié"}

    sectors = rotation.get("sectors", {})
    sector_data = sectors.get(sector)

    if not sector_data:
        return {"score": 50, "sector": sector, "reason": "Pas de données sectorielles"}

    momentum = sector_data["momentum_score"]
    in_favor = sector in rotation.get("favor_sectors", [])
    in_avoid = sector in rotation.get("avoid_sectors", [])

    if in_favor:
        score = min(90, 65 + momentum)
    elif in_avoid:
        score = max(15, 35 + momentum)
    else:
        score = 50 + momentum * 0.5

    score = max(0, min(100, score))

    return {
        "score": round(score, 1),
        "sector": sector,
        "momentum": momentum,
        "in_favor": in_favor,
        "in_avoid": in_avoid,
        "cycle_phase": rotation.get("cycle_phase", "unknown"),
    }
