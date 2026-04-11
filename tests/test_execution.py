"""Tests de l'exécution (Module 4)."""

import pytest

from backend.modules.execution.order_engine import (
    ExecutionOrder, OrderType, OrderSide, OrderStatus, ExecutionMode,
    simulate_fill, create_scaling_orders, SCALING_TRANCHES,
)
from backend.modules.execution.position_manager import (
    ActivePosition, compute_twap_schedule, compute_vwap_schedule,
)
from backend.modules.execution.bias_detector import (
    detect_disposition_effect, detect_revenge_trading,
    detect_fomo, detect_overtrading, run_full_bias_check,
)


class TestOrderEngine:
    def test_create_scaling_orders(self):
        orders = create_scaling_orders("AAPL", OrderSide.BUY, 100, 150.0, OrderType.MARKET)
        assert len(orders) == 3
        total_qty = sum(o.quantity for o in orders)
        assert abs(total_qty - 100) < 0.01
        assert orders[0].tranche == 1
        assert orders[1].tranche == 2
        assert orders[2].tranche == 3

    def test_scaling_percentages(self):
        orders = create_scaling_orders("AAPL", OrderSide.BUY, 100, 150.0, OrderType.MARKET)
        assert abs(orders[0].quantity - 40) < 0.01
        assert abs(orders[1].quantity - 35) < 0.01
        assert abs(orders[2].quantity - 25) < 0.01

    def test_simulate_fill_market(self):
        order = ExecutionOrder(
            symbol="AAPL", side=OrderSide.BUY,
            order_type=OrderType.MARKET, quantity=10,
        )
        filled = simulate_fill(order, 150.0)
        assert filled.status == OrderStatus.FILLED
        assert filled.filled_price is not None
        assert abs(filled.filled_price - 150) < 1  # Slippage < 1$
        assert filled.slippage > 0

    def test_simulate_fill_limit_favorable(self):
        order = ExecutionOrder(
            symbol="AAPL", side=OrderSide.BUY,
            order_type=OrderType.LIMIT, quantity=10, price=155.0,
        )
        filled = simulate_fill(order, 150.0)  # Prix < limit → fill
        assert filled.status == OrderStatus.FILLED
        assert filled.filled_price == 155.0

    def test_simulate_fill_limit_unfavorable(self):
        order = ExecutionOrder(
            symbol="AAPL", side=OrderSide.BUY,
            order_type=OrderType.LIMIT, quantity=10, price=145.0,
        )
        filled = simulate_fill(order, 150.0)  # Prix > limit → pas de fill
        assert filled.status == OrderStatus.PENDING

    def test_order_to_dict(self):
        order = ExecutionOrder(
            symbol="AAPL", side=OrderSide.BUY,
            order_type=OrderType.MARKET, quantity=10,
        )
        d = order.to_dict()
        assert d["symbol"] == "AAPL"
        assert d["side"] == "BUY"
        assert d["quantity"] == 10


class TestPositionManager:
    def test_long_position_pnl(self):
        pos = ActivePosition(
            symbol="AAPL", direction="LONG",
            entry_price=100, current_price=100,
            quantity=10, stop_loss=95, take_profit=110,
        )
        result = pos.update(105)
        assert pos.pnl == 50  # (105-100) * 10
        assert pos.pnl_pct == pytest.approx(5.0, abs=0.1)

    def test_long_stop_loss_hit(self):
        pos = ActivePosition(
            symbol="AAPL", direction="LONG",
            entry_price=100, current_price=100,
            quantity=10, stop_loss=95, take_profit=110,
        )
        result = pos.update(94)
        assert result["action"] == "STOP_HIT"

    def test_long_take_profit_hit(self):
        pos = ActivePosition(
            symbol="AAPL", direction="LONG",
            entry_price=100, current_price=100,
            quantity=10, stop_loss=95, take_profit=110,
        )
        result = pos.update(111)
        assert result["action"] == "TP_HIT"

    def test_trailing_stop_updates(self):
        pos = ActivePosition(
            symbol="AAPL", direction="LONG",
            entry_price=100, current_price=100,
            quantity=10, stop_loss=95, take_profit=120,
            trailing_pct=0.05,
        )
        pos.update(105)
        trailing_1 = pos.trailing_stop
        pos.update(110)
        trailing_2 = pos.trailing_stop
        assert trailing_2 > trailing_1  # Trailing monte avec le prix

    def test_twap_schedule(self):
        schedule = compute_twap_schedule(100, 60, 5)
        assert len(schedule) == 5
        total = sum(s["quantity"] for s in schedule)
        assert abs(total - 100) < 0.01

    def test_position_to_dict(self):
        pos = ActivePosition(
            symbol="AAPL", direction="LONG",
            entry_price=100, current_price=105,
            quantity=10, stop_loss=95, take_profit=110,
        )
        d = pos.to_dict()
        assert d["symbol"] == "AAPL"
        assert d["direction"] == "LONG"


class TestBiasDetector:
    def test_no_trades_ok(self):
        result = detect_disposition_effect([])
        assert result["level"] == "OK"

    def test_fomo_no_movement(self):
        prices = [100, 100.5, 101, 100.8, 101.2, 100.9, 101.1, 100.7, 101, 100.5]
        result = detect_fomo(101, prices)
        assert result["level"] == "OK"
        assert result["score"] <= 30

    def test_fomo_large_movement(self):
        prices = [100, 105, 110, 115, 118, 120, 122, 125, 128, 130]
        result = detect_fomo(130, prices)
        assert result["score"] >= 60  # 30% move → FOMO

    def test_overtrading_few_trades(self):
        result = detect_overtrading([], lookback_days=7)
        assert result["level"] == "OK"

    def test_full_bias_check_structure(self):
        result = run_full_bias_check([], entry_price=100, recent_prices=[100, 101, 102])
        assert "overall_level" in result
        assert "can_execute" in result
        assert "biases" in result
        assert len(result["biases"]) == 4

    def test_full_bias_check_no_trades_can_execute(self):
        result = run_full_bias_check([], entry_price=100, recent_prices=[100, 101])
        assert result["can_execute"] is True
