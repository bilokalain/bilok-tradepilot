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
from backend.database.sync_session import engine as _engine

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
        from sqlalchemy.orm import Session
        from backend.database.models import Asset, OHLCVDaily

        with Session(_engine) as db:
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
            except Exception as e:
                logger.warning(f"[PIPELINE] Erreur notification data update: {e}")

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
        except Exception as e2:
            logger.warning(f"[PIPELINE] Erreur notification pipeline error: {e2}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name="pipeline.update_intraday_data", bind=True, max_retries=3)
def task_update_intraday_data(self):
    """Met à jour les données intraday 1h."""
    logger.info("[PIPELINE] Mise à jour données intraday...")
    try:
        import yfinance as yf
        from sqlalchemy.orm import Session
        from backend.database.models import Asset, OHLCV1H

        with Session(_engine) as db:
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
    from sqlalchemy.orm import Session
    from backend.modules.scanner.service import ScannerService

    with Session(_engine) as db:
        service = ScannerService(db)
        results = service.scan_all()
        logger.info(f"[PIPELINE] {len(results)} actifs scannés")

        # Sauvegarder dans le cache disque
        try:
            from backend.modules.scanner.cache import update_cache
            update_cache(results)
            logger.info("[PIPELINE] Cache scanner sauvegardé sur disque")
        except Exception as e:
            logger.warning(f"[PIPELINE] Erreur sauvegarde cache scanner: {e}")

        # Signaux GO
        top_signals = [
            {"symbol": r["symbol"], "score": r["scores"]["final"], "direction": "LONG"}
            for r in results if r["scores"]["final"] >= 65
        ]

        # Notification
        try:
            from backend.notifications import notify_scan_complete
            notify_scan_complete(len(results), top_signals)
        except Exception as e:
            logger.warning(f"[PIPELINE] Erreur notification scan complete: {e}")

        # Ajouter les signaux en file d'attente si max positions atteint
        try:
            from backend.modules.execution.position_manager_v2 import (
                can_open_position, add_to_queue, get_open_symbols,
            )
            open_symbols = get_open_symbols(db)
            for sig in top_signals:
                if sig["symbol"] not in open_symbols:
                    add_to_queue(sig)
        except Exception as e:
            logger.warning(f"[PIPELINE] Erreur ajout signaux en file d'attente: {e}")

        return {
            "status": "ok",
            "scanned": len(results),
            "signals_go": len(top_signals),
            "top_5": [{"symbol": r["symbol"], "score": r["scores"]["final"]} for r in results[:5]],
        }


@celery_app.task(name="pipeline.build_correlation_cache")
def task_build_correlation_cache():
    """Pré-calcul de la matrice de corrélation — UNE SEULE FOIS pour tout le pipeline."""
    logger.info("[PIPELINE] Construction du cache de corrélation...")
    from sqlalchemy.orm import Session
    from backend.modules.scanner.correlation_cache import build_correlation_cache

    with Session(_engine) as db:
        result = build_correlation_cache(db)
        n = result.get("n_assets", 0)
        logger.info(f"[PIPELINE] Cache corrélation prêt — {n} actifs")
        return {"status": "ok", "n_assets": n}


@celery_app.task(name="pipeline.run_analyser")
def task_run_analyser(scanner_results: dict = None):
    """Module 2 — Analyse de tous les actifs."""
    logger.info("[PIPELINE] Lancement de l'analyseur...")
    from sqlalchemy.orm import Session
    from backend.modules.analyser.service import AnalyserService

    with Session(_engine) as db:
        service = AnalyserService(db)
        results = service.analyse_all()
        regime = service.get_regime_summary()
        logger.info(f"[PIPELINE] {len(results)} actifs analysés, régime: {regime['dominant_regime']}")

        # Sauvegarder les caches disque
        try:
            import json
            from pathlib import Path
            DATA_DIR = Path("data")
            DATA_DIR.mkdir(exist_ok=True)
            DATA_DIR.joinpath("regime_cache.json").write_text(json.dumps(regime, default=str))
            DATA_DIR.joinpath("analyser_cache.json").write_text(json.dumps({"regime": regime, "analyses": results[:50]}, default=str))
            # Régime global
            from backend.modules.analyser.regime_global import detect_global_regime
            global_regime = detect_global_regime(db)
            DATA_DIR.joinpath("global_regime_cache.json").write_text(json.dumps(global_regime, default=str))
            logger.info("[PIPELINE] Caches analyseur/régime sauvegardés")
        except Exception as e:
            logger.warning(f"[PIPELINE] Erreur sauvegarde cache analyseur: {e}")

        return {
            "status": "ok",
            "analysed": len(results),
            "regime": regime["dominant_regime"],
        }


@celery_app.task(name="pipeline.run_scoring")
def task_run_scoring(analyser_results: dict = None):
    """Module 3 — Scoring de tous les actifs."""
    logger.info("[PIPELINE] Lancement du scoring...")
    from sqlalchemy.orm import Session
    from backend.modules.scoring.service import ScoringService

    with Session(_engine) as db:
        service = ScoringService(db)
        signals = service.get_active_signals()
        logger.info(f"[PIPELINE] {len(signals)} signaux GO générés")

        # Sauvegarder les signaux dans le cache disque
        try:
            import json
            from pathlib import Path
            Path("data/signals_cache.json").write_text(json.dumps(signals, default=str))
            logger.info("[PIPELINE] Cache signaux sauvegardé")
        except Exception as e:
            logger.warning(f"[PIPELINE] Erreur sauvegarde cache signaux: {e}")

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
    """Module 4 — Exécution des signaux GO + vérification retournement."""
    logger.info("[PIPELINE] Lancement de l'exécution...")
    from sqlalchemy.orm import Session

    # Vérifier les signaux de retournement AVANT d'exécuter
    try:
        with Session(_engine) as db_check:
            from backend.modules.portfolio.reversal_guard import check_reversal_signals, auto_protect
            reversal = check_reversal_signals(db_check)
            logger.info(f"[PIPELINE] Reversal Guard: {reversal['level']} ({reversal['n_signals']} signaux)")
            if reversal["level"] in ("ROUGE", "ORANGE"):
                logger.warning(f"[PIPELINE] RETOURNEMENT DÉTECTÉ — {reversal['message']}")
                protection = auto_protect(db_check)
                logger.warning(f"[PIPELINE] Protection: {protection['message']}")
                if reversal["level"] == "ROUGE":
                    return {
                        "status": "paused",
                        "reason": reversal["message"],
                        "reversal": reversal,
                        "protection": protection,
                        "executed": 0, "skipped": 0, "capital_deployed": 0,
                    }
    except Exception as e:
        logger.warning(f"[PIPELINE] Erreur reversal check: {e}")
    from backend.modules.execution.service import ExecutionService

    with Session(_engine) as db:
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
    from sqlalchemy.orm import Session
    from backend.modules.portfolio.service import PortfolioService

    with Session(_engine) as db:
        service = PortfolioService(db)
        summary = service.get_portfolio_summary()
        stress = service.run_stress_tests()
        logger.info(f"[PIPELINE] Portefeuille: {summary['num_positions']} positions, regime={summary['regime']['regime']}")

        # Sauvegarder le cache disque
        try:
            import json
            from pathlib import Path
            Path("data/portfolio_cache.json").write_text(json.dumps({
                "summary": summary, "stress_tests": stress
            }, default=str))
            logger.info("[PIPELINE] Cache portefeuille sauvegardé")
        except Exception as e:
            logger.warning(f"[PIPELINE] Erreur sauvegarde cache portefeuille: {e}")

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
    from sqlalchemy.orm import Session
    from backend.modules.performance.service import PerformanceService

    with Session(_engine) as db:
        service = PerformanceService(db)
        report = service.get_full_report()
        meta = report["meta_score"]
        feedback = report["feedback_loop"]
        logger.info(f"[PIPELINE] Meta-Score: {meta['meta_score']}, Engagement: {meta['engagement']}, Action: {feedback['action']}")

        # Sauvegarder le cache disque
        try:
            import json
            from pathlib import Path
            Path("data/performance_cache.json").write_text(json.dumps(report, default=str))
            logger.info("[PIPELINE] Cache performance sauvegardé")
        except Exception as e:
            logger.warning(f"[PIPELINE] Erreur sauvegarde cache performance: {e}")

        # Notification Monte Carlo
        try:
            from backend.notifications import notify_monte_carlo
            notify_monte_carlo(0, 100_000, meta["meta_score"])
        except Exception as e:
            logger.warning(f"[PIPELINE] Erreur notification Monte Carlo: {e}")

        # Rapport hebdomadaire (si dimanche)
        from datetime import date
        if date.today().weekday() == 6:  # Dimanche
            try:
                from backend.modules.performance.weekly_report import generate_weekly_report
                weekly = generate_weekly_report(db)
                from backend.notifications import notify_weekly_report
                notify_weekly_report(weekly)
            except Exception as e:
                logger.warning(f"[PIPELINE] Erreur rapport hebdomadaire: {e}")

        # Enregistrer l'equity du jour
        try:
            from backend.modules.performance.equity_tracker import record_daily_equity
            record_daily_equity()
        except Exception as e:
            logger.warning(f"[PIPELINE] Erreur equity tracker: {e}")

        # Calibrage scoring — comparer avec les top movers du jour
        try:
            from backend.modules.learning.scoring_calibrator import record_daily_performance
            calib = record_daily_performance(db)
            logger.info(f"[PIPELINE] Calibrage: détection {calib.get('detection_rate', '?')}%")
        except Exception as e:
            logger.warning(f"[PIPELINE] Erreur calibrage: {e}")

        # Auto-apprentissage — ré-entraîner le ML si nécessaire
        try:
            from backend.modules.learning.adaptive_engine import should_retrain, auto_retrain_ml, compute_weight_adjustments
            # Recalculer les ajustements de poids
            adjustments = compute_weight_adjustments()
            if adjustments:
                logger.info(f"[PIPELINE] Poids adaptatifs recalculés: {adjustments}")
            # Ré-entraîner XGBoost si nécessaire
            if should_retrain():
                retrain_result = auto_retrain_ml(db)
                logger.info(f"[PIPELINE] Auto-retrain ML: {retrain_result}")
        except Exception as e:
            logger.warning(f"[PIPELINE] Erreur apprentissage: {e}")

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

@celery_app.task(name="pipeline.run_full_pipeline")
def task_run_full_pipeline():
    """Lance le pipeline complet en chaîne Celery : M1→M2→M3→M4→M5→M6.

    Lock Redis pour empêcher deux pipelines en parallèle.
    """
    import redis as redis_lib
    from backend.config.settings import settings

    lock_client = redis_lib.from_url(settings.REDIS_URL)
    lock = lock_client.lock("tradepilot:pipeline_lock", timeout=1800, blocking=False)

    if not lock.acquire(blocking=False):
        logger.warning("[PIPELINE] Pipeline skip — un pipeline est déjà en cours")
        return {"skipped": True, "reason": "pipeline already running"}

    # Le lock est libéré après 30 min max (timeout) — la chaîne Celery
    # s'exécute dans des tasks séparées, on ne peut pas release dans un finally
    logger.info("[PIPELINE] Lancement du pipeline complet...")
    pipeline = chain(
        task_run_scanner.si(),
        task_build_correlation_cache.si(),
        task_run_analyser.si(),
        task_run_scoring.si(),
        task_run_execution.si(),
        task_run_portfolio.si(),
        task_run_performance.si(),
    )
    return pipeline.apply_async()


def run_full_pipeline():
    """Raccourci pour lancer le pipeline complet."""
    return task_run_full_pipeline.delay()


def run_data_update():
    """Lance uniquement la mise à jour des données."""
    pipeline = chain(
        task_update_market_data.si(),
        task_update_intraday_data.si(),
    )
    return pipeline.apply_async()


@celery_app.task(name="pipeline.run_light_pipeline")
def task_run_light_pipeline():
    """Pipeline léger — saute le scanner, part du cache existant.

    Analyseur → Scoring → Exécution → Portefeuille → Performance
    ~5 min au lieu de 1h+ pour le pipeline complet.
    Utile pour recalculer les signaux GO sans rescanner les 500 actifs.
    """
    import redis as redis_lib
    from backend.config.settings import settings

    lock_client = redis_lib.from_url(settings.REDIS_URL)
    lock = lock_client.lock("tradepilot:pipeline_lock", timeout=600, blocking=False)

    if not lock.acquire(blocking=False):
        logger.warning("[PIPELINE] Light pipeline skip — un pipeline est déjà en cours")
        return {"skipped": True, "reason": "pipeline already running"}

    logger.info("[PIPELINE] Lancement du pipeline LÉGER (sans scanner)...")
    pipeline = chain(
        task_build_correlation_cache.si(),
        task_run_analyser.si(),
        task_run_scoring.si(),
        task_run_execution.si(),
        task_run_portfolio.si(),
        task_run_performance.si(),
    )
    return pipeline.apply_async()


def run_light_pipeline():
    """Raccourci pour lancer le pipeline léger."""
    return task_run_light_pipeline.delay()


@celery_app.task(name="pipeline.check_tp_sl", bind=True)
def task_check_tp_sl(self):
    """Vérifie et ferme les positions qui ont atteint leur TP ou SL.

    Utilise un lock Redis pour empêcher les exécutions parallèles :
    si un cycle précédent est encore en cours, on skip silencieusement.
    """
    import redis as redis_lib
    from backend.config.settings import settings

    lock_client = redis_lib.from_url(settings.REDIS_URL)
    lock = lock_client.lock("tradepilot:tp_sl_lock", timeout=270, blocking=False)

    if not lock.acquire(blocking=False):
        logger.warning("[PIPELINE] TP/SL skip — cycle précédent encore en cours")
        return {"skipped": True, "reason": "lock held by previous cycle"}

    try:
        logger.info("[PIPELINE] Vérification TP/SL...")
        from sqlalchemy.orm import Session
        from backend.modules.execution.tp_sl_monitor import check_and_close_positions

        with Session(_engine) as db:
            result = check_and_close_positions(db)
            if result["closed"]:
                logger.info(f"[PIPELINE] TP/SL: {len(result['closed'])} positions fermées")
            return result
    finally:
        try:
            lock.release()
        except Exception:
            pass  # Lock expiré naturellement


@celery_app.task(name="pipeline.intraday_scan")
def task_intraday_scan():
    """Scan intraday rapide — détecte les breakouts en cours de séance.

    Lancé 15 min après l'ouverture US (15h45 Paris = 13h45 UTC)
    et au milieu de séance (18h Paris = 16h UTC).

    Plus léger que le pipeline complet :
    1. MAJ prix intraday (Yahoo Finance 1h)
    2. Scan rapide des 335 actifs
    3. Scoring V2 des meilleurs
    4. Alerte si nouveau signal GO (pas en position et pas déjà dans le scan du soir)
    """
    import redis as redis_lib
    from backend.config.settings import settings

    lock_client = redis_lib.from_url(settings.REDIS_URL)
    lock = lock_client.lock("tradepilot:intraday_lock", timeout=600, blocking=False)

    if not lock.acquire(blocking=False):
        logger.warning("[PIPELINE] Intraday scan skip — déjà en cours")
        return {"skipped": True}

    try:
        logger.info("[PIPELINE] Scan intraday — détection breakouts...")
        from sqlalchemy.orm import Session
        from backend.modules.scanner.service import ScannerService
        from backend.modules.execution.exhaustion_checker import check_position_health
        import json
        from pathlib import Path

        # 1. Scanner rapide
        with Session(_engine) as db:
            service = ScannerService(db)
            results = service.scan_all()
            logger.info(f"[PIPELINE] Intraday: {len(results)} actifs scannés")

            # 2. Filtrer les GO avec santé > 60 (pas épuisés)
            fresh_signals = []
            for r in results:
                score = r["scores"]["final"]
                if score < 63:
                    continue

                sym = r["symbol"]
                health = check_position_health(db, sym, "LONG", 0.01)
                rsi_sig = next((s for s in health["signals"] if s["name"] == "RSI"), None)
                rsi_status = rsi_sig["status"] if rsi_sig else "?"

                if health["score"] >= 60 and rsi_status != "FAIBLE":
                    fresh_signals.append({
                        "symbol": sym,
                        "scanner_score": score,
                        "health_score": health["score"],
                        "direction": "LONG",
                        "timing": "EARLY" if health["score"] >= 70 else "OK",
                    })

            fresh_signals.sort(key=lambda x: x["scanner_score"], reverse=True)

            # 3. Comparer avec le dernier scan nocturne pour trouver les NOUVEAUX
            old_go = set()
            try:
                signals_cache = json.loads(Path("data/signals_cache.json").read_text())
                old_go = {s["symbol"] for s in signals_cache}
            except Exception:
                pass

            new_signals = [s for s in fresh_signals if s["symbol"] not in old_go]

            # 4. Sauvegarder les résultats intraday
            intraday_report = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_scanned": len(results),
                "fresh_signals": len(fresh_signals),
                "new_vs_night": len(new_signals),
                "signals": fresh_signals[:20],
                "new_signals": new_signals[:10],
            }
            Path("data/intraday_scan.json").write_text(json.dumps(intraday_report, default=str, indent=1))

            # 5. Mettre à jour le cache scanner avec les données fraîches
            try:
                from backend.modules.scanner.cache import update_cache
                update_cache(results)
            except Exception as e:
                logger.warning(f"[PIPELINE] Erreur MAJ cache intraday: {e}")

            # 6. Ajouter les nouveaux signaux à la queue
            if new_signals:
                try:
                    from backend.modules.execution.position_manager_v2 import add_to_queue, get_open_symbols
                    open_symbols = get_open_symbols(db)
                    added = 0
                    for sig in new_signals:
                        if sig["symbol"] not in open_symbols:
                            add_to_queue({"symbol": sig["symbol"], "score": sig["scanner_score"], "direction": "LONG"})
                            added += 1
                    logger.info(f"[PIPELINE] Intraday: {added} nouveaux signaux ajoutés à la queue")
                except Exception as e:
                    logger.warning(f"[PIPELINE] Erreur ajout queue intraday: {e}")

            logger.info(f"[PIPELINE] Intraday terminé: {len(fresh_signals)} signaux frais, {len(new_signals)} nouveaux")

            return {
                "status": "ok",
                "scanned": len(results),
                "fresh_signals": len(fresh_signals),
                "new_signals": len(new_signals),
                "top_new": [s["symbol"] for s in new_signals[:5]],
            }
    finally:
        try:
            lock.release()
        except Exception:
            pass


# ============================================================
# Beat schedule — tâches planifiées
# ============================================================

celery_app.conf.beat_schedule = {
    # ─── PIPELINE NOCTURNE (22h UTC = 00h Paris) ───
    # MAJ données daily → Scanner 500 actifs → Corrélation → Analyseur →
    # Scoring → Exécution → Portefeuille → Performance → Monte Carlo
    "daily-data-update": {
        "task": "pipeline.update_market_data",
        "schedule": crontab(hour=21, minute=30),
    },
    "daily-pipeline": {
        "task": "pipeline.run_full_pipeline",
        "schedule": crontab(hour=22, minute=0),
    },

    # ─── SCAN INTRADAY (13h45 UTC = 15h45 Paris) ───
    # 15 min après ouverture US — détecte les breakouts de la séance
    "intraday-scan": {
        "task": "pipeline.intraday_scan",
        "schedule": crontab(hour=13, minute=45),
    },

    # ─── TP/SL MONITOR (toutes les 5 min, 24/7) ───
    # Protection permanente : trailing stop, SL, TP, essoufflement,
    # signal inverse, file d'attente
    "tp-sl-monitor": {
        "task": "pipeline.check_tp_sl",
        "schedule": crontab(minute="*/5"),
    },
}
