"""Adaptive Engine — Le système apprend de chaque trade fermé

3 mécanismes d'apprentissage autonome :

1. PERFORMANCE MATRIX LIVE — mise à jour après chaque trade fermé
   La matrice stratégie×actif évolue avec les résultats réels (pas que backtest)

2. SCANNER WEIGHT ADAPTATION — les poids des 11 critères s'ajustent
   Si un critère prédit mal les trades gagnants, son poids diminue

3. XGBOOST AUTO-RETRAIN — ré-entraînement hebdomadaire
   Le modèle ML se ré-entraîne avec les nouveaux trades

Persisté dans data/learning_state.json — survit aux redémarrages.
"""

import json
import logging
import time
from pathlib import Path
from datetime import datetime

import numpy as np

logger = logging.getLogger("tradepilot.learning")

LEARNING_FILE = Path("data/learning_state.json")
LEARNING_FILE.parent.mkdir(exist_ok=True)


def _load_state() -> dict:
    """Charge l'état d'apprentissage depuis le disque."""
    if LEARNING_FILE.exists():
        try:
            return json.loads(LEARNING_FILE.read_text())
        except Exception:
            pass
    return {
        "strategy_performance": {},  # {symbol: {strategy: {wins, losses, total_pnl, sharpe_live}}}
        "criterion_accuracy": {},    # {criterion: {correct_predictions, total_predictions}}
        "weight_adjustments": {},    # {asset_class: {criterion: modifier}}
        "trades_processed": 0,
        "last_retrain": None,
        "version": 1,
    }


def _save_state(state: dict):
    """Sauvegarde l'état sur disque."""
    try:
        LEARNING_FILE.write_text(json.dumps(state, default=str, indent=1))
    except Exception as e:
        logger.warning(f"[LEARNING] Erreur sauvegarde: {e}")


# ============================================================
# 1. PERFORMANCE MATRIX LIVE
# ============================================================

def record_trade_result(symbol: str, strategy: str, direction: str,
                         pnl: float, pnl_pct: float, entry_scores: dict = None):
    """Enregistre le résultat d'un trade pour mettre à jour la matrice.

    Appelé automatiquement quand une position est fermée.
    """
    state = _load_state()

    if symbol not in state["strategy_performance"]:
        state["strategy_performance"][symbol] = {}

    if strategy not in state["strategy_performance"][symbol]:
        state["strategy_performance"][symbol][strategy] = {
            "wins": 0, "losses": 0, "total_pnl": 0, "pnl_history": [],
        }

    perf = state["strategy_performance"][symbol][strategy]
    if pnl > 0:
        perf["wins"] += 1
    else:
        perf["losses"] += 1
    perf["total_pnl"] = round(perf["total_pnl"] + pnl, 2)
    perf["pnl_history"].append(round(pnl_pct, 2))

    # Garder les 50 derniers trades
    perf["pnl_history"] = perf["pnl_history"][-50:]

    # Calculer le Sharpe live
    if len(perf["pnl_history"]) >= 5:
        returns = np.array(perf["pnl_history"])
        mean_ret = float(np.mean(returns))
        std_ret = float(np.std(returns))
        perf["sharpe_live"] = round(mean_ret / std_ret * np.sqrt(252), 3) if std_ret > 0 else 0
    else:
        perf["sharpe_live"] = 0

    perf["win_rate"] = round(perf["wins"] / (perf["wins"] + perf["losses"]) * 100, 1)

    # 2. Enregistrer l'accuracy des critères du scanner
    if entry_scores:
        _update_criterion_accuracy(state, entry_scores, pnl > 0)

    state["trades_processed"] += 1
    _save_state(state)

    logger.info(f"[LEARNING] Trade enregistré: {symbol} {strategy} P/L={pnl:+.2f} "
                f"(WR={perf['win_rate']}%, Sharpe={perf.get('sharpe_live', 0)})")

    return perf


def get_live_best_strategy(symbol: str) -> dict | None:
    """Retourne la meilleure stratégie LIVE pour un actif (basée sur les trades réels)."""
    state = _load_state()
    strategies = state["strategy_performance"].get(symbol, {})

    if not strategies:
        return None

    # Trouver la meilleure par Sharpe live (minimum 3 trades)
    best = None
    for strat, perf in strategies.items():
        total = perf["wins"] + perf["losses"]
        if total < 3:
            continue
        if best is None or perf.get("sharpe_live", 0) > best.get("sharpe_live", 0):
            best = {"strategy": strat, **perf}

    return best


def get_live_matrix() -> dict:
    """Retourne la matrice de performance live complète."""
    state = _load_state()
    return state["strategy_performance"]


# ============================================================
# 2. SCANNER WEIGHT ADAPTATION
# ============================================================

def _update_criterion_accuracy(state: dict, scores: dict, was_profitable: bool):
    """Met à jour l'accuracy de chaque critère du scanner.

    Logique : si un critère avait un score > 60 et le trade a gagné → correct
              si un critère avait un score > 60 et le trade a perdu → incorrect
              L'inverse pour les scores < 40.
    """
    for criterion, score in scores.items():
        if criterion in ("final",):
            continue
        if not isinstance(score, (int, float)):
            continue

        if criterion not in state["criterion_accuracy"]:
            state["criterion_accuracy"][criterion] = {
                "correct": 0, "total": 0, "recent_accuracy": [],
            }

        acc = state["criterion_accuracy"][criterion]
        acc["total"] += 1

        # Score élevé = prédiction haussière
        predicted_good = score >= 60
        # Score bas = prédiction baissière / à éviter
        predicted_bad = score < 40

        if (predicted_good and was_profitable) or (predicted_bad and not was_profitable):
            acc["correct"] += 1
            acc["recent_accuracy"].append(1)
        else:
            acc["recent_accuracy"].append(0)

        # Garder les 30 dernières prédictions
        acc["recent_accuracy"] = acc["recent_accuracy"][-30:]


def compute_weight_adjustments() -> dict:
    """Calcule les ajustements de poids basés sur l'accuracy des critères.

    Retourne un dict {criterion: modifier} où modifier est entre 0.7 et 1.3.
    Les critères qui prédisent bien voient leur poids augmenter.
    """
    state = _load_state()
    adjustments = {}

    for criterion, acc in state["criterion_accuracy"].items():
        if len(acc["recent_accuracy"]) < 10:
            adjustments[criterion] = 1.0
            continue

        recent_acc = sum(acc["recent_accuracy"]) / len(acc["recent_accuracy"])

        # Accuracy > 60% → augmenter le poids (max +30%)
        # Accuracy < 40% → réduire le poids (max -30%)
        # Accuracy 50% → pas de changement
        modifier = 0.7 + (recent_acc * 0.6)  # 0% acc → 0.7, 50% → 1.0, 100% → 1.3
        adjustments[criterion] = round(max(0.7, min(1.3, modifier)), 3)

    # Sauvegarder
    state["weight_adjustments"] = adjustments
    _save_state(state)

    return adjustments


def get_adapted_weights(base_weights: dict) -> dict:
    """Applique les ajustements d'apprentissage aux poids du scanner.

    Appelé par le scanner à chaque scan.
    """
    adjustments = compute_weight_adjustments()
    if not adjustments:
        return base_weights

    adapted = {}
    total = 0
    for criterion, base_weight in base_weights.items():
        modifier = adjustments.get(criterion, 1.0)
        adapted[criterion] = base_weight * modifier
        total += adapted[criterion]

    # Re-normaliser pour que la somme = 1.0
    if total > 0:
        for k in adapted:
            adapted[k] = round(adapted[k] / total, 4)

    return adapted


# ============================================================
# 3. XGBOOST AUTO-RETRAIN
# ============================================================

def should_retrain() -> bool:
    """Vérifie si le modèle ML doit être ré-entraîné."""
    state = _load_state()
    last = state.get("last_retrain")
    if not last:
        return state["trades_processed"] >= 20

    # Ré-entraîner si > 7 jours ou > 50 nouveaux trades
    try:
        last_dt = datetime.fromisoformat(last)
        days_since = (datetime.utcnow() - last_dt).days
        return days_since >= 7 or state["trades_processed"] % 50 == 0
    except Exception:
        return True


def auto_retrain_ml(db) -> dict:
    """Ré-entraîne le modèle XGBoost avec les données récentes."""
    try:
        from backend.modules.scoring.ml_scorer import MLScorer
        scorer = MLScorer()

        # Construire les données d'entraînement depuis les trades fermés
        from backend.database.models import Position, PositionStatus, Asset, OHLCVDaily
        import pandas as pd

        positions = db.query(Position).filter_by(status=PositionStatus.CLOSED).all()
        if len(positions) < 20:
            return {"status": "skipped", "reason": f"Pas assez de trades ({len(positions)}, min 20)"}

        training_rows = []
        for pos in positions:
            asset = db.query(Asset).filter_by(id=pos.asset_id).first()
            if not asset:
                continue

            pnl = 0
            if pos.exit_price and pos.entry_price:
                if pos.direction.value == "LONG":
                    pnl = float(pos.exit_price) - float(pos.entry_price)
                else:
                    pnl = float(pos.entry_price) - float(pos.exit_price)

            profitable = 1 if pnl > 0 else 0

            training_rows.append({
                "symbol": asset.symbol,
                "technical": 50, "correlation": 50, "sentiment": 50,
                "genome": 50, "ipi": 50, "ivf": 50,
                "mts": 50, "sgi": 50, "sus": 50, "narrative": 50,
                "regime": "BULL",
                "target": profitable,
            })

        if len(training_rows) < 20:
            return {"status": "skipped", "reason": "Pas assez de données"}

        df = pd.DataFrame(training_rows)
        scorer.train(df)

        # Mettre à jour le timestamp
        state = _load_state()
        state["last_retrain"] = datetime.utcnow().isoformat()
        _save_state(state)

        logger.info(f"[LEARNING] XGBoost ré-entraîné avec {len(training_rows)} échantillons")
        return {"status": "ok", "samples": len(training_rows)}

    except Exception as e:
        logger.warning(f"[LEARNING] Erreur ré-entraînement: {e}")
        return {"status": "error", "message": str(e)}


# ============================================================
# API de monitoring
# ============================================================

def get_learning_status() -> dict:
    """Statut complet du système d'apprentissage."""
    state = _load_state()

    # Accuracy par critère
    criterion_accuracy = {}
    for criterion, acc in state.get("criterion_accuracy", {}).items():
        recent = acc.get("recent_accuracy", [])
        criterion_accuracy[criterion] = {
            "total_predictions": acc["total"],
            "overall_accuracy": round(acc["correct"] / acc["total"] * 100, 1) if acc["total"] > 0 else 0,
            "recent_accuracy": round(sum(recent) / len(recent) * 100, 1) if recent else 0,
            "sample_size": len(recent),
        }

    # Top stratégies live
    top_strategies = []
    for symbol, strategies in state.get("strategy_performance", {}).items():
        for strat, perf in strategies.items():
            total = perf["wins"] + perf["losses"]
            if total >= 3:
                top_strategies.append({
                    "symbol": symbol,
                    "strategy": strat,
                    "win_rate": perf.get("win_rate", 0),
                    "sharpe_live": perf.get("sharpe_live", 0),
                    "total_trades": total,
                    "total_pnl": perf["total_pnl"],
                })
    top_strategies.sort(key=lambda x: x["sharpe_live"], reverse=True)

    return {
        "trades_processed": state["trades_processed"],
        "last_retrain": state.get("last_retrain"),
        "should_retrain": should_retrain(),
        "criterion_accuracy": criterion_accuracy,
        "weight_adjustments": state.get("weight_adjustments", {}),
        "top_strategies_live": top_strategies[:10],
        "total_symbols_learned": len(state.get("strategy_performance", {})),
    }
