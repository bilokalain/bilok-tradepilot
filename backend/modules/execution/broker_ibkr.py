"""Broker Interactive Brokers — Live Trading via ib_insync

Même interface que AlpacaBroker pour une intégration transparente.
Supporte tous les marchés : actions US/EU, ETF, forex, crypto, commodities.

Prérequis :
- pip install ib_insync
- TWS ou IB Gateway en cours d'exécution
- Port 7496 (live) ou 7497 (paper)
"""

import logging
from datetime import datetime

from backend.config.settings import settings

logger = logging.getLogger("tradepilot.broker.ibkr")

# Client IDs centralisés — chaque usage a un ID unique pour éviter les déconnexions
IBKR_CLIENT_IDS = {
    "broker": 1,        # Singleton ibkr_broker
    "monitor": 10,      # TP/SL monitor
    "queue_buy": 11,    # Achat depuis la queue
}


# Mapping des symboles TradePilot → contrats IBKR
SYMBOL_MAPPING = {
    # Crypto (format Yahoo → IBKR)
    "BTC-USD": ("BTC", "CRYPTO", "PAXOS", "USD"),
    "ETH-USD": ("ETH", "CRYPTO", "PAXOS", "USD"),
    "SOL-USD": ("SOL", "CRYPTO", "PAXOS", "USD"),
    # Forex
    "EURUSD=X": ("EUR", "CASH", "IDEALPRO", "USD"),
    "GBPUSD=X": ("GBP", "CASH", "IDEALPRO", "USD"),
    "USDJPY=X": ("USD", "CASH", "IDEALPRO", "JPY"),
    # Commodities (futures)
    "GC=F": ("GC", "FUT", "COMEX", "USD"),
    "CL=F": ("CL", "FUT", "NYMEX", "USD"),
    "SI=F": ("SI", "FUT", "COMEX", "USD"),
    "HG=F": ("HG", "FUT", "COMEX", "USD"),
    # Actions EU
    "BNP.PA": ("BNP", "STK", "SBF", "EUR"),
    "MC.PA": ("MC", "STK", "SBF", "EUR"),
    "OR.PA": ("OR", "STK", "SBF", "EUR"),
    "SAN.PA": ("SAN", "STK", "SBF", "EUR"),
    "AI.PA": ("AI", "STK", "SBF", "EUR"),
    "RMS.PA": ("RMS", "STK", "SBF", "EUR"),
    "TTE.PA": ("TTE", "STK", "SBF", "EUR"),
    "SAP.DE": ("SAP", "STK", "IBIS", "EUR"),
    "SIE.DE": ("SIE", "STK", "IBIS", "EUR"),
    "ALV.DE": ("ALV", "STK", "IBIS", "EUR"),
    "NESN.SW": ("NESN", "STK", "SWX", "CHF"),
    "ROG.SW": ("ROG", "STK", "SWX", "CHF"),
    "NOVN.SW": ("NOVN", "STK", "SWX", "CHF"),
    "AZN.L": ("AZN", "STK", "LSE", "GBP"),
    "SHEL.L": ("SHEL", "STK", "LSE", "GBP"),
    "HSBA.L": ("HSBA", "STK", "LSE", "GBP"),
}


class IBKRBroker:
    """Client Interactive Brokers via ib_insync — même interface qu'AlpacaBroker."""

    def __init__(self):
        self.host = settings.IBKR_HOST
        self.port = settings.IBKR_PORT
        self.client_id = settings.IBKR_CLIENT_ID
        self.account_id = settings.IBKR_ACCOUNT_ID
        self._ib = None

    @property
    def is_configured(self) -> bool:
        return bool(self.account_id)

    def _connect(self):
        """Connexion lazy à TWS/IB Gateway."""
        if self._ib is not None and self._ib.isConnected():
            return self._ib
        try:
            from ib_insync import IB
            self._ib = IB()
            self._ib.connect(self.host, self.port, clientId=self.client_id, timeout=10)
            logger.info(f"[IBKR] Connecté à {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"[IBKR] Connexion échouée: {e}")
            self._ib = None
            raise
        return self._ib

    @property
    def is_connected(self) -> bool:
        return self._ib is not None and self._ib.isConnected()

    def _make_contract(self, symbol: str):
        """Crée un contrat IBKR à partir d'un symbole TradePilot."""
        from ib_insync import Stock, Forex, Future, Crypto

        # Mapping connu
        if symbol in SYMBOL_MAPPING:
            sym, sec_type, exchange, currency = SYMBOL_MAPPING[symbol]
            if sec_type == "STK":
                return Stock(sym, exchange, currency)
            elif sec_type == "CASH":
                return Forex(f"{sym}{currency}")
            elif sec_type == "FUT":
                return Future(sym, exchange=exchange, currency=currency)
            elif sec_type == "CRYPTO":
                return Crypto(sym, exchange, currency)

        # Actions US par défaut (SMART routing)
        return Stock(symbol, "SMART", "USD")

    def get_account(self) -> dict:
        """Récupère les infos du compte."""
        ib = self._connect()
        summary = ib.accountSummary(self.account_id)

        values = {}
        for item in summary:
            values[item.tag] = item.value

        equity = float(values.get("NetLiquidation", 0))
        cash = float(values.get("TotalCashValue", 0))

        return {
            "id": self.account_id,
            "status": "ACTIVE",
            "equity": equity,
            "cash": cash,
            "buying_power": float(values.get("BuyingPower", 0)),
            "portfolio_value": equity,
            "currency": values.get("Currency", "EUR"),
            "paper": self.port == 7497,
        }

    def place_order(self, symbol: str, side: str, quantity: float,
                    order_type: str = "market", limit_price: float = None,
                    stop_price: float = None, time_in_force: str = "day",
                    cash_qty: float = None) -> dict:
        """Place un ordre via IBKR. Supporte les fractional shares via cash_qty."""
        from ib_insync import MarketOrder, LimitOrder, StopOrder, StopLimitOrder, Order as IBOrder

        ib = self._connect()
        contract = self._make_contract(symbol)

        # Qualifier le contrat (résoudre les détails)
        try:
            ib.qualifyContracts(contract)
        except Exception as e:
            return {"error": f"Contrat non trouvé pour {symbol}: {e}"}

        action = "BUY" if side.upper() == "BUY" else "SELL"

        try:
            # Fractional shares : utiliser cashQty au lieu de qty
            if cash_qty and cash_qty > 0 and order_type == "market":
                order = IBOrder()
                order.action = action
                order.orderType = "MKT"
                order.cashQty = round(cash_qty, 2)
                order.tif = "DAY"
                logger.info(f"[IBKR] Fractional order: {action} ${cash_qty:.2f} of {symbol}")
            elif order_type == "market":
                order = MarketOrder(action, quantity)
            elif order_type == "limit":
                order = LimitOrder(action, quantity, limit_price)
            elif order_type == "stop":
                order = StopOrder(action, quantity, stop_price)
            elif order_type == "stop_limit":
                order = StopLimitOrder(action, quantity, limit_price, stop_price)
            else:
                return {"error": f"Type d'ordre inconnu: {order_type}"}

            if time_in_force == "gtc":
                order.tif = "GTC"

            trade = ib.placeOrder(contract, order)
            ib.sleep(1)  # Attendre confirmation

            logger.info(f"[IBKR] Ordre placé: {action} {quantity} {symbol} ({order_type}) → {trade.order.orderId}")

            return {
                "broker_order_id": str(trade.order.orderId),
                "symbol": symbol,
                "side": side.upper(),
                "quantity": float(quantity),
                "order_type": order_type,
                "status": trade.orderStatus.status,
                "limit_price": limit_price,
                "stop_price": stop_price,
                "submitted_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"[IBKR] Erreur placement ordre: {e}")
            return {"error": str(e)}

    def get_positions(self) -> list[dict]:
        """Récupère les positions ouvertes."""
        ib = self._connect()
        positions = ib.positions(self.account_id)

        result = []
        for pos in positions:
            if pos.position == 0:
                continue

            symbol = pos.contract.symbol
            # Reconvertir vers le format TradePilot si nécessaire
            tp_symbol = self._ibkr_to_tp_symbol(pos.contract)

            # Prix actuel
            current_price = self._get_market_price(pos.contract)
            entry_price = pos.avgCost
            quantity = abs(pos.position)
            market_value = quantity * current_price if current_price else 0
            pnl = (current_price - entry_price) * pos.position if current_price else 0
            pnl_pct = ((current_price / entry_price) - 1) * 100 if entry_price and current_price else 0

            result.append({
                "symbol": tp_symbol,
                "quantity": float(quantity),
                "side": "long" if pos.position > 0 else "short",
                "entry_price": float(entry_price),
                "current_price": float(current_price) if current_price else 0,
                "market_value": float(market_value),
                "pnl": round(float(pnl), 2),
                "pnl_pct": round(float(pnl_pct), 2),
            })

        return result

    def get_orders(self, status: str = "all", limit: int = 50) -> list[dict]:
        """Récupère les ordres récents."""
        ib = self._connect()

        if status == "open":
            orders = ib.openOrders()
        else:
            orders = ib.reqAllOpenOrders()
            # IBKR ne fournit pas facilement l'historique complet via ib_insync
            # Les ordres fermés sont dans les trades
            trades = ib.trades()
            orders = [t.order for t in trades[-limit:]]

        result = []
        for trade in ib.trades()[-limit:]:
            o = trade.order
            status_str = trade.orderStatus.status if trade.orderStatus else "Unknown"
            result.append({
                "id": str(o.orderId),
                "symbol": trade.contract.symbol,
                "side": o.action.lower(),
                "quantity": float(o.totalQuantity),
                "filled_qty": float(trade.orderStatus.filled) if trade.orderStatus else 0,
                "order_type": o.orderType.lower(),
                "status": status_str.lower(),
                "limit_price": float(o.lmtPrice) if o.lmtPrice else None,
                "stop_price": float(o.auxPrice) if o.auxPrice else None,
                "filled_avg_price": float(trade.orderStatus.avgFillPrice) if trade.orderStatus and trade.orderStatus.avgFillPrice else None,
                "submitted_at": datetime.utcnow().isoformat(),
                "filled_at": None,
            })

        return result

    def cancel_order(self, order_id: str) -> dict:
        """Annule un ordre."""
        ib = self._connect()
        try:
            for trade in ib.trades():
                if str(trade.order.orderId) == order_id:
                    ib.cancelOrder(trade.order)
                    return {"status": "cancelled", "order_id": order_id}
            return {"error": f"Ordre {order_id} non trouvé"}
        except Exception as e:
            return {"error": str(e)}

    def place_bracket_order(self, symbol: str, side: str, quantity: float,
                            stop_loss: float, take_profit: float) -> dict:
        """Place un bracket order IBKR : entry + SL + TP côté serveur.

        Les ordres SL/TP restent actifs chez IBKR même si le terminal tombe.
        C'est l'équivalent des bracket orders Alpaca.
        """
        from ib_insync import MarketOrder, StopOrder, LimitOrder

        ib = self._connect()
        contract = self._make_contract(symbol)

        try:
            ib.qualifyContracts(contract)
        except Exception as e:
            return {"error": f"Contrat non trouvé pour {symbol}: {e}"}

        action = "BUY" if side.upper() in ("BUY", "LONG") else "SELL"
        reverse = "SELL" if action == "BUY" else "BUY"

        try:
            # Ordre parent : entrée au marché
            parent = MarketOrder(action, quantity)
            parent.orderId = ib.client.getReqId()
            parent.transmit = False  # Ne pas transmettre avant les enfants

            # Ordre enfant 1 : Take Profit (limit)
            tp_order = LimitOrder(reverse, quantity, round(take_profit, 2))
            tp_order.orderId = ib.client.getReqId()
            tp_order.parentId = parent.orderId
            tp_order.transmit = False

            # Ordre enfant 2 : Stop Loss (stop)
            sl_order = StopOrder(reverse, quantity, round(stop_loss, 2))
            sl_order.orderId = ib.client.getReqId()
            sl_order.parentId = parent.orderId
            sl_order.transmit = True  # Transmettre tout le groupe (OCA)

            # Placer les 3 ordres
            parent_trade = ib.placeOrder(contract, parent)
            ib.placeOrder(contract, tp_order)
            ib.placeOrder(contract, sl_order)
            ib.sleep(2)

            logger.info(
                f"[IBKR] Bracket order: {action} {quantity} {symbol} "
                f"SL=${stop_loss:.2f} TP=${take_profit:.2f} → parent={parent.orderId}"
            )

            return {
                "broker_order_id": str(parent.orderId),
                "symbol": symbol,
                "side": side.upper(),
                "quantity": float(quantity),
                "order_type": "bracket",
                "status": parent_trade.orderStatus.status,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "sl_order_id": str(sl_order.orderId),
                "tp_order_id": str(tp_order.orderId),
                "submitted_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"[IBKR] Erreur bracket order {symbol}: {e}")
            # Fallback : ordre market simple (sans protection)
            try:
                fallback = MarketOrder(action, quantity)
                trade = ib.placeOrder(contract, fallback)
                ib.sleep(1)
                logger.warning(f"[IBKR] Fallback market order pour {symbol} (bracket échoué)")
                return {
                    "broker_order_id": str(trade.order.orderId),
                    "symbol": symbol,
                    "side": side.upper(),
                    "quantity": float(quantity),
                    "order_type": "market_fallback",
                    "status": trade.orderStatus.status,
                    "submitted_at": datetime.utcnow().isoformat(),
                    "warning": f"Bracket échoué, market order utilisé: {e}",
                }
            except Exception as e2:
                logger.error(f"[IBKR] Fallback market aussi échoué {symbol}: {e2}")
                return {"error": f"Bracket et fallback échoués: {e2}"}

    def close_position(self, symbol: str) -> dict:
        """Ferme une position."""
        ib = self._connect()
        try:
            contract = self._make_contract(symbol)
            ib.qualifyContracts(contract)

            for pos in ib.positions(self.account_id):
                if pos.contract.symbol == contract.symbol and pos.position != 0:
                    side = "SELL" if pos.position > 0 else "BUY"
                    from ib_insync import MarketOrder
                    order = MarketOrder(side, abs(pos.position))
                    ib.placeOrder(contract, order)
                    return {"status": "closed", "symbol": symbol}

            return {"error": f"Aucune position ouverte pour {symbol}"}
        except Exception as e:
            return {"error": str(e)}

    def get_last_price(self, symbol: str) -> float | None:
        """Récupère le dernier prix."""
        try:
            contract = self._make_contract(symbol)
            return self._get_market_price(contract)
        except Exception as e:
            logger.warning(f"[IBKR] Erreur prix {symbol}: {e}")
            return None

    def _get_market_price(self, contract) -> float | None:
        """Récupère le prix marché d'un contrat."""
        ib = self._connect()
        try:
            ib.qualifyContracts(contract)
            [ticker] = ib.reqTickers(contract)
            if ticker.marketPrice():
                return float(ticker.marketPrice())
            if ticker.close:
                return float(ticker.close)
            return None
        except Exception as e:
            logger.warning(f"[IBKR] Erreur récupération prix marché pour {contract.symbol}: {e}")
            return None

    def _ibkr_to_tp_symbol(self, contract) -> str:
        """Convertit un contrat IBKR vers un symbole TradePilot."""
        # Chercher dans le mapping inverse
        for tp_sym, (ibkr_sym, sec_type, exchange, currency) in SYMBOL_MAPPING.items():
            if contract.symbol == ibkr_sym and contract.secType == sec_type:
                return tp_sym

        # Actions US : retourner tel quel
        if contract.secType == "STK" and contract.currency == "USD":
            return contract.symbol

        # Fallback
        return contract.symbol


# Singleton
ibkr_broker = IBKRBroker()
