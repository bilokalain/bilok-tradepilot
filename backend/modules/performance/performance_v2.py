"""Performance V2 — métriques professionnelles

1. Benchmarks réels (SPY Buy&Hold, 60/40)
2. Equity curve live (tracking jour par jour)
3. Statistiques de trading détaillées
4. Performance par stratégie live
5. Performance par classe d'actif
6. Sharpe/Sortino/Calmar live
7. Drawdown tracking historique
8. Rapport hebdomadaire
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database.models import Asset, OHLCVDaily, Position, Order, PositionStatus, SignalDirection


EQUITY_FILE = Path("data/equity_curve.json")
EQUITY_FILE.parent.mkdir(exist_ok=True)


# ============================================================
# 1. BENCHMARKS RÉELS
# ============================================================

def compute_benchmarks(db: Session, start_date: date | None = None,
                        initial_capital: float = 100_000) -> dict:
    """Compare la performance du portefeuille vs benchmarks réels."""
    # SPY Buy & Hold
    spy = db.query(Asset).filter_by(symbol="SPY").first()
    spy_return = 0
    balanced_return = 0

    if spy:
        spy_rows = db.query(OHLCVDaily).filter_by(asset_id=spy.id).order_by(OHLCVDaily.date.desc()).limit(252).all()
        if len(spy_rows) >= 21:
            spy_now = float(spy_rows[0].close)
            spy_1m = float(spy_rows[20].close) if len(spy_rows) > 20 else spy_now
            spy_1y = float(spy_rows[-1].close) if len(spy_rows) >= 252 else spy_rows[-1].close
            spy_return_1m = (spy_now / spy_1m - 1) * 100
            spy_return_1y = (spy_now / float(spy_1y) - 1) * 100
        else:
            spy_return_1m = 0
            spy_return_1y = 0

        # 60/40 (60% SPY + 40% TLT)
        tlt = db.query(Asset).filter_by(symbol="TLT").first()
        if tlt:
            tlt_rows = db.query(OHLCVDaily).filter_by(asset_id=tlt.id).order_by(OHLCVDaily.date.desc()).limit(252).all()
            if len(tlt_rows) >= 21:
                tlt_now = float(tlt_rows[0].close)
                tlt_1m = float(tlt_rows[20].close)
                tlt_1y = float(tlt_rows[-1].close)
                tlt_ret_1m = (tlt_now / tlt_1m - 1) * 100
                tlt_ret_1y = (tlt_now / float(tlt_1y) - 1) * 100
                balanced_1m = spy_return_1m * 0.6 + tlt_ret_1m * 0.4
                balanced_1y = spy_return_1y * 0.6 + tlt_ret_1y * 0.4
            else:
                balanced_1m = spy_return_1m * 0.6
                balanced_1y = spy_return_1y * 0.6
        else:
            balanced_1m = spy_return_1m * 0.6
            balanced_1y = spy_return_1y * 0.6
    else:
        spy_return_1m = spy_return_1y = balanced_1m = balanced_1y = 0

    # Notre performance
    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    total_pnl = 0
    for p in positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if not asset:
            continue
        last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
        if not last:
            continue
        price = float(last.close)
        if p.direction == SignalDirection.LONG:
            total_pnl += (price - p.entry_price) * p.quantity
        else:
            total_pnl += (p.entry_price - price) * p.quantity

    our_return = (total_pnl / initial_capital) * 100

    return {
        "our_return": round(our_return, 2),
        "benchmarks": {
            "spy_buy_hold_1m": round(spy_return_1m, 2),
            "spy_buy_hold_1y": round(spy_return_1y, 2),
            "balanced_60_40_1m": round(balanced_1m, 2),
            "balanced_60_40_1y": round(balanced_1y, 2),
        },
        "vs_spy": round(our_return - spy_return_1m, 2),
        "vs_balanced": round(our_return - balanced_1m, 2),
        "outperforming_spy": our_return > spy_return_1m,
    }


# ============================================================
# 2. EQUITY CURVE LIVE
# ============================================================

def record_equity(db: Session, initial_capital: float = 100_000):
    """Enregistre l'equity du jour (à appeler quotidiennement)."""
    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    total_pnl = 0
    for p in positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if not asset:
            continue
        last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
        if not last:
            continue
        price = float(last.close)
        if p.direction == SignalDirection.LONG:
            total_pnl += (price - p.entry_price) * p.quantity
        else:
            total_pnl += (p.entry_price - price) * p.quantity

    equity = initial_capital + total_pnl
    today_str = str(date.today())

    # Charger l'historique existant
    curve = _load_equity_curve()
    curve[today_str] = round(equity, 2)
    _save_equity_curve(curve)

    return {"date": today_str, "equity": round(equity, 2), "pnl": round(total_pnl, 2)}


def get_equity_curve() -> dict:
    """Retourne la courbe d'equity complète."""
    curve = _load_equity_curve()
    if not curve:
        return {"dates": [], "values": [], "returns": []}

    dates = sorted(curve.keys())
    values = [curve[d] for d in dates]
    returns = [0]
    for i in range(1, len(values)):
        ret = (values[i] / values[i - 1] - 1) * 100 if values[i - 1] > 0 else 0
        returns.append(round(ret, 3))

    return {"dates": dates, "values": values, "returns": returns}


def _load_equity_curve() -> dict:
    if EQUITY_FILE.exists():
        try:
            return json.loads(EQUITY_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_equity_curve(curve: dict):
    EQUITY_FILE.write_text(json.dumps(curve, indent=2))


# ============================================================
# 3. STATISTIQUES DE TRADING DÉTAILLÉES
# ============================================================

def compute_trading_stats(db: Session) -> dict:
    """Statistiques détaillées sur tous les trades."""
    # Trades fermés
    closed = db.query(Position).filter_by(status=PositionStatus.CLOSED).all()
    # Trades ouverts
    open_pos = db.query(Position).filter_by(status=PositionStatus.OPEN).all()

    all_pnls = []
    wins = []
    losses = []
    durations = []

    for p in closed:
        pnl = float(p.pnl) if p.pnl else 0
        all_pnls.append(pnl)
        if pnl > 0:
            wins.append(pnl)
        elif pnl < 0:
            losses.append(pnl)
        if p.opened_at and p.closed_at:
            dur = (p.closed_at - p.opened_at).days
            durations.append(dur)

    # Open P&L
    open_pnls = []
    for p in open_pos:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if not asset:
            continue
        last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
        if not last:
            continue
        price = float(last.close)
        if p.direction == SignalDirection.LONG:
            pnl = (price - p.entry_price) * p.quantity
        else:
            pnl = (p.entry_price - price) * p.quantity
        open_pnls.append(round(float(pnl), 2))

    # Streaks
    max_win_streak = 0
    max_loss_streak = 0
    current_streak = 0
    for pnl in all_pnls:
        if pnl > 0:
            if current_streak > 0:
                current_streak += 1
            else:
                current_streak = 1
            max_win_streak = max(max_win_streak, current_streak)
        elif pnl < 0:
            if current_streak < 0:
                current_streak -= 1
            else:
                current_streak = -1
            max_loss_streak = max(max_loss_streak, abs(current_streak))

    total_trades = len(all_pnls)
    win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0

    return {
        "total_trades": total_trades,
        "open_trades": len(open_pos),
        "closed_trades": len(closed),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate": round(win_rate, 1),
        "avg_win": round(np.mean(wins), 2) if wins else 0,
        "avg_loss": round(np.mean(losses), 2) if losses else 0,
        "largest_win": round(max(wins), 2) if wins else 0,
        "largest_loss": round(min(losses), 2) if losses else 0,
        "total_pnl_closed": round(sum(all_pnls), 2),
        "total_pnl_open": round(sum(open_pnls), 2),
        "profit_factor": round(sum(wins) / abs(sum(losses)), 2) if losses else 0,
        "avg_duration_days": round(np.mean(durations), 1) if durations else 0,
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak,
        "expectancy": round((win_rate / 100 * np.mean(wins) if wins else 0) + ((1 - win_rate / 100) * np.mean(losses) if losses else 0), 2),
    }


# ============================================================
# 4. PERFORMANCE PAR STRATÉGIE
# ============================================================

def compute_performance_by_strategy(db: Session) -> dict:
    """Performance de chaque stratégie en live."""
    orders = db.query(Order).all()
    positions = db.query(Position).all()

    # Grouper par broker (qui indique la stratégie indirectement)
    # En l'absence de lien direct, on retourne les stats par broker
    by_broker = {}
    for o in orders:
        broker = o.broker or "unknown"
        if broker not in by_broker:
            by_broker[broker] = {"orders": 0, "filled": 0}
        by_broker[broker]["orders"] += 1
        if o.status.value == "FILLED":
            by_broker[broker]["filled"] += 1

    return {"by_broker": by_broker, "total_orders": len(orders)}


# ============================================================
# 5. PERFORMANCE PAR CLASSE D'ACTIF
# ============================================================

def compute_performance_by_class(db: Session) -> dict:
    """P&L par classe d'actif."""
    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    by_class = {}

    for p in positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if not asset:
            continue
        last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
        if not last:
            continue

        price = float(last.close)
        if p.direction == SignalDirection.LONG:
            pnl = (price - p.entry_price) * p.quantity
        else:
            pnl = (p.entry_price - price) * p.quantity

        ac = asset.asset_class.value
        if ac not in by_class:
            by_class[ac] = {"pnl": 0, "positions": 0, "value": 0}
        by_class[ac]["pnl"] += float(pnl)
        by_class[ac]["positions"] += 1
        by_class[ac]["value"] += price * float(p.quantity)

    # Arrondir
    for ac in by_class:
        by_class[ac]["pnl"] = round(by_class[ac]["pnl"], 2)
        by_class[ac]["value"] = round(by_class[ac]["value"], 2)

    return by_class


# ============================================================
# 6. SHARPE / SORTINO / CALMAR LIVE
# ============================================================

def compute_live_ratios(initial_capital: float = 100_000) -> dict:
    """Calcule Sharpe, Sortino et Calmar sur l'equity curve live."""
    curve = _load_equity_curve()
    if len(curve) < 5:
        return {
            "sharpe": 0, "sortino": 0, "calmar": 0,
            "note": f"Minimum 5 jours d'historique ({len(curve)} disponibles)",
        }

    dates = sorted(curve.keys())
    values = [curve[d] for d in dates]
    returns = pd.Series(values).pct_change().dropna()

    if returns.empty or returns.std() == 0:
        return {"sharpe": 0, "sortino": 0, "calmar": 0}

    # Sharpe (annualisé)
    sharpe = float(returns.mean() / returns.std() * np.sqrt(252))

    # Sortino (pénalise seulement les pertes)
    downside = returns[returns < 0]
    downside_std = float(downside.std()) if len(downside) > 1 else float(returns.std())
    sortino = float(returns.mean() / downside_std * np.sqrt(252)) if downside_std > 0 else 0

    # Calmar (rendement / max drawdown)
    cumulative = (1 + returns).cumprod()
    peak = cumulative.expanding().max()
    drawdown = ((cumulative - peak) / peak)
    max_dd = float(drawdown.min())
    total_return = (values[-1] / values[0] - 1) if values[0] > 0 else 0
    calmar = float(total_return / abs(max_dd)) if max_dd != 0 else 0

    return {
        "sharpe": round(sharpe, 3),
        "sortino": round(sortino, 3),
        "calmar": round(calmar, 3),
        "max_drawdown": round(max_dd * 100, 2),
        "total_return": round(total_return * 100, 2),
        "days_tracked": len(values),
    }


# ============================================================
# 7. RAPPORT COMPLET
# ============================================================

def generate_full_report(db: Session, initial_capital: float = 100_000) -> dict:
    """Rapport de performance complet."""
    # Enregistrer l'equity du jour
    record_equity(db, initial_capital)

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "equity_curve": get_equity_curve(),
        "benchmarks": compute_benchmarks(db, initial_capital=initial_capital),
        "trading_stats": compute_trading_stats(db),
        "by_asset_class": compute_performance_by_class(db),
        "by_strategy": compute_performance_by_strategy(db),
        "live_ratios": compute_live_ratios(initial_capital),
    }
