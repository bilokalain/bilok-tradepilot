"""Critère 8 — Topologie Sociale (SGI)

Mesure l'adoption communautaire et la qualité des discussions :
1. Volume de mentions (buzz social)
2. Ratio signal/bruit (qualité des discussions)
3. Network Effect (Loi de Metcalfe pour crypto)
4. Tendance de l'intérêt (Google Trends proxy via momentum mentions)

Phase 1 : basé sur le sentiment déjà implémenté + heuristiques.
Phase 2 : Twitter/X API, Stocktwits, Google Trends (pytrends).
Score 0-100.
"""

import numpy as np

from backend.modules.scanner.sentiment import compute_sentiment_score


def compute_signal_to_noise(mentions: list[dict]) -> float:
    """Ratio signal/bruit des mentions.

    Signal = mentions avec un sentiment clair (positif ou négatif fort)
    Bruit = mentions neutres ou sans contenu utile
    """
    if not mentions:
        return 50.0

    from backend.modules.scanner.sentiment import analyse_text_sentiment

    strong_signals = 0
    for m in mentions:
        sent = analyse_text_sentiment(m.get("text", ""))
        if abs(sent["polarity"]) > 0.3:
            strong_signals += 1

    ratio = strong_signals / len(mentions)

    if ratio > 0.6:
        return 85.0  # Haute conviction dans la communauté
    elif ratio > 0.4:
        return 70.0
    elif ratio > 0.2:
        return 55.0
    else:
        return 35.0  # Beaucoup de bruit, peu de signal


def compute_network_effect(symbol: str, mentions: list[dict],
                           asset_class: str) -> float:
    """Network Effect — Loi de Metcalfe (surtout pour crypto).

    La valeur d'un réseau croît proportionnellement au carré du nombre d'utilisateurs.
    Plus de mentions uniques = plus de participants = valeur réseau en hausse.
    """
    if asset_class != "CRYPTO":
        return 50.0  # Non applicable aux non-crypto

    if not mentions:
        return 30.0

    # Nombre de sources uniques (proxy participants)
    sources = set(m.get("source", "") for m in mentions)
    n_sources = len(sources)
    n_mentions = len(mentions)

    # Metcalfe simplifié : score basé sur log(n²)
    if n_mentions > 40:
        return 85.0
    elif n_mentions > 20:
        return 70.0
    elif n_mentions > 10:
        return 55.0
    elif n_mentions > 3:
        return 40.0
    else:
        return 25.0


def compute_interest_momentum(mentions: list[dict]) -> float:
    """Tendance de l'intérêt — les mentions augmentent-elles ?

    Proxy pour Google Trends via le volume de mentions récentes vs anciennes.
    """
    if len(mentions) < 4:
        return 50.0

    from datetime import datetime, timedelta

    now = datetime.utcnow()
    recent_cutoff = now - timedelta(days=3)

    recent = 0
    older = 0
    for m in mentions:
        date_str = m.get("date", "")
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
            if date >= recent_cutoff:
                recent += 1
            else:
                older += 1
        except (ValueError, TypeError):
            older += 1

    if older == 0:
        return 65.0 if recent > 0 else 50.0

    ratio = recent / older

    if ratio > 3.0:
        return 90.0  # Intérêt en forte hausse
    elif ratio > 1.5:
        return 72.0
    elif ratio > 0.8:
        return 55.0
    elif ratio > 0.3:
        return 38.0
    else:
        return 20.0  # Intérêt en chute


def compute_sgi_score(mentions: list[dict], symbol: str,
                       asset_class: str) -> dict:
    """Score Topologie Sociale (SGI) composite.

    Combine :
    - Sentiment volume + polarité (30%)
    - Signal/bruit (25%)
    - Network Effect (20%)
    - Momentum d'intérêt (25%)
    """
    sentiment = compute_sentiment_score(mentions)
    signal_noise = compute_signal_to_noise(mentions)
    network = compute_network_effect(symbol, mentions, asset_class)
    interest = compute_interest_momentum(mentions)

    score = (
        sentiment["score"] * 0.30 +
        signal_noise * 0.25 +
        network * 0.20 +
        interest * 0.25
    )

    return {
        "score": round(min(100, max(0, score)), 2),
        "sentiment": sentiment,
        "signal_to_noise": round(signal_noise, 1),
        "network_effect": round(network, 1),
        "interest_momentum": round(interest, 1),
    }
