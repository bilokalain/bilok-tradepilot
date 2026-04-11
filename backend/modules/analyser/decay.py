"""Strategy Decay — détection et quarantaine des stratégies qui perdent leur edge

Méthode : suivi du taux de réussite sur fenêtre glissante.
Si le taux passe sous un seuil, la stratégie est mise en quarantaine.

Métriques surveillées :
- Win rate (taux de trades gagnants)
- Profit factor (gains bruts / pertes brutes)
- Sharpe ratio de la stratégie
- Consistency (écart-type des rendements par trade)
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StrategyPerformance:
    """Performance historique d'une stratégie."""
    strategy_name: str
    total_trades: int = 0
    winning_trades: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    returns: list[float] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.winning_trades / self.total_trades

    @property
    def profit_factor(self) -> float:
        if self.total_loss == 0:
            return float("inf") if self.total_profit > 0 else 0.0
        return abs(self.total_profit / self.total_loss)

    @property
    def avg_return(self) -> float:
        if not self.returns:
            return 0.0
        return sum(self.returns) / len(self.returns)

    @property
    def consistency(self) -> float:
        """Plus c'est bas, plus la stratégie est consistante."""
        if len(self.returns) < 2:
            return 0.0
        mean = self.avg_return
        variance = sum((r - mean) ** 2 for r in self.returns) / len(self.returns)
        return variance ** 0.5


# Seuils de quarantaine
DECAY_THRESHOLDS = {
    "win_rate_min": 0.35,       # sous 35% de win rate
    "profit_factor_min": 0.8,   # sous 0.8 de profit factor
    "min_trades": 20,           # minimum de trades avant évaluation
    "consistency_max": 0.15,    # écart-type max acceptable
}


def check_strategy_decay(perf: StrategyPerformance) -> dict:
    """Vérifie si une stratégie montre des signes de decay.

    Retourne :
    - is_decaying: bool
    - reasons: liste des raisons
    - health_score: 0-100 (santé de la stratégie)
    """
    if perf.total_trades < DECAY_THRESHOLDS["min_trades"]:
        return {
            "strategy": perf.strategy_name,
            "is_decaying": False,
            "reasons": [],
            "health_score": 50.0,
            "status": "INSUFFICIENT_DATA",
            "message": f"Seulement {perf.total_trades} trades — minimum {DECAY_THRESHOLDS['min_trades']} requis",
        }

    reasons = []
    health_score = 100.0

    # Win rate
    if perf.win_rate < DECAY_THRESHOLDS["win_rate_min"]:
        reasons.append(f"Win rate bas : {perf.win_rate:.1%} (seuil : {DECAY_THRESHOLDS['win_rate_min']:.0%})")
        health_score -= 30

    # Profit factor
    if perf.profit_factor < DECAY_THRESHOLDS["profit_factor_min"]:
        reasons.append(f"Profit factor bas : {perf.profit_factor:.2f} (seuil : {DECAY_THRESHOLDS['profit_factor_min']})")
        health_score -= 30

    # Consistency
    if perf.consistency > DECAY_THRESHOLDS["consistency_max"]:
        reasons.append(f"Inconsistance élevée : {perf.consistency:.3f} (seuil : {DECAY_THRESHOLDS['consistency_max']})")
        health_score -= 20

    # Tendance récente (derniers 10 trades vs historique)
    if len(perf.returns) >= 20:
        recent = perf.returns[-10:]
        historical = perf.returns[:-10]
        recent_avg = sum(recent) / len(recent)
        hist_avg = sum(historical) / len(historical)
        if recent_avg < hist_avg * 0.5:
            reasons.append(f"Dégradation récente : rendement moyen en baisse de {((hist_avg - recent_avg) / abs(hist_avg) * 100):.0f}%")
            health_score -= 20

    is_decaying = health_score < 50
    status = "QUARANTINE" if is_decaying else "ACTIVE" if health_score >= 70 else "WARNING"

    return {
        "strategy": perf.strategy_name,
        "is_decaying": is_decaying,
        "reasons": reasons,
        "health_score": max(0, round(health_score, 1)),
        "status": status,
        "metrics": {
            "win_rate": round(perf.win_rate, 3),
            "profit_factor": round(perf.profit_factor, 2),
            "avg_return": round(perf.avg_return, 4),
            "consistency": round(perf.consistency, 4),
            "total_trades": perf.total_trades,
        },
    }
