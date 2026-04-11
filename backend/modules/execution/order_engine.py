"""Moteur d'ordres — Paper Trading + Scaling 3 tranches

Gère l'exécution des ordres en mode paper trading (Phase 1)
et prépare la structure pour le live trading (Phase 2).

Scaling in progressif :
- Tranche 1 : 40% à l'entrée
- Tranche 2 : 35% sur confirmation (prix dépasse 0.5 ATR dans la bonne direction)
- Tranche 3 : 25% sur momentum fort (prix dépasse 1 ATR)

Modes :
- PAPER : simulation locale, pas d'API broker
- LIVE_ALPACA : Alpaca API (Phase 2)
- LIVE_BINANCE : Binance API pour crypto (Phase 2)
"""

from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

import numpy as np


class ExecutionMode(str, Enum):
    PAPER = "PAPER"
    LIVE_ALPACA = "LIVE_ALPACA"
    LIVE_BINANCE = "LIVE_BINANCE"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


SCALING_TRANCHES = [0.40, 0.35, 0.25]


@dataclass
class ExecutionOrder:
    """Représente un ordre d'exécution."""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float | None = None
    stop_price: float | None = None
    tranche: int = 1
    status: OrderStatus = OrderStatus.PENDING
    filled_price: float | None = None
    filled_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    broker_order_id: str | None = None
    mode: ExecutionMode = ExecutionMode.PAPER
    slippage: float = 0.0

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": round(self.quantity, 4),
            "price": self.price,
            "stop_price": self.stop_price,
            "tranche": self.tranche,
            "status": self.status.value,
            "filled_price": self.filled_price,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "created_at": self.created_at.isoformat(),
            "mode": self.mode.value,
            "slippage": round(self.slippage, 4),
        }


def simulate_fill(order: ExecutionOrder, current_price: float) -> ExecutionOrder:
    """Simule le fill d'un ordre en paper trading.

    Applique un slippage réaliste :
    - Market : 0.02-0.05%
    - Limit : 0% (rempli au prix demandé si favorable)
    - Stop : 0.03-0.08% (slippage typique sur stops)
    """
    if order.order_type == OrderType.MARKET:
        slippage_pct = np.random.uniform(0.0002, 0.0005)
        if order.side == OrderSide.BUY:
            order.filled_price = round(current_price * (1 + slippage_pct), 4)
        else:
            order.filled_price = round(current_price * (1 - slippage_pct), 4)
        order.slippage = slippage_pct

    elif order.order_type == OrderType.LIMIT:
        if order.price is None:
            order.status = OrderStatus.REJECTED
            return order
        # Limit : fill seulement si le prix est favorable
        if order.side == OrderSide.BUY and current_price <= order.price:
            order.filled_price = order.price
        elif order.side == OrderSide.SELL and current_price >= order.price:
            order.filled_price = order.price
        else:
            # Pas encore rempli
            return order

    elif order.order_type == OrderType.STOP:
        if order.stop_price is None:
            order.status = OrderStatus.REJECTED
            return order
        slippage_pct = np.random.uniform(0.0003, 0.0008)
        if order.side == OrderSide.BUY and current_price >= order.stop_price:
            order.filled_price = round(current_price * (1 + slippage_pct), 4)
            order.slippage = slippage_pct
        elif order.side == OrderSide.SELL and current_price <= order.stop_price:
            order.filled_price = round(current_price * (1 - slippage_pct), 4)
            order.slippage = slippage_pct
        else:
            return order

    order.status = OrderStatus.FILLED
    order.filled_at = datetime.utcnow()
    return order


def create_scaling_orders(symbol: str, side: OrderSide, total_quantity: float,
                          entry_price: float, order_type: OrderType,
                          mode: ExecutionMode = ExecutionMode.PAPER) -> list[ExecutionOrder]:
    """Crée les 3 tranches de scaling pour un trade.

    Tranche 1 (40%) : ordre immédiat
    Tranche 2 (35%) : ordre limit légèrement au-dessus/dessous
    Tranche 3 (25%) : ordre stop sur confirmation momentum
    """
    orders = []
    for i, pct in enumerate(SCALING_TRANCHES):
        qty = round(total_quantity * pct, 4)
        tranche = i + 1

        if tranche == 1:
            # Tranche 1 : exécution immédiate
            orders.append(ExecutionOrder(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=qty,
                price=entry_price if order_type == OrderType.LIMIT else None,
                tranche=tranche,
                mode=mode,
            ))
        elif tranche == 2:
            # Tranche 2 : limit order légèrement décalé
            offset = entry_price * 0.005  # 0.5%
            limit_price = entry_price + offset if side == OrderSide.BUY else entry_price - offset
            orders.append(ExecutionOrder(
                symbol=symbol,
                side=side,
                order_type=OrderType.LIMIT,
                quantity=qty,
                price=round(limit_price, 2),
                tranche=tranche,
                mode=mode,
            ))
        else:
            # Tranche 3 : stop order sur momentum
            offset = entry_price * 0.01  # 1%
            stop_price = entry_price + offset if side == OrderSide.BUY else entry_price - offset
            orders.append(ExecutionOrder(
                symbol=symbol,
                side=side,
                order_type=OrderType.STOP,
                quantity=qty,
                stop_price=round(stop_price, 2),
                tranche=tranche,
                mode=mode,
            ))

    return orders
