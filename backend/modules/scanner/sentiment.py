"""Critère 2 — Sentiment : Score composite NLP

Sources (Phase 1 — gratuites) :
1. Reddit (r/wallstreetbets, r/stocks, r/CryptoCurrency) via PRAW
2. NewsAPI (flux actualités financières)

Analyse :
- Comptage mentions positives/négatives/neutres
- Score de volume (buzz)
- Score de polarité (positif vs négatif)

Score final : combinaison volume + polarité (0-100)
"""

import re
from datetime import datetime, timedelta

import numpy as np


# Mots-clés financiers pour l'analyse simple (sans FinBERT en Phase 1)
BULLISH_KEYWORDS = [
    "buy", "bull", "moon", "rocket", "calls", "long", "breakout", "upgrade",
    "beat", "growth", "rally", "surge", "soar", "strong", "record", "high",
    "acheter", "haussier", "hausse", "croissance", "record",
]

BEARISH_KEYWORDS = [
    "sell", "bear", "crash", "puts", "short", "dump", "downgrade", "miss",
    "decline", "drop", "plunge", "weak", "low", "recession", "fear",
    "vendre", "baissier", "baisse", "chute", "krach", "peur",
]


def analyse_text_sentiment(text: str) -> dict:
    """Analyse le sentiment d'un texte.

    Essaie FinBERT d'abord, fallback sur mots-clés si indisponible.
    Retourne : polarity (-1 à +1), label (positive/negative/neutral)
    """
    # Essayer FinBERT
    try:
        from backend.models.sentiment import get_finbert
        finbert = get_finbert()
        if finbert.is_available:
            result = finbert.predict_one(text)
            return {
                "polarity": result["polarity"],
                "label": result["label"],
                "method": "finbert",
                "confidence": result.get("confidence", 0),
            }
    except Exception:
        pass

    # Fallback : mots-clés
    text_lower = text.lower()
    words = re.findall(r'\w+', text_lower)

    bullish_count = sum(1 for w in words if w in BULLISH_KEYWORDS)
    bearish_count = sum(1 for w in words if w in BEARISH_KEYWORDS)
    total = bullish_count + bearish_count

    if total == 0:
        return {"polarity": 0, "label": "neutral", "method": "keywords"}

    polarity = (bullish_count - bearish_count) / total
    label = "positive" if polarity > 0.2 else "negative" if polarity < -0.2 else "neutral"

    return {
        "polarity": round(polarity, 3),
        "label": label,
        "method": "keywords",
    }


def compute_sentiment_score(mentions: list[dict]) -> dict:
    """Calcule le score de sentiment composite.

    Chaque mention : {"text": "...", "source": "reddit/news", "date": "..."}

    Combine :
    - Volume score (nombre de mentions) — 40%
    - Polarity score (positif vs négatif) — 60%
    """
    if not mentions:
        return {
            "score": 50.0,  # Neutre par défaut
            "volume_score": 0,
            "polarity_score": 50.0,
            "num_mentions": 0,
            "sentiment_breakdown": {"positive": 0, "negative": 0, "neutral": 0},
        }

    # Analyser chaque mention
    sentiments = [analyse_text_sentiment(m.get("text", "")) for m in mentions]

    positive = sum(1 for s in sentiments if s["label"] == "positive")
    negative = sum(1 for s in sentiments if s["label"] == "negative")
    neutral = sum(1 for s in sentiments if s["label"] == "neutral")
    total = len(sentiments)

    # Volume score : plus de mentions = plus d'intérêt
    if total > 50:
        volume_score = 90
    elif total > 20:
        volume_score = 70
    elif total > 10:
        volume_score = 50
    elif total > 3:
        volume_score = 30
    else:
        volume_score = 15

    # Polarity score
    avg_polarity = np.mean([s["polarity"] for s in sentiments])
    polarity_score = 50 + avg_polarity * 50  # -1→0, 0→50, +1→100
    polarity_score = max(0, min(100, polarity_score))

    # Score final
    score = volume_score * 0.40 + polarity_score * 0.60

    return {
        "score": round(score, 2),
        "volume_score": round(volume_score, 1),
        "polarity_score": round(polarity_score, 1),
        "avg_polarity": round(avg_polarity, 3),
        "num_mentions": total,
        "sentiment_breakdown": {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
        },
    }


async def fetch_reddit_mentions(symbol: str, limit: int = 50) -> list[dict]:
    """Récupère les mentions d'un symbole sur Reddit.

    Nécessite PRAW configuré (REDDIT_CLIENT_ID / SECRET dans .env).
    Phase 1 : retourne des données simulées si PRAW non configuré.
    """
    try:
        import praw
        from backend.config.settings import settings

        if not settings.REDDIT_CLIENT_ID:
            return _simulate_mentions(symbol)

        reddit = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent="Bilok-TradePilot/0.1",
        )

        mentions = []
        subreddits = ["wallstreetbets", "stocks", "investing"]
        if "USD" in symbol or "BTC" in symbol or "ETH" in symbol:
            subreddits.extend(["CryptoCurrency", "Bitcoin"])

        clean_symbol = symbol.replace("-USD", "").replace("-", "")

        for sub_name in subreddits:
            try:
                subreddit = reddit.subreddit(sub_name)
                for post in subreddit.search(clean_symbol, limit=limit // len(subreddits), time_filter="week"):
                    mentions.append({
                        "text": f"{post.title} {post.selftext[:200]}",
                        "source": f"reddit/{sub_name}",
                        "date": datetime.fromtimestamp(post.created_utc).isoformat(),
                        "score": post.score,
                    })
            except Exception:
                continue

        return mentions

    except ImportError:
        return _simulate_mentions(symbol)
    except Exception:
        return _simulate_mentions(symbol)


def _simulate_mentions(symbol: str) -> list[dict]:
    """Données simulées pour le développement."""
    np.random.seed(hash(symbol) % 2**31)
    n = np.random.randint(5, 30)
    mentions = []
    templates_bull = [
        f"{symbol} looking strong, breakout incoming",
        f"Just bought more {symbol}, bullish on growth",
        f"{symbol} beat earnings, strong momentum",
        f"Long {symbol}, this is the dip to buy",
    ]
    templates_bear = [
        f"{symbol} overvalued, sell before the drop",
        f"Short {symbol}, weak fundamentals",
        f"{symbol} crash coming, get out now",
        f"Bearish on {symbol}, declining revenue",
    ]
    templates_neutral = [
        f"What do you think about {symbol}?",
        f"{symbol} holding steady around current levels",
        f"Anyone watching {symbol} today?",
    ]

    for i in range(n):
        r = np.random.random()
        if r > 0.5:
            text = np.random.choice(templates_bull)
        elif r > 0.2:
            text = np.random.choice(templates_neutral)
        else:
            text = np.random.choice(templates_bear)

        mentions.append({
            "text": text,
            "source": "reddit/simulated",
            "date": (datetime.utcnow() - timedelta(hours=np.random.randint(1, 168))).isoformat(),
        })

    return mentions
