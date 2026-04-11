"""Tests du scoring (Module 3)."""

import numpy as np
import pandas as pd
import pytest

from backend.modules.scoring.bayesian import (
    compute_historical_prior, compute_observation_likelihood,
    compute_bayesian_score,
)
from backend.modules.scoring.context import (
    compute_liquidity_score, compute_volatility_context,
    compute_sqc, estimate_shelf_life,
)
from backend.modules.scoring.kelly import (
    compute_win_rate_estimate, compute_kelly_fraction,
    compute_risk_reward, compute_position_sizing,
)


class TestBayesianScore:
    def test_prior_range(self, bullish_data):
        prior = compute_historical_prior(bullish_data["close"])
        assert 0 <= prior <= 100

    def test_prior_bullish_higher(self, bullish_data, bearish_data):
        bull_prior = compute_historical_prior(bullish_data["close"])
        bear_prior = compute_historical_prior(bearish_data["close"])
        assert bull_prior > bear_prior

    def test_prior_short_data(self, short_data):
        prior = compute_historical_prior(short_data["close"])
        assert prior == 50.0  # Default pour données insuffisantes

    def test_likelihood_range(self):
        result = compute_observation_likelihood(80, 70, 0.5)
        assert 0 <= result <= 100

    def test_bayesian_complete(self, bullish_data):
        result = compute_bayesian_score(bullish_data["close"], 70, 65, 0.4)
        assert "prior" in result
        assert "likelihood" in result
        assert "posterior" in result
        assert 0 <= result["posterior"] <= 100
        assert abs(result["prior_weight"] + result["observation_weight"] - 1.0) < 0.01

    def test_high_confidence_weights_observations(self, bullish_data):
        low_conf = compute_bayesian_score(bullish_data["close"], 70, 65, 0.2)
        high_conf = compute_bayesian_score(bullish_data["close"], 70, 65, 0.8)
        assert high_conf["observation_weight"] > low_conf["observation_weight"]


class TestContextQuality:
    def test_liquidity_high_volume(self):
        volume = pd.Series([1_000_000] * 19 + [3_000_000], dtype=float)
        score = compute_liquidity_score(volume)
        assert score >= 70

    def test_liquidity_low_volume(self):
        volume = pd.Series([1_000_000] * 19 + [300_000], dtype=float)
        score = compute_liquidity_score(volume)
        assert score <= 50

    def test_sqc_structure(self, bullish_data):
        result = compute_sqc(
            bullish_data["volume"], bullish_data["high"],
            bullish_data["low"], bullish_data["close"],
        )
        assert "sqc" in result
        assert "components" in result
        assert 0 <= result["sqc"] <= 100

    def test_shelf_life_structure(self):
        result = estimate_shelf_life("momentum", "BULL", 80, 70)
        assert "shelf_life_hours" in result
        assert "order_type" in result
        assert result["shelf_life_hours"] > 0
        assert result["order_type"] in ("MARKET", "LIMIT")

    def test_crisis_shorter_shelf_life(self):
        normal = estimate_shelf_life("momentum", "BULL", 60, 60)
        crisis = estimate_shelf_life("momentum", "CRISIS", 60, 60)
        assert crisis["shelf_life_hours"] < normal["shelf_life_hours"]


class TestKelly:
    def test_win_rate_estimate_range(self):
        for score in [20, 50, 70, 90]:
            wr = compute_win_rate_estimate(score, 50)
            assert 0.20 <= wr <= 0.75

    def test_higher_score_higher_wr(self):
        wr_low = compute_win_rate_estimate(30, 50)
        wr_high = compute_win_rate_estimate(80, 50)
        assert wr_high > wr_low

    def test_kelly_fraction_positive_edge(self):
        kelly = compute_kelly_fraction(0.6, 1.5)
        assert kelly > 0
        assert kelly <= 0.20  # plafonné

    def test_kelly_fraction_no_edge(self):
        kelly = compute_kelly_fraction(0.3, 1.0)
        assert kelly == 0  # p*b - q < 0

    def test_risk_reward(self):
        rr = compute_risk_reward(100, 95, 115)
        assert abs(rr - 3.0) < 0.01  # 15/5 = 3

    def test_risk_reward_zero_risk(self):
        rr = compute_risk_reward(100, 100, 110)
        assert rr == 0

    def test_position_sizing_complete(self):
        result = compute_position_sizing(100_000, 50, 48, 56, 70, 65)
        assert "kelly_fraction" in result
        assert "position_size_usd" in result
        assert "risk_reward_ratio" in result
        assert result["risk_reward_ratio"] > 0
        assert result["position_size_usd"] > 0

    def test_position_sizing_reject_low_rr(self):
        result = compute_position_sizing(100_000, 50, 49, 50.5, 70, 65)
        assert result["kelly_fraction"] == 0
        assert result["reject_reason"] is not None
