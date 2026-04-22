"""Configuration centralisée Bilok-TradePilot"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Base de données ---
    DATABASE_URL: str = "postgresql://localhost:5432/tradepilot"
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = ""
    INFLUXDB_ORG: str = "tradepilot"
    INFLUXDB_BUCKET: str = "market_data"

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # --- APIs Marché ---
    ALPHA_VANTAGE_API_KEY: str = ""
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""
    POLYGON_API_KEY: str = ""

    # --- Broker Alpaca (paper trading) ---
    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"

    # --- Broker IBKR (live trading) ---
    IBKR_HOST: str = "127.0.0.1"
    IBKR_PORT: int = 7497  # 7497 = paper, 7496 = live
    IBKR_CLIENT_ID: int = 1
    IBKR_ACCOUNT_ID: str = ""
    IBKR_DEFAULT_EQUITY: float = 320.0     # Fallback si lecture compte IBKR échoue
    IBKR_INITIAL_CAPITAL: float = 320.0   # Capital initial déposé (pour calcul rendement)

    # --- Sentiment ---
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    NEWSAPI_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # --- FRED ---
    FRED_API_KEY: str = ""

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # --- App ---
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "https://*.vercel.app",
        "https://bilok-tradepilot.be",
        "https://*.bilok-tradepilot.be",
    ]
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
