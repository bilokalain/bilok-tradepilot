"""Tests des 9 critères du scanner."""

import numpy as np
import pandas as pd
import pytest

from backend.modules.scanner.genome import (
    detect_cycle_phase, compute_seismograph, compute_fractal_memory,
    compute_genome_score,
)
from backend.modules.scanner.institutional import (
    compute_accumulation_distribution, detect_smart_money_flow,
    detect_volume_anomaly, compute_ipi_score,
)
from backend.modules.scanner.fundamental_velocity import (
    compute_price_acceleration, compute_relative_strength,
    detect_earnings_gaps, compute_ivf_score,
)
from backend.modules.scanner.macro import (
    detect_economic_cycle, detect_rate_regime, compute_mts_score,
)
from backend.modules.scanner.social import compute_sgi_score
from backend.modules.scanner.uniqueness import (
    compute_crowding_score, compute_novelty_score,
    compute_timeframe_neglect, compute_sus_score,
)
from backend.modules.scanner.correlation import compute_correlation_score
from backend.modules.scanner.sentiment import analyse_text_sentiment, compute_sentiment_score


class TestGenome:
    def test_cycle_phase_range(self, bullish_data):
        result = detect_cycle_phase(bullish_data["close"], bullish_data["volume"])
        assert 1 <= result["phase"] <= 5
        assert 0 <= result["score"] <= 100

    def test_seismograph_structure(self, bullish_data):
        result = compute_seismograph(
            bullish_data["close"], bullish_data["high"],
            bullish_data["low"], bullish_data["volume"],
        )
        assert "signals" in result
        assert "active" in result
        assert 0 <= result["score"] <= 100

    def test_fractal_memory_range(self, bullish_data):
        score = compute_fractal_memory(bullish_data["close"])
        assert 0 <= score <= 100

    def test_genome_score_composite(self, bullish_data):
        result = compute_genome_score(
            bullish_data["close"], bullish_data["high"],
            bullish_data["low"], bullish_data["volume"],
        )
        assert 0 <= result["score"] <= 100
        assert "cycle_phase" in result
        assert "seismograph" in result


class TestInstitutional:
    def test_ad_line_cumulative(self, bullish_data):
        ad = compute_accumulation_distribution(
            bullish_data["high"], bullish_data["low"],
            bullish_data["close"], bullish_data["volume"],
        )
        assert len(ad) == len(bullish_data)

    def test_smart_money_range(self, bullish_data):
        score = detect_smart_money_flow(bullish_data["close"], bullish_data["volume"])
        assert 0 <= score <= 100

    def test_volume_anomaly_structure(self, bullish_data):
        result = detect_volume_anomaly(bullish_data["volume"])
        assert "anomaly" in result
        assert "ratio" in result
        assert "score" in result

    def test_ipi_composite(self, bullish_data):
        result = compute_ipi_score(
            bullish_data["close"], bullish_data["high"],
            bullish_data["low"], bullish_data["volume"],
        )
        assert 0 <= result["score"] <= 100
        assert result["ad_trend"] in ("UP", "DOWN", "FLAT")


class TestFundamentalVelocity:
    def test_acceleration_range(self, bullish_data):
        score = compute_price_acceleration(bullish_data["close"])
        assert 0 <= score <= 100

    def test_relative_strength_range(self, bullish_data):
        score = compute_relative_strength(bullish_data["close"])
        assert 0 <= score <= 100

    def test_earnings_gaps_structure(self, bullish_data):
        result = detect_earnings_gaps(bullish_data["close"], bullish_data["volume"])
        assert "gaps_up" in result
        assert "gaps_down" in result
        assert 0 <= result["score"] <= 100

    def test_ivf_composite(self, bullish_data):
        result = compute_ivf_score(bullish_data["close"], bullish_data["volume"])
        assert 0 <= result["score"] <= 100


class TestMacro:
    def test_economic_cycle(self, bullish_data):
        result = detect_economic_cycle(bullish_data["close"])
        assert result["phase"] in ("expansion", "pic", "contraction", "creux", "unknown")
        assert 0 <= result["score"] <= 100

    def test_rate_regime(self, bullish_data):
        result = detect_rate_regime(bullish_data["close"])
        assert result["regime"] in ("dovish", "easing", "neutral", "tightening", "hawkish")

    def test_mts_composite(self, bullish_data):
        result = compute_mts_score("ACTION_US", spy_close=bullish_data["close"])
        assert 0 <= result["score"] <= 100

    def test_mts_crypto_vs_stock(self, bullish_data):
        stock = compute_mts_score("ACTION_US", spy_close=bullish_data["close"])
        crypto = compute_mts_score("CRYPTO", spy_close=bullish_data["close"])
        # Les poids sont différents, les scores aussi
        assert isinstance(stock["score"], float)
        assert isinstance(crypto["score"], float)


class TestSocial:
    def test_empty_mentions(self):
        result = compute_sgi_score([], "AAPL", "ACTION_US")
        assert 0 <= result["score"] <= 100

    def test_with_mentions(self):
        mentions = [
            {"text": "AAPL looking strong, bullish breakout", "source": "reddit", "date": "2024-01-01"},
            {"text": "Buy AAPL, great earnings", "source": "reddit", "date": "2024-01-02"},
            {"text": "AAPL crash coming", "source": "twitter", "date": "2024-01-03"},
        ]
        result = compute_sgi_score(mentions, "AAPL", "ACTION_US")
        assert 0 <= result["score"] <= 100
        assert result["sentiment"]["num_mentions"] == 3


class TestUniqueness:
    def test_crowding_no_data(self):
        score = compute_crowding_score({}, "AAPL")
        assert score == 50.0

    def test_crowding_unique(self):
        scores = {"AAPL": 90, "MSFT": 30, "GOOGL": 40, "AMZN": 35}
        score = compute_crowding_score(scores, "AAPL")
        assert score >= 70  # AAPL est unique (90 vs 30-40)

    def test_crowding_crowded(self):
        scores = {"AAPL": 50, "MSFT": 52, "GOOGL": 48, "AMZN": 51}
        score = compute_crowding_score(scores, "AAPL")
        assert score <= 30  # Tout le monde à ~50

    def test_novelty_range(self, bullish_data):
        score = compute_novelty_score(bullish_data["close"])
        assert 0 <= score <= 100

    def test_sus_composite(self, bullish_data):
        all_scores = {"AAPL": 70, "MSFT": 50}
        result = compute_sus_score(
            bullish_data["close"], bullish_data["high"],
            bullish_data["low"], all_scores, "AAPL",
        )
        assert 0 <= result["score"] <= 100


class TestSentiment:
    def test_bullish_text(self):
        result = analyse_text_sentiment("buy AAPL, bullish breakout, moon rocket!")
        assert result["polarity"] > 0
        assert result["label"] == "positive"

    def test_bearish_text(self):
        result = analyse_text_sentiment("sell everything, crash incoming, bear market")
        assert result["polarity"] < 0
        assert result["label"] == "negative"

    def test_neutral_text(self):
        result = analyse_text_sentiment("the weather is nice today")
        assert result["label"] == "neutral"

    def test_sentiment_score_range(self):
        mentions = [{"text": "buy buy buy bullish!"}, {"text": "sell crash fear"}]
        result = compute_sentiment_score(mentions)
        assert 0 <= result["score"] <= 100


class TestCorrelation:
    def test_single_asset(self, bullish_data):
        closes = {"AAPL": bullish_data["close"]}
        score = compute_correlation_score(closes, "AAPL")
        assert score == 50.0  # Pas assez d'actifs pour corréler

    def test_two_assets(self, bullish_data, bearish_data):
        closes = {"AAPL": bullish_data["close"], "MSFT": bearish_data["close"]}
        score = compute_correlation_score(closes, "AAPL")
        assert 0 <= score <= 100
