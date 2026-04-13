"""Thèses manuelles — intégrer vos convictions dans le modèle

Permet d'entrer des thèses comme :
- "Le pétrole va monter à cause de la guerre en Iran"
- "La tech va corriger après les résultats"
- "Bitcoin va exploser grâce au halving"

Chaque thèse :
1. Identifie les actifs corrélés à la thèse
2. Booste ou pénalise leur score dans le scanner
3. Génère un plan de trade (quoi acheter, quoi shorter, sizing)
4. Persiste dans un fichier JSON (survit aux redémarrages)

Quand aucune thèse n'est active → le système fonctionne normalement.
"""

import json
import time
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

THESES_FILE = Path("data/manual_theses.json")
THESES_FILE.parent.mkdir(exist_ok=True)


# Mapping actif → actifs corrélés connus (pour les thèses sur des thèmes)
THEME_ASSETS = {
    "PETROLE": {
        "long": ["CL=F", "XOM", "CVX", "COP", "XLE", "TTE.PA"],
        "short": ["XLU", "NEE"],
        "description": "Hausse du pétrole favorise les pétrolières, pénalise les utilities",
    },
    "OIL": {
        "long": ["CL=F", "XOM", "CVX", "COP", "XLE", "TTE.PA"],
        "short": ["XLU", "NEE"],
        "description": "Oil up = energy stocks up, utilities down",
    },
    "OR": {
        "long": ["GC=F", "GLD", "SI=F", "SLV", "PL=F"],
        "short": ["SPY", "QQQ"],
        "description": "L'or monte en période d'incertitude, les actions baissent",
    },
    "GOLD": {
        "long": ["GC=F", "GLD", "SI=F", "SLV", "PL=F"],
        "short": ["SPY", "QQQ"],
        "description": "Gold = safe haven, equities inversely correlated",
    },
    "TECH": {
        "long": ["QQQ", "XLK", "AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMZN", "AMD", "CRM"],
        "short": ["XLU", "XLP"],
        "description": "Tech en hausse = growth over value",
    },
    "BITCOIN": {
        "long": ["BTC-USD", "ETH-USD", "SOL-USD", "COIN", "DOGE-USD", "ADA-USD"],
        "short": [],
        "description": "Bitcoin entraîne tout le marché crypto",
    },
    "CRYPTO": {
        "long": ["BTC-USD", "ETH-USD", "SOL-USD", "COIN", "DOGE-USD", "ADA-USD", "AVAX-USD", "LINK-USD"],
        "short": [],
        "description": "Bull run crypto global",
    },
    "RECESSION": {
        "long": ["TLT", "GLD", "XLU", "XLP", "JNJ", "KO", "PG"],
        "short": ["SPY", "QQQ", "XLY", "XLF", "ARKK"],
        "description": "Récession = défensif en hausse, cyclique en baisse",
    },
    "INFLATION": {
        "long": ["GC=F", "CL=F", "GLD", "XLE", "XOM", "ZW=F"],
        "short": ["TLT", "QQQ", "ARKK"],
        "description": "Inflation = commodities up, obligations et tech down",
    },
    "TAUX": {
        "long": ["XLF", "JPM", "GS", "BAC"],
        "short": ["TLT", "XLRE", "NEE"],
        "description": "Hausse des taux = banques profitent, immobilier et obligations souffrent",
    },
    "GUERRE": {
        "long": ["LMT", "RTX", "BA", "GC=F", "CL=F"],
        "short": ["SPY", "EEM"],
        "description": "Conflit = défense et commodities up, marchés généraux down",
    },
    "IA": {
        "long": ["NVDA", "AMD", "AVGO", "MSFT", "GOOGL", "META", "PLTR", "SNOW", "DDOG", "CRM", "NOW"],
        "short": [],
        "description": "Boom de l'intelligence artificielle",
    },
    "PHARMA": {
        "long": ["XLV", "LLY", "UNH", "JNJ", "PFE", "ABBV", "MRK", "MRNA", "ISRG"],
        "short": [],
        "description": "Secteur pharma/santé en hausse",
    },
    "LUXE": {
        "long": ["MC.PA", "OR.PA", "RACE.MI", "RI.PA"],
        "short": [],
        "description": "Luxe européen en hausse",
    },
}


def _load_theses() -> list[dict]:
    if THESES_FILE.exists():
        try:
            return json.loads(THESES_FILE.read_text())
        except Exception:
            return []
    return []


def _save_theses(theses: list[dict]):
    THESES_FILE.write_text(json.dumps(theses, indent=2, ensure_ascii=False, default=str))


def add_thesis(
    theme: str,
    direction: str,
    conviction: str,
    reason: str = "",
    horizon_days: int = 30,
    custom_symbols_long: list[str] | None = None,
    custom_symbols_short: list[str] | None = None,
) -> dict:
    """Ajoute une thèse manuelle.

    Args:
        theme: le thème (PETROLE, TECH, BITCOIN, IA...) ou un symbole (AAPL, NVDA)
        direction: HAUSSE ou BAISSE
        conviction: FAIBLE (25%), MOYENNE (50%), FORTE (75%), CERTAINE (90%)
        reason: explication libre
        horizon_days: horizon en jours (30 par défaut)
        custom_symbols_long: symboles à acheter (override le thème)
        custom_symbols_short: symboles à shorter (override le thème)
    """
    conviction_map = {
        "FAIBLE": 0.25,
        "MOYENNE": 0.50,
        "FORTE": 0.75,
        "CERTAINE": 0.90,
    }
    conv_pct = conviction_map.get(conviction.upper(), 0.50)

    # Résoudre les actifs du thème
    theme_upper = theme.upper().strip()
    theme_data = THEME_ASSETS.get(theme_upper)

    if theme_data:
        if direction.upper() == "HAUSSE":
            symbols_long = custom_symbols_long or theme_data["long"]
            symbols_short = custom_symbols_short or theme_data["short"]
        else:
            symbols_long = custom_symbols_long or theme_data["short"]
            symbols_short = custom_symbols_short or theme_data["long"]
        description = theme_data["description"]
    else:
        # C'est un symbole unique
        from backend.modules.scanner.quick_analyse import resolve_symbol
        resolved = resolve_symbol(theme)
        if direction.upper() == "HAUSSE":
            symbols_long = custom_symbols_long or [resolved]
            symbols_short = custom_symbols_short or []
        else:
            symbols_long = custom_symbols_long or []
            symbols_short = custom_symbols_short or [resolved]
        description = f"Thèse sur {resolved}"

    thesis = {
        "id": f"thesis_{int(time.time())}",
        "theme": theme,
        "direction": direction.upper(),
        "conviction": conviction.upper(),
        "conviction_pct": conv_pct,
        "reason": reason,
        "horizon_days": horizon_days,
        "symbols_long": symbols_long,
        "symbols_short": symbols_short,
        "description": description,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (date.today() + timedelta(days=horizon_days)).isoformat(),
        "active": True,
    }

    theses = _load_theses()
    theses.append(thesis)
    _save_theses(theses)

    return thesis


def remove_thesis(thesis_id: str) -> bool:
    theses = _load_theses()
    theses = [t for t in theses if t.get("id") != thesis_id]
    _save_theses(theses)
    return True


def get_active_theses() -> list[dict]:
    theses = _load_theses()
    today = date.today().isoformat()
    active = [t for t in theses if t.get("active") and t.get("expires_at", "9999") >= today]
    return active


def deactivate_thesis(thesis_id: str) -> bool:
    theses = _load_theses()
    for t in theses:
        if t.get("id") == thesis_id:
            t["active"] = False
    _save_theses(theses)
    return True


def compute_thesis_boost(symbol: str) -> dict:
    """Calcule le boost/malus de score pour un actif basé sur les thèses actives.

    Retourne :
    - score_modifier : +/- points à ajouter au score scanner
    - sizing_modifier : multiplicateur du sizing
    - reasons : pourquoi
    """
    active = get_active_theses()
    if not active:
        return {"score_modifier": 0, "sizing_modifier": 1.0, "reasons": [], "has_thesis": False}

    total_boost = 0
    sizing_mult = 1.0
    reasons = []

    for thesis in active:
        conv = thesis.get("conviction_pct", 0.5)

        if symbol in thesis.get("symbols_long", []):
            boost = 15 * conv  # Max +13.5 points pour conviction CERTAINE
            total_boost += boost
            sizing_mult *= (1 + conv * 0.3)  # Max ×1.27
            reasons.append(f"Thèse HAUSSE {thesis['theme']} ({thesis['conviction']}) : +{boost:.0f} pts")

        elif symbol in thesis.get("symbols_short", []):
            malus = -15 * conv
            total_boost += malus
            sizing_mult *= max(0.5, 1 - conv * 0.3)
            reasons.append(f"Thèse BAISSE {thesis['theme']} ({thesis['conviction']}) : {malus:.0f} pts")

    return {
        "score_modifier": round(total_boost, 1),
        "sizing_modifier": round(sizing_mult, 3),
        "reasons": reasons,
        "has_thesis": len(reasons) > 0,
        "active_theses": len(active),
    }


def generate_trade_plan(db: Session, thesis_id: str) -> dict:
    """Génère un plan de trade complet pour une thèse."""
    theses = _load_theses()
    thesis = next((t for t in theses if t.get("id") == thesis_id), None)
    if not thesis:
        return {"error": "Thèse non trouvée"}

    from backend.database.models import Asset, OHLCVDaily
    from backend.modules.scanner.indicators import atr
    import pandas as pd

    plan_long = []
    plan_short = []
    conv = thesis.get("conviction_pct", 0.5)

    for sym in thesis.get("symbols_long", []):
        asset = db.query(Asset).filter_by(symbol=sym).first()
        if not asset:
            continue
        rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(50).all()
        if len(rows) < 14:
            continue

        closes = pd.Series([float(r.close) for r in reversed(rows)])
        highs = pd.Series([float(r.high) for r in reversed(rows)])
        lows = pd.Series([float(r.low) for r in reversed(rows)])
        price = float(rows[0].close)
        atr_val = float(atr(highs, lows, closes, 14).iloc[-1])

        sizing_pct = 5 * conv  # 1.25% à 4.5% selon conviction
        plan_long.append({
            "symbol": sym,
            "name": asset.name,
            "action": "ACHETER",
            "price": round(price, 2),
            "stop_loss": round(price - 2 * atr_val, 2),
            "take_profit": round(price + 3 * atr_val, 2),
            "sizing_pct": round(sizing_pct, 1),
        })

    for sym in thesis.get("symbols_short", []):
        asset = db.query(Asset).filter_by(symbol=sym).first()
        if not asset:
            continue
        rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(50).all()
        if len(rows) < 14:
            continue

        closes = pd.Series([float(r.close) for r in reversed(rows)])
        highs = pd.Series([float(r.high) for r in reversed(rows)])
        lows = pd.Series([float(r.low) for r in reversed(rows)])
        price = float(rows[0].close)
        atr_val = float(atr(highs, lows, closes, 14).iloc[-1])

        sizing_pct = 3 * conv
        plan_short.append({
            "symbol": sym,
            "name": asset.name,
            "action": "SHORTER",
            "price": round(price, 2),
            "stop_loss": round(price + 2 * atr_val, 2),
            "take_profit": round(price - 3 * atr_val, 2),
            "sizing_pct": round(sizing_pct, 1),
        })

    return {
        "thesis": thesis,
        "plan_long": plan_long,
        "plan_short": plan_short,
        "total_positions": len(plan_long) + len(plan_short),
        "total_sizing_pct": round(sum(p["sizing_pct"] for p in plan_long + plan_short), 1),
    }
