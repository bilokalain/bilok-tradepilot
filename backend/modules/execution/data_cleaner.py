"""Data cleaner — garanties d'intégrité pour éviter zombies et doublons.

Garanties :
1. Pas de doublons d'ordres pending sur Alpaca (check avant chaque placement)
2. Pas de zombies en BDD (positions OPEN sans contrepartie live)
3. Auto-clean déclenché après chaque cycle TP/SL (toutes les 5 min)
4. Log structuré des nettoyages pour audit
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger("tradepilot.data_cleaner")


def has_pending_order(symbol: str, side: str = None) -> bool:
    """Vérifie si Alpaca a déjà un ordre pending pour ce symbole.

    Args:
        symbol: Le symbole à vérifier
        side: "buy" ou "sell" pour filtrer, None pour toutes directions

    Returns:
        True si un ordre pending existe déjà (évite les doublons)
    """
    try:
        from backend.modules.execution.broker_alpaca import alpaca_broker
        if not alpaca_broker.is_configured:
            return False
        from alpaca.trading.client import TradingClient
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus
        from backend.config.settings import settings

        client = TradingClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY, paper=True)
        orders = client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN, symbols=[symbol], limit=50))
        if not orders:
            return False
        if side is None:
            return len(orders) > 0
        return any(str(o.side).lower().endswith(side.lower()) for o in orders)
    except Exception as e:
        logger.warning(f"[CLEANER] has_pending_order({symbol}) échoué: {e}")
        return False


def _get_alpaca_live_and_pending() -> set:
    """Récupère symboles Alpaca live (positions filled) + pending (ordres ACCEPTED/NEW).

    Les pending sont en attente d'exécution (marché fermé) — ce sont des positions futures,
    pas des zombies.
    """
    syms = set()
    try:
        from backend.modules.execution.broker_alpaca import alpaca_broker
        if not alpaca_broker.is_configured:
            return syms
        # Positions live
        try:
            syms.update({p["symbol"] for p in alpaca_broker.get_positions()})
        except Exception as e:
            logger.warning(f"[CLEANER] Alpaca positions: {e}")
        # Ordres pending
        try:
            from alpaca.trading.client import TradingClient
            from alpaca.trading.requests import GetOrdersRequest
            from alpaca.trading.enums import QueryOrderStatus
            from backend.config.settings import settings
            client = TradingClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY, paper=True)
            orders = client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN, limit=200))
            syms.update({o.symbol for o in orders})
        except Exception as e:
            logger.warning(f"[CLEANER] Alpaca orders: {e}")
    except Exception as e:
        logger.warning(f"[CLEANER] Alpaca total: {e}")
    return syms


def clean_zombie_positions(db: Session) -> dict:
    """Ferme les positions OPEN en BDD qui n'ont plus de contrepartie live (Alpaca ou IBKR).

    Une position est un zombie si elle est OPEN en BDD mais n'existe :
    - NI en position live Alpaca
    - NI en ordre pending Alpaca (ACCEPTED/NEW)
    - NI en position IBKR

    Returns:
        dict avec 'closed' (liste des symboles fermés), 'alpaca_count', 'ibkr_count'
    """
    from backend.database.models import Asset, Position, PositionStatus

    # 1. Symboles Alpaca (live + pending)
    alpaca_syms = _get_alpaca_live_and_pending()

    # 2. Symboles live IBKR
    ibkr_syms = set()
    try:
        from backend.config.settings import settings
        if settings.IBKR_ACCOUNT_ID:
            from ib_insync import IB
            ib = IB()
            try:
                ib.connect(settings.IBKR_HOST, settings.IBKR_PORT, clientId=88, timeout=5)
                ibkr_syms = {p.contract.symbol for p in ib.positions(settings.IBKR_ACCOUNT_ID) if p.position != 0}
                ib.disconnect()
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"[CLEANER] IBKR skip: {e}")

    # 3. Identifier et fermer les zombies
    zombies = []
    for p in db.query(Position).filter_by(status=PositionStatus.OPEN).all():
        asset = db.query(Asset).filter_by(id=p.asset_id).first()
        if not asset:
            continue
        if asset.symbol not in alpaca_syms and asset.symbol not in ibkr_syms:
            zombies.append((p, asset.symbol))

    closed_symbols = []
    for pos, sym in zombies:
        pos.status = PositionStatus.CLOSED
        pos.closed_at = datetime.utcnow()
        closed_symbols.append(sym)

    if zombies:
        db.commit()
        logger.info(f"[CLEANER] {len(zombies)} zombies fermés: {closed_symbols}")

    return {
        "closed": closed_symbols,
        "alpaca_count": len(alpaca_syms),
        "ibkr_count": len(ibkr_syms),
        "zombies_removed": len(zombies),
    }


def dedupe_alpaca_orders() -> int:
    """Annule les ordres pending Alpaca en doublon (même symbol/side/qty).
    Garde le plus ancien. Returns nb d'ordres annulés.

    IMPORTANT : les ordres enfants de brackets (SL/TP protecteurs) sont IGNORÉS —
    ne jamais les considérer comme doublons car ils protègent les positions.
    """
    try:
        from alpaca.trading.client import TradingClient
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus
        from backend.config.settings import settings
        from collections import defaultdict

        client = TradingClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY, paper=True)
        orders = client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN, limit=200))

        groups = defaultdict(list)
        for o in orders:
            # EXCLURE les ordres qui font partie d'un bracket (SL/TP protecteurs)
            # Ces ordres ont un legs parent ou order_class = BRACKET/OCO
            oc = str(o.order_class).upper() if o.order_class else ""
            if "BRACKET" in oc or "OCO" in oc or "OTO" in oc:
                continue
            # Exclure aussi les ordres STOP/LIMIT typiques de protection
            ot = str(o.order_type).upper() if o.order_type else ""
            if "STOP" in ot or ot == "LIMIT":
                # Ce sont presque toujours des SL/TP protecteurs — ne pas dédupliquer
                continue
            groups[(o.symbol, str(o.side), float(o.qty))].append(o)

        cancelled = 0
        for key, group in groups.items():
            if len(group) > 1:
                group.sort(key=lambda o: o.created_at)
                for o in group[1:]:
                    try:
                        client.cancel_order_by_id(o.id)
                        cancelled += 1
                    except Exception as e:
                        logger.warning(f"[CLEANER] Cancel order {o.id} échoué: {e}")

        if cancelled:
            logger.info(f"[CLEANER] {cancelled} ordres doublons annulés sur Alpaca")
        return cancelled
    except Exception as e:
        logger.warning(f"[CLEANER] dedupe_alpaca_orders échoué: {e}")
        return 0


def restore_missing_brackets() -> int:
    """Détecte les positions Alpaca qui n'ont AUCUN SL/TP pending et ajoute une
    protection OCO automatique (SL -8% / TP +12%).

    Essentiel après un nettoyage accidentel ou un bracket expiré.
    Returns: nb de positions re-protégées.
    """
    try:
        from alpaca.trading.client import TradingClient
        from alpaca.trading.requests import (
            LimitOrderRequest, GetOrdersRequest, TakeProfitRequest, StopLossRequest,
        )
        from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass, QueryOrderStatus
        from backend.config.settings import settings
        from backend.modules.execution.broker_alpaca import alpaca_broker

        if not alpaca_broker.is_configured:
            return 0

        client = TradingClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY, paper=True)

        # 1. Positions live
        positions = alpaca_broker.get_positions()
        if not positions:
            return 0

        # 2. Symboles avec ordres SL/TP actifs
        orders = client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN, limit=300))
        protected_syms = set()
        for o in orders:
            ot = str(o.order_type).upper() if o.order_type else ""
            if "STOP" in ot or ot == "LIMIT":
                protected_syms.add(o.symbol)

        # 3. Pour chaque position non protégée, ajouter un OCO
        restored = 0
        for pos in positions:
            sym = pos["symbol"]
            if sym in protected_syms:
                continue  # déjà protégé

            side = pos.get("side", "long").lower()
            qty = abs(float(pos["quantity"]))
            entry = float(pos["entry_price"])
            current = float(pos.get("current_price", entry))

            # SL/TP : 8%/12% basés sur entry
            if side == "long":
                sl = round(entry * 0.92, 2)
                tp = round(entry * 1.12, 2)
                exit_side = OrderSide.SELL
                # SL must be < current pour SELL stop
                if sl >= current: sl = round(current * 0.95, 2)
            else:
                sl = round(entry * 1.08, 2)
                tp = round(entry * 0.88, 2)
                exit_side = OrderSide.BUY
                if sl <= current: sl = round(current * 1.05, 2)

            try:
                oco = LimitOrderRequest(
                    symbol=sym, qty=qty, side=exit_side,
                    time_in_force=TimeInForce.GTC,
                    limit_price=tp,
                    order_class=OrderClass.OCO,
                    take_profit=TakeProfitRequest(limit_price=tp),
                    stop_loss=StopLossRequest(stop_price=sl),
                )
                client.submit_order(oco)
                restored += 1
                logger.info(f"[CLEANER] Bracket restauré: {sym} {side} SL=${sl} TP=${tp}")
            except Exception as e:
                logger.debug(f"[CLEANER] Impossible de restaurer bracket {sym}: {str(e)[:100]}")

        if restored:
            logger.info(f"[CLEANER] {restored} brackets restaurés sur positions orphelines")
        return restored
    except Exception as e:
        logger.warning(f"[CLEANER] restore_missing_brackets échoué: {e}")
        return 0


def full_clean(db: Session) -> dict:
    """Nettoyage complet : zombies + doublons + restauration brackets.
    Appelé périodiquement toutes les 5 min via TP/SL monitor.
    """
    z = clean_zombie_positions(db)
    d = dedupe_alpaca_orders()
    b = restore_missing_brackets()
    return {
        "zombies_removed": z["zombies_removed"],
        "duplicates_cancelled": d,
        "brackets_restored": b,
        "alpaca_live_count": z["alpaca_count"],
        "ibkr_live_count": z["ibkr_count"],
    }
