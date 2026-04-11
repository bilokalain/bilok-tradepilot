"""Gestion dynamique post-entrée + TWAP/VWAP

Trailing Stop : ajuste le stop loss à mesure que le prix progresse
Réduction préventive : réduit la position si le contexte se dégrade
TWAP : découpe l'exécution en tranches temporelles égales
VWAP : pondère les tranches par le volume historique
"""

from datetime import datetime
from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class ActivePosition:
    """Position ouverte avec gestion dynamique."""
    symbol: str
    direction: str  # LONG ou SHORT
    entry_price: float
    current_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    trailing_stop: float | None = None
    trailing_pct: float = 0.02  # 2% par défaut
    highest_price: float = 0.0  # Plus haut depuis l'entrée (LONG)
    lowest_price: float = float("inf")  # Plus bas depuis l'entrée (SHORT)
    opened_at: datetime = field(default_factory=datetime.utcnow)
    pnl: float = 0.0
    pnl_pct: float = 0.0

    def update(self, new_price: float) -> dict:
        """Met à jour la position avec un nouveau prix.

        Retourne les actions à prendre :
        - HOLD : ne rien faire
        - STOP_HIT : stop loss atteint
        - TP_HIT : take profit atteint
        - TRAILING_UPDATED : trailing stop ajusté
        - REDUCE : réduction préventive suggérée
        """
        self.current_price = new_price
        action = "HOLD"
        details = {}

        if self.direction == "LONG":
            self.pnl = (new_price - self.entry_price) * self.quantity
            self.pnl_pct = (new_price / self.entry_price - 1) * 100

            # Mise à jour du plus haut
            if new_price > self.highest_price:
                self.highest_price = new_price

            # Trailing stop
            new_trailing = self.highest_price * (1 - self.trailing_pct)
            if self.trailing_stop is None or new_trailing > self.trailing_stop:
                if self.trailing_stop is not None:
                    action = "TRAILING_UPDATED"
                    details["old_trailing"] = self.trailing_stop
                self.trailing_stop = round(new_trailing, 2)
                details["new_trailing"] = self.trailing_stop

            # Vérifier stops
            effective_stop = max(self.stop_loss, self.trailing_stop or 0)
            if new_price <= effective_stop:
                action = "STOP_HIT"
                details["stop_type"] = "trailing" if (self.trailing_stop or 0) > self.stop_loss else "initial"
                details["stop_price"] = effective_stop

            # Vérifier TP
            if new_price >= self.take_profit:
                action = "TP_HIT"

        elif self.direction == "SHORT":
            self.pnl = (self.entry_price - new_price) * self.quantity
            self.pnl_pct = (1 - new_price / self.entry_price) * 100

            if new_price < self.lowest_price:
                self.lowest_price = new_price

            new_trailing = self.lowest_price * (1 + self.trailing_pct)
            if self.trailing_stop is None or new_trailing < self.trailing_stop:
                if self.trailing_stop is not None:
                    action = "TRAILING_UPDATED"
                    details["old_trailing"] = self.trailing_stop
                self.trailing_stop = round(new_trailing, 2)
                details["new_trailing"] = self.trailing_stop

            effective_stop = min(self.stop_loss, self.trailing_stop or float("inf"))
            if new_price >= effective_stop:
                action = "STOP_HIT"
                details["stop_type"] = "trailing" if (self.trailing_stop or float("inf")) < self.stop_loss else "initial"
                details["stop_price"] = effective_stop

            if new_price <= self.take_profit:
                action = "TP_HIT"

        return {
            "action": action,
            "pnl": round(self.pnl, 2),
            "pnl_pct": round(self.pnl_pct, 2),
            "trailing_stop": self.trailing_stop,
            **details,
        }

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "quantity": self.quantity,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "trailing_stop": self.trailing_stop,
            "pnl": round(self.pnl, 2),
            "pnl_pct": round(self.pnl_pct, 2),
            "opened_at": self.opened_at.isoformat(),
        }


def compute_twap_schedule(total_quantity: float, duration_minutes: int,
                           n_slices: int = 5) -> list[dict]:
    """Calcule un plan d'exécution TWAP.

    Découpe la quantité en tranches égales sur la durée.
    """
    qty_per_slice = round(total_quantity / n_slices, 4)
    interval = duration_minutes / n_slices

    schedule = []
    for i in range(n_slices):
        schedule.append({
            "slice": i + 1,
            "quantity": qty_per_slice,
            "delay_minutes": round(interval * i, 1),
            "type": "MARKET",
        })

    return schedule


def compute_vwap_schedule(total_quantity: float, volume_profile: pd.Series,
                           n_slices: int = 5) -> list[dict]:
    """Calcule un plan d'exécution VWAP.

    Pondère les tranches par le profil de volume historique.
    Plus de volume = plus grosse tranche à ce moment.
    """
    if len(volume_profile) < n_slices:
        # Fallback TWAP si pas assez de données
        return compute_twap_schedule(total_quantity, 60, n_slices)

    # Diviser le profil en n_slices segments
    segment_size = len(volume_profile) // n_slices
    weights = []
    for i in range(n_slices):
        start = i * segment_size
        end = start + segment_size
        segment_vol = volume_profile.iloc[start:end].sum()
        weights.append(segment_vol)

    total_weight = sum(weights)
    if total_weight == 0:
        return compute_twap_schedule(total_quantity, 60, n_slices)

    schedule = []
    for i, w in enumerate(weights):
        pct = w / total_weight
        schedule.append({
            "slice": i + 1,
            "quantity": round(total_quantity * pct, 4),
            "weight_pct": round(pct * 100, 1),
            "type": "LIMIT",
        })

    return schedule
