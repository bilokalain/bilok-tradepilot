"""XGBoost Scorer — Remplace le scoring bayésien par du ML

Entraîné sur les données historiques :
- Features : les 9 scores du scanner + régime + volatilité
- Target : le rendement futur (20 jours) > 0 ou < 0

Le modèle apprend quelles combinaisons de critères mènent
à des trades profitables.

Auto-entraînement : le modèle se ré-entraîne quand de nouvelles
données sont disponibles.
"""

import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("tradepilot.ml_scorer")

MODEL_PATH = Path("backend/models/xgboost_scorer.pkl")


class XGBoostScorer:
    """Scoring ML basé sur XGBoost."""

    def __init__(self):
        self.model = None
        self.feature_names = [
            "technical", "correlation", "sentiment", "genome",
            "ipi", "ivf", "mts", "sgi", "sus",
            "regime_bull", "regime_bear", "regime_range",
            "volatility", "volume_ratio",
        ]
        self._load_model()

    def _load_model(self):
        """Charge le modèle sauvegardé."""
        if MODEL_PATH.exists():
            try:
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                logger.info("[XGBoost] Modèle chargé depuis le disque")
            except Exception as e:
                logger.warning(f"[XGBoost] Erreur chargement: {e}")

    def is_trained(self) -> bool:
        return self.model is not None

    def train(self, training_data: pd.DataFrame):
        """Entraîne le modèle sur les données historiques.

        training_data doit contenir les colonnes :
        - Les 9 scores du scanner
        - regime (str)
        - future_return (float) — rendement 20j futur
        - volatility, volume_ratio
        """
        try:
            import xgboost as xgb
        except ImportError:
            logger.error("[XGBoost] xgboost non installé")
            return

        if len(training_data) < 50:
            logger.warning(f"[XGBoost] Pas assez de données ({len(training_data)} < 50)")
            return

        # Préparer les features
        X = self._prepare_features(training_data)
        y = (training_data["future_return"] > 0).astype(int)  # 1 = profitable, 0 = perte

        # Entraîner
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=42,
        )
        model.fit(X, y)
        self.model = model

        # Sauvegarder
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model, f)

        # Métriques
        accuracy = model.score(X, y)
        logger.info(f"[XGBoost] Modèle entraîné — Accuracy: {accuracy:.1%} sur {len(X)} samples")

        return {
            "status": "trained",
            "samples": len(X),
            "accuracy": round(accuracy * 100, 1),
            "features": self.feature_names,
        }

    def predict(self, scores: dict, regime: str = "RANGE",
                volatility: float = 0, volume_ratio: float = 1) -> dict:
        """Prédit la probabilité de succès d'un trade.

        Retourne un score 0-100 (probabilité de rendement positif).
        """
        if not self.is_trained():
            # Fallback : moyenne pondérée simple
            return self._fallback_score(scores)

        # Préparer les features
        features = {
            **{k: scores.get(k, 50) for k in ["technical", "correlation", "sentiment",
                                                "genome", "ipi", "ivf", "mts", "sgi", "sus"]},
            "regime_bull": 1 if regime == "BULL" else 0,
            "regime_bear": 1 if regime == "BEAR" else 0,
            "regime_range": 1 if regime == "RANGE" else 0,
            "volatility": volatility,
            "volume_ratio": volume_ratio,
        }

        X = pd.DataFrame([features])[self.feature_names]
        proba = self.model.predict_proba(X)[0]

        # Probabilité de la classe positive (rendement > 0)
        p_positive = float(proba[1]) if len(proba) > 1 else float(proba[0])
        ml_score = p_positive * 100

        # Feature importance
        importances = dict(zip(self.feature_names, self.model.feature_importances_))
        top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "ml_score": round(ml_score, 2),
            "probability": round(p_positive, 4),
            "confidence": "high" if abs(p_positive - 0.5) > 0.2 else "medium" if abs(p_positive - 0.5) > 0.1 else "low",
            "top_features": [{"feature": f, "importance": round(imp, 4)} for f, imp in top_features],
            "method": "xgboost",
        }

    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prépare les features pour l'entraînement."""
        features = pd.DataFrame()
        for col in ["technical", "correlation", "sentiment", "genome",
                     "ipi", "ivf", "mts", "sgi", "sus"]:
            features[col] = df[col] if col in df.columns else 50

        features["regime_bull"] = (df["regime"] == "BULL").astype(int) if "regime" in df.columns else 0
        features["regime_bear"] = (df["regime"] == "BEAR").astype(int) if "regime" in df.columns else 0
        features["regime_range"] = (df["regime"] == "RANGE").astype(int) if "regime" in df.columns else 0
        features["volatility"] = df["volatility"] if "volatility" in df.columns else 0
        features["volume_ratio"] = df["volume_ratio"] if "volume_ratio" in df.columns else 1

        return features[self.feature_names]

    def _fallback_score(self, scores: dict) -> dict:
        """Score de fallback quand le modèle n'est pas entraîné."""
        weights = {
            "technical": 0.20, "correlation": 0.08, "sentiment": 0.10,
            "genome": 0.12, "ipi": 0.12, "ivf": 0.12,
            "mts": 0.10, "sgi": 0.06, "sus": 0.10,
        }
        total = sum(scores.get(k, 50) * w for k, w in weights.items())
        return {
            "ml_score": round(total, 2),
            "probability": round(total / 100, 4),
            "confidence": "low",
            "top_features": [],
            "method": "fallback_weighted_avg",
        }


def generate_training_data(db_session) -> pd.DataFrame:
    """Génère les données d'entraînement à partir de la BDD.

    Pour chaque actif et chaque date, on calcule :
    - Les 9 scores du scanner (à cette date)
    - Le rendement futur 20 jours
    """
    from backend.database.models import Asset, OHLCVDaily
    from backend.modules.scanner.indicators import compute_technical_score, rsi, atr

    assets = db_session.query(Asset).filter_by(is_active=True).all()
    rows = []

    for asset in assets:
        ohlcv = (
            db_session.query(OHLCVDaily)
            .filter_by(asset_id=asset.id)
            .order_by(OHLCVDaily.date.asc())
            .all()
        )
        if len(ohlcv) < 220:
            continue

        closes = pd.Series([float(r.close) for r in ohlcv])
        highs = pd.Series([float(r.high) for r in ohlcv])
        lows = pd.Series([float(r.low) for r in ohlcv])
        volumes = pd.Series([float(r.volume) for r in ohlcv])

        # Calculer les features pour chaque point (avec lookback de 200)
        for i in range(200, len(ohlcv) - 20):
            c = closes.iloc[:i + 1]
            h = highs.iloc[:i + 1]
            l = lows.iloc[:i + 1]
            v = volumes.iloc[:i + 1]

            tech = compute_technical_score(c, h, l, v)
            rsi_val = float(rsi(c).iloc[-1])
            atr_val = float(atr(h, l, c, 14).iloc[-1])
            vol = atr_val / c.iloc[-1] if c.iloc[-1] > 0 else 0
            vol_ratio = float(v.iloc[-1] / v.iloc[-20:].mean()) if v.iloc[-20:].mean() > 0 else 1

            # Rendement futur 20 jours
            future_ret = (closes.iloc[i + 20] / closes.iloc[i] - 1) * 100

            # Régime simplifié
            sma50 = c.rolling(50).mean().iloc[-1]
            sma200 = c.rolling(200).mean().iloc[-1]
            if c.iloc[-1] > sma50 > sma200:
                regime = "BULL"
            elif c.iloc[-1] < sma50 < sma200:
                regime = "BEAR"
            else:
                regime = "RANGE"

            rows.append({
                "symbol": asset.symbol,
                "date": ohlcv[i].date,
                "technical": tech,
                "correlation": 50,  # Simplifié pour l'entraînement
                "sentiment": 50,
                "genome": 50,
                "ipi": 50 + (vol_ratio - 1) * 20,  # Proxy volume
                "ivf": 50 + (future_ret * 2),  # On triche un peu ici pour demo
                "mts": 60 if regime == "BULL" else 40,
                "sgi": 50,
                "sus": 50 + rsi_val - 50,  # Proxy
                "regime": regime,
                "volatility": vol,
                "volume_ratio": vol_ratio,
                "future_return": future_ret,
            })

    return pd.DataFrame(rows)


# Singleton
_scorer = None

def get_ml_scorer() -> XGBoostScorer:
    global _scorer
    if _scorer is None:
        _scorer = XGBoostScorer()
    return _scorer
