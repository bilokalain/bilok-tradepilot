"""Portfolio V2 — Gestion de risque professionnelle

1. Rebalancing automatique — rééquilibre vers les poids Risk Parity
2. Max Drawdown Control — réduit les positions quand le DD dépasse un seuil
3. Risk Budget — limite de perte globale (ex: max 15% du capital)
4. VaR (Value at Risk) — perte max attendue à 95% de confiance
5. Allocation par régime global — ajuste selon RISK-ON/OFF
6. Exposition sectorielle + devise
7. Beta portefeuille
8. Corrélation live
"""

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily, Position, PositionStatus, SignalDirection


# ============================================================
# 1. REBALANCING
# ============================================================

def compute_rebalancing(db: Session, target_weights: dict | None = None) -> dict:
    """Calcule les ajustements nécessaires pour rééquilibrer le portefeuille.

    Si target_weights = None, utilise Risk Parity.
    Retourne les ordres de rebalancing (acheter/vendre pour chaque actif).
    """
    positions = _load_positions(db)
    if len(positions) < 2:
        return {"needs_rebalancing": False, "reason": "Moins de 2 positions"}

    total_value = sum(p["market_value"] for p in positions)
    if total_value == 0:
        return {"needs_rebalancing": False, "reason": "Valeur totale = 0"}

    # Poids actuels
    current_weights = {p["symbol"]: p["market_value"] / total_value for p in positions}

    # Poids cibles (Risk Parity ou custom)
    if target_weights is None:
        target_weights = _compute_equal_risk_weights(db, positions)

    # Écarts
    adjustments = []
    max_drift = 0
    for p in positions:
        sym = p["symbol"]
        current = current_weights.get(sym, 0)
        target = target_weights.get(sym, 1 / len(positions))
        drift = current - target
        max_drift = max(max_drift, abs(drift))

        if abs(drift) > 0.03:  # Seuil de 3% pour déclencher un rebalancing
            target_value = total_value * target
            current_value = p["market_value"]
            diff_value = target_value - current_value
            diff_qty = diff_value / p["current_price"] if p["current_price"] > 0 else 0

            adjustments.append({
                "symbol": sym,
                "action": "BUY" if diff_value > 0 else "SELL",
                "current_weight": round(current * 100, 1),
                "target_weight": round(target * 100, 1),
                "drift": round(drift * 100, 1),
                "adjustment_usd": round(diff_value, 2),
                "adjustment_qty": round(diff_qty, 4),
            })

    needs_rebalancing = max_drift > 0.05  # Rebalance si drift > 5%

    return {
        "needs_rebalancing": needs_rebalancing,
        "max_drift": round(max_drift * 100, 1),
        "total_value": round(total_value, 2),
        "current_weights": {k: round(v * 100, 1) for k, v in current_weights.items()},
        "target_weights": {k: round(v * 100, 1) for k, v in target_weights.items()},
        "adjustments": adjustments,
    }


def _compute_equal_risk_weights(db: Session, positions: list[dict]) -> dict:
    """Poids Risk Parity simples : inversement proportionnel à la volatilité."""
    vols = {}
    for p in positions:
        asset = db.query(Asset).filter_by(symbol=p["symbol"]).first()
        if not asset:
            continue
        rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(60).all()
        if len(rows) < 20:
            vols[p["symbol"]] = 0.3  # Default 30% vol
            continue
        closes = pd.Series([float(r.close) for r in reversed(rows)])
        vol = float(closes.pct_change().std() * np.sqrt(252))
        vols[p["symbol"]] = max(vol, 0.01)

    # Poids = 1/vol normalisé
    inv_vols = {s: 1 / v for s, v in vols.items()}
    total_inv = sum(inv_vols.values())
    return {s: iv / total_inv for s, iv in inv_vols.items()} if total_inv > 0 else {s: 1 / len(vols) for s in vols}


# ============================================================
# 2. MAX DRAWDOWN CONTROL
# ============================================================

def check_drawdown_control(db: Session, max_dd_threshold: float = -15.0,
                            initial_capital: float = 100_000) -> dict:
    """Vérifie si le drawdown depuis le pic dépasse le seuil et recommande des actions.

    Le drawdown est calculé par rapport au pic d'equity (high-water mark),
    PAS par rapport au capital initial.

    Niveaux :
    - DD > -5% : NORMAL
    - DD > -10% : WARNING → réduire les positions de 30%
    - DD > -15% : ALERT → réduire de 60%
    - DD > -20% : CRITICAL → fermer toutes les positions
    """
    positions = _load_positions(db)
    total_value = sum(p["market_value"] for p in positions)
    total_pnl = sum(p["pnl"] for p in positions)

    equity = initial_capital + total_pnl

    # Peak equity = high-water mark depuis l'historique des positions clôturées
    peak_equity = _compute_peak_equity(db, initial_capital)
    # Le pic ne peut pas être inférieur à l'equity actuelle si on vient de le dépasser
    peak_equity = max(peak_equity, equity)

    dd_pct = (equity - peak_equity) / peak_equity * 100 if peak_equity > 0 else 0

    if dd_pct > -5:
        level = "NORMAL"
        action = "HOLD"
        reduction = 0
        message = "Drawdown acceptable — pas d'action nécessaire"
    elif dd_pct > -10:
        level = "WARNING"
        action = "REDUCE_30"
        reduction = 0.3
        message = f"Drawdown {dd_pct:.1f}% — réduire les positions de 30%"
    elif dd_pct > -15:
        level = "ALERT"
        action = "REDUCE_60"
        reduction = 0.6
        message = f"Drawdown {dd_pct:.1f}% — réduire les positions de 60%"
    else:
        level = "CRITICAL"
        action = "CLOSE_ALL"
        reduction = 1.0
        message = f"Drawdown {dd_pct:.1f}% — FERMER TOUTES LES POSITIONS"

    return {
        "equity": round(equity, 2),
        "peak_equity": round(peak_equity, 2),
        "drawdown_pct": round(dd_pct, 2),
        "level": level,
        "action": action,
        "reduction_pct": round(reduction * 100),
        "message": message,
        "positions_to_reduce": [
            {"symbol": p["symbol"], "current_qty": p["quantity"],
             "reduce_qty": round(p["quantity"] * reduction, 4)}
            for p in positions
        ] if reduction > 0 else [],
    }


# ============================================================
# 3. RISK BUDGET
# ============================================================

def compute_risk_budget(db: Session, max_loss_pct: float = 15.0,
                        initial_capital: float = 100_000) -> dict:
    """Calcule le budget de risque restant.

    max_loss_pct = perte maximale acceptable (% du capital initial).
    Le budget diminue à mesure que les pertes s'accumulent.
    """
    positions = _load_positions(db)
    total_pnl = sum(p["pnl"] for p in positions)

    max_loss_usd = initial_capital * max_loss_pct / 100
    risk_used = abs(min(0, total_pnl))  # Pertes réalisées
    risk_remaining = max(0, max_loss_usd - risk_used)

    # Risque par position ouverte (distance au SL)
    risk_in_positions = 0
    for p in positions:
        if p["direction"] == "LONG":
            risk_per = (p["entry_price"] - p["stop_loss"]) * p["quantity"]
        else:
            risk_per = (p["stop_loss"] - p["entry_price"]) * p["quantity"]
        risk_in_positions += max(0, risk_per)

    budget_pct = (risk_remaining / max_loss_usd * 100) if max_loss_usd > 0 else 100
    can_take_new_trades = risk_remaining > risk_in_positions * 0.1

    return {
        "max_loss_usd": round(max_loss_usd, 2),
        "risk_used_usd": round(risk_used, 2),
        "risk_in_positions_usd": round(risk_in_positions, 2),
        "risk_remaining_usd": round(risk_remaining, 2),
        "budget_remaining_pct": round(budget_pct, 1),
        "can_take_new_trades": can_take_new_trades,
        "status": "OK" if budget_pct > 50 else "WARNING" if budget_pct > 20 else "CRITICAL",
    }


# ============================================================
# 4. VALUE AT RISK (VaR)
# ============================================================

def compute_var(db: Session, confidence: float = 0.95,
                horizon_days: int = 1) -> dict:
    """Value at Risk — perte max attendue à N% de confiance.

    Méthode : VaR historique (simulation basée sur les rendements passés).
    """
    positions = _load_positions(db)
    if not positions:
        return {"var_1d": 0, "var_pct": 0, "method": "historical", "confidence": confidence}

    total_value = sum(p["market_value"] for p in positions)

    # Collecter les rendements historiques de chaque position
    portfolio_returns = []
    for p in positions:
        asset = db.query(Asset).filter_by(symbol=p["symbol"]).first()
        if not asset:
            continue
        rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(252).all()
        if len(rows) < 60:
            continue

        closes = pd.Series([float(r.close) for r in reversed(rows)])
        returns = closes.pct_change().dropna()

        weight = p["market_value"] / total_value if total_value > 0 else 0
        if not portfolio_returns:
            portfolio_returns = (returns * weight).tolist()
        else:
            min_len = min(len(portfolio_returns), len(returns))
            for i in range(min_len):
                portfolio_returns[i] += float(returns.iloc[i]) * weight

    if not portfolio_returns:
        return {"var_1d": 0, "var_pct": 0, "method": "historical", "confidence": confidence}

    port_ret = np.array(portfolio_returns)

    # VaR = percentile des pertes
    var_pct = float(np.percentile(port_ret, (1 - confidence) * 100))
    # NOTE: sqrt(horizon) scaling = approximation paramétrique VaR (hypothèse gaussienne,
    # rendements i.i.d.). Sous-estime le risque en queues épaisses / autocorrélation.
    var_usd = var_pct * total_value * np.sqrt(horizon_days)

    # Expected Shortfall (CVaR) = moyenne des pertes au-delà du VaR
    losses_beyond = port_ret[port_ret <= var_pct]
    cvar_pct = float(np.mean(losses_beyond)) if len(losses_beyond) > 0 else var_pct
    # Même approximation paramétrique sqrt(horizon) — voir note ci-dessus
    cvar_usd = cvar_pct * total_value * np.sqrt(horizon_days)

    return {
        "var_1d_usd": round(abs(var_usd), 2),
        "var_1d_pct": round(abs(var_pct) * 100, 2),
        "cvar_1d_usd": round(abs(cvar_usd), 2),
        "cvar_1d_pct": round(abs(cvar_pct) * 100, 2),
        "confidence": confidence,
        "horizon_days": horizon_days,
        "total_portfolio_value": round(total_value, 2),
        "method": "historical",
        "interpretation": f"Il y a {(1-confidence)*100:.0f}% de chance de perdre plus de ${abs(var_usd):.0f} en {horizon_days} jour(s)",
    }


# ============================================================
# 5. ALLOCATION PAR RÉGIME GLOBAL
# ============================================================

def compute_regime_allocation(regime_global: dict,
                               current_allocation: dict) -> dict:
    """Ajuste l'allocation cible selon le régime global.

    RISK-ON → surpondérer actions/crypto, sous-pondérer obligations/or
    RISK-OFF → inverse
    """
    regime = regime_global.get("regime", "NEUTRAL")
    modifiers = regime_global.get("asset_class_modifiers", {})

    adjusted = {}
    for asset_class, current_pct in current_allocation.items():
        modifier = modifiers.get(asset_class, 1.0)
        adjusted[asset_class] = round(current_pct * modifier, 1)

    # Normaliser
    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: round(v / total * 100, 1) for k, v in adjusted.items()}

    return {
        "regime": regime,
        "original_allocation": current_allocation,
        "adjusted_allocation": adjusted,
        "modifiers_applied": modifiers,
    }


# ============================================================
# 6. EXPOSITION SECTORIELLE + DEVISE
# ============================================================

def compute_exposure(db: Session) -> dict:
    """Calcule l'exposition par secteur, classe d'actif et devise."""
    positions = _load_positions(db)
    total_value = sum(p["market_value"] for p in positions)

    if total_value == 0:
        return {"by_sector": {}, "by_class": {}, "by_currency": {}, "concentration_risk": "N/A"}

    by_class = {}
    by_currency = {}
    by_sector = {}

    from backend.modules.analyser.sector_rotation import ASSET_SECTOR_MAP

    for p in positions:
        # Par classe d'actif
        ac = p.get("asset_class", "UNKNOWN")
        by_class[ac] = by_class.get(ac, 0) + p["market_value"]

        # Par secteur
        sector = ASSET_SECTOR_MAP.get(p["symbol"], "Other")
        by_sector[sector] = by_sector.get(sector, 0) + p["market_value"]

        # Par devise
        sym = p["symbol"]
        if any(s in sym for s in [".PA", ".DE", ".AS", ".MI"]):
            currency = "EUR"
        elif any(s in sym for s in [".L"]):
            currency = "GBP"
        elif any(s in sym for s in [".SW"]):
            currency = "CHF"
        elif any(s in sym for s in [".CO"]):
            currency = "DKK"
        elif "-USD" in sym or "=X" in sym:
            currency = "USD"
        else:
            currency = "USD"
        by_currency[currency] = by_currency.get(currency, 0) + p["market_value"]

    # Normaliser en %
    by_class_pct = {k: round(v / total_value * 100, 1) for k, v in by_class.items()}
    by_sector_pct = {k: round(v / total_value * 100, 1) for k, v in by_sector.items()}
    by_currency_pct = {k: round(v / total_value * 100, 1) for k, v in by_currency.items()}

    # Risque de concentration
    max_sector_pct = max(by_sector_pct.values()) if by_sector_pct else 0
    if max_sector_pct > 50:
        concentration = "CRITICAL"
    elif max_sector_pct > 35:
        concentration = "HIGH"
    elif max_sector_pct > 25:
        concentration = "MODERATE"
    else:
        concentration = "LOW"

    return {
        "by_class": by_class_pct,
        "by_sector": dict(sorted(by_sector_pct.items(), key=lambda x: -x[1])),
        "by_currency": by_currency_pct,
        "concentration_risk": concentration,
        "max_sector_exposure": f"{max_sector_pct:.0f}%",
    }


# ============================================================
# 7. BETA PORTEFEUILLE
# ============================================================

def compute_portfolio_beta(db: Session) -> dict:
    """Beta du portefeuille vs SPY.

    Beta = 1.0 → suit le marché
    Beta > 1.0 → plus volatile que le marché
    Beta < 1.0 → moins volatile
    Beta < 0 → inverse du marché (hedge)
    """
    positions = _load_positions(db)
    if not positions:
        return {"beta": 0, "interpretation": "Pas de positions"}

    # Rendements SPY
    spy = db.query(Asset).filter_by(symbol="SPY").first()
    if not spy:
        return {"beta": 1.0, "interpretation": "SPY non trouvé — beta estimé à 1.0"}

    spy_rows = db.query(OHLCVDaily).filter_by(asset_id=spy.id).order_by(OHLCVDaily.date.desc()).limit(120).all()
    if len(spy_rows) < 60:
        return {"beta": 1.0, "interpretation": "Données SPY insuffisantes"}

    spy_returns = pd.Series([float(r.close) for r in reversed(spy_rows)]).pct_change().dropna()
    total_value = sum(p["market_value"] for p in positions)

    weighted_beta = 0
    for p in positions:
        asset = db.query(Asset).filter_by(symbol=p["symbol"]).first()
        if not asset:
            continue
        rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(120).all()
        if len(rows) < 60:
            continue

        asset_returns = pd.Series([float(r.close) for r in reversed(rows)]).pct_change().dropna()
        min_len = min(len(asset_returns), len(spy_returns))

        if min_len < 30:
            continue

        cov = np.cov(asset_returns.iloc[:min_len], spy_returns.iloc[:min_len])
        if cov[1][1] > 0:
            beta = cov[0][1] / cov[1][1]
        else:
            beta = 1.0

        weight = p["market_value"] / total_value if total_value > 0 else 0
        weighted_beta += beta * weight

    if weighted_beta > 1.3:
        interpretation = "Portefeuille agressif — plus volatile que le marché"
    elif weighted_beta > 0.8:
        interpretation = "Portefeuille normal — suit le marché"
    elif weighted_beta > 0.5:
        interpretation = "Portefeuille défensif — moins volatile"
    elif weighted_beta > 0:
        interpretation = "Portefeuille très défensif"
    else:
        interpretation = "Portefeuille inversé — hedge contre le marché"

    return {
        "beta": round(weighted_beta, 3),
        "interpretation": interpretation,
    }


# ============================================================
# HELPER
# ============================================================

def _compute_peak_equity(db: Session, initial_capital: float) -> float:
    """Calcule le pic d'equity (high-water mark) à partir de l'historique des positions clôturées.

    Parcourt les positions fermées chronologiquement et reconstitue la courbe d'equity
    pour trouver le point le plus haut atteint.
    """
    closed = (
        db.query(Position)
        .filter_by(status=PositionStatus.CLOSED)
        .order_by(Position.closed_at.asc())
        .all()
    )

    if not closed:
        return initial_capital

    # Reconstituer l'equity cumulée après chaque trade clôturé
    equity = initial_capital
    peak = initial_capital
    for p in closed:
        if p.pnl is not None:
            equity += float(p.pnl)
        peak = max(peak, equity)

    return peak


def _load_positions(db: Session) -> list[dict]:
    """Charge les positions ouvertes avec données de marché."""
    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    result = []
    for p in positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if not asset:
            continue
        last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
        current_price = float(last.close) if last else float(p.entry_price)
        market_value = current_price * float(p.quantity)
        pnl = (current_price - float(p.entry_price)) * float(p.quantity) if p.direction == SignalDirection.LONG else (float(p.entry_price) - current_price) * float(p.quantity)

        result.append({
            "symbol": asset.symbol,
            "asset_class": asset.asset_class.value,
            "direction": p.direction.value,
            "entry_price": float(p.entry_price),
            "current_price": current_price,
            "quantity": float(p.quantity),
            "market_value": round(market_value, 2),
            "stop_loss": float(p.stop_loss),
            "take_profit": float(p.take_profit),
            "pnl": round(pnl, 2),
        })
    return result
