"""Backtest des 5 stratégies pro sur 218 actifs × 10 ans

Compare les stratégies pro vs classiques pour voir si elles apportent
un vrai avantage.

Résultats sauvegardés dans data/backtest_pro.json
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, ".")

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily
from backend.modules.analyser.backtester import run_backtest

DB_URL = "postgresql://tradepilot:tradepilot_dev@localhost:5432/tradepilot"
OUTPUT = Path("data/backtest_pro.json")
OUTPUT.parent.mkdir(exist_ok=True)

# Toutes les stratégies à tester (classiques + pro)
# Note: les pro utilisent les mêmes signatures que breakout (close, high, low, volume)
ALL_STRATEGIES = [
    "trend_following", "mean_reversion", "breakout", "momentum",
    "adaptive_trend", "multi_signal", "keltner_breakout", "vwap_reversion", "momentum_rotation",
]


def main():
    start_time = time.time()
    engine = create_engine(DB_URL)

    # Ajouter les stratégies pro au backtester
    # Le backtester utilise _get_strategy_signal — on doit le patcher
    import backend.modules.analyser.backtester as bt_module
    from backend.modules.analyser.strategies_pro import (
        strategy_adaptive_trend, strategy_multi_signal,
        strategy_keltner_breakout, strategy_vwap_reversion,
        strategy_momentum_rotation,
    )

    original_get_signal = bt_module._get_strategy_signal

    def patched_get_signal(strategy_name, close, high, low, volume):
        if strategy_name == "adaptive_trend":
            return strategy_adaptive_trend(close, high, low, volume)
        elif strategy_name == "multi_signal":
            return strategy_multi_signal(close, high, low, volume)
        elif strategy_name == "keltner_breakout":
            return strategy_keltner_breakout(close, high, low, volume)
        elif strategy_name == "vwap_reversion":
            return strategy_vwap_reversion(close, high, low, volume)
        elif strategy_name == "momentum_rotation":
            return strategy_momentum_rotation(close, high, low, volume)
        else:
            return original_get_signal(strategy_name, close, high, low, volume)

    bt_module._get_strategy_signal = patched_get_signal

    results = []
    pro_vs_classic = {"pro_wins": 0, "classic_wins": 0, "tie": 0}

    with Session(engine) as session:
        assets = session.query(Asset).filter_by(is_active=True).all()
        print(f"\nBacktest PRO — {len(assets)} actifs × {len(ALL_STRATEGIES)} stratégies")
        print(f"{'='*90}")

        for i, asset in enumerate(assets):
            rows = session.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.asc()).all()
            if len(rows) < 500:
                continue

            data = [{"date": r.date, "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume} for r in rows]
            df = pd.DataFrame(data)
            df.set_index("date", inplace=True)

            # Prendre les 10 dernières années ou tout si < 10 ans
            df_test = df.iloc[-2520:] if len(df) >= 2520 else df

            asset_results = {}
            best_classic_sharpe = -999
            best_classic_strat = ""
            best_pro_sharpe = -999
            best_pro_strat = ""

            for strat in ALL_STRATEGIES:
                try:
                    bt = run_backtest(df_test, strat, asset.symbol)
                    sharpe = bt.sharpe_ratio
                    asset_results[strat] = {
                        "return": round(bt.total_return, 2),
                        "sharpe": round(sharpe, 3),
                        "win_rate": round(bt.win_rate, 1),
                        "max_dd": round(bt.max_drawdown, 2),
                        "trades": bt.num_trades,
                        "pf": round(bt.profit_factor, 2),
                    }

                    if strat in ("trend_following", "mean_reversion", "breakout", "momentum"):
                        if sharpe > best_classic_sharpe:
                            best_classic_sharpe = sharpe
                            best_classic_strat = strat
                    else:
                        if sharpe > best_pro_sharpe:
                            best_pro_sharpe = sharpe
                            best_pro_strat = strat
                except Exception as e:
                    asset_results[strat] = {"error": str(e)}

            # Comparaison pro vs classique
            if best_pro_sharpe > best_classic_sharpe + 0.05:
                pro_vs_classic["pro_wins"] += 1
                winner = "PRO"
            elif best_classic_sharpe > best_pro_sharpe + 0.05:
                pro_vs_classic["classic_wins"] += 1
                winner = "CLASSIC"
            else:
                pro_vs_classic["tie"] += 1
                winner = "TIE"

            results.append({
                "symbol": asset.symbol,
                "asset_class": asset.asset_class.value,
                "best_classic": {"strategy": best_classic_strat, "sharpe": round(best_classic_sharpe, 3)},
                "best_pro": {"strategy": best_pro_strat, "sharpe": round(best_pro_sharpe, 3)},
                "winner": winner,
                "improvement": round(best_pro_sharpe - best_classic_sharpe, 3),
                "strategies": asset_results,
            })

            if (i + 1) % 20 == 0:
                elapsed = time.time() - start_time
                print(f"  [{i+1}/{len(assets)}] {elapsed/60:.0f}min | Pro:{pro_vs_classic['pro_wins']} Classic:{pro_vs_classic['classic_wins']} Tie:{pro_vs_classic['tie']}")

    # Résumé
    results.sort(key=lambda x: x["improvement"], reverse=True)

    print(f"\n{'='*90}")
    print(f"  RÉSULTATS — Pro vs Classique")
    print(f"{'='*90}")
    print(f"  Pro gagne     : {pro_vs_classic['pro_wins']}")
    print(f"  Classique gagne: {pro_vs_classic['classic_wins']}")
    print(f"  Égalité       : {pro_vs_classic['tie']}")
    total = sum(pro_vs_classic.values())
    if total > 0:
        print(f"  Pro win rate  : {pro_vs_classic['pro_wins']/total*100:.0f}%")

    print(f"\n  TOP 15 améliorations (Pro meilleur que Classique) :")
    for r in results[:15]:
        if r["improvement"] > 0:
            print(f"    {r['symbol']:12} {r['best_pro']['strategy']:20} Sharpe={r['best_pro']['sharpe']:.3f}  vs Classic {r['best_classic']['strategy']:18} Sharpe={r['best_classic']['sharpe']:.3f}  Δ={r['improvement']:+.3f}")

    print(f"\n  TOP 15 régressions (Classique meilleur que Pro) :")
    for r in reversed(results[-15:]):
        if r["improvement"] < 0:
            print(f"    {r['symbol']:12} Classic {r['best_classic']['strategy']:18} Sharpe={r['best_classic']['sharpe']:.3f}  vs Pro {r['best_pro']['strategy']:20} Sharpe={r['best_pro']['sharpe']:.3f}  Δ={r['improvement']:+.3f}")

    # Meilleure stratégie globale
    strat_wins = {}
    for r in results:
        all_strats = r.get("strategies", {})
        best = max(all_strats.items(), key=lambda x: x[1].get("sharpe", -999) if "error" not in x[1] else -999, default=(None, None))
        if best[0]:
            strat_wins[best[0]] = strat_wins.get(best[0], 0) + 1

    print(f"\n  Stratégie gagnante par actif :")
    for strat, count in sorted(strat_wins.items(), key=lambda x: -x[1]):
        bar = "█" * count
        print(f"    {strat:20} {count:>3} actifs  {bar}")

    # Sauvegarder
    output = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M"),
        "duration_minutes": round((time.time() - start_time) / 60, 1),
        "num_assets": len(results),
        "pro_vs_classic": pro_vs_classic,
        "strategy_wins": strat_wins,
        "top_20_improvements": results[:20],
        "top_20_regressions": results[-20:],
    }

    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2, default=str)

    elapsed = time.time() - start_time
    print(f"\n{'='*90}")
    print(f"  Terminé en {elapsed/60:.1f} minutes")
    print(f"  Résultats dans {OUTPUT}")
    print(f"{'='*90}")


if __name__ == "__main__":
    main()
