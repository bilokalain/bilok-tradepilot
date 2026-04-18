"""
Full Backtest — 500 actifs × 9 stratégies
==========================================
Teste chaque stratégie sur chaque actif avec tout l'historique disponible.
Sauvegarde les résultats dans data/backtest_full_500.json

Usage: python scripts/full_backtest_500.py
Durée estimée: 2-4 heures (500 actifs × 9 stratégies)
"""

import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, ".")

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily
from backend.modules.analyser.backtester import run_backtest

DB_URL = "postgresql://tradepilot:tradepilot_dev@localhost:5432/tradepilot"
OUTPUT = Path("data/backtest_full_500.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("backtest")

STRATEGIES = [
    "trend_following",
    "mean_reversion",
    "breakout",
    "momentum",
    "adaptive_trend",
    "multi_signal",
    "keltner_breakout",
    "vwap_reversion",
    "momentum_rotation",
]

STRATEGY_LABELS = {
    "trend_following": "Trend Following",
    "mean_reversion": "Mean Reversion",
    "breakout": "Breakout",
    "momentum": "Momentum Adaptatif",
    "adaptive_trend": "Adaptive Trend",
    "multi_signal": "Multi-Signal",
    "keltner_breakout": "Keltner Breakout",
    "vwap_reversion": "VWAP Reversion",
    "momentum_rotation": "Momentum Rotation",
}


def load_ohlcv(session: Session, asset: Asset) -> pd.DataFrame:
    rows = session.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.asc()).all()
    if not rows:
        return pd.DataFrame()
    data = [{"date": r.date, "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume} for r in rows]
    df = pd.DataFrame(data)
    df.set_index("date", inplace=True)
    return df


def main():
    engine = create_engine(DB_URL)
    start_time = time.time()

    all_results = {}
    global_stats = {
        "total_assets": 0,
        "total_backtests": 0,
        "profitable_strategies": 0,
        "best_overall": None,
        "worst_overall": None,
        "by_strategy": {},
        "by_asset_class": {},
        "started_at": datetime.utcnow().isoformat(),
    }

    with Session(engine) as session:
        assets = session.query(Asset).filter_by(is_active=True).order_by(Asset.symbol).all()
        total = len(assets)
        global_stats["total_assets"] = total

        logger.info(f"")
        logger.info(f"{'═' * 65}")
        logger.info(f"  FULL BACKTEST — {total} actifs × {len(STRATEGIES)} stratégies")
        logger.info(f"  = {total * len(STRATEGIES)} backtests à calculer")
        logger.info(f"{'═' * 65}")

        for idx, asset in enumerate(assets):
            df = load_ohlcv(session, asset)
            if df.empty or len(df) < 250:
                logger.info(f"  [{idx+1}/{total}] {asset.symbol:12s} — SKIP ({len(df)} jours, min 250)")
                continue

            # Limiter à 5 ans (1260 jours) pour un temps de calcul raisonnable
            if len(df) > 1260:
                df = df.iloc[-1260:]

            asset_results = []
            best_sharpe = -999
            best_strat = None

            for strat in STRATEGIES:
                try:
                    result = run_backtest(df, strat, asset.symbol)
                    d = result.to_dict()
                    asset_results.append(d)
                    global_stats["total_backtests"] += 1

                    if d["sharpe_ratio"] > best_sharpe:
                        best_sharpe = d["sharpe_ratio"]
                        best_strat = strat

                    if d["total_return"] > 0:
                        global_stats["profitable_strategies"] += 1

                    # Stats par stratégie
                    if strat not in global_stats["by_strategy"]:
                        global_stats["by_strategy"][strat] = {
                            "total": 0, "profitable": 0, "avg_sharpe": 0,
                            "avg_return": 0, "best_asset": None, "best_return": -999,
                        }
                    ss = global_stats["by_strategy"][strat]
                    ss["total"] += 1
                    if d["total_return"] > 0:
                        ss["profitable"] += 1
                    ss["avg_sharpe"] = (ss["avg_sharpe"] * (ss["total"] - 1) + d["sharpe_ratio"]) / ss["total"]
                    ss["avg_return"] = (ss["avg_return"] * (ss["total"] - 1) + d["total_return"]) / ss["total"]
                    if d["total_return"] > ss["best_return"]:
                        ss["best_return"] = d["total_return"]
                        ss["best_asset"] = asset.symbol

                except Exception as e:
                    logger.warning(f"    {strat} failed: {e}")

            # Stats par classe d'actif
            ac = asset.asset_class.value
            if ac not in global_stats["by_asset_class"]:
                global_stats["by_asset_class"][ac] = {"count": 0, "avg_best_sharpe": 0, "total_profitable": 0}
            acs = global_stats["by_asset_class"][ac]
            acs["count"] += 1
            if best_sharpe > 0:
                acs["total_profitable"] += 1
            acs["avg_best_sharpe"] = (acs["avg_best_sharpe"] * (acs["count"] - 1) + best_sharpe) / acs["count"]

            # Meilleur/pire global
            if best_strat and (global_stats["best_overall"] is None or best_sharpe > global_stats["best_overall"]["sharpe"]):
                global_stats["best_overall"] = {"symbol": asset.symbol, "strategy": best_strat, "sharpe": best_sharpe}
            if best_strat and (global_stats["worst_overall"] is None or best_sharpe < global_stats["worst_overall"]["sharpe"]):
                global_stats["worst_overall"] = {"symbol": asset.symbol, "strategy": best_strat, "sharpe": best_sharpe}

            # Sauvegarder (sans equity_curve pour économiser l'espace)
            all_results[asset.symbol] = {
                "name": asset.name,
                "asset_class": ac,
                "data_points": len(df),
                "best_strategy": best_strat,
                "best_sharpe": round(best_sharpe, 3),
                "strategies": [{
                    "strategy": r["strategy"],
                    "total_return": r["total_return"],
                    "sharpe_ratio": r["sharpe_ratio"],
                    "win_rate": r["win_rate"],
                    "max_drawdown": r["max_drawdown"],
                    "num_trades": r["num_trades"],
                    "profit_factor": r["profit_factor"],
                } for r in asset_results],
            }

            elapsed = time.time() - start_time
            eta = elapsed / (idx + 1) * (total - idx - 1) if idx > 0 else 0
            logger.info(f"  [{idx+1}/{total}] {asset.symbol:12s} best={STRATEGY_LABELS.get(best_strat, '?'):20s} sharpe={best_sharpe:6.3f} ({len(df)} jours) ETA: {eta/60:.0f}min")

            # Sauvegarder tous les 50 actifs (checkpoint)
            if (idx + 1) % 50 == 0:
                _save(all_results, global_stats, start_time)

    # Sauvegarde finale
    _save(all_results, global_stats, start_time)
    _print_summary(global_stats, start_time)


def _save(results: dict, stats: dict, start_time: float):
    stats["completed_at"] = datetime.utcnow().isoformat()
    stats["duration_minutes"] = round((time.time() - start_time) / 60, 1)
    OUTPUT.write_text(json.dumps({
        "stats": stats,
        "results": results,
    }, default=str, indent=1))
    logger.info(f"  💾 Checkpoint sauvegardé ({len(results)} actifs)")


def _print_summary(stats: dict, start_time: float):
    duration = (time.time() - start_time) / 60
    logger.info(f"")
    logger.info(f"{'═' * 65}")
    logger.info(f"  RÉSULTATS — Full Backtest 500")
    logger.info(f"{'═' * 65}")
    logger.info(f"  Durée          : {duration:.0f} minutes")
    logger.info(f"  Backtests      : {stats['total_backtests']}")
    logger.info(f"  Profitables    : {stats['profitable_strategies']} ({stats['profitable_strategies']/max(stats['total_backtests'],1)*100:.0f}%)")
    logger.info(f"")

    if stats["best_overall"]:
        b = stats["best_overall"]
        logger.info(f"  Meilleur       : {b['symbol']} — {STRATEGY_LABELS.get(b['strategy'], b['strategy'])} (Sharpe {b['sharpe']:.3f})")
    if stats["worst_overall"]:
        w = stats["worst_overall"]
        logger.info(f"  Pire           : {w['symbol']} — {STRATEGY_LABELS.get(w['strategy'], w['strategy'])} (Sharpe {w['sharpe']:.3f})")

    logger.info(f"")
    logger.info(f"  Par stratégie :")
    for strat, ss in sorted(stats["by_strategy"].items(), key=lambda x: x[1]["avg_sharpe"], reverse=True):
        logger.info(f"    {STRATEGY_LABELS.get(strat, strat):22s}  Sharpe moy={ss['avg_sharpe']:.3f}  Win={ss['profitable']}/{ss['total']} ({ss['profitable']/max(ss['total'],1)*100:.0f}%)  Best={ss['best_asset']}")

    logger.info(f"")
    logger.info(f"  Par classe d'actif :")
    for ac, acs in sorted(stats["by_asset_class"].items()):
        logger.info(f"    {ac:15s}  {acs['count']} actifs  Sharpe moy={acs['avg_best_sharpe']:.3f}  Profitable={acs['total_profitable']}/{acs['count']}")

    logger.info(f"{'═' * 65}")


if __name__ == "__main__":
    main()
