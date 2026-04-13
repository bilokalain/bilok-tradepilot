"""Analyse rapide d'un actif quelconque — pas besoin d'être en BDD.

L'utilisateur tape un symbole (ex: ^GSPC, PLTR, COIN, AMC)
et le système :
1. Télécharge les données via Yahoo Finance
2. Calcule les indicateurs techniques
3. Détecte le régime
4. Sélectionne la meilleure stratégie
5. Produit un score et une recommandation

Tout en une seule requête, sans sauvegarder en BDD.
"""

import numpy as np
import pandas as pd
import yfinance as yf

from backend.modules.scanner.indicators import (
    compute_technical_score, sma, rsi, macd, bollinger_bands, atr,
)
from backend.modules.analyser.regime import detect_regime
from backend.modules.analyser.strategies import (
    strategy_trend_following, strategy_mean_reversion,
    strategy_breakout, strategy_momentum,
)
from backend.modules.analyser.strategies_advanced import (
    strategy_mean_reversion_v2, strategy_fibonacci, strategy_ichimoku,
)
from backend.modules.scanner.genome import compute_genome_score
from backend.modules.scanner.institutional import compute_ipi_score
from backend.modules.scanner.fundamental_velocity import compute_ivf_score
from backend.modules.scanner.uniqueness import compute_novelty_score, compute_timeframe_neglect, compute_complexity_premium


# Symboles courants et leurs équivalents Yahoo Finance
SYMBOL_ALIASES = {
    "S&P 500": "^GSPC", "S&P500": "^GSPC", "SP500": "^GSPC",
    "CAC 40": "^FCHI", "CAC40": "^FCHI",
    "DAX": "^GDAXI", "DAX 40": "^GDAXI",
    "NASDAQ": "^IXIC", "NASDAQ 100": "^NDX",
    "DOW JONES": "^DJI", "DOW": "^DJI", "DJIA": "^DJI",
    "NIKKEI": "^N225", "NIKKEI 225": "^N225",
    "FTSE": "^FTSE", "FTSE 100": "^FTSE",
    "BITCOIN": "BTC-USD", "BTC": "BTC-USD",
    "ETHEREUM": "ETH-USD", "ETH": "ETH-USD",
    "GOLD": "GC=F", "OR": "GC=F",
    "OIL": "CL=F", "PETROLE": "CL=F", "PÉTROLE": "CL=F", "CRUDE": "CL=F",
    "CRUDE OIL": "CL=F", "WTI": "CL=F",
    "SILVER": "SI=F", "ARGENT": "SI=F",
    "CUIVRE": "HG=F", "COPPER": "HG=F",
    "PLATINE": "PL=F", "PLATINUM": "PL=F",
    "GAZ": "NG=F", "GAZ NATUREL": "NG=F", "NATURAL GAS": "NG=F",
    "BLE": "ZW=F", "BLÉ": "ZW=F", "WHEAT": "ZW=F",
    "MAIS": "ZC=F", "MAÏS": "ZC=F", "CORN": "ZC=F",
    "SOJA": "ZS=F", "SOYBEAN": "ZS=F",
    "CACAO": "CC=F", "COCOA": "CC=F",
    "EURO DOLLAR": "EURUSD=X", "EUR/USD": "EURUSD=X",
    "LIVRE DOLLAR": "GBPUSD=X", "GBP/USD": "GBPUSD=X",
    "DOLLAR YEN": "USDJPY=X", "USD/JPY": "USDJPY=X",
    "SOLANA": "SOL-USD", "SOL": "SOL-USD",
    "DOGECOIN": "DOGE-USD", "DOGE": "DOGE-USD",
    "CARDANO": "ADA-USD", "ADA": "ADA-USD",
    "RIPPLE": "XRP-USD", "XRP": "XRP-USD",
}


def resolve_symbol(query: str) -> str:
    """Convertit un nom commun en symbole Yahoo Finance."""
    upper = query.upper().strip()
    return SYMBOL_ALIASES.get(upper, query.strip())


def quick_analyse(query: str) -> dict:
    """Analyse complète d'un actif quelconque."""
    symbol = resolve_symbol(query)

    # 1. Télécharger les données
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2y", interval="1d")
    except Exception as e:
        return {"error": f"Impossible de récupérer les données pour '{query}' ({symbol}): {e}"}

    if df.empty or len(df) < 50:
        return {"error": f"Pas assez de données pour '{query}' ({symbol}). Vérifiez le symbole Yahoo Finance."}

    # Infos de base
    info = {}
    try:
        ti = ticker.info
        info = {
            "name": ti.get("longName") or ti.get("shortName") or symbol,
            "sector": ti.get("sector", ""),
            "industry": ti.get("industry", ""),
            "market_cap": ti.get("marketCap", 0),
            "currency": ti.get("currency", "USD"),
            "exchange": ti.get("exchange", ""),
        }
    except Exception:
        info = {"name": symbol, "sector": "", "industry": "", "market_cap": 0, "currency": "USD", "exchange": ""}

    close = pd.Series(df["Close"].values, dtype=float)
    high = pd.Series(df["High"].values, dtype=float)
    low = pd.Series(df["Low"].values, dtype=float)
    volume = pd.Series(df["Volume"].values, dtype=float)
    last_price = float(close.iloc[-1])

    # Prix live Alpaca si disponible
    live_price = None
    try:
        from backend.modules.scanner.live_data import get_live_quote
        quote = get_live_quote(symbol)
        if quote and quote.get("price"):
            live_price = float(quote["price"])
            last_price = live_price  # Utiliser le prix live
    except Exception:
        pass

    # 2. Indicateurs techniques
    tech_score = compute_technical_score(close, high, low, volume)

    rsi_val = float(rsi(close).iloc[-1]) if len(close) >= 14 else 50
    macd_data = macd(close)
    macd_hist = float(macd_data["histogram"].iloc[-1]) if not np.isnan(macd_data["histogram"].iloc[-1]) else 0
    sma_20 = float(sma(close, 20).iloc[-1]) if len(close) >= 20 else last_price
    sma_50 = float(sma(close, 50).iloc[-1]) if len(close) >= 50 else last_price
    sma_200 = float(sma(close, 200).iloc[-1]) if len(close) >= 200 else last_price
    atr_val = float(atr(high, low, close, 14).iloc[-1]) if len(close) >= 14 else 0
    bb = bollinger_bands(close)

    # 3. Génome + IPI + IVF
    genome = compute_genome_score(close, high, low, volume) if len(close) >= 100 else {"score": 50, "cycle_phase": 3, "seismograph": {"active": 0}}
    ipi = compute_ipi_score(close, high, low, volume)
    ivf = compute_ivf_score(close, volume)

    # 4. Régime
    if len(close) >= 200:
        regime_result = detect_regime(close, high, low)
    else:
        regime_result = {"regime": "UNKNOWN", "probabilities": {}, "confidence": 0}

    # 5. Stratégies (toutes, y compris pro)
    from backend.modules.analyser.strategies_pro import (
        strategy_adaptive_trend, strategy_multi_signal,
        strategy_keltner_breakout, strategy_vwap_reversion,
        strategy_momentum_rotation,
    )

    strategies_results = []
    all_strategies = {
        "trend_following": lambda: strategy_trend_following(close, high, low),
        "mean_reversion": lambda: strategy_mean_reversion(close, high, low),
        "breakout": lambda: strategy_breakout(close, high, low, volume),
        "momentum": lambda: strategy_momentum(close, high, low),
        "adaptive_trend": lambda: strategy_adaptive_trend(close, high, low, volume),
        "multi_signal": lambda: strategy_multi_signal(close, high, low, volume),
        "keltner_breakout": lambda: strategy_keltner_breakout(close, high, low, volume),
        "vwap_reversion": lambda: strategy_vwap_reversion(close, high, low, volume),
        "momentum_rotation": lambda: strategy_momentum_rotation(close, high, low, volume),
    }
    if len(close) >= 60:
        all_strategies["mean_reversion_v2"] = lambda: strategy_mean_reversion_v2(close, high, low, volume)
        all_strategies["fibonacci"] = lambda: strategy_fibonacci(close, high, low)
    if len(close) >= 80:
        all_strategies["ichimoku"] = lambda: strategy_ichimoku(close, high, low)

    best_strategy = None
    best_conviction = 0

    # Précision et multiplicateurs adaptatifs selon le type d'actif
    if last_price < 5:
        # Forex, penny stocks — prix bas, besoin de plus de décimales
        price_decimals = 5 if last_price < 2 else 4
        sl_mult = 3.0  # Plus large en pips
        tp_mult = 5.0
    elif last_price < 50:
        price_decimals = 3
        sl_mult = 2.0
        tp_mult = 3.0
    else:
        price_decimals = 2
        sl_mult = 2.0
        tp_mult = 3.0

    for name, func in all_strategies.items():
        try:
            result = func()
            # Ajouter entry/SL/TP si manquants — avec précision adaptée
            if "entry" not in result or result.get("entry") is None:
                result["entry"] = round(last_price, price_decimals)
            else:
                result["entry"] = round(result["entry"], price_decimals)
            if "stop_loss" not in result or result.get("stop_loss") is None:
                if result.get("direction") == "LONG":
                    result["stop_loss"] = round(last_price - sl_mult * atr_val, price_decimals)
                elif result.get("direction") == "SHORT":
                    result["stop_loss"] = round(last_price + sl_mult * atr_val, price_decimals)
            else:
                result["stop_loss"] = round(result["stop_loss"], price_decimals)
            if "take_profit" not in result or result.get("take_profit") is None:
                if result.get("direction") == "LONG":
                    result["take_profit"] = round(last_price + tp_mult * atr_val, price_decimals)
                elif result.get("direction") == "SHORT":
                    result["take_profit"] = round(last_price - tp_mult * atr_val, price_decimals)
            else:
                result["take_profit"] = round(result["take_profit"], price_decimals)
            strategies_results.append(result)
            if result["conviction"] > best_conviction and result["direction"] != "NEUTRAL":
                best_conviction = result["conviction"]
                best_strategy = result
        except Exception:
            pass

    # 6. Scores détaillés
    novelty = compute_novelty_score(close) if len(close) >= 252 else 50
    complexity = compute_complexity_premium(close, high, low) if len(close) >= 50 else 50

    scores = {
        "technical": round(tech_score, 1),
        "genome": round(genome["score"], 1),
        "ipi": round(ipi["score"], 1),
        "ivf": round(ivf["score"], 1),
        "novelty": round(novelty, 1),
        "complexity": round(complexity, 1),
    }

    # 7. Score V2 (même méthode que le pipeline)
    from backend.modules.scoring.scorer_v2 import compute_score_v2
    from backend.modules.analyser.performance_matrix import get_best_strategy, get_strategy_sharpe

    best_strat_name = best_strategy["strategy"] if best_strategy else "momentum"
    backtest_sharpe = get_strategy_sharpe(symbol, best_strat_name) if get_best_strategy(symbol) else 0

    score_v2_result = compute_score_v2(
        scanner_score=tech_score,
        strategy_conviction=best_conviction,
        backtest_sharpe=backtest_sharpe,
        symbol=symbol,
        asset_class="CRYPTO" if "-USD" in symbol else "FOREX" if "=X" in symbol else "COMMODITY" if "=F" in symbol else "ACTION_US",
    )

    global_score = score_v2_result["score_v2"]
    action = score_v2_result["action"]

    # SL/TP avec précision adaptée
    if best_strategy and best_strategy.get("direction") == "LONG":
        sl = round(last_price - sl_mult * atr_val, price_decimals)
        tp = round(last_price + tp_mult * atr_val, price_decimals)
    elif best_strategy and best_strategy.get("direction") == "SHORT":
        sl = round(last_price + sl_mult * atr_val, price_decimals)
        tp = round(last_price - tp_mult * atr_val, price_decimals)
    else:
        sl = 0
        tp = 0

    # Performance récente
    perf_1m = round((close.iloc[-1] / close.iloc[-21] - 1) * 100, 2) if len(close) >= 21 else 0
    perf_3m = round((close.iloc[-1] / close.iloc[-63] - 1) * 100, 2) if len(close) >= 63 else 0
    perf_1y = round((close.iloc[-1] / close.iloc[-252] - 1) * 100, 2) if len(close) >= 252 else 0

    def _clean(obj):
        """Convertit les types numpy en types Python natifs pour JSON."""
        import json
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_clean(v) for v in obj]
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_,)):
            return bool(obj)
        return obj

    return _clean({
        "symbol": symbol,
        "query": query,
        "info": info,
        "last_price": round(last_price, price_decimals),
        "live_price": round(live_price, price_decimals) if live_price else None,
        "price_source": "alpaca_live" if live_price else "yahoo_close",
        "data_points": len(df),
        "action": action,
        "global_score": round(global_score, 1),
        "score_v2": score_v2_result,
        "scores": scores,
        "regime": regime_result,
        "best_strategy": {
            "name": best_strategy["strategy"] if best_strategy else None,
            "direction": best_strategy["direction"] if best_strategy else "NEUTRAL",
            "conviction": best_strategy["conviction"] if best_strategy else 0,
            "entry": round(last_price, 2),
            "stop_loss": sl,
            "take_profit": tp,
        },
        "all_strategies": strategies_results,
        "indicators": {
            "rsi": round(rsi_val, 1),
            "macd_histogram": round(macd_hist, 4),
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "sma_200": round(sma_200, 2),
            "atr": round(atr_val, 2),
            "bb_upper": round(float(bb["upper"].iloc[-1]), 2) if not np.isnan(bb["upper"].iloc[-1]) else 0,
            "bb_lower": round(float(bb["lower"].iloc[-1]), 2) if not np.isnan(bb["lower"].iloc[-1]) else 0,
        },
        "details": {
            "genome_phase": genome.get("cycle_phase", 0),
            "seismograph_active": genome.get("seismograph", {}).get("active", 0),
            "ipi_ad_trend": ipi.get("ad_trend", ""),
            "ivf_acceleration": ivf.get("acceleration", 0),
        },
        "performance": {
            "1_month": perf_1m,
            "3_months": perf_3m,
            "1_year": perf_1y,
        },
        "ohlcv": [
            {"date": str(df.index[i].date()), "open": round(float(df["Open"].iloc[i]), 2),
             "high": round(float(df["High"].iloc[i]), 2), "low": round(float(df["Low"].iloc[i]), 2),
             "close": round(float(df["Close"].iloc[i]), 2), "volume": int(df["Volume"].iloc[i])}
            for i in range(max(0, len(df) - 100), len(df))
        ],
    })
