"""Module 3 — Moteur de Scoring : Logique métier

Orchestre les 3 composantes pour produire la Thèse de Trade :
1. Score Bayésien Adaptatif (prior + observations)
2. Score de Qualité du Contexte (SQC) + Shelf Life
3. Sizing Kelly Généralisé

Output : Thèse de Trade complète par actif
"""

import logging
import pandas as pd
from sqlalchemy.orm import Session

logger = logging.getLogger("tradepilot.scoring.service")

from backend.database.models import Asset, OHLCVDaily
from backend.modules.scanner.service import ScannerService
from backend.modules.analyser.service import AnalyserService
from backend.modules.scoring.bayesian import compute_bayesian_score
from backend.modules.scoring.context import compute_sqc, estimate_shelf_life
from backend.modules.scoring.kelly import compute_position_sizing


DEFAULT_CAPITAL = 100_000.0  # Capital paper trading par défaut


class ScoringService:
    """Produit la Thèse de Trade complète pour chaque actif."""

    def __init__(self, db: Session):
        self.db = db
        self.scanner = ScannerService(db)
        self.analyser = AnalyserService(db)

    def _load_ohlcv(self, asset_id: int) -> pd.DataFrame:
        rows = (
            self.db.query(OHLCVDaily)
            .filter_by(asset_id=asset_id)
            .order_by(OHLCVDaily.date.asc())
            .all()
        )
        if not rows:
            return pd.DataFrame()

        data = [{
            "date": r.date,
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "volume": r.volume,
        } for r in rows]

        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        return df

    def _get_cached_scan(self, symbol: str) -> dict | None:
        """Lit le score scanner depuis le cache disque (instantané)."""
        try:
            from backend.modules.scanner.cache import get_cached_results
            cached = get_cached_results()
            for r in cached:
                if r["symbol"] == symbol:
                    return r
        except Exception as e:
            logger.warning(f"[SCORING] Failed to read scanner cache for {symbol}: {e}")
        return None

    def _get_cached_analysis(self, symbol: str) -> dict | None:
        """Lit l'analyse depuis le cache disque (instantané)."""
        try:
            from backend.cache_global import get_analyser_cache
            cache = get_analyser_cache()
            for a in cache.get("analyses", []):
                if a.get("symbol") == symbol:
                    return a
        except Exception as e:
            logger.warning(f"[SCORING] Failed to read analyser cache for {symbol}: {e}")
        return None

    def generate_thesis(self, symbol: str, capital: float = DEFAULT_CAPITAL) -> dict:
        """Génère la Thèse de Trade complète pour un actif."""
        asset = self.db.query(Asset).filter_by(symbol=symbol).first()
        if not asset:
            return {"error": f"Actif {symbol} non trouvé"}

        df = self._load_ohlcv(asset.id)
        if df.empty or len(df) < 200:
            return {"error": f"Pas assez de données pour {symbol}"}

        # --- Module 1 : Scanner (cache d'abord, fallback calcul) ---
        cached_scan = self._get_cached_scan(symbol)
        if cached_scan:
            scan_result = cached_scan
            scanner_score = cached_scan["scores"]["final"]
        else:
            scan_result = self.scanner.scan_asset(symbol)
            if "error" in scan_result:
                return scan_result
            scanner_score = scan_result["scores"]["final"]

        # --- Module 2 : Analyseur (cache d'abord, fallback calcul) ---
        cached_analysis = self._get_cached_analysis(symbol)
        if cached_analysis:
            try:
                analysis = {
                    "regime": {
                        "regime": cached_analysis.get("regime", "BULL"),
                        "confidence": cached_analysis.get("confidence", 0.5),
                    },
                    "best_strategy": {
                        "name": cached_analysis.get("best_strategy", "momentum"),
                        "direction": cached_analysis.get("direction", "LONG"),
                        "conviction": cached_analysis.get("conviction", 50),
                        "backtest_sharpe": cached_analysis.get("backtest_sharpe", 0),
                    },
                }
            except Exception as e:
                logger.warning(f"[SCORING] Failed to parse cached analysis for {symbol}: {e}")
                cached_analysis = None

        if not cached_analysis:
            analysis = self.analyser.analyse_asset(symbol)
            if "error" in analysis:
                return analysis

        regime_data = analysis.get("regime", {})
        regime = regime_data.get("regime", "BULL") if isinstance(regime_data, dict) else str(regime_data) if regime_data else "BULL"
        regime_confidence = regime_data.get("confidence", 0.5) if isinstance(regime_data, dict) else 0.5
        best_strategy = analysis.get("best_strategy", {})
        direction = best_strategy.get("direction", "LONG") if isinstance(best_strategy, dict) else "LONG"
        conviction = best_strategy.get("conviction", 50) if isinstance(best_strategy, dict) else 50
        strategy_name = best_strategy.get("name", "momentum") if isinstance(best_strategy, dict) else str(best_strategy)
        # Sécurité : s'assurer que regime et strategy_name sont des strings
        if not isinstance(regime, str):
            regime = "BULL"
        if not isinstance(strategy_name, str):
            strategy_name = "momentum"

        # Pas de signal → pas de thèse
        if direction == "NEUTRAL" or conviction == 0:
            return {
                "symbol": symbol,
                "name": asset.name,
                "asset_class": asset.asset_class.value,
                "action": "NO_TRADE",
                "reason": "Aucun signal directionnel",
                "scanner_score": scanner_score,
                "regime": analysis["regime"],
            }

        entry = best_strategy.get("entry", float(df["close"].iloc[-1]))
        stop_loss = best_strategy.get("stop_loss")
        take_profit = best_strategy.get("take_profit")

        # --- Score Bayésien ---
        bayesian = compute_bayesian_score(
            df["close"], scanner_score, conviction, regime_confidence
        )

        # --- Score de Qualité du Contexte ---
        sqc_result = compute_sqc(df["volume"], df["high"], df["low"], df["close"])

        # --- Signal Shelf Life ---
        safe_strategy = strategy_name if isinstance(strategy_name, str) else "momentum"
        shelf_life = estimate_shelf_life(
            safe_strategy or "momentum", regime, conviction, sqc_result["sqc"]
        )

        # --- Sizing Kelly ---
        sizing = compute_position_sizing(
            capital, entry, stop_loss, take_profit,
            bayesian["posterior"], conviction
        )

        # --- Score final de la thèse ---
        # Poids dynamiques — ajustés par le calibrateur basé sur les top movers
        try:
            from backend.modules.learning.scoring_calibrator import get_current_weights
            w = get_current_weights()
        except Exception as e:
            logger.warning(f"[SCORING] Calibrator weights unavailable, using defaults: {e}")
            w = {"bayesian": 0.30, "sqc": 0.20, "conviction": 0.35, "scanner": 0.15}

        thesis_score = (
            bayesian["posterior"] * w["bayesian"] +
            sqc_result["sqc"] * w["sqc"] +
            conviction * w["conviction"] +
            scanner_score * w["scanner"]
        )

        # Décision : GO / WAIT / NO_TRADE
        if thesis_score >= 65 and sizing["kelly_fraction"] > 0:
            action = "GO"
        elif thesis_score >= 50:
            action = "WAIT"
        else:
            action = "NO_TRADE"

        # TP2 = 1.5x le TP1
        tp2 = None
        if entry and take_profit:
            tp2 = round(entry + 1.5 * (take_profit - entry), 2)

        return {
            "symbol": symbol,
            "name": asset.name,
            "asset_class": asset.asset_class.value,
            "action": action,
            "thesis_score": round(thesis_score, 2),
            "score_v2": round(thesis_score, 2),

            # Direction
            "direction": direction,
            "strategy": strategy_name,
            "regime": analysis["regime"],

            # Prix
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit_1": take_profit,
            "take_profit_2": tp2,
            "last_close": float(df["close"].iloc[-1]),

            # Scores
            "bayesian": bayesian,
            "scanner_score": scanner_score,
            "conviction": conviction,
            "sqc": sqc_result,
            "shelf_life": shelf_life,

            # Sizing
            "sizing": sizing,
        }

    def generate_all_theses(self, capital: float = DEFAULT_CAPITAL) -> list[dict]:
        """Génère les thèses de trade pour tous les actifs."""
        assets = self.db.query(Asset).filter_by(is_active=True).all()
        theses = []

        for asset in assets:
            thesis = self.generate_thesis(asset.symbol, capital)
            if "error" not in thesis:
                theses.append(thesis)

        # Trier : GO d'abord, puis par score décroissant
        action_order = {"GO": 0, "WAIT": 1, "NO_TRADE": 2}
        theses.sort(
            key=lambda t: (action_order.get(t["action"], 3), -t.get("thesis_score", 0))
        )

        return theses

    def get_active_signals(self, capital: float = DEFAULT_CAPITAL) -> list[dict]:
        """Retourne uniquement les signaux actifs (GO)."""
        all_theses = self.generate_all_theses(capital)
        return [t for t in all_theses if t["action"] == "GO"]
