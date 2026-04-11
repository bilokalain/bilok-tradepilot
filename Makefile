# TradePilot — Commandes de développement

.PHONY: help infra backend worker beat frontend install

help: ## Affiche l'aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Infrastructure ---
infra: ## Lance PostgreSQL + Redis + InfluxDB (Docker)
	docker compose up -d

infra-stop: ## Arrête l'infrastructure
	docker compose down

# --- Backend ---
backend: ## Lance le serveur FastAPI
	source .venv/bin/activate && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

worker: ## Lance le worker Celery (4 workers)
	source .venv/bin/activate && celery -A backend.tasks.celery_app worker --loglevel=info --concurrency=4

beat: ## Lance le scheduler Celery Beat (tâches planifiées)
	source .venv/bin/activate && celery -A backend.tasks.celery_app beat --loglevel=info

# --- Frontend ---
frontend: ## Lance le serveur Vite (React)
	cd frontend && npm run dev

# --- Installation ---
install: ## Installe toutes les dépendances
	python3 -m venv .venv
	source .venv/bin/activate && pip install -r requirements.txt && pip install psycopg2-binary alpaca-py
	cd frontend && npm install

# --- Base de données ---
db-migrate: ## Crée une migration Alembic (msg="description")
	source .venv/bin/activate && alembic revision --autogenerate -m "$(msg)"

db-upgrade: ## Applique les migrations
	source .venv/bin/activate && alembic upgrade head

# --- Données ---
load-data: ## Charge les données historiques daily (2 ans)
	source .venv/bin/activate && python scripts/load_historical_data.py

load-intraday: ## Charge les données intraday 1H
	source .venv/bin/activate && python scripts/load_intraday_data.py

# --- Pipeline ---
pipeline: ## Lance le pipeline complet via l'API
	curl -s -X POST http://localhost:8000/api/pipeline/run | python3 -m json.tool

scan: ## Lance uniquement le scanner
	curl -s -X POST http://localhost:8000/api/pipeline/scan | python3 -m json.tool

# --- Démarrage complet ---
start: ## Lance tout (infra + backend + frontend)
	@echo "1. Lancer Docker: make infra"
	@echo "2. Lancer backend: make backend"
	@echo "3. Lancer frontend: make frontend"
	@echo "4. (optionnel) Lancer Celery: make worker & make beat"
