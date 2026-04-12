"""Modèles SQLAlchemy — 5 couches de données Bilok-TradePilot

1. Raw Market Data — assets, ohlcv_daily, ohlcv_1h, ohlcv_5min
2. Features Précalculées — features_daily
3. Génome des Actifs — asset_genome
4. Signaux et Décisions — signals, orders
5. Trades et Performance — positions, performance_daily
"""

import enum
from datetime import datetime, date

from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Boolean, DateTime, Date,
    Enum, JSON, ForeignKey, UniqueConstraint, Index, Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# --- Enums ---

class AssetClass(str, enum.Enum):
    ACTION_US = "ACTION_US"
    ACTION_EU = "ACTION_EU"
    ETF = "ETF"
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    COMMODITY = "COMMODITY"


class SignalDirection(str, enum.Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


class OrderSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


class PositionStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class PortfolioRegime(str, enum.Enum):
    ALPHA = "ALPHA"
    BETA = "BETA"
    STRESS = "STRESS"


# ============================================================
# COUCHE 1 — Raw Market Data
# ============================================================

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    asset_class = Column(Enum(AssetClass), nullable=False)
    exchange = Column(String(50))
    sector = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    ohlcv_daily = relationship("OHLCVDaily", back_populates="asset")
    ohlcv_1h = relationship("OHLCV1H", back_populates="asset")
    ohlcv_5min = relationship("OHLCV5Min", back_populates="asset")
    features = relationship("FeaturesDaily", back_populates="asset")
    genome = relationship("AssetGenome", back_populates="asset", uselist=False)


class OHLCVDaily(Base):
    __tablename__ = "ohlcv_daily"
    __table_args__ = (
        UniqueConstraint("asset_id", "date", name="uq_ohlcv_daily_asset_date"),
        Index("ix_ohlcv_daily_date", "date"),
    )

    id = Column(BigInteger, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    source = Column(String(50), default="yahoo")

    asset = relationship("Asset", back_populates="ohlcv_daily")


class OHLCV1H(Base):
    __tablename__ = "ohlcv_1h"
    __table_args__ = (
        UniqueConstraint("asset_id", "datetime", name="uq_ohlcv_1h_asset_dt"),
    )

    id = Column(BigInteger, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    datetime = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    source = Column(String(50), default="yahoo")

    asset = relationship("Asset", back_populates="ohlcv_1h")


class OHLCV5Min(Base):
    __tablename__ = "ohlcv_5min"
    __table_args__ = (
        UniqueConstraint("asset_id", "datetime", name="uq_ohlcv_5min_asset_dt"),
    )

    id = Column(BigInteger, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    datetime = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    source = Column(String(50), default="binance")

    asset = relationship("Asset", back_populates="ohlcv_5min")


# ============================================================
# COUCHE 2 — Features Précalculées
# ============================================================

class FeaturesDaily(Base):
    __tablename__ = "features_daily"
    __table_args__ = (
        UniqueConstraint("asset_id", "date", name="uq_features_daily_asset_date"),
    )

    id = Column(BigInteger, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)

    # Indicateurs techniques
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    sma_200 = Column(Float)
    ema_12 = Column(Float)
    ema_26 = Column(Float)
    rsi_14 = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    bollinger_upper = Column(Float)
    bollinger_middle = Column(Float)
    bollinger_lower = Column(Float)
    atr_14 = Column(Float)
    stochastic_k = Column(Float)
    stochastic_d = Column(Float)

    # Scores des 9 critères du scanner
    score_correlation = Column(Float)
    score_sentiment = Column(Float)
    score_technical = Column(Float)
    score_genome = Column(Float)
    score_ipi = Column(Float)
    score_ivf = Column(Float)
    score_mts = Column(Float)
    score_sgi = Column(Float)
    score_sus = Column(Float)
    score_final = Column(Float)

    asset = relationship("Asset", back_populates="features")


# ============================================================
# COUCHE 3 — Génome des Actifs
# ============================================================

class AssetGenome(Base):
    """ADN comportemental de l'actif — une ligne par actif, MAJ hebdomadaire."""
    __tablename__ = "asset_genome"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), unique=True, nullable=False)

    # Phase de cycle (1-5)
    cycle_phase = Column(Integer)
    # Sismographe — 6 micro-signaux (JSON)
    seismograph = Column(JSON)
    # Mémoire fractale — cosine similarity patterns
    fractal_memory = Column(JSON)
    # Réseau de contagion inter-actifs
    contagion_network = Column(JSON)
    # Méta-données
    last_updated = Column(DateTime, default=datetime.utcnow)

    asset = relationship("Asset", back_populates="genome")


# ============================================================
# COUCHE 4 — Signaux et Décisions
# ============================================================

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    direction = Column(Enum(SignalDirection), nullable=False)
    score = Column(Float, nullable=False)
    context_quality = Column(Float)
    shelf_life_minutes = Column(Integer)

    # Thèse de trade
    entry_price = Column(Float)
    stop_loss = Column(Float)
    take_profit_1 = Column(Float)
    take_profit_2 = Column(Float)
    risk_reward_ratio = Column(Float)
    kelly_size = Column(Float)

    # Stratégie source
    strategy_name = Column(String(100))
    regime = Column(String(50))

    # Méta
    created_at = Column(DateTime, default=datetime.utcnow)
    expired_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)

    orders = relationship("Order", back_populates="signal")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    signal_id = Column(Integer, ForeignKey("signals.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float)
    filled_price = Column(Float)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    tranche = Column(Integer)  # 1, 2, 3 pour scaling
    broker = Column(String(50))
    broker_order_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    filled_at = Column(DateTime)

    signal = relationship("Signal", back_populates="orders")


# ============================================================
# COUCHE 5 — Trades et Performance
# ============================================================

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    direction = Column(Enum(SignalDirection), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    quantity = Column(Float, nullable=False)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    status = Column(Enum(PositionStatus), default=PositionStatus.OPEN)
    pnl = Column(Float)
    pnl_percent = Column(Float)
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime)

    # Attribution causale (Module 6)
    attribution = Column(JSON)


class PerformanceDaily(Base):
    __tablename__ = "performance_daily"
    __table_args__ = (
        UniqueConstraint("date", name="uq_performance_daily_date"),
    )

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    equity = Column(Float, nullable=False)
    daily_pnl = Column(Float)
    daily_return = Column(Float)
    cumulative_return = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    meta_score = Column(Float)  # 0-100, santé du système
    portfolio_regime = Column(Enum(PortfolioRegime))
    ews_level = Column(String(20))  # NORMAL / ATTENTION / ALERTE / CRITIQUE
