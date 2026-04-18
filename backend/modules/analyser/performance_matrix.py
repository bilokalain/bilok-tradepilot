"""Matrice de performance stratégie×actif — basée sur les backtests réels

Cette matrice remplace les heuristiques du Module 2 par des données empiriques.
Le Module 2 utilise cette matrice pour sélectionner la meilleure stratégie
pour chaque actif, en tenant compte du régime de marché.

Mise à jour : recalculée hebdomadairement via Celery.
"""

# Meilleure stratégie par actif (issue du backtest sur 2 ans de données)
# Format : {symbol: {"best": strategy, "sharpe": float, "all": {strategy: sharpe}}}
BACKTEST_MATRIX = {
    "AAPL": {
        "best": "breakout",
        "sharpe": 1.042,
        "all": {"breakout": 1.042, "trend_following": 0.583, "mean_reversion": -0.165, "momentum": -0.830},
    },
    "AMZN": {
        "best": "mean_reversion",
        "sharpe": 1.703,
        "all": {"mean_reversion": 1.703, "trend_following": -0.745, "breakout": -1.008, "momentum": -1.469},
    },
    "BNB-USD": {
        "best": "trend_following",
        "sharpe": 0.867,
        "all": {"trend_following": 0.867, "momentum": 0.856, "breakout": 0.462, "mean_reversion": -0.612},
    },
    "BTC-USD": {
        "best": "momentum",
        "sharpe": 0.161,
        "all": {"momentum": 0.161, "mean_reversion": 0.139, "trend_following": 0.100, "breakout": -0.145},
    },
    "ETH-USD": {
        "best": "breakout",
        "sharpe": 0.452,
        "all": {"breakout": 0.452, "momentum": 0.086, "trend_following": 0.025, "mean_reversion": -0.869},
    },
    "GLD": {
        "best": "breakout",
        "sharpe": 1.619,
        "all": {"breakout": 1.619, "trend_following": 1.617, "momentum": 0.287, "mean_reversion": -0.781},
    },
    "GOOGL": {
        "best": "trend_following",
        "sharpe": 1.809,
        "all": {"trend_following": 1.809, "momentum": 0.905, "breakout": 0.522, "mean_reversion": -0.279},
    },
    "IWM": {
        "best": "momentum",
        "sharpe": 0.809,
        "all": {"momentum": 0.809, "breakout": 0.686, "trend_following": 0.200, "mean_reversion": -0.932},
    },
    "JNJ": {
        "best": "momentum",
        "sharpe": 1.763,
        "all": {"momentum": 1.763, "trend_following": 1.512, "breakout": 0.648, "mean_reversion": 0.274},
    },
    "JPM": {
        "best": "trend_following",
        "sharpe": 0.622,
        "all": {"trend_following": 0.622, "momentum": 0.201, "mean_reversion": -0.141, "breakout": -0.620},
    },
    "META": {
        "best": "mean_reversion",
        "sharpe": 0.142,
        "all": {"mean_reversion": 0.142, "momentum": -0.406, "breakout": -0.549, "trend_following": -1.350},
    },
    "MSFT": {
        "best": "trend_following",
        "sharpe": 1.372,
        "all": {"trend_following": 1.372, "breakout": 0.448, "momentum": 0.408, "mean_reversion": -0.790},
    },
    "NVDA": {
        "best": "mean_reversion",
        "sharpe": 1.232,
        "all": {"mean_reversion": 1.232, "momentum": 0.312, "trend_following": -0.006, "breakout": -0.256},
    },
    "QQQ": {
        "best": "breakout",
        "sharpe": 0.685,
        "all": {"breakout": 0.685, "trend_following": 0.492, "momentum": 0.204, "mean_reversion": 0.002},
    },
    "SOL-USD": {
        "best": "mean_reversion",
        "sharpe": 0.321,
        "all": {"mean_reversion": 0.321, "trend_following": -0.412, "momentum": -0.486, "breakout": -0.624},
    },
    "SPY": {
        "best": "trend_following",
        "sharpe": 0.909,
        "all": {"trend_following": 0.909, "breakout": -0.069, "mean_reversion": -0.167, "momentum": -0.495},
    },
    "TLT": {
        "best": "mean_reversion",
        "sharpe": 0.531,
        "all": {"mean_reversion": 0.531, "momentum": -1.365, "trend_following": -1.971, "breakout": -2.135},
    },
    "TSLA": {
        "best": "trend_following",
        "sharpe": 0.983,
        "all": {"trend_following": 0.983, "breakout": 0.699, "momentum": 0.196, "mean_reversion": -0.154},
    },
    "V": {
        "best": "mean_reversion",
        "sharpe": -0.188,
        "all": {"mean_reversion": -0.188, "breakout": -0.691, "momentum": -1.759, "trend_following": -1.862},
    },
    "VTI": {
        "best": "trend_following",
        "sharpe": 0.491,
        "all": {"trend_following": 0.491, "momentum": 0.046, "mean_reversion": -0.279, "breakout": -0.485},
    },
    "XRP-USD": {
        "best": "momentum",
        "sharpe": 1.285,
        "all": {"momentum": 1.285, "trend_following": 1.008, "breakout": 0.638, "mean_reversion": -0.774},
    },
    # --- Actions EU ---
    "MC.PA": {
        "best": "trend_following",
        "sharpe": 1.409,
        "all": {"trend_following": 1.409, "momentum": 1.399, "breakout": 1.23, "mean_reversion": -0.304},
    },
    "OR.PA": {
        "best": "mean_reversion",
        "sharpe": 0.752,
        "all": {"mean_reversion": 0.752, "momentum": -0.47, "trend_following": -1.103, "breakout": -1.35},
    },
    "SAN.PA": {
        "best": "mean_reversion",
        "sharpe": 1.084,
        "all": {"mean_reversion": 1.084, "breakout": -0.039, "momentum": -1.077, "trend_following": -1.237},
    },
    "AIR.PA": {
        "best": "mean_reversion",
        "sharpe": 0.661,
        "all": {"mean_reversion": 0.661, "breakout": 0.384, "trend_following": 0.29, "momentum": -0.426},
    },
    "BNP.PA": {
        "best": "mean_reversion",
        "sharpe": 0.41,
        "all": {"mean_reversion": 0.41, "breakout": 0.407, "momentum": 0.406, "trend_following": 0.274},
    },
    "SAP.DE": {
        "best": "momentum",
        "sharpe": 0.474,
        "all": {"momentum": 0.474, "trend_following": 0.228, "breakout": 0.067, "mean_reversion": -0.347},
    },
    "SIE.DE": {
        "best": "mean_reversion",
        "sharpe": 0.378,
        "all": {"mean_reversion": 0.378, "breakout": -0.454, "momentum": -0.724, "trend_following": -1.002},
    },
    "ASML.AS": {
        "best": "mean_reversion",
        "sharpe": -0.087,
        "all": {"mean_reversion": -0.087, "trend_following": -0.123, "momentum": -0.283, "breakout": -0.435},
    },
    "NESN.SW": {
        "best": "breakout",
        "sharpe": 0.826,
        "all": {"breakout": 0.826, "trend_following": 0.701, "momentum": 0.641, "mean_reversion": -0.494},
    },
    "ROG.SW": {
        "best": "mean_reversion",
        "sharpe": 0.235,
        "all": {"mean_reversion": 0.235, "trend_following": -0.087, "breakout": -0.353, "momentum": -0.751},
    },
    # --- Forex ---
    "EURUSD=X": {
        "best": "trend_following",
        "sharpe": 0.203,
        "all": {"trend_following": 0.203, "mean_reversion": 0.02, "breakout": 0.0, "momentum": -1.322},
    },
    "GBPUSD=X": {
        "best": "trend_following",
        "sharpe": 0.522,
        "all": {"trend_following": 0.522, "mean_reversion": 0.092, "breakout": 0.0, "momentum": -0.17},
    },
    "USDJPY=X": {
        "best": "trend_following",
        "sharpe": 0.167,
        "all": {"trend_following": 0.167, "momentum": 0.155, "breakout": 0.0, "mean_reversion": -0.415},
    },
    "USDCHF=X": {
        "best": "trend_following",
        "sharpe": 1.003,
        "all": {"trend_following": 1.003, "mean_reversion": 0.704, "breakout": 0.0, "momentum": -0.153},
    },
    "AUDUSD=X": {
        "best": "mean_reversion",
        "sharpe": 0.062,
        "all": {"mean_reversion": 0.062, "breakout": 0.0, "momentum": -0.556, "trend_following": -0.704},
    },
    "USDCAD=X": {
        "best": "mean_reversion",
        "sharpe": 1.131,
        "all": {"mean_reversion": 1.131, "trend_following": 0.167, "breakout": 0.0, "momentum": -1.074},
    },
    "NZDUSD=X": {
        "best": "mean_reversion",
        "sharpe": 1.402,
        "all": {"mean_reversion": 1.402, "breakout": 0.0, "momentum": -0.398, "trend_following": -0.817},
    },
    "EURGBP=X": {
        "best": "mean_reversion",
        "sharpe": 0.47,
        "all": {"mean_reversion": 0.47, "breakout": 0.0, "momentum": -0.117, "trend_following": -0.445},
    },
    "EURJPY=X": {
        "best": "trend_following",
        "sharpe": 1.163,
        "all": {"trend_following": 1.163, "momentum": 0.836, "breakout": 0.0, "mean_reversion": -1.32},
    },
    "GBPJPY=X": {
        "best": "breakout",
        "sharpe": 0.0,
        "all": {"breakout": 0.0, "mean_reversion": -0.386, "trend_following": -0.87, "momentum": -1.388},
    },
    # --- Matières Premières ---
    "GC=F": {
        "best": "trend_following",
        "sharpe": 1.733,
        "all": {"trend_following": 1.733, "momentum": 1.289, "breakout": 1.267, "mean_reversion": -0.847},
    },
    "SI=F": {
        "best": "trend_following",
        "sharpe": 2.062,
        "all": {"trend_following": 2.062, "breakout": 1.815, "momentum": 1.29, "mean_reversion": -1.235},
    },
    "CL=F": {
        "best": "breakout",
        "sharpe": 0.952,
        "all": {"breakout": 0.952, "momentum": 0.845, "trend_following": 0.673, "mean_reversion": -0.553},
    },
    "NG=F": {
        "best": "breakout",
        "sharpe": 0.288,
        "all": {"breakout": 0.288, "mean_reversion": 0.221, "momentum": -0.05, "trend_following": -1.216},
    },
    "HG=F": {
        "best": "breakout",
        "sharpe": 0.169,
        "all": {"breakout": 0.169, "trend_following": -0.103, "momentum": -0.391, "mean_reversion": -0.64},
    },
    "PL=F": {
        "best": "breakout",
        "sharpe": 1.822,
        "all": {"breakout": 1.822, "momentum": 0.982, "trend_following": 0.76, "mean_reversion": -0.133},
    },
    "ZW=F": {
        "best": "mean_reversion",
        "sharpe": 1.03,
        "all": {"mean_reversion": 1.03, "breakout": -0.823, "momentum": -0.88, "trend_following": -1.66},
    },
    "ZC=F": {
        "best": "mean_reversion",
        "sharpe": 0.198,
        "all": {"mean_reversion": 0.198, "momentum": 0.023, "breakout": -0.297, "trend_following": -0.901},
    },
    "ZS=F": {
        "best": "momentum",
        "sharpe": 0.518,
        "all": {"momentum": 0.518, "mean_reversion": 0.187, "breakout": 0.09, "trend_following": -0.135},
    },
    "CC=F": {
        "best": "momentum",
        "sharpe": 0.207,
        "all": {"momentum": 0.207, "trend_following": 0.039, "mean_reversion": -0.083, "breakout": -0.42},
    },
}


# ─── Chargement dynamique depuis le fichier backtest_full_500.json ───
# Fusionne avec la BACKTEST_MATRIX hardcodée (le fichier prend priorité)

import json
import logging
from pathlib import Path

_logger = logging.getLogger("tradepilot.performance_matrix")
_BACKTEST_FILE = Path("data/backtest_full_500.json")
_dynamic_matrix: dict = {}
_dynamic_loaded = False


def _load_dynamic_matrix():
    """Charge les résultats du full backtest depuis le disque."""
    global _dynamic_matrix, _dynamic_loaded
    if not _BACKTEST_FILE.exists():
        _dynamic_loaded = True
        return
    try:
        data = json.loads(_BACKTEST_FILE.read_text())
        results = data.get("results", {})
        for symbol, r in results.items():
            strats = r.get("strategies", [])
            if not strats:
                continue
            all_sharpes = {s["strategy"]: s["sharpe_ratio"] for s in strats}
            best = r.get("best_strategy")
            best_sharpe = r.get("best_sharpe", 0)
            if best:
                _dynamic_matrix[symbol] = {
                    "best": best,
                    "sharpe": best_sharpe,
                    "all": all_sharpes,
                }
        _dynamic_loaded = True
        _logger.info(f"Matrice backtest chargée : {len(_dynamic_matrix)} actifs depuis {_BACKTEST_FILE}")
    except Exception as e:
        _logger.warning(f"Erreur chargement matrice backtest : {e}")
        _dynamic_loaded = True


def _get_entry(symbol: str) -> dict | None:
    """Récupère l'entrée backtest pour un actif (dynamique > hardcodé)."""
    global _dynamic_loaded
    if not _dynamic_loaded:
        _load_dynamic_matrix()
    # Priorité au fichier backtest, fallback sur la matrice hardcodée
    return _dynamic_matrix.get(symbol) or BACKTEST_MATRIX.get(symbol)


def reload_matrix():
    """Force le rechargement de la matrice depuis le disque."""
    global _dynamic_loaded
    _dynamic_loaded = False
    _dynamic_matrix.clear()
    _load_dynamic_matrix()


def get_best_strategy(symbol: str) -> str | None:
    """Retourne la meilleure stratégie backtest pour un actif."""
    entry = _get_entry(symbol)
    return entry["best"] if entry else None


def get_strategy_sharpe(symbol: str, strategy: str) -> float:
    """Retourne le Sharpe du backtest pour un actif+stratégie."""
    entry = _get_entry(symbol)
    if not entry:
        return 0.0
    return entry["all"].get(strategy, 0.0)


def get_profitable_strategies(symbol: str) -> list[str]:
    """Retourne les stratégies avec un Sharpe > 0 pour cet actif."""
    entry = _get_entry(symbol)
    if not entry:
        return []
    return [s for s, sharpe in entry["all"].items() if sharpe > 0]


def get_strategy_ranking(symbol: str) -> list[dict]:
    """Classement des stratégies pour un actif."""
    entry = _get_entry(symbol)
    if not entry:
        return []
    ranking = sorted(entry["all"].items(), key=lambda x: x[1], reverse=True)
    return [{"strategy": s, "sharpe": round(sh, 3)} for s, sh in ranking]


def get_matrix_stats() -> dict:
    """Stats sur la matrice de backtest."""
    if not _dynamic_loaded:
        _load_dynamic_matrix()
    return {
        "hardcoded_assets": len(BACKTEST_MATRIX),
        "dynamic_assets": len(_dynamic_matrix),
        "total_assets": len(set(list(BACKTEST_MATRIX.keys()) + list(_dynamic_matrix.keys()))),
        "source": str(_BACKTEST_FILE) if _dynamic_matrix else "hardcoded only",
    }
