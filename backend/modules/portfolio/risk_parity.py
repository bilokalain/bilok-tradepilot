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
    "oil_shock_iran": {
        "name": "Choc Pétrolier — Conflit Iran",
        "description": "Escalade militaire au Moyen-Orient, fermeture du détroit d'Ormuz, pétrole +60%, crise énergétique mondiale",
        "shocks": {
            "ACTION_US": -0.18,
            "ACTION_EU": -0.25,
            "ETF": -0.15,
            "CRYPTO": -0.10,
            "FOREX": -0.08,
            "COMMODITY": 0.45,
        },
        "asset_overrides": {
            "CL=F": 0.60, "NG=F": 0.40, "XLE": 0.30, "XOM": 0.25, "CVX": 0.20,
            "COP": 0.20, "TTE.PA": 0.22, "RB=F": 0.50,
            "GC=F": 0.15, "SI=F": 0.10, "GLD": 0.12,
            "LMT": 0.18, "RTX": 0.15, "GD": 0.12, "NOC": 0.14, "KTOS": 0.20, "RHM.DE": 0.25,
            "BA": -0.15, "AIR.DE": -0.12,
            "XLU": 0.05, "NEE": -0.08,
            "TSLA": -0.20, "NIO": -0.25, "RIVN": -0.22, "LCID": -0.25,
        },
        "volatility_multiplier": 3.5,
    },
    "taper_tantrum_rates": {
        "name": "Choc de Taux — Fed +200bps",
        "description": "Hausse brutale des taux d'intérêt (+200 points de base), crash obligataire, tech et growth massacrés",
        "shocks": {
            "ACTION_US": -0.20,
            "ACTION_EU": -0.15,
            "ETF": -0.18,
            "CRYPTO": -0.30,
            "FOREX": 0.05,
            "COMMODITY": -0.08,
        },
        "asset_overrides": {
            "TLT": -0.25, "HYG": -0.15, "LQD": -0.12, "EMB": -0.18,
            "ARKK": -0.40, "ARKG": -0.35,
            "JPM": 0.10, "GS": 0.08, "BAC": 0.12, "MS": 0.08,
            "XLF": 0.10, "KRE": 0.15,
            "NVDA": -0.25, "TSLA": -0.30, "PLTR": -0.35,
        },
        "volatility_multiplier": 3.0,
    },
    "dollar_collapse": {
        "name": "Effondrement du Dollar",
        "description": "DXY -15%, perte de confiance dans le dollar, fuite vers l'or et les actifs réels",
        "shocks": {
            "ACTION_US": -0.12,
            "ACTION_EU": 0.08,
            "ETF": -0.08,
            "CRYPTO": 0.25,
            "FOREX": -0.12,
            "COMMODITY": 0.30,
        },
        "asset_overrides": {
            "GC=F": 0.35, "SI=F": 0.30, "GLD": 0.32, "SLV": 0.28,
            "BTC-USD": 0.40, "ETH-USD": 0.35,
            "EURUSD=X": 0.15, "GBPUSD=X": 0.12, "USDJPY=X": -0.10,
            "MELI": 0.15, "SE": 0.12,
        },
        "volatility_multiplier": 2.5,
    },
    "stagflation": {
        "name": "Stagflation",
        "description": "Croissance nulle + inflation à 8%+ — le pire des deux mondes. Les actions baissent ET le pouvoir d'achat s'érode",
        "shocks": {
            "ACTION_US": -0.22,
            "ACTION_EU": -0.20,
            "ETF": -0.18,
            "CRYPTO": -0.35,
            "FOREX": -0.05,
            "COMMODITY": 0.25,
        },
        "asset_overrides": {
            "GC=F": 0.20, "SI=F": 0.15, "GLD": 0.18,
            "CL=F": 0.15, "NG=F": 0.20,
            "XLP": 0.02, "KO": 0.03, "PG": 0.02,
            "TLT": -0.15,
            "ARKK": -0.45, "ARKG": -0.40,
            "CCJ": 0.10, "LEU": 0.12, "URA": 0.08,
        },
        "volatility_multiplier": 2.0,
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

    overrides = scenario.get("asset_overrides", {})

    for p in positions:
        symbol = p.get("symbol", "")
        asset_class = p.get("asset_class", "ACTION_US")
        # Choc spécifique par actif si disponible, sinon choc de la classe
        if symbol in overrides:
            shock = overrides[symbol]
        else:
            shock = scenario["shocks"].get(asset_class, -0.10)
        market_value = p.get("market_value", 0)
        impact = market_value * shock
        total_impact += impact

        impacts.append({
            "symbol": symbol,
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
