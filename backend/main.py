"""Bilok-TradePilot — FastAPI Entry Point"""

# Fix SSL certificates pour macOS (tvDatafeed, requests, etc.)
import ssl
import certifi
import os
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import settings

app = FastAPI(
    title="Bilok-TradePilot",
    description="Système de trading automatisé — Pipeline 6 modules",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


# --- Routers des modules ---
from backend.modules.scanner.router import router as scanner_router
from backend.modules.analyser.router import router as analyser_router
from backend.modules.scoring.router import router as scoring_router
from backend.modules.execution.router import router as execution_router
from backend.modules.portfolio.router import router as portfolio_router
from backend.modules.performance.router import router as performance_router
from backend.modules.analyser.backtest_router import router as backtest_router
from backend.tasks.router import router as pipeline_router
from backend.modules.execution.broker_router import router as broker_router
from backend.auth_router import router as auth_router
from backend.admin_router import router as admin_router
from backend.admin_stats import router as admin_stats_router

app.include_router(auth_router, prefix="/api/auth", tags=["Authentification"])
app.include_router(scanner_router, prefix="/api/scanner", tags=["Scanner"])
app.include_router(analyser_router, prefix="/api/analyser", tags=["Analyseur"])
app.include_router(scoring_router, prefix="/api/scoring", tags=["Scoring"])
app.include_router(execution_router, prefix="/api/execution", tags=["Exécution"])
app.include_router(portfolio_router, prefix="/api/portfolio", tags=["Portefeuille"])
app.include_router(performance_router, prefix="/api/performance", tags=["Performance"])
app.include_router(backtest_router, prefix="/api/backtest", tags=["Backtesting"])
app.include_router(pipeline_router, prefix="/api/pipeline", tags=["Pipeline"])
app.include_router(broker_router, prefix="/api/broker", tags=["Broker Alpaca"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(admin_stats_router, prefix="/api/admin", tags=["Admin Stats"])
