"""Chargement des données intraday 1H → PostgreSQL

Yahoo Finance limite les données intraday à ~730 jours pour le 1H.
On charge ce qui est disponible pour tous les actifs.
"""

import sys
import time
sys.path.insert(0, ".")

from datetime import datetime

import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCV1H

DB_URL = "postgresql://tradepilot:tradepilot_dev@localhost:5432/tradepilot"


def main():
    engine = create_engine(DB_URL)
    total = 0

    with Session(engine) as session:
        assets = session.query(Asset).filter_by(is_active=True).all()
        print(f"\nChargement intraday 1H pour {len(assets)} actifs\n")

        for asset in assets:
            # Vérifier si données déjà chargées
            existing = session.query(OHLCV1H).filter_by(asset_id=asset.id).count()
            if existing > 0:
                print(f"  [{asset.symbol}] {existing} barres 1H déjà en BDD, skip")
                continue

            try:
                ticker = yf.Ticker(asset.symbol)
                # Yahoo Finance : max ~730 jours en 1H
                df = ticker.history(period="2y", interval="1h")
                time.sleep(0.5)
            except Exception as e:
                print(f"  [{asset.symbol}] Erreur: {e}")
                continue

            if df.empty:
                print(f"  [{asset.symbol}] Aucune donnée intraday")
                continue

            rows = []
            for idx, row in df.iterrows():
                dt = idx.to_pydatetime().replace(tzinfo=None)
                rows.append(OHLCV1H(
                    asset_id=asset.id,
                    datetime=dt,
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
            print(f"  [{asset.symbol}] {len(rows)} barres 1H chargées")

    print(f"\n{'='*50}")
    print(f"  TOTAL : {total} barres intraday 1H chargées")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
