"""Broker Alpaca — Paper Trading & Live Trading

Alpaca API pour :
- Passer des ordres (market, limit, stop, stop_limit)
- Récupérer les positions ouvertes
- Récupérer l'historique des ordres
- Données temps réel (dernier prix)

Mode paper : https://paper-api.alpaca.markets
Mode live : https://api.alpaca.markets
"""

import logging
from datetime import datetime

from backend.config.settings import settings

logger = logging.getLogger("tradepilot.broker.alpaca")


class AlpacaBroker:
    """Client Alpaca pour le paper trading et le live trading."""

    def __init__(self):
        self.api_key = settings.ALPACA_API_KEY
        self.secret_key = settings.ALPACA_SECRET_KEY
        self.base_url = settings.ALPACA_BASE_URL
        self._client = None
        self._trading_client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.secret_key)

    def _get_trading_client(self):
        """Lazy init du client de trading."""
        if self._trading_client is None:
            if not self.is_configured:
                raise ValueError("Alpaca API non configuré — ajoutez ALPACA_API_KEY et ALPACA_SECRET_KEY dans .env")
            from alpaca.trading.client import TradingClient
            self._trading_client = TradingClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
                paper=("paper" in self.base_url),
            )
        return self._trading_client

    def get_account(self) -> dict:
        """Récupère les infos du compte."""
        client = self._get_trading_client()
        account = client.get_account()
        return {
            "id": str(account.id),
            "status": account.status.value if hasattr(account.status, 'value') else str(account.status),
            "equity": float(account.equity),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "portfolio_value": float(account.portfolio_value),
            "currency": account.currency,
            "paper": "paper" in self.base_url,
        }

    def place_order(self, symbol: str, side: str, quantity: float,
                    order_type: str = "market", limit_price: float = None,
                    stop_price: float = None, time_in_force: str = "day") -> dict:
        """Place un ordre via Alpaca."""
        from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest, StopLimitOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce

        client = self._get_trading_client()
        alpaca_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
        tif = TimeInForce.DAY if time_in_force == "day" else TimeInForce.GTC

        try:
            if order_type == "market":
                request = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=alpaca_side,
                    time_in_force=tif,
                )
            elif order_type == "limit":
                request = LimitOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=alpaca_side,
                    time_in_force=tif,
                    limit_price=limit_price,
                )
            elif order_type == "stop":
                request = StopOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=alpaca_side,
                    time_in_force=tif,
                    stop_price=stop_price,
                )
            elif order_type == "stop_limit":
                request = StopLimitOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=alpaca_side,
                    time_in_force=tif,
                    limit_price=limit_price,
                    stop_price=stop_price,
                )
            else:
                return {"error": f"Type d'ordre inconnu: {order_type}"}

            order = client.submit_order(request)
            logger.info(f"[ALPACA] Ordre placé: {side} {quantity} {symbol} ({order_type}) → {order.id}")

            return {
                "broker_order_id": str(order.id),
                "symbol": symbol,
                "side": side,
                "quantity": float(quantity),
                "order_type": order_type,
                "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
                "limit_price": limit_price,
                "stop_price": stop_price,
                "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
            }

        except Exception as e:
            logger.error(f"[ALPACA] Erreur placement ordre: {e}")
            return {"error": str(e)}

    def get_positions(self) -> list[dict]:
        """Récupère les positions ouvertes."""
        client = self._get_trading_client()
        positions = client.get_all_positions()

        return [
            {
                "symbol": p.symbol,
                "quantity": float(p.qty),
                "side": p.side.value if hasattr(p.side, 'value') else str(p.side),
                "entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "market_value": float(p.market_value),
                "pnl": float(p.unrealized_pl),
                "pnl_pct": float(p.unrealized_plpc) * 100,
            }
            for p in positions
        ]

    def get_orders(self, status: str = "all", limit: int = 50) -> list[dict]:
        """Récupère les ordres récents."""
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus

        client = self._get_trading_client()
        status_map = {
            "all": QueryOrderStatus.ALL,
            "open": QueryOrderStatus.OPEN,
            "closed": QueryOrderStatus.CLOSED,
        }
        request = GetOrdersRequest(
            status=status_map.get(status, QueryOrderStatus.ALL),
            limit=limit,
        )
        orders = client.get_orders(request)

        return [
            {
                "id": str(o.id),
                "symbol": o.symbol,
                "side": o.side.value if hasattr(o.side, 'value') else str(o.side),
                "quantity": float(o.qty) if o.qty else 0,
                "filled_qty": float(o.filled_qty) if o.filled_qty else 0,
                "order_type": o.order_type.value if hasattr(o.order_type, 'value') else str(o.order_type),
                "status": o.status.value if hasattr(o.status, 'value') else str(o.status),
                "limit_price": float(o.limit_price) if o.limit_price else None,
                "stop_price": float(o.stop_price) if o.stop_price else None,
                "filled_avg_price": float(o.filled_avg_price) if o.filled_avg_price else None,
                "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None,
                "filled_at": o.filled_at.isoformat() if o.filled_at else None,
            }
            for o in orders
        ]

    def cancel_order(self, order_id: str) -> dict:
        """Annule un ordre."""
        client = self._get_trading_client()
        try:
            client.cancel_order_by_id(order_id)
            return {"status": "cancelled", "order_id": order_id}
        except Exception as e:
            return {"error": str(e)}

    def close_position(self, symbol: str) -> dict:
        """Ferme une position."""
        client = self._get_trading_client()
        try:
            client.close_position(symbol)
            return {"status": "closed", "symbol": symbol}
        except Exception as e:
            return {"error": str(e)}

    def get_last_price(self, symbol: str) -> float | None:
        """Récupère le dernier prix via Alpaca Data API."""
        try:
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockLatestQuoteRequest

            data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = data_client.get_stock_latest_quote(request)

            if symbol in quote:
                return float(quote[symbol].ask_price)
            return None
        except Exception as e:
            logger.warning(f"[ALPACA] Erreur prix {symbol}: {e}")
            return None


# Singleton
alpaca_broker = AlpacaBroker()
