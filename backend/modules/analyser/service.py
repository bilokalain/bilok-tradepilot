"""Module 2 — Analyseur de Stratégies : Logique métier

Corrigé avec la matrice de performance réelle issue des backtests.
Le Module 2 sélectionne maintenant la stratégie qui a le meilleur Sharpe
historique pour chaque actif, avec ajustement selon le régime de marché.

Intègre la détection de Strategy Decay : les stratégies en QUARANTINE
sont automatiquement écartées au profit de la suivante dans le classement.
"""

import logging

import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily, Signal, Position, PositionStatus
from backend.modules.analyser.decay import check_strategy_decay, StrategyPerformance
from backend.modules.analyser.regime import detect_regime
from backend.modules.analyser.strategies import run_all_strategies, ALL_STRATEGIES
from backend.modules.analyser.performance_matrix import (
    BACKTEST_MATRIX, get_best_strategy, get_strategy_sharpe,
    get_profitable_strategies, get_strategy_ranking,
)

logger = logging.getLogger(__name__)


# Poids de régime pour ajuster la sélection basée sur le backtest
# Si le régime favorise une stratégie, on boost son score
REGIME_BOOST = {
    "BULL": {"trend_following": 0.15, "momentum": 0.10, "breakout": 0.05},
    "BEAR": {"mean_reversion": 0.15, "trend_following": 0.10},
    "RANGE": {"mean_reversion": 0.20, "breakout": 0.10},
    "CRISIS": {"mean_reversion": 0.10},
    "TRANSITION": {"breakout": 0.15, "momentum": 0.10},
}


class AnalyserService:
    """Analyse le marché et sélectionne les stratégies basées sur les données empiriques."""

    def __init__(self, db: Session):
        self.db = db

    def _build_strategy_performance(self, strategy_name: str) -> StrategyPerformance:
        """Construit un StrategyPerformance depuis les positions clôturées en BDD."""
        # Positions clôturées liées à cette stratégie via la table signals
        rows = (
            self.db.query(Position.pnl, Position.pnl_percent)
            .join(Signal, Signal.asset_id == Position.asset_id)
            .filter(
                Signal.strategy_name == strategy_name,
                Position.status == PositionStatus.CLOSED,
                Position.pnl.isnot(None),
            )
            .all()
        )

        perf = StrategyPerformance(strategy_name=strategy_name)
        for pnl, pnl_pct in rows:
            perf.total_trades += 1
            ret = pnl_pct if pnl_pct is not None else 0.0
            perf.returns.append(ret)
            if pnl is not None and pnl > 0:
                perf.winning_trades += 1
                perf.total_profit += pnl
            elif pnl is not None:
                perf.total_loss += pnl  # négatif

        return perf

    def _filter_quarantined(self, ranked_strategies: list[dict]) -> tuple[list[dict], list[dict]]:
        """Filtre les stratégies en QUARANTINE du classement.

        Retourne (strategies_actives, strategies_quarantined).
        """
        active = []
        quarantined = []
        for entry in ranked_strategies:
            strat_name = entry["strategy"]
            perf = self._build_strategy_performance(strat_name)
            decay_result = check_strategy_decay(perf)
            entry["decay_status"] = decay_result["status"]
            entry["decay_health"] = decay_result["health_score"]

            if decay_result["status"] == "QUARANTINE":
                quarantined.append(entry)
                reasons = ", ".join(decay_result["reasons"])
                logger.warning(
                    "Strategy QUARANTINE : %s — health=%.0f — %s",
                    strat_name, decay_result["health_score"], reasons,
                )
            else:
                active.append(entry)

        return active, quarantined

    def _load_ohlcv(self, asset_id: int) -> pd.DataFrame:
        rows = (
            self.db.query(OHLCVDaily)
            .filter_by(asset_id=asset_id)
            .order_by(OHLCVDaily.date.asc())
            .all()
        )
        if not rows:
            return pd.DataFrame()

        data = [{"date": r.date, "open": r.open, "high": r.high,
                 "low": r.low, "close": r.close, "volume": r.volume} for r in rows]
        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        return df

    def analyse_asset(self, symbol: str) -> dict:
        """Analyse complète : régime + sélection stratégie empirique."""
        asset = self.db.query(Asset).filter_by(symbol=symbol).first()
        if not asset:
            return {"error": f"Actif {symbol} non trouvé"}

        df = self._load_ohlcv(asset.id)
        if df.empty or len(df) < 200:
            return {"error": f"Pas assez de données pour {symbol} ({len(df)} jours)"}

        # 1. Détection du régime
        regime_result = detect_regime(df["close"], df["high"], df["low"])
        regime = regime_result["regime"]

        # 2. Sélection par matrice de backtest + ajustement régime
        backtest_data = BACKTEST_MATRIX.get(symbol)
        ranking = get_strategy_ranking(symbol)

        if backtest_data:
            # Ajuster les Sharpe par le boost du régime
            boosts = REGIME_BOOST.get(regime, {})
            adjusted_ranking = []
            for entry in ranking:
                strat = entry["strategy"]
                base_sharpe = entry["sharpe"]
                boost = boosts.get(strat, 0)
                adjusted = base_sharpe + boost
                adjusted_ranking.append({
                    "strategy": strat,
                    "backtest_sharpe": entry["sharpe"],
                    "regime_boost": round(boost, 3),
                    "adjusted_sharpe": round(adjusted, 3),
                })
            adjusted_ranking.sort(key=lambda x: x["adjusted_sharpe"], reverse=True)

            # Filtrer les stratégies en quarantaine (Strategy Decay)
            active_strategies, quarantined = self._filter_quarantined(adjusted_ranking)

            if active_strategies:
                best = active_strategies[0]
                best_strategy = best["strategy"]
            elif adjusted_ranking:
                # Toutes en quarantaine — fallback sur la meilleure malgré tout
                logger.warning(
                    "Toutes les stratégies en quarantaine pour %s — fallback sur la première",
                    symbol,
                )
                best = adjusted_ranking[0]
                best_strategy = best["strategy"]
            else:
                best_strategy = "trend_following"
        else:
            adjusted_ranking = []
            quarantined = []
            best_strategy = "trend_following"  # Fallback

        # 3. Exécuter la stratégie sélectionnée pour obtenir le signal
        signal = self._run_strategy(
            best_strategy, df["close"], df["high"], df["low"], df["volume"]
        )

        # 4. Résultat enrichi
        return {
            "symbol": symbol,
            "name": asset.name,
            "asset_class": asset.asset_class.value,
            "regime": regime_result,
            "best_strategy": {
                "name": best_strategy,
                "direction": signal.get("direction", "NEUTRAL"),
                "conviction": signal.get("conviction", 0),
                "entry": signal.get("entry"),
                "stop_loss": signal.get("stop_loss"),
                "take_profit": signal.get("take_profit"),
                "backtest_sharpe": get_strategy_sharpe(symbol, best_strategy),
            },
            "strategy_ranking": adjusted_ranking,
            "quarantined_strategies": [q["strategy"] for q in quarantined],
            "profitable_strategies": get_profitable_strategies(symbol),
            "all_strategies": self._run_all_with_ranking(
                df["close"], df["high"], df["low"], df["volume"], symbol, regime
            ),
            "last_close": float(df["close"].iloc[-1]),
        }

    def _run_strategy(self, strategy_name: str, close, high, low, volume) -> dict:
        """Exécute une stratégie spécifique."""
        from backend.modules.analyser.strategies import (
            strategy_trend_following, strategy_mean_reversion,
            strategy_breakout, strategy_momentum,
        )
        strategies = {
            "trend_following": lambda: strategy_trend_following(close, high, low),
            "mean_reversion": lambda: strategy_mean_reversion(close, high, low),
            "breakout": lambda: strategy_breakout(close, high, low, volume),
            "momentum": lambda: strategy_momentum(close, high, low),
        }
        func = strategies.get(strategy_name)
        if func:
            return func()
        return {"direction": "NEUTRAL", "conviction": 0}

    def _run_all_with_ranking(self, close, high, low, volume,
                               symbol: str, regime: str) -> list[dict]:
        """Exécute toutes les stratégies et ajoute le Sharpe backtest."""
        results = run_all_strategies(close, high, low, volume, regime)
        for r in results:
            strat = r["strategy"]
            r["backtest_sharpe"] = get_strategy_sharpe(symbol, strat)
            # Score combiné : conviction actuelle × backtest
            bt_factor = max(0, (r["backtest_sharpe"] + 1) / 2)  # normaliser sharpe → 0-1
            r["combined_score"] = round(r["conviction"] * bt_factor, 1)
        results.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
        return results

    def analyse_all(self) -> list[dict]:
        """Analyse tous les actifs actifs."""
        assets = self.db.query(Asset).filter_by(is_active=True).all()
        results = []
        for asset in assets:
            result = self.analyse_asset(asset.symbol)
            if "error" not in result:
                results.append(result)

        results.sort(
            key=lambda x: x["best_strategy"].get("backtest_sharpe", 0),
            reverse=True,
        )
        return results

    def get_regime_summary(self) -> dict:
        """Résumé des régimes détectés pour tous les actifs."""
        assets = self.db.query(Asset).filter_by(is_active=True).all()
        regimes = {"BULL": 0, "BEAR": 0, "RANGE": 0, "CRISIS": 0, "TRANSITION": 0}

        for asset in assets:
            df = self._load_ohlcv(asset.id)
            if len(df) >= 200:
                result = detect_regime(df["close"], df["high"], df["low"])
                r = result["regime"]
                if r in regimes:
                    regimes[r] += 1

        dominant = max(regimes, key=regimes.get) if any(regimes.values()) else "UNKNOWN"
        return {
            "dominant_regime": dominant,
            "distribution": regimes,
            "total_assets": sum(regimes.values()),
        }
