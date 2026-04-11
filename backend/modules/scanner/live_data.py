"""Données live via Alpaca Data API

Récupère les prix temps réel et les dernières barres OHLCV
directement depuis Alpaca au lieu de la BDD.

Fonctionne pour :
- Actions US (AAPL, MSFT, etc.)
- ETF (SPY, QQQ, etc.)
- Crypto (BTC/USD, ETH/USD via Alpaca)

Ne fonctionne PAS pour :
- Actions EU (.PA, .DE) — pas sur Alpaca
- Forex (=X) — pas sur Alpaca
- Commodities (=F) — pas sur Alpaca
Pour ces actifs, on continue avec Yahoo Finance.
"""

import logging
from datetime import datetime, timedelta

from backend.config.settings import settings

logger = logging.getLogger("tradepilot.live_data")


def is_alpaca_symbol(symbol: str) -> bool:
    """Vérifie si le symbole est tradable sur Alpaca."""
    # Alpaca ne supporte pas les symboles avec des suffixes de marché
    if any(suffix in symbol for suffix in [".PA", ".DE", ".AS", ".SW", "=X", "=F"]):
        return False
    return True


def get_alpaca_crypto_symbol(symbol: str) -> str | None:
    """Convertit un symbole crypto Yahoo Finance en symbole Alpaca."""
    mapping = {
        "BTC-USD": "BTC/USD",
        "ETH-USD": "ETH/USD",
        "BNB-USD": None,  # Pas sur Alpaca
        "SOL-USD": "SOL/USD",
        "XRP-USD": None,  # Pas sur Alpaca
    }
    return mapping.get(symbol)


def get_live_quote(symbol: str) -> dict | None:
    """Récupère le dernier prix via Alpaca."""
    if not settings.ALPACA_API_KEY:
        return None

    try:
        if "-USD" in symbol:
            # Crypto
            alpaca_sym = get_alpaca_crypto_symbol(symbol)
            if not alpaca_sym:
                return None

            from alpaca.data.historical import CryptoHistoricalDataClient
            from alpaca.data.requests import CryptoLatestQuoteRequest

            client = CryptoHistoricalDataClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY)
            request = CryptoLatestQuoteRequest(symbol_or_symbols=alpaca_sym)
            quotes = client.get_crypto_latest_quote(request)

            if alpaca_sym in quotes:
                q = quotes[alpaca_sym]
                return {
                    "symbol": symbol,
                    "price": float(q.ask_price),
                    "bid": float(q.bid_price),
                    "ask": float(q.ask_price),
                    "timestamp": q.timestamp.isoformat() if q.timestamp else None,
                    "source": "alpaca_live",
                }
        elif is_alpaca_symbol(symbol):
            # Actions / ETF
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockLatestQuoteRequest

            client = StockHistoricalDataClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY)
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = client.get_stock_latest_quote(request)

            if symbol in quotes:
                q = quotes[symbol]
                return {
                    "symbol": symbol,
                    "price": float(q.ask_price) if q.ask_price else float(q.bid_price),
                    "bid": float(q.bid_price) if q.bid_price else 0,
                    "ask": float(q.ask_price) if q.ask_price else 0,
                    "timestamp": q.timestamp.isoformat() if q.timestamp else None,
                    "source": "alpaca_live",
                }

        return None

    except Exception as e:
        logger.warning(f"[LIVE] Erreur quote {symbol}: {e}")
        return None


def get_live_bars(symbol: str, timeframe: str = "1Day", limit: int = 100) -> list[dict] | None:
    """Récupère les dernières barres OHLCV via Alpaca."""
    if not settings.ALPACA_API_KEY:
        return None

    try:
        from alpaca.data.timeframe import TimeFrame

        tf_map = {
            "1Min": TimeFrame.Minute,
            "5Min": TimeFrame(5, "Min"),
            "1Hour": TimeFrame.Hour,
            "1Day": TimeFrame.Day,
        }
        tf = tf_map.get(timeframe, TimeFrame.Day)
        start = datetime.now() - timedelta(days=limit * 2)

        if "-USD" in symbol:
            alpaca_sym = get_alpaca_crypto_symbol(symbol)
            if not alpaca_sym:
                return None

            from alpaca.data.historical import CryptoHistoricalDataClient
            from alpaca.data.requests import CryptoBarsRequest

            client = CryptoHistoricalDataClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY)
            request = CryptoBarsRequest(
                symbol_or_symbols=alpaca_sym,
                timeframe=tf,
                start=start,
                limit=limit,
            )
            bars = client.get_crypto_bars(request)
            bar_list = bars[alpaca_sym] if alpaca_sym in bars else []

        elif is_alpaca_symbol(symbol):
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockBarsRequest

            client = StockHistoricalDataClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY)
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=tf,
                start=start,
                limit=limit,
            )
            bars = client.get_stock_bars(request)
            bar_list = bars[symbol] if symbol in bars else []
        else:
            return None

        return [
            {
                "date": bar.timestamp.strftime("%Y-%m-%d") if hasattr(bar.timestamp, 'strftime') else str(bar.timestamp)[:10],
                "datetime": bar.timestamp.isoformat() if hasattr(bar.timestamp, 'isoformat') else str(bar.timestamp),
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": int(bar.volume),
                "source": "alpaca_live",
            }
            for bar in bar_list
        ]

    except Exception as e:
        logger.warning(f"[LIVE] Erreur bars {symbol}: {e}")
        return None
