"""Chargement étendu : ~175 actifs supplémentaires

Actions US Top 100, Actions EU Top 50, Crypto Top 20,
Indices mondiaux, ETF sectoriels
"""

import sys
import time
sys.path.insert(0, ".")

import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily, OHLCV1H, AssetClass

DB_URL = "postgresql://tradepilot:tradepilot_dev@localhost:5432/tradepilot"

EXTENDED_ASSETS = {
    # === ACTIONS US — Top 100 (hors ceux déjà en base) ===
    AssetClass.ACTION_US: {
        # Tech
        "AMD": "AMD",
        "INTC": "Intel",
        "AVGO": "Broadcom",
        "CRM": "Salesforce",
        "ORCL": "Oracle",
        "ADBE": "Adobe",
        "CSCO": "Cisco",
        "QCOM": "Qualcomm",
        "TXN": "Texas Instruments",
        "AMAT": "Applied Materials",
        "MU": "Micron Technology",
        "LRCX": "Lam Research",
        "KLAC": "KLA Corp",
        "SNPS": "Synopsys",
        "CDNS": "Cadence Design",
        "MRVL": "Marvell Technology",
        "NOW": "ServiceNow",
        "PANW": "Palo Alto Networks",
        "CRWD": "CrowdStrike",
        "ZS": "Zscaler",
        "DDOG": "Datadog",
        "SNOW": "Snowflake",
        "NET": "Cloudflare",
        "SHOP": "Shopify",
        "SQ": "Block (Square)",
        "COIN": "Coinbase",
        "PLTR": "Palantir",
        "U": "Unity Software",
        "RBLX": "Roblox",
        "UBER": "Uber",
        "LYFT": "Lyft",
        "ABNB": "Airbnb",
        "DASH": "DoorDash",
        # Finance
        "GS": "Goldman Sachs",
        "MS": "Morgan Stanley",
        "BAC": "Bank of America",
        "C": "Citigroup",
        "WFC": "Wells Fargo",
        "AXP": "American Express",
        "BLK": "BlackRock",
        "SCHW": "Charles Schwab",
        "MA": "Mastercard",
        "PYPL": "PayPal",
        # Santé
        "UNH": "UnitedHealth",
        "LLY": "Eli Lilly",
        "PFE": "Pfizer",
        "ABBV": "AbbVie",
        "MRK": "Merck",
        "TMO": "Thermo Fisher",
        "ABT": "Abbott Labs",
        "BMY": "Bristol-Myers",
        "AMGN": "Amgen",
        "GILD": "Gilead",
        "ISRG": "Intuitive Surgical",
        "MRNA": "Moderna",
        # Consommation
        "WMT": "Walmart",
        "COST": "Costco",
        "HD": "Home Depot",
        "LOW": "Lowe's",
        "TGT": "Target",
        "NKE": "Nike",
        "SBUX": "Starbucks",
        "MCD": "McDonald's",
        "KO": "Coca-Cola",
        "PEP": "PepsiCo",
        "PG": "Procter & Gamble",
        "CL": "Colgate-Palmolive",
        # Industrie / Énergie
        "XOM": "ExxonMobil",
        "CVX": "Chevron",
        "COP": "ConocoPhillips",
        "NEE": "NextEra Energy",
        "DUK": "Duke Energy",
        "SO": "Southern Company",
        "BA": "Boeing",
        "LMT": "Lockheed Martin",
        "RTX": "RTX (Raytheon)",
        "GE": "GE Aerospace",
        "CAT": "Caterpillar",
        "DE": "Deere & Company",
        "UPS": "UPS",
        "FDX": "FedEx",
        # Télécom / Médias
        "DIS": "Walt Disney",
        "NFLX": "Netflix",
        "CMCSA": "Comcast",
        "T": "AT&T",
        "VZ": "Verizon",
        "TMUS": "T-Mobile",
        # Meme / Retail favorites
        "GME": "GameStop",
        "AMC": "AMC Entertainment",
        "RIVN": "Rivian",
        "LCID": "Lucid Motors",
        "NIO": "NIO",
    },
    # === ACTIONS EU — Top 40 supplémentaires ===
    AssetClass.ACTION_EU: {
        "TTE.PA": "TotalEnergies",
        "DG.PA": "Vinci",
        "DSY.PA": "Dassault Systèmes",
        "HO.PA": "Thales",
        "SGO.PA": "Saint-Gobain",
        "SU.PA": "Schneider Electric",
        "RI.PA": "Pernod Ricard",
        "CAP.PA": "Capgemini",
        "CS.PA": "AXA",
        "EN.PA": "Bouygues",
        "ALV.DE": "Allianz",
        "DTE.DE": "Deutsche Telekom",
        "BAS.DE": "BASF",
        "BMW.DE": "BMW",
        "MBG.DE": "Mercedes-Benz",
        "VOW3.DE": "Volkswagen",
        "DB1.DE": "Deutsche Börse",
        "MRK.DE": "Merck KGaA",
        "ADS.DE": "Adidas",
        "IFX.DE": "Infineon",
        "PHIA.AS": "Philips",
        "AD.AS": "Ahold Delhaize",
        "INGA.AS": "ING Group",
        "UNA.AS": "Unilever",
        "NOVN.SW": "Novartis",
        "ZURN.SW": "Zurich Insurance",
        "UBSG.SW": "UBS",
        "ABBN.SW": "ABB",
        "RACE.MI": "Ferrari",
        "ISP.MI": "Intesa Sanpaolo",
        "NOVO-B.CO": "Novo Nordisk",
        "MAERSK-B.CO": "Maersk",
        "SHEL.L": "Shell",
        "AZN.L": "AstraZeneca",
        "HSBA.L": "HSBC",
        "BP.L": "BP",
        "RIO.L": "Rio Tinto",
        "GSK.L": "GSK",
        "ULVR.L": "Unilever UK",
        "LSEG.L": "London Stock Exchange",
    },
    # === CRYPTO — Top 15 supplémentaires ===
    AssetClass.CRYPTO: {
        "DOGE-USD": "Dogecoin",
        "ADA-USD": "Cardano",
        "AVAX-USD": "Avalanche",
        "DOT-USD": "Polkadot",
        "LINK-USD": "Chainlink",
        "MATIC-USD": "Polygon",
        "UNI-USD": "Uniswap",
        "ATOM-USD": "Cosmos",
        "LTC-USD": "Litecoin",
        "FIL-USD": "Filecoin",
        "AAVE-USD": "Aave",
        "NEAR-USD": "NEAR Protocol",
        "ARB-USD": "Arbitrum",
        "OP-USD": "Optimism",
        "APT-USD": "Aptos",
    },
    # === ETF SECTORIELS ===
    AssetClass.ETF: {
        "XLF": "Financial Select SPDR",
        "XLE": "Energy Select SPDR",
        "XLK": "Technology Select SPDR",
        "XLV": "Health Care Select SPDR",
        "XLI": "Industrial Select SPDR",
        "XLP": "Consumer Staples SPDR",
        "XLY": "Consumer Discretionary SPDR",
        "XLU": "Utilities Select SPDR",
        "XLB": "Materials Select SPDR",
        "XLRE": "Real Estate Select SPDR",
        "ARKK": "ARK Innovation",
        "ARKG": "ARK Genomic",
        "SOXX": "iShares Semiconductor",
        "EEM": "iShares Emerging Markets",
        "EFA": "iShares EAFE",
        "HYG": "iShares High Yield",
        "LQD": "iShares Investment Grade",
        "SLV": "iShares Silver",
        "USO": "United States Oil",
        "UNG": "United States Natural Gas",
    },
}


def load_asset(session, symbol, name, asset_class):
    """Crée l'actif et charge daily (pas intraday pour gagner du temps)."""
    existing = session.query(Asset).filter_by(symbol=symbol).first()
    if existing:
        return {"symbol": symbol, "status": "exists", "daily": 0}

    asset = Asset(symbol=symbol, name=name, asset_class=asset_class, is_active=True)
    session.add(asset)
    session.flush()

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2y", interval="1d")
        time.sleep(0.3)
    except Exception as e:
        session.commit()
        return {"symbol": symbol, "status": f"error: {e}", "daily": 0}

    if df.empty:
        session.commit()
        return {"symbol": symbol, "status": "no_data", "daily": 0}

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
    return {"symbol": symbol, "status": "ok", "daily": len(rows)}


def main():
    engine = create_engine(DB_URL)
    total = 0
    errors = 0

    with Session(engine) as session:
        for asset_class, symbols in EXTENDED_ASSETS.items():
            print(f"\n{'='*60}")
            print(f"  {asset_class.value} ({len(symbols)} actifs)")
            print(f"{'='*60}")

            for symbol, name in symbols.items():
                result = load_asset(session, symbol, name, asset_class)
                total += result["daily"]
                status = result["status"]

                if status == "ok":
                    print(f"  [{symbol:12}] {name:25} {result['daily']}d")
                elif status == "exists":
                    print(f"  [{symbol:12}] déjà en BDD")
                else:
                    print(f"  [{symbol:12}] {status}")
                    errors += 1

    # Compter le total en BDD
    with Session(engine) as session:
        total_assets = session.query(Asset).filter_by(is_active=True).count()
        total_daily = session.query(OHLCVDaily).count()

    print(f"\n{'='*60}")
    print(f"  RÉSULTAT")
    print(f"  Nouvelles barres : {total}")
    print(f"  Erreurs : {errors}")
    print(f"  Total actifs en BDD : {total_assets}")
    print(f"  Total barres daily : {total_daily}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
