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

import logging
import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger("tradepilot.quick_analyse")

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
from backend.modules.scanner.uniqueness import compute_novelty_score, compute_timeframe_neglect, compute_complexity_premium, compute_sus_score
from backend.modules.scanner.macro import compute_mts_score
from backend.modules.scanner.social import compute_sgi_score


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
    # Actions EU — noms courants
    "BNP PARIBAS": "BNP.PA", "BNP": "BNP.PA",
    "DANONE": "BN.PA",
    "HERMES": "RMS.PA", "HERMÈS": "RMS.PA",
    "L'OREAL": "OR.PA", "LOREAL": "OR.PA", "L'ORÉAL": "OR.PA",
    "TOTAL": "TTE.PA", "TOTALENERGIES": "TTE.PA",
    "SANOFI": "SAN.PA",
    "AIR LIQUIDE": "AI.PA",
    "SCHNEIDER": "SU.PA", "SCHNEIDER ELECTRIC": "SU.PA",
    "ESSILOR": "EL.PA", "ESSILORLUXOTTICA": "EL.PA",
    "VINCI": "DG.PA",
    "AIRBUS": "AIR.PA",
    "SAFRAN": "SAF.PA",
    "SAINT GOBAIN": "SGO.PA", "SAINT-GOBAIN": "SGO.PA",
    "PERNOD": "RI.PA", "PERNOD RICARD": "RI.PA",
    "KERING": "KER.PA",
    "STELLANTIS": "STLAP.PA",
    "RENAULT": "RNO.PA",
    "SOCIETE GENERALE": "GLE.PA", "SOCIÉTÉ GÉNÉRALE": "GLE.PA",
    "CREDIT AGRICOLE": "ACA.PA", "CRÉDIT AGRICOLE": "ACA.PA",
    "AXA": "CS.PA",
    "ORANGE": "ORA.PA",
    "ENGIE": "ENGI.PA",
    "BOUYGUES": "EN.PA",
    "CAPGEMINI": "CAP.PA",
    "DASSAULT": "AM.PA", "DASSAULT SYSTEMES": "DSY.PA",
    "THALES": "HO.PA",
    "MICHELIN": "ML.PA",
    "LEGRAND": "LR.PA",
    "PUBLICIS": "PUB.PA",
    "VEOLIA": "VIE.PA",
    "WORLDLINE": "WLN.PA",
    "ALSTOM": "ALO.PA",
    "SIEMENS": "SIE.DE",
    "SAP": "SAP.DE",
    "VOLKSWAGEN": "VOW3.DE", "VW": "VOW3.DE",
    "BMW": "BMW.DE",
    "MERCEDES": "MBG.DE", "MERCEDES BENZ": "MBG.DE",
    "BAYER": "BAYN.DE",
    "BASF": "BAS.DE",
    "DEUTSCHE BANK": "DBK.DE",
    "ADIDAS": "ADS.DE",
    "ASML": "ASML.AS",
    "SHELL": "SHEL.L",
    "UNILEVER": "ULVR.L",
    "NESTLE": "NESN.SW", "NESTLÉ": "NESN.SW",
    "ROCHE": "ROG.SW",
    "NOVARTIS": "NOVN.SW",
    "UBS": "UBSG.SW",
}


def resolve_symbol(query: str) -> str:
    """Convertit un nom commun en symbole Yahoo Finance."""
    upper = query.upper().strip()
    return SYMBOL_ALIASES.get(upper, query.strip())


def _symbol_to_tv(symbol: str) -> tuple[str, str]:
    """Convertit un symbole Yahoo Finance en (symbole TV, exchange TV)."""
    TV_MAP = {
        ".PA": ("EURONEXT", lambda s: s.replace(".PA", "")),
        ".DE": ("XETR", lambda s: s.replace(".DE", "")),
        ".AS": ("EURONEXT", lambda s: s.replace(".AS", "")),
        ".L": ("LSE", lambda s: s.replace(".L", "")),
        ".SW": ("SIX", lambda s: s.replace(".SW", "")),
        ".MI": ("MIL", lambda s: s.replace(".MI", "")),
        ".CO": ("CSE", lambda s: s.replace(".CO", "")),
        ".TO": ("TSX", lambda s: s.replace(".TO", "")),
        ".MC": ("BME", lambda s: s.replace(".MC", "")),
        "-USD": ("BINANCE", lambda s: s.replace("-USD", "USDT")),
        "=X": ("FX_IDC", lambda s: s.replace("=X", "")),
        "=F": ("NYMEX", lambda s: s.replace("=F", "")),
    }
    for suffix, (exchange, transform) in TV_MAP.items():
        if suffix in symbol:
            return transform(symbol), exchange
    # US stocks — pas de suffixe
    return symbol, ""


def _fetch_tvdatafeed(symbol: str, n_bars: int = 500) -> pd.DataFrame | None:
    """Fallback : télécharge les données via TradingView websocket."""
    try:
        from tvDatafeed import TvDatafeed, Interval
        tv_sym, tv_exchange = _symbol_to_tv(symbol)
        tv = TvDatafeed()
        df = tv.get_hist(
            tv_sym,
            exchange=tv_exchange,
            interval=Interval.in_daily,
            n_bars=n_bars,
        )
        if df is not None and not df.empty:
            # Renommer les colonnes pour matcher le format Yahoo
            df = df.rename(columns={
                "open": "Open", "high": "High", "low": "Low",
                "close": "Close", "volume": "Volume",
            })
            return df
    except Exception as e:
        logger.warning(f"[QUICK_ANALYSE] TradingView fallback failed for {symbol}: {e}")
    return None


def quick_analyse(query: str) -> dict:
    """Analyse complète d'un actif quelconque."""
    symbol = resolve_symbol(query)
    data_source = "yahoo"

    # 1. Télécharger les données — Yahoo Finance en priorité, TradingView en fallback
    df = pd.DataFrame()
    ticker = None
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2y", interval="1d")
    except Exception as e:
        logger.warning(f"[QUICK_ANALYSE] Yahoo Finance download failed for {symbol}: {e}")

    if df.empty or len(df) < 50:
        # Fallback TradingView
        tv_df = _fetch_tvdatafeed(symbol)
        if tv_df is not None and len(tv_df) >= 50:
            df = tv_df
            data_source = "tradingview"

    if df.empty or len(df) < 50:
        return {"error": f"Pas assez de données pour '{query}' ({symbol}). Vérifiez le symbole."}

    # Infos de base
    info = {}
    try:
        if ticker:
            ti = ticker.info
            info = {
                "name": ti.get("longName") or ti.get("shortName") or symbol,
                "sector": ti.get("sector", ""),
                "industry": ti.get("industry", ""),
                "market_cap": ti.get("marketCap", 0),
                "currency": ti.get("currency", "USD"),
                "exchange": ti.get("exchange", ""),
            }
    except Exception as e:
        logger.warning(f"[QUICK_ANALYSE] Failed to fetch ticker info for {symbol}: {e}")
    if not info:
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
    except Exception as e:
        logger.warning(f"[QUICK_ANALYSE] Live price fetch failed for {symbol}: {e}")

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
    # Genius strategies
    if len(close) >= 100:
        from backend.modules.analyser.strategies_genius import (
            strategy_regime_cascade, strategy_volatility_explosion, strategy_anti_consensus,
        )
        all_strategies["regime_cascade"] = lambda: strategy_regime_cascade(close, high, low, volume)
        all_strategies["volatility_explosion"] = lambda: strategy_volatility_explosion(close, high, low, volume)
        all_strategies["anti_consensus"] = lambda: strategy_anti_consensus(close, high, low, volume)

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
        except Exception as e:
            logger.warning(f"[QUICK_ANALYSE] Strategy '{name}' failed for {symbol}: {e}")

    # 6. Scores détaillés — les 9 critères complets
    novelty = compute_novelty_score(close) if len(close) >= 252 else 50
    complexity = compute_complexity_premium(close, high, low) if len(close) >= 50 else 50
    try:
        sus_result = compute_sus_score(close, high, low, {}, symbol) if len(close) >= 50 else {"score": 50}
        sus_score = sus_result.get("score", 50) if isinstance(sus_result, dict) else float(sus_result)
    except Exception:
        sus_score = 50

    # MTS (Macro Tailwind)
    if "-USD" in symbol:
        asset_class_mts = "CRYPTO"
    elif "=X" in symbol:
        asset_class_mts = "FOREX"
    elif "=F" in symbol:
        asset_class_mts = "COMMODITY"
    else:
        asset_class_mts = "ACTION_US"
    try:
        mts_result = compute_mts_score(asset_class_mts)
        mts_score = mts_result.get("score", 50)
    except Exception:
        mts_score = 50

    # SGI (Topologie Sociale) — simplifié sans données Reddit
    sgi_score = 50  # Neutre par défaut (pas de données sociales en temps réel)

    # Fondamental
    fundamental_score = 50
    try:
        from backend.modules.scanner.fundamental import compute_fundamental_score
        fund_result = compute_fundamental_score(symbol)
        fundamental_score = fund_result.get("score", 50)
    except Exception:
        pass

    # MTA (Multi-Timeframe Analysis)
    mta_result = {"score": 50, "alignment": "NEUTRAL", "daily": "NEUTRAL", "hourly": "NEUTRAL"}
    try:
        from backend.modules.scanner.multi_timeframe import compute_mta_score
        mta_result = compute_mta_score(symbol)
    except Exception:
        pass

    scores = {
        "technical": round(tech_score, 1),
        "correlation": 50,  # Pas de corrélation en analyse rapide (pas de portefeuille)
        "sentiment": 50,  # Pas de sentiment en temps réel
        "genome": round(genome["score"], 1),
        "ipi": round(ipi["score"], 1),
        "ivf": round(ivf["score"], 1),
        "mts": round(mts_score, 1),
        "sgi": round(sgi_score, 1),
        "sus": round(sus_score, 1),
        "fundamental": round(fundamental_score or 50, 1),
    }

    # 7. Score V2 (même méthode que le pipeline)
    try:
        from backend.modules.scoring.scorer_v2 import compute_score_v2
        from backend.modules.analyser.performance_matrix import get_best_strategy, get_strategy_sharpe

        best_strat_name = best_strategy["strategy"] if best_strategy else "momentum"
        # Essayer avec le best_strat, sinon avec le best du backtest
        bt_best = get_best_strategy(symbol)
        if bt_best:
            backtest_sharpe = get_strategy_sharpe(symbol, bt_best)
        else:
            backtest_sharpe = 0

        # Classe d'actif
        if "-USD" in symbol:
            asset_class = "CRYPTO"
        elif "=X" in symbol:
            asset_class = "FOREX"
        elif "=F" in symbol:
            asset_class = "COMMODITY"
        elif any(s in symbol for s in [".PA", ".DE", ".AS", ".SW", ".MI", ".CO", ".L"]):
            asset_class = "ACTION_EU"
        else:
            asset_class = "ACTION_US"

        score_v2_result = compute_score_v2(
            scanner_score=float(tech_score),
            strategy_conviction=float(best_conviction),
            backtest_sharpe=float(backtest_sharpe),
            symbol=symbol,
            asset_class=asset_class,
        )

        global_score = float(score_v2_result["score_v2"])
        action = score_v2_result["action"]
    except Exception as e:
        # Fallback simplifié si V2 échoue
        global_score = float(np.mean(list(scores.values())))
        if best_strategy and best_conviction >= 60 and global_score >= 55:
            action = "GO"
        elif best_strategy and best_conviction >= 40:
            action = "WAIT"
        else:
            action = "NO_TRADE"
        score_v2_result = {"score_v2": global_score, "action": action, "error": str(e)}

    # SL/TP1/TP2 avec précision adaptée
    tp2_mult = tp_mult * 1.6  # TP2 = 1.6x TP1
    if best_strategy and best_strategy.get("direction") == "LONG":
        sl = round(last_price - sl_mult * atr_val, price_decimals)
        tp = round(last_price + tp_mult * atr_val, price_decimals)
        tp2 = round(last_price + tp2_mult * atr_val, price_decimals)
    elif best_strategy and best_strategy.get("direction") == "SHORT":
        sl = round(last_price + sl_mult * atr_val, price_decimals)
        tp = round(last_price - tp_mult * atr_val, price_decimals)
        tp2 = round(last_price - tp2_mult * atr_val, price_decimals)
    else:
        sl = 0
        tp = 0
        tp2 = 0

    # Sizing Kelly
    risk_reward = abs(tp - last_price) / abs(last_price - sl) if sl != 0 and sl != last_price else 1.5
    win_rate_est = min(0.35 + (global_score / 200), 0.70)  # 35%-70% basé sur le score
    kelly_full = (win_rate_est * risk_reward - (1 - win_rate_est)) / risk_reward if risk_reward > 0 else 0
    kelly_frac = max(0, kelly_full * 0.25)  # 25% du Kelly
    expected_value = win_rate_est * risk_reward - (1 - win_rate_est)

    sizing = {
        "kelly_full": round(kelly_full * 100, 1),
        "kelly_fraction": round(kelly_frac * 100, 1),
        "risk_reward": round(risk_reward, 2),
        "win_rate_est": round(win_rate_est * 100, 1),
        "expected_value": round(expected_value, 3),
        "position_pct": round(min(kelly_frac, 0.15) * 100, 1),
    }

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
        "price_source": "alpaca_live" if live_price else data_source,
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
            "entry": round(last_price, price_decimals),
            "stop_loss": sl,
            "take_profit_1": tp,
            "take_profit_2": tp2,
        },
        "sizing": sizing,
        "mta": mta_result,
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
