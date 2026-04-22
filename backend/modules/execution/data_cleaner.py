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


def full_clean(db: Session) -> dict:
    """Nettoyage complet : zombies + doublons. Appelé périodiquement."""
    z = clean_zombie_positions(db)
    d = dedupe_alpaca_orders()
    return {
        "zombies_removed": z["zombies_removed"],
        "duplicates_cancelled": d,
        "alpaca_live_count": z["alpaca_count"],
        "ibkr_live_count": z["ibkr_count"],
    }
