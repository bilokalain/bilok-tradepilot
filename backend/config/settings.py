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

    # --- Broker ---
    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"

    # --- Sentiment ---
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    NEWSAPI_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # --- FRED ---
    FRED_API_KEY: str = ""

    # --- App ---
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
