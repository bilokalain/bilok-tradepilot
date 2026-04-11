"""Tests détection de régime + stratégies (Module 2)."""

import pytest

from backend.modules.analyser.regime import detect_regime, REGIMES
from backend.modules.analyser.strategies import (
    strategy_trend_following, strategy_mean_reversion,
    strategy_breakout, strategy_momentum,
    run_all_strategies, select_best_strategy, REGIME_STRATEGY_MATRIX,
)
from backend.modules.analyser.performance_matrix import (
    get_best_strategy, get_strategy_sharpe, get_profitable_strategies,
    get_strategy_ranking, BACKTEST_MATRIX,
)


class TestRegimeDetection:
    def test_returns_all_regimes(self, bullish_data):
        result = detect_regime(bullish_data["close"], bullish_data["high"], bullish_data["low"])
        assert "regime" in result
        assert "probabilities" in result
        assert "confidence" in result
        assert result["regime"] in REGIMES

    def test_probabilities_sum_to_one(self, bullish_data):
        result = detect_regime(bullish_data["close"], bullish_data["high"], bullish_data["low"])
        total = sum(result["probabilities"].values())
        assert abs(total - 1.0) < 0.01

    def test_bullish_data_bull_regime(self, bullish_data):
        result = detect_regime(bullish_data["close"], bullish_data["high"], bullish_data["low"])
        # Le régime BULL devrait avoir une probabilité élevée
        assert result["probabilities"]["BULL"] > result["probabilities"]["BEAR"]

    def test_bearish_data_bear_regime(self, bearish_data):
        result = detect_regime(bearish_data["close"], bearish_data["high"], bearish_data["low"])
        assert result["probabilities"]["BEAR"] > result["probabilities"]["BULL"]

    def test_short_data_unknown(self, short_data):
        result = detect_regime(short_data["close"], short_data["high"], short_data["low"])
        assert result["regime"] == "UNKNOWN"

    def test_confidence_range(self, bullish_data):
        result = detect_regime(bullish_data["close"], bullish_data["high"], bullish_data["low"])
        assert 0 <= result["confidence"] <= 1


class TestStrategies:
    def test_trend_following_structure(self, bullish_data):
        result = strategy_trend_following(bullish_data["close"], bullish_data["high"], bullish_data["low"])
        assert "strategy" in result
        assert result["strategy"] == "trend_following"
        assert "direction" in result
        assert result["direction"] in ("LONG", "SHORT", "NEUTRAL")
        assert "conviction" in result
        assert 0 <= result["conviction"] <= 100

    def test_mean_reversion_structure(self, bullish_data):
        result = strategy_mean_reversion(bullish_data["close"], bullish_data["high"], bullish_data["low"])
        assert result["strategy"] == "mean_reversion"
        assert result["direction"] in ("LONG", "SHORT", "NEUTRAL")

    def test_breakout_structure(self, bullish_data):
        result = strategy_breakout(bullish_data["close"], bullish_data["high"], bullish_data["low"], bullish_data["volume"])
        assert result["strategy"] == "breakout"

    def test_momentum_structure(self, bullish_data):
        result = strategy_momentum(bullish_data["close"], bullish_data["high"], bullish_data["low"])
        assert result["strategy"] == "momentum"

    def test_run_all_returns_6(self, bullish_data):
        results = run_all_strategies(
            bullish_data["close"], bullish_data["high"],
            bullish_data["low"], bullish_data["volume"], "BULL"
        )
        assert len(results) == 6  # 4 actives + 2 placeholders

    def test_regime_strategy_matrix_complete(self):
        for regime in REGIMES:
            assert regime in REGIME_STRATEGY_MATRIX
            weights = REGIME_STRATEGY_MATRIX[regime]
            total = sum(weights.values())
            assert abs(total - 1.0) < 0.01, f"Weights for {regime} sum to {total}"


class TestPerformanceMatrix:
    def test_matrix_has_entries(self):
        assert len(BACKTEST_MATRIX) >= 21  # Au moins les 21 originaux

    def test_get_best_strategy(self):
        best = get_best_strategy("AAPL")
        assert best in ("trend_following", "mean_reversion", "breakout", "momentum")

    def test_get_best_strategy_unknown(self):
        assert get_best_strategy("UNKNOWN_SYMBOL") is None

    def test_get_strategy_sharpe(self):
        sharpe = get_strategy_sharpe("AAPL", "breakout")
        assert isinstance(sharpe, float)
        assert sharpe > 0  # AAPL breakout est profitable

    def test_get_profitable_strategies(self):
        profitable = get_profitable_strategies("GOOGL")
        assert "trend_following" in profitable
        assert len(profitable) >= 1

    def test_ranking_sorted(self):
        ranking = get_strategy_ranking("AAPL")
        sharpes = [r["sharpe"] for r in ranking]
        assert sharpes == sorted(sharpes, reverse=True)
