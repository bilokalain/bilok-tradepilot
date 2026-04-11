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
}


def get_best_strategy(symbol: str) -> str | None:
    """Retourne la meilleure stratégie backtest pour un actif."""
    entry = BACKTEST_MATRIX.get(symbol)
    return entry["best"] if entry else None


def get_strategy_sharpe(symbol: str, strategy: str) -> float:
    """Retourne le Sharpe du backtest pour un actif+stratégie."""
    entry = BACKTEST_MATRIX.get(symbol)
    if not entry:
        return 0.0
    return entry["all"].get(strategy, 0.0)


def get_profitable_strategies(symbol: str) -> list[str]:
    """Retourne les stratégies avec un Sharpe > 0 pour cet actif."""
    entry = BACKTEST_MATRIX.get(symbol)
    if not entry:
        return []
    return [s for s, sharpe in entry["all"].items() if sharpe > 0]


def get_strategy_ranking(symbol: str) -> list[dict]:
    """Classement des stratégies pour un actif."""
    entry = BACKTEST_MATRIX.get(symbol)
    if not entry:
        return []
    ranking = sorted(entry["all"].items(), key=lambda x: x[1], reverse=True)
    return [{"strategy": s, "sharpe": round(sh, 3)} for s, sh in ranking]
