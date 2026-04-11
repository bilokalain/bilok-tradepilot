"""Détection des biais comportementaux

4 biais surveillés :
1. Disposition Effect — couper les gains trop tôt, garder les pertes trop longtemps
2. Revenge Trading — augmenter le risque après une perte pour "se refaire"
3. FOMO — entrer sur un mouvement déjà avancé par peur de rater
4. Over-Trading — trop de trades, frais qui mangent la performance

Chaque biais produit un score 0-100 (0 = pas de biais, 100 = biais critique)
et un niveau d'alerte : OK / WARNING / BLOCK
"""

from datetime import datetime, timedelta


def detect_disposition_effect(trades: list[dict]) -> dict:
    """Détecte le biais de disposition.

    Symptôme : les trades gagnants sont fermés beaucoup plus vite
    que les trades perdants.
    """
    if len(trades) < 5:
        return {"bias": "disposition", "score": 0, "level": "OK", "detail": "Pas assez de trades"}

    winning_durations = []
    losing_durations = []

    for t in trades:
        pnl = t.get("pnl", 0)
        opened = t.get("opened_at")
        closed = t.get("closed_at")
        if opened and closed:
            if isinstance(opened, str):
                opened = datetime.fromisoformat(opened)
            if isinstance(closed, str):
                closed = datetime.fromisoformat(closed)
            duration = (closed - opened).total_seconds() / 3600  # en heures
            if pnl > 0:
                winning_durations.append(duration)
            elif pnl < 0:
                losing_durations.append(duration)

    if not winning_durations or not losing_durations:
        return {"bias": "disposition", "score": 0, "level": "OK", "detail": "Données insuffisantes"}

    avg_win_duration = sum(winning_durations) / len(winning_durations)
    avg_loss_duration = sum(losing_durations) / len(losing_durations)

    if avg_win_duration == 0:
        ratio = 0
    else:
        ratio = avg_loss_duration / avg_win_duration

    # Ratio > 2 = on garde les perdants 2x plus longtemps
    if ratio > 3:
        score = 90
        level = "BLOCK"
    elif ratio > 2:
        score = 70
        level = "WARNING"
    elif ratio > 1.5:
        score = 40
        level = "WARNING"
    else:
        score = 10
        level = "OK"

    return {
        "bias": "disposition",
        "score": score,
        "level": level,
        "detail": f"Ratio durée perdant/gagnant : {ratio:.1f}x",
        "avg_win_hours": round(avg_win_duration, 1),
        "avg_loss_hours": round(avg_loss_duration, 1),
    }


def detect_revenge_trading(trades: list[dict]) -> dict:
    """Détecte le revenge trading.

    Symptôme : après une perte, la taille de la position suivante augmente
    significativement.
    """
    if len(trades) < 3:
        return {"bias": "revenge", "score": 0, "level": "OK", "detail": "Pas assez de trades"}

    revenge_count = 0
    total_sequences = 0

    for i in range(1, len(trades)):
        prev = trades[i - 1]
        curr = trades[i]

        prev_pnl = prev.get("pnl", 0)
        prev_size = prev.get("position_size", 0)
        curr_size = curr.get("position_size", 0)

        if prev_pnl < 0 and prev_size > 0:
            total_sequences += 1
            # Si la position suivante est > 30% plus grosse
            if curr_size > prev_size * 1.3:
                revenge_count += 1

    if total_sequences == 0:
        return {"bias": "revenge", "score": 0, "level": "OK", "detail": "Pas de séquence perte→trade"}

    revenge_rate = revenge_count / total_sequences

    if revenge_rate > 0.5:
        score = 85
        level = "BLOCK"
    elif revenge_rate > 0.3:
        score = 60
        level = "WARNING"
    elif revenge_rate > 0.15:
        score = 35
        level = "WARNING"
    else:
        score = 5
        level = "OK"

    return {
        "bias": "revenge",
        "score": score,
        "level": level,
        "detail": f"Revenge rate : {revenge_rate:.0%} ({revenge_count}/{total_sequences})",
    }


def detect_fomo(entry_price: float, recent_prices: list[float]) -> dict:
    """Détecte le FOMO sur un trade potentiel.

    Symptôme : le prix a déjà beaucoup bougé dans la direction du trade
    avant l'entrée → on arrive tard.
    """
    if len(recent_prices) < 10:
        return {"bias": "fomo", "score": 0, "level": "OK", "detail": "Pas assez de données"}

    # Mouvement des 10 dernières bougies
    start_price = recent_prices[0]
    move_pct = abs(entry_price - start_price) / start_price * 100

    if move_pct > 25:
        score = 85
        level = "BLOCK"
        detail = f"Mouvement de {move_pct:.1f}% déjà réalisé — entrée tardive"
    elif move_pct > 15:
        score = 60
        level = "WARNING"
        detail = f"Mouvement de {move_pct:.1f}% — attention FOMO"
    elif move_pct > 3:
        score = 30
        level = "OK"
        detail = f"Mouvement modéré de {move_pct:.1f}%"
    else:
        score = 0
        level = "OK"
        detail = "Entrée précoce — pas de FOMO"

    return {
        "bias": "fomo",
        "score": score,
        "level": level,
        "detail": detail,
        "move_pct": round(move_pct, 2),
    }


def detect_overtrading(trades: list[dict], lookback_days: int = 7) -> dict:
    """Détecte l'over-trading.

    Symptôme : nombre de trades excessif sur la période récente.
    Seuils basés sur un trading swing/position :
    - > 5 trades/jour = excessif
    - > 3 trades/jour = élevé
    """
    if not trades:
        return {"bias": "overtrading", "score": 0, "level": "OK", "detail": "Aucun trade récent"}

    cutoff = datetime.utcnow() - timedelta(days=lookback_days)
    recent = []
    for t in trades:
        opened = t.get("opened_at")
        if opened:
            if isinstance(opened, str):
                opened = datetime.fromisoformat(opened)
            if opened >= cutoff:
                recent.append(t)

    trades_per_day = len(recent) / lookback_days if lookback_days > 0 else 0

    if trades_per_day > 5:
        score = 80
        level = "BLOCK"
    elif trades_per_day > 3:
        score = 55
        level = "WARNING"
    elif trades_per_day > 1.5:
        score = 25
        level = "OK"
    else:
        score = 0
        level = "OK"

    return {
        "bias": "overtrading",
        "score": score,
        "level": level,
        "detail": f"{trades_per_day:.1f} trades/jour sur {lookback_days}j ({len(recent)} trades)",
        "trades_per_day": round(trades_per_day, 2),
    }


def run_full_bias_check(trades: list[dict], entry_price: float = 0,
                        recent_prices: list[float] | None = None) -> dict:
    """Exécute tous les checks de biais et retourne un résumé.

    Bloque l'exécution si un biais est en BLOCK.
    """
    results = [
        detect_disposition_effect(trades),
        detect_revenge_trading(trades),
        detect_fomo(entry_price, recent_prices or []),
        detect_overtrading(trades),
    ]

    max_score = max(r["score"] for r in results)
    any_block = any(r["level"] == "BLOCK" for r in results)
    any_warning = any(r["level"] == "WARNING" for r in results)

    if any_block:
        overall = "BLOCK"
        message = "Biais comportemental critique détecté — exécution bloquée"
    elif any_warning:
        overall = "WARNING"
        message = "Attention : biais détecté — réduire la taille de position recommandé"
    else:
        overall = "OK"
        message = "Aucun biais significatif détecté"

    return {
        "overall_level": overall,
        "overall_score": max_score,
        "message": message,
        "can_execute": not any_block,
        "biases": results,
    }
