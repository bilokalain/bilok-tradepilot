"""Chargement de l'historique profond — max Yahoo Finance gratuit

Yahoo Finance permet :
- Actions US / ETF : jusqu'à ~30 ans en daily (max)
- Crypto : depuis la création du token
- Forex : ~20 ans
- Commodities : ~20 ans
- Actions EU : ~10-20 ans selon le marché

On charge avec period="max" pour récupérer tout ce qui est disponible.
On ne re-télécharge pas les données déjà en base.
"""

import sys
import time
sys.path.insert(0, ".")

from datetime import date

import yfinance as yf
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily

DB_URL = "postgresql://tradepilot:tradepilot_dev@localhost:5432/tradepilot"


def load_deep_history(session: Session, asset: Asset) -> dict:
    """Charge l'historique maximum pour un actif."""
    # Date la plus ancienne déjà en base
    oldest = session.query(func.min(OHLCVDaily.date)).filter_by(asset_id=asset.id).scalar()
    existing_count = session.query(OHLCVDaily).filter_by(asset_id=asset.id).count()

    try:
        ticker = yf.Ticker(asset.symbol)
        df = ticker.history(period="max", interval="1d")
        time.sleep(0.3)
    except Exception as e:
        return {"symbol": asset.symbol, "status": f"error: {e}", "added": 0}

    if df.empty:
        return {"symbol": asset.symbol, "status": "no_data", "added": 0}

    # Filtrer les dates pas encore en base
    new_rows = []
    for idx, row in df.iterrows():
        d = idx.date()
        if oldest and d >= oldest:
            continue  # Déjà en base
        new_rows.append(OHLCVDaily(
            asset_id=asset.id,
            date=d,
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=int(row["Volume"]),
            source="yahoo",
        ))

    if new_rows:
        session.bulk_save_objects(new_rows)
        session.commit()

    total_available = len(df)
    first_date = df.index[0].date()
    last_date = df.index[-1].date()
    years = (last_date - first_date).days / 365

    return {
        "symbol": asset.symbol,
        "status": "ok",
        "added": len(new_rows),
        "total_available": total_available,
        "existing": existing_count,
        "first_date": str(first_date),
        "last_date": str(last_date),
        "years": round(years, 1),
    }


def main():
    engine = create_engine(DB_URL)
    total_added = 0

    with Session(engine) as session:
        assets = session.query(Asset).filter_by(is_active=True).order_by(Asset.id).all()
        print(f"\nChargement historique profond pour {len(assets)} actifs\n")
        print(f"{'Symbol':12} {'Nom':25} {'Ajouté':>8} {'Total':>8} {'Depuis':>12} {'Années':>7}")
        print("─" * 80)

        for asset in assets:
            result = load_deep_history(session, asset)

            if result["status"] == "ok":
                total_added += result["added"]
                print(f"{asset.symbol:12} {asset.name[:25]:25} {result['added']:>8} {result['total_available']:>8} {result['first_date']:>12} {result['years']:>6.1f}a")
            else:
                print(f"{asset.symbol:12} {asset.name[:25]:25} {result['status']}")

    # Stats finales
    with Session(engine) as session:
        total_daily = session.query(OHLCVDaily).count()
        oldest = session.query(func.min(OHLCVDaily.date)).scalar()
        newest = session.query(func.max(OHLCVDaily.date)).scalar()

    print(f"\n{'='*80}")
    print(f"  Nouvelles barres ajoutées : {total_added:,}")
    print(f"  Total barres daily : {total_daily:,}")
    print(f"  Période couverte : {oldest} → {newest}")
    if oldest and newest:
        print(f"  Durée maximale : {(newest - oldest).days / 365:.1f} ans")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
