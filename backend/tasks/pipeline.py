"""Pipeline Bilok-TradePilot — Chaîne des 6 modules automatisée via Celery

[ Scanner ] → [ Analyseur ] → [ Scoring ] → [ Exécution ] → [ Portefeuille ] → [ Rentabilité ]
     ↑_____________________________________________________________feedback loop____________________________|

Tâches planifiées :
- daily_pipeline : 22h UTC — scan complet + analyse + scoring + exécution
- daily_data_update : 21h30 UTC — mise à jour OHLCV du jour
- weekly_genome : dimanche 3h UTC — recalcul du génome des actifs
- nightly_monte_carlo : 2h UTC — simulation Monte Carlo
"""

import logging
from datetime import datetime

from celery import chain
from celery.schedules import crontab

from backend.tasks.celery_app import celery_app

logger = logging.getLogger("tradepilot.pipeline")


# ============================================================
# Tâches du pipeline
# ============================================================

@celery_app.task(name="pipeline.update_market_data", bind=True, max_retries=3)
def task_update_market_data(self):
    """Met à jour les données OHLCV daily pour tous les actifs."""
    logger.info("[PIPELINE] Mise à jour des données marché...")
    try:
        import yfinance as yf
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from backend.config.settings import settings
        from backend.database.models import Asset, OHLCVDaily

        engine = create_engine(settings.DATABASE_URL)
        with Session(engine) as db:
            assets = db.query(Asset).filter_by(is_active=True).all()
            updated = 0

            for asset in assets:
                try:
                    ticker = yf.Ticker(asset.symbol)
                    df = ticker.history(period="5d", interval="1d")

                    if df.empty:
                        continue

                    for idx, row in df.iterrows():
                        date = idx.date()
                        existing = (
                            db.query(OHLCVDaily)
                            .filter_by(asset_id=asset.id, date=date)
                            .first()
                        )
                        if not existing:
                            db.add(OHLCVDaily(
                                asset_id=asset.id,
                                date=date,
                                open=float(row["Open"]),
                                high=float(row["High"]),
                                low=float(row["Low"]),
                                close=float(row["Close"]),
                                volume=int(row["Volume"]),
                                source="yahoo",
                            ))
                            updated += 1

                    import time
                    time.sleep(0.3)
                except Exception as e:
                    logger.warning(f"[{asset.symbol}] Erreur: {e}")

            db.commit()
            logger.info(f"[PIPELINE] {updated} nouvelles barres OHLCV insérées")

            # Notification
            try:
                from backend.notifications import notify_data_update
                notify_data_update(updated, len(assets))
            except Exception:
                pass

            # Vérifier les positions (SL/TP) + remplacement auto
            try:
                from backend.modules.execution.position_manager_v2 import run_position_cycle
                cycle = run_position_cycle(db)
                if cycle["closed"]:
                    from backend.notifications import notify_position_closed
                    for c in cycle["closed"]:
                        notify_position_closed(c["symbol"], c["reason"], c["pnl"], c["direction"])
                if cycle["executed_from_queue"]:
                    from backend.notifications import notify_queue_execution
                    for e in cycle["executed_from_queue"]:
                        notify_queue_execution(e["symbol"], e["direction"], e["entry_price"])
            except Exception as e:
                logger.warning(f"[PIPELINE] Erreur cycle positions: {e}")

            return {"status": "ok", "updated": updated, "assets": len(assets)}

    except Exception as e:
        logger.error(f"[PIPELINE] Erreur mise à jour données: {e}")
        try:
            from backend.notifications import notify_pipeline_error
            notify_pipeline_error("update_market_data", str(e))
        except Exception:
            pass
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name="pipeline.update_intraday_data", bind=True, max_retries=3)
def task_update_intraday_data(self):
    """Met à jour les données intraday 1h."""
    logger.info("[PIPELINE] Mise à jour données intraday...")
    try:
        import yfinance as yf
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from backend.config.settings import settings
        from backend.database.models import Asset, OHLCV1H

        engine = create_engine(settings.DATABASE_URL)
        with Session(engine) as db:
            assets = db.query(Asset).filter_by(is_active=True).all()
            updated = 0

            for asset in assets:
                try:
                    ticker = yf.Ticker(asset.symbol)
                    df = ticker.history(period="5d", interval="1h")

                    if df.empty:
                        continue

                    for idx, row in df.iterrows():
                        dt = idx.to_pydatetime().replace(tzinfo=None)
                        existing = (
                            db.query(OHLCV1H)
                            .filter_by(asset_id=asset.id, datetime=dt)
                            .first()
                        )
                        if not existing:
                            db.add(OHLCV1H(
                                asset_id=asset.id,
                                datetime=dt,
                                open=float(row["Open"]),
                                high=float(row["High"]),
                                low=float(row["Low"]),
                                close=float(row["Close"]),
                                volume=int(row["Volume"]),
                                source="yahoo",
                            ))
                            updated += 1

                    import time
                    time.sleep(0.3)
                except Exception as e:
                    logger.warning(f"[{asset.symbol}] Erreur intraday: {e}")

            db.commit()
            logger.info(f"[PIPELINE] {updated} nouvelles barres 1H insérées")
            return {"status": "ok", "updated": updated}

    except Exception as e:
        logger.error(f"[PIPELINE] Erreur intraday: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name="pipeline.run_scanner")
def task_run_scanner():
    """Module 1 — Scan complet de tous les actifs."""
    logger.info("[PIPELINE] Lancement du scanner...")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from backend.config.settings import settings
    from backend.modules.scanner.service import ScannerService

    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as db:
        service = ScannerService(db)
        results = service.scan_all()
        logger.info(f"[PIPELINE] {len(results)} actifs scannés")

        # Signaux GO
        top_signals = [
            {"symbol": r["symbol"], "score": r["scores"]["final"], "direction": "LONG"}
            for r in results if r["scores"]["final"] >= 65
        ]

        # Notification
        try:
            from backend.notifications import notify_scan_complete
            notify_scan_complete(len(results), top_signals)
        except Exception:
            pass

        # Ajouter les signaux en file d'attente si max positions atteint
        try:
            from backend.modules.execution.position_manager_v2 import (
                can_open_position, add_to_queue, get_open_symbols,
            )
            open_symbols = get_open_symbols(db)
            for sig in top_signals:
                if sig["symbol"] not in open_symbols:
                    add_to_queue(sig)
        except Exception:
            pass

        return {
            "status": "ok",
            "scanned": len(results),
            "signals_go": len(top_signals),
            "top_5": [{"symbol": r["symbol"], "score": r["scores"]["final"]} for r in results[:5]],
        }


@celery_app.task(name="pipeline.run_analyser")
def task_run_analyser(scanner_results: dict = None):
    """Module 2 — Analyse de tous les actifs."""
    logger.info("[PIPELINE] Lancement de l'analyseur...")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from backend.config.settings import settings
    from backend.modules.analyser.service import AnalyserService

    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as db:
        service = AnalyserService(db)
        results = service.analyse_all()
        regime = service.get_regime_summary()
        logger.info(f"[PIPELINE] {len(results)} actifs analysés, régime: {regime['dominant_regime']}")
        return {
            "status": "ok",
            "analysed": len(results),
            "regime": regime["dominant_regime"],
        }


@celery_app.task(name="pipeline.run_scoring")
def task_run_scoring(analyser_results: dict = None):
    """Module 3 — Scoring de tous les actifs."""
    logger.info("[PIPELINE] Lancement du scoring...")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from backend.config.settings import settings
    from backend.modules.scoring.service import ScoringService

    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as db:
        service = ScoringService(db)
        signals = service.get_active_signals()
        logger.info(f"[PIPELINE] {len(signals)} signaux GO générés")
        return {
            "status": "ok",
            "signals": len(signals),
            "top_signals": [
                {"symbol": s["symbol"], "score": s["thesis_score"], "direction": s["direction"]}
                for s in signals[:5]
            ],
        }


@celery_app.task(name="pipeline.run_execution")
def task_run_execution(scoring_results: dict = None):
    """Module 4 — Exécution des signaux GO (paper trading)."""
    logger.info("[PIPELINE] Lancement de l'exécution...")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from backend.config.settings import settings
    from backend.modules.execution.service import ExecutionService

    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as db:
        service = ExecutionService(db)
        result = service.execute_all_signals()
        logger.info(f"[PIPELINE] {result['executed']} trades exécutés sur {result['total_signals']} signaux")
        return {
            "status": "ok",
            "executed": result["executed"],
            "skipped": result["skipped"],
            "capital_deployed": result["capital_deployed"],
        }


@celery_app.task(name="pipeline.run_portfolio")
def task_run_portfolio(execution_results: dict = None):
    """Module 5 — Gestion du portefeuille."""
    logger.info("[PIPELINE] Mise à jour portefeuille...")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from backend.config.settings import settings
    from backend.modules.portfolio.service import PortfolioService

    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as db:
        service = PortfolioService(db)
        summary = service.get_portfolio_summary()
        stress = service.run_stress_tests()
        logger.info(f"[PIPELINE] Portefeuille: {summary['num_positions']} positions, regime={summary['regime']['regime']}")
        return {
            "status": "ok",
            "positions": summary["num_positions"],
            "total_value": summary["total_value"],
            "regime": summary["regime"]["regime"],
        }


@celery_app.task(name="pipeline.run_performance")
def task_run_performance(portfolio_results: dict = None):
    """Module 6 — Suivi de rentabilité + feedback loop."""
    logger.info("[PIPELINE] Calcul performance + feedback...")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from backend.config.settings import settings
    from backend.modules.performance.service import PerformanceService

    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as db:
        service = PerformanceService(db)
        report = service.get_full_report()
        meta = report["meta_score"]
        feedback = report["feedback_loop"]
        logger.info(f"[PIPELINE] Meta-Score: {meta['meta_score']}, Engagement: {meta['engagement']}, Action: {feedback['action']}")

        # Notification Monte Carlo
        try:
            from backend.notifications import notify_monte_carlo
            notify_monte_carlo(0, 100_000, meta["meta_score"])
        except Exception:
            pass

        # Rapport hebdomadaire (si dimanche)
        from datetime import date
        if date.today().weekday() == 6:  # Dimanche
            try:
                from backend.modules.performance.weekly_report import generate_weekly_report
                weekly = generate_weekly_report(db)
                from backend.notifications import notify_weekly_report
                notify_weekly_report(weekly)
            except Exception:
                pass

        return {
            "status": "ok",
            "meta_score": meta["meta_score"],
            "engagement": meta["engagement"],
            "feedback_action": feedback["action"],
            "timestamp": datetime.utcnow().isoformat(),
        }


# ============================================================
# Chaînes de pipeline
# ============================================================

def run_full_pipeline():
    """Lance le pipeline complet en chaîne Celery."""
    pipeline = chain(
        task_update_market_data.si(),
        task_run_scanner.si(),
        task_run_analyser.s(),
        task_run_scoring.s(),
        task_run_execution.s(),
        task_run_portfolio.s(),
        task_run_performance.s(),
    )
    return pipeline.apply_async()


def run_data_update():
    """Lance uniquement la mise à jour des données."""
    pipeline = chain(
        task_update_market_data.si(),
        task_update_intraday_data.si(),
    )
    return pipeline.apply_async()


# ============================================================
# Beat schedule — tâches planifiées
# ============================================================

celery_app.conf.beat_schedule = {
    # MAJ données daily à 21h30 UTC (22h30 Paris)
    "daily-data-update": {
        "task": "pipeline.update_market_data",
        "schedule": crontab(hour=21, minute=30),
    },
    # MAJ intraday toutes les 4h (heures de marché)
    "intraday-update": {
        "task": "pipeline.update_intraday_data",
        "schedule": crontab(hour="10,14,18,22", minute=0),
    },
    # Pipeline complet à 22h UTC
    "daily-pipeline": {
        "task": "pipeline.run_scanner",
        "schedule": crontab(hour=22, minute=0),
    },
    # Monte Carlo nocturne à 2h UTC
    "nightly-monte-carlo": {
        "task": "pipeline.run_performance",
        "schedule": crontab(hour=2, minute=0),
    },
}
