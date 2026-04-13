"""Pré-calcul complet de tous les modules — à lancer une fois puis via Celery Beat

Calcule et sauvegarde sur disque TOUS les résultats :
1. Scanner (218 actifs × 10 critères)
2. Analyseur (régime + stratégies pour chaque actif)
3. Scoring (signaux GO)
4. Performance (benchmarks, stats)
5. Portefeuille (VaR, exposure, beta)
6. Régime global

Après ce script, TOUS les modules affichent instantanément.
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, ".")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DB_URL = "postgresql://tradepilot:tradepilot_dev@localhost:5432/tradepilot"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def save_cache(name: str, data):
    filepath = DATA_DIR / f"{name}_cache.json"
    filepath.write_text(json.dumps(data, default=str, ensure_ascii=False, indent=1))
    print(f"  [{name}] Sauvegardé ({filepath.stat().st_size // 1024} KB)")


def main():
    start = time.time()
    engine = create_engine(DB_URL)

    print(f"\n{'='*60}")
    print(f"  BILOK-TRADEPILOT — Pré-calcul complet")
    print(f"{'='*60}\n")

    with Session(engine) as db:

        # === 1. SCANNER ===
        print("[1/6] Scanner (218 actifs × 10 critères)...")
        try:
            from backend.modules.scanner.service import ScannerService
            from backend.modules.scanner.cache import update_cache
            service = ScannerService(db)
            scan_results = service.scan_all()
            update_cache(scan_results)
            print(f"  {len(scan_results)} actifs scannés, #1: {scan_results[0]['symbol']} ({scan_results[0]['scores']['final']:.1f})")
        except Exception as e:
            print(f"  ERREUR Scanner: {e}")
            scan_results = []

        # === 2. ANALYSEUR ===
        print("[2/6] Analyseur (régime + stratégies)...")
        try:
            from backend.modules.analyser.service import AnalyserService
            analyser = AnalyserService(db)

            # Régime summary
            regime_summary = analyser.get_regime_summary()
            save_cache("regime", regime_summary)

            # Analyse par actif (top 50 seulement pour la vitesse)
            analyses = []
            from backend.database.models import Asset
            assets = db.query(Asset).filter_by(is_active=True).all()
            for i, asset in enumerate(assets[:50]):
                try:
                    result = analyser.analyse_asset(asset.symbol)
                    if "error" not in result:
                        analyses.append({
                            "symbol": result["symbol"],
                            "name": result.get("name", ""),
                            "regime": result["regime"]["regime"],
                            "confidence": result["regime"]["confidence"],
                            "best_strategy": result["best_strategy"]["name"],
                            "direction": result["best_strategy"]["direction"],
                            "conviction": result["best_strategy"]["conviction"],
                            "backtest_sharpe": result["best_strategy"].get("backtest_sharpe", 0),
                        })
                except Exception:
                    pass
                if (i + 1) % 10 == 0:
                    print(f"  [{i+1}/50] analysés...")

            analyses.sort(key=lambda x: x.get("backtest_sharpe", 0), reverse=True)
            save_cache("analyser", {"regime": regime_summary, "analyses": analyses})
            print(f"  {len(analyses)} actifs analysés")
        except Exception as e:
            print(f"  ERREUR Analyseur: {e}")

        # === 3. SCORING (signaux) ===
        print("[3/6] Scoring (signaux GO)...")
        try:
            from backend.modules.scoring.service import ScoringService
            scoring = ScoringService(db)
            signals = scoring.get_active_signals()
            save_cache("signals", signals)
            print(f"  {len(signals)} signaux GO")
        except Exception as e:
            print(f"  ERREUR Scoring: {e}")
            save_cache("signals", [])

        # === 4. PERFORMANCE ===
        print("[4/6] Performance (benchmarks + stats)...")
        try:
            from backend.modules.performance.performance_v2 import (
                compute_benchmarks, compute_trading_stats, compute_performance_by_class,
                compute_live_ratios, record_equity,
            )
            record_equity(db)
            perf_data = {
                "benchmarks": compute_benchmarks(db),
                "trading_stats": compute_trading_stats(db),
                "by_class": compute_performance_by_class(db),
                "ratios": compute_live_ratios(),
            }
            save_cache("performance", perf_data)
            print(f"  Benchmarks + stats calculés")
        except Exception as e:
            print(f"  ERREUR Performance: {e}")

        # === 5. PORTEFEUILLE ===
        print("[5/6] Portefeuille (VaR + exposure + beta)...")
        try:
            from backend.modules.portfolio.portfolio_v2 import (
                compute_var, compute_exposure, compute_portfolio_beta,
                check_drawdown_control, compute_risk_budget,
            )
            portfolio_data = {
                "var": compute_var(db),
                "exposure": compute_exposure(db),
                "beta": compute_portfolio_beta(db),
                "drawdown": check_drawdown_control(db),
                "risk_budget": compute_risk_budget(db),
            }
            save_cache("portfolio", portfolio_data)
            print(f"  VaR + exposure + beta calculés")
        except Exception as e:
            print(f"  ERREUR Portefeuille: {e}")

        # === 6. RÉGIME GLOBAL ===
        print("[6/6] Régime global multi-assets...")
        try:
            from backend.modules.analyser.regime_global import detect_global_regime
            global_regime = detect_global_regime(db)
            save_cache("global_regime", global_regime)
            print(f"  Régime: {global_regime['regime']} ({global_regime['confidence']:.0%})")
        except Exception as e:
            print(f"  ERREUR Régime: {e}")

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  TERMINÉ en {elapsed/60:.1f} minutes")
    print(f"  Fichiers cache dans data/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
