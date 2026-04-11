"""Attribution P&L + Monte Carlo + Early Warning System

Attribution causale P&L — décompose la performance en 6 facteurs :
1. Scanner (qualité de la sélection d'actifs)
2. Timing (qualité du point d'entrée)
3. Sizing (taille de position vs optimal)
4. Sortie (qualité du point de sortie)
5. Régime (effet du régime de marché)
6. Friction (coûts de transaction, slippage)

Monte Carlo — simulation de 10 000 trajectoires futures
Early Warning System — 5 indicateurs, 4 niveaux d'alerte
"""

import numpy as np
import pandas as pd
from datetime import datetime


# ============================================================
# Attribution P&L
# ============================================================

def compute_pnl_attribution(trades: list[dict]) -> dict:
    """Décompose le P&L en 6 facteurs causaux.

    Chaque trade doit avoir :
    - pnl, entry_price, exit_price, direction
    - scanner_score, timing_score (optionnel)
    - optimal_size vs actual_size (optionnel)
    - slippage, commission
    """
    if not trades:
        return {
            "total_pnl": 0,
            "attribution": {
                "scanner": 0, "timing": 0, "sizing": 0,
                "exit": 0, "regime": 0, "friction": 0,
            },
            "attribution_pct": {
                "scanner": 0, "timing": 0, "sizing": 0,
                "exit": 0, "regime": 0, "friction": 0,
            },
        }

    total_pnl = sum(t.get("pnl", 0) for t in trades)
    n = len(trades)

    # Facteurs
    friction_total = sum(t.get("slippage_cost", 0) + t.get("commission", 0) for t in trades)

    # Scanner : corrélation entre scanner_score et P&L du trade
    scanner_scores = [t.get("scanner_score", 50) for t in trades]
    pnls = [t.get("pnl", 0) for t in trades]
    if np.std(scanner_scores) > 0 and np.std(pnls) > 0:
        scanner_corr = np.corrcoef(scanner_scores, pnls)[0, 1]
    else:
        scanner_corr = 0
    scanner_contrib = total_pnl * max(0, scanner_corr) * 0.3

    # Timing : ratio d'entrée favorable
    timing_total = 0
    for t in trades:
        entry = t.get("entry_price", 0)
        best_entry = t.get("best_possible_entry", entry)
        if entry > 0 and best_entry > 0:
            if t.get("direction") == "LONG":
                timing_total += (best_entry - entry) / entry * t.get("pnl", 0)
            else:
                timing_total += (entry - best_entry) / entry * t.get("pnl", 0)

    # Sizing : écart entre taille réelle et optimale
    sizing_total = 0
    for t in trades:
        actual = t.get("position_size", 0)
        optimal = t.get("optimal_size", actual)
        if optimal > 0:
            ratio = actual / optimal
            sizing_total += t.get("pnl", 0) * (1 - abs(1 - ratio)) * 0.2

    # Sortie et régime : résiduel réparti
    residual = total_pnl - scanner_contrib - timing_total - sizing_total - friction_total
    exit_contrib = residual * 0.5
    regime_contrib = residual * 0.5

    attribution = {
        "scanner": round(scanner_contrib, 2),
        "timing": round(timing_total, 2),
        "sizing": round(sizing_total, 2),
        "exit": round(exit_contrib, 2),
        "regime": round(regime_contrib, 2),
        "friction": round(-abs(friction_total), 2),
    }

    # Pourcentages
    abs_total = sum(abs(v) for v in attribution.values())
    attribution_pct = {}
    for k, v in attribution.items():
        attribution_pct[k] = round(v / abs_total * 100, 1) if abs_total > 0 else 0

    return {
        "total_pnl": round(total_pnl, 2),
        "num_trades": n,
        "attribution": attribution,
        "attribution_pct": attribution_pct,
    }


# ============================================================
# Monte Carlo
# ============================================================

def run_monte_carlo(equity_curve: list[float], n_simulations: int = 10_000,
                    horizon_days: int = 252) -> dict:
    """Simulation Monte Carlo de trajectoires futures.

    Retourne les percentiles 10/50/90 et P(ruine).
    """
    if len(equity_curve) < 20:
        return {
            "status": "insufficient_data",
            "message": f"Minimum 20 points requis ({len(equity_curve)} fournis)",
        }

    returns = pd.Series(equity_curve).pct_change().dropna()
    mu = float(returns.mean())
    sigma = float(returns.std())

    if sigma == 0:
        return {"status": "no_variance", "message": "Variance nulle — impossible de simuler"}

    initial_equity = equity_curve[-1]
    final_equities = []

    rng = np.random.default_rng(42)

    for _ in range(n_simulations):
        daily_returns = rng.normal(mu, sigma, horizon_days)
        trajectory = initial_equity * np.cumprod(1 + daily_returns)
        final_equities.append(trajectory[-1])

    final_equities = np.array(final_equities)

    p10 = float(np.percentile(final_equities, 10))
    p50 = float(np.percentile(final_equities, 50))
    p90 = float(np.percentile(final_equities, 90))

    # P(ruine) = probabilité de perdre > 50% du capital
    ruin_threshold = initial_equity * 0.5
    p_ruin = float(np.mean(final_equities < ruin_threshold))

    return {
        "status": "ok",
        "initial_equity": round(initial_equity, 2),
        "horizon_days": horizon_days,
        "n_simulations": n_simulations,
        "percentiles": {
            "p10": round(p10, 2),
            "p50": round(p50, 2),
            "p90": round(p90, 2),
        },
        "expected_return_pct": round((p50 / initial_equity - 1) * 100, 2),
        "p_ruin": round(p_ruin * 100, 2),
        "daily_mu": round(mu * 100, 4),
        "daily_sigma": round(sigma * 100, 4),
    }


# ============================================================
# Early Warning System
# ============================================================

EWS_THRESHOLDS = {
    "drawdown": {"attention": -5, "alerte": -10, "critique": -20},
    "losing_streak": {"attention": 3, "alerte": 5, "critique": 8},
    "win_rate_decline": {"attention": -10, "alerte": -20, "critique": -30},
    "volatility_spike": {"attention": 1.5, "alerte": 2.5, "critique": 4.0},
    "correlation_break": {"attention": 0.3, "alerte": 0.5, "critique": 0.7},
}


def compute_ews(equity_curve: list[float], trades: list[dict]) -> dict:
    """Early Warning System — 5 indicateurs, 4 niveaux.

    Niveaux : NORMAL → ATTENTION → ALERTE → CRITIQUE
    Action CRITIQUE = pause automatique du pipeline.
    """
    indicators = []

    # 1. Drawdown actuel
    if len(equity_curve) >= 5:
        peak = max(equity_curve)
        current = equity_curve[-1]
        dd_pct = (current / peak - 1) * 100 if peak > 0 else 0
        level = _classify(dd_pct, EWS_THRESHOLDS["drawdown"], invert=True)
        indicators.append({
            "name": "Drawdown",
            "value": round(dd_pct, 2),
            "unit": "%",
            "level": level,
        })
    else:
        indicators.append({"name": "Drawdown", "value": 0, "unit": "%", "level": "NORMAL"})

    # 2. Série de pertes
    if trades:
        streak = 0
        for t in reversed(trades):
            if t.get("pnl", 0) < 0:
                streak += 1
            else:
                break
        level = _classify(streak, EWS_THRESHOLDS["losing_streak"])
        indicators.append({
            "name": "Série de pertes",
            "value": streak,
            "unit": "trades",
            "level": level,
        })
    else:
        indicators.append({"name": "Série de pertes", "value": 0, "unit": "trades", "level": "NORMAL"})

    # 3. Déclin du win rate (20 derniers vs historique)
    if len(trades) >= 20:
        recent_wr = sum(1 for t in trades[-10:] if t.get("pnl", 0) > 0) / 10
        hist_wr = sum(1 for t in trades[:-10] if t.get("pnl", 0) > 0) / len(trades[:-10])
        decline = (recent_wr - hist_wr) * 100
        level = _classify(decline, EWS_THRESHOLDS["win_rate_decline"], invert=True)
        indicators.append({
            "name": "Déclin Win Rate",
            "value": round(decline, 1),
            "unit": "pp",
            "level": level,
        })
    else:
        indicators.append({"name": "Déclin Win Rate", "value": 0, "unit": "pp", "level": "NORMAL"})

    # 4. Spike de volatilité
    if len(equity_curve) >= 60:
        returns = pd.Series(equity_curve).pct_change().dropna()
        recent_vol = returns.iloc[-20:].std()
        hist_vol = returns.iloc[-60:-20].std()
        ratio = recent_vol / hist_vol if hist_vol > 0 else 1
        level = _classify(ratio, EWS_THRESHOLDS["volatility_spike"])
        indicators.append({
            "name": "Spike Volatilité",
            "value": round(ratio, 2),
            "unit": "x",
            "level": level,
        })
    else:
        indicators.append({"name": "Spike Volatilité", "value": 1.0, "unit": "x", "level": "NORMAL"})

    # 5. Placeholder corrélation (à connecter au Module 1)
    indicators.append({
        "name": "Rupture Corrélation",
        "value": 0,
        "unit": "delta",
        "level": "NORMAL",
    })

    # Niveau global
    levels_order = {"NORMAL": 0, "ATTENTION": 1, "ALERTE": 2, "CRITIQUE": 3}
    max_level = max(indicators, key=lambda x: levels_order.get(x["level"], 0))["level"]
    should_pause = max_level == "CRITIQUE"

    return {
        "overall_level": max_level,
        "should_pause": should_pause,
        "indicators": indicators,
    }


def _classify(value: float, thresholds: dict, invert: bool = False) -> str:
    """Classifie une valeur selon les seuils."""
    if invert:
        if value <= thresholds.get("critique", -999):
            return "CRITIQUE"
        elif value <= thresholds.get("alerte", -999):
            return "ALERTE"
        elif value <= thresholds.get("attention", -999):
            return "ATTENTION"
        return "NORMAL"
    else:
        if value >= thresholds.get("critique", 999):
            return "CRITIQUE"
        elif value >= thresholds.get("alerte", 999):
            return "ALERTE"
        elif value >= thresholds.get("attention", 999):
            return "ATTENTION"
        return "NORMAL"


# ============================================================
# Meta-Score
# ============================================================

def compute_meta_score(ews: dict, portfolio_regime: str,
                       win_rate: float, sharpe: float) -> dict:
    """Meta-Score santé du système (0-100).

    Pilote le niveau d'engagement du pipeline :
    > 80 : Pipeline full → exécution agressive
    60-80 : Pipeline normal
    40-60 : Pipeline prudent → réduire taille positions
    < 40 : Pipeline minimal → pause partielle
    """
    score = 50.0  # Base neutre

    # EWS impact (-30 à 0)
    ews_levels = {"NORMAL": 0, "ATTENTION": -10, "ALERTE": -20, "CRITIQUE": -30}
    score += ews_levels.get(ews.get("overall_level", "NORMAL"), 0)

    # Régime portefeuille (-15 à +15)
    regime_impact = {"ALPHA": 15, "BETA": 5, "STRESS": -15}
    score += regime_impact.get(portfolio_regime, 0)

    # Win rate (+/- 15)
    if win_rate > 0.55:
        score += 15
    elif win_rate > 0.45:
        score += 5
    elif win_rate < 0.35:
        score -= 15
    else:
        score -= 5

    # Sharpe (+/- 20)
    if sharpe > 1.5:
        score += 20
    elif sharpe > 1.0:
        score += 10
    elif sharpe > 0.5:
        score += 5
    elif sharpe < 0:
        score -= 15

    score = max(0, min(100, score))

    # Engagement level
    if score >= 80:
        engagement = "FULL"
        description = "Pipeline agressif — taille de position maximale"
    elif score >= 60:
        engagement = "NORMAL"
        description = "Pipeline normal — paramètres standard"
    elif score >= 40:
        engagement = "PRUDENT"
        description = "Pipeline prudent — taille de position réduite"
    else:
        engagement = "MINIMAL"
        description = "Pipeline minimal — pause partielle recommandée"

    return {
        "meta_score": round(score, 1),
        "engagement": engagement,
        "description": description,
    }


def generate_feedback(meta_score: dict, ews: dict,
                      attribution: dict) -> dict:
    """Génère le feedback loop pour le Module 1 (Scanner).

    Le feedback ajuste les poids du scanner en fonction de la performance.
    """
    adjustments = {}

    # Si le scanner contribue négativement au P&L
    scanner_pct = attribution.get("attribution_pct", {}).get("scanner", 0)
    if scanner_pct < -10:
        adjustments["scanner_weight_modifier"] = 0.8
        adjustments["scanner_note"] = "Réduire le poids du scanner — sélection sous-performante"
    elif scanner_pct > 20:
        adjustments["scanner_weight_modifier"] = 1.1
        adjustments["scanner_note"] = "Scanner performant — maintenir les poids"

    # Si timing est mauvais
    timing_pct = attribution.get("attribution_pct", {}).get("timing", 0)
    if timing_pct < -15:
        adjustments["shelf_life_modifier"] = 0.7
        adjustments["timing_note"] = "Réduire la shelf life — timing à améliorer"

    # Engagement du pipeline
    adjustments["pipeline_engagement"] = meta_score.get("engagement", "NORMAL")

    # EWS actions
    if ews.get("should_pause"):
        adjustments["action"] = "PAUSE_PIPELINE"
        adjustments["reason"] = "Early Warning System CRITIQUE — pause automatique"
    else:
        adjustments["action"] = "CONTINUE"

    return adjustments
