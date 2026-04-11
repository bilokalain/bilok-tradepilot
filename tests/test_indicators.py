"""Tests des indicateurs techniques (Module 1)."""

import numpy as np
import pandas as pd
import pytest

from backend.modules.scanner.indicators import (
    sma, ema, rsi, macd, bollinger_bands, atr, stochastic, obv,
    volume_sma, compute_technical_score,
)


class TestSMA:
    def test_basic(self):
        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
        result = sma(data, 3)
        assert result.iloc[-1] == 9.0  # (8+9+10)/3
        assert np.isnan(result.iloc[0])  # pas assez de données

    def test_period_equals_length(self):
        data = pd.Series([10, 20, 30], dtype=float)
        result = sma(data, 3)
        assert result.iloc[-1] == 20.0

    def test_constant_series(self):
        data = pd.Series([50.0] * 20)
        result = sma(data, 10)
        assert result.iloc[-1] == 50.0


class TestEMA:
    def test_basic(self):
        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
        result = ema(data, 3)
        assert not np.isnan(result.iloc[-1])
        assert result.iloc[-1] > 8.5  # EMA suit la tendance

    def test_ema_reacts_faster(self):
        # EMA réagit plus vite au changement que SMA
        data = pd.Series([10, 10, 10, 10, 10, 10, 10, 20], dtype=float)
        ema_val = ema(data, 5).iloc[-1]
        sma_val = sma(data, 5).iloc[-1]
        assert ema_val > sma_val  # EMA a plus bougé vers 20


class TestRSI:
    def test_range(self, bullish_data):
        result = rsi(bullish_data["close"])
        valid = result.dropna()
        assert all(0 <= v <= 100 for v in valid)

    def test_bullish_rsi_high(self, bullish_data):
        result = rsi(bullish_data["close"])
        assert result.iloc[-1] > 40  # tendance haussière → RSI élevé

    def test_bearish_rsi_low(self, bearish_data):
        result = rsi(bearish_data["close"])
        assert result.iloc[-1] < 60  # tendance baissière → RSI bas

    def test_short_data(self):
        data = pd.Series([1, 2, 3], dtype=float)
        result = rsi(data, 14)
        assert all(np.isnan(v) for v in result)


class TestMACD:
    def test_structure(self, bullish_data):
        result = macd(bullish_data["close"])
        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result
        assert len(result["macd"]) == len(bullish_data)

    def test_histogram_is_diff(self, bullish_data):
        result = macd(bullish_data["close"])
        idx = -1
        expected = result["macd"].iloc[idx] - result["signal"].iloc[idx]
        assert abs(result["histogram"].iloc[idx] - expected) < 1e-10


class TestBollingerBands:
    def test_structure(self, bullish_data):
        result = bollinger_bands(bullish_data["close"])
        assert "upper" in result
        assert "middle" in result
        assert "lower" in result

    def test_ordering(self, bullish_data):
        result = bollinger_bands(bullish_data["close"])
        idx = -1
        assert result["upper"].iloc[idx] > result["middle"].iloc[idx]
        assert result["middle"].iloc[idx] > result["lower"].iloc[idx]

    def test_middle_equals_sma(self, bullish_data):
        result = bollinger_bands(bullish_data["close"], 20)
        sma_20 = sma(bullish_data["close"], 20)
        assert abs(result["middle"].iloc[-1] - sma_20.iloc[-1]) < 1e-10


class TestATR:
    def test_positive(self, bullish_data):
        result = atr(bullish_data["high"], bullish_data["low"], bullish_data["close"])
        valid = result.dropna()
        assert all(v > 0 for v in valid)

    def test_higher_volatility_higher_atr(self):
        # Données calmes
        close_calm = pd.Series([100 + i * 0.1 for i in range(50)], dtype=float)
        high_calm = close_calm + 0.5
        low_calm = close_calm - 0.5
        # Données volatiles
        close_vol = pd.Series([100 + i * 0.1 + np.sin(i) * 5 for i in range(50)], dtype=float)
        high_vol = close_vol + 3
        low_vol = close_vol - 3

        atr_calm = atr(high_calm, low_calm, close_calm).iloc[-1]
        atr_vol = atr(high_vol, low_vol, close_vol).iloc[-1]
        assert atr_vol > atr_calm


class TestStochastic:
    def test_range(self, bullish_data):
        result = stochastic(bullish_data["high"], bullish_data["low"], bullish_data["close"])
        k_valid = result["k"].dropna()
        assert all(0 <= v <= 100 for v in k_valid)

    def test_structure(self, bullish_data):
        result = stochastic(bullish_data["high"], bullish_data["low"], bullish_data["close"])
        assert "k" in result
        assert "d" in result


class TestOBV:
    def test_basic(self):
        close = pd.Series([10, 11, 10.5, 12, 11.5], dtype=float)
        volume = pd.Series([100, 200, 150, 300, 100], dtype=float)
        result = obv(close, volume)
        assert len(result) == 5
        assert result.iloc[1] > 0  # prix monte → OBV augmente


class TestComputeTechnicalScore:
    def test_range(self, bullish_data):
        score = compute_technical_score(
            bullish_data["close"], bullish_data["high"],
            bullish_data["low"], bullish_data["volume"],
        )
        assert 0 <= score <= 100

    def test_bullish_higher_score(self, bullish_data, bearish_data):
        bull_score = compute_technical_score(
            bullish_data["close"], bullish_data["high"],
            bullish_data["low"], bullish_data["volume"],
        )
        bear_score = compute_technical_score(
            bearish_data["close"], bearish_data["high"],
            bearish_data["low"], bearish_data["volume"],
        )
        assert bull_score > bear_score
