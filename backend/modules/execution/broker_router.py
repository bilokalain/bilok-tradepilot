"""Broker Alpaca : API endpoints directs"""

from fastapi import APIRouter

from backend.modules.execution.broker_alpaca import alpaca_broker

router = APIRouter()


@router.get("/status")
def broker_status():
    """Vérifie si Alpaca est configuré et connecté."""
    if not alpaca_broker.is_configured:
        return {
            "connected": False,
            "message": "Alpaca non configuré — ajoutez ALPACA_API_KEY dans .env",
        }
    try:
        account = alpaca_broker.get_account()
        return {"connected": True, "account": account}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@router.get("/positions")
def broker_positions():
    """Positions ouvertes chez Alpaca."""
    if not alpaca_broker.is_configured:
        return {"error": "Alpaca non configuré"}
    return alpaca_broker.get_positions()


@router.get("/orders")
def broker_orders(status: str = "all"):
    """Ordres chez Alpaca."""
    if not alpaca_broker.is_configured:
        return {"error": "Alpaca non configuré"}
    return alpaca_broker.get_orders(status)


@router.post("/order")
def broker_place_order(
    symbol: str,
    side: str,
    quantity: float,
    order_type: str = "market",
    limit_price: float = None,
    stop_price: float = None,
):
    """Place un ordre directement via Alpaca."""
    if not alpaca_broker.is_configured:
        return {"error": "Alpaca non configuré"}
    return alpaca_broker.place_order(symbol, side, quantity, order_type, limit_price, stop_price)


@router.delete("/order/{order_id}")
def broker_cancel_order(order_id: str):
    """Annule un ordre."""
    if not alpaca_broker.is_configured:
        return {"error": "Alpaca non configuré"}
    return alpaca_broker.cancel_order(order_id)


@router.post("/close/{symbol}")
def broker_close_position(symbol: str):
    """Ferme une position."""
    if not alpaca_broker.is_configured:
        return {"error": "Alpaca non configuré"}
    return alpaca_broker.close_position(symbol)
