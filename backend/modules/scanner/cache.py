"""Cache persistant pour les résultats du scanner.

Le scan de 218 actifs × 10 critères × 20 indicateurs prend plusieurs heures.
On persiste le cache sur disque pour qu'il survive aux redémarrages.
"""

import json
import time
import logging
from pathlib import Path

logger = logging.getLogger("tradepilot.scanner.cache")

CACHE_FILE = Path("data/scanner_cache.json")
CACHE_FILE.parent.mkdir(exist_ok=True)

_cache: dict = {
    "scan_results": [],
    "last_updated": 0,
    "updating": False,
}

CACHE_TTL = 3600 * 6  # 6 heures (au lieu de 5 minutes)


def _load_from_disk():
    """Charge le cache depuis le disque au démarrage."""
    global _cache
    if CACHE_FILE.exists() and not _cache["scan_results"]:
        try:
            data = json.loads(CACHE_FILE.read_text())
            _cache["scan_results"] = data.get("results", [])
            _cache["last_updated"] = data.get("last_updated", 0)
            logger.info(f"Cache chargé depuis disque : {len(_cache['scan_results'])} actifs")
        except Exception as e:
            logger.warning(f"Erreur chargement cache disque : {e}")


def _save_to_disk():
    """Sauvegarde le cache sur disque."""
    try:
        CACHE_FILE.write_text(json.dumps({
            "results": _cache["scan_results"],
            "last_updated": _cache["last_updated"],
        }, default=str))
    except Exception as e:
        logger.warning(f"Erreur sauvegarde cache disque : {e}")


# Charger au démarrage
_load_from_disk()


def get_cached_results() -> list[dict]:
    if not _cache["scan_results"]:
        _load_from_disk()
    return _cache["scan_results"]


def is_cache_fresh() -> bool:
    return (time.time() - _cache["last_updated"]) < CACHE_TTL and len(_cache["scan_results"]) > 0


def is_updating() -> bool:
    return _cache["updating"]


def update_cache(results: list[dict]):
    _cache["scan_results"] = results
    _cache["last_updated"] = time.time()
    _cache["updating"] = False
    _save_to_disk()
    logger.info(f"Cache scanner mis à jour et sauvegardé : {len(results)} actifs")


def set_updating():
    _cache["updating"] = True
