"""Analyse profonde — Backtest 10 ans + Saisonnalité + Walk-Forward + Cycles

Utilise les 1.6M barres daily pour :
1. Backtester les 4 stratégies sur 10 ans (au lieu de 2)
2. Détecter les patterns saisonniers (mois par mois)
3. Walk-forward robuste (fenêtres glissantes)
4. Analyser les cycles économiques (récessions, crises, bull markets)

Résultats sauvegardés dans data/deep_analysis.json
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, ".")

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily
from backend.modules.analyser.backtester import run_backtest, run_walk_forward

DB_URL = "postgresql://tradepilot:tradepilot_dev@localhost:5432/tradepilot"
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

STRATEGIES = ["trend_following", "mean_reversion", "breakout", "momentum"]


def load_ohlcv(session, asset_id):
    rows = session.query(OHLCVDaily).filter_by(asset_id=asset_id).order_by(OHLCVDaily.date.asc()).all()
    if not rows:
        return pd.DataFrame()
    data = [{"date": r.date, "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume} for r in rows]
    df = pd.DataFrame(data)
    df.set_index("date", inplace=True)
    return df


# ============================================================
# 1. BACKTEST 10 ANS
# ============================================================

def run_backtest_10y(session):
    """Backtest sur les 10 dernières années (2516 jours de trading)."""
    print("\n" + "=" * 80)
    print("  1. BACKTEST 10 ANS — 218 actifs × 4 stratégies")
    print("=" * 80)

    assets = session.query(Asset).filter_by(is_active=True).all()
    results = []
    best_per_asset = {}

    for i, asset in enumerate(assets):
        df = load_ohlcv(session, asset.id)
        if len(df) < 2520:  # ~10 ans minimum
            continue

        # Prendre les 10 dernières années
        df_10y = df.iloc[-2520:]

        best_sharpe = -999
        best_strat = ""
        asset_results = {}

        for strat in STRATEGIES:
            bt = run_backtest(df_10y, strat, asset.symbol)
            asset_results[strat] = {
                "return": round(bt.total_return, 2),
                "sharpe": round(bt.sharpe_ratio, 3),
                "win_rate": round(bt.win_rate, 1),
                "max_dd": round(bt.max_drawdown, 2),
                "trades": bt.num_trades,
                "pf": round(bt.profit_factor, 2),
                "calmar": round(bt.calmar_ratio, 3),
            }
            if bt.sharpe_ratio > best_sharpe:
                best_sharpe = bt.sharpe_ratio
                best_strat = strat

        results.append({
            "symbol": asset.symbol,
            "asset_class": asset.asset_class.value,
            "data_years": round(len(df) / 252, 1),
            "best_strategy": best_strat,
            "best_sharpe": round(best_sharpe, 3),
            "strategies": asset_results,
        })
        best_per_asset[asset.symbol] = {"best": best_strat, "sharpe": round(best_sharpe, 3), "all": {k: v["sharpe"] for k, v in asset_results.items()}}

        if (i + 1) % 20 == 0:
            print(f"  [{i + 1}/{len(assets)}] {asset.symbol:12} → {best_strat:18} Sharpe={best_sharpe:.3f}")

    # Top 20
    results.sort(key=lambda x: x["best_sharpe"], reverse=True)
    print(f"\n  TOP 20 (sur {len(results)} actifs avec 10+ ans):")
    for r in results[:20]:
        print(f"    {r['symbol']:12} {r['asset_class']:12} {r['best_strategy']:18} Sharpe={r['best_sharpe']:.3f}  Return={r['strategies'][r['best_strategy']]['return']:.1f}%")

    return results, best_per_asset


# ============================================================
# 2. PATTERNS SAISONNIERS
# ============================================================

def analyse_seasonality(session):
    """Analyse les rendements par mois sur l'historique complet."""
    print("\n" + "=" * 80)
    print("  2. PATTERNS SAISONNIERS — Rendements par mois")
    print("=" * 80)

    assets = session.query(Asset).filter_by(is_active=True).all()
    seasonality = {}

    for asset in assets:
        df = load_ohlcv(session, asset.id)
        if len(df) < 252 * 5:  # minimum 5 ans
            continue

        df_dt = df.copy()
        df_dt.index = pd.to_datetime(df_dt.index)
        monthly_returns = df_dt["close"].resample("M").last().pct_change().dropna()
        if monthly_returns.empty:
            continue

        by_month = {}
        for month in range(1, 13):
            month_data = monthly_returns[monthly_returns.index.month == month]
            if len(month_data) >= 3:
                by_month[month] = {
                    "avg_return": round(float(month_data.mean()) * 100, 3),
                    "win_rate": round(float((month_data > 0).mean()) * 100, 1),
                    "best": round(float(month_data.max()) * 100, 2),
                    "worst": round(float(month_data.min()) * 100, 2),
                    "samples": len(month_data),
                }

        if by_month:
            best_month = max(by_month, key=lambda m: by_month[m]["avg_return"])
            worst_month = min(by_month, key=lambda m: by_month[m]["avg_return"])
            seasonality[asset.symbol] = {
                "months": by_month,
                "best_month": best_month,
                "worst_month": worst_month,
                "best_avg": by_month[best_month]["avg_return"],
                "worst_avg": by_month[worst_month]["avg_return"],
            }

    # Résumé
    month_names = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]

    # Agrégation globale (tous les actifs)
    global_months = {}
    for month in range(1, 13):
        returns = [s["months"][month]["avg_return"] for s in seasonality.values() if month in s["months"]]
        if returns:
            global_months[month_names[month - 1]] = {
                "avg_return": round(np.mean(returns), 3),
                "positive_assets": sum(1 for r in returns if r > 0),
                "total_assets": len(returns),
            }

    print(f"\n  Saisonnalité globale ({len(seasonality)} actifs):")
    for name, data in global_months.items():
        bar = "█" * max(1, int(abs(data["avg_return"]) * 10))
        sign = "+" if data["avg_return"] > 0 else ""
        print(f"    {name:4} {sign}{data['avg_return']:.2f}%  {bar}  ({data['positive_assets']}/{data['total_assets']} positifs)")

    return seasonality, global_months


# ============================================================
# 3. WALK-FORWARD ROBUSTE
# ============================================================

def run_walk_forward_deep(session):
    """Walk-forward sur 10 fenêtres glissantes (beaucoup plus robuste)."""
    print("\n" + "=" * 80)
    print("  3. WALK-FORWARD ROBUSTE — 10 fenêtres glissantes")
    print("=" * 80)

    assets = session.query(Asset).filter_by(is_active=True).all()
    wf_results = {}

    count = 0
    for asset in assets:
        df = load_ohlcv(session, asset.id)
        if len(df) < 2520:  # 10 ans minimum
            continue

        # Walk-forward avec 10 folds
        best_wf = None
        best_consistency = 0

        for strat in STRATEGIES:
            wf = run_walk_forward(df.iloc[-2520:], strat, asset.symbol, n_folds=10)
            consistency = wf["summary"]["consistency"]

            if consistency > best_consistency:
                best_consistency = consistency
                best_wf = wf

        if best_wf:
            wf_results[asset.symbol] = {
                "strategy": best_wf["strategy"],
                "consistency": best_wf["summary"]["consistency"],
                "avg_return": best_wf["summary"]["avg_return"],
                "avg_sharpe": best_wf["summary"]["avg_sharpe"],
                "avg_win_rate": best_wf["summary"]["avg_win_rate"],
                "avg_max_dd": best_wf["summary"]["avg_max_drawdown"],
                "n_folds": best_wf["n_folds"],
            }

        count += 1
        if count % 20 == 0:
            print(f"  [{count}] {asset.symbol:12} → consistency={best_consistency:.0f}%")

    # Top consistants
    sorted_wf = sorted(wf_results.items(), key=lambda x: x[1]["consistency"], reverse=True)
    print(f"\n  TOP 15 plus consistants ({len(wf_results)} actifs testés):")
    for sym, data in sorted_wf[:15]:
        print(f"    {sym:12} {data['strategy']:18} consistency={data['consistency']:.0f}%  Sharpe={data['avg_sharpe']:.3f}  WR={data['avg_win_rate']:.0f}%")

    return wf_results


# ============================================================
# 4. CYCLES ÉCONOMIQUES
# ============================================================

def analyse_economic_cycles(session):
    """Performance pendant les grandes crises et bull markets."""
    print("\n" + "=" * 80)
    print("  4. ANALYSE DES CYCLES ÉCONOMIQUES")
    print("=" * 80)

    # Périodes historiques clés
    CYCLES = {
        "Dot-com Crash (2000-2002)": ("2000-03-10", "2002-10-09"),
        "Bull Market (2003-2007)": ("2003-03-12", "2007-10-09"),
        "Crise Financière (2007-2009)": ("2007-10-09", "2009-03-09"),
        "Bull Market Post-2009 (2009-2020)": ("2009-03-09", "2020-02-19"),
        "COVID Crash (Feb-Mar 2020)": ("2020-02-19", "2020-03-23"),
        "Recovery COVID (2020-2021)": ("2020-03-23", "2021-12-31"),
        "Bear Market 2022": ("2022-01-03", "2022-10-12"),
        "Rally IA (2023-2024)": ("2023-01-01", "2024-12-31"),
        "Période récente (2025-2026)": ("2025-01-01", "2026-04-12"),
    }

    assets = session.query(Asset).filter_by(is_active=True).all()
    cycle_performance = {}

    for cycle_name, (start, end) in CYCLES.items():
        from datetime import date as dt_date
        start_date = pd.to_datetime(start).date()
        end_date = pd.to_datetime(end).date()
        cycle_perf = []

        for asset in assets:
            df = load_ohlcv(session, asset.id)
            if df.empty:
                continue

            # Convertir l'index en date si nécessaire
            dates = [d if isinstance(d, dt_date) else d.date() for d in df.index]
            mask = [(d >= start_date and d <= end_date) for d in dates]
            period = df.iloc[[i for i, m in enumerate(mask) if m]]

            if len(period) < 10:
                continue

            ret = (float(period["close"].iloc[-1]) / float(period["close"].iloc[0]) - 1) * 100
            cycle_perf.append({
                "symbol": asset.symbol,
                "asset_class": asset.asset_class.value,
                "return": round(ret, 2),
                "days": len(period),
            })

        if cycle_perf:
            cycle_perf.sort(key=lambda x: x["return"], reverse=True)
            avg_return = np.mean([c["return"] for c in cycle_perf])

            cycle_performance[cycle_name] = {
                "start": start,
                "end": end,
                "avg_return": round(avg_return, 2),
                "num_assets": len(cycle_perf),
                "best_5": cycle_perf[:5],
                "worst_5": cycle_perf[-5:],
            }

            print(f"\n  {cycle_name}")
            print(f"    Rendement moyen : {avg_return:+.1f}%  ({len(cycle_perf)} actifs)")
            top3 = ", ".join(c["symbol"] + " " + f'{c["return"]:+.0f}%' for c in cycle_perf[:3])
            flop3 = ", ".join(c["symbol"] + " " + f'{c["return"]:+.0f}%' for c in cycle_perf[-3:])
            print(f"    Top 3 : {top3}")
            print(f"    Flop 3 : {flop3}")

    return cycle_performance


# ============================================================
# MAIN
# ============================================================

def main():
    start_time = time.time()
    engine = create_engine(DB_URL)

    with Session(engine) as session:
        # 1. Backtest 10 ans
        bt_results, bt_matrix = run_backtest_10y(session)

        # 2. Saisonnalité
        seasonality, global_months = analyse_seasonality(session)

        # 3. Walk-forward
        wf_results = run_walk_forward_deep(session)

        # 4. Cycles économiques
        cycles = analyse_economic_cycles(session)

    # Sauvegarder tout
    output = {
        "generated_at": datetime.utcnow().isoformat(),
        "duration_seconds": round(time.time() - start_time),
        "backtest_10y": {
            "num_assets": len(bt_results),
            "top_20": bt_results[:20],
            "matrix": bt_matrix,
        },
        "seasonality": {
            "global": global_months,
            "per_asset_count": len(seasonality),
        },
        "walk_forward": {
            "num_assets": len(wf_results),
            "top_15": dict(list(sorted(wf_results.items(), key=lambda x: x[1]["consistency"], reverse=True))[:15]),
        },
        "economic_cycles": cycles,
    }

    output_file = OUTPUT_DIR / "deep_analysis.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)

    elapsed = time.time() - start_time
    print(f"\n{'=' * 80}")
    print(f"  ANALYSE TERMINÉE en {elapsed / 60:.1f} minutes")
    print(f"  Résultats sauvegardés dans {output_file}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
