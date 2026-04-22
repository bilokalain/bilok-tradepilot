"""Position Manager V2 — Max positions + File d'attente + Remplacement auto

1. Maximum 10 positions simultanées
2. File d'attente des signaux GO en attente
3. Quand une position se ferme → le meilleur signal en attente est exécuté
4. Vérification périodique des SL/TP atteints
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily, Position, Order, PositionStatus, SignalDirection
from backend.database.models import OrderSide as DBOrderSide, OrderStatus as DBOrderStatus

logger = logging.getLogger("tradepilot.position_manager_v2")

MAX_POSITIONS_ALPACA = 30   # Lab — entraîne le modèle (LGN : 20-30 positions pour variance faible)
MAX_POSITIONS_IBKR = 10     # Live — argent réel, plus conservateur
MAX_POSITIONS = MAX_POSITIONS_ALPACA  # Default pour compatibilité
QUEUE_FILE = Path("data/signal_queue.json")
QUEUE_FILE.parent.mkdir(exist_ok=True)


# ============================================================
# FILE D'ATTENTE
# ============================================================

def _load_queue() -> list[dict]:
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text())
        except Exception as e:
            logger.warning(f"[POSITION] Erreur lecture file d'attente: {e}")
            return []
    return []


def _save_queue(queue: list[dict]):
    QUEUE_FILE.write_text(json.dumps(queue, indent=2, default=str))


def add_to_queue(signal: dict):
    """Ajoute un signal GO à la file d'attente avec broker tag."""
    queue = _load_queue()
    # Éviter les doublons
    if any(s.get("symbol") == signal.get("symbol") for s in queue):
        return
    signal["queued_at"] = datetime.utcnow().isoformat()
    # Tag broker — par défaut ALPACA (lab), IBKR piochera dedans
    if "broker" not in signal:
        signal["broker"] = "alpaca"
    queue.append(signal)
    # Trier par score décroissant
    queue.sort(key=lambda x: x.get("score", 0), reverse=True)
    _save_queue(queue)
    logger.info(f"[QUEUE] {signal.get('symbol')} ajouté (score {signal.get('score', 0)}, broker={signal.get('broker')})")


def remove_from_queue(symbol: str):
    """Retire un symbole de la file d'attente."""
    queue = _load_queue()
    queue = [s for s in queue if s.get("symbol") != symbol]
    _save_queue(queue)


def get_queue() -> list[dict]:
    """Retourne la file d'attente triée par score."""
    return _load_queue()


def get_next_in_queue(broker: str = "alpaca") -> dict | None:
    """Retourne le meilleur signal en attente pour un broker donné."""
    queue = _load_queue()
    for s in queue:
        if s.get("broker", "alpaca") == broker or s.get("broker") == "both":
            return s
    return queue[0] if queue else None


def get_ibkr_candidates(db: Session) -> list[dict]:
    """Retourne les positions Alpaca validées qu'IBKR peut copier.

    Critères pour qu'une position Alpaca soit éligible IBKR :
    1. Position OPEN avec un score_v2 >= 65
    2. Pas déjà en position chez IBKR
    3. En profit ou neutre (pas copier une position en perte)
    """
    from backend.modules.execution.broker_alpaca import alpaca_broker

    # Positions Alpaca actuelles
    try:
        alpaca_positions = alpaca_broker.get_positions()
    except Exception:
        alpaca_positions = []

    # Positions IBKR actuelles (via BDD avec tag broker)
    ibkr_symbols = set()
    try:
        from backend.modules.execution.broker_ibkr import IBKRBroker
        ibkr = IBKRBroker()
        if ibkr.is_connected:
            for p in ibkr.get_positions():
                ibkr_symbols.add(p.contract.symbol)
    except Exception:
        pass

    candidates = []
    for p in alpaca_positions:
        sym = p.get("symbol", "")
        qty = float(p.get("qty", 0))
        if qty <= 0:
            continue
        if sym in ibkr_symbols:
            continue  # Déjà chez IBKR

        pnl_pct = float(p.get("unrealized_plpc", 0)) * 100
        entry = float(p.get("avg_entry_price", 0))
        current = float(p.get("current_price", 0))

        # Chercher le score dans le cache signaux
        score = 0
        try:
            import json
            from pathlib import Path
            sig_file = Path("data/signals_cache.json")
            if sig_file.exists():
                sigs = json.loads(sig_file.read_text())
                sigs = sigs if isinstance(sigs, list) else sigs.get("signals", [])
                for s in sigs:
                    if s.get("symbol") == sym:
                        score = s.get("score_v2", s.get("thesis_score", 0))
                        break
        except Exception:
            pass

        candidates.append({
            "symbol": sym,
            "direction": "LONG" if qty > 0 else "SHORT",
            "qty_alpaca": abs(qty),
            "entry_alpaca": entry,
            "current_price": current,
            "pnl_pct": round(pnl_pct, 2),
            "score_v2": score,
            "eligible": pnl_pct >= -2 and score >= 60,  # En profit ou presque + bon score
            "source": "alpaca_validated",
        })

    # Trier : éligibles d'abord, puis par score
    candidates.sort(key=lambda x: (-int(x["eligible"]), -x["score_v2"]))
    return candidates


# ============================================================
# CONTRÔLE DES POSITIONS
# ============================================================

def count_open_positions(db: Session) -> int:
    return db.query(Position).filter_by(status=PositionStatus.OPEN).count()


def can_open_position(db: Session) -> bool:
    return count_open_positions(db) < MAX_POSITIONS


def get_open_symbols(db: Session) -> set[str]:
    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    symbols = set()
    for p in positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if asset:
            symbols.add(asset.symbol)
    return symbols


# ============================================================
# VÉRIFICATION SL/TP + FERMETURE
# ============================================================

def check_and_close_positions(db: Session) -> list[dict]:
    """Vérifie les positions ouvertes et ferme celles qui ont atteint SL/TP.

    Les Bracket Orders Alpaca gèrent ça automatiquement pour les actifs US,
    mais on vérifie aussi en BDD pour les actifs non-Alpaca et pour la sync.
    """
    positions = db.query(Position).filter_by(status=PositionStatus.OPEN).all()
    closed = []

    for p in positions:
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if not asset:
            continue

        last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
        if not last:
            continue

        current_price = float(last.close)
        hit = None

        if p.direction == SignalDirection.LONG:
            if current_price <= float(p.stop_loss):
                hit = "STOP_LOSS"
            elif current_price >= float(p.take_profit):
                hit = "TAKE_PROFIT"
            pnl = (current_price - float(p.entry_price)) * float(p.quantity)
        else:
            if current_price >= float(p.stop_loss):
                hit = "STOP_LOSS"
            elif current_price <= float(p.take_profit):
                hit = "TAKE_PROFIT"
            pnl = (float(p.entry_price) - current_price) * float(p.quantity)

        if hit:
            p.status = PositionStatus.CLOSED
            p.exit_price = current_price
            p.pnl = round(pnl, 2)
            p.pnl_percent = round(pnl / (float(p.entry_price) * float(p.quantity)) * 100, 2)
            p.closed_at = datetime.utcnow()
            db.commit()

            closed.append({
                "symbol": asset.symbol,
                "reason": hit,
                "entry_price": float(p.entry_price),
                "exit_price": current_price,
                "pnl": round(pnl, 2),
                "direction": p.direction.value,
            })

            logger.info(f"[CLOSE] {asset.symbol} fermé ({hit}) — P&L ${pnl:.2f}")

    return closed


# ============================================================
# REMPLACEMENT AUTOMATIQUE
# ============================================================

def process_queue_after_close(db: Session) -> list[dict]:
    """Après une fermeture, exécute le meilleur signal en attente si possible.

    Retourne la liste des trades exécutés depuis la queue.
    """
    executed = []

    while can_open_position(db):
        next_signal = get_next_in_queue()
        if not next_signal:
            break

        symbol = next_signal.get("symbol")
        direction = next_signal.get("direction", "LONG")

        # Vérifier que l'actif n'est pas déjà en position
        open_symbols = get_open_symbols(db)
        if symbol in open_symbols:
            remove_from_queue(symbol)
            continue

        # Exécuter
        asset = db.query(Asset).filter_by(symbol=symbol).first()
        if not asset:
            remove_from_queue(symbol)
            continue

        last = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).first()
        if not last:
            remove_from_queue(symbol)
            continue

        import pandas as pd
        from backend.modules.scanner.indicators import atr
        rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(50).all()
        if len(rows) < 14:
            remove_from_queue(symbol)
            continue

        closes = pd.Series([float(r.close) for r in reversed(rows)])
        highs = pd.Series([float(r.high) for r in reversed(rows)])
        lows = pd.Series([float(r.low) for r in reversed(rows)])
        entry_price = float(last.close)
        atr_val = float(atr(highs, lows, closes, 14).iloc[-1])

        if direction == "LONG":
            sl = round(entry_price - 2 * atr_val, 2)
            tp = round(entry_price + 3 * atr_val, 2)
        else:
            sl = round(entry_price + 2 * atr_val, 2)
            tp = round(entry_price - 3 * atr_val, 2)

        # Sizing 5% du capital restant
        from backend.modules.execution.broker_alpaca import alpaca_broker
        from backend.modules.scanner.live_data import is_alpaca_symbol

        capital = 100_000  # Default
        if alpaca_broker.is_configured:
            try:
                account = alpaca_broker.get_account()
                capital = account.get("equity", 100_000)
            except Exception as e:
                logger.warning(f"[POSITION] Erreur récupération compte Alpaca: {e}")

        from backend.modules.execution.sizing import compute_position_size, quantize
        sizing = compute_position_size(capital=capital, entry_price=entry_price, score=next_signal.get("score", 50))
        quantity = quantize(sizing["quantity"], symbol)

        # Envoyer à Alpaca si possible
        alpaca_result = None
        broker = "local"
        if alpaca_broker.is_configured and is_alpaca_symbol(symbol):
            try:
                from backend.modules.execution.router import _place_bracket_order
                alpaca_result = _place_bracket_order(symbol, "buy" if direction == "LONG" else "sell", float(quantity), sl, tp)
                if alpaca_result and "error" not in alpaca_result:
                    broker = "alpaca_bracket"
            except Exception as e:
                logger.error(f"[POSITION] Erreur placement bracket order {symbol}: {e}")

        # Sauvegarder
        db.add(Order(
            asset_id=asset.id,
            side=DBOrderSide.BUY if direction == "LONG" else DBOrderSide.SELL,
            quantity=float(quantity), price=entry_price, filled_price=entry_price,
            status=DBOrderStatus.FILLED, tranche=1, broker=broker,
        ))
        db.add(Position(
            asset_id=asset.id,
            direction=SignalDirection.LONG if direction == "LONG" else SignalDirection.SHORT,
            entry_price=entry_price, quantity=float(quantity),
            stop_loss=sl, take_profit=tp, status=PositionStatus.OPEN,
        ))
        db.commit()

        remove_from_queue(symbol)

        executed.append({
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "quantity": float(quantity),
            "source": "queue_replacement",
        })

        logger.info(f"[QUEUE→EXEC] {symbol} {direction} exécuté depuis la file d'attente")

    return executed


# ============================================================
# CYCLE COMPLET
# ============================================================

def run_position_cycle(db: Session) -> dict:
    """Cycle complet : vérifier SL/TP → fermer → remplacer depuis la queue."""
    # 1. Vérifier et fermer
    closed = check_and_close_positions(db)

    # 2. Remplacer depuis la queue
    executed = []
    if closed:
        executed = process_queue_after_close(db)

    return {
        "closed": closed,
        "executed_from_queue": executed,
        "open_positions": count_open_positions(db),
        "max_positions": MAX_POSITIONS,
        "queue_size": len(get_queue()),
    }
