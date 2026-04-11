"""Tests des endpoints API (FastAPI TestClient)."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestScannerEndpoints:
    def test_assets_list(self):
        response = client.get("/api/scanner/assets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "symbol" in data[0]
        assert "name" in data[0]
        assert "asset_class" in data[0]

    def test_scan_result(self):
        response = client.get("/api/scanner/results/AAPL")
        assert response.status_code == 200
        data = response.json()
        if "error" not in data:
            assert "scores" in data
            assert "final" in data["scores"]
            assert 0 <= data["scores"]["final"] <= 100

    def test_scan_unknown_symbol(self):
        response = client.get("/api/scanner/results/ZZZZZ")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    def test_ohlcv(self):
        response = client.get("/api/scanner/ohlcv/AAPL?limit=5")
        assert response.status_code == 200
        data = response.json()
        if "error" not in data:
            assert "data" in data
            assert len(data["data"]) <= 5

    def test_sentiment(self):
        response = client.get("/api/scanner/sentiment/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert 0 <= data["score"] <= 100


class TestAnalyserEndpoints:
    def test_regime(self):
        response = client.get("/api/analyser/regime")
        assert response.status_code == 200
        data = response.json()
        assert "dominant_regime" in data
        assert "distribution" in data

    def test_analyse_asset(self):
        response = client.get("/api/analyser/analyse/AAPL")
        assert response.status_code == 200
        data = response.json()
        if "error" not in data:
            assert "regime" in data
            assert "best_strategy" in data


class TestScoringEndpoints:
    def test_thesis(self):
        response = client.get("/api/scoring/thesis/AAPL")
        assert response.status_code == 200
        data = response.json()
        if "error" not in data:
            assert "action" in data
            assert data["action"] in ("GO", "WAIT", "NO_TRADE")


class TestExecutionEndpoints:
    def test_positions(self):
        response = client.get("/api/execution/positions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_orders(self):
        response = client.get("/api/execution/orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_bias_check(self):
        response = client.get("/api/execution/bias-check")
        assert response.status_code == 200
        data = response.json()
        assert "overall_level" in data
        assert "can_execute" in data


class TestPortfolioEndpoints:
    def test_summary(self):
        response = client.get("/api/portfolio/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_value" in data
        assert "num_positions" in data

    def test_stress_test(self):
        response = client.get("/api/portfolio/stress-test")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestPerformanceEndpoints:
    def test_meta_score(self):
        response = client.get("/api/performance/meta-score")
        assert response.status_code == 200
        data = response.json()
        assert "meta_score" in data
        assert 0 <= data["meta_score"] <= 100

    def test_ews(self):
        response = client.get("/api/performance/ews")
        assert response.status_code == 200
        data = response.json()
        assert "overall_level" in data
        assert "indicators" in data

    def test_report(self):
        response = client.get("/api/performance/report")
        assert response.status_code == 200
        data = response.json()
        assert "equity" in data
        assert "meta_score" in data
        assert "ews" in data


class TestBrokerEndpoints:
    def test_broker_status(self):
        response = client.get("/api/broker/status")
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
