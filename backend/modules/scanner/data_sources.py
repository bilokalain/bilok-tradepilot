"""Sources de données gratuites — FRED, Google Trends, Reddit

FRED (Federal Reserve Economic Data) :
- Taux Fed Funds, Treasury 10Y, VIX, Chômage, M2, DXY
- Clé gratuite : https://fred.stlouisfed.org/docs/api/api_key.html

Google Trends (pytrends) :
- Intérêt de recherche pour chaque actif
- Pas de clé API nécessaire

Reddit (PRAW) :
- Mentions sur r/wallstreetbets, r/stocks, r/CryptoCurrency
- Clé gratuite : https://www.reddit.com/prefs/apps
"""

import logging
from datetime import datetime, timedelta
from functools import lru_cache

import numpy as np
import pandas as pd

logger = logging.getLogger("tradepilot.data_sources")


# ============================================================
# FRED — Données macro-économiques
# ============================================================

# Cache en mémoire (les données macro changent lentement)
_fred_cache: dict = {}
_fred_cache_time: float = 0
FRED_CACHE_TTL = 3600  # 1 heure

FRED_SERIES = {
    "fed_funds_rate": "FEDFUNDS",       # Taux directeur Fed
    "treasury_10y": "DGS10",            # Taux Treasury 10 ans
    "vix": "VIXCLS",                    # Indice de peur
    "unemployment": "UNRATE",           # Taux de chômage
    "cpi_yoy": "CPIAUCSL",             # Inflation (CPI)
    "m2_money": "M2SL",                # Masse monétaire M2
    "initial_claims": "ICSA",           # Demandes d'allocations chômage
    "consumer_sentiment": "UMCSENT",    # Confiance des consommateurs
}


def fetch_fred_data() -> dict:
    """Récupère les dernières données FRED."""
    import time
    global _fred_cache, _fred_cache_time

    if time.time() - _fred_cache_time < FRED_CACHE_TTL and _fred_cache:
        return _fred_cache

    from backend.config.settings import settings
    if not settings.FRED_API_KEY:
        logger.info("[FRED] Pas de clé API — utilisation des estimations")
        return _estimate_macro_data()

    try:
        from fredapi import Fred
        fred = Fred(api_key=settings.FRED_API_KEY)
        result = {}

        for name, series_id in FRED_SERIES.items():
            try:
                data = fred.get_series(series_id, observation_start=datetime.now() - timedelta(days=365))
                if not data.empty:
                    result[name] = {
                        "value": float(data.iloc[-1]),
                        "previous": float(data.iloc[-2]) if len(data) > 1 else None,
                        "date": str(data.index[-1].date()),
                        "change": float(data.iloc[-1] - data.iloc[-2]) if len(data) > 1 else 0,
                    }
            except Exception as e:
                logger.warning(f"[FRED] Erreur {name}: {e}")

        _fred_cache = result
        _fred_cache_time = time.time()
        return result

    except Exception as e:
        logger.warning(f"[FRED] Erreur globale: {e}")
        return _estimate_macro_data()


def _estimate_macro_data() -> dict:
    """Estimations par défaut quand FRED n'est pas disponible."""
    return {
        "fed_funds_rate": {"value": 5.25, "previous": 5.25, "date": "estimated", "change": 0},
        "treasury_10y": {"value": 4.2, "previous": 4.3, "date": "estimated", "change": -0.1},
        "vix": {"value": 18.5, "previous": 17.0, "date": "estimated", "change": 1.5},
        "unemployment": {"value": 3.8, "previous": 3.7, "date": "estimated", "change": 0.1},
    }


def compute_macro_score_from_fred(asset_class: str) -> dict:
    """Score macro enrichi avec les vraies données FRED.

    Remplace les proxies SPY/TLT/GLD par les vrais indicateurs économiques.
    """
    data = fetch_fred_data()

    score = 50.0
    factors = {}

    # VIX (peur du marché)
    vix = data.get("vix", {}).get("value", 20)
    if vix < 15:
        vix_score = 80  # Marché calme = favorable
    elif vix < 20:
        vix_score = 65
    elif vix < 30:
        vix_score = 40
    else:
        vix_score = 15  # Panique
    factors["vix"] = {"value": vix, "score": vix_score}

    # Taux Fed (direction)
    fed_change = data.get("fed_funds_rate", {}).get("change", 0)
    if fed_change < 0:
        fed_score = 75  # Baisse des taux = favorable
    elif fed_change == 0:
        fed_score = 55
    else:
        fed_score = 30  # Hausse des taux
    factors["fed_funds"] = {"change": fed_change, "score": fed_score}

    # Chômage
    unemp = data.get("unemployment", {}).get("value", 4)
    unemp_change = data.get("unemployment", {}).get("change", 0)
    if unemp < 4 and unemp_change <= 0:
        unemp_score = 75
    elif unemp < 5:
        unemp_score = 55
    else:
        unemp_score = 30
    factors["unemployment"] = {"value": unemp, "score": unemp_score}

    # Pondération par classe d'actif
    if asset_class in ("ACTION_US", "ACTION_EU", "ETF"):
        score = vix_score * 0.35 + fed_score * 0.35 + unemp_score * 0.30
    elif asset_class == "CRYPTO":
        score = vix_score * 0.20 + fed_score * 0.50 + unemp_score * 0.30
    elif asset_class == "COMMODITY":
        score = vix_score * 0.25 + fed_score * 0.40 + unemp_score * 0.35
    else:
        score = (vix_score + fed_score + unemp_score) / 3

    return {
        "score": round(score, 2),
        "factors": factors,
        "source": "fred" if "estimated" not in str(data.get("vix", {}).get("date", "")) else "estimated",
    }


# ============================================================
# Google Trends — Intérêt de recherche
# ============================================================

_trends_cache: dict = {}
_trends_cache_time: dict = {}
TRENDS_CACHE_TTL = 3600


def fetch_google_trends(keyword: str) -> dict:
    """Récupère l'intérêt Google Trends pour un mot-clé."""
    import time

    cache_key = keyword
    if cache_key in _trends_cache and time.time() - _trends_cache_time.get(cache_key, 0) < TRENDS_CACHE_TTL:
        return _trends_cache[cache_key]

    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl='fr-FR', tz=60)
        pytrends.build_payload([keyword], timeframe='now 7-d')
        data = pytrends.interest_over_time()

        if data.empty:
            return {"keyword": keyword, "score": 50, "trend": "stable", "source": "google_trends"}

        values = data[keyword].values
        current = int(values[-1])
        avg = float(np.mean(values))
        trend_direction = "rising" if current > avg * 1.2 else "falling" if current < avg * 0.8 else "stable"

        result = {
            "keyword": keyword,
            "current_interest": current,
            "avg_interest": round(avg, 1),
            "score": min(100, current),
            "trend": trend_direction,
            "source": "google_trends",
        }

        _trends_cache[cache_key] = result
        _trends_cache_time[cache_key] = time.time()
        return result

    except Exception as e:
        logger.warning(f"[TRENDS] Erreur {keyword}: {e}")
        return {"keyword": keyword, "score": 50, "trend": "unknown", "source": "error"}


def get_trends_score(symbol: str) -> float:
    """Score d'intérêt Google Trends pour un actif (0-100)."""
    # Convertir le symbole en terme de recherche
    search_map = {
        "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana",
        "AAPL": "Apple stock", "MSFT": "Microsoft stock", "TSLA": "Tesla stock",
        "NVDA": "NVIDIA stock", "AMZN": "Amazon stock", "GOOGL": "Google stock",
        "GC=F": "Gold price", "CL=F": "Oil price", "SI=F": "Silver price",
    }
    keyword = search_map.get(symbol, symbol)
    result = fetch_google_trends(keyword)
    return result["score"]


# ============================================================
# Reddit — Mentions temps réel (amélioré)
# ============================================================

def fetch_reddit_live(symbol: str, limit: int = 50) -> list[dict]:
    """Récupère les mentions Reddit en temps réel via PRAW."""
    from backend.config.settings import settings

    if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
        return []

    try:
        import praw

        reddit = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent="TradePilot/0.1",
        )

        clean = symbol.replace("-USD", "").replace("=X", "").replace("=F", "")
        clean = clean.split(".")[0]  # Enlever .PA, .DE, etc.

        mentions = []
        subs = ["wallstreetbets", "stocks", "investing"]
        if "BTC" in symbol or "ETH" in symbol or "SOL" in symbol:
            subs.extend(["CryptoCurrency", "Bitcoin"])

        per_sub = max(5, limit // len(subs))

        for sub_name in subs:
            try:
                subreddit = reddit.subreddit(sub_name)
                for post in subreddit.search(clean, limit=per_sub, time_filter="week", sort="relevance"):
                    mentions.append({
                        "text": f"{post.title} {(post.selftext or '')[:300]}",
                        "source": f"reddit/{sub_name}",
                        "date": datetime.fromtimestamp(post.created_utc).isoformat(),
                        "score": post.score,
                        "num_comments": post.num_comments,
                        "upvote_ratio": post.upvote_ratio,
                    })
            except Exception:
                continue

        return mentions

    except Exception as e:
        logger.warning(f"[REDDIT] Erreur: {e}")
        return []
