"""Fixtures partagées pour les tests."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def bullish_data() -> pd.DataFrame:
    """Données OHLCV simulant une tendance haussière sur 300 jours."""
    np.random.seed(42)
    n = 300
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    base = 100
    returns = np.random.normal(0.001, 0.015, n)
    close = base * np.cumprod(1 + returns)
    high = close * (1 + np.random.uniform(0.001, 0.02, n))
    low = close * (1 - np.random.uniform(0.001, 0.02, n))
    open_ = close * (1 + np.random.normal(0, 0.005, n))
    volume = np.random.randint(1_000_000, 10_000_000, n)

    return pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close, "volume": volume,
    }, index=dates)


@pytest.fixture
def bearish_data() -> pd.DataFrame:
    """Données OHLCV simulant une tendance baissière sur 300 jours."""
    np.random.seed(123)
    n = 300
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    base = 100
    returns = np.random.normal(-0.001, 0.015, n)
    close = base * np.cumprod(1 + returns)
    high = close * (1 + np.random.uniform(0.001, 0.02, n))
    low = close * (1 - np.random.uniform(0.001, 0.02, n))
    open_ = close * (1 + np.random.normal(0, 0.005, n))
    volume = np.random.randint(1_000_000, 10_000_000, n)

    return pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close, "volume": volume,
    }, index=dates)


@pytest.fixture
def range_data() -> pd.DataFrame:
    """Données OHLCV simulant un marché latéral sur 300 jours."""
    np.random.seed(99)
    n = 300
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    base = 100
    returns = np.random.normal(0, 0.01, n)
    close = base * np.cumprod(1 + returns)
    # Forcer le range en ramenant vers la moyenne
    for i in range(1, n):
        if close[i] > 110:
            close[i] = close[i] * 0.995
        elif close[i] < 90:
            close[i] = close[i] * 1.005
    high = close * (1 + np.random.uniform(0.001, 0.015, n))
    low = close * (1 - np.random.uniform(0.001, 0.015, n))
    open_ = close * (1 + np.random.normal(0, 0.003, n))
    volume = np.random.randint(1_000_000, 10_000_000, n)

    return pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close, "volume": volume,
    }, index=dates)


@pytest.fixture
def short_data() -> pd.DataFrame:
    """Données OHLCV courtes (30 jours) pour tester les edge cases."""
    np.random.seed(77)
    n = 30
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    close = 100 + np.cumsum(np.random.normal(0, 1, n))
    high = close + np.random.uniform(0.5, 2, n)
    low = close - np.random.uniform(0.5, 2, n)
    open_ = close + np.random.normal(0, 0.5, n)
    volume = np.random.randint(500_000, 5_000_000, n)

    return pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close, "volume": volume,
    }, index=dates)
