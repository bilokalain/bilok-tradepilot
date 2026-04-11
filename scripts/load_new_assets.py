"""Chargement des nouveaux actifs : Actions EU, Forex, Matières Premières

Symboles Yahoo Finance :
- Actions EU : ticker.PA (Paris), .DE (Francfort), .AS (Amsterdam), .SW (Zurich)
- Forex : EURUSD=X, GBPUSD=X, etc.
- Matières premières : GC=F (Gold futures), CL=F (Crude Oil), etc.
"""

import sys
import time
sys.path.insert(0, ".")

import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily, OHLCV1H, AssetClass

DB_URL = "postgresql://tradepilot:tradepilot_dev@localhost:5432/tradepilot"

NEW_ASSETS = {
    AssetClass.ACTION_EU: {
        "MC.PA": "LVMH",
        "OR.PA": "L'Oréal",
        "SAN.PA": "Sanofi",
        "AIR.PA": "Airbus",
        "BNP.PA": "BNP Paribas",
        "SAP.DE": "SAP",
        "SIE.DE": "Siemens",
        "ASML.AS": "ASML",
        "NESN.SW": "Nestlé",
        "ROG.SW": "Roche",
    },
    AssetClass.FOREX: {
        "EURUSD=X": "EUR/USD",
        "GBPUSD=X": "GBP/USD",
        "USDJPY=X": "USD/JPY",
        "USDCHF=X": "USD/CHF",
        "AUDUSD=X": "AUD/USD",
        "USDCAD=X": "USD/CAD",
        "NZDUSD=X": "NZD/USD",
        "EURGBP=X": "EUR/GBP",
        "EURJPY=X": "EUR/JPY",
        "GBPJPY=X": "GBP/JPY",
    },
    AssetClass.COMMODITY: {
        "GC=F": "Gold Futures",
        "SI=F": "Silver Futures",
        "CL=F": "Crude Oil WTI",
        "NG=F": "Natural Gas",
        "HG=F": "Copper Futures",
        "PL=F": "Platinum Futures",
        "ZW=F": "Wheat Futures",
        "ZC=F": "Corn Futures",
        "ZS=F": "Soybean Futures",
        "CC=F": "Cocoa Futures",
    },
}


def load_asset_data(session: Session, symbol: str, name: str,
                    asset_class: AssetClass) -> dict:
    """Crée l'actif et charge daily + intraday."""
    result = {"symbol": symbol, "daily": 0, "intraday": 0, "errors": []}

    # Créer ou récupérer l'actif
    asset = session.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        asset = Asset(symbol=symbol, name=name, asset_class=asset_class, is_active=True)
        session.add(asset)
        session.flush()

    # --- Daily ---
    existing_daily = session.query(OHLCVDaily).filter_by(asset_id=asset.id).count()
    if existing_daily == 0:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="2y", interval="1d")
            time.sleep(0.3)

            if not df.empty:
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
                result["daily"] = len(rows)
        except Exception as e:
            result["errors"].append(f"daily: {e}")

    # --- Intraday 1H ---
    existing_1h = session.query(OHLCV1H).filter_by(asset_id=asset.id).count()
    if existing_1h == 0:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="2y", interval="1h")
            time.sleep(0.3)

            if not df.empty:
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
                result["intraday"] = len(rows)
        except Exception as e:
            result["errors"].append(f"intraday: {e}")

    session.commit()
    return result


def main():
    engine = create_engine(DB_URL)
    total_daily = 0
    total_intraday = 0

    with Session(engine) as session:
        for asset_class, symbols in NEW_ASSETS.items():
            print(f"\n{'='*60}")
            print(f"  {asset_class.value} ({len(symbols)} actifs)")
            print(f"{'='*60}")

            for symbol, name in symbols.items():
                result = load_asset_data(session, symbol, name, asset_class)
                total_daily += result["daily"]
                total_intraday += result["intraday"]

                status = ""
                if result["daily"] > 0:
                    status += f"{result['daily']}d "
                if result["intraday"] > 0:
                    status += f"{result['intraday']}h "
                if result["errors"]:
                    status += f"ERR:{result['errors']}"
                if not status:
                    status = "déjà en BDD"

                print(f"  [{symbol:12}] {name:20} → {status}")

    print(f"\n{'='*60}")
    print(f"  TOTAL : {total_daily} daily + {total_intraday} intraday")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
