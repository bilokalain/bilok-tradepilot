# Bilok-TradePilot — Contexte Projet pour Claude Code

## Vue d'ensemble

Bilok-TradePilot est un système de trading automatisé full-stack organisé en pipeline de 6 modules enchaînés automatiquement avec feedback loop.

```
[ Scanner ] → [ Analyseur ] → [ Scoring ] → [ Exécution ] → [ Gestion Portefeuille ] → [ Suivi Rentabilité ]
     ↑_____________________________________________________________feedback loop____________________________|
```

---

## Stack Technique

| Couche | Technologie | Rôle |
|--------|------------|------|
| Frontend | React + TailwindCSS + Recharts | Dashboard temps réel |
| Backend | Python FastAPI | API REST + WebSockets |
| Pipeline | Celery + Redis | Orchestration tâches en chaîne |
| Base de données | PostgreSQL + InfluxDB | Trades, portefeuille, séries temporelles |
| Broker API | CCXT / Alpaca | Ordres réels ou simulés |
| Données marché | Yahoo Finance / Binance / Alpha Vantage | OHLCV et fondamentaux |
| ML / NLP | PyTorch (Metal/MPS) + FinBERT + CNN ResNet18 | Sentiment + patterns graphiques |

**Environnement local : MacBook M3** → GPU via Metal/MPS, RAM unifiée CPU/GPU.

---

## Architecture des Modules

### Module 1 — Scanner de Marché
Filtre les actifs selon **9 critères orthogonaux** :

1. **Corrélation** — Matrice multi-temporelle (5 horizons : jour/semaine/mois/trimestre/année). Détecte les décrochages sectoriels et ruptures de corrélation.
2. **Sentiment** — Score composite de 5 sources : influenceurs Twitter/X, rumeurs, signaux de retournement, NLP FinBERT (discours Fed / earnings), options smart money.
3. **Analyse Technique** — 6 familles (Tendance, Momentum, Volatilité, Volume, Structure de Prix, Chandeliers) + Multi-Timeframe Analysis.
4. **Génome Explosif** — ADN comportemental de l'actif : 5 phases de cycle, sismographe (6 micro-signaux), mémoire fractale (cosine similarity), réseau de contagion inter-actifs.
5. **Capital Institutionnel (IPI)** — SEC 13F, dark pools, options flow institutionnel, short interest / squeeze setups.
6. **Vélocité Fondamentale (IVF)** — Accélération du CA, expansion des marges, révisions analystes, surprise earnings répétée.
7. **Macro Tailwind (MTS)** — Phase du cycle économique, régime de taux, force du dollar (DXY), liquidité globale.
8. **Topologie Sociale (SGI)** — Adoption communauté, qualité discussions, Network Effect (Loi de Metcalfe pour crypto).
9. **Unicité du Signal (SUS)** — Crowding score, novelty score, timeframe neglect, complexity premium.

**Score Scanner Final** = combinaison pondérée des 9 critères, avec vetos croisés (MTS < -60, SUS < 25, IPI < -60).

**Matrice de sélection adaptative** : les poids des 9 critères s'ajustent automatiquement selon 5 axes contextuels :
- Classe d'actif (crypto / actions US / forex / matières premières)
- Régime de marché (bull / bear / range / crise / transition)
- Horizon de trading (scalp / swing / position / investissement)
- Phase du cycle macro (expansion / pic / contraction / creux)
- Capitalisation (mega / mid / small / micro cap)

### Module 2 — Analyseur de Stratégies
- Détection **probabiliste** du régime de marché (pas binaire)
- Stratégies adaptatives : Trend Following, Mean Reversion, Breakout, Momentum Adaptatif, Microstructure carnet d'ordres, CNN Pattern Recognition
- Matrice performance régime → stratégie, mise à jour hebdomadaire
- Anticipation des catalyseurs (calendrier économique, earnings, crypto events)
- Stratégies inter-marchés Lead-Lag détectées automatiquement
- **Strategy Decay** : détection et quarantaine des stratégies qui perdent leur edge

### Module 3 — Moteur de Scoring
- Score Bayésien Adaptatif (prior historique + mise à jour contexte actuel)
- Score de Qualité du Contexte (SQC) : liquidité, heure, proximité événement
- Signal Shelf Life : durée de vie estimée du signal → type d'ordre optimal
- Priorisation Kelly Généralisé inter-actifs (corrélations portefeuille)
- Output : **Thèse de Trade complète** (direction, score, sizing Kelly, entrée, SL, TP1/TP2, ratio R:R)

### Module 4 — Exécution des Ordres
- Algorithme TWAP/VWAP adaptatif
- Scaling in progressif (3 tranches : 40% / 35% / 25%)
- Smart Order Routing multi-exchanges
- Gestion dynamique post-entrée (trailing stop, réduction préventive)
- Correction automatique des biais comportementaux (disposition, revenge trading, FOMO, over-trading)

### Module 5 — Gestion du Portefeuille
- Risk Parity Dynamique : répartition égale du risque (pas du capital)
- Stress Testing temps réel : scénarios historiques (Mars 2020, 2022, Black Swan crypto)
- Frontière Efficiente Dynamique : recalculée toutes les 4 heures
- Gestion de la liquidité de sortie (Liquidation Score)
- Détection régime portefeuille : ALPHA / BETA / STRESS
- Optimisation fiscale (Tax Loss Harvesting, Long Term Capital Gains)

### Module 6 — Suivi de Rentabilité
- Attribution causale P&L : scanner / timing / sizing / sortie / régime / friction
- Simulation Monte Carlo (10 000 runs / nuit) → percentiles 10/50/90 + P(ruine)
- Early Warning System (EWS) : 5 indicateurs, 4 niveaux d'alerte → pause automatique
- Analyse comparative multi-benchmark (Buy&Hold, 60/40, momentum simple...)
- Rapport d'amélioration continue hebdomadaire
- **Meta-Score** santé du système (0-100) → pilote le niveau d'engagement du pipeline

---

## Architecture Base de Données

5 couches dans PostgreSQL + InfluxDB :

1. **Raw Market Data** — `assets`, `ohlcv_daily`, `ohlcv_1h`, `ohlcv_5min`
2. **Features Précalculées** — `features_daily` (tous les indicateurs + scores des 9 critères)
3. **Génome des Actifs** — `asset_genome` (ADN comportemental, une ligne par actif, MAJ hebdo)
4. **Signaux et Décisions** — `signals`, `orders`
5. **Trades et Performance** — `positions`, `performance_daily`

**Horizon de données recommandé :**
- 20-30 ans daily pour la saisonnalité
- 10 ans daily pour le génome, walk-forward, corrélations
- 2 ans intraday pour AT court terme et microstructure

**Walk-forward testing** : fenêtre glissante 5 ans train + 1 an test, répétée sur 10 ans.

---

## Configuration Locale MacBook M3

```python
import torch
device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
# → Device utilisé : mps
```

**Services locaux :**
```bash
brew services start postgresql@15
brew services start redis
brew services start influxdb
# Empêcher la mise en veille
caffeinate -s
```

**Workers Celery selon modèle M3 :**
- M3 standard (8 cœurs) → 4 workers
- M3 Pro (12 cœurs) → 6 workers
- M3 Max (16 cœurs) → 8 workers

**Optimisation Pandas ARM :**
```python
import pandas as pd
pd.options.mode.dtype_backend = 'pyarrow'
```

---

## Plan de Développement

### Phase 1 — Prototype Paper Trading (mois 1-4) — ~100-200$/mois
- Backend FastAPI + BDD + pipeline Celery
- Module 1 Scanner (corrélation + AT, données gratuites)
- Module 1 Sentiment (Reddit + NewsAPI + sources gratuites)
- Modules 2 et 3 (stratégies + scoring)
- Interface dashboard de base
- Backtesting + validation out-of-sample

### Phase 2 — Live Trading Basique (mois 5-8) — ~600-1300$/mois
- Module 4 Exécution live (Alpaca ou Binance)
- Module 5 Gestion portefeuille complète
- Module 6 Suivi rentabilité + alertes
- Données sentiment payantes (Apify + NewsAPI Pro)
- Interface web complète

### Phase 3 — Scaling (mois 9+) — selon performance prouvée
- Broker supplémentaire (Interactive Brokers)
- RavenPack / sentiment professionnel
- Twitter/X API Pro si edge sentiment prouvé

**Règle d'or : ne jamais dépenser plus en infra que ce que le système génère.**

---

## Fichiers et Structure du Projet

```
tradepilot/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── modules/
│   │   ├── scanner/             # Module 1 — 9 critères
│   │   ├── analyser/            # Module 2 — stratégies adaptatives
│   │   ├── scoring/             # Module 3 — thèse de trade
│   │   ├── execution/           # Module 4 — ordres
│   │   ├── portfolio/           # Module 5 — gestion portefeuille
│   │   ├── performance/         # Module 6 — suivi rentabilité
│   ├── models/                  # ML : FinBERT, CNN ResNet18
│   ├── database/                # SQLAlchemy models + migrations Alembic
│   ├── tasks/                   # Celery tasks
├── frontend/
│   ├── src/                     # React + TailwindCSS + Recharts
├── scripts/
│   ├── load_historical_data.py  # Chargement initial données historiques
│   ├── update_daily.py          # MAJ quotidienne automatique (22h)
├── CLAUDE.md                    # Ce fichier
```

---

## Conventions de Code

- Python 3.11, FastAPI, SQLAlchemy 2.0
- Toujours utiliser `device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')`
- Pandas avec backend PyArrow pour les performances ARM
- Scores toujours entre 0 et 100 (ou -100 et +100 pour les indices directionnels)
- Chaque module reçoit en entrée l'output du module précédent + feedback loop du Module 6
- Logging structuré pour chaque signal généré (attribution causale Module 6)

---

## Ressources et APIs

| Service | Usage | Coût |
|---------|-------|------|
| Yahoo Finance (yfinance) | Prix historiques actions | Gratuit |
| Binance API | Prix crypto + OHLCV | Gratuit |
| Alpha Vantage | Données marché | 0-50$/mois |
| Polygon.io | Données qualité | 29-199$/mois |
| Reddit API | Sentiment retail | Gratuit |
| NewsAPI | Flux actualités | 0-449$/mois |
| Stocktwits API | Sentiment traders | 0-99$/mois |
| Google Trends (pytrends) | Tendances recherche | Gratuit |
| FRED API | Données macro (taux, M2, VIX) | Gratuit |
| Unusual Whales | Dark pools + options flow | 50-200$/mois |
| WhaleWisdom / SEC EDGAR | 13F hedge funds | 0-200$/mois |
| Glassnode / Dune Analytics | On-chain crypto | 29$/mois / Gratuit |
