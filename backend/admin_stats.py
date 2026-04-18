"""Statistiques de trading professionnelles — calculs avancés."""

import math
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database.sync_session import get_sync_db
from backend.database.models import (
    Asset, Position, PositionStatus, Order, OHLCVDaily, OrderStatus,
)

router = APIRouter()


SYMBOL_SECTORS = {
    "AAPL": "Tech", "MSFT": "Tech", "GOOGL": "Tech", "GOOG": "Tech", "META": "Tech",
    "NVDA": "Tech", "AMD": "Tech", "INTC": "Tech", "MU": "Tech", "AVGO": "Tech",
    "MRVL": "Tech", "QCOM": "Tech", "TXN": "Tech", "AMAT": "Tech", "LRCX": "Tech",
    "KLAC": "Tech", "CRM": "Tech", "ORCL": "Tech", "ADBE": "Tech", "NOW": "Tech",
    "AMZN": "Conso. Cyclique", "TSLA": "Conso. Cyclique", "HD": "Conso. Cyclique",
    "NKE": "Conso. Cyclique", "SBUX": "Conso. Cyclique", "MCD": "Conso. Cyclique",
    "JPM": "Finance", "BAC": "Finance", "GS": "Finance", "MS": "Finance",
    "V": "Finance", "MA": "Finance", "AXP": "Finance",
    "JNJ": "Santé", "UNH": "Santé", "PFE": "Santé", "ABBV": "Santé", "LLY": "Santé",
    "XOM": "Énergie", "CVX": "Énergie", "COP": "Énergie", "SLB": "Énergie",
    "PG": "Conso. Défensif", "KO": "Conso. Défensif", "PEP": "Conso. Défensif",
    "WMT": "Conso. Défensif", "COST": "Conso. Défensif",
    "DIS": "Communication", "NFLX": "Communication", "CMCSA": "Communication",
    "BA": "Industrie", "CAT": "Industrie", "HON": "Industrie", "GE": "Industrie",
    "LMT": "Industrie", "RTX": "Industrie",
    "SPY": "ETF", "QQQ": "ETF", "IWM": "ETF", "DIA": "ETF",
    "GLD": "ETF", "TLT": "ETF", "VTI": "ETF", "VOO": "ETF",
}


def _classify_sector(symbol: str, asset_class: str, sector: str) -> str:
    """Classe un actif dans un secteur lisible."""
    # D'abord le mapping hardcodé (plus fiable)
    if symbol in SYMBOL_SECTORS:
        return SYMBOL_SECTORS[symbol]

    SECTOR_MAP = {
        "Technology": "Tech",
        "Consumer Cyclical": "Conso. Cyclique",
        "Communication Services": "Communication",
        "Financial Services": "Finance",
        "Healthcare": "Santé",
        "Consumer Defensive": "Conso. Défensif",
        "Industrials": "Industrie",
        "Energy": "Énergie",
        "Basic Materials": "Matériaux",
        "Real Estate": "Immobilier",
        "Utilities": "Services publics",
    }
    if asset_class in ("CRYPTO",):
        return "Crypto"
    if asset_class in ("FOREX",):
        return "Forex"
    if asset_class in ("COMMODITY",):
        return "Matières 1ères"
    if asset_class in ("ETF",):
        return "ETF"
    return SECTOR_MAP.get(sector, sector or "Autre")


@router.get("/trades-history")
def trades_history(db: Session = Depends(get_sync_db)):
    """Historique complet de tous les trades (ouverts + fermés)."""
    all_positions = db.query(Position).order_by(Position.opened_at.desc()).all()

    # Prix live Alpaca
    alpaca_prices = {}
    alpaca_symbols = set()
    try:
        from backend.modules.execution.broker_alpaca import alpaca_broker
        if alpaca_broker.is_configured:
            for p in alpaca_broker.get_positions():
                alpaca_prices[p["symbol"]] = p["current_price"]
                alpaca_symbols.add(p["symbol"])
    except Exception:
        pass

    # Mapper asset_id → broker via les ordres (dernier ordre = broker actuel)
    # On groupe par (asset_id, quantity, price) pour différencier paper vs réel
    from backend.database.models import Order as OrderModel
    position_broker_map = {}  # (asset_id, qty_approx) → broker
    all_orders = db.query(OrderModel).order_by(OrderModel.created_at.desc()).all()
    for o in all_orders:
        key = (o.asset_id, round(float(o.quantity), 0))
        if key not in position_broker_map:
            broker_val = o.broker or "local"
            if "alpaca" in broker_val:
                position_broker_map[key] = "alpaca"
            elif "ibkr" in broker_val:
                position_broker_map[key] = "ibkr"
            else:
                position_broker_map[key] = "local"

    trades = []
    for p in all_positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if not asset:
            continue

        entry = float(p.entry_price) if p.entry_price else 0
        exit_price = float(p.exit_price) if p.exit_price else None

        # Prix actuel : Alpaca avec validation croisée BDD
        alpaca_price = alpaca_prices.get(asset.symbol)
        db_last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
        db_price = float(db_last.close) if db_last else None

        if alpaca_price and db_price:
            deviation = abs(alpaca_price - db_price) / db_price if db_price > 0 else 999
            current = alpaca_price if deviation < 0.5 else db_price
        elif alpaca_price:
            current = alpaca_price
        elif db_price:
            current = db_price
        else:
            current = exit_price or entry
        qty = float(p.quantity)
        direction = p.direction.value
        sl = float(p.stop_loss) if p.stop_loss else None
        tp = float(p.take_profit) if p.take_profit else None

        # P&L
        if direction == "LONG":
            price_for_pnl = exit_price if exit_price else current
            pnl = (price_for_pnl - entry) * qty if price_for_pnl else 0
            pnl_pct = ((price_for_pnl / entry) - 1) * 100 if entry and price_for_pnl else 0
        else:
            price_for_pnl = exit_price if exit_price else current
            pnl = (entry - price_for_pnl) * qty if price_for_pnl else 0
            pnl_pct = ((entry / price_for_pnl) - 1) * 100 if price_for_pnl and price_for_pnl > 0 else 0

        # Durée
        duration = None
        if p.opened_at and p.closed_at:
            delta = p.closed_at - p.opened_at
            hours = delta.total_seconds() / 3600
            if hours < 24:
                duration = f"{hours:.0f}h"
            else:
                duration = f"{delta.days}j {int(hours % 24)}h"

        # Résultat
        if p.status.value == "CLOSED":
            if pnl > 0:
                result = "WIN"
            elif pnl < 0:
                result = "LOSS"
            else:
                result = "BREAKEVEN"
            # Raison de fermeture
            if tp and exit_price and ((direction == "LONG" and exit_price >= tp) or (direction == "SHORT" and exit_price <= tp)):
                close_reason = "Take Profit"
            elif sl and exit_price and ((direction == "LONG" and exit_price <= sl) or (direction == "SHORT" and exit_price >= sl)):
                close_reason = "Stop Loss"
            else:
                close_reason = "Manuel"
        else:
            result = "OPEN"
            close_reason = None

        # Déterminer le broker via (asset_id, qty)
        qty_key = (asset.id, round(qty, 0))
        broker = position_broker_map.get(qty_key, "local")
        if broker == "local" and asset.symbol in alpaca_symbols:
            broker = "alpaca"

        trades.append({
            "id": p.id,
            "symbol": asset.symbol,
            "name": asset.name,
            "asset_class": asset.asset_class.value,
            "direction": direction,
            "broker": broker,
            "status": p.status.value,
            "result": result,
            "entry_price": round(entry, 2),
            "exit_price": round(exit_price, 2) if exit_price else None,
            "current_price": round(current, 2) if current else None,
            "quantity": round(qty, 4),
            "stop_loss": round(sl, 2) if sl else None,
            "take_profit": round(tp, 2) if tp else None,
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "opened_at": p.opened_at.isoformat() if p.opened_at else None,
            "closed_at": p.closed_at.isoformat() if p.closed_at else None,
            "duration": duration,
            "close_reason": close_reason,
        })

    # Les positions IBKR sont déjà en BDD (synchronisées).
    # Pas besoin de re-fetcher depuis IBKR live — ça crée des doublons.

    # Stats résumé
    closed_trades = [t for t in trades if t["status"] == "CLOSED"]
    wins = [t for t in closed_trades if t["pnl"] > 0]
    losses = [t for t in closed_trades if t["pnl"] < 0]

    return {
        "trades": trades,
        "summary": {
            "total": len(trades),
            "open": len([t for t in trades if t["status"] == "OPEN"]),
            "closed": len(closed_trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(len(wins) / len(closed_trades) * 100, 1) if closed_trades else 0,
            "total_pnl": round(sum(t["pnl"] for t in closed_trades), 2),
            "avg_win": round(sum(t["pnl"] for t in wins) / len(wins), 2) if wins else 0,
            "avg_loss": round(sum(t["pnl"] for t in losses) / len(losses), 2) if losses else 0,
            "best_trade": max(closed_trades, key=lambda t: t["pnl"]) if closed_trades else None,
            "worst_trade": min(closed_trades, key=lambda t: t["pnl"]) if closed_trades else None,
            "avg_duration": None,  # TODO
        },
    }


@router.get("/trading-stats")
def pro_trading_stats(db: Session = Depends(get_sync_db)):
    """Statistiques de trading professionnelles complètes."""

    # ---- Données Alpaca live ----
    try:
        from backend.modules.execution.broker_alpaca import alpaca_broker
        alpaca_positions = alpaca_broker.get_positions() if alpaca_broker.is_configured else []
        account = alpaca_broker.get_account() if alpaca_broker.is_configured else {}
    except Exception:
        alpaca_positions = []
        account = {}

    equity = float(account.get("equity", 100000))
    cash = float(account.get("cash", 0))
    initial_capital = 100000  # Paper trading
    portfolio_value = equity
    total_invested = portfolio_value - cash

    # ---- Positions live ----
    positions_data = []
    sector_data = defaultdict(lambda: {"invested": 0, "pnl": 0, "count": 0, "positions": []})
    total_pnl = 0
    winners = 0
    losers = 0
    best_trade = {"symbol": "—", "pnl": 0, "pnl_pct": 0}
    worst_trade = {"symbol": "—", "pnl": 0, "pnl_pct": 0}
    pnl_list = []

    for p in alpaca_positions:
        pnl = float(p.get("pnl", 0))
        pnl_pct = float(p.get("pnl_pct", 0))
        mv = float(p.get("market_value", 0))
        symbol = p["symbol"]
        total_pnl += pnl
        pnl_list.append(pnl_pct)

        if pnl >= 0:
            winners += 1
        else:
            losers += 1

        if pnl > best_trade["pnl"]:
            best_trade = {"symbol": symbol, "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2)}
        if pnl < worst_trade["pnl"]:
            worst_trade = {"symbol": symbol, "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2)}

        # Secteur
        asset = db.query(Asset).filter_by(symbol=symbol).first()
        sector = _classify_sector(
            symbol,
            asset.asset_class.value if asset else "ACTION_US",
            asset.sector if asset else "",
        )
        sector_data[sector]["invested"] += mv
        sector_data[sector]["pnl"] += pnl
        sector_data[sector]["count"] += 1
        sector_data[sector]["positions"].append({
            "symbol": symbol,
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "weight": 0,  # Calculé après
            "market_value": round(mv, 2),
        })

        positions_data.append({
            "symbol": symbol,
            "side": p.get("side", "long"),
            "entry": float(p.get("entry_price", 0)),
            "current": float(p.get("current_price", 0)),
            "quantity": float(p.get("quantity", 0)),
            "market_value": round(mv, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "sector": sector,
        })

    # Poids de chaque position
    for pd in positions_data:
        pd["weight"] = round(pd["market_value"] / total_invested * 100, 1) if total_invested > 0 else 0

    # Poids par secteur
    for sec in sector_data.values():
        sec["weight"] = round(sec["invested"] / total_invested * 100, 1) if total_invested > 0 else 0
        sec["pnl"] = round(sec["pnl"], 2)
        sec["invested"] = round(sec["invested"], 2)
        for sp in sec["positions"]:
            sp["weight"] = round(sp["market_value"] / total_invested * 100, 1) if total_invested > 0 else 0

    # ---- Ratios professionnels ----
    n_positions = len(alpaca_positions)
    total_return_pct = (equity / initial_capital - 1) * 100
    win_rate = (winners / n_positions * 100) if n_positions > 0 else 0

    # Profit Factor
    gross_profit = sum(p for p in [float(x.get("pnl", 0)) for x in alpaca_positions] if p > 0)
    gross_loss = abs(sum(p for p in [float(x.get("pnl", 0)) for x in alpaca_positions] if p < 0))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else float("inf") if gross_profit > 0 else 0

    # Average Win / Average Loss
    avg_win = gross_profit / winners if winners > 0 else 0
    avg_loss = gross_loss / losers if losers > 0 else 0
    risk_reward = round(avg_win / avg_loss, 2) if avg_loss > 0 else float("inf") if avg_win > 0 else 0

    # Expectancy (edge per dollar risked)
    if n_positions > 0:
        expectancy = (win_rate / 100 * avg_win - (1 - win_rate / 100) * avg_loss)
    else:
        expectancy = 0

    # Concentration (Herfindahl Index)
    weights = [pd["weight"] / 100 for pd in positions_data]
    herfindahl = sum(w ** 2 for w in weights) if weights else 0
    concentration = "Concentré" if herfindahl > 0.25 else "Équilibré" if herfindahl < 0.15 else "Modéré"

    # Cash ratio
    cash_pct = cash / equity * 100 if equity > 0 else 100

    # Exposure
    long_exposure = sum(pd["market_value"] for pd in positions_data if pd["side"] == "long")
    short_exposure = sum(pd["market_value"] for pd in positions_data if pd["side"] == "short")
    net_exposure = long_exposure - short_exposure
    gross_exposure = long_exposure + short_exposure

    # ---- Historique positions fermées ----
    closed_positions = db.query(Position).filter_by(status=PositionStatus.CLOSED).all()
    closed_pnls = []
    closed_wins = 0
    closed_losses = 0
    for cp in closed_positions:
        if cp.exit_price and cp.entry_price:
            if cp.direction.value == "LONG":
                cpnl = (float(cp.exit_price) - float(cp.entry_price)) * float(cp.quantity)
            else:
                cpnl = (float(cp.entry_price) - float(cp.exit_price)) * float(cp.quantity)
            closed_pnls.append(cpnl)
            if cpnl >= 0:
                closed_wins += 1
            else:
                closed_losses += 1

    # ---- Ordres ----
    total_orders = db.query(Order).count()
    filled_orders = db.query(Order).filter_by(status=OrderStatus.FILLED).count()
    fill_rate = round(filled_orders / total_orders * 100, 1) if total_orders > 0 else 0

    # ---- Score de risque ----
    risk_score = 0
    risk_flags = []
    if cash_pct < 20:
        risk_score += 30
        risk_flags.append("Cash < 20% — sur-exposé")
    if herfindahl > 0.25:
        risk_score += 20
        risk_flags.append("Portefeuille trop concentré")
    if n_positions >= 9:
        risk_score += 15
        risk_flags.append("Proche du max positions (10)")
    if any(abs(pd["pnl_pct"]) > 5 for pd in positions_data):
        risk_score += 10
        risk_flags.append("Position avec P/L > 5%")
    risk_level = "FAIBLE" if risk_score < 20 else "MODÉRÉ" if risk_score < 40 else "ÉLEVÉ" if risk_score < 60 else "CRITIQUE"

    return {
        # Global
        "portfolio": {
            "equity": round(equity, 2),
            "cash": round(cash, 2),
            "cash_pct": round(cash_pct, 1),
            "invested": round(total_invested, 2),
            "initial_capital": initial_capital,
            "total_return": round(total_return_pct, 3),
            "total_pnl": round(total_pnl, 2),
            "daily_pnl": round(total_pnl, 2),  # Live = daily for now
        },
        # Ratios
        "ratios": {
            "win_rate": round(win_rate, 1),
            "profit_factor": profit_factor,
            "risk_reward": risk_reward,
            "expectancy": round(expectancy, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "winners": winners,
            "losers": losers,
        },
        # Exposition
        "exposure": {
            "long": round(long_exposure, 2),
            "short": round(short_exposure, 2),
            "net": round(net_exposure, 2),
            "gross": round(gross_exposure, 2),
            "net_pct": round(net_exposure / equity * 100, 1) if equity > 0 else 0,
            "concentration": concentration,
            "herfindahl": round(herfindahl, 3),
            "n_positions": n_positions,
            "max_positions": 10,
        },
        # Risque
        "risk": {
            "score": risk_score,
            "level": risk_level,
            "flags": risk_flags,
        },
        # Par secteur
        "by_sector": dict(sorted(sector_data.items(), key=lambda x: abs(x[1]["pnl"]), reverse=True)),
        # Positions individuelles triées par P/L
        "positions": sorted(positions_data, key=lambda x: x["pnl"], reverse=True),
        # Historique
        "history": {
            "closed_trades": len(closed_pnls),
            "closed_wins": closed_wins,
            "closed_losses": closed_losses,
            "closed_win_rate": round(closed_wins / len(closed_pnls) * 100, 1) if closed_pnls else 0,
            "total_orders": total_orders,
            "filled_orders": filled_orders,
            "fill_rate": fill_rate,
        },
    }


@router.get("/ibkr-stats")
def ibkr_live_stats(db: Session = Depends(get_sync_db)):
    """Statistiques exclusives du compte IBKR (argent réel)."""
    from backend.config.settings import settings

    if not settings.IBKR_ACCOUNT_ID:
        return {"status": "not_configured", "message": "IBKR non configuré — ajoutez IBKR_ACCOUNT_ID dans .env"}

    # Connexion via thread séparé pour éviter le conflit asyncio FastAPI/ib_insync
    import concurrent.futures
    import asyncio

    def _fetch_ibkr_data():
        """Exécute tout dans un thread séparé avec sa propre boucle asyncio."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        from ib_insync import IB
        ib = IB()
        ib.connect(settings.IBKR_HOST, settings.IBKR_PORT, clientId=10, timeout=10)

        summary = ib.accountSummary(settings.IBKR_ACCOUNT_ID)
        values = {item.tag: item.value for item in summary}
        account = {
            "id": settings.IBKR_ACCOUNT_ID,
            "equity": float(values.get("NetLiquidation", 0)),
            "cash": float(values.get("TotalCashValue", 0)),
            "buying_power": float(values.get("BuyingPower", 0)),
            "currency": values.get("Currency", "EUR"),
            "paper": settings.IBKR_PORT in (7497, 4002),
        }

        ib_positions = ib.positions(settings.IBKR_ACCOUNT_ID)
        positions = []
        for p in ib_positions:
            if p.position == 0:
                continue
            positions.append({
                "symbol": p.contract.symbol,
                "quantity": abs(float(p.position)),
                "side": "long" if p.position > 0 else "short",
                "entry_price": float(p.avgCost),
                "pnl": 0,
                "pnl_pct": 0,
                "market_value": abs(float(p.position)) * float(p.avgCost),
            })

        ib.disconnect()
        loop.close()
        return account, positions

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(_fetch_ibkr_data)
            account, positions = future.result(timeout=20)
    except Exception as e:
        return {"status": "disconnected", "message": f"IBKR déconnecté — {str(e)[:100]}"}

    # Enrichir avec les prix live — validation croisée pour éviter les prix aberrants
    try:
        from backend.modules.execution.broker_alpaca import alpaca_broker
        for pos in positions:
            sym = pos["symbol"]
            entry = pos["entry_price"]
            qty = pos["quantity"]

            # 1. Prix Alpaca
            alpaca_price = None
            if alpaca_broker.is_configured:
                try:
                    alpaca_price = alpaca_broker.get_last_price(sym)
                except Exception:
                    pass

            # 2. Dernier close en BDD (Yahoo Finance) comme référence
            db_price = None
            asset = db.query(Asset).filter_by(symbol=sym).first()
            if asset:
                last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
                if last:
                    db_price = float(last.close)

            # 3. Validation : si Alpaca dévie de > 50% du prix BDD, c'est suspect → utiliser BDD
            price = None
            if alpaca_price and db_price:
                deviation = abs(alpaca_price - db_price) / db_price if db_price > 0 else 999
                if deviation < 0.5:
                    price = alpaca_price  # Alpaca cohérent
                else:
                    price = db_price  # Alpaca aberrant, fallback BDD
            elif alpaca_price:
                price = alpaca_price
            elif db_price:
                price = db_price

            if price:
                if pos["side"] == "long":
                    pos["pnl"] = round((price - entry) * qty, 2)
                    pos["pnl_pct"] = round((price / entry - 1) * 100, 2) if entry > 0 else 0
                else:
                    pos["pnl"] = round((entry - price) * qty, 2)
                    pos["pnl_pct"] = round((1 - price / entry) * 100, 2) if entry > 0 else 0
                pos["current_price"] = round(price, 2)
                pos["market_value"] = round(qty * price, 2)
    except Exception:
        pass

    equity = account["equity"]
    cash = account["cash"]
    invested = equity - cash
    total_pnl = 0
    winners = 0
    losers = 0
    best_trade = {"symbol": "—", "pnl": 0, "pnl_pct": 0}
    worst_trade = {"symbol": "—", "pnl": 0, "pnl_pct": 0}
    positions_data = []

    for p in positions:
        pnl = p.get("pnl", 0)
        pnl_pct = p.get("pnl_pct", 0)
        mv = p.get("market_value", 0)
        total_pnl += pnl

        if pnl >= 0:
            winners += 1
        else:
            losers += 1

        if pnl > best_trade["pnl"]:
            best_trade = {"symbol": p["symbol"], "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2)}
        if pnl < worst_trade["pnl"]:
            worst_trade = {"symbol": p["symbol"], "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2)}

        # Secteur
        asset = db.query(Asset).filter_by(symbol=p["symbol"]).first()
        sector = _classify_sector(
            p["symbol"],
            asset.asset_class.value if asset else "ACTION_US",
            asset.sector if asset else "",
        ) if asset else "Autre"

        positions_data.append({
            "symbol": p["symbol"],
            "side": p.get("side", "long"),
            "entry": p.get("entry_price", 0),
            "current": p.get("current_price", 0),
            "quantity": p.get("quantity", 0),
            "market_value": round(mv, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "sector": sector,
            "weight": round(mv / invested * 100, 1) if invested > 0 else 0,
        })

    n = len(positions)
    initial_capital = settings.IBKR_INITIAL_CAPITAL  # Capital réel déposé
    total_return_pct = (equity / initial_capital - 1) * 100 if initial_capital > 0 else 0
    win_rate = (winners / n * 100) if n > 0 else 0

    # Profit Factor
    gross_profit = sum(p["pnl"] for p in positions_data if p["pnl"] > 0)
    gross_loss = abs(sum(p["pnl"] for p in positions_data if p["pnl"] < 0))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else float("inf") if gross_profit > 0 else 0

    avg_win = gross_profit / winners if winners > 0 else 0
    avg_loss = gross_loss / losers if losers > 0 else 0
    risk_reward = round(avg_win / avg_loss, 2) if avg_loss > 0 else float("inf") if avg_win > 0 else 0

    # Concentration
    weights = [p["weight"] / 100 for p in positions_data]
    herfindahl = sum(w ** 2 for w in weights) if weights else 0

    return {
        "status": "connected",
        "broker": "ibkr",
        "paper": account.get("paper", False),
        "account": {
            "equity": round(equity, 2),
            "cash": round(cash, 2),
            "cash_pct": round(cash / equity * 100, 1) if equity > 0 else 100,
            "invested": round(invested, 2),
            "initial_capital": initial_capital,
            "total_return": round(total_return_pct, 2),
            "total_pnl": round(total_pnl, 2),
            "currency": account.get("currency", "EUR"),
        },
        "ratios": {
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else 999,
            "risk_reward": round(risk_reward, 2) if risk_reward != float("inf") else 999,
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "winners": winners,
            "losers": losers,
        },
        "exposure": {
            "n_positions": n,
            "concentration": "Concentré" if herfindahl > 0.25 else "Équilibré" if herfindahl < 0.15 else "Modéré",
            "herfindahl": round(herfindahl, 3),
        },
        "positions": sorted(positions_data, key=lambda x: x["pnl"], reverse=True),
    }
