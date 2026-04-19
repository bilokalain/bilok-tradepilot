"""API endpoints pour le pipeline Celery"""

from fastapi import APIRouter

from backend.tasks.pipeline import (
    run_full_pipeline, run_data_update, run_light_pipeline,
    task_run_scanner, task_update_market_data,
)

router = APIRouter()


@router.post("/run")
def trigger_full_pipeline():
    """Lance le pipeline complet manuellement."""
    result = run_full_pipeline()
    return {
        "status": "pipeline_started",
        "task_id": result.id,
        "message": "Pipeline complet lancé : Data → Scanner → Analyseur → Scoring → Exécution → Portefeuille → Performance",
    }


@router.post("/update-data")
def trigger_data_update():
    """Lance uniquement la mise à jour des données."""
    result = run_data_update()
    return {
        "status": "data_update_started",
        "task_id": result.id,
    }


@router.post("/run-light")
def trigger_light_pipeline():
    """Lance le pipeline léger (sans scanner) — Analyseur → Scoring → Exécution → Portfolio → Performance."""
    result = run_light_pipeline()
    return {
        "status": "light_pipeline_started",
        "task_id": result.id,
        "message": "Pipeline léger lancé : Corrélation → Analyseur → Scoring → Exécution → Portefeuille → Performance (sans scanner)",
    }


@router.post("/scan")
def trigger_scan():
    """Lance uniquement le scanner."""
    result = task_run_scanner.delay()
    return {"status": "scan_started", "task_id": result.id}


@router.get("/status/{task_id}")
def get_task_status(task_id: str):
    """Vérifie le statut d'une tâche Celery."""
    from backend.tasks.celery_app import celery_app
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
