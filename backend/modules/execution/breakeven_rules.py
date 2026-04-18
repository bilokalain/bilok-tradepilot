"""Gestion des règles breakeven — fermer une position dès retour au prix d'entrée.

Usage :
    from backend.modules.execution.breakeven_rules import add_breakeven, remove_breakeven, get_rules

    add_breakeven("PTEN", 9.82)   # Fermer dès que PTEN >= 9.82$
    remove_breakeven("PTEN")       # Annuler la règle
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("tradepilot.breakeven")

RULES_FILE = Path("data/breakeven_rules.json")
RULES_FILE.parent.mkdir(exist_ok=True)


def _load() -> list[dict]:
    if RULES_FILE.exists():
        try:
            return json.loads(RULES_FILE.read_text())
        except Exception:
            return []
    return []


def _save(rules: list[dict]):
    RULES_FILE.write_text(json.dumps(rules, indent=2))


def add_breakeven(symbol: str, breakeven_price: float):
    """Ajoute une règle : fermer dès que le prix atteint breakeven_price."""
    rules = _load()
    # Remplacer si existe déjà
    rules = [r for r in rules if r.get("symbol") != symbol]
    rules.append({
        "symbol": symbol,
        "breakeven_price": breakeven_price,
        "active": True,
    })
    _save(rules)
    logger.info(f"[BREAKEVEN] Règle ajoutée: {symbol} → fermer à ${breakeven_price:.2f}")


def remove_breakeven(symbol: str):
    """Supprime la règle breakeven pour un symbole."""
    rules = _load()
    rules = [r for r in rules if r.get("symbol") != symbol]
    _save(rules)
    logger.info(f"[BREAKEVEN] Règle supprimée: {symbol}")


def get_rules() -> list[dict]:
    """Retourne toutes les règles actives."""
    return [r for r in _load() if r.get("active")]
