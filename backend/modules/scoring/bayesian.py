"""Score Bayésien Adaptatif

Combine un prior historique (performance passée de l'actif/stratégie)
avec les observations actuelles (Module 1 Scanner + Module 2 Analyseur)
pour produire un score postérieur mis à jour.

Formule simplifiée :
  posterior = (prior * prior_weight + likelihood * obs_weight) / (prior_weight + obs_weight)

Où :
- prior = score historique de l'actif (basé sur la tendance long terme)
- likelihood = score actuel combinant scanner + analyseur
- Les poids s'ajustent selon la confiance du régime détecté
"""

import numpy as np
import pandas as pd


def compute_historical_prior(close: pd.Series) -> float:
    """Prior historique basé sur la performance long terme.

    Combine :
    - Performance 6 mois (rendement)
    - Consistance (% de mois positifs)
    - Tendance (position relative dans le range)
    """
    if len(close) < 126:  # minimum 6 mois
        return 50.0

    # Performance 6 mois
    perf_6m = (close.iloc[-1] / close.iloc[-126] - 1) * 100
    perf_score = 50 + np.clip(perf_6m * 2, -40, 40)

    # Consistance mensuelle (sur 6 mois)
    monthly_returns = []
    for i in range(6):
        start = -126 + i * 21
        end = start + 21
        if end == 0:
            end = None
        month_slice = close.iloc[start:end] if end else close.iloc[start:]
        if len(month_slice) >= 2:
            ret = (month_slice.iloc[-1] / month_slice.iloc[0] - 1) * 100
            monthly_returns.append(ret)

    if monthly_returns:
        positive_months = sum(1 for r in monthly_returns if r > 0)
        consistency = positive_months / len(monthly_returns)
        consistency_score = consistency * 100
    else:
        consistency_score = 50.0

    # Position dans le range 52 semaines
    if len(close) >= 252:
        high_52w = close.iloc[-252:].max()
        low_52w = close.iloc[-252:].min()
        if high_52w != low_52w:
            position = (close.iloc[-1] - low_52w) / (high_52w - low_52w) * 100
        else:
            position = 50.0
    else:
        position = 50.0

    # Pondération
    prior = perf_score * 0.40 + consistency_score * 0.30 + position * 0.30
    return round(np.clip(prior, 0, 100), 2)


def compute_observation_likelihood(scanner_score: float, strategy_conviction: float,
                                    regime_confidence: float) -> float:
    """Likelihood basé sur les observations actuelles.

    Combine :
    - Score scanner (Module 1) — 40%
    - Conviction stratégie (Module 2) — 40%
    - Confiance du régime — 20% (modulateur)
    """
    # La confiance du régime module l'impact des observations
    # Haute confiance = on fait plus confiance aux observations
    regime_confidence = float(np.clip(regime_confidence, 0, 1))
    confidence_factor = 0.5 + regime_confidence * 0.5  # entre 0.5 et 1.0

    raw = scanner_score * 0.40 + strategy_conviction * 0.40 + regime_confidence * 100 * 0.20
    modulated = raw * confidence_factor + 50 * (1 - confidence_factor)

    return round(np.clip(modulated, 0, 100), 2)


def compute_bayesian_score(close: pd.Series, scanner_score: float,
                           strategy_conviction: float, regime_confidence: float) -> dict:
    """Score Bayésien Adaptatif complet.

    Les poids prior/likelihood s'ajustent selon la confiance du régime :
    - Haute confiance → plus de poids aux observations actuelles
    - Basse confiance → plus de poids à l'historique (prior)
    """
    prior = compute_historical_prior(close)
    likelihood = compute_observation_likelihood(
        scanner_score, strategy_conviction, regime_confidence
    )

    # Poids adaptatifs
    # Confiance haute (>0.4) → observations pèsent plus
    # Confiance basse (<0.3) → prior pèse plus
    clamped_confidence = float(np.clip(regime_confidence, 0, 1))
    obs_weight = 0.4 + clamped_confidence * 0.4  # entre 0.4 et 0.8
    prior_weight = 1.0 - obs_weight

    posterior = prior * prior_weight + likelihood * obs_weight

    return {
        "prior": prior,
        "likelihood": likelihood,
        "posterior": round(np.clip(posterior, 0, 100), 2),
        "prior_weight": round(prior_weight, 3),
        "observation_weight": round(obs_weight, 3),
    }
