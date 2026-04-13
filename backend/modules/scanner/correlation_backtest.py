"""Backtest de corrélation historique

Teste la stabilité des corrélations sur l'historique complet :

1. Rolling Correlation — corrélation glissante (fenêtre 60j) sur tout l'historique
2. Corrélation par période — chaque année, chaque crise, chaque bull market
3. Stress Test Corrélation — la corrélation tient-elle pendant les crises ?
4. Fiabilité du beta — si A fait +X%, B fait-il vraiment +beta*X% historiquement ?
5. Score de stabilité — la corrélation est-elle fiable pour trader ?
"""

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily


HISTORICAL_PERIODS = {
    "Dot-com Crash": ("2000-03-10", "2002-10-09"),
    "Bull 2003-2007": ("2003-03-12", "2007-10-09"),
    "Crise 2008": ("2007-10-09", "2009-03-09"),
    "Bull 2009-2020": ("2009-03-09", "2020-02-19"),
    "COVID Crash": ("2020-02-19", "2020-03-23"),
    "Recovery COVID": ("2020-03-23", "2021-12-31"),
    "Bear 2022": ("2022-01-03", "2022-10-12"),
    "Rally IA": ("2023-01-01", "2024-12-31"),
    "2025-2026": ("2025-01-01", "2026-12-31"),
}


def _load_closes(db: Session, symbol: str) -> pd.Series | None:
    asset = db.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        from backend.modules.scanner.quick_analyse import resolve_symbol
        resolved = resolve_symbol(symbol)
        asset = db.query(Asset).filter_by(symbol=resolved).first()
    if not asset:
        return None

    rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.asc()).all()
    if len(rows) < 30:
        return None

    dates = [r.date for r in rows]
    closes = [float(r.close) for r in rows]
    return pd.Series(closes, index=pd.to_datetime(dates))


def rolling_correlation(db: Session, symbol_a: str, symbol_b: str,
                         window: int = 60) -> dict:
    """Corrélation glissante sur tout l'historique.

    Retourne la série temporelle de corrélation pour visualiser
    quand elle est forte et quand elle casse.
    """
    closes_a = _load_closes(db, symbol_a)
    closes_b = _load_closes(db, symbol_b)

    if closes_a is None or closes_b is None:
        return {"error": f"Données manquantes pour {symbol_a} ou {symbol_b}"}

    # Aligner
    df = pd.DataFrame({"a": closes_a, "b": closes_b}).dropna()
    if len(df) < window + 10:
        return {"error": f"Pas assez de données communes ({len(df)} jours, minimum {window + 10})"}

    ret_a = df["a"].pct_change().dropna()
    ret_b = df["b"].pct_change().dropna()

    rolling_corr = ret_a.rolling(window).corr(ret_b).dropna()

    # Statistiques
    corr_values = rolling_corr.values
    dates = [str(d.date()) for d in rolling_corr.index]

    # Échantillonner pour ne pas surcharger (max 500 points)
    step = max(1, len(dates) // 500)
    sampled_dates = dates[::step]
    sampled_values = [round(float(v), 3) for v in corr_values[::step]]

    # Périodes de rupture (corrélation < 0 alors que moyenne > 0.3)
    mean_corr = float(np.mean(corr_values))
    breaks = []
    if mean_corr > 0.3:
        for i, v in enumerate(corr_values):
            if v < 0 and i > 0 and corr_values[i - 1] >= 0:
                breaks.append({
                    "date": dates[i],
                    "correlation": round(float(v), 3),
                    "duration_days": 0,
                })

    return {
        "symbol_a": symbol_a,
        "symbol_b": symbol_b,
        "window": window,
        "data_points": len(rolling_corr),
        "first_date": dates[0] if dates else None,
        "last_date": dates[-1] if dates else None,
        "statistics": {
            "mean": round(mean_corr, 3),
            "min": round(float(np.min(corr_values)), 3),
            "max": round(float(np.max(corr_values)), 3),
            "std": round(float(np.std(corr_values)), 3),
            "current": round(float(corr_values[-1]), 3),
            "pct_positive": round(float(np.mean(corr_values > 0)) * 100, 1),
            "pct_above_05": round(float(np.mean(corr_values > 0.5)) * 100, 1),
        },
        "breaks": breaks[:20],
        "chart": {
            "dates": sampled_dates,
            "values": sampled_values,
        },
    }


def correlation_by_period(db: Session, symbol_a: str, symbol_b: str) -> dict:
    """Corrélation pour chaque période historique (crises, bull markets)."""
    closes_a = _load_closes(db, symbol_a)
    closes_b = _load_closes(db, symbol_b)

    if closes_a is None or closes_b is None:
        return {"error": f"Données manquantes"}

    df = pd.DataFrame({"a": closes_a, "b": closes_b}).dropna()
    ret_a = df["a"].pct_change()
    ret_b = df["b"].pct_change()

    periods = {}
    for name, (start, end) in HISTORICAL_PERIODS.items():
        start_dt = pd.Timestamp(start)
        end_dt = pd.Timestamp(end)

        mask = (df.index >= start_dt) & (df.index <= end_dt)
        period_a = ret_a[mask].dropna()
        period_b = ret_b[mask].dropna()

        if len(period_a) < 15:
            continue

        min_len = min(len(period_a), len(period_b))
        corr = float(np.corrcoef(period_a.iloc[:min_len], period_b.iloc[:min_len])[0, 1])

        if np.isnan(corr):
            continue

        # Performance de chaque actif pendant cette période
        period_df = df[mask]
        if len(period_df) >= 2:
            perf_a = (float(period_df["a"].iloc[-1]) / float(period_df["a"].iloc[0]) - 1) * 100
            perf_b = (float(period_df["b"].iloc[-1]) / float(period_df["b"].iloc[0]) - 1) * 100
        else:
            perf_a = perf_b = 0

        periods[name] = {
            "correlation": round(corr, 3),
            "days": len(period_a),
            "perf_a": round(perf_a, 1),
            "perf_b": round(perf_b, 1),
            "moved_together": (perf_a > 0) == (perf_b > 0),
        }

    # Score de stabilité
    if periods:
        corr_values = [p["correlation"] for p in periods.values()]
        stability = 100 - float(np.std(corr_values)) * 200  # Moins de variance = plus stable
        stability = max(0, min(100, stability))
    else:
        stability = 0

    return {
        "symbol_a": symbol_a,
        "symbol_b": symbol_b,
        "periods": periods,
        "stability_score": round(stability, 1),
        "interpretation": (
            "Corrélation très stable dans le temps — fiable pour trader" if stability > 75
            else "Corrélation modérément stable — utiliser avec prudence" if stability > 50
            else "Corrélation instable — ne pas s'y fier pour le trading"
        ),
    }


def beta_backtest(db: Session, symbol_a: str, symbol_b: str) -> dict:
    """Vérifie si le beta historique est fiable.

    Si beta = 1.2, est-ce que quand A fait +10%, B fait vraiment +12% ?
    """
    closes_a = _load_closes(db, symbol_a)
    closes_b = _load_closes(db, symbol_b)

    if closes_a is None or closes_b is None:
        return {"error": "Données manquantes"}

    df = pd.DataFrame({"a": closes_a, "b": closes_b}).dropna()
    if len(df) < 60:
        return {"error": "Pas assez de données"}

    ret_a = df["a"].pct_change().dropna()
    ret_b = df["b"].pct_change().dropna()
    min_len = min(len(ret_a), len(ret_b))
    ret_a = ret_a.iloc[:min_len]
    ret_b = ret_b.iloc[:min_len]

    # Beta calculé
    cov = np.cov(ret_a, ret_b)
    beta = float(cov[0][1] / cov[0][0]) if cov[0][0] > 0 else 0

    # Tester le beta sur des "gros mouvements" de A
    # Quand A fait > +2% en un jour, combien B fait ?
    big_up_a = ret_a[ret_a > 0.02]
    big_down_a = ret_a[ret_a < -0.02]

    predicted_vs_actual_up = []
    for date in big_up_a.index:
        if date in ret_b.index:
            actual_b = float(ret_b[date]) * 100
            predicted_b = float(ret_a[date]) * beta * 100
            predicted_vs_actual_up.append({
                "date": str(date.date()) if hasattr(date, 'date') else str(date),
                "move_a": round(float(ret_a[date]) * 100, 2),
                "predicted_b": round(predicted_b, 2),
                "actual_b": round(actual_b, 2),
                "error": round(abs(actual_b - predicted_b), 2),
            })

    predicted_vs_actual_down = []
    for date in big_down_a.index:
        if date in ret_b.index:
            actual_b = float(ret_b[date]) * 100
            predicted_b = float(ret_a[date]) * beta * 100
            predicted_vs_actual_down.append({
                "date": str(date.date()) if hasattr(date, 'date') else str(date),
                "move_a": round(float(ret_a[date]) * 100, 2),
                "predicted_b": round(predicted_b, 2),
                "actual_b": round(actual_b, 2),
                "error": round(abs(actual_b - predicted_b), 2),
            })

    # Erreur moyenne
    all_errors = [p["error"] for p in predicted_vs_actual_up + predicted_vs_actual_down]
    avg_error = float(np.mean(all_errors)) if all_errors else 0

    # Fiabilité : % de fois où la direction est correcte
    correct_direction = 0
    total = 0
    for p in predicted_vs_actual_up + predicted_vs_actual_down:
        total += 1
        if (p["predicted_b"] > 0) == (p["actual_b"] > 0):
            correct_direction += 1

    reliability = (correct_direction / total * 100) if total > 0 else 0

    return {
        "symbol_a": symbol_a,
        "symbol_b": symbol_b,
        "beta": round(beta, 3),
        "avg_prediction_error": round(avg_error, 2),
        "direction_reliability": round(reliability, 1),
        "big_moves_tested": total,
        "sample_predictions_up": predicted_vs_actual_up[:10],
        "sample_predictions_down": predicted_vs_actual_down[:10],
        "interpretation": (
            f"Beta {beta:.2f} fiable à {reliability:.0f}% (direction correcte). Erreur moyenne {avg_error:.1f}%."
            + (" Très fiable !" if reliability > 75 else " Utiliser avec prudence." if reliability > 60 else " Pas fiable — ne pas trader dessus.")
        ),
    }


def full_correlation_backtest(db: Session, symbol_a: str, symbol_b: str) -> dict:
    """Backtest complet de la corrélation entre deux actifs."""
    rolling = rolling_correlation(db, symbol_a, symbol_b)
    periods = correlation_by_period(db, symbol_a, symbol_b)
    beta_test = beta_backtest(db, symbol_a, symbol_b)

    # Score global de fiabilité
    scores = []
    if "statistics" in rolling:
        scores.append(rolling["statistics"]["pct_above_05"])
    if "stability_score" in periods:
        scores.append(periods["stability_score"])
    if "direction_reliability" in beta_test:
        scores.append(beta_test["direction_reliability"])

    global_score = float(np.mean(scores)) if scores else 0

    return {
        "global_reliability_score": round(global_score, 1),
        "verdict": (
            "Corrélation fiable — exploitable pour le trading" if global_score > 70
            else "Corrélation modérée — utiliser avec des stops serrés" if global_score > 50
            else "Corrélation faible — ne pas baser de stratégie dessus"
        ),
        "rolling_correlation": rolling,
        "by_period": periods,
        "beta_backtest": beta_test,
    }
