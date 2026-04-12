"""Détection des catalyseurs — événements qui bougent les marchés

1. Earnings dates — dates de résultats trimestriels
2. Événements macro — FOMC, CPI, NFP, GDP
3. Ex-dividend dates
4. Proximité d'événement → ajustement du signal

Quand un événement est proche (< 3 jours) :
- Réduire la conviction (incertitude)
- Augmenter la shelf life (attendre après l'événement)
- Ajuster le sizing (réduire la taille)
"""

import logging
from datetime import datetime, timedelta, date

logger = logging.getLogger("tradepilot.catalysts")

# Cache
_earnings_cache: dict[str, dict] = {}
_cache_time: dict[str, float] = {}
CACHE_TTL = 3600 * 12  # 12h


# Calendrier macro fixe (dates importantes récurrentes)
MACRO_EVENTS_MONTHLY = {
    # Jour approximatif du mois pour chaque événement récurrent
    "FOMC": [28, 29, 30],  # Fin de mois ~8 fois par an
    "CPI": [10, 11, 12, 13],  # Mi-mois
    "NFP": [1, 2, 3, 4, 5],  # Premier vendredi du mois
}


def get_earnings_date(symbol: str) -> dict | None:
    """Récupère la prochaine date de résultats via Yahoo Finance."""
    import time
    now = time.time()

    if symbol in _earnings_cache and now - _cache_time.get(symbol, 0) < CACHE_TTL:
        return _earnings_cache[symbol]

    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        cal = ticker.calendar
        if cal is not None and not cal.empty:
            # Chercher la prochaine date de résultats
            if "Earnings Date" in cal.index:
                dates = cal.loc["Earnings Date"]
                if len(dates) > 0:
                    next_date = dates.iloc[0]
                    if hasattr(next_date, 'date'):
                        next_date = next_date.date()
                    result = {
                        "symbol": symbol,
                        "earnings_date": str(next_date),
                        "days_until": (next_date - date.today()).days if isinstance(next_date, date) else None,
                    }
                    _earnings_cache[symbol] = result
                    _cache_time[symbol] = now
                    return result
    except Exception:
        pass

    # Fallback : essayer via .info
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        # Pas de date d'earnings dans info standard
    except Exception:
        pass

    return None


def get_upcoming_macro_events(days_ahead: int = 7) -> list[dict]:
    """Liste les événements macro dans les N prochains jours."""
    today = date.today()
    events = []

    for i in range(days_ahead):
        check_date = today + timedelta(days=i)
        day_of_month = check_date.day
        weekday = check_date.weekday()  # 0=lundi

        # FOMC (environ 8 fois par an, fin de mois)
        if day_of_month in MACRO_EVENTS_MONTHLY["FOMC"]:
            if check_date.month in [1, 3, 5, 6, 7, 9, 11, 12]:
                events.append({
                    "event": "FOMC Decision",
                    "date": str(check_date),
                    "days_until": i,
                    "impact": "HIGH",
                    "description": "Décision de taux de la Fed — peut bouger tout le marché",
                })

        # CPI (chaque mois, vers le 10-13)
        if day_of_month in MACRO_EVENTS_MONTHLY["CPI"]:
            events.append({
                "event": "CPI Release",
                "date": str(check_date),
                "days_until": i,
                "impact": "HIGH",
                "description": "Publication de l'inflation — impact sur les taux et les actions",
            })

        # NFP (premier vendredi du mois)
        if day_of_month <= 7 and weekday == 4:  # Vendredi
            events.append({
                "event": "Non-Farm Payrolls",
                "date": str(check_date),
                "days_until": i,
                "impact": "HIGH",
                "description": "Emploi US — indicateur clé de l'économie",
            })

    return events


def compute_catalyst_adjustment(symbol: str) -> dict:
    """Calcule l'ajustement de signal basé sur les catalyseurs proches.

    Retourne :
    - conviction_modifier : multiplicateur (0.5 à 1.0)
    - sizing_modifier : multiplicateur (0.5 à 1.0)
    - reason : explication
    """
    events = []
    modifiers = {"conviction": 1.0, "sizing": 1.0}
    reasons = []

    # 1. Earnings
    earnings = get_earnings_date(symbol)
    if earnings and earnings.get("days_until") is not None:
        days = earnings["days_until"]
        if 0 <= days <= 2:
            modifiers["conviction"] *= 0.5
            modifiers["sizing"] *= 0.5
            reasons.append(f"Résultats dans {days}j — forte incertitude")
            events.append({**earnings, "type": "earnings", "impact": "CRITICAL"})
        elif 0 <= days <= 5:
            modifiers["conviction"] *= 0.7
            modifiers["sizing"] *= 0.7
            reasons.append(f"Résultats dans {days}j — prudence")
            events.append({**earnings, "type": "earnings", "impact": "HIGH"})
        elif 0 <= days <= 10:
            modifiers["conviction"] *= 0.9
            reasons.append(f"Résultats dans {days}j — attention")
            events.append({**earnings, "type": "earnings", "impact": "MEDIUM"})

    # 2. Macro events
    macro = get_upcoming_macro_events(5)
    for event in macro:
        if event["days_until"] <= 1:
            modifiers["conviction"] *= 0.7
            modifiers["sizing"] *= 0.8
            reasons.append(f"{event['event']} demain — volatilité attendue")
        elif event["days_until"] <= 3:
            modifiers["conviction"] *= 0.85
            reasons.append(f"{event['event']} dans {event['days_until']}j")
    events.extend(macro)

    return {
        "conviction_modifier": round(modifiers["conviction"], 2),
        "sizing_modifier": round(modifiers["sizing"], 2),
        "events": events,
        "reasons": reasons,
        "has_catalyst": len(reasons) > 0,
    }
