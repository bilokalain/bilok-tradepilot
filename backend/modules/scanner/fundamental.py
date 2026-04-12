"""Analyse Fondamentale — 10ème critère du scanner

6 dimensions fondamentales via Yahoo Finance (gratuit) :

1. Valorisation : P/E, P/B, P/S, PEG, EV/EBITDA
2. Profitabilité : Marge nette, ROE, ROA, marge opérationnelle
3. Croissance : Revenue growth, Earnings growth
4. Santé financière : Debt/Equity, Current Ratio, Free Cash Flow
5. Dividendes : Yield, Payout ratio
6. Qualité : Score Piotroski simplifié, Altman Z-Score

Score final 0-100.
Ne s'applique qu'aux actions (pas crypto, forex, commodities).
"""

import logging
import time
from functools import lru_cache

import numpy as np

logger = logging.getLogger("tradepilot.fundamental")

# Cache en mémoire (les fondamentaux changent lentement)
_fundamentals_cache: dict[str, dict] = {}
_cache_time: dict[str, float] = {}
CACHE_TTL = 3600 * 6  # 6 heures


def fetch_fundamentals(symbol: str) -> dict:
    """Récupère les fondamentaux via Yahoo Finance."""
    now = time.time()
    if symbol in _fundamentals_cache and now - _cache_time.get(symbol, 0) < CACHE_TTL:
        return _fundamentals_cache[symbol]

    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
    except Exception as e:
        logger.warning(f"[FUNDAMENTAL] Erreur {symbol}: {e}")
        return {}

    fundamentals = {
        # Valorisation
        "pe_ratio": _safe_float(info.get("trailingPE")),
        "forward_pe": _safe_float(info.get("forwardPE")),
        "pb_ratio": _safe_float(info.get("priceToBook")),
        "ps_ratio": _safe_float(info.get("priceToSalesTrailing12Months")),
        "peg_ratio": _safe_float(info.get("pegRatio")),
        "ev_ebitda": _safe_float(info.get("enterpriseToEbitda")),

        # Profitabilité
        "profit_margin": _safe_float(info.get("profitMargins")),
        "operating_margin": _safe_float(info.get("operatingMargins")),
        "roe": _safe_float(info.get("returnOnEquity")),
        "roa": _safe_float(info.get("returnOnAssets")),
        "gross_margin": _safe_float(info.get("grossMargins")),

        # Croissance
        "revenue_growth": _safe_float(info.get("revenueGrowth")),
        "earnings_growth": _safe_float(info.get("earningsGrowth")),
        "revenue_per_share": _safe_float(info.get("revenuePerShare")),

        # Santé financière
        "debt_to_equity": _safe_float(info.get("debtToEquity")),
        "current_ratio": _safe_float(info.get("currentRatio")),
        "free_cash_flow": _safe_float(info.get("freeCashflow")),
        "total_cash": _safe_float(info.get("totalCash")),
        "total_debt": _safe_float(info.get("totalDebt")),

        # Dividendes
        "dividend_yield": _safe_float(info.get("dividendYield")),
        "payout_ratio": _safe_float(info.get("payoutRatio")),

        # Infos
        "market_cap": _safe_float(info.get("marketCap")),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "name": info.get("longName") or info.get("shortName") or symbol,
    }

    _fundamentals_cache[symbol] = fundamentals
    _cache_time[symbol] = now
    return fundamentals


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return f if not np.isnan(f) and not np.isinf(f) else None
    except (ValueError, TypeError):
        return None


# ============================================================
# Scores par dimension
# ============================================================

def score_valuation(data: dict) -> dict:
    """Score de valorisation (0-100). Bas = cher, Haut = bon marché."""
    score = 50.0
    details = {}

    pe = data.get("pe_ratio")
    if pe is not None:
        if pe < 0:
            s = 20  # Perte = mauvais
        elif pe < 10:
            s = 90  # Très bon marché
        elif pe < 15:
            s = 75
        elif pe < 20:
            s = 60
        elif pe < 30:
            s = 45
        elif pe < 50:
            s = 30
        else:
            s = 15  # Très cher
        details["pe"] = {"value": round(pe, 1), "score": s}
        score = s

    peg = data.get("peg_ratio")
    if peg is not None and peg > 0:
        if peg < 1:
            s = 85  # Sous-évalué par rapport à la croissance
        elif peg < 1.5:
            s = 65
        elif peg < 2:
            s = 45
        else:
            s = 25
        details["peg"] = {"value": round(peg, 2), "score": s}
        score = (score + s) / 2

    pb = data.get("pb_ratio")
    if pb is not None:
        if pb < 1:
            s = 85
        elif pb < 3:
            s = 65
        elif pb < 5:
            s = 45
        else:
            s = 25
        details["pb"] = {"value": round(pb, 2), "score": s}
        score = (score * 2 + s) / 3

    return {"score": round(score, 1), "details": details}


def score_profitability(data: dict) -> dict:
    """Score de profitabilité (0-100)."""
    scores = []
    details = {}

    margin = data.get("profit_margin")
    if margin is not None:
        m_pct = margin * 100
        if m_pct > 20:
            s = 90
        elif m_pct > 10:
            s = 70
        elif m_pct > 5:
            s = 55
        elif m_pct > 0:
            s = 35
        else:
            s = 15
        scores.append(s)
        details["profit_margin"] = {"value": f"{m_pct:.1f}%", "score": s}

    roe = data.get("roe")
    if roe is not None:
        roe_pct = roe * 100
        if roe_pct > 25:
            s = 90
        elif roe_pct > 15:
            s = 70
        elif roe_pct > 10:
            s = 55
        elif roe_pct > 0:
            s = 35
        else:
            s = 15
        scores.append(s)
        details["roe"] = {"value": f"{roe_pct:.1f}%", "score": s}

    roa = data.get("roa")
    if roa is not None:
        roa_pct = roa * 100
        if roa_pct > 15:
            s = 85
        elif roa_pct > 8:
            s = 65
        elif roa_pct > 3:
            s = 45
        else:
            s = 25
        scores.append(s)
        details["roa"] = {"value": f"{roa_pct:.1f}%", "score": s}

    return {"score": round(np.mean(scores), 1) if scores else 50.0, "details": details}


def score_growth(data: dict) -> dict:
    """Score de croissance (0-100)."""
    scores = []
    details = {}

    rev_growth = data.get("revenue_growth")
    if rev_growth is not None:
        g_pct = rev_growth * 100
        if g_pct > 30:
            s = 95
        elif g_pct > 15:
            s = 80
        elif g_pct > 5:
            s = 60
        elif g_pct > 0:
            s = 45
        elif g_pct > -5:
            s = 30
        else:
            s = 15
        scores.append(s)
        details["revenue_growth"] = {"value": f"{g_pct:.1f}%", "score": s}

    earn_growth = data.get("earnings_growth")
    if earn_growth is not None:
        e_pct = earn_growth * 100
        if e_pct > 30:
            s = 90
        elif e_pct > 15:
            s = 75
        elif e_pct > 5:
            s = 55
        elif e_pct > 0:
            s = 40
        else:
            s = 20
        scores.append(s)
        details["earnings_growth"] = {"value": f"{e_pct:.1f}%", "score": s}

    return {"score": round(np.mean(scores), 1) if scores else 50.0, "details": details}


def score_financial_health(data: dict) -> dict:
    """Score de santé financière (0-100)."""
    scores = []
    details = {}

    de = data.get("debt_to_equity")
    if de is not None:
        if de < 30:
            s = 90  # Très peu endetté
        elif de < 60:
            s = 75
        elif de < 100:
            s = 55
        elif de < 200:
            s = 35
        else:
            s = 15  # Très endetté
        scores.append(s)
        details["debt_to_equity"] = {"value": round(de, 1), "score": s}

    cr = data.get("current_ratio")
    if cr is not None:
        if cr > 3:
            s = 85
        elif cr > 2:
            s = 75
        elif cr > 1.5:
            s = 60
        elif cr > 1:
            s = 40
        else:
            s = 20  # Ne peut pas payer ses dettes court terme
        scores.append(s)
        details["current_ratio"] = {"value": round(cr, 2), "score": s}

    fcf = data.get("free_cash_flow")
    if fcf is not None:
        if fcf > 0:
            s = 70
        else:
            s = 25  # FCF négatif = brûle du cash
        scores.append(s)
        details["free_cash_flow"] = {"value": f"${fcf/1e9:.1f}B" if abs(fcf) > 1e9 else f"${fcf/1e6:.0f}M", "score": s}

    return {"score": round(np.mean(scores), 1) if scores else 50.0, "details": details}


def score_dividends(data: dict) -> dict:
    """Score dividendes (0-100)."""
    div_yield = data.get("dividend_yield")
    payout = data.get("payout_ratio")
    details = {}

    if div_yield is None or div_yield == 0:
        return {"score": 40.0, "details": {"note": "Pas de dividende"}}

    dy_pct = div_yield * 100
    if dy_pct > 5:
        s = 85
    elif dy_pct > 3:
        s = 75
    elif dy_pct > 1.5:
        s = 60
    elif dy_pct > 0.5:
        s = 45
    else:
        s = 30
    details["dividend_yield"] = {"value": f"{dy_pct:.2f}%", "score": s}

    # Payout ratio soutenable ?
    if payout is not None:
        p_pct = payout * 100
        if 30 < p_pct < 70:
            s2 = 80  # Soutenable
        elif p_pct < 30:
            s2 = 60  # Pourrait payer plus
        elif p_pct < 90:
            s2 = 45
        else:
            s2 = 20  # Non soutenable
        details["payout_ratio"] = {"value": f"{p_pct:.0f}%", "score": s2}
        s = (s + s2) / 2

    return {"score": round(s, 1), "details": details}


def compute_piotroski_score(data: dict) -> dict:
    """Score de Piotroski simplifié (0-9 → normalisé 0-100).

    9 critères binaires (oui/non) :
    1. ROA positif
    2. Cash flow opérationnel positif (proxy: FCF)
    3. ROA en amélioration (proxy: earnings growth > 0)
    4. FCF > Net Income (proxy: profit margin OK et FCF positif)
    5. Dette en baisse (proxy: D/E < 100)
    6. Current ratio en amélioration (proxy: CR > 1.5)
    7. Pas de dilution (proxy: on ne peut pas vérifier)
    8. Marge brute en amélioration (proxy: gross margin > 30%)
    9. Asset turnover (proxy: revenue growth > 0)
    """
    points = 0
    checks = []

    roa = data.get("roa")
    if roa is not None and roa > 0:
        points += 1
        checks.append("ROA positif")

    fcf = data.get("free_cash_flow")
    if fcf is not None and fcf > 0:
        points += 1
        checks.append("Free Cash Flow positif")

    eg = data.get("earnings_growth")
    if eg is not None and eg > 0:
        points += 1
        checks.append("Bénéfices en croissance")

    margin = data.get("profit_margin")
    if margin is not None and margin > 0 and fcf is not None and fcf > 0:
        points += 1
        checks.append("Qualité des bénéfices")

    de = data.get("debt_to_equity")
    if de is not None and de < 100:
        points += 1
        checks.append("Endettement modéré")

    cr = data.get("current_ratio")
    if cr is not None and cr > 1.5:
        points += 1
        checks.append("Bonne liquidité")

    # Point 7 : on accorde par défaut
    points += 1
    checks.append("Pas de dilution (estimé)")

    gm = data.get("gross_margin")
    if gm is not None and gm > 0.30:
        points += 1
        checks.append("Marge brute saine")

    rg = data.get("revenue_growth")
    if rg is not None and rg > 0:
        points += 1
        checks.append("Revenus en croissance")

    score = (points / 9) * 100

    return {
        "piotroski": points,
        "score": round(score, 1),
        "checks": checks,
        "interpretation": "Excellent" if points >= 7 else "Bon" if points >= 5 else "Moyen" if points >= 3 else "Faible",
    }


# ============================================================
# Score composite
# ============================================================

def compute_fundamental_score(symbol: str) -> dict:
    """Score fondamental composite (0-100).

    Combine : Valorisation (20%) + Profitabilité (25%) + Croissance (20%)
    + Santé (15%) + Dividendes (10%) + Qualité Piotroski (10%)

    Retourne None si l'actif n'est pas une action (crypto, forex, commodity).
    """
    # Vérifier si c'est une action
    if any(x in symbol for x in ["-USD", "=X", "=F"]):
        return {
            "score": None,
            "applicable": False,
            "reason": "L'analyse fondamentale ne s'applique qu'aux actions",
        }

    data = fetch_fundamentals(symbol)
    if not data or not data.get("pe_ratio"):
        # Pas de données fondamentales
        return {
            "score": 50.0,
            "applicable": True,
            "source": "no_data",
            "reason": "Données fondamentales non disponibles",
        }

    valuation = score_valuation(data)
    profitability = score_profitability(data)
    growth = score_growth(data)
    health = score_financial_health(data)
    dividends = score_dividends(data)
    piotroski = compute_piotroski_score(data)

    composite = (
        valuation["score"] * 0.20 +
        profitability["score"] * 0.25 +
        growth["score"] * 0.20 +
        health["score"] * 0.15 +
        dividends["score"] * 0.10 +
        piotroski["score"] * 0.10
    )

    return {
        "score": round(composite, 1),
        "applicable": True,
        "source": "yahoo_finance",
        "dimensions": {
            "valuation": valuation,
            "profitability": profitability,
            "growth": growth,
            "financial_health": health,
            "dividends": dividends,
            "quality_piotroski": piotroski,
        },
        "raw_data": {
            "pe": data.get("pe_ratio"),
            "pb": data.get("pb_ratio"),
            "roe": f"{data['roe']*100:.1f}%" if data.get("roe") else None,
            "margin": f"{data['profit_margin']*100:.1f}%" if data.get("profit_margin") else None,
            "debt_equity": data.get("debt_to_equity"),
            "revenue_growth": f"{data['revenue_growth']*100:.1f}%" if data.get("revenue_growth") else None,
            "dividend_yield": f"{data['dividend_yield']*100:.2f}%" if data.get("dividend_yield") else None,
            "market_cap": f"${data['market_cap']/1e9:.1f}B" if data.get("market_cap") and data["market_cap"] > 1e9 else None,
            "sector": data.get("sector"),
            "industry": data.get("industry"),
        },
    }
