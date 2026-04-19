"""Moteur de Backtesting + Walk-Forward

Teste les stratégies du Module 2 sur les données historiques.

Walk-forward : fenêtre glissante train (80%) + test (20%)
- Optimise les paramètres sur train
- Valide la performance sur test (out-of-sample)

Métriques produites :
- Rendement total / annualisé
- Sharpe Ratio
- Max Drawdown
- Win Rate
- Profit Factor
- Nombre de trades
- Calmar Ratio
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import date

from backend.modules.scanner.indicators import (
    sma, ema, rsi, macd, bollinger_bands, atr, stochastic,
)
from backend.modules.analyser.strategies import (
    strategy_trend_following, strategy_mean_reversion,
    strategy_breakout, strategy_momentum,
)
from backend.modules.analyser.strategies_advanced import (
    strategy_mean_reversion_v2, strategy_fibonacci, strategy_ichimoku,
)
from backend.modules.analyser.strategies_pro import (
    strategy_adaptive_trend, strategy_multi_signal,
    strategy_keltner_breakout, strategy_vwap_reversion,
    strategy_momentum_rotation,
)
from backend.modules.analyser.strategies_genius import (
    strategy_regime_cascade, strategy_volatility_explosion,
    strategy_anti_consensus,
)


# Frais de transaction réalistes
COMMISSION_PCT = 0.001     # 0.1% par côté (entrée + sortie = 0.2%)
SLIPPAGE_PCT = 0.0005      # 0.05% de slippage moyen par exécution


@dataclass
class BacktestTrade:
    entry_date: date
    exit_date: date | None = None
    direction: str = "LONG"
    entry_price: float = 0
    exit_price: float = 0
    quantity: float = 1
    pnl: float = 0
    pnl_pct: float = 0
    fees: float = 0
    strategy: str = ""
    exit_reason: str = ""


@dataclass
class BacktestResult:
    strategy: str
    symbol: str
    period: str
    trades: list[BacktestTrade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)

    @property
    def total_return(self) -> float:
        if not self.equity_curve or self.equity_curve[0] == 0:
            return 0
        return (self.equity_curve[-1] / self.equity_curve[0] - 1) * 100

    @property
    def num_trades(self) -> int:
        return len(self.trades)

    @property
    def winning_trades(self) -> int:
        return sum(1 for t in self.trades if t.pnl > 0)

    @property
    def win_rate(self) -> float:
        return self.winning_trades / self.num_trades * 100 if self.num_trades else 0

    @property
    def total_fees(self) -> float:
        return sum(t.fees for t in self.trades)

    @property
    def profit_factor(self) -> float:
        gains = sum(t.pnl for t in self.trades if t.pnl > 0)
        losses = abs(sum(t.pnl for t in self.trades if t.pnl < 0))
        return gains / losses if losses > 0 else float("inf") if gains > 0 else 0

    @property
    def max_drawdown(self) -> float:
        if not self.equity_curve:
            return 0
        peak = self.equity_curve[0]
        max_dd = 0
        for eq in self.equity_curve:
            if eq > peak:
                peak = eq
            dd = (eq - peak) / peak * 100
            if dd < max_dd:
                max_dd = dd
        return max_dd

    @property
    def sharpe_ratio(self) -> float:
        if len(self.equity_curve) < 2:
            return 0
        returns = pd.Series(self.equity_curve).pct_change().dropna()
        if returns.std() == 0:
            return 0
        return float(returns.mean() / returns.std() * np.sqrt(252))

    @property
    def calmar_ratio(self) -> float:
        dd = abs(self.max_drawdown)
        if dd == 0:
            return 0
        days = len(self.equity_curve)
        annual_return = self.total_return * 252 / days if days > 0 else 0
        return annual_return / dd

    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy,
            "symbol": self.symbol,
            "period": self.period,
            "total_return": round(self.total_return, 2),
            "num_trades": self.num_trades,
            "winning_trades": self.winning_trades,
            "win_rate": round(self.win_rate, 1),
            "profit_factor": round(self.profit_factor, 2),
            "max_drawdown": round(self.max_drawdown, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 3),
            "calmar_ratio": round(self.calmar_ratio, 3),
            "total_fees": round(self.total_fees, 2),
            "equity_curve": [round(e, 2) for e in self.equity_curve[::5]],  # échantillonné
            "trades": [
                {
                    "entry_date": str(t.entry_date),
                    "exit_date": str(t.exit_date) if t.exit_date else None,
                    "direction": t.direction,
                    "entry_price": round(t.entry_price, 2),
                    "exit_price": round(t.exit_price, 2),
                    "pnl": round(t.pnl, 2),
                    "pnl_pct": round(t.pnl_pct, 2),
                    "exit_reason": t.exit_reason,
                }
                for t in self.trades[-20:]  # derniers 20 trades
            ],
        }


def _apply_slippage(price: float, direction: str, is_entry: bool) -> float:
    """Applique le slippage au prix.

    Entrée : on paye plus cher (LONG) ou on vend moins cher (SHORT)
    Sortie : inverse
    """
    if (direction == "LONG" and is_entry) or (direction == "SHORT" and not is_entry):
        return price * (1 + SLIPPAGE_PCT)
    return price * (1 - SLIPPAGE_PCT)


def _compute_fees(price: float, quantity: float) -> float:
    """Calcule les frais de commission pour une transaction."""
    return price * quantity * COMMISSION_PCT


def run_backtest(df: pd.DataFrame, strategy_name: str, symbol: str,
                 initial_capital: float = 100_000,
                 risk_per_trade: float = 0.02) -> BacktestResult:
    """Exécute un backtest sur un DataFrame OHLCV.

    Paramètres :
    - risk_per_trade : fraction du capital risquée par trade (2%)

    Inclut les frais de commission (0.1% par côté) et le slippage (0.05%).
    """
    result = BacktestResult(
        strategy=strategy_name,
        symbol=symbol,
        period=f"{df.index[0]} → {df.index[-1]}",
    )

    capital = initial_capital
    position = None  # BacktestTrade en cours
    result.equity_curve = [capital]

    for i in range(200, len(df)):  # besoin de 200 barres d'historique
        window = df.iloc[:i + 1]
        close = window["close"]
        high = window["high"]
        low = window["low"]
        volume = window["volume"]
        current_price = float(close.iloc[-1])
        current_date = window.index[-1]

        # Calculer ATR pour le sizing
        atr_val = atr(high, low, close, 14).iloc[-1]
        if np.isnan(atr_val) or atr_val == 0:
            result.equity_curve.append(capital)
            continue

        # --- Gestion position existante ---
        if position:
            if position.direction == "LONG":
                # Check stop loss
                if current_price <= position.entry_price - 2 * atr_val:
                    position.exit_price = _apply_slippage(current_price, "LONG", is_entry=False)
                    position.exit_date = current_date
                    exit_fees = _compute_fees(position.exit_price, position.quantity)
                    position.fees += exit_fees
                    position.pnl = (position.exit_price - position.entry_price) * position.quantity - exit_fees
                    position.pnl_pct = (position.exit_price / position.entry_price - 1) * 100
                    position.exit_reason = "STOP_LOSS"
                    capital += position.pnl
                    result.trades.append(position)
                    position = None
                # Check take profit (3 ATR)
                elif current_price >= position.entry_price + 3 * atr_val:
                    position.exit_price = _apply_slippage(current_price, "LONG", is_entry=False)
                    position.exit_date = current_date
                    exit_fees = _compute_fees(position.exit_price, position.quantity)
                    position.fees += exit_fees
                    position.pnl = (position.exit_price - position.entry_price) * position.quantity - exit_fees
                    position.pnl_pct = (position.exit_price / position.entry_price - 1) * 100
                    position.exit_reason = "TAKE_PROFIT"
                    capital += position.pnl
                    result.trades.append(position)
                    position = None

            elif position.direction == "SHORT":
                if current_price >= position.entry_price + 2 * atr_val:
                    position.exit_price = _apply_slippage(current_price, "SHORT", is_entry=False)
                    position.exit_date = current_date
                    exit_fees = _compute_fees(position.exit_price, position.quantity)
                    position.fees += exit_fees
                    position.pnl = (position.entry_price - position.exit_price) * position.quantity - exit_fees
                    position.pnl_pct = (1 - position.exit_price / position.entry_price) * 100
                    position.exit_reason = "STOP_LOSS"
                    capital += position.pnl
                    result.trades.append(position)
                    position = None
                elif current_price <= position.entry_price - 3 * atr_val:
                    position.exit_price = _apply_slippage(current_price, "SHORT", is_entry=False)
                    position.exit_date = current_date
                    exit_fees = _compute_fees(position.exit_price, position.quantity)
                    position.fees += exit_fees
                    position.pnl = (position.entry_price - position.exit_price) * position.quantity - exit_fees
                    position.pnl_pct = (1 - position.exit_price / position.entry_price) * 100
                    position.exit_reason = "TAKE_PROFIT"
                    capital += position.pnl
                    result.trades.append(position)
                    position = None

            # Mettre à jour l'equity avec la position ouverte
            if position:
                if position.direction == "LONG":
                    unrealized = (current_price - position.entry_price) * position.quantity
                else:
                    unrealized = (position.entry_price - current_price) * position.quantity
                result.equity_curve.append(capital + unrealized)
                continue

        # --- Pas de position → chercher un signal ---
        if position is None:
            signal = _get_strategy_signal(strategy_name, close, high, low, volume)

            if signal["direction"] != "NEUTRAL" and signal["conviction"] > 50:
                # Sizing basé sur le risque
                risk_amount = capital * risk_per_trade
                stop_distance = 2 * atr_val
                quantity = risk_amount / stop_distance if stop_distance > 0 else 0

                if quantity > 0:
                    slipped_entry = _apply_slippage(current_price, signal["direction"], is_entry=True)
                    entry_fees = _compute_fees(slipped_entry, round(quantity, 4))
                    capital -= entry_fees
                    position = BacktestTrade(
                        entry_date=current_date,
                        direction=signal["direction"],
                        entry_price=slipped_entry,
                        quantity=round(quantity, 4),
                        strategy=strategy_name,
                        fees=entry_fees,
                    )

        result.equity_curve.append(capital)

    # Fermer la position ouverte à la fin
    if position:
        raw_exit = float(df["close"].iloc[-1])
        position.exit_price = _apply_slippage(raw_exit, position.direction, is_entry=False)
        position.exit_date = df.index[-1]
        exit_fees = _compute_fees(position.exit_price, position.quantity)
        position.fees += exit_fees
        if position.direction == "LONG":
            position.pnl = (position.exit_price - position.entry_price) * position.quantity - exit_fees
            position.pnl_pct = (position.exit_price / position.entry_price - 1) * 100
        else:
            position.pnl = (position.entry_price - position.exit_price) * position.quantity - exit_fees
            position.pnl_pct = (1 - position.exit_price / position.entry_price) * 100
        position.exit_reason = "END_OF_DATA"
        capital += position.pnl
        result.trades.append(position)
        result.equity_curve[-1] = capital

    return result


def run_walk_forward(df: pd.DataFrame, strategy_name: str, symbol: str,
                     n_folds: int = 5, train_pct: float = 0.8) -> dict:
    """Walk-forward testing : validation out-of-sample.

    Découpe les données en n_folds fenêtres glissantes.
    Chaque fenêtre : 80% train + 20% test.
    """
    total_len = len(df)
    fold_size = total_len // n_folds
    results = []

    for fold in range(n_folds):
        start = fold * fold_size
        end = min(start + fold_size, total_len)
        fold_data = df.iloc[start:end]

        if len(fold_data) < 250:  # min 250 barres
            continue

        split = int(len(fold_data) * train_pct)
        train_data = fold_data.iloc[:split]
        test_data = fold_data.iloc[split:]

        if len(test_data) < 50:
            continue

        # Backtest sur fold complet (train+test) pour que les indicateurs
        # se réchauffent sur les données train — élimine le look-ahead bias.
        # Seuls les trades dont l'entrée tombe dans la période test comptent.
        full_result = run_backtest(fold_data, strategy_name, symbol)

        test_start_date = test_data.index[0]
        test_trades = [t for t in full_result.trades if t.entry_date >= test_start_date]

        # Reconstruire l'equity curve à partir des trades test uniquement
        test_equity = [full_result.equity_curve[0]]  # capital initial
        capital = test_equity[0]
        for t in test_trades:
            capital += t.pnl
            test_equity.append(capital)

        test_result = BacktestResult(
            strategy=strategy_name,
            symbol=symbol,
            period=f"{test_start_date} → {fold_data.index[-1]}",
            trades=test_trades,
            equity_curve=test_equity,
        )

        results.append({
            "fold": fold + 1,
            "train_period": f"{train_data.index[0]} → {train_data.index[-1]}",
            "test_period": f"{test_data.index[0]} → {test_data.index[-1]}",
            "test_days": len(test_data),
            **test_result.to_dict(),
        })

    # Métriques agrégées
    if results:
        avg_return = np.mean([r["total_return"] for r in results])
        avg_sharpe = np.mean([r["sharpe_ratio"] for r in results])
        avg_win_rate = np.mean([r["win_rate"] for r in results])
        avg_drawdown = np.mean([r["max_drawdown"] for r in results])
        consistency = sum(1 for r in results if r["total_return"] > 0) / len(results) * 100
    else:
        avg_return = avg_sharpe = avg_win_rate = avg_drawdown = consistency = 0

    return {
        "strategy": strategy_name,
        "symbol": symbol,
        "n_folds": len(results),
        "summary": {
            "avg_return": round(avg_return, 2),
            "avg_sharpe": round(avg_sharpe, 3),
            "avg_win_rate": round(avg_win_rate, 1),
            "avg_max_drawdown": round(avg_drawdown, 2),
            "consistency": round(consistency, 1),
        },
        "folds": results,
    }


def _get_strategy_signal(strategy_name: str, close: pd.Series, high: pd.Series,
                          low: pd.Series, volume: pd.Series) -> dict:
    """Appelle la bonne stratégie — 9 stratégies supportées."""
    try:
        # Classiques
        if strategy_name == "trend_following":
            return strategy_trend_following(close, high, low)
        elif strategy_name == "mean_reversion":
            return strategy_mean_reversion(close, high, low)
        elif strategy_name == "breakout":
            return strategy_breakout(close, high, low, volume)
        elif strategy_name == "momentum":
            return strategy_momentum(close, high, low)
        # Avancées
        elif strategy_name == "mean_reversion_v2":
            return strategy_mean_reversion_v2(close, high, low, volume)
        elif strategy_name == "fibonacci":
            return strategy_fibonacci(close, high, low)
        elif strategy_name == "ichimoku":
            return strategy_ichimoku(close, high, low)
        # Pro
        elif strategy_name == "adaptive_trend":
            return strategy_adaptive_trend(close, high, low, volume)
        elif strategy_name == "multi_signal":
            return strategy_multi_signal(close, high, low, volume)
        elif strategy_name == "keltner_breakout":
            return strategy_keltner_breakout(close, high, low, volume)
        elif strategy_name == "vwap_reversion":
            return strategy_vwap_reversion(close, high, low, volume)
        elif strategy_name == "momentum_rotation":
            return strategy_momentum_rotation(close, high, low, volume)
        # Genius
        elif strategy_name == "regime_cascade":
            return strategy_regime_cascade(close, high, low, volume)
        elif strategy_name == "volatility_explosion":
            return strategy_volatility_explosion(close, high, low, volume)
        elif strategy_name == "anti_consensus":
            return strategy_anti_consensus(close, high, low, volume)
        else:
            return {"direction": "NEUTRAL", "conviction": 0}
    except Exception:
        return {"direction": "NEUTRAL", "conviction": 0}
