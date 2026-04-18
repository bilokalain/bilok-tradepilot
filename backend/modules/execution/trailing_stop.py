"""Trailing Stop — Le SL remonte avec le prix pour protéger les gains

Logique :
- LONG : si le prix fait un nouveau plus haut, le SL monte à (plus_haut - 2×ATR)
- SHORT : si le prix fait un nouveau plus bas, le SL descend à (plus_bas + 2×ATR)
- Le SL ne redescend JAMAIS (LONG) / ne remonte JAMAIS (SHORT)

Exécuté toutes les 5 minutes avec le TP/SL monitor.
"""

import logging
from sqlalchemy.orm import Session
import pandas as pd

from backend.database.models import Asset, Position, PositionStatus, OHLCVDaily, SignalDirection

logger = logging.getLogger("tradepilot.trailing_stop")


def update_trailing_stops(db: Session) -> dict:
    """Met à jour les trailing stops pour toutes les positions ouvertes."""
    from backend.modules.execution.broker_alpaca import alpaca_broker

    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    if not positions:
        return {"updated": 0, "positions": []}

    # Prix live Alpaca
    alpaca_prices = {}
    if alpaca_broker.is_configured:
        try:
            for p in alpaca_broker.get_positions():
                alpaca_prices[p["symbol"]] = float(p["current_price"])
        except Exception as e:
            logger.warning(f"[TRAILING] Impossible de récupérer les prix Alpaca: {e}")

    updated = []

    for pos in positions:
        asset = db.query(Asset).filter_by(id=pos.asset_id).first()
        if not asset:
            continue

        current_price = alpaca_prices.get(asset.symbol)
        if not current_price:
            continue

        entry = float(pos.entry_price)
        old_sl = float(pos.stop_loss) if pos.stop_loss else None
        if not old_sl:
            continue

        # Calculer l'ATR actuel
        rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(20).all()
        if len(rows) < 14:
            continue

        highs = pd.Series([float(r.high) for r in reversed(rows)])
        lows = pd.Series([float(r.low) for r in reversed(rows)])
        closes = pd.Series([float(r.close) for r in reversed(rows)])

        # ATR 14 périodes
        tr = pd.concat([
            highs - lows,
            (highs - closes.shift(1)).abs(),
            (lows - closes.shift(1)).abs(),
        ], axis=1).max(axis=1)
        atr_val = float(tr.iloc[-14:].mean())

        direction = pos.direction.value
        new_sl = old_sl

        if direction == "LONG":
            # Le SL trail à 2×ATR sous le prix actuel
            trailing_sl = round(current_price - 2 * atr_val, 2)
            # Ne monter le SL que s'il est au-dessus de l'ancien ET au-dessus de l'entry
            if trailing_sl > old_sl and current_price > entry:
                new_sl = trailing_sl
        else:  # SHORT
            trailing_sl = round(current_price + 2 * atr_val, 2)
            if trailing_sl < old_sl and current_price < entry:
                new_sl = trailing_sl

        if new_sl != old_sl:
            pos.stop_loss = new_sl
            pnl_protected = abs(new_sl - entry) / entry * 100
            updated.append({
                "symbol": asset.symbol,
                "direction": direction,
                "old_sl": old_sl,
                "new_sl": new_sl,
                "current_price": current_price,
                "entry": entry,
                "pnl_protected": round(pnl_protected, 2),
            })
            logger.info(f"[TRAILING] {asset.symbol} SL: ${old_sl:.2f} → ${new_sl:.2f} (protège {pnl_protected:.1f}%)")

    if updated:
        db.commit()

    return {"updated": len(updated), "positions": updated}
