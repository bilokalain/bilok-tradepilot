"""MAJ quotidienne automatique (22h)

Met à jour :
1. Données OHLCV du jour
2. Features précalculées (indicateurs + scores)
3. Signaux actifs
"""

import asyncio
from datetime import datetime

import pandas as pd

pd.options.mode.dtype_backend = "pyarrow"


async def update_market_data():
    """Met à jour les données marché du jour."""
    # TODO: Charger les dernières données et insérer en BDD
    print(f"[{datetime.now()}] MAJ données marché...")


async def update_features():
    """Recalcule les features daily (indicateurs + 9 scores scanner)."""
    # TODO: Calculer SMA, EMA, RSI, MACD, Bollinger, ATR, Stochastic + 9 scores
    print(f"[{datetime.now()}] MAJ features...")


async def main():
    await update_market_data()
    await update_features()
    print(f"[{datetime.now()}] MAJ quotidienne terminée")


if __name__ == "__main__":
    asyncio.run(main())
