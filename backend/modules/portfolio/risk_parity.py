"""Risk Parity Dynamique — répartition égale du risque, pas du capital

Chaque position contribue le même montant de risque au portefeuille.
Positions plus volatiles → allocation plus petite.
Positions moins volatiles → allocation plus grande.

Stress Testing : scénarios historiques
- Mars 2020 (COVID crash : -34% S&P500 en 23 jours)
- 2022 (Bear market tech : -33% Nasdaq sur l'année)
- Black Swan crypto (Luna/FTX : -80% en quelques jours)
"""

import numpy as np
import pandas as pd


def compute_risk_contribution(weights: np.ndarray, cov_matrix: np.ndarray) -> np.ndarray:
    """Calcule la contribution au risque de chaque actif."""
    portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
    if portfolio_vol == 0:
        return np.zeros(len(weights))
    marginal_risk = cov_matrix @ weights
    risk_contrib = weights * marginal_risk / portfolio_vol
    return risk_contrib


def compute_risk_parity_weights(cov_matrix: np.ndarray, n_iterations: int = 1000,
                                 lr: float = 0.01) -> np.ndarray:
    """Calcule les poids Risk Parity par optimisation itérative.

    Objectif : chaque actif contribue 1/n du risque total.
    """
    n = cov_matrix.shape[0]
    if n == 0:
        return np.array([])
    if n == 1:
        return np.array([1.0])

    weights = np.ones(n) / n  # Départ : equal weight
    target_risk = 1.0 / n

    for _ in range(n_iterations):
        risk_contrib = compute_risk_contribution(weights, cov_matrix)
        total_risk = risk_contrib.sum()

        if total_risk == 0:
            break

        risk_pct = risk_contrib / total_risk

        # Gradient : ajuster les poids pour rapprocher chaque contribution de la cible
        gradient = risk_pct - target_risk
        weights -= lr * gradient
        weights = np.maximum(weights, 0.01)  # Pas de poids négatif
        weights /= weights.sum()  # Normaliser

    return weights


def compute_portfolio_volatility(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
    """Volatilité annualisée du portefeuille."""
    variance = weights @ cov_matrix @ weights
    return float(np.sqrt(variance * 252))


STRESS_SCENARIOS = {
    "covid_2020": {
        "name": "COVID Mars 2020",
        "description": "Crash de -34% en 23 jours de bourse",
        "shocks": {
            "ACTION_US": -0.34,
            "ACTION_EU": -0.38,
            "ETF": -0.30,
            "CRYPTO": -0.50,
            "FOREX": -0.05,
            "COMMODITY": -0.20,
        },
        "volatility_multiplier": 4.0,
    },
    "bear_2022": {
        "name": "Bear Market Tech 2022",
        "description": "Baisse prolongée -33% Nasdaq, hausse des taux",
        "shocks": {
            "ACTION_US": -0.25,
            "ACTION_EU": -0.18,
            "ETF": -0.20,
            "CRYPTO": -0.65,
            "FOREX": 0.10,
            "COMMODITY": 0.15,
        },
        "volatility_multiplier": 2.5,
    },
    "crypto_blackswan": {
        "name": "Black Swan Crypto (Luna/FTX)",
        "description": "Effondrement crypto -80%, contagion limitée",
        "shocks": {
            "ACTION_US": -0.05,
            "ACTION_EU": -0.03,
            "ETF": -0.04,
            "CRYPTO": -0.80,
            "FOREX": 0.0,
            "COMMODITY": -0.02,
        },
        "volatility_multiplier": 3.0,
    },
    "flash_crash": {
        "name": "Flash Crash",
        "description": "Chute brutale intraday -10% puis recovery partiel",
        "shocks": {
            "ACTION_US": -0.10,
            "ACTION_EU": -0.08,
            "ETF": -0.10,
            "CRYPTO": -0.15,
            "FOREX": -0.02,
            "COMMODITY": -0.05,
        },
        "volatility_multiplier": 6.0,
    },
}


def run_stress_test(positions: list[dict], scenario_key: str) -> dict:
    """Exécute un stress test sur le portefeuille.

    Chaque position a : symbol, asset_class, market_value, pnl
    """
    scenario = STRESS_SCENARIOS.get(scenario_key)
    if not scenario:
        return {"error": f"Scénario {scenario_key} inconnu"}

    total_value = sum(p.get("market_value", 0) for p in positions)
    if total_value == 0:
        return {
            "scenario": scenario["name"],
            "impact": 0,
            "impact_pct": 0,
            "positions": [],
        }

    impacts = []
    total_impact = 0

    for p in positions:
        asset_class = p.get("asset_class", "ACTION_US")
        shock = scenario["shocks"].get(asset_class, -0.10)
        market_value = p.get("market_value", 0)
        impact = market_value * shock
        total_impact += impact

        impacts.append({
            "symbol": p.get("symbol"),
            "asset_class": asset_class,
            "market_value": round(market_value, 2),
            "shock_pct": round(shock * 100, 1),
            "impact_usd": round(impact, 2),
        })

    return {
        "scenario": scenario["name"],
        "description": scenario["description"],
        "total_impact_usd": round(total_impact, 2),
        "total_impact_pct": round(total_impact / total_value * 100, 2) if total_value else 0,
        "portfolio_after": round(total_value + total_impact, 2),
        "volatility_multiplier": scenario["volatility_multiplier"],
        "positions": impacts,
    }


def detect_portfolio_regime(positions: list[dict], equity_curve: list[float]) -> dict:
    """Détecte le régime du portefeuille : ALPHA / BETA / STRESS.

    ALPHA : surperformance, drawdown faible, Sharpe > 1
    BETA : performance proche du marché
    STRESS : drawdown > 10%, volatilité élevée
    """
    if not equity_curve or len(equity_curve) < 20:
        return {"regime": "BETA", "confidence": 0.5, "reason": "Données insuffisantes"}

    returns = pd.Series(equity_curve).pct_change().dropna()
    if len(returns) < 10:
        return {"regime": "BETA", "confidence": 0.5, "reason": "Données insuffisantes"}

    mean_return = returns.mean() * 252
    vol = returns.std() * np.sqrt(252)
    sharpe = mean_return / vol if vol > 0 else 0

    # Max drawdown
    cumulative = (1 + returns).cumprod()
    peak = cumulative.expanding().max()
    drawdown = ((cumulative - peak) / peak).min()

    if drawdown < -0.10 or vol > 0.30:
        regime = "STRESS"
        confidence = min(0.9, abs(drawdown) * 3)
        reason = f"Drawdown {drawdown:.1%}, Volatilité {vol:.1%}"
    elif sharpe > 1.0 and drawdown > -0.05:
        regime = "ALPHA"
        confidence = min(0.9, sharpe * 0.4)
        reason = f"Sharpe {sharpe:.2f}, Drawdown {drawdown:.1%}"
    else:
        regime = "BETA"
        confidence = 0.6
        reason = f"Sharpe {sharpe:.2f}, performance marché"

    return {
        "regime": regime,
        "confidence": round(confidence, 3),
        "reason": reason,
        "metrics": {
            "annualized_return": round(mean_return * 100, 2),
            "annualized_vol": round(vol * 100, 2),
            "sharpe_ratio": round(sharpe, 3),
            "max_drawdown": round(drawdown * 100, 2),
        },
    }


def compute_liquidation_score(volume_avg: float, position_size: float,
                               market_cap: float = 0) -> float:
    """Score de liquidité de sortie (0-100).

    Évalue la facilité à sortir de la position sans impact marché.
    """
    if volume_avg == 0:
        return 10.0

    # Ratio position / volume journalier
    volume_ratio = position_size / volume_avg

    if volume_ratio < 0.01:
        score = 95.0  # Très facile à sortir
    elif volume_ratio < 0.05:
        score = 80.0
    elif volume_ratio < 0.10:
        score = 60.0
    elif volume_ratio < 0.25:
        score = 40.0
    else:
        score = 15.0  # Difficile à sortir sans impact

    return round(score, 1)
