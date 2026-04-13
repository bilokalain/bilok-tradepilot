"""Cache global — sert les résultats pré-calculés pour tous les modules.

Chaque module lit son cache depuis data/{module}_cache.json.
Les caches sont générés par scripts/precompute_all.py et mis à jour
par Celery Beat la nuit.
"""

import json
from pathlib import Path

DATA_DIR = Path("data")


def load_cache(name: str) -> dict | list | None:
    filepath = DATA_DIR / f"{name}_cache.json"
    if filepath.exists():
        try:
            return json.loads(filepath.read_text())
        except Exception:
            return None
    return None


def get_analyser_cache() -> dict:
    data = load_cache("analyser")
    return data if data else {"regime": {}, "analyses": []}


def get_signals_cache() -> list:
    data = load_cache("signals")
    return data if isinstance(data, list) else []


def get_performance_cache() -> dict:
    data = load_cache("performance")
    return data if data else {}


def get_portfolio_cache() -> dict:
    data = load_cache("portfolio")
    return data if data else {}


def get_global_regime_cache() -> dict:
    data = load_cache("global_regime")
    return data if data else {"regime": "UNKNOWN", "confidence": 0}
