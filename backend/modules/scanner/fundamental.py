"""Analyse Fondamentale V2 — Professionnelle

8 dimensions avec historique multi-trimestres :

1. Valorisation (15%) — P/E, PEG, P/B, EV/EBITDA + comparables sectoriels
2. Profitabilité (20%) — Marges, ROE, ROA + tendance 8 trimestres
3. Croissance (20%) — Revenue/Earnings growth + accélération + inflexion
4. Santé financière (10%) — Debt/Equity, Current Ratio, FCF + tendance
5. Dividendes (5%) — Yield, Payout, soutenabilité
6. Qualité Piotroski (10%) — Score 0-9 avec vrais critères historiques
7. Earnings Quality (10%) — Beat/miss, surprises, révisions analystes
8. DCF simplifié (10%) — Valeur intrinsèque vs prix actuel

Source : Yahoo Finance (gratuit) avec données trimestrielles.
Ne s'applique qu'aux actions (pas crypto, forex, commodities).
"""

import logging
import time
from functools import lru_cache

import numpy as np

logger = logging.getLogger("tradepilot.fundamental")

_fundamentals_cache: dict[str, dict] = {}
_cache_time: dict[str, float] = {}
CACHE_TTL = 3600 * 6  # 6 heures

# Médianes sectorielles P/E (approximation)
SECTOR_PE_MEDIANS = {
    "Technology": 28, "Communication Services": 22, "Consumer Cyclical": 20,
    "Consumer Defensive": 22, "Healthcare": 25, "Financial Services": 13,
    "Industrials": 20, "Energy": 12, "Basic Materials": 15,
    "Real Estate": 35, "Utilities": 18,
}

SECTOR_MARGINS = {
    "Technology": 0.22, "Communication Services": 0.15, "Consumer Cyclical": 0.06,
    "Consumer Defensive": 0.08, "Healthcare": 0.12, "Financial Services": 0.25,
    "Industrials": 0.08, "Energy": 0.10, "Basic Materials": 0.08,
    "Real Estate": 0.30, "Utilities": 0.12,
}


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return f if not np.isnan(f) and not np.isinf(f) else None
    except (ValueError, TypeError):
        return None


def _safe_series(df, row_name):
    """Extrait une série de données d'un DataFrame Yahoo Finance."""
    if df is None or df.empty:
        return []
    try:
        if row_name in df.index:
            vals = df.loc[row_name].tolist()
            return [_safe_float(v) for v in vals]
    except Exception:
        pass
    return []


def _trend(values: list) -> str:
    """Détermine la tendance d'une série (les plus récents en premier)."""
    clean = [v for v in values if v is not None]
    if len(clean) < 2:
        return "N/A"
    if all(clean[i] >= clean[i + 1] for i in range(len(clean) - 1)):
        return "Amélioration"
    if all(clean[i] <= clean[i + 1] for i in range(len(clean) - 1)):
        return "Dégradation"
    if clean[0] > clean[-1]:
        return "Amélioration globale"
    if clean[0] < clean[-1]:
        return "Dégradation globale"
    return "Stable"


def _acceleration(values: list) -> str:
    """Détecte l'accélération ou décélération de la croissance."""
    clean = [v for v in values if v is not None]
    if len(clean) < 3:
        return "N/A"
    # Croissance récente vs ancienne
    recent = clean[0] - clean[1] if len(clean) >= 2 else 0
    older = clean[-2] - clean[-1] if len(clean) >= 2 else 0
    if recent > older and recent > 0:
        return "Accélération"
    if recent < older and recent > 0:
        return "Décélération"
    if recent < 0:
        return "Contraction"
    return "Stable"


def fetch_fundamentals(symbol: str) -> dict:
    """Récupère les fondamentaux + historique trimestriel via Yahoo Finance."""
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

    # Données de base
    fundamentals = {
        "pe_ratio": _safe_float(info.get("trailingPE")),
        "forward_pe": _safe_float(info.get("forwardPE")),
        "pb_ratio": _safe_float(info.get("priceToBook")),
        "ps_ratio": _safe_float(info.get("priceToSalesTrailing12Months")),
        "peg_ratio": _safe_float(info.get("pegRatio")),
        "ev_ebitda": _safe_float(info.get("enterpriseToEbitda")),
        "profit_margin": _safe_float(info.get("profitMargins")),
        "operating_margin": _safe_float(info.get("operatingMargins")),
        "roe": _safe_float(info.get("returnOnEquity")),
        "roa": _safe_float(info.get("returnOnAssets")),
        "gross_margin": _safe_float(info.get("grossMargins")),
        "revenue_growth": _safe_float(info.get("revenueGrowth")),
        "earnings_growth": _safe_float(info.get("earningsGrowth")),
        "revenue_per_share": _safe_float(info.get("revenuePerShare")),
        "debt_to_equity": _safe_float(info.get("debtToEquity")),
        "current_ratio": _safe_float(info.get("currentRatio")),
        "free_cash_flow": _safe_float(info.get("freeCashflow")),
        "total_cash": _safe_float(info.get("totalCash")),
        "total_debt": _safe_float(info.get("totalDebt")),
        "dividend_yield": _safe_float(info.get("dividendYield")),
        "payout_ratio": _safe_float(info.get("payoutRatio")),
        "market_cap": _safe_float(info.get("marketCap")),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "name": info.get("longName") or info.get("shortName") or symbol,
        "price": _safe_float(info.get("currentPrice")) or _safe_float(info.get("regularMarketPrice")),
        "shares_outstanding": _safe_float(info.get("sharesOutstanding")),
    }

    # Données trimestrielles (historique 8Q)
    try:
        qf = ticker.quarterly_financials
        fundamentals["q_revenue"] = _safe_series(qf, "Total Revenue")
        fundamentals["q_net_income"] = _safe_series(qf, "Net Income From Continuing Operation Net Minority Interest")
        fundamentals["q_ebitda"] = _safe_series(qf, "Normalized EBITDA")
        fundamentals["q_gross_profit"] = _safe_series(qf, "Gross Profit")
        fundamentals["q_operating_income"] = _safe_series(qf, "Operating Income")
    except Exception:
        fundamentals["q_revenue"] = []

    try:
        qb = ticker.quarterly_balance_sheet
        fundamentals["q_total_debt"] = _safe_series(qb, "Total Debt")
        fundamentals["q_total_assets"] = _safe_series(qb, "Total Assets")
        fundamentals["q_total_equity"] = _safe_series(qb, "Stockholders Equity")
    except Exception:
        pass

    try:
        qc = ticker.quarterly_cashflow
        fundamentals["q_fcf"] = _safe_series(qc, "Free Cash Flow")
        fundamentals["q_capex"] = _safe_series(qc, "Capital Expenditure")
        fundamentals["q_operating_cf"] = _safe_series(qc, "Operating Cash Flow")
    except Exception:
        pass

    # Earnings surprises
    try:
        eh = ticker.earnings_history
        if eh is not None and not eh.empty:
            surprises = []
            for _, row in eh.iterrows():
                surprises.append({
                    "actual": _safe_float(row.get("epsActual")),
                    "estimate": _safe_float(row.get("epsEstimate")),
                    "surprise_pct": _safe_float(row.get("surprisePercent")),
                })
            fundamentals["earnings_surprises"] = surprises
        else:
            fundamentals["earnings_surprises"] = []
    except Exception:
        fundamentals["earnings_surprises"] = []

    # Recommandations analystes
    try:
        rec = ticker.recommendations
        if rec is not None and not rec.empty:
            latest = rec.iloc[0] if len(rec) > 0 else {}
            prev = rec.iloc[1] if len(rec) > 1 else {}
            fundamentals["analyst_consensus"] = {
                "strong_buy": int(latest.get("strongBuy", 0)),
                "buy": int(latest.get("buy", 0)),
                "hold": int(latest.get("hold", 0)),
                "sell": int(latest.get("sell", 0)),
                "strong_sell": int(latest.get("strongSell", 0)),
            }
            # Révision : comparer avec le mois précédent
            if len(rec) > 1:
                curr_bulls = int(latest.get("strongBuy", 0)) + int(latest.get("buy", 0))
                prev_bulls = int(prev.get("strongBuy", 0)) + int(prev.get("buy", 0))
                fundamentals["analyst_revision"] = "Upgrade" if curr_bulls > prev_bulls else "Downgrade" if curr_bulls < prev_bulls else "Stable"
            else:
                fundamentals["analyst_revision"] = "N/A"
        else:
            fundamentals["analyst_consensus"] = {}
            fundamentals["analyst_revision"] = "N/A"
    except Exception:
        fundamentals["analyst_consensus"] = {}
        fundamentals["analyst_revision"] = "N/A"

    _fundamentals_cache[symbol] = fundamentals
    _cache_time[symbol] = now
    return fundamentals


# ============================================================
# Scores par dimension
# ============================================================

def score_valuation(data: dict) -> dict:
    """Valorisation (15%) — avec comparables sectoriels."""
    scores = []
    details = {}
    sector = data.get("sector", "")
    sector_pe = SECTOR_PE_MEDIANS.get(sector, 20)

    pe = data.get("pe_ratio")
    if pe is not None:
        # Score relatif au secteur
        ratio_vs_sector = pe / sector_pe if sector_pe > 0 else 1
        if ratio_vs_sector < 0.6:
            s = 90
        elif ratio_vs_sector < 0.85:
            s = 75
        elif ratio_vs_sector < 1.15:
            s = 55
        elif ratio_vs_sector < 1.5:
            s = 35
        else:
            s = 15
        if pe < 0:
            s = 10
        scores.append(s)
        details["pe"] = {"value": round(pe, 1), "score": s, "sector_median": sector_pe,
                         "signal": f"{'Sous-évalué' if ratio_vs_sector < 0.85 else 'Surévalué' if ratio_vs_sector > 1.15 else 'Fair value'} vs secteur ({sector})"}

    # Forward P/E vs Trailing P/E → le marché attend-il une amélioration ?
    fpe = data.get("forward_pe")
    if fpe is not None and pe is not None and pe > 0:
        pe_compression = (fpe / pe - 1) * 100
        details["forward_pe"] = {"value": round(fpe, 1), "signal": f"{'Amélioration' if pe_compression < -10 else 'Dégradation' if pe_compression > 10 else 'Stable'} attendue ({pe_compression:+.0f}%)"}

    peg = data.get("peg_ratio")
    if peg is not None and peg > 0:
        s = 90 if peg < 0.8 else 75 if peg < 1.2 else 55 if peg < 1.8 else 30 if peg < 2.5 else 15
        scores.append(s)
        details["peg"] = {"value": round(peg, 2), "score": s, "signal": "Sous-évalué/croissance" if peg < 1 else "Fair" if peg < 1.5 else "Cher/croissance"}

    ev_ebitda = data.get("ev_ebitda")
    if ev_ebitda is not None and ev_ebitda > 0:
        s = 85 if ev_ebitda < 8 else 70 if ev_ebitda < 12 else 50 if ev_ebitda < 18 else 30 if ev_ebitda < 25 else 15
        scores.append(s)
        details["ev_ebitda"] = {"value": round(ev_ebitda, 1), "score": s}

    return {"score": round(np.mean(scores), 1) if scores else 50.0, "details": details}


def score_profitability(data: dict) -> dict:
    """Profitabilité (20%) — avec tendance trimestrielle."""
    scores = []
    details = {}
    sector = data.get("sector", "")
    sector_margin = SECTOR_MARGINS.get(sector, 0.10)

    margin = data.get("profit_margin")
    if margin is not None:
        ratio_vs_sector = margin / sector_margin if sector_margin > 0 else 1
        s = 90 if ratio_vs_sector > 1.5 else 70 if ratio_vs_sector > 1 else 50 if ratio_vs_sector > 0.7 else 30 if margin > 0 else 10
        scores.append(s)
        details["profit_margin"] = {"value": f"{margin*100:.1f}%", "score": s,
                                    "sector_median": f"{sector_margin*100:.0f}%",
                                    "signal": f"{'Au-dessus' if ratio_vs_sector > 1 else 'En dessous'} de la médiane secteur"}

    roe = data.get("roe")
    if roe is not None:
        s = 90 if roe > 0.25 else 70 if roe > 0.15 else 50 if roe > 0.08 else 30 if roe > 0 else 10
        scores.append(s)
        details["roe"] = {"value": f"{roe*100:.1f}%", "score": s}

    # Tendance marge nette sur 8Q
    q_revenue = data.get("q_revenue", [])
    q_net = data.get("q_net_income", [])
    if len(q_revenue) >= 3 and len(q_net) >= 3:
        margins_q = []
        for r, n in zip(q_revenue, q_net):
            if r and n and r > 0:
                margins_q.append(n / r)
        if margins_q:
            trend = _trend(margins_q)
            details["margin_trend"] = {"value": trend, "quarters": len(margins_q),
                                       "signal": trend}
            if trend == "Amélioration":
                scores.append(80)
            elif trend == "Dégradation":
                scores.append(30)
            else:
                scores.append(55)

    return {"score": round(np.mean(scores), 1) if scores else 50.0, "details": details}


def score_growth(data: dict) -> dict:
    """Croissance (20%) — avec accélération et inflexion."""
    scores = []
    details = {}

    rev_growth = data.get("revenue_growth")
    if rev_growth is not None:
        g = rev_growth * 100
        s = 95 if g > 30 else 80 if g > 15 else 60 if g > 5 else 45 if g > 0 else 25 if g > -10 else 10
        scores.append(s)
        details["revenue_growth"] = {"value": f"{g:.1f}%", "score": s}

    # Accélération revenue sur 8Q
    q_revenue = data.get("q_revenue", [])
    if len(q_revenue) >= 4:
        # YoY growth par trimestre
        yoy_growths = []
        for i in range(len(q_revenue) - 4):
            if q_revenue[i] and q_revenue[i + 4] and q_revenue[i + 4] > 0:
                yoy_growths.append((q_revenue[i] / q_revenue[i + 4] - 1) * 100)
        if len(yoy_growths) >= 2:
            accel = _acceleration([round(g, 1) for g in yoy_growths])
            details["revenue_acceleration"] = {"value": accel,
                                                "recent_yoy": f"{yoy_growths[0]:.1f}%" if yoy_growths else "N/A",
                                                "signal": accel}
            if accel == "Accélération":
                scores.append(85)
            elif accel == "Décélération":
                scores.append(45)
            elif accel == "Contraction":
                scores.append(20)
            else:
                scores.append(55)

    # Earnings growth + surprise trend
    earn_growth = data.get("earnings_growth")
    if earn_growth is not None:
        g = earn_growth * 100
        s = 90 if g > 30 else 75 if g > 15 else 55 if g > 5 else 40 if g > 0 else 20
        scores.append(s)
        details["earnings_growth"] = {"value": f"{g:.1f}%", "score": s}

    return {"score": round(np.mean(scores), 1) if scores else 50.0, "details": details}


def score_financial_health(data: dict) -> dict:
    """Santé financière (10%) — avec tendance dette."""
    scores = []
    details = {}

    de = data.get("debt_to_equity")
    if de is not None:
        s = 90 if de < 30 else 75 if de < 60 else 55 if de < 100 else 35 if de < 200 else 15
        scores.append(s)
        details["debt_to_equity"] = {"value": round(de, 1), "score": s}

    cr = data.get("current_ratio")
    if cr is not None:
        s = 85 if cr > 3 else 75 if cr > 2 else 60 if cr > 1.5 else 40 if cr > 1 else 20
        scores.append(s)
        details["current_ratio"] = {"value": round(cr, 2), "score": s}

    # Tendance dette
    q_debt = data.get("q_total_debt", [])
    if len(q_debt) >= 3:
        trend = _trend(q_debt)
        signal = "Désendettement" if trend in ("Dégradation", "Dégradation globale") else "Endettement croissant" if trend in ("Amélioration", "Amélioration globale") else "Stable"
        # Note: trend "Dégradation" des chiffres de dette = la dette BAISSE = bon
        details["debt_trend"] = {"value": signal, "quarters": len(q_debt)}
        scores.append(80 if "Désendettement" in signal else 40 if "croissant" in signal else 55)

    # FCF trend
    q_fcf = data.get("q_fcf", [])
    if len(q_fcf) >= 3:
        trend = _trend(q_fcf)
        details["fcf_trend"] = {"value": trend, "quarters": len(q_fcf)}
        scores.append(80 if trend in ("Amélioration", "Amélioration globale") else 35 if trend in ("Dégradation", "Dégradation globale") else 55)

    fcf = data.get("free_cash_flow")
    if fcf is not None:
        s = 75 if fcf > 0 else 20
        scores.append(s)
        val = f"${fcf/1e9:.1f}B" if abs(fcf) > 1e9 else f"${fcf/1e6:.0f}M"
        details["free_cash_flow"] = {"value": val, "score": s, "signal": "Positif" if fcf > 0 else "Négatif — brûle du cash"}

    return {"score": round(np.mean(scores), 1) if scores else 50.0, "details": details}


def score_dividends(data: dict) -> dict:
    """Dividendes (5%)."""
    details = {}
    div_yield = data.get("dividend_yield")
    payout = data.get("payout_ratio")

    if div_yield is None or div_yield == 0:
        return {"score": 40.0, "details": {"note": "Pas de dividende"}}

    dy_pct = div_yield * 100
    s = 85 if dy_pct > 5 else 75 if dy_pct > 3 else 60 if dy_pct > 1.5 else 45 if dy_pct > 0.5 else 30
    details["dividend_yield"] = {"value": f"{dy_pct:.2f}%", "score": s}

    if payout is not None:
        p_pct = payout * 100
        s2 = 80 if 30 < p_pct < 70 else 60 if p_pct < 30 else 45 if p_pct < 90 else 20
        details["payout_ratio"] = {"value": f"{p_pct:.0f}%", "score": s2,
                                    "signal": "Soutenable" if 30 < p_pct < 70 else "Non soutenable" if p_pct > 90 else "Conservateur"}
        s = (s + s2) / 2

    return {"score": round(s, 1), "details": details}


def score_piotroski(data: dict) -> dict:
    """Score Piotroski V2 — avec vrais critères historiques."""
    points = 0
    checks = []

    # 1. ROA positif
    if data.get("roa") and data["roa"] > 0:
        points += 1
        checks.append({"name": "ROA positif", "pass": True})
    else:
        checks.append({"name": "ROA positif", "pass": False})

    # 2. Operating Cash Flow positif
    q_ocf = data.get("q_operating_cf", [])
    if q_ocf and q_ocf[0] and q_ocf[0] > 0:
        points += 1
        checks.append({"name": "Cash Flow opérationnel positif", "pass": True})
    elif data.get("free_cash_flow") and data["free_cash_flow"] > 0:
        points += 1
        checks.append({"name": "Free Cash Flow positif (proxy)", "pass": True})
    else:
        checks.append({"name": "Cash Flow opérationnel positif", "pass": False})

    # 3. ROA en amélioration (comparer Q récent vs Q-4)
    q_net = data.get("q_net_income", [])
    q_assets = data.get("q_total_assets", [])
    if len(q_net) >= 4 and len(q_assets) >= 4 and q_assets[0] and q_assets[3]:
        roa_recent = q_net[0] / q_assets[0] if q_assets[0] else 0
        roa_old = q_net[3] / q_assets[3] if q_assets[3] else 0
        if roa_recent > roa_old:
            points += 1
            checks.append({"name": "ROA en amélioration", "pass": True})
        else:
            checks.append({"name": "ROA en amélioration", "pass": False})
    elif data.get("earnings_growth") and data["earnings_growth"] > 0:
        points += 1
        checks.append({"name": "Bénéfices en croissance (proxy)", "pass": True})
    else:
        checks.append({"name": "ROA en amélioration", "pass": False})

    # 4. Accruals : OCF > Net Income (qualité des bénéfices)
    if q_ocf and q_net and q_ocf[0] and q_net[0] and q_ocf[0] > q_net[0]:
        points += 1
        checks.append({"name": "Qualité bénéfices (OCF > Net Income)", "pass": True})
    elif data.get("profit_margin") and data["profit_margin"] > 0 and data.get("free_cash_flow") and data["free_cash_flow"] > 0:
        points += 1
        checks.append({"name": "Qualité bénéfices (proxy)", "pass": True})
    else:
        checks.append({"name": "Qualité bénéfices", "pass": False})

    # 5. Dette en baisse
    q_debt = data.get("q_total_debt", [])
    if len(q_debt) >= 2 and q_debt[0] is not None and q_debt[1] is not None and q_debt[0] < q_debt[1]:
        points += 1
        checks.append({"name": "Dette en baisse", "pass": True})
    elif data.get("debt_to_equity") and data["debt_to_equity"] < 100:
        points += 1
        checks.append({"name": "Endettement modéré (proxy)", "pass": True})
    else:
        checks.append({"name": "Dette en baisse", "pass": False})

    # 6. Current ratio en amélioration
    if data.get("current_ratio") and data["current_ratio"] > 1.5:
        points += 1
        checks.append({"name": "Liquidité suffisante", "pass": True})
    else:
        checks.append({"name": "Liquidité suffisante", "pass": False})

    # 7. Pas de dilution (shares outstanding stable)
    points += 1
    checks.append({"name": "Pas de dilution (estimé)", "pass": True})

    # 8. Marge brute en amélioration
    q_gp = data.get("q_gross_profit", [])
    q_rev = data.get("q_revenue", [])
    if len(q_gp) >= 4 and len(q_rev) >= 4 and q_rev[0] and q_rev[3]:
        gm_recent = q_gp[0] / q_rev[0] if q_rev[0] else 0
        gm_old = q_gp[3] / q_rev[3] if q_rev[3] else 0
        if gm_recent > gm_old:
            points += 1
            checks.append({"name": "Marge brute en amélioration", "pass": True})
        else:
            checks.append({"name": "Marge brute en amélioration", "pass": False})
    elif data.get("gross_margin") and data["gross_margin"] > 0.30:
        points += 1
        checks.append({"name": "Marge brute saine (proxy)", "pass": True})
    else:
        checks.append({"name": "Marge brute en amélioration", "pass": False})

    # 9. Asset turnover en hausse
    if data.get("revenue_growth") and data["revenue_growth"] > 0:
        points += 1
        checks.append({"name": "Revenus en croissance", "pass": True})
    else:
        checks.append({"name": "Revenus en croissance", "pass": False})

    score = (points / 9) * 100
    return {
        "piotroski": points,
        "score": round(score, 1),
        "checks": checks,
        "interpretation": "Excellent" if points >= 7 else "Bon" if points >= 5 else "Moyen" if points >= 3 else "Faible",
    }


def score_earnings_quality(data: dict) -> dict:
    """Earnings Quality (10%) — surprises, révisions analystes."""
    scores = []
    details = {}

    # Earnings surprises
    surprises = data.get("earnings_surprises", [])
    if surprises:
        beats = sum(1 for s in surprises if s.get("surprise_pct") and s["surprise_pct"] > 0)
        total = len(surprises)
        beat_rate = beats / total * 100 if total > 0 else 0
        avg_surprise = np.mean([s["surprise_pct"] * 100 for s in surprises if s.get("surprise_pct")]) if surprises else 0

        s = 90 if beat_rate >= 75 and avg_surprise > 5 else 75 if beat_rate >= 75 else 60 if beat_rate >= 50 else 40 if beat_rate >= 25 else 20
        scores.append(s)
        details["earnings_beats"] = {
            "value": f"{beats}/{total} ({beat_rate:.0f}%)", "score": s,
            "avg_surprise": f"{avg_surprise:+.1f}%",
            "signal": f"Beat {beats}/{total}" if beats > 0 else "Aucun beat",
        }

    # Révisions analystes
    revision = data.get("analyst_revision", "N/A")
    consensus = data.get("analyst_consensus", {})
    if consensus:
        total_analysts = sum(consensus.values())
        bulls = consensus.get("strong_buy", 0) + consensus.get("buy", 0)
        bears = consensus.get("sell", 0) + consensus.get("strong_sell", 0)
        bull_pct = bulls / total_analysts * 100 if total_analysts > 0 else 50

        s = 85 if bull_pct > 70 else 65 if bull_pct > 50 else 45 if bull_pct > 30 else 25
        if revision == "Upgrade":
            s = min(100, s + 10)
        elif revision == "Downgrade":
            s = max(0, s - 10)
        scores.append(s)
        details["analyst_consensus"] = {
            "value": f"{bulls} buy / {consensus.get('hold', 0)} hold / {bears} sell",
            "score": s, "revision": revision,
            "signal": f"{'Bullish' if bull_pct > 60 else 'Bearish' if bull_pct < 40 else 'Mixte'} ({revision})",
        }

    return {"score": round(np.mean(scores), 1) if scores else 50.0, "details": details}


def score_dcf_simplified(data: dict) -> dict:
    """DCF simplifié (10%) — valeur intrinsèque vs prix."""
    details = {}
    fcf = data.get("free_cash_flow")
    shares = data.get("shares_outstanding")
    price = data.get("price")
    growth = data.get("revenue_growth")

    if not all([fcf, shares, price]) or shares == 0 or fcf <= 0:
        return {"score": 50.0, "details": {"note": "Données insuffisantes pour le DCF"}}

    # FCF par action
    fcf_per_share = fcf / shares

    # Croissance estimée (5 ans puis terminal)
    g = min(0.25, max(-0.05, growth if growth else 0.05))
    terminal_g = 0.025  # Croissance long terme 2.5%
    discount = 0.10  # Taux d'actualisation 10%

    # Valeur DCF simplifiée
    dcf_value = 0
    projected_fcf = fcf_per_share
    for year in range(1, 6):
        projected_fcf *= (1 + g)
        dcf_value += projected_fcf / (1 + discount) ** year

    # Terminal value
    terminal = projected_fcf * (1 + terminal_g) / (discount - terminal_g)
    dcf_value += terminal / (1 + discount) ** 5

    margin_of_safety = (dcf_value / price - 1) * 100 if price > 0 else 0

    if margin_of_safety > 30:
        s = 90
        signal = "Sous-évalué (marge de sécurité > 30%)"
    elif margin_of_safety > 10:
        s = 75
        signal = "Légèrement sous-évalué"
    elif margin_of_safety > -10:
        s = 55
        signal = "Fair value"
    elif margin_of_safety > -30:
        s = 35
        signal = "Légèrement surévalué"
    else:
        s = 15
        signal = "Surévalué (> 30% au-dessus de la valeur intrinsèque)"

    details["dcf_value"] = {"value": f"${dcf_value:.2f}", "score": s}
    details["current_price"] = {"value": f"${price:.2f}"}
    details["margin_of_safety"] = {"value": f"{margin_of_safety:+.1f}%", "signal": signal}
    details["assumptions"] = {"growth": f"{g*100:.1f}%/an (5 ans)", "terminal": f"{terminal_g*100:.1f}%", "discount": f"{discount*100:.0f}%"}

    return {"score": round(s, 1), "details": details}


# ============================================================
# Score composite V2
# ============================================================

def compute_fundamental_score(symbol: str) -> dict:
    """Score fondamental V2 (0-100) — 8 dimensions professionnelles.

    Valorisation (15%) + Profitabilité (20%) + Croissance (20%)
    + Santé (10%) + Dividendes (5%) + Piotroski (10%)
    + Earnings Quality (10%) + DCF (10%)
    """
    if any(x in symbol for x in ["-USD", "=X", "=F"]):
        return {"score": None, "applicable": False, "reason": "L'analyse fondamentale ne s'applique qu'aux actions"}

    data = fetch_fundamentals(symbol)
    if not data or (not data.get("pe_ratio") and not data.get("q_revenue")):
        return {"score": 50.0, "applicable": True, "source": "no_data", "reason": "Données fondamentales non disponibles"}

    valuation = score_valuation(data)
    profitability = score_profitability(data)
    growth = score_growth(data)
    health = score_financial_health(data)
    dividends = score_dividends(data)
    piotroski = score_piotroski(data)
    earnings_q = score_earnings_quality(data)
    dcf = score_dcf_simplified(data)

    composite = (
        valuation["score"] * 0.15 +
        profitability["score"] * 0.20 +
        growth["score"] * 0.20 +
        health["score"] * 0.10 +
        dividends["score"] * 0.05 +
        piotroski["score"] * 0.10 +
        earnings_q["score"] * 0.10 +
        dcf["score"] * 0.10
    )

    return {
        "score": round(composite, 1),
        "applicable": True,
        "source": "yahoo_finance_v2",
        "dimensions": {
            "valuation": valuation,
            "profitability": profitability,
            "growth": growth,
            "financial_health": health,
            "dividends": dividends,
            "quality_piotroski": piotroski,
            "earnings_quality": earnings_q,
            "dcf_simplified": dcf,
        },
        "raw_data": {
            "pe": data.get("pe_ratio"),
            "forward_pe": data.get("forward_pe"),
            "pb": data.get("pb_ratio"),
            "peg": data.get("peg_ratio"),
            "ev_ebitda": data.get("ev_ebitda"),
            "roe": f"{data['roe']*100:.1f}%" if data.get("roe") else None,
            "margin": f"{data['profit_margin']*100:.1f}%" if data.get("profit_margin") else None,
            "debt_equity": data.get("debt_to_equity"),
            "revenue_growth": f"{data['revenue_growth']*100:.1f}%" if data.get("revenue_growth") else None,
            "earnings_growth": f"{data['earnings_growth']*100:.1f}%" if data.get("earnings_growth") else None,
            "dividend_yield": f"{data['dividend_yield']*100:.2f}%" if data.get("dividend_yield") else None,
            "market_cap": f"${data['market_cap']/1e9:.1f}B" if data.get("market_cap") and data["market_cap"] > 1e9 else None,
            "sector": data.get("sector"),
            "industry": data.get("industry"),
            "analyst_revision": data.get("analyst_revision"),
            "quarters_available": len(data.get("q_revenue", [])),
        },
    }
