"""Scoring V2 — intègre TOUTES les sources d'information

Le scoring V1 utilisait 3 composantes (Bayésien + SQC + Conviction).
Le V2 intègre les 8 nouvelles sources pour un score beaucoup plus riche.

Architecture :
1. Score Scanner (10 critères) — qualité intrinsèque de l'actif
2. Conviction stratégie + backtest Sharpe — fiabilité historique
3. Régime Global modifier — contexte macro (RISK-ON/OFF)
4. Fondamentaux — santé financière réelle
5. Catalyseurs — timing (proximity d'événements)
6. Corrélation portefeuille — diversification
7. Sector Rotation — vent sectoriel favorable/défavorable
8. Lead-Lag signal — avantage temporel

Score final = 0 à 100
Action : GO (≥65) / WAIT (50-65) / NO_TRADE (<50)
"""

import logging
import numpy as np

logger = logging.getLogger("tradepilot.scorer_v2")


def compute_score_v2(
    scanner_score: float,
    strategy_conviction: float,
    backtest_sharpe: float,
    regime_global: dict | None = None,
    symbol: str = "",
    fundamental_score: float | None = None,
    catalyst_adjustment: dict | None = None,
    correlation_check: dict | None = None,
    sector_rotation_score: float | None = None,
    lead_lag_signal: dict | None = None,
    asset_class: str = "ACTION_US",
) -> dict:
    """Calcule le score V2 en intégrant toutes les sources.

    Retourne le score final + le détail de chaque composante.
    """
    components = {}

    # ============================================================
    # 1. Score Scanner (25%)
    # ============================================================
    scanner_component = min(100, max(0, scanner_score))
    components["scanner"] = {
        "score": round(scanner_component, 1),
        "weight": 0.25,
        "description": "Qualité intrinsèque (10 critères : AT, sentiment, génome, IPI, fondamentaux...)",
    }

    # ============================================================
    # 2. Conviction stratégie + Backtest (20%)
    # ============================================================
    # Conviction brute (0-100) + bonus si Sharpe backtest élevé
    sharpe_bonus = min(20, max(-20, backtest_sharpe * 15))
    conviction_component = min(100, max(0, strategy_conviction + sharpe_bonus))
    components["conviction"] = {
        "score": round(conviction_component, 1),
        "weight": 0.20,
        "strategy_conviction": round(strategy_conviction, 1),
        "backtest_sharpe": round(backtest_sharpe, 3),
        "sharpe_bonus": round(sharpe_bonus, 1),
        "description": "Fiabilité de la stratégie (conviction actuelle + performance historique)",
    }

    # ============================================================
    # 3. Régime Global (10%)
    # ============================================================
    if regime_global and regime_global.get("regime") != "UNKNOWN":
        modifiers = regime_global.get("asset_class_modifiers", {})
        modifier = modifiers.get(asset_class, 1.0)
        regime_score = 50 * modifier  # 50 = neutre, modifier l'ajuste

        regime_name = regime_global["regime"]
        regime_conf = regime_global.get("confidence", 0)

        # Pondérer par la confiance du régime
        regime_component = 50 + (regime_score - 50) * regime_conf

        components["regime_global"] = {
            "score": round(min(100, max(0, regime_component)), 1),
            "weight": 0.10,
            "regime": regime_name,
            "confidence": round(regime_conf, 2),
            "modifier": modifier,
            "description": f"Contexte macro : {regime_name} — modifier ×{modifier} pour {asset_class}",
        }
    else:
        components["regime_global"] = {
            "score": 50.0,
            "weight": 0.10,
            "regime": "UNKNOWN",
            "description": "Pas de régime global détecté",
        }

    # ============================================================
    # 4. Fondamentaux (10%)
    # ============================================================
    if fundamental_score is not None:
        fund_component = min(100, max(0, fundamental_score))
    else:
        fund_component = 50.0  # Neutre si pas applicable (crypto, forex)

    components["fundamentals"] = {
        "score": round(fund_component, 1),
        "weight": 0.10,
        "applicable": fundamental_score is not None,
        "description": "Santé financière (P/E, ROE, croissance, dette, Piotroski)" if fundamental_score else "Non applicable (crypto/forex/commodity)",
    }

    # ============================================================
    # 5. Catalyseurs (10%)
    # ============================================================
    if catalyst_adjustment and catalyst_adjustment.get("has_catalyst"):
        conv_mod = catalyst_adjustment.get("conviction_modifier", 1.0)
        # Plus le modifier est bas, plus le score est impacté
        catalyst_component = 50 * conv_mod + 50 * (1 - conv_mod) * 0.3
        reasons = catalyst_adjustment.get("reasons", [])

        components["catalysts"] = {
            "score": round(min(100, max(0, catalyst_component)), 1),
            "weight": 0.10,
            "conviction_modifier": conv_mod,
            "events": len(catalyst_adjustment.get("events", [])),
            "reasons": reasons[:3],
            "description": f"Attention : {reasons[0]}" if reasons else "Événement proche",
        }
    else:
        components["catalysts"] = {
            "score": 60.0,  # Pas de catalyseur = légèrement positif (pas d'incertitude)
            "weight": 0.10,
            "description": "Aucun événement majeur à proximité",
        }

    # ============================================================
    # 6. Corrélation Portefeuille (10%)
    # ============================================================
    if correlation_check:
        sizing_mod = correlation_check.get("sizing_modifier", 1.0)
        diversification = correlation_check.get("diversification_bonus", False)
        max_corr = correlation_check.get("max_correlation", 0)

        if diversification:
            corr_component = 75  # Bonus diversification
        elif sizing_mod < 0.5:
            corr_component = 20  # Très corrélé = mauvais
        elif sizing_mod < 0.8:
            corr_component = 40
        else:
            corr_component = 55

        components["correlation"] = {
            "score": round(corr_component, 1),
            "weight": 0.10,
            "max_correlation": round(max_corr, 3),
            "sizing_modifier": sizing_mod,
            "diversification_bonus": diversification,
            "description": f"Corrélation max : {max_corr:.2f} — sizing ×{sizing_mod}",
        }
    else:
        components["correlation"] = {
            "score": 55.0,
            "weight": 0.10,
            "description": "Pas de positions existantes à comparer",
        }

    # ============================================================
    # 7. Sector Rotation (8%)
    # ============================================================
    if sector_rotation_score is not None:
        sector_component = min(100, max(0, sector_rotation_score))
    else:
        sector_component = 50.0

    components["sector_rotation"] = {
        "score": round(sector_component, 1),
        "weight": 0.08,
        "description": "Vent sectoriel favorable/défavorable selon le cycle économique",
    }

    # ============================================================
    # 8. Lead-Lag Signal (7%)
    # ============================================================
    if lead_lag_signal and lead_lag_signal.get("signal"):
        ll_sig = lead_lag_signal["signal"]
        ll_conf = ll_sig.get("confidence", 0)
        ll_component = 50 + ll_conf * 0.4  # Max boost de 40 points

        components["lead_lag"] = {
            "score": round(min(100, max(0, ll_component)), 1),
            "weight": 0.07,
            "leader": ll_sig.get("leader"),
            "leader_move": ll_sig.get("leader_move"),
            "lag_days": ll_sig.get("lag_days"),
            "predicted_direction": ll_sig.get("predicted_direction"),
            "description": ll_sig.get("reason", "Signal lead-lag détecté"),
        }
    else:
        components["lead_lag"] = {
            "score": 50.0,
            "weight": 0.07,
            "description": "Pas de signal lead-lag actif",
        }

    # ============================================================
    # 9. Thèses Manuelles (boost/malus)
    # ============================================================
    try:
        from backend.modules.analyser.manual_thesis import compute_thesis_boost
        thesis_boost = compute_thesis_boost(symbol)
    except Exception:
        thesis_boost = {"score_modifier": 0, "sizing_modifier": 1.0, "reasons": [], "has_thesis": False}

    if thesis_boost.get("has_thesis"):
        components["manual_thesis"] = {
            "score": round(50 + thesis_boost["score_modifier"], 1),
            "weight": 0.0,  # Pas de poids — c'est un bonus/malus additif
            "modifier": thesis_boost["score_modifier"],
            "sizing_modifier": thesis_boost["sizing_modifier"],
            "reasons": thesis_boost["reasons"],
            "description": f"Thèse manuelle : {', '.join(thesis_boost['reasons'][:2])}",
        }

    # ============================================================
    # SCORE FINAL
    # ============================================================
    final_score = sum(
        comp["score"] * comp["weight"]
        for comp in components.values()
        if comp["weight"] > 0
    )

    # Ajouter le boost des thèses (additif, pas pondéré)
    if thesis_boost.get("has_thesis"):
        final_score += thesis_boost["score_modifier"]

    # Ajustement catalyseur (multiplicatif en plus du poids)
    if catalyst_adjustment and catalyst_adjustment.get("has_catalyst"):
        conv_mod = catalyst_adjustment.get("conviction_modifier", 1.0)
        if conv_mod < 0.7:
            # Événement imminent → réduire le score final
            final_score = final_score * (0.7 + conv_mod * 0.3)

    final_score = min(100, max(0, final_score))

    # Action
    if final_score >= 65:
        action = "GO"
    elif final_score >= 50:
        action = "WAIT"
    else:
        action = "NO_TRADE"

    # Sizing modifier (combiné)
    sizing_modifier = 1.0
    if catalyst_adjustment:
        sizing_modifier *= catalyst_adjustment.get("sizing_modifier", 1.0)
    if correlation_check:
        sizing_modifier *= correlation_check.get("sizing_modifier", 1.0)
    if regime_global:
        modifiers = regime_global.get("asset_class_modifiers", {})
        sizing_modifier *= modifiers.get(asset_class, 1.0)
    if thesis_boost.get("has_thesis"):
        sizing_modifier *= thesis_boost.get("sizing_modifier", 1.0)

    return {
        "score_v2": round(final_score, 1),
        "action": action,
        "sizing_modifier": round(sizing_modifier, 3),
        "components": components,
        "version": "v2",
        "num_sources": len(components),
    }
