"""Multi-Broker — Exécute sur IBKR (live) + Alpaca (paper) en parallèle

Stratégie :
- IBKR = broker principal (argent réel)
- Alpaca = mirror paper trading (validation)
- Chaque ordre est envoyé aux DEUX brokers
- Les positions live viennent d'IBKR
- Les positions paper viennent d'Alpaca
- Si IBKR est down, on continue en paper-only sur Alpaca
"""

import logging
from typing import Optional

logger = logging.getLogger("tradepilot.broker.multi")


class MultiBroker:
    """Routeur multi-broker : IBKR (live) + Alpaca (paper)."""

    def __init__(self):
        from backend.modules.execution.broker_alpaca import alpaca_broker
        from backend.modules.execution.broker_ibkr import ibkr_broker

        self.ibkr = ibkr_broker
        self.alpaca = alpaca_broker

    @property
    def is_configured(self) -> bool:
        """Au moins un broker doit être configuré."""
        return self.ibkr.is_configured or self.alpaca.is_configured

    @property
    def ibkr_live(self) -> bool:
        """IBKR est-il connecté en live ?"""
        if not self.ibkr.is_configured:
            return False
        if self.ibkr.is_connected:
            return True
        try:
            self.ibkr._connect()
            return self.ibkr.is_connected
        except Exception as e:
            logger.warning(f"[MULTI] IBKR connexion échouée: {e}")
            return False

    @property
    def mode(self) -> str:
        """Mode actuel : DUAL, IBKR_ONLY, ALPACA_ONLY, NONE."""
        ibkr_ok = self.ibkr_live
        alpaca_ok = self.alpaca.is_configured
        if ibkr_ok and alpaca_ok:
            return "DUAL"
        elif ibkr_ok:
            return "IBKR_ONLY"
        elif alpaca_ok:
            return "ALPACA_ONLY"
        return "NONE"

    def get_account(self) -> dict:
        """Compte principal = IBKR si dispo, sinon Alpaca."""
        if self.ibkr_live:
            try:
                acct = self.ibkr.get_account()
                acct["broker"] = "ibkr"
                acct["mode"] = self.mode
                return acct
            except Exception as e:
                logger.warning(f"[MULTI] IBKR account failed: {e}")

        if self.alpaca.is_configured:
            acct = self.alpaca.get_account()
            acct["broker"] = "alpaca"
            acct["mode"] = self.mode
            return acct

        return {"error": "Aucun broker configuré", "mode": "NONE"}

    def place_order(self, symbol: str, side: str, quantity: float,
                    order_type: str = "market", limit_price: float = None,
                    stop_price: float = None, time_in_force: str = "day") -> dict:
        """Place l'ordre sur les deux brokers en parallèle."""
        results = {"ibkr": None, "alpaca": None, "primary": None}

        # 1. IBKR (live) — prioritaire
        if self.ibkr_live:
            try:
                ibkr_result = self.ibkr.place_order(
                    symbol, side, quantity, order_type,
                    limit_price, stop_price, time_in_force
                )
                results["ibkr"] = ibkr_result
                if "error" not in ibkr_result:
                    results["primary"] = "ibkr"
                    logger.info(f"[MULTI] IBKR OK: {side} {quantity} {symbol}")
                else:
                    logger.warning(f"[MULTI] IBKR erreur: {ibkr_result['error']}")
            except Exception as e:
                logger.error(f"[MULTI] IBKR exception: {e}")
                results["ibkr"] = {"error": str(e)}

        # 2. Alpaca (paper mirror) — toujours essayer
        if self.alpaca.is_configured:
            # Pour Alpaca, ne trader que les actifs US supportés
            if self._alpaca_supports(symbol):
                try:
                    alpaca_symbol = self._to_alpaca_symbol(symbol)
                    alpaca_result = self.alpaca.place_order(
                        alpaca_symbol, side, quantity, order_type,
                        limit_price, stop_price, time_in_force
                    )
                    results["alpaca"] = alpaca_result
                    if results["primary"] is None and "error" not in alpaca_result:
                        results["primary"] = "alpaca"
                    logger.info(f"[MULTI] Alpaca mirror: {side} {quantity} {alpaca_symbol}")
                except Exception as e:
                    results["alpaca"] = {"error": str(e)}
            else:
                results["alpaca"] = {"skipped": f"{symbol} non supporté par Alpaca"}

        # Résultat combiné
        primary = results.get(results.get("primary", ""), {})
        return {
            **primary,
            "broker": results["primary"] or "none",
            "mode": self.mode,
            "mirror": results,
        }

    def get_positions(self, source: str = "auto") -> list[dict]:
        """Positions — IBKR live par défaut, Alpaca en fallback.

        Args:
            source: "ibkr", "alpaca", "both", ou "auto" (IBKR si dispo)
        """
        if source == "both":
            return self._get_all_positions()

        if source == "ibkr" or (source == "auto" and self.ibkr_live):
            try:
                positions = self.ibkr.get_positions()
                for p in positions:
                    p["broker"] = "ibkr"
                return positions
            except Exception as e:
                logger.warning(f"[MULTI] IBKR positions failed: {e}")

        if self.alpaca.is_configured:
            positions = self.alpaca.get_positions()
            for p in positions:
                p["broker"] = "alpaca"
            return positions

        return []

    def _get_all_positions(self) -> list[dict]:
        """Positions combinées des deux brokers."""
        positions = []

        if self.ibkr_live:
            try:
                for p in self.ibkr.get_positions():
                    p["broker"] = "ibkr"
                    positions.append(p)
            except Exception as e:
                logger.warning(f"[MULTI] IBKR positions failed in _get_all_positions: {e}")

        if self.alpaca.is_configured:
            for p in self.alpaca.get_positions():
                p["broker"] = "alpaca"
                positions.append(p)

        return positions

    def get_orders(self, status: str = "all", limit: int = 50) -> list[dict]:
        """Ordres du broker principal."""
        if self.ibkr_live:
            try:
                orders = self.ibkr.get_orders(status, limit)
                for o in orders:
                    o["broker"] = "ibkr"
                return orders
            except Exception as e:
                logger.warning(f"[MULTI] IBKR orders failed, falling back to Alpaca: {e}")

        if self.alpaca.is_configured:
            orders = self.alpaca.get_orders(status, limit)
            for o in orders:
                o["broker"] = "alpaca"
            return orders

        return []

    def cancel_order(self, order_id: str, broker: str = "auto") -> dict:
        """Annule un ordre sur le broker spécifié."""
        if broker == "ibkr" or (broker == "auto" and self.ibkr_live):
            return self.ibkr.cancel_order(order_id)
        return self.alpaca.cancel_order(order_id)

    def close_position(self, symbol: str) -> dict:
        """Ferme une position sur les deux brokers."""
        results = {}

        if self.ibkr_live:
            try:
                results["ibkr"] = self.ibkr.close_position(symbol)
            except Exception as e:
                results["ibkr"] = {"error": str(e)}

        if self.alpaca.is_configured and self._alpaca_supports(symbol):
            try:
                results["alpaca"] = self.alpaca.close_position(
                    self._to_alpaca_symbol(symbol)
                )
            except Exception as e:
                results["alpaca"] = {"error": str(e)}

        return {"status": "closed", "symbol": symbol, "results": results}

    def get_last_price(self, symbol: str) -> float | None:
        """Prix — IBKR d'abord (tous marchés), Alpaca en fallback."""
        if self.ibkr_live:
            try:
                price = self.ibkr.get_last_price(symbol)
                if price:
                    return price
            except Exception as e:
                logger.warning(f"[MULTI] IBKR price failed for {symbol}, trying Alpaca: {e}")

        if self.alpaca.is_configured and self._alpaca_supports(symbol):
            return self.alpaca.get_last_price(self._to_alpaca_symbol(symbol))

        return None

    def get_status(self) -> dict:
        """Statut de tous les brokers."""
        status = {"mode": self.mode}

        if self.ibkr.is_configured:
            try:
                if self.ibkr_live:
                    acct = self.ibkr.get_account()
                    status["ibkr"] = {
                        "status": "connected",
                        "equity": acct["equity"],
                        "paper": acct["paper"],
                    }
                else:
                    status["ibkr"] = {"status": "disconnected"}
            except Exception as e:
                status["ibkr"] = {"status": "error", "error": str(e)}
        else:
            status["ibkr"] = {"status": "not_configured"}

        if self.alpaca.is_configured:
            try:
                acct = self.alpaca.get_account()
                status["alpaca"] = {
                    "status": "connected",
                    "equity": acct["equity"],
                    "paper": acct["paper"],
                }
            except Exception as e:
                status["alpaca"] = {"status": "error", "error": str(e)}
        else:
            status["alpaca"] = {"status": "not_configured"}

        return status

    def _alpaca_supports(self, symbol: str) -> bool:
        """Vérifie si Alpaca supporte cet actif (US stocks, ETF, crypto)."""
        # Alpaca ne supporte pas : actions EU (.PA, .DE, .L, .SW), forex (=X), futures (=F)
        unsupported = [".PA", ".DE", ".L", ".SW", ".AS", ".MI", "=X", "=F"]
        return not any(symbol.endswith(suffix) for suffix in unsupported)

    def _to_alpaca_symbol(self, symbol: str) -> str:
        """Convertit un symbole vers le format Alpaca si nécessaire."""
        # Crypto : BTC-USD → BTC/USD pour Alpaca
        if symbol.endswith("-USD") and symbol.replace("-USD", "") in (
            "BTC", "ETH", "SOL", "DOGE", "AVAX", "ADA", "XRP", "BNB", "DOT", "LINK"
        ):
            return symbol.replace("-", "/")
        return symbol


# Singleton
multi_broker = MultiBroker()
