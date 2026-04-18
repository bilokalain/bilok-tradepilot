"""Module 6 — Suivi de Rentabilité V2 : API endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.sync_session import get_sync_db
from backend.modules.performance.service import PerformanceService
from backend.modules.performance.performance_v2 import (
    compute_benchmarks, record_equity, get_equity_curve,
    compute_trading_stats, compute_performance_by_class,
    compute_live_ratios, generate_full_report,
)

router = APIRouter()


@router.get("/report")
def get_full_report(db: Session = Depends(get_sync_db)):
    """Rapport V1 (compatibilité)."""
    return PerformanceService(db).get_full_report()


@router.get("/report-v2")
def get_full_report_v2(db: Session = Depends(get_sync_db)):
    """Rapport V2 complet — benchmarks, stats, equity curve, ratios."""
    return generate_full_report(db)


@router.get("/meta-score")
def get_meta_score(db: Session = Depends(get_sync_db)):
    """Meta-Score santé du système."""
    return PerformanceService(db).get_meta_score()


@router.get("/ews")
def get_ews(db: Session = Depends(get_sync_db)):
    """Early Warning System."""
    return PerformanceService(db).get_ews()


@router.get("/feedback")
def get_feedback(db: Session = Depends(get_sync_db)):
    """Feedback loop vers le Module 1."""
    return PerformanceService(db).get_feedback()


@router.get("/attribution")
def get_attribution(db: Session = Depends(get_sync_db)):
    """Attribution causale P&L."""
    report = PerformanceService(db).get_full_report()
    return report["attribution"]


@router.get("/benchmarks")
def get_benchmarks(db: Session = Depends(get_sync_db)):
    """Performance vs benchmarks (SPY, 60/40)."""
    return compute_benchmarks(db)


@router.get("/equity-curve")
def get_equity():
    """Equity curve live avec comparaison SPY."""
    from backend.modules.performance.equity_tracker import record_daily_equity, get_equity_curve as get_new_equity_curve
    record_daily_equity()
    return get_new_equity_curve()


@router.get("/stats")
def get_trading_stats(db: Session = Depends(get_sync_db)):
    """Statistiques de trading détaillées."""
    return compute_trading_stats(db)


@router.get("/by-class")
def get_perf_by_class(db: Session = Depends(get_sync_db)):
    """Performance par classe d'actif."""
    return compute_performance_by_class(db)


@router.get("/ratios")
def get_live_ratios():
    """Sharpe, Sortino, Calmar live."""
    return compute_live_ratios()


@router.get("/weekly-report")
def get_weekly_report_endpoint(db: Session = Depends(get_sync_db)):
    """Génère le rapport hebdomadaire."""
    from backend.modules.performance.weekly_report import generate_weekly_report
    return generate_weekly_report(db)


@router.get("/weekly-reports")
def list_reports():
    """Liste les rapports hebdomadaires sauvegardés."""
    from backend.modules.performance.weekly_report import list_weekly_reports
    return list_weekly_reports()


@router.get("/weekly-reports/{filename}")
def get_saved_report(filename: str):
    """Récupère un rapport hebdomadaire spécifique."""
    from backend.modules.performance.weekly_report import get_weekly_report
    report = get_weekly_report(filename)
    if not report:
        return {"error": "Rapport non trouvé"}
    return report


@router.get("/learning")
def learning_status():
    """Statut du système d'apprentissage autonome."""
    from backend.modules.learning.adaptive_engine import get_learning_status
    return get_learning_status()


@router.get("/entry-quality")
def entry_quality():
    """Apprentissage qualité d'entrée — quels signaux de santé prédisent le succès."""
    from backend.modules.learning.entry_quality_tracker import get_entry_quality_status
    return get_entry_quality_status()


@router.get("/calibration")
def calibration_status():
    """Statut du calibrage automatique du scoring V2."""
    from backend.modules.learning.scoring_calibrator import get_calibration_status
    return get_calibration_status()


@router.get("/detection")
def detection_report(db: Session = Depends(get_sync_db)):
    """Rapport de détection du jour — compare les top movers vs signaux GO."""
    import json
    from pathlib import Path
    from backend.database.models import Asset, OHLCVDaily

    # Top movers — prix live Alpaca si disponible, sinon BDD
    assets = db.query(Asset).filter_by(is_active=True).all()

    live_prices = {}
    try:
        from backend.modules.execution.broker_alpaca import alpaca_broker
        if alpaca_broker.is_configured:
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockSnapshotRequest
            from backend.config.settings import settings
            data_client = StockHistoricalDataClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY)
            us_symbols = [a.symbol for a in assets if not any(a.symbol.endswith(s) for s in ['.PA', '.DE', '.SW', '.L', '.AS', '.MI', '=X', '=F', '-USD'])]
            for i in range(0, len(us_symbols), 50):
                batch = us_symbols[i:i+50]
                try:
                    snapshots = data_client.get_stock_snapshot(StockSnapshotRequest(symbol_or_symbols=batch))
                    for sym, snap in snapshots.items():
                        if snap.daily_bar and snap.previous_daily_bar:
                            live_prices[sym] = {
                                "current": float(snap.daily_bar.close),
                                "prev_close": float(snap.previous_daily_bar.close),
                            }
                except Exception:
                    pass
    except Exception:
        pass

    movers = []
    for asset in assets:
        sym = asset.symbol
        if sym in live_prices:
            curr = live_prices[sym]["current"]
            prev = live_prices[sym]["prev_close"]
        else:
            rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(2).all()
            if len(rows) < 2:
                continue
            prev = float(rows[1].close)
            curr = float(rows[0].close)
        if prev <= 0:
            continue
        change = (curr / prev - 1) * 100
        movers.append({"symbol": sym, "change_pct": round(change, 2), "close": round(curr, 2)})

    top_gainers = sorted([m for m in movers if m["change_pct"] > 3], key=lambda x: -x["change_pct"])[:20]

    # Signaux GO
    go_symbols = set()
    try:
        signals = json.loads(Path("data/signals_cache.json").read_text())
        go_symbols = {s["symbol"] for s in signals if s.get("action") == "GO"}
    except Exception:
        pass

    # Scanner scores
    scan_map = {}
    try:
        cache = json.loads(Path("data/scanner_cache.json").read_text())
        results = cache.get("results", cache) if isinstance(cache, dict) else cache
        for r in results:
            if isinstance(r, dict):
                scan_map[r.get("symbol", "")] = r.get("scores", {}).get("final", 0)
    except Exception:
        pass

    # Évaluer la détection
    report = []
    detected = 0
    for m in top_gainers:
        sym = m["symbol"]
        scanner_score = scan_map.get(sym, 0)
        is_go = sym in go_symbols
        is_detected = scanner_score >= 60 or is_go
        if is_detected:
            detected += 1
        report.append({
            "symbol": sym,
            "change_pct": m["change_pct"],
            "close": m["close"],
            "scanner_score": round(scanner_score, 1),
            "is_go": is_go,
            "detected": is_detected,
        })

    rate = round(detected / len(top_gainers) * 100, 1) if top_gainers else 0

    # Historique
    history = []
    try:
        calib = json.loads(Path("data/scoring_calibration.json").read_text())
        history = calib.get("daily_records", [])[-30:]
    except Exception:
        pass

    return {
        "date": str(__import__("datetime").date.today()),
        "total_movers": len(top_gainers),
        "detected": detected,
        "missed": len(top_gainers) - detected,
        "detection_rate": rate,
        "movers": report,
        "history": history,
    }


@router.post("/equity-record")
def record_equity_endpoint():
    """Enregistre l'equity du jour."""
    from backend.modules.performance.equity_tracker import record_daily_equity
    record_daily_equity()
    return {"status": "ok"}
