"""Chargement initial des données historiques → PostgreSQL"""

import sys
import time
sys.path.insert(0, ".")

from datetime import datetime

import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily, AssetClass

DB_URL = "postgresql://tradepilot:tradepilot_dev@localhost:5432/tradepilot"

INITIAL_SYMBOLS = {
    AssetClass.ACTION_US: {
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "GOOGL": "Alphabet",
        "AMZN": "Amazon",
        "TSLA": "Tesla",
        "NVDA": "NVIDIA",
        "META": "Meta Platforms",
        "JPM": "JPMorgan Chase",
        "V": "Visa",
        "JNJ": "Johnson & Johnson",
    },
    AssetClass.CRYPTO: {
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
        "BNB-USD": "Binance Coin",
        "SOL-USD": "Solana",
        "XRP-USD": "Ripple",
    },
    AssetClass.ETF: {
        "SPY": "SPDR S&P 500",
        "QQQ": "Invesco QQQ",
        "IWM": "iShares Russell 2000",
        "VTI": "Vanguard Total Stock",
        "GLD": "SPDR Gold",
        "TLT": "iShares 20+ Year Treasury",
    },
}


def main():
    engine = create_engine(DB_URL)
    total = 0

    with Session(engine) as session:
        for asset_class, symbols in INITIAL_SYMBOLS.items():
            print(f"\n{'='*50}")
            print(f"  {asset_class.value}")
            print(f"{'='*50}")

            for symbol, name in symbols.items():
                # Créer ou récupérer l'actif
                asset = session.query(Asset).filter_by(symbol=symbol).first()
                if not asset:
                    asset = Asset(symbol=symbol, name=name, asset_class=asset_class, is_active=True)
                    session.add(asset)
                    session.flush()
                    print(f"  [{symbol}] créé (id={asset.id})")
                else:
                    print(f"  [{symbol}] existant (id={asset.id})")

                # Vérifier si données déjà chargées
                existing = session.query(OHLCVDaily).filter_by(asset_id=asset.id).count()
                if existing > 0:
                    print(f"    → {existing} jours déjà en BDD, skip")
                    continue

                # Charger depuis Yahoo Finance
                try:
                    ticker = yf.Ticker(symbol)
                    df = ticker.history(period="2y", interval="1d")
                    time.sleep(0.5)  # anti rate-limit
                except Exception as e:
                    print(f"    → Erreur: {e}")
                    continue

                if df.empty:
                    print(f"    → Aucune donnée")
                    continue

                rows = []
                for idx, row in df.iterrows():
                    rows.append(OHLCVDaily(
                        asset_id=asset.id,
                        date=idx.date(),
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"]),
                        volume=int(row["Volume"]),
                        source="yahoo",
                    ))

                session.bulk_save_objects(rows)
                session.commit()
                total += len(rows)
                print(f"    → {len(rows)} jours chargés ✓")

    print(f"\n{'='*50}")
    print(f"  TOTAL : {total} lignes OHLCV chargées")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
