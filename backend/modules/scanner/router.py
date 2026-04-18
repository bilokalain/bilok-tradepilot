"""Module 1 — Scanner de Marché : API endpoints"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

logger = logging.getLogger("tradepilot.scanner.router")

from backend.database.sync_session import get_sync_db
from backend.database.models import Asset, OHLCVDaily
from backend.modules.scanner.service import ScannerService
from backend.modules.scanner.sentiment import fetch_reddit_mentions, compute_sentiment_score
from backend.modules.scanner.multi_timeframe import compute_mta_score
from backend.modules.scanner.cache import (
    get_cached_results, is_cache_fresh, is_updating,
    update_cache, set_updating,
)
from backend.database.models import OHLCV1H

import threading

router = APIRouter()


def _run_scan_background(db_url: str):
    """Exécute le scan en arrière-plan et met à jour le cache."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SyncSession
    try:
        engine = create_engine(db_url)
        with SyncSession(engine) as db:
            service = ScannerService(db)
            results = service.scan_all()
            update_cache(results)
    except Exception as e:
        from backend.modules.scanner.cache import _cache
        _cache["updating"] = False
        print(f"[SCANNER] Erreur scan background: {e}")


@router.get("/pipeline-status")
def pipeline_status():
    """Statut du pipeline en cours."""
    from backend.modules.scanner.cache import is_updating, is_cache_fresh, _cache
    import time

    # Vérifier si un worker traite un task pipeline
    running = is_updating()

    # Vérifier via Celery si des tasks pipeline sont actives
    active_tasks = []
    try:
        from backend.tasks.celery_app import celery_app
        inspect = celery_app.control.inspect(timeout=2)
        active = inspect.active() or {}
        for worker, tasks in active.items():
            for t in tasks:
                name = t.get("name", "")
                if "pipeline" in name and "check_tp_sl" not in name:
                    active_tasks.append({
                        "task": name.replace("pipeline.", ""),
                        "started": t.get("time_start"),
                    })
    except Exception as e:
        logger.warning(f"[SCANNER] Celery inspect failed: {e}")

    # Dernier update du cache
    last_updated = _cache.get("last_updated", 0)
    age_minutes = round((time.time() - last_updated) / 60) if last_updated else None

    return {
        "running": running or len(active_tasks) > 0,
        "active_tasks": active_tasks,
        "current_step": active_tasks[0]["task"] if active_tasks else None,
        "cache_age_minutes": age_minutes,
        "cache_fresh": is_cache_fresh(),
    }


@router.get("/intraday")
def intraday_scan_results():
    """Résultats du dernier scan intraday — breakouts détectés en cours de séance."""
    import json
    from pathlib import Path

    intraday_file = Path("data/intraday_scan.json")
    if not intraday_file.exists():
        return {"status": "no_data", "message": "Aucun scan intraday disponible. Prochains scans à 15h45 et 18h Paris."}

    try:
        data = json.loads(intraday_file.read_text())
        return {"status": "ok", **data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/top-movers")
def top_movers(db: Session = Depends(get_sync_db)):
    """Top movers du jour — les actifs qui bougent le plus (hausse et baisse)."""
    from backend.database.models import Asset, OHLCVDaily
    from backend.modules.execution.broker_alpaca import alpaca_broker

    assets = db.query(Asset).filter_by(is_active=True).all()

    # Positions actuelles (rapide)
    my_symbols = set()
    try:
        if alpaca_broker.is_configured:
            for p in alpaca_broker.get_positions():
                my_symbols.add(p["symbol"])
    except Exception as e:
        logger.warning(f"[SCANNER] Alpaca positions fetch failed: {e}")

    # Prix live Alpaca pour les movers du jour (pas d'hier)
    live_prices = {}
    try:
        if alpaca_broker.is_configured:
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockSnapshotRequest
            from backend.config.settings import settings
            data_client = StockHistoricalDataClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY)
            # Fetch en batch de 50 symboles
            all_symbols = [a.symbol for a in assets if not any(a.symbol.endswith(s) for s in ['.PA', '.DE', '.SW', '.L', '.AS', '.MI', '=X', '=F', '-USD'])]
            for i in range(0, len(all_symbols), 50):
                batch = all_symbols[i:i+50]
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
    except Exception as e:
        logger.warning(f"[SCANNER] Alpaca snapshots failed: {e}")

    movers = []
    for asset in assets:
        sym = asset.symbol

        # Priorité : prix live Alpaca (jour en cours)
        if sym in live_prices:
            current = live_prices[sym]["current"]
            prev_close = live_prices[sym]["prev_close"]
        else:
            # Fallback : BDD (J-1 vs J-2)
            rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(2).all()
            if len(rows) < 2:
                continue
            prev_close = float(rows[1].close)
            current = float(rows[0].close)

        change_pct = (current / prev_close - 1) * 100 if prev_close > 0 else 0

        movers.append({
            "symbol": sym,
            "name": asset.name,
            "asset_class": asset.asset_class.value,
            "price": round(current, 2),
            "prev_close": round(prev_close, 2),
            "change_pct": round(change_pct, 2),
            "in_position": sym in my_symbols,
            "source": "live" if sym in live_prices else "daily",
        })

    gainers = sorted([m for m in movers if m["change_pct"] > 0], key=lambda x: -x["change_pct"])[:15]
    losers = sorted([m for m in movers if m["change_pct"] < 0], key=lambda x: x["change_pct"])[:15]

    # Comparer avec le marché global (top movers via Alpaca)
    market_top = []
    detected = 0
    missed = []
    our_symbols = {m["symbol"] for m in movers}
    try:
        if alpaca_broker.is_configured:
            from alpaca.trading.client import TradingClient
            from backend.config.settings import settings
            data_client = None
            try:
                from alpaca.data.historical import StockHistoricalDataClient
                from alpaca.data.requests import StockSnapshotRequest, MostActivesRequest
                data_client = StockHistoricalDataClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY)
                # Top movers via screener
                from alpaca.data.requests import ScreenerRequest
                screener = data_client.get_stock_most_actives(MostActivesRequest(top=50))
                for s in screener.most_actives:
                    sym = s.symbol
                    chg = float(s.trade_count) if hasattr(s, 'trade_count') else 0
                    in_ours = sym in our_symbols
                    if in_ours:
                        detected += 1
                    else:
                        missed.append({"symbol": sym, "in_scanner": False})
                    market_top.append({"symbol": sym, "in_scanner": in_ours})
            except Exception as e:
                logger.warning(f"[SCANNER] Alpaca screener/most-actives failed: {e}")
    except Exception as e:
        logger.warning(f"[SCANNER] Market top movers comparison failed: {e}")

    # Taux de détection
    detection_rate = round(detected / len(market_top) * 100, 1) if market_top else None

    return {
        "gainers": gainers,
        "losers": losers,
        "total_assets": len(movers),
        "in_position": len(my_symbols),
        "market_comparison": {
            "market_top_count": len(market_top),
            "detected": detected,
            "detection_rate": detection_rate,
            "missed": missed[:10],
        } if market_top else None,
    }


@router.post("/launch-pipeline")
def launch_pipeline():
    """Lance le pipeline complet en arrière-plan (Scanner → Analyseur → Scoring → Exécution → Portefeuille → Performance)."""
    try:
        from backend.tasks.pipeline import task_run_full_pipeline
        result = task_run_full_pipeline.delay()
        return {
            "status": "launched",
            "task_id": str(result.id),
            "message": "Pipeline complet lancé en arrière-plan (~35 min). Les données se mettront à jour automatiquement.",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/scan")
def scan_market(db: Session = Depends(get_sync_db)):
    """Retourne les résultats du scanner (cache disque persistant)."""
    # Toujours retourner le cache s'il existe (mémoire ou disque)
    cached = get_cached_results()
    if cached:
        return cached

    # Premier scan — retourner les actifs sans score en attendant
    assets = db.query(Asset).filter_by(is_active=True).all()
    quick_results = []
    for asset in assets:
        last = (
            db.query(OHLCVDaily)
            .filter_by(asset_id=asset.id)
            .order_by(OHLCVDaily.date.desc())
            .first()
        )
        quick_results.append({
            "symbol": asset.symbol,
            "name": asset.name,
            "asset_class": asset.asset_class.value,
            "scores": {
                "correlation": 50, "sentiment": 50, "technical": 50,
                "genome": 50, "ipi": 50, "ivf": 50,
                "mts": 50, "sgi": 50, "sus": 50, "final": 50,
            },
            "weights": {},
            "vetoed": False,
            "veto_reasons": [],
            "last_close": float(last.close) if last else 0,
            "data_points": 0,
            "details": {},
            "_loading": True,
        })
    return quick_results


@router.get("/search")
def search_assets(q: str = "", db: Session = Depends(get_sync_db)):
    """Recherche d'actifs par nom ou symbole — autocomplete.

    Cherche dans : BDD assets, SYMBOL_ALIASES, puis Yahoo Finance.
    Retourne max 8 suggestions triées par pertinence.
    """
    from backend.modules.scanner.quick_analyse import SYMBOL_ALIASES

    if not q or len(q.strip()) < 1:
        return []

    query = q.strip().upper()
    results = []
    seen = set()

    # 1. Recherche dans les actifs en BDD (symbol + name)
    db_assets = db.query(Asset).filter_by(is_active=True).all()
    for a in db_assets:
        sym_up = a.symbol.upper()
        name_up = a.name.upper()
        if query in sym_up or query in name_up:
            score = 0
            if sym_up == query:
                score = 100
            elif sym_up.startswith(query):
                score = 90
            elif query in sym_up:
                score = 70
            elif name_up.startswith(query):
                score = 60
            else:
                score = 40
            results.append({
                "symbol": a.symbol,
                "name": a.name,
                "asset_class": a.asset_class.value,
                "source": "database",
                "relevance": score,
            })
            seen.add(a.symbol)

    # 2. Recherche dans SYMBOL_ALIASES (noms courants → symboles Yahoo)
    for alias, symbol in SYMBOL_ALIASES.items():
        alias_up = alias.upper()
        if query in alias_up or query in symbol.upper():
            if symbol not in seen:
                score = 85 if alias_up == query else (75 if alias_up.startswith(query) else 50)
                results.append({
                    "symbol": symbol,
                    "name": alias.title(),
                    "asset_class": _guess_class(symbol),
                    "source": "alias",
                    "relevance": score,
                })
                seen.add(symbol)

    # 3. Si peu de résultats, chercher via TradingView (instantané, mondial)
    if len(results) < 5 and len(query) >= 2:
        try:
            import re
            import requests as _requests
            resp = _requests.get(
                "https://symbol-search.tradingview.com/symbol_search/",
                params={"text": q.strip(), "hl": "0", "exchange": "", "lang": "fr", "type": "", "domain": "production"},
                headers={"User-Agent": "Mozilla/5.0", "Origin": "https://www.tradingview.com", "Referer": "https://www.tradingview.com/"},
                timeout=3,
            )
            tv_data = resp.json()

            # Mapping exchange TradingView → suffixe Yahoo Finance
            TV_EXCHANGE_MAP = {
                # Europe
                "EURONEXT": ".PA", "EURONEXT_PAR": ".PA", "EPA": ".PA",
                "EURONEXT_AMS": ".AS", "EURONEXT_BRU": ".BR", "EURONEXT_LIS": ".LS",
                "XETR": ".DE", "FWB": ".DE", "GETTEX": ".DE", "TRADEGATE": ".DE", "DUS": ".DE",
                "LSE": ".L", "LSIN": ".L",
                "AMS": ".AS", "SIX": ".SW", "MIL": ".MI", "BIT": ".MI",
                "CSE": ".CO", "BME": ".MC", "WBAG": ".VI",
                # US
                "NASDAQ": "", "NYSE": "", "AMEX": "", "ARCA": "", "BATS": "",
                # Asie / Pacifique
                "TSX": ".TO", "ASX": ".AX", "HKEX": ".HK", "TSE": ".T",
                "KRX": ".KS", "TWSE": ".TW", "SGX": ".SI",
                # Crypto
                "BINANCE": "", "COINBASE": "", "KRAKEN": "", "BITSTAMP": "",
                # Noms avec espaces (TradingView)
                "Euronext Paris": ".PA", "Euronext Amsterdam": ".AS",
                "Euronext Brussels": ".BR", "Euronext Lisbon": ".LS",
                "London Stock Exchange": ".L",
                # Autres
                "EUROTLX": ".MI", "AQUISUK": ".L", "AQUISEU": ".DE",
                "LSX": ".DE", "LS": ".DE",
            }
            TV_TYPE_MAP = {
                "stock": "ACTION_US", "fund": "ETF", "futures": "COMMODITY",
                "forex": "FOREX", "crypto": "CRYPTO", "index": "INDEX",
                "dr": "ACTION_US", "bond": "BOND",
            }

            # Trier TV : prioriser exchanges principaux (Euronext, NYSE, NASDAQ)
            PRIORITY_EXCHANGES = {"EURONEXT", "EPA", "NASDAQ", "NYSE", "AMEX", "XETR", "LSE", "SIX", "MIL", "BINANCE", "COINBASE"}
            tv_sorted = sorted(tv_data, key=lambda x: (
                0 if x.get("exchange", "") in PRIORITY_EXCHANGES else 1,
                0 if x.get("type") == "stock" else (1 if x.get("type") in ("crypto", "index", "fund") else 2),
            ))

            for item in tv_sorted[:8]:
                tv_sym = item.get("symbol", "")
                tv_desc = item.get("description", "")
                tv_exchange = item.get("exchange", "")
                tv_type = item.get("type", "stock")

                # Ignorer bonds et types peu utiles
                if tv_type in ("bond", "economic"):
                    continue

                # Construire le symbole Yahoo Finance
                suffix = TV_EXCHANGE_MAP.get(tv_exchange, "")
                if tv_type == "crypto":
                    # Crypto : BTCUSD → BTC-USD
                    yahoo_sym = tv_sym.replace("USD", "-USD") if "USD" in tv_sym and "-" not in tv_sym else tv_sym
                elif tv_type == "futures":
                    yahoo_sym = tv_sym + "=F" if "=F" not in tv_sym else tv_sym
                elif tv_type == "forex":
                    yahoo_sym = tv_sym + "=X" if "=X" not in tv_sym else tv_sym
                else:
                    yahoo_sym = tv_sym + suffix

                if yahoo_sym in seen:
                    continue

                # Classe d'actif
                asset_class = TV_TYPE_MAP.get(tv_type, "ACTION_US")
                if suffix in [".PA", ".DE", ".AS", ".SW", ".MI", ".CO", ".L"]:
                    asset_class = "ACTION_EU"

                # Nettoyer les balises HTML éventuelles
                clean_desc = re.sub(r"<[^>]+>", "", tv_desc)

                results.append({
                    "symbol": yahoo_sym,
                    "name": clean_desc or tv_sym,
                    "asset_class": asset_class,
                    "source": "tradingview",
                    "relevance": 62 if tv_sym.upper().startswith(query) else 55,
                })
                seen.add(yahoo_sym)
        except Exception as e:
            logger.warning(f"[SCANNER] TradingView search failed for '{q}': {e}")

    # Trier par pertinence et limiter à 8
    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results[:8]


def _guess_class(symbol: str) -> str:
    if "-USD" in symbol:
        return "CRYPTO"
    if "=X" in symbol:
        return "FOREX"
    if "=F" in symbol:
        return "COMMODITY"
    if any(s in symbol for s in [".PA", ".DE", ".AS", ".SW", ".MI", ".CO", ".L"]):
        return "ACTION_EU"
    if symbol.startswith("^"):
        return "INDEX"
    return "ACTION_US"


@router.get("/analyse")
def analyse_any_asset(q: str):
    """Analyse complète d'un actif quelconque (pas besoin d'être en BDD).

    Exemples : ?q=PLTR, ?q=S&P 500, ?q=COIN, ?q=AMC, ?q=CAC 40
    """
    from backend.modules.scanner.quick_analyse import quick_analyse
    return quick_analyse(q)


@router.get("/correlation-map")
def get_correlation_map(q: str = "", lookback: int = 120, db: Session = Depends(get_sync_db)):
    """Carte de corrélation — accepte noms en français.

    Exemples : ?q=petrole, ?q=or, ?q=bitcoin, ?q=CL=F, ?q=NVDA
    """
    from backend.modules.scanner.correlation_map import compute_correlation_map
    from backend.modules.scanner.quick_analyse import resolve_symbol
    resolved = resolve_symbol(q)
    return compute_correlation_map(db, resolved, lookback)


@router.get("/impact-simulation")
def simulate_impact_endpoint(q: str = "", move_pct: float = 10, lookback: int = 120, db: Session = Depends(get_sync_db)):
    """Simule l'impact d'un mouvement sur les actifs corrélés.

    Exemple : ?q=petrole&move_pct=20
    """
    from backend.modules.scanner.correlation_map import simulate_impact
    from backend.modules.scanner.quick_analyse import resolve_symbol
    resolved = resolve_symbol(q)
    return simulate_impact(db, resolved, move_pct, lookback)


@router.get("/correlation-backtest")
def backtest_correlation(a: str = "", b: str = "", db: Session = Depends(get_sync_db)):
    """Backtest complet de la corrélation entre deux actifs.

    Exemple : ?a=petrole&b=XOM
    """
    from backend.modules.scanner.correlation_backtest import full_correlation_backtest
    from backend.modules.scanner.quick_analyse import resolve_symbol
    resolved_a = resolve_symbol(a)
    resolved_b = resolve_symbol(b)
    return full_correlation_backtest(db, resolved_a, resolved_b)


@router.get("/correlation-rolling")
def rolling_corr(a: str = "", b: str = "", window: int = 60, db: Session = Depends(get_sync_db)):
    """Corrélation glissante entre deux actifs.

    Exemple : ?a=CL=F&b=XOM&window=60
    """
    from backend.modules.scanner.correlation_backtest import rolling_correlation
    from backend.modules.scanner.quick_analyse import resolve_symbol
    return rolling_correlation(db, resolve_symbol(a), resolve_symbol(b), window)


@router.get("/fundamental/{symbol}")
def get_fundamentals(symbol: str):
    """Analyse fondamentale complète d'un actif."""
    from backend.modules.scanner.fundamental import compute_fundamental_score
    return compute_fundamental_score(symbol)


@router.get("/technical-breakdown/{symbol}")
def technical_breakdown(symbol: str, db: Session = Depends(get_sync_db)):
    """Détail complet de l'analyse technique — 7 familles, 20 indicateurs."""
    from backend.modules.scanner.indicators import compute_technical_breakdown
    import pandas as pd

    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return {"error": f"Actif {symbol} non trouvé"}

    rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(250).all()
    if len(rows) < 50:
        return {"error": "Pas assez de données"}

    close = pd.Series([float(r.close) for r in reversed(rows)])
    high = pd.Series([float(r.high) for r in reversed(rows)])
    low = pd.Series([float(r.low) for r in reversed(rows)])
    volume = pd.Series([float(r.volume) for r in reversed(rows)])

    result = compute_technical_breakdown(close, high, low, volume)
    result["symbol"] = symbol
    result["price"] = round(float(close.iloc[-1]), 2)
    return result


CRITERION_NAMES = {
    "correlation": "Corrélation",
    "sentiment": "Sentiment",
    "genome": "Génome Explosif",
    "ipi": "Capital Institutionnel (IPI)",
    "ivf": "Vélocité Fondamentale (IVF)",
    "mts": "Macro Tailwind (MTS)",
    "sgi": "Topologie Sociale (SGI)",
    "sus": "Unicité du Signal (SUS)",
    "narrative": "Narrative Momentum",
}

VALID_CRITERIA = set(CRITERION_NAMES.keys())


def _safe_round(v, decimals=2):
    """Arrondit une valeur numérique, retourne None si NaN."""
    import math
    if v is None:
        return None
    try:
        if math.isnan(v) or math.isinf(v):
            return None
    except (TypeError, ValueError):
        return v
    return round(v, decimals)


@router.get("/criterion-breakdown/{symbol}/{criterion}")
def criterion_breakdown(symbol: str, criterion: str, db: Session = Depends(get_sync_db)):
    """Détail complet d'un critère du scanner — familles, indicateurs, scores.

    Critères disponibles : correlation, sentiment, genome, ipi, ivf, mts, sgi, sus, narrative.
    """
    import pandas as pd

    if criterion not in VALID_CRITERIA:
        return {"error": f"Critère inconnu: {criterion}. Valeurs possibles: {', '.join(sorted(VALID_CRITERIA))}"}

    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return {"error": f"Actif {symbol} non trouvé"}

    asset_class = asset.asset_class.value

    # Charger les données OHLCV
    rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.asc()).all()
    if len(rows) < 50:
        return {"error": "Pas assez de données"}

    close = pd.Series([float(r.close) for r in rows])
    high = pd.Series([float(r.high) for r in rows])
    low = pd.Series([float(r.low) for r in rows])
    volume = pd.Series([float(r.volume) for r in rows])

    families = []

    # ---- CORRELATION ----
    if criterion == "correlation":
        from backend.modules.scanner.correlation import (
            compute_correlation_score, detect_correlation_break,
        )
        # Charger tous les closes pour la corrélation
        all_assets = db.query(Asset).filter_by(is_active=True).all()
        closes_dict = {}
        for a in all_assets:
            a_rows = db.query(OHLCVDaily).filter_by(asset_id=a.id).order_by(OHLCVDaily.date.asc()).all()
            if len(a_rows) >= 50:
                closes_dict[a.symbol] = pd.Series([float(r.close) for r in a_rows])

        score = compute_correlation_score(closes_dict, symbol)
        breaks = detect_correlation_break(closes_dict, symbol)

        families.append({
            "name": "Score global", "score": _safe_round(score), "weight": 100,
            "signal": f"{len(breaks.get('breaks', []))} rupture(s) détectée(s)",
            "indicators": [],
        })
        for b in breaks.get("breaks", [])[:10]:
            families.append({
                "name": f"Rupture vs {b['symbol']}", "score": _safe_round(b['delta'] * 100),
                "weight": 0, "signal": f"Court: {b['corr_short']}, Long: {b['corr_long']}",
                "indicators": [
                    {"name": "Corrélation court terme (21j)", "value": b["corr_short"]},
                    {"name": "Corrélation long terme (252j)", "value": b["corr_long"]},
                    {"name": "Delta", "value": b["delta"], "signal": "Rupture significative" if b["delta"] > 0.5 else "Rupture modérée"},
                ],
            })

    # ---- SENTIMENT ----
    elif criterion == "sentiment":
        from backend.modules.scanner.sentiment import compute_sentiment_score, _simulate_mentions
        mentions = _simulate_mentions(symbol)
        result = compute_sentiment_score(mentions)
        score = result["score"]

        bd = result.get("sentiment_breakdown", {})
        families = [
            {
                "name": "Volume de mentions", "score": _safe_round(result.get("volume_score", 50)),
                "weight": 40, "signal": f"{result.get('num_mentions', 0)} mentions",
                "indicators": [
                    {"name": "Nombre de mentions", "value": result.get("num_mentions", 0)},
                    {"name": "Positives", "value": bd.get("positive", 0)},
                    {"name": "Négatives", "value": bd.get("negative", 0)},
                    {"name": "Neutres", "value": bd.get("neutral", 0)},
                ],
            },
            {
                "name": "Polarité", "score": _safe_round(result.get("polarity_score", 50)),
                "weight": 60, "signal": "Positif" if result.get("avg_polarity", 0) > 0.2 else "Négatif" if result.get("avg_polarity", 0) < -0.2 else "Neutre",
                "indicators": [
                    {"name": "Polarité moyenne", "value": _safe_round(result.get("avg_polarity", 0), 3),
                     "signal": "Bullish" if result.get("avg_polarity", 0) > 0.2 else "Bearish" if result.get("avg_polarity", 0) < -0.2 else "Neutre"},
                ],
            },
        ]

    # ---- GENOME ----
    elif criterion == "genome":
        from backend.modules.scanner.genome import (
            compute_genome_score, detect_cycle_phase,
            compute_seismograph, compute_fractal_memory,
        )
        result = compute_genome_score(close, high, low, volume)
        score = result["score"]

        phase_names = {1: "Accumulation", 2: "Markup", 3: "Distribution", 4: "Markdown", 5: "Capitulation"}
        seismo = result.get("seismograph", {})
        signals = seismo.get("signals", {})

        families = [
            {
                "name": "Phase de Cycle (Wyckoff)", "score": _safe_round(result.get("cycle_score", 50)),
                "weight": 30, "signal": phase_names.get(result.get("cycle_phase", 3), "Inconnue"),
                "indicators": [
                    {"name": "Phase actuelle", "value": result.get("cycle_phase", 3),
                     "signal": phase_names.get(result.get("cycle_phase", 3), "Inconnue")},
                ],
            },
            {
                "name": "Sismographe", "score": _safe_round(seismo.get("score", 50)),
                "weight": 40, "signal": f"{seismo.get('active', 0)} micro-signaux actifs",
                "indicators": [
                    {"name": "Bollinger Squeeze", "signal": "Actif" if signals.get("bollinger_squeeze") else "Inactif"},
                    {"name": "Contraction Volume", "signal": "Actif" if signals.get("volume_contraction") else "Inactif"},
                    {"name": "Spike Volume", "signal": "Actif" if signals.get("volume_spike") else "Inactif"},
                    {"name": "Inside Bars", "value": signals.get("inside_bars", 0),
                     "signal": f"{signals.get('inside_bars', 0)} barre(s)"},
                    {"name": "Compression ATR", "signal": "Actif" if signals.get("atr_compression") else "Inactif"},
                    {"name": "Divergence RSI", "signal": "Actif" if signals.get("rsi_divergence") else "Inactif"},
                ],
            },
            {
                "name": "Mémoire Fractale", "score": _safe_round(result.get("fractal_memory", 50)),
                "weight": 30, "signal": "Répétitif" if result.get("fractal_memory", 50) > 65 else "Normal" if result.get("fractal_memory", 50) > 40 else "Unique",
                "indicators": [
                    {"name": "Cosine Similarity max", "value": _safe_round(result.get("fractal_memory", 50)),
                     "signal": "Pattern historique détecté" if result.get("fractal_memory", 50) > 65 else "Pas de pattern répétitif"},
                ],
            },
        ]

    # ---- IPI ----
    elif criterion == "ipi":
        from backend.modules.scanner.institutional import compute_ipi_score
        result = compute_ipi_score(close, high, low, volume)
        score = result["score"]

        vol_anom = result.get("volume_anomaly", {})
        families = [
            {
                "name": "Accumulation/Distribution (A/D)", "score": _safe_round(result.get("ad_score", 50)),
                "weight": 30, "signal": f"Tendance {result.get('ad_trend', 'FLAT')}",
                "indicators": [
                    {"name": "A/D Trend", "signal": result.get("ad_trend", "FLAT")},
                ],
            },
            {
                "name": "Smart Money Flow", "score": _safe_round(result.get("smart_money_score", 50)),
                "weight": 35,
                "signal": "Accumulation" if result.get("smart_money_score", 50) > 65 else "Distribution" if result.get("smart_money_score", 50) < 35 else "Neutre",
                "indicators": [
                    {"name": "Score Smart Money", "value": _safe_round(result.get("smart_money_score", 50)),
                     "signal": "Gros volume, petit mouvement = accumulation" if result.get("smart_money_score", 50) > 65 else "Normal"},
                ],
            },
            {
                "name": "Anomalie de Volume", "score": _safe_round(vol_anom.get("score", 50)),
                "weight": 35,
                "signal": "Anomalie détectée" if vol_anom.get("anomaly") else "Normal",
                "indicators": [
                    {"name": "Ratio Volume", "value": vol_anom.get("ratio", 1.0),
                     "signal": f"{vol_anom.get('ratio', 1.0)}x la moyenne"},
                    {"name": "Anomalie", "signal": "Oui — activité institutionnelle probable" if vol_anom.get("anomaly") else "Non"},
                ],
            },
        ]

    # ---- IVF ----
    elif criterion == "ivf":
        from backend.modules.scanner.fundamental_velocity import compute_ivf_score
        benchmark_close = None
        spy_asset = db.query(Asset).filter_by(symbol="SPY").first()
        if spy_asset:
            spy_rows = db.query(OHLCVDaily).filter_by(asset_id=spy_asset.id).order_by(OHLCVDaily.date.asc()).all()
            if len(spy_rows) >= 60:
                benchmark_close = pd.Series([float(r.close) for r in spy_rows])

        result = compute_ivf_score(close, volume, benchmark_close)
        score = result["score"]

        gaps = result.get("earnings_gaps", {})
        families = [
            {
                "name": "Accélération du Prix", "score": _safe_round(result.get("acceleration", 50)),
                "weight": 35,
                "signal": "Accélération" if result.get("acceleration", 50) > 65 else "Décélération" if result.get("acceleration", 50) < 35 else "Stable",
                "indicators": [
                    {"name": "Momentum 20j accélère", "value": _safe_round(result.get("acceleration", 50)),
                     "signal": "Rendements qui accélèrent" if result.get("acceleration", 50) > 65 else "Stable"},
                ],
            },
            {
                "name": "Force Relative vs Benchmark", "score": _safe_round(result.get("relative_strength", 50)),
                "weight": 30,
                "signal": "Surperformance" if result.get("relative_strength", 50) > 65 else "Sous-performance" if result.get("relative_strength", 50) < 35 else "En ligne",
                "indicators": [
                    {"name": "Performance relative 60j", "value": _safe_round(result.get("relative_strength", 50)),
                     "signal": "Bat le benchmark" if result.get("relative_strength", 50) > 65 else "Sous le benchmark" if result.get("relative_strength", 50) < 35 else "Neutre"},
                ],
            },
            {
                "name": "Gaps Earnings", "score": _safe_round(gaps.get("score", 50)),
                "weight": 35,
                "signal": f"{gaps.get('gaps_up', 0)} gaps up, {gaps.get('gaps_down', 0)} gaps down",
                "indicators": [
                    {"name": "Gaps haussiers", "value": gaps.get("gaps_up", 0), "signal": "Surprises positives"},
                    {"name": "Gaps baissiers", "value": gaps.get("gaps_down", 0), "signal": "Surprises négatives"},
                ],
            },
        ]

    # ---- MTS ----
    elif criterion == "mts":
        from backend.modules.scanner.macro import compute_mts_score

        macro_data = {}
        for sym in ["SPY", "TLT", "GLD"]:
            macro_asset = db.query(Asset).filter_by(symbol=sym).first()
            if macro_asset:
                m_rows = db.query(OHLCVDaily).filter_by(asset_id=macro_asset.id).order_by(OHLCVDaily.date.asc()).all()
                if len(m_rows) >= 50:
                    macro_data[sym] = pd.Series([float(r.close) for r in m_rows])

        result = compute_mts_score(
            asset_class,
            spy_close=macro_data.get("SPY"),
            tlt_close=macro_data.get("TLT"),
            gld_close=macro_data.get("GLD"),
        )
        score = result["score"]

        cycle = result.get("cycle", {})
        rates = result.get("rates", {})
        risk = result.get("risk_appetite", {})

        # Poids selon la classe d'actif (comme dans compute_mts_score)
        if asset_class in ("ACTION_US", "ACTION_EU", "ETF"):
            w_cycle, w_rates, w_risk = 40, 30, 30
        elif asset_class == "CRYPTO":
            w_cycle, w_rates, w_risk = 30, 20, 50
        elif asset_class == "COMMODITY":
            w_cycle, w_rates, w_risk = 25, 35, 40
        else:
            w_cycle, w_rates, w_risk = 34, 33, 33

        families = [
            {
                "name": "Cycle Économique", "score": _safe_round(cycle.get("score", 50)),
                "weight": w_cycle, "signal": cycle.get("phase", "unknown").capitalize(),
                "indicators": [
                    {"name": "Phase", "signal": cycle.get("phase", "unknown").capitalize()},
                    {"name": "Proxy", "signal": "SPY vs SMA200"},
                ],
            },
            {
                "name": "Régime de Taux", "score": _safe_round(rates.get("score", 50)),
                "weight": w_rates, "signal": rates.get("regime", "neutral").capitalize(),
                "indicators": [
                    {"name": "Régime", "signal": rates.get("regime", "neutral").replace("_", " ").capitalize()},
                    {"name": "Proxy", "signal": "TLT (obligations 20+ ans)"},
                ],
            },
            {
                "name": "Appétit pour le Risque", "score": _safe_round(risk.get("score", 50)),
                "weight": w_risk, "signal": risk.get("regime", "neutral").replace("_", " ").capitalize(),
                "indicators": [
                    {"name": "Régime", "signal": risk.get("regime", "neutral").replace("_", " ").capitalize()},
                    {"name": "Proxy", "signal": "Ratio SPY/GLD"},
                ],
            },
        ]

    # ---- SGI ----
    elif criterion == "sgi":
        from backend.modules.scanner.social import compute_sgi_score
        from backend.modules.scanner.sentiment import _simulate_mentions
        mentions = _simulate_mentions(symbol)
        result = compute_sgi_score(mentions, symbol, asset_class)
        score = result["score"]

        sentiment_sub = result.get("sentiment", {})
        families = [
            {
                "name": "Sentiment Social", "score": _safe_round(sentiment_sub.get("score", 50)),
                "weight": 30, "signal": f"{sentiment_sub.get('num_mentions', 0)} mentions",
                "indicators": [
                    {"name": "Volume Score", "value": _safe_round(sentiment_sub.get("volume_score", 0))},
                    {"name": "Polarité Score", "value": _safe_round(sentiment_sub.get("polarity_score", 50))},
                ],
            },
            {
                "name": "Ratio Signal/Bruit", "score": _safe_round(result.get("signal_to_noise", 50)),
                "weight": 25,
                "signal": "Haute conviction" if result.get("signal_to_noise", 50) > 70 else "Beaucoup de bruit" if result.get("signal_to_noise", 50) < 40 else "Normal",
                "indicators": [
                    {"name": "Qualité des discussions", "value": _safe_round(result.get("signal_to_noise", 50)),
                     "signal": "Forte" if result.get("signal_to_noise", 50) > 70 else "Faible" if result.get("signal_to_noise", 50) < 40 else "Moyenne"},
                ],
            },
            {
                "name": "Network Effect", "score": _safe_round(result.get("network_effect", 50)),
                "weight": 20,
                "signal": "Applicable" if asset_class == "CRYPTO" else "Non applicable (non-crypto)",
                "indicators": [
                    {"name": "Loi de Metcalfe", "value": _safe_round(result.get("network_effect", 50)),
                     "signal": "Réseau en croissance" if result.get("network_effect", 50) > 65 else "Stable"},
                ],
            },
            {
                "name": "Momentum d'Intérêt", "score": _safe_round(result.get("interest_momentum", 50)),
                "weight": 25,
                "signal": "En hausse" if result.get("interest_momentum", 50) > 65 else "En baisse" if result.get("interest_momentum", 50) < 35 else "Stable",
                "indicators": [
                    {"name": "Tendance des mentions", "value": _safe_round(result.get("interest_momentum", 50)),
                     "signal": "Intérêt croissant" if result.get("interest_momentum", 50) > 65 else "Intérêt décroissant" if result.get("interest_momentum", 50) < 35 else "Stable"},
                ],
            },
        ]

    # ---- SUS ----
    elif criterion == "sus":
        from backend.modules.scanner.uniqueness import compute_sus_score
        from backend.modules.scanner.indicators import compute_technical_score

        # Calcul des scores techniques pour le crowding
        all_assets = db.query(Asset).filter_by(is_active=True).all()
        all_tech_scores = {}
        for a in all_assets:
            a_rows = db.query(OHLCVDaily).filter_by(asset_id=a.id).order_by(OHLCVDaily.date.asc()).all()
            if len(a_rows) >= 50:
                a_close = pd.Series([float(r.close) for r in a_rows])
                a_high = pd.Series([float(r.high) for r in a_rows])
                a_low = pd.Series([float(r.low) for r in a_rows])
                a_volume = pd.Series([float(r.volume) for r in a_rows])
                all_tech_scores[a.symbol] = compute_technical_score(a_close, a_high, a_low, a_volume)

        result = compute_sus_score(close, high, low, all_tech_scores, symbol)
        score = result["score"]

        families = [
            {
                "name": "Crowding Score", "score": _safe_round(result.get("crowding", 50)),
                "weight": 30,
                "signal": "Signal unique" if result.get("crowding", 50) > 70 else "Signal crowdé" if result.get("crowding", 50) < 30 else "Modéré",
                "indicators": [
                    {"name": "Actifs avec signal similaire", "value": _safe_round(result.get("crowding", 50)),
                     "signal": "Peu d'actifs = bon" if result.get("crowding", 50) > 70 else "Trop d'actifs similaires"},
                ],
            },
            {
                "name": "Novelty Score", "score": _safe_round(result.get("novelty", 50)),
                "weight": 25,
                "signal": "Comportement inhabituel" if result.get("novelty", 50) > 65 else "Normal",
                "indicators": [
                    {"name": "Z-score des rendements", "value": _safe_round(result.get("novelty", 50)),
                     "signal": "Inhabituel = haute valeur" if result.get("novelty", 50) > 65 else "Comportement normal"},
                ],
            },
            {
                "name": "Timeframe Neglect", "score": _safe_round(result.get("timeframe_neglect", 50)),
                "weight": 20,
                "signal": "Signal négligé" if result.get("timeframe_neglect", 50) > 65 else "Visible sur les TF populaires",
                "indicators": [
                    {"name": "Divergence inter-TF", "value": _safe_round(result.get("timeframe_neglect", 50)),
                     "signal": "RSI/MACD divergent entre daily et weekly" if result.get("timeframe_neglect", 50) > 65 else "Aligné"},
                ],
            },
            {
                "name": "Complexity Premium", "score": _safe_round(result.get("complexity_premium", 50)),
                "weight": 25,
                "signal": "Analyse complexe requise" if result.get("complexity_premium", 50) > 65 else "Signal simple (visible par tous)",
                "indicators": [
                    {"name": "Complexité du signal", "value": _safe_round(result.get("complexity_premium", 50)),
                     "signal": "Avantage (signal complexe)" if result.get("complexity_premium", 50) > 65 else "Pas d'avantage"},
                ],
            },
        ]

    # ---- NARRATIVE ----
    elif criterion == "narrative":
        from backend.modules.scanner.narrative import compute_narrative_score
        result = compute_narrative_score(close, high, low, volume)
        score = result["score"]

        comp = result.get("components", {})
        signal = result.get("signal", "NEUTRAL")

        weights = {
            "volume_acceleration": 25,
            "momentum_shift": 25,
            "breakout_freshness": 20,
            "cross_tf_alignment": 15,
            "anomaly": 15,
        }

        families = [
            {
                "name": "Accélération Volume", "score": _safe_round(comp.get("volume_acceleration", 50)),
                "weight": weights["volume_acceleration"],
                "signal": "Volume explose" if comp.get("volume_acceleration", 50) > 70 else "Volume en contraction" if comp.get("volume_acceleration", 50) < 35 else "Stable",
                "indicators": [
                    {"name": "Volume 5j vs 20j vs 60j", "value": _safe_round(comp.get("volume_acceleration", 50)),
                     "signal": "Smart money en action" if comp.get("volume_acceleration", 50) > 70 else "Normal"},
                ],
            },
            {
                "name": "Shift de Momentum", "score": _safe_round(comp.get("momentum_shift", 50)),
                "weight": weights["momentum_shift"],
                "signal": "Changement de régime" if comp.get("momentum_shift", 50) > 65 else "Flat",
                "indicators": [
                    {"name": "Momentum court vs long", "value": _safe_round(comp.get("momentum_shift", 50)),
                     "signal": "De flat à directionnel" if comp.get("momentum_shift", 50) > 65 else "Pas de changement"},
                ],
            },
            {
                "name": "Fraîcheur du Breakout", "score": _safe_round(comp.get("breakout_freshness", 50)),
                "weight": weights["breakout_freshness"],
                "signal": "Breakout récent" if comp.get("breakout_freshness", 50) > 65 else "Dans le range",
                "indicators": [
                    {"name": "Cassure Donchian 20j", "value": _safe_round(comp.get("breakout_freshness", 50)),
                     "signal": "Cassure dans les 5 derniers jours" if comp.get("breakout_freshness", 50) > 65 else "Pas de cassure"},
                ],
            },
            {
                "name": "Alignement Cross-Timeframe", "score": _safe_round(comp.get("cross_tf_alignment", 50)),
                "weight": weights["cross_tf_alignment"],
                "signal": "Aligné" if comp.get("cross_tf_alignment", 50) > 65 else "Divergent",
                "indicators": [
                    {"name": "Daily + Weekly + Monthly", "value": _safe_round(comp.get("cross_tf_alignment", 50)),
                     "signal": "Même direction" if comp.get("cross_tf_alignment", 50) > 65 else "Directions mixtes"},
                ],
            },
            {
                "name": "Score d'Anomalie", "score": _safe_round(comp.get("anomaly", 50)),
                "weight": weights["anomaly"],
                "signal": "Comportement anomal" if comp.get("anomaly", 50) > 65 else "Normal",
                "indicators": [
                    {"name": "Z-score prix + volume", "value": _safe_round(comp.get("anomaly", 50)),
                     "signal": "Narrative en cours (statistiquement inhabituel)" if comp.get("anomaly", 50) > 65 else "Rien d'anormal"},
                ],
            },
        ]
        # Ajouter le signal directionnel global
        families.insert(0, {
            "name": "Signal Narratif", "score": _safe_round(score), "weight": 0,
            "signal": signal.replace("_", " ").capitalize(),
            "indicators": [],
        })

    return {
        "criterion": criterion,
        "criterion_name": CRITERION_NAMES[criterion],
        "score": _safe_round(score),
        "symbol": symbol,
        "price": round(float(close.iloc[-1]), 2),
        "families": families,
    }


@router.get("/results/{symbol}")
def get_scan_result(symbol: str, db: Session = Depends(get_sync_db)):
    """Retourne le résultat de scan pour un actif donné — depuis le cache."""
    cached = get_cached_results()
    for r in cached:
        if isinstance(r, dict) and r.get("symbol") == symbol:
            return r

    service = ScannerService(db)
    return service.scan_asset(symbol)


@router.get("/assets")
def list_assets(db: Session = Depends(get_sync_db)):
    """Liste tous les actifs en base."""
    assets = db.query(Asset).filter_by(is_active=True).all()
    return [
        {
            "id": a.id,
            "symbol": a.symbol,
            "name": a.name,
            "asset_class": a.asset_class.value,
        }
        for a in assets
    ]


@router.get("/ohlcv/{symbol}")
def get_ohlcv(symbol: str, limit: int = 100, db: Session = Depends(get_sync_db)):
    """Retourne les données OHLCV daily d'un actif."""
    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return {"error": f"Actif {symbol} non trouvé"}

    rows = (
        db.query(OHLCVDaily)
        .filter_by(asset_id=asset.id)
        .order_by(OHLCVDaily.date.desc())
        .limit(limit)
        .all()
    )

    return {
        "symbol": symbol,
        "name": asset.name,
        "count": len(rows),
        "data": [
            {
                "date": str(r.date),
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            }
            for r in reversed(rows)
        ],
    }


@router.get("/sentiment/{symbol}")
async def get_sentiment(symbol: str):
    """Score de sentiment pour un actif (Reddit + simulation)."""
    mentions = await fetch_reddit_mentions(symbol)
    result = compute_sentiment_score(mentions)
    result["symbol"] = symbol
    return result


@router.get("/ohlcv-1h/{symbol}")
def get_ohlcv_1h(symbol: str, limit: int = 168, db: Session = Depends(get_sync_db)):
    """Données OHLCV intraday 1H d'un actif."""
    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return {"error": f"Actif {symbol} non trouvé"}

    rows = (
        db.query(OHLCV1H)
        .filter_by(asset_id=asset.id)
        .order_by(OHLCV1H.datetime.desc())
        .limit(limit)
        .all()
    )

    return {
        "symbol": symbol,
        "timeframe": "1h",
        "count": len(rows),
        "data": [
            {
                "datetime": r.datetime.isoformat(),
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            }
            for r in reversed(rows)
        ],
    }


@router.get("/mta/{symbol}")
def get_multi_timeframe(symbol: str, db: Session = Depends(get_sync_db)):
    """Analyse Multi-Timeframe V2 — Weekly + Daily + 4H + 1H."""
    import pandas as pd

    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        return {"error": f"Actif {symbol} non trouvé"}

    # Daily
    daily_rows = (
        db.query(OHLCVDaily).filter_by(asset_id=asset.id)
        .order_by(OHLCVDaily.date.asc()).all()
    )
    if not daily_rows:
        return {"error": "Pas de données daily"}

    daily_df = pd.DataFrame([{
        "date": r.date, "open": float(r.open), "high": float(r.high),
        "low": float(r.low), "close": float(r.close), "volume": float(r.volume),
    } for r in daily_rows])
    daily_close = daily_df["close"]
    daily_high = daily_df["high"]
    daily_low = daily_df["low"]
    daily_volume = daily_df["volume"]

    # 1H
    hourly_rows = (
        db.query(OHLCV1H).filter_by(asset_id=asset.id)
        .order_by(OHLCV1H.datetime.asc()).all()
    )
    hourly_df = None
    hourly_close = None
    hourly_high = None
    hourly_low = None
    hourly_volume = None
    if hourly_rows:
        hourly_df = pd.DataFrame([{
            "datetime": r.datetime, "open": float(r.open), "high": float(r.high),
            "low": float(r.low), "close": float(r.close), "volume": float(r.volume),
        } for r in hourly_rows])
        hourly_close = hourly_df["close"]
        hourly_high = hourly_df["high"]
        hourly_low = hourly_df["low"]
        hourly_volume = hourly_df["volume"]

    result = compute_mta_score(
        daily_close=daily_close, hourly_close=hourly_close,
        daily_high=daily_high, daily_low=daily_low, daily_volume=daily_volume,
        hourly_high=hourly_high, hourly_low=hourly_low, hourly_volume=hourly_volume,
        daily_df=daily_df, hourly_df=hourly_df,
    )
    result["symbol"] = symbol
    return result


# ============================================================
# Endpoints LIVE (Alpaca temps réel)
# ============================================================

from backend.modules.scanner.live_data import get_live_quote, get_live_bars, is_alpaca_symbol


@router.get("/live/quote/{symbol}")
def live_quote(symbol: str):
    """Prix temps réel via Alpaca."""
    quote = get_live_quote(symbol)
    if quote:
        return quote
    return {"symbol": symbol, "error": "Pas de données live pour cet actif", "source": "unavailable"}


@router.get("/live/quotes")
def live_quotes_all(db: Session = Depends(get_sync_db)):
    """Prix temps réel pour tous les actifs supportés par Alpaca."""
    assets = db.query(Asset).filter_by(is_active=True).all()
    results = []
    for asset in assets:
        quote = get_live_quote(asset.symbol)
        if quote:
            quote["name"] = asset.name
            quote["asset_class"] = asset.asset_class.value
            results.append(quote)
        else:
            # Fallback BDD
            last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
            results.append({
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_class": asset.asset_class.value,
                "price": float(last.close) if last else 0,
                "source": "database",
            })
    return results


@router.get("/live/bars/{symbol}")
def live_bars(symbol: str, timeframe: str = "1Day", limit: int = 100):
    """Barres OHLCV live via Alpaca."""
    bars = get_live_bars(symbol, timeframe, limit)
    if bars:
        return {"symbol": symbol, "timeframe": timeframe, "count": len(bars), "data": bars, "source": "alpaca_live"}
    return {"symbol": symbol, "error": "Pas de données live", "source": "unavailable"}
