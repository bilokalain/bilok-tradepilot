"""Portfolio Balancer — calcule la répartition LONG/SHORT optimale.

Objectifs :
1. Réduire la volatilité en ajustant l'exposition nette
2. Limiter le levier à un niveau raisonnable (1.5x max)
3. Équilibrer par secteur (pas de concentration >30%)
4. Prioriser les GO SHORT si le portefeuille est trop LONG (et vice-versa)

Utilisation : évaluer le risque actuel + proposer des rotations.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("tradepilot.balancer")


# ─────────────────────── CIBLES ───────────────────────

TARGET_NET_EXPOSURE_PCT = 50        # Net = LONG - SHORT, cible 40-60% de l'equity
TARGET_MAX_GROSS_PCT = 150          # Gross = LONG + SHORT, max 150% de l'equity
TARGET_MAX_SECTOR_PCT = 30          # Aucun secteur > 30% du gross
TARGET_MIN_SHORT_RATIO = 0.25       # Min 25% de SHORT dans la gross (hedge)


# ─────────────────────── ANALYSE ───────────────────────

def analyze_portfolio() -> dict:
    """Analyse le portefeuille Alpaca actuel : expositions, déséquilibres."""
    from backend.modules.execution.broker_alpaca import alpaca_broker
    from alpaca.trading.client import TradingClient
    from backend.config.settings import settings

    if not alpaca_broker.is_configured:
        return {"error": "Alpaca non configuré"}

    client = TradingClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY, paper=True)
    account = client.get_account()
    positions = client.get_all_positions()

    equity = float(account.equity)
    cash = float(account.cash)

    def _is_long(pos):
        s = str(pos.side).lower()
        return "long" in s

    long_positions = [p for p in positions if _is_long(p)]
    short_positions = [p for p in positions if not _is_long(p)]

    long_mv = sum(float(p.market_value) for p in long_positions)
    short_mv = sum(abs(float(p.market_value)) for p in short_positions)
    gross_mv = long_mv + short_mv
    net_mv = long_mv - short_mv

    # Ratios
    gross_pct = (gross_mv / equity * 100) if equity > 0 else 0
    net_pct = (net_mv / equity * 100) if equity > 0 else 0
    short_ratio = (short_mv / gross_mv) if gross_mv > 0 else 0

    # Par secteur (via cache scanner)
    scanner = {}
    try:
        with open("data/scanner_cache.json") as f:
            scanner = {r["symbol"]: r for r in json.load(f).get("results", [])}
    except Exception:
        pass

    from collections import defaultdict
    sector_exposure = defaultdict(lambda: {"long": 0, "short": 0})
    for p in positions:
        sym = p.symbol
        side = "long" if _is_long(p) else "short"
        mv = abs(float(p.market_value))
        info = scanner.get(sym, {}).get("info", {}) or {}
        sector = info.get("sector") or "Unknown"
        sector_exposure[sector][side] += mv

    sector_breakdown = []
    for s, vals in sorted(sector_exposure.items(), key=lambda x: -(x[1]["long"] + x[1]["short"])):
        total = vals["long"] + vals["short"]
        pct = (total / gross_mv * 100) if gross_mv > 0 else 0
        sector_breakdown.append({
            "sector": s, "long": round(vals["long"], 0), "short": round(vals["short"], 0),
            "total": round(total, 0), "pct": round(pct, 2),
        })

    # Diagnostic
    issues = []
    if net_pct > 80:
        issues.append({"level": "CRITIQUE", "msg": f"Net exposure trop haut ({net_pct:.0f}%) → très sensible au marché"})
    elif net_pct > 65:
        issues.append({"level": "WARN", "msg": f"Net exposure élevé ({net_pct:.0f}%) → réduire ou hedger"})

    if gross_pct > 180:
        issues.append({"level": "CRITIQUE", "msg": f"Levier trop fort ({gross_pct:.0f}%) → risque d'appel de marge"})
    elif gross_pct > 150:
        issues.append({"level": "WARN", "msg": f"Levier élevé ({gross_pct:.0f}%)"})

    if short_ratio < 0.15:
        issues.append({"level": "WARN", "msg": f"Trop peu de SHORT ({short_ratio*100:.0f}%) → peu de hedge"})

    for s in sector_breakdown[:3]:
        if s["pct"] > 35:
            issues.append({"level": "WARN", "msg": f"Concentration {s['sector']} ({s['pct']:.0f}%) > 30%"})

    return {
        "equity": round(equity, 2),
        "cash": round(cash, 2),
        "long_mv": round(long_mv, 2),
        "short_mv": round(short_mv, 2),
        "gross_mv": round(gross_mv, 2),
        "net_mv": round(net_mv, 2),
        "gross_pct": round(gross_pct, 2),
        "net_pct": round(net_pct, 2),
        "short_ratio": round(short_ratio, 3),
        "n_long": len(long_positions),
        "n_short": len(short_positions),
        "sectors": sector_breakdown[:10],
        "issues": issues,
    }


# ─────────────────────── RECOMMANDATIONS ───────────────────────

def recommend_rebalance() -> dict:
    """Retourne un plan d'action pour rééquilibrer le portefeuille.

    Se base sur les GO du jour pour proposer des ajouts SHORT si trop LONG,
    ou LONG si trop SHORT.
    """
    analysis = analyze_portfolio()
    if "error" in analysis:
        return analysis

    equity = analysis["equity"]
    long_mv = analysis["long_mv"]
    short_mv = analysis["short_mv"]
    gross_mv = analysis["gross_mv"]
    net_mv = analysis["net_mv"]

    # Cibles absolues
    target_gross = equity * TARGET_MAX_GROSS_PCT / 100
    target_net = equity * TARGET_NET_EXPOSURE_PCT / 100

    # Calcul des ajustements nécessaires
    # Net = L - S, on veut net = target_net
    # Gross = L + S, on veut gross <= target_gross
    # → L = (target_net + target_gross) / 2, S = (target_gross - target_net) / 2

    target_long = (target_net + target_gross) / 2
    target_short = (target_gross - target_net) / 2

    delta_long = target_long - long_mv        # positif = ouvrir LONG, négatif = fermer
    delta_short = target_short - short_mv     # positif = ouvrir SHORT, négatif = fermer

    # Charger les GO pour les recommandations concrètes
    go_signals = []
    try:
        with open("data/signals_cache.json") as f:
            raw = json.load(f)
            sigs = raw if isinstance(raw, list) else raw.get("signals", [])
            go_signals = [s for s in sigs if s.get("action") == "GO"]
    except Exception:
        pass

    go_longs = sorted([s for s in go_signals if s.get("direction") == "LONG"],
                     key=lambda x: -x.get("score_v2", x.get("score", 0)))
    go_shorts = sorted([s for s in go_signals if s.get("direction") == "SHORT"],
                      key=lambda x: -x.get("score_v2", x.get("score", 0)))

    # Positions actuelles pour connaître ce qui est déjà pris
    from backend.modules.execution.broker_alpaca import alpaca_broker
    current_syms = {p["symbol"] for p in alpaca_broker.get_positions()}

    recommendations = []

    if delta_long > 500:
        # Besoin de plus de LONG
        n_to_open = max(1, int(delta_long / 3000))  # ~$3000 par position
        available = [s for s in go_longs if s["symbol"] not in current_syms][:n_to_open]
        if available:
            recommendations.append({
                "action": "OUVRIR LONG",
                "amount_usd": round(delta_long, 0),
                "targets": [{"sym": s["symbol"], "score": s.get("score_v2", s.get("score", 0))} for s in available],
            })
    elif delta_long < -500:
        # Besoin de fermer des LONG
        recommendations.append({
            "action": "FERMER LONG",
            "amount_usd": round(abs(delta_long), 0),
            "note": f"Réduire l'exposition LONG de ${abs(delta_long):,.0f}",
        })

    if delta_short > 500:
        n_to_open = max(1, int(delta_short / 3000))
        available = [s for s in go_shorts if s["symbol"] not in current_syms][:n_to_open]
        if available:
            recommendations.append({
                "action": "OUVRIR SHORT",
                "amount_usd": round(delta_short, 0),
                "targets": [{"sym": s["symbol"], "score": s.get("score_v2", s.get("score", 0))} for s in available],
            })
    elif delta_short < -500:
        recommendations.append({
            "action": "FERMER SHORT",
            "amount_usd": round(abs(delta_short), 0),
        })

    return {
        "current": analysis,
        "target": {
            "long_mv": round(target_long, 0),
            "short_mv": round(target_short, 0),
            "gross_mv": round(target_gross, 0),
            "net_mv": round(target_net, 0),
            "net_pct": TARGET_NET_EXPOSURE_PCT,
            "gross_pct": TARGET_MAX_GROSS_PCT,
        },
        "delta": {
            "long_mv": round(delta_long, 0),
            "short_mv": round(delta_short, 0),
        },
        "recommendations": recommendations,
        "summary": _build_summary(analysis, delta_long, delta_short, go_longs, go_shorts),
    }


def _build_summary(analysis: dict, delta_long: float, delta_short: float,
                    go_longs: list, go_shorts: list) -> str:
    """Construit un résumé texte lisible."""
    parts = []
    parts.append(f"📊 Portefeuille à {analysis['gross_pct']:.0f}% de levier (cible {TARGET_MAX_GROSS_PCT}%)")
    parts.append(f"Net exposure : {analysis['net_pct']:.0f}% (cible {TARGET_NET_EXPOSURE_PCT}%)")
    parts.append(f"Ratio SHORT : {analysis['short_ratio']*100:.0f}% du gross (min {TARGET_MIN_SHORT_RATIO*100:.0f}%)")

    if delta_long < -1000:
        parts.append(f"⚠️ Réduire LONG de ${abs(delta_long):,.0f}")
    if delta_short > 1000:
        parts.append(f"💡 Ajouter SHORT de ${delta_short:,.0f} — {len(go_shorts)} GO SHORT disponibles")

    return " | ".join(parts)
