"""Notifications par email — statut du pipeline

Envoie un email à chaque étape du pipeline :
- MAJ données terminée
- Scan complet terminé (avec top signaux)
- Monte Carlo terminée
- Position fermée (SL/TP atteint)
- Nouveau signal exécuté depuis la queue

Utilise smtplib avec Gmail App Password.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger("tradepilot.notifications")

# Configuration email
EMAIL_TO = "bilokalain@gmail.com"
EMAIL_FROM = "biloktradepilot@gmail.com"  # Créer ce compte ou utiliser le vôtre
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Pour l'instant on utilise un fallback fichier si l'email n'est pas configuré
NOTIF_LOG = "data/notifications.log"


def send_notification(subject: str, body: str, html: bool = False):
    """Envoie une notification par email ou la log dans un fichier."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Essayer l'email
    try:
        from backend.config.settings import settings
        smtp_password = getattr(settings, "SMTP_PASSWORD", "")

        if smtp_password:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[Bilok-TradePilot] {subject}"
            msg["From"] = EMAIL_FROM
            msg["To"] = EMAIL_TO

            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_FROM, smtp_password)
                server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

            logger.info(f"[EMAIL] Envoyé : {subject}")
            return True
    except Exception as e:
        logger.warning(f"[EMAIL] Échec envoi : {e}")

    # Fallback : sauvegarder dans un fichier
    try:
        from pathlib import Path
        Path("data").mkdir(exist_ok=True)
        with open(NOTIF_LOG, "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"[{timestamp}] {subject}\n")
            f.write(f"{'='*60}\n")
            f.write(body + "\n")
        logger.info(f"[NOTIF] Sauvegardé dans {NOTIF_LOG} : {subject}")
    except Exception:
        pass

    return False


# ============================================================
# Templates de notifications
# ============================================================

def notify_data_update(updated: int, assets: int):
    send_notification(
        "MAJ Données terminée",
        f"""Mise à jour des données marché terminée.

Nouvelles barres : {updated}
Actifs mis à jour : {assets}
Heure : {datetime.utcnow().strftime('%H:%M UTC')}

Le scan complet va démarrer dans 30 minutes.
"""
    )


def notify_scan_complete(num_assets: int, top_signals: list[dict]):
    signals_text = ""
    for s in top_signals[:10]:
        signals_text += f"  {s.get('symbol', '?'):12} Score={s.get('score', 0):.1f}  {s.get('direction', '?')}\n"

    send_notification(
        f"Scan terminé — {len(top_signals)} signaux GO",
        f"""Scan complet des {num_assets} actifs terminé.

Signaux GO ({len(top_signals)}) :
{signals_text if signals_text else '  Aucun signal GO aujourd\'hui.'}

Connectez-vous pour exécuter : http://localhost:5173/execution
"""
    )


def notify_monte_carlo(p_ruin: float, p50: float, meta_score: float):
    send_notification(
        f"Monte Carlo — Meta-Score {meta_score:.0f}/100",
        f"""Simulation Monte Carlo nocturne terminée.

Percentile 50 (médiane) : ${p50:.0f}
Probabilité de ruine : {p_ruin:.1f}%
Meta-Score : {meta_score:.0f}/100

{'⚠️ ATTENTION : P(ruine) élevée !' if p_ruin > 5 else '✅ Risque de ruine acceptable.'}
"""
    )


def notify_position_closed(symbol: str, reason: str, pnl: float, direction: str):
    emoji = "✅" if pnl > 0 else "❌"
    send_notification(
        f"{emoji} {symbol} fermé ({reason}) — P&L ${pnl:+.2f}",
        f"""Position fermée automatiquement.

Actif : {symbol}
Direction : {direction}
Raison : {reason}
P&L : ${pnl:+.2f}

{'Un nouveau signal de la file d\'attente sera exécuté si disponible.' if reason == 'TAKE_PROFIT' or reason == 'STOP_LOSS' else ''}
"""
    )


def notify_queue_execution(symbol: str, direction: str, entry_price: float):
    send_notification(
        f"File d'attente → {symbol} {direction} exécuté",
        f"""Nouveau trade exécuté depuis la file d'attente.

Actif : {symbol}
Direction : {direction}
Prix d'entrée : ${entry_price:.2f}
Source : Remplacement automatique (position précédente fermée)
"""
    )


def notify_weekly_report(report: dict):
    summary = report.get("summary", {})
    meta = report.get("meta_score", {})
    recs = report.get("recommendations", [])

    recs_text = "\n".join(f"  [{r['priority']}] {r['action']} — {r['reason']}" for r in recs)

    send_notification(
        f"Rapport hebdo — P&L ${summary.get('weekly_pnl', 0):+.2f} | Meta-Score {meta.get('meta_score', 0):.0f}",
        f"""RAPPORT HEBDOMADAIRE Bilok-TradePilot

Période : {report.get('period', {}).get('week_start')} → {report.get('period', {}).get('week_end')}

Equity : ${summary.get('equity', 0):.2f}
P&L semaine : ${summary.get('weekly_pnl', 0):+.2f} ({summary.get('weekly_return_pct', 0):.3f}%)
Positions : {summary.get('total_positions', 0)}

Meta-Score : {meta.get('meta_score', 0):.0f}/100 — {meta.get('engagement', '?')}

Recommandations :
{recs_text}

Détails : http://localhost:5173/performance
"""
    )


def notify_pipeline_error(task_name: str, error: str):
    send_notification(
        f"⚠️ Erreur Pipeline — {task_name}",
        f"""Une erreur est survenue dans le pipeline.

Tâche : {task_name}
Erreur : {error}
Heure : {datetime.utcnow().strftime('%H:%M UTC')}

Le pipeline continuera à la prochaine exécution planifiée.
"""
    )
