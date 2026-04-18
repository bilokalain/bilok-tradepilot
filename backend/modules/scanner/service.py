"""Module 1 — Scanner de Marché : Logique métier

9 critères orthogonaux avec matrice de poids adaptatifs :
1. Corrélation          2. Sentiment           3. Analyse Technique
4. Génome Explosif      5. Capital Institutionnel (IPI)
6. Vélocité Fondamentale (IVF)   7. Macro Tailwind (MTS)
8. Topologie Sociale (SGI)       9. Unicité du Signal (SUS)

Matrice adaptative selon : classe d'actif, régime de marché, horizon.
Vetos croisés : MTS < 20, SUS < 25, IPI < 20 → rejet.
"""

import logging
import pandas as pd
from sqlalchemy.orm import Session

logger = logging.getLogger("tradepilot.scanner.service")

from backend.database.models import Asset, OHLCVDaily
from backend.modules.scanner.indicators import compute_technical_score
from backend.modules.scanner.correlation import compute_correlation_score
from backend.modules.scanner.sentiment import fetch_reddit_mentions, compute_sentiment_score
from backend.modules.scanner.genome import compute_genome_score
from backend.modules.scanner.institutional import compute_ipi_score
from backend.modules.scanner.fundamental_velocity import compute_ivf_score
from backend.modules.scanner.macro import compute_mts_score
from backend.modules.scanner.social import compute_sgi_score
from backend.modules.scanner.uniqueness import compute_sus_score
from backend.modules.scanner.narrative import compute_narrative_score


# Matrice de poids adaptatifs par classe d'actif
WEIGHT_MATRIX = {
    "ACTION_US": {
        "correlation": 0.07, "sentiment": 0.07, "technical": 0.16,
        "genome": 0.10, "ipi": 0.13, "ivf": 0.12,
        "mts": 0.08, "sgi": 0.05, "sus": 0.08, "narrative": 0.14,
    },
    "ACTION_EU": {
        "correlation": 0.09, "sentiment": 0.05, "technical": 0.16,
        "genome": 0.10, "ipi": 0.11, "ivf": 0.12,
        "mts": 0.10, "sgi": 0.05, "sus": 0.10, "narrative": 0.12,
    },
    "ETF": {
        "correlation": 0.10, "sentiment": 0.04, "technical": 0.18,
        "genome": 0.08, "ipi": 0.08, "ivf": 0.08,
        "mts": 0.13, "sgi": 0.03, "sus": 0.13, "narrative": 0.15,
    },
    "CRYPTO": {
        "correlation": 0.05, "sentiment": 0.13, "technical": 0.13,
        "genome": 0.12, "ipi": 0.04, "ivf": 0.07,
        "mts": 0.06, "sgi": 0.15, "sus": 0.10, "narrative": 0.15,
    },
    "FOREX": {
        "correlation": 0.13, "sentiment": 0.04, "technical": 0.18,
        "genome": 0.07, "ipi": 0.04, "ivf": 0.09,
        "mts": 0.18, "sgi": 0.02, "sus": 0.13, "narrative": 0.12,
    },
    "COMMODITY": {
        "correlation": 0.09, "sentiment": 0.07, "technical": 0.16,
        "genome": 0.09, "ipi": 0.09, "ivf": 0.10,
        "mts": 0.13, "sgi": 0.04, "sus": 0.10, "narrative": 0.13,
    },
}

DEFAULT_WEIGHTS = {
    "correlation": 0.08, "sentiment": 0.07, "technical": 0.16,
    "genome": 0.10, "ipi": 0.09, "ivf": 0.10,
    "mts": 0.10, "sgi": 0.06, "sus": 0.10, "narrative": 0.14,
}

VETO_THRESHOLDS = {
    "mts": 20,
    "sus": 25,
    "ipi": 20,
}


class ScannerService:
    """Orchestre les 9 critères du scanner et produit le score final."""

    def __init__(self, db: Session):
        self.db = db
        self._ohlcv_cache: dict[str, pd.DataFrame] = {}
        self._closes_cache: dict[str, pd.Series] = {}

    def _load_ohlcv(self, asset_id: int) -> pd.DataFrame:
        if asset_id in self._ohlcv_cache:
            return self._ohlcv_cache[asset_id]

        rows = (
            self.db.query(OHLCVDaily)
            .filter_by(asset_id=asset_id)
            .order_by(OHLCVDaily.date.asc())
            .all()
        )
        if not rows:
            return pd.DataFrame()

        data = [{"date": r.date, "open": r.open, "high": r.high,
                 "low": r.low, "close": r.close, "volume": r.volume} for r in rows]
        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        self._ohlcv_cache[asset_id] = df
        return df

    def _load_all_closes(self) -> dict[str, pd.Series]:
        """Charge les closes de tous les actifs (pour corrélation + crowding)."""
        if self._closes_cache:
            return self._closes_cache

        assets = self.db.query(Asset).filter_by(is_active=True).all()
        for a in assets:
            df = self._load_ohlcv(a.id)
            if not df.empty:
                self._closes_cache[a.symbol] = df["close"]
        return self._closes_cache

    def _get_benchmark_close(self, symbol: str) -> pd.Series | None:
        """Retourne le close du benchmark selon le symbole."""
        benchmarks = {"SPY": "SPY", "TLT": "TLT", "GLD": "GLD"}
        for bench_sym in benchmarks.values():
            if bench_sym == symbol:
                continue
            asset = self.db.query(Asset).filter_by(symbol=bench_sym).first()
            if asset:
                df = self._load_ohlcv(asset.id)
                if not df.empty:
                    return df["close"]
        return None

    def _get_macro_data(self) -> dict:
        """Charge les données macro (SPY, TLT, GLD)."""
        result = {}
        for sym in ["SPY", "TLT", "GLD"]:
            asset = self.db.query(Asset).filter_by(symbol=sym).first()
            if asset:
                df = self._load_ohlcv(asset.id)
                if not df.empty:
                    result[sym] = df["close"]
        return result

    def scan_asset(self, symbol: str) -> dict:
        """Scan complet d'un actif avec les 9 critères."""
        asset = self.db.query(Asset).filter_by(symbol=symbol).first()
        if not asset:
            return {"error": f"Actif {symbol} non trouvé"}

        df = self._load_ohlcv(asset.id)
        if df.empty or len(df) < 50:
            return {"error": f"Pas assez de données pour {symbol}"}

        close, high, low, volume = df["close"], df["high"], df["low"], df["volume"]
        asset_class = asset.asset_class.value
        all_closes = self._load_all_closes()

        # --- 1. Corrélation ---
        corr_score = compute_correlation_score(all_closes, symbol)

        # --- 2. Sentiment ---
        from backend.modules.scanner.sentiment import _simulate_mentions
        mentions = _simulate_mentions(symbol)
        sentiment_result = compute_sentiment_score(mentions)
        sentiment_score = sentiment_result["score"]

        # --- 3. Analyse Technique ---
        tech_score = compute_technical_score(close, high, low, volume)

        # --- 4. Génome Explosif ---
        genome_result = compute_genome_score(close, high, low, volume)
        genome_score = genome_result["score"]

        # --- 5. Capital Institutionnel (IPI) ---
        ipi_result = compute_ipi_score(close, high, low, volume)
        ipi_score = ipi_result["score"]

        # --- 6. Vélocité Fondamentale (IVF) ---
        benchmark = self._get_benchmark_close(symbol)
        ivf_result = compute_ivf_score(close, volume, benchmark)
        ivf_score = ivf_result["score"]

        # --- 7. Macro Tailwind (MTS) ---
        macro = self._get_macro_data()
        mts_result = compute_mts_score(
            asset_class,
            spy_close=macro.get("SPY"),
            tlt_close=macro.get("TLT"),
            gld_close=macro.get("GLD"),
        )
        mts_score = mts_result["score"]

        # --- 8. Topologie Sociale (SGI) ---
        sgi_result = compute_sgi_score(mentions, symbol, asset_class)
        sgi_score = sgi_result["score"]

        # --- 9. Unicité du Signal (SUS) ---
        # On a besoin de tous les scores techniques pour le crowding
        all_tech_scores = {}
        for sym, closes in all_closes.items():
            if len(closes) >= 50:
                # Réutiliser le cache ou un calcul rapide
                all_tech_scores[sym] = compute_technical_score(
                    closes,
                    self._load_ohlcv(self.db.query(Asset).filter_by(symbol=sym).first().id)["high"],
                    self._load_ohlcv(self.db.query(Asset).filter_by(symbol=sym).first().id)["low"],
                    self._load_ohlcv(self.db.query(Asset).filter_by(symbol=sym).first().id)["volume"],
                )

        sus_result = compute_sus_score(close, high, low, all_tech_scores, symbol)
        sus_score = sus_result["score"]

        # --- 11. Narrative Momentum ---
        narrative_result = compute_narrative_score(close, high, low, volume)
        narrative_score = narrative_result["score"]

        # --- Score final avec poids adaptatifs + apprentissage ---
        base_weights = WEIGHT_MATRIX.get(asset_class, DEFAULT_WEIGHTS).copy()
        weights = base_weights
        try:
            from backend.modules.learning.adaptive_engine import get_adapted_weights
            adapted = get_adapted_weights(base_weights)
            if adapted != base_weights:
                weights = adapted
                logger.info(f"[SCANNER] {symbol}: poids adaptés par apprentissage appliqués")
            else:
                logger.debug(f"[SCANNER] {symbol}: poids adaptés identiques aux poids de base")
        except Exception as e:
            logger.warning(f"[SCANNER] {symbol}: échec poids adaptatifs, fallback poids de base: {e}")
        scores = {
            "correlation": corr_score,
            "sentiment": sentiment_score,
            "technical": tech_score,
            "genome": genome_score,
            "ipi": ipi_score,
            "ivf": ivf_score,
            "mts": mts_score,
            "sgi": sgi_score,
            "sus": sus_score,
            "narrative": narrative_score,
        }

        # Vetos croisés
        vetoed = False
        veto_reasons = []
        for criterion, threshold in VETO_THRESHOLDS.items():
            if scores.get(criterion, 100) < threshold:
                vetoed = True
                veto_reasons.append(f"{criterion.upper()} = {scores[criterion]:.1f} (seuil: {threshold})")

        # Score pondéré
        final_score = sum(scores[k] * weights[k] for k in scores)

        if vetoed:
            final_score = min(final_score, 30)  # Plafonner si veto

        return {
            "symbol": symbol,
            "name": asset.name,
            "asset_class": asset_class,
            "scores": {
                **scores,
                "final": round(final_score, 2),
            },
            "weights": weights,
            "vetoed": vetoed,
            "veto_reasons": veto_reasons,
            "last_close": float(close.iloc[-1]),
            "data_points": len(df),
            "details": {
                "genome": {
                    "cycle_phase": genome_result["cycle_phase"],
                    "seismograph_active": genome_result["seismograph"]["active"],
                },
                "ipi": {
                    "ad_trend": ipi_result["ad_trend"],
                    "smart_money": ipi_result["smart_money_score"],
                },
                "ivf": {
                    "acceleration": ivf_result["acceleration"],
                    "relative_strength": ivf_result["relative_strength"],
                },
                "mts": {
                    "cycle": mts_result["cycle"]["phase"],
                    "rates": mts_result["rates"]["regime"],
                    "risk": mts_result["risk_appetite"]["regime"],
                },
                "sgi": {
                    "mentions": sgi_result["sentiment"]["num_mentions"],
                    "signal_noise": sgi_result["signal_to_noise"],
                },
                "sus": {
                    "crowding": sus_result["crowding"],
                    "novelty": sus_result["novelty"],
                },
            },
        }

    def scan_all(self) -> list[dict]:
        """Scan tous les actifs actifs."""
        assets = self.db.query(Asset).filter_by(is_active=True).all()
        results = []
        for asset in assets:
            result = self.scan_asset(asset.symbol)
            if "error" not in result:
                results.append(result)

        results.sort(key=lambda x: x["scores"]["final"], reverse=True)
        return results
