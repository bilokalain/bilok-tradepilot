"""Cache en mémoire pour les résultats du scanner.

Le scan complet de 51 actifs prend ~80 secondes.
On cache le résultat et on le recalcule en arrière-plan.
"""

import time
import threading
import logging

logger = logging.getLogger("tradepilot.scanner.cache")

_cache: dict = {
    "scan_results": [],
    "last_updated": 0,
    "updating": False,
}

CACHE_TTL = 300  # 5 minutes


def get_cached_results() -> list[dict]:
    return _cache["scan_results"]


def is_cache_fresh() -> bool:
    return (time.time() - _cache["last_updated"]) < CACHE_TTL and len(_cache["scan_results"]) > 0


def is_updating() -> bool:
    return _cache["updating"]


def update_cache(results: list[dict]):
    _cache["scan_results"] = results
    _cache["last_updated"] = time.time()
    _cache["updating"] = False
    logger.info(f"Cache scanner mis à jour : {len(results)} actifs")


def set_updating():
    _cache["updating"] = True
