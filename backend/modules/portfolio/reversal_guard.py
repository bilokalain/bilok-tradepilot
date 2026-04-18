"""Reversal Guard — Détection de retournement et clôture automatique

Surveille 5 signaux de retournement en temps réel :
1. Régime passe de BULL → BEAR/CRISIS
2. VIX spike (> 25 = panique)
3. Drawdown portefeuille > -5%
4. Cassure SMA200 sur SPY
5. Corrélation cross-asset (tout baisse en même temps)

Niveaux d'alerte :
- VERT  : 0-1 signal  → tout va bien
- JAUNE : 2 signaux   → surveiller, trailing stops serrés
- ORANGE : 3 signaux  → réduire 30% des positions
- ROUGE : 4-5 signaux → fermer toutes les positions LONG
"""

import logging
from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Asset, OHLCVDaily

logger = logging.getLogger("tradepilot.reversal_guard")


def check_reversal_signals(db: Session) -> dict:
    """Vérifie les 5 signaux de retournement."""
    signals = []

    # 1. Régime de marché
    try:
        from backend.modules.analyser.service import AnalyserService
        regime = AnalyserService(db).get_regime_summary()
        dominant = regime.get("dominant_regime", "BULL")
        bear_prob = regime.get("probabilities", {}).get("BEAR", 0) + regime.get("probabilities", {}).get("CRISIS", 0)

        if dominant in ("BEAR", "CRISIS"):
            signals.append({"name": "Régime BEAR/CRISIS", "severity": 2, "detail": f"Régime {dominant} ({bear_prob:.0%})"})
        elif dominant == "TRANSITION" or bear_prob > 0.3:
            signals.append({"name": "Régime en transition", "severity": 1, "detail": f"Prob Bear+Crisis: {bear_prob:.0%}"})
    except Exception:
        pass

    # 2. VIX (peur du marché)
    try:
        spy = db.query(Asset).filter_by(symbol="SPY").first()
        if spy:
            rows = db.query(OHLCVDaily).filter_by(asset_id=spy.id).order_by(OHLCVDaily.date.desc()).limit(30).all()
            if len(rows) >= 20:
                closes = [float(r.close) for r in reversed(rows)]
                returns = pd.Series(closes).pct_change().dropna()
                volatility = float(returns.std() * np.sqrt(252) * 100)  # Annualisée

                if volatility > 30:
                    signals.append({"name": "Volatilité extrême", "severity": 2, "detail": f"Vol annualisée {volatility:.0f}% (seuil 30%)"})
                elif volatility > 20:
                    signals.append({"name": "Volatilité élevée", "severity": 1, "detail": f"Vol annualisée {volatility:.0f}% (seuil 20%)"})
    except Exception:
        pass

    # 3. Drawdown portefeuille
    try:
        from backend.modules.execution.broker_alpaca import alpaca_broker
        if alpaca_broker.is_configured:
            acct = alpaca_broker.get_account()
            equity = float(acct["equity"])
            dd_pct = (equity / 100_000 - 1) * 100

            if dd_pct < -10:
                signals.append({"name": "Drawdown critique", "severity": 2, "detail": f"Drawdown {dd_pct:.1f}% (seuil -10%)"})
            elif dd_pct < -5:
                signals.append({"name": "Drawdown élevé", "severity": 1, "detail": f"Drawdown {dd_pct:.1f}% (seuil -5%)"})
    except Exception:
        pass

    # 4. Cassure SMA200 sur SPY
    try:
        spy = db.query(Asset).filter_by(symbol="SPY").first()
        if spy:
            rows = db.query(OHLCVDaily).filter_by(asset_id=spy.id).order_by(OHLCVDaily.date.desc()).limit(210).all()
            if len(rows) >= 200:
                closes = [float(r.close) for r in reversed(rows)]
                sma200 = np.mean(closes[-200:])
                current = closes[-1]

                if current < sma200 * 0.97:
                    signals.append({"name": "SPY sous SMA200", "severity": 2, "detail": f"SPY ${current:.0f} < SMA200 ${sma200:.0f} (-{(1-current/sma200)*100:.1f}%)"})
                elif current < sma200:
                    signals.append({"name": "SPY touche SMA200", "severity": 1, "detail": f"SPY ${current:.0f} ≈ SMA200 ${sma200:.0f}"})
    except Exception:
        pass

    # 5. Corrélation cross-asset (tout baisse en même temps)
    try:
        benchmarks = ["SPY", "QQQ", "IWM", "GLD", "TLT"]
        down_count = 0
        details = []
        for sym in benchmarks:
            asset = db.query(Asset).filter_by(symbol=sym).first()
            if asset:
                rows = db.query(OHLCVDaily).filter_by(asset_id=asset.id).order_by(OHLCVDaily.date.desc()).limit(6).all()
                if len(rows) >= 2:
                    ret_5d = (float(rows[0].close) / float(rows[-1].close) - 1) * 100
                    details.append(f"{sym} {ret_5d:+.1f}%")
                    if ret_5d < -2:
                        down_count += 1

        if down_count >= 4:
            signals.append({"name": "Sell-off généralisé", "severity": 2, "detail": f"{down_count}/5 benchmarks en baisse: {', '.join(details)}"})
        elif down_count >= 3:
            signals.append({"name": "Faiblesse généralisée", "severity": 1, "detail": f"{down_count}/5 en baisse: {', '.join(details)}"})
    except Exception:
        pass

    # Calcul du niveau d'alerte
    total_severity = sum(s["severity"] for s in signals)
    n_signals = len(signals)

    if total_severity >= 6 or n_signals >= 4:
        level = "ROUGE"
        action = "CLOSE_ALL_LONG"
        message = "Retournement détecté — fermer toutes les positions LONG"
    elif total_severity >= 4 or n_signals >= 3:
        level = "ORANGE"
        action = "REDUCE_30"
        message = "Signaux de retournement — réduire 30% des positions"
    elif total_severity >= 2 or n_signals >= 2:
        level = "JAUNE"
        action = "TIGHTEN_STOPS"
        message = "Vigilance — resserrer les stop-loss"
    else:
        level = "VERT"
        action = "HOLD"
        message = "Pas de signal de retournement"

    return {
        "level": level,
        "action": action,
        "message": message,
        "n_signals": n_signals,
        "total_severity": total_severity,
        "signals": signals,
        "checked_at": datetime.utcnow().isoformat(),
    }


def auto_protect(db: Session) -> dict:
    """Exécute les actions de protection automatiquement.

    Appelé par le pipeline nocturne ou manuellement.
    """
    check = check_reversal_signals(db)
    actions_taken = []

    if check["action"] == "HOLD":
        return {"check": check, "actions": [], "message": "Aucune action nécessaire"}

    try:
        from backend.modules.execution.broker_alpaca import alpaca_broker
        if not alpaca_broker.is_configured:
            return {"check": check, "actions": [], "message": "Alpaca non configuré"}

        positions = alpaca_broker.get_positions()
        long_positions = [p for p in positions if p.get("side", "long") == "long"]

        if check["action"] == "CLOSE_ALL_LONG":
            # Fermer toutes les positions LONG
            for p in long_positions:
                try:
                    # Annuler les ordres ouverts
                    open_orders = alpaca_broker.get_orders(status="open")
                    for o in open_orders:
                        if o["symbol"] == p["symbol"]:
                            alpaca_broker.cancel_order(o["id"])
                    # Fermer
                    result = alpaca_broker.close_position(p["symbol"])
                    actions_taken.append({"symbol": p["symbol"], "action": "CLOSED", "pnl": p.get("pnl", 0)})
                    logger.warning(f"[REVERSAL] Position fermée: {p['symbol']} P/L=${p.get('pnl',0):.2f}")
                except Exception as e:
                    actions_taken.append({"symbol": p["symbol"], "action": "ERROR", "error": str(e)})

        elif check["action"] == "REDUCE_30":
            # Réduire 30% de chaque position LONG
            for p in long_positions:
                qty_to_sell = round(float(p["quantity"]) * 0.3, 2)
                if qty_to_sell < 1:
                    qty_to_sell = 1
                try:
                    result = alpaca_broker.place_order(p["symbol"], "SELL", qty_to_sell, "market")
                    actions_taken.append({"symbol": p["symbol"], "action": "REDUCED_30%", "qty_sold": qty_to_sell})
                    logger.warning(f"[REVERSAL] Position réduite 30%: {p['symbol']} -{qty_to_sell}")
                except Exception as e:
                    actions_taken.append({"symbol": p["symbol"], "action": "ERROR", "error": str(e)})

    except Exception as e:
        return {"check": check, "actions": [], "message": f"Erreur: {e}"}

    return {
        "check": check,
        "actions": actions_taken,
        "message": f"{len(actions_taken)} actions exécutées — niveau {check['level']}",
    }
