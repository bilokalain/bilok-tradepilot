"""Sizing centralisé — UN SEUL endroit pour calculer la taille de position

Règles :
1. Kelly × V2 modifier si disponible (router.py, execute_trade)
2. Fallback : base_pct (5%) + bonus score → plafond 15%
3. Plancher : au moins 1 unité pour les actions
4. Plafond absolu : jamais > MAX_PCT du capital

Tous les modules (router, tp_sl_monitor, position_manager_v2) appellent
compute_position_size() au lieu de recalculer le sizing localement.
"""

import logging

logger = logging.getLogger("tradepilot.sizing")

# Paramètres centralisés
BASE_PCT = 0.05        # 5% du capital minimum par position
MAX_PCT = 0.15         # 15% du capital max par position
SCORE_BONUS_RANGE = 0.10  # Le score peut ajouter jusqu'à 10% (5% → 15%)
SCORE_THRESHOLD = 50   # Score en dessous duquel on reste au minimum


def compute_position_size(
    capital: float,
    entry_price: float,
    score: float = 50,
    kelly_size: float | None = None,
    sizing_modifier: float = 1.0,
) -> dict:
    """Calcule la taille de position — source unique de vérité.

    Args:
        capital: Capital disponible (equity du broker)
        entry_price: Prix d'entrée estimé
        score: Score V2 ou score scanner (0-100)
        kelly_size: Taille Kelly calculée (None = pas disponible)
        sizing_modifier: Multiplicateur V2 (catalyseurs, corrélation, régime)

    Returns:
        dict avec position_size, quantity, pct_of_capital
    """
    if capital <= 0 or entry_price <= 0:
        return {"position_size": 0, "quantity": 0, "pct_of_capital": 0}

    # Score factor : 0.0 (score=50) → 1.0 (score=80+)
    score_factor = max(0.0, min(1.0, (score - SCORE_THRESHOLD) / 30))

    # Taille de base : 5% à 15% selon le score
    base_size = capital * (BASE_PCT + score_factor * SCORE_BONUS_RANGE)

    # Si Kelly est disponible et positif, prendre le max(kelly, base)
    if kelly_size and kelly_size > 0:
        position_size = max(kelly_size, base_size)
    else:
        position_size = base_size

    # Appliquer le modifier V2
    position_size *= sizing_modifier

    # Plafond absolu : 15% du capital
    position_size = min(position_size, capital * MAX_PCT)

    # Plancher : au moins le prix d'une unité
    position_size = max(position_size, entry_price)

    # Ne pas dépasser le capital disponible
    position_size = min(position_size, capital)

    # Quantité
    quantity = round(position_size / entry_price, 4)

    return {
        "position_size": round(position_size, 2),
        "quantity": quantity,
        "pct_of_capital": round(position_size / capital * 100, 2),
    }


def quantize(quantity: float, symbol: str) -> float:
    """Arrondit la quantité selon le type d'actif.

    Crypto (-USD) : fractions autorisées (4 décimales)
    Actions : minimum 1, entier
    """
    if "-USD" in symbol:
        return max(0.0001, round(quantity, 4))
    return max(1, int(quantity))
