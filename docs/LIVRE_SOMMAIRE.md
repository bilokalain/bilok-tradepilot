# BILOK-TRADEPILOT — Le Système

## Architecture d'un Pipeline de Trading Automatisé à 6 Modules avec Feedback Loop

---

# SOMMAIRE DÉTAILLÉ

---

## AVANT-PROPOS
- Pourquoi ce livre
- À qui s'adresse-t-il
- Ce que ce livre n'est pas (disclaimer : pas un conseil financier)

## INTRODUCTION — La Philosophie du Système
- Le problème : pourquoi 90% des traders retail perdent
- La solution : remplacer les émotions par un pipeline systématique
- Vue d'ensemble : 6 modules enchaînés avec feedback loop
- Le principe de la chaîne : chaque module filtre, affine et valide
- De la thèse à la performance : le parcours d'un signal

```
[ Thèses ] → [ Scanner ] → [ Analyseur ] → [ Scoring ] → [ Exécution ] → [ Portfolio ] → [ Performance ]
     ↑_____________________________________________feedback loop______________________________________________|
```

---

## PARTIE I — LA VISION

### Section 1 — Les Thèses de Trading

#### Chapitre 1 : Qu'est-ce qu'une thèse de trading
- Définition : une conviction directionnelle structurée
- La différence entre une opinion et une thèse
- Les 4 composantes d'une thèse : thème, direction, horizon, conviction
- Exemples : "L'IA va transformer la santé", "Le cycle crypto repart"

#### Chapitre 2 : Construire une thèse solide
- L'analyse top-down : macro → secteur → actif
- Les catalyseurs : ce qui transforme une idée en mouvement de prix
- L'horizon temporel : scalp, swing, position, investissement
- La conviction : quantifier sa certitude (0-100)

#### Chapitre 3 : Intégrer les thèses dans le pipeline
- Comment le système amplifie les signaux alignés avec vos thèses
- Le filtre thématique : booster les actifs cohérents
- Quand une thèse est invalidée par les données
- L'humilité systématique : le modèle a le dernier mot

---

## PARTIE II — LE SCANNER (Module 1)

### Section 2 — Le Scanner de Marché : Filtrer le Bruit

#### Chapitre 4 : Architecture du Scanner
- Le problème : 10 000+ actifs, comment trouver les bons ?
- Le principe des 10 critères orthogonaux
- Pourquoi orthogonaux : chaque critère mesure une dimension indépendante
- La matrice de pondération adaptative
- Les 5 axes d'adaptation : classe d'actif, régime, horizon, cycle macro, capitalisation

#### Chapitre 5 : Critère 1 — Analyse Technique
- Les 7 familles d'indicateurs (20 indicateurs au total)
  - Tendance : SMA 20/50/200, ADX, alignement des moyennes
  - Momentum : RSI, MACD, Williams %R, CCI, ROC
  - Volatilité : Bandes de Bollinger, ATR
  - Volume : OBV, Chaikin Money Flow, VWAP, ratio volume
  - Structure : Points Pivots (PP, R1-R3, S1-S3)
  - Divergences : détection automatique RSI/MACD vs prix
  - Force de tendance : ADX et interprétation
- Le score composite pondéré (0-100)
- Multi-Timeframe Analysis V2 : Weekly, Daily, 4H, 1H
  - Pondération hiérarchique (Weekly 35%, Daily 30%, 4H 20%, 1H 15%)
  - Le concept d'alignement des timeframes
  - Construction des barres 4H et Weekly depuis les données existantes

#### Chapitre 6 : Critère 2 — Corrélation
- La matrice de corrélation multi-temporelle
- Les 5 horizons : jour (5j), semaine (20j), mois (60j), trimestre (260j), année (1300j)
- Détection des ruptures de corrélation
- Les décrochages sectoriels : quand un actif sort du groupe
- Pourquoi la décorrélation est un signal fort

#### Chapitre 7 : Critère 3 — Sentiment
- L'analyse NLP avec FinBERT
- Les sources : Reddit, NewsAPI, flux d'actualités
- Le score de polarité : positif, négatif, neutre
- Le ratio volume de mentions vs qualité
- Les limites du sentiment gratuit vs professionnel

#### Chapitre 8 : Critère 4 — Génome Explosif
- L'ADN comportemental d'un actif
- Les 5 phases de Wyckoff : Accumulation → Markup → Distribution → Markdown → Capitulation
- Le Sismographe : 6 micro-signaux de compression
  - Bollinger Squeeze, contraction volume, spike volume
  - Inside bars, compression ATR, divergence RSI
- La Mémoire Fractale : cosine similarity avec les patterns historiques
- Le Réseau de Contagion inter-actifs

#### Chapitre 9 : Critère 5 — Capital Institutionnel (IPI)
- Détecter les gros acteurs sans les voir
- La ligne d'Accumulation/Distribution
- Le Smart Money Flow : gros volumes sans mouvement de prix
- Les Dark Pools et l'options flow
- Le Short Interest et les setups de squeeze

#### Chapitre 10 : Critère 6 — Vélocité Fondamentale (IVF)
- Ce n'est pas "les fondamentaux sont-ils bons" mais "s'améliorent-ils de plus en plus vite ?"
- L'accélération du chiffre d'affaires sur 8 trimestres
- L'expansion des marges : tendance trimestrielle
- La force relative vs le benchmark
- Les révisions analystes : le consensus monte ou descend ?

#### Chapitre 11 : Critère 7 — Macro Tailwind (MTS)
- Le vent macro souffle-t-il dans le bon sens ?
- La phase du cycle économique : expansion, pic, contraction, creux
- Le régime de taux : accommodant, neutre, restrictif
- L'appétit pour le risque : DXY, VIX, liquidité globale
- L'adaptation par classe d'actif : la macro n'affecte pas la crypto comme les actions

#### Chapitre 12 : Critère 8 — Topologie Sociale (SGI)
- La qualité de la communauté autour de l'actif
- Le ratio Signal/Bruit des discussions
- Le Network Effect (Loi de Metcalfe pour la crypto)
- Le momentum d'intérêt : Google Trends, volume de mentions
- La différence entre buzz et conviction

#### Chapitre 13 : Critère 9 — Unicité du Signal (SUS)
- Le signal que tout le monde voit est déjà dans le prix
- Le Crowding Score : combien d'actifs ont le même pattern ?
- Le Novelty Score : ce comportement est-il inhabituel ?
- Le Timeframe Neglect : visible uniquement sur des TF non-populaires
- Le Complexity Premium : le signal nécessite-t-il une analyse complexe ?

#### Chapitre 14 : Critère 10 — Analyse Fondamentale V2
- Les 8 dimensions professionnelles
  - Valorisation : P/E vs médiane sectorielle, PEG, EV/EBITDA
  - Profitabilité : marges + tendance 8 trimestres
  - Croissance : accélération et point d'inflexion
  - Santé financière : dette, FCF, liquidité + tendance
  - Dividendes : yield et soutenabilité
  - Score Piotroski : 9 critères avec vrais historiques trimestriels
  - Earnings Quality : beat rate, surprises, révisions analystes
  - DCF simplifié : valeur intrinsèque vs prix actuel
- Les comparables sectoriels
- Pourquoi le fondamental pèse seulement 8% dans le scoring

#### Chapitre 15 : Critère 11 — Narrative Momentum
- La force du récit autour d'un mouvement de prix
- Volume acceleration, price momentum, structure de marché
- Breakout detection et momentum persistance
- Quand la narrative s'épuise

#### Chapitre 16 : Le Score Scanner Final
- La combinaison pondérée des 10 critères
- Les vetos croisés : MTS < 20, SUS < 25, IPI < 20 → rejet automatique
- La matrice de sélection adaptative
- Du score à la shortlist : le filtre final

---

## PARTIE III — L'ANALYSEUR (Module 2)

### Section 3 — L'Analyseur de Stratégies : Comment Trader

#### Chapitre 17 : La détection probabiliste du régime
- Pourquoi le régime n'est pas binaire (bull/bear)
- Les 5 régimes : BULL, BEAR, RANGE, CRISIS, TRANSITION
- Les probabilités par régime : un actif peut être 60% bull et 30% range
- Le régime global vs le régime individuel

#### Chapitre 18 : Les 12+ stratégies adaptatives
- Trend Following : surfer la tendance
- Mean Reversion : acheter les excès
- Breakout : capter les ruptures
- Momentum Adaptatif : accélérer avec le mouvement
- Fibonacci : les niveaux de retracement et extension
- Ichimoku : le nuage japonais
- Les stratégies avancées et professionnelles
- La matrice performance régime × stratégie

#### Chapitre 19 : La sélection de stratégie
- Le classement dynamique par régime actuel
- Le Strategy Decay : détecter les stratégies qui perdent leur edge
- La quarantaine automatique
- L'ensemble weighting : combiner plusieurs stratégies

#### Chapitre 20 : Les catalyseurs
- Le calendrier économique et son impact
- Les earnings : avant, pendant, après
- Les événements crypto : halvings, upgrades, régulation
- L'ajustement du signal par proximité de catalyseur

#### Chapitre 21 : Les signaux inter-marchés
- Le Lead-Lag : quand un marché anticipe l'autre
- La rotation sectorielle : suivre l'argent
- Les corrélations dynamiques inter-classes

---

## PARTIE IV — LE SCORING (Module 3)

### Section 4 — Le Moteur de Scoring : La Décision

#### Chapitre 22 : Le Score V2 — Fusion de 8 sources
- Architecture du score composite
- Les 8 composantes et leurs poids
- Le sizing modifier : catalyseurs, corrélation, régime
- Le seuil GO/WAIT/NO_TRADE

#### Chapitre 23 : Le Score Bayésien Adaptatif
- Le prior historique : ce que l'histoire nous dit
- La mise à jour par le contexte actuel
- La confiance du régime comme pondérateur
- L'observation likelihood

#### Chapitre 24 : La Qualité du Contexte (SQC)
- La liquidité du marché
- L'heure de la journée et son impact
- La proximité d'événements
- Le Shelf Life : combien de temps le signal reste valide

#### Chapitre 25 : La Thèse de Trade Complète
- Direction (LONG/SHORT) et justification
- Prix d'entrée optimal
- Stop-Loss : 2 × ATR — pourquoi ce multiple
- Take-Profit 1 et 2 : 3 × ATR — le ratio R:R
- Le sizing Kelly : la fraction optimale du capital

#### Chapitre 26 : Le Sizing Kelly Généralisé
- La formule de Kelly classique
- Le Fractional Kelly (1/4) : pourquoi être conservateur
- Le Kelly inter-actifs avec corrélations
- Les plafonds de sécurité : jamais > 15% du capital

---

## PARTIE V — L'EXÉCUTION (Module 4)

### Section 5 — L'Exécution : Passer à l'Action

#### Chapitre 27 : L'architecture d'exécution
- Le multi-broker : IBKR (live) + Alpaca (paper)
- La priorité IBKR : l'argent réel d'abord
- Le fallback Alpaca : validation en parallèle
- Les Bracket Orders : entrée + SL + TP atomiques

#### Chapitre 28 : Le Scaling d'entrée
- Les 3 tranches : 40% / 35% / 25%
- L'algorithme TWAP/VWAP adaptatif
- Le Smart Order Routing

#### Chapitre 29 : La correction des biais comportementaux
- Le Disposition Effect : couper les gagnants trop tôt
- Le Revenge Trading : doubler après une perte
- Le FOMO : entrer trop tard par peur de rater
- L'Over-Trading : trop de trades, pas assez de conviction
- Comment le système détecte et bloque chaque biais

#### Chapitre 30 : La gestion dynamique post-entrée
- Le Trailing Stop : protéger les gains
- La réduction préventive
- L'Exhaustion Checker : 5 signaux d'essoufflement
  - Momentum ralentit
  - Volume sèche
  - Narrative épuisée
  - RSI en zone extrême
  - P&L stagne
- Les 4 niveaux : FORT → MODÉRÉ → FAIBLE → ÉPUISÉ
- Le Breakeven automatique

#### Chapitre 31 : L'Arbitrage d'Opportunité
- Le concept : EV/jour (Espérance de Valeur par Jour)
- Le classement unifié positions vs signaux
- Le swap recommandé : fermer le faible, ouvrir le fort
- Le coût de friction dans le calcul

#### Chapitre 32 : La file d'attente intelligente
- Maximum de positions simultanées
- La queue triée par score décroissant
- Le remplacement automatique : quand une position se ferme
- La vérification de santé pré-entrée

---

## PARTIE VI — LE PORTEFEUILLE (Module 5)

### Section 6 — La Gestion du Portefeuille : Contrôler le Risque

#### Chapitre 33 : Le Risk Parity Dynamique
- Répartir le risque, pas le capital
- La volatilité comme mesure du risque
- Le rééquilibrage périodique

#### Chapitre 34 : Le Stress Testing
- Les scénarios historiques : Mars 2020, crypto crash 2022, Black Swan
- La simulation en temps réel
- Le Liquidation Score : priorité de sortie

#### Chapitre 35 : La détection de régime portefeuille
- ALPHA : le système surperforme
- BETA : performance normale
- STRESS : drawdown significatif
- Les actions automatiques par régime

#### Chapitre 36 : Le contrôle du Drawdown
- Le calcul depuis le peak equity (pas le capital initial)
- Les 4 niveaux : NORMAL → WARNING → ALERT → CRITICAL
- La réduction automatique de l'exposition
- La VaR (Value at Risk) et ses limites

#### Chapitre 37 : Le Reversal Guard
- La détection de retournement macro
- La protection automatique en cas de signal rouge
- Le pause pipeline : quand le système s'arrête de lui-même

---

## PARTIE VII — LA PERFORMANCE (Module 6)

### Section 7 — Le Suivi de Performance : Apprendre et S'améliorer

#### Chapitre 38 : L'attribution causale du P&L
- Les 6 sources de performance
  - Scanner : a-t-on choisi les bons actifs ?
  - Timing : est-on entré au bon moment ?
  - Sizing : a-t-on mis la bonne taille ?
  - Sortie : a-t-on coupé au bon endroit ?
  - Régime : le contexte macro a-t-il aidé ?
  - Friction : combien ont coûté les commissions et le slippage ?

#### Chapitre 39 : Les métriques professionnelles
- Sharpe Ratio : rendement ajusté au risque
- Sortino Ratio : pénaliser uniquement les pertes
- Calmar Ratio : rendement vs drawdown max
- Profit Factor : gains bruts / pertes brutes
- Win Rate et Expectancy

#### Chapitre 40 : Le Meta-Score
- La santé du système en un chiffre (0-100)
- Les composantes : win rate, Sharpe, régime, EWS
- Les niveaux d'engagement : FULL → NORMAL → PRUDENT → MINIMAL
- Quand le système se met en pause

#### Chapitre 41 : L'Early Warning System (EWS)
- Les 5 indicateurs de danger
- Les 4 niveaux d'alerte : NORMAL → ATTENTION → ALERTE → CRITIQUE
- Les actions automatiques par niveau
- La pause préventive du pipeline

#### Chapitre 42 : Le taux de détection
- Comparer les top movers du jour vs les signaux GO
- Le rapport quotidien de détection
- L'historique sur 30 jours
- L'amélioration continue du scanner

#### Chapitre 43 : Le benchmarking
- vs Buy & Hold SPY
- vs Portefeuille 60/40
- vs Simple Momentum
- La Equity Curve et son interprétation

---

## PARTIE VIII — LA BOUCLE DE FEEDBACK

### Section 8 — L'Apprentissage Autonome : Le Système Apprend

#### Chapitre 44 : La boucle Module 6 → Module 1
- Comment la performance passée ajuste le scanner futur
- Les poids adaptatifs : recalculés automatiquement
- L'accélération des critères qui performent
- La réduction des critères qui échouent

#### Chapitre 45 : Le Scoring Calibrator
- L'ajustement des poids du Score V2
- L'optimisation basée sur le taux de détection
- La stabilité : ne pas sur-réagir aux fluctuations
- Le cooldown : période minimale entre deux ajustements

#### Chapitre 46 : L'Entry Quality Tracker
- Quels signaux de santé prédisent le succès ?
- Le seuil optimal appris automatiquement
- Le risque d'overfitting et comment l'éviter

#### Chapitre 47 : Le Strategy Decay
- Détecter quand une stratégie perd son edge
- La quarantaine automatique
- La réhabilitation : quand remettre une stratégie en service

---

## PARTIE IX — L'INFRASTRUCTURE

### Section 9 — L'Architecture Technique

#### Chapitre 48 : Le Stack Technique
- Python FastAPI (backend)
- React + TailwindCSS (frontend)
- PostgreSQL + Redis + InfluxDB (données)
- Celery (orchestration pipeline)
- Docker (services)

#### Chapitre 49 : Le Pipeline Celery
- La chaîne des 7 tâches
- Le scheduling : quand chaque module tourne
- Le scan intraday : 15h45 et 18h Paris
- Le lock Redis : empêcher les doublons
- L'engine DB partagé : pas de fuite mémoire

#### Chapitre 50 : Le Multi-Broker
- L'intégration IBKR (ib_insync)
- L'intégration Alpaca
- Le SYMBOL_MAPPING pour les marchés européens
- Les Client IDs centralisés
- La validation croisée des prix

#### Chapitre 51 : Le Déploiement
- Cloudflare Tunnel pour l'accès distant
- Vercel pour le frontend
- Le domaine custom (bilok-tradepilot.be)
- Le keep-alive et la résilience

#### Chapitre 52 : La Robustesse
- Les guards NaN et division par zéro
- Le logging explicite (pas de except: pass)
- Le sizing centralisé
- Les frais de transaction dans le backtester
- Le drawdown depuis le peak

---

## PARTIE X — LA PRATIQUE

### Section 10 — Le Trading au Quotidien

#### Chapitre 53 : La journée type
- 00h00 : le pipeline nocturne tourne
- 09h00 : consultation du dashboard et des signaux
- 15h45 : scan intraday à l'ouverture US
- 18h00 : deuxième scan mid-séance
- 22h00 : le pipeline complet se relance

#### Chapitre 54 : Lire le Dashboard
- Les métriques clés en un coup d'oeil
- Les top movers et leur interprétation
- Le statut du pipeline
- Les alertes EWS

#### Chapitre 55 : Prendre une décision
- Analyser un signal GO : les 10 critères à vérifier
- L'Arbitrage d'Opportunité : garder ou swapper
- Le rapport de détection : le système voit-il les bons mouvements ?
- Quand ignorer le système (et pourquoi c'est rarement une bonne idée)

#### Chapitre 56 : Gérer les pertes
- Le drawdown est normal : les statistiques historiques
- Les niveaux de contrôle automatique
- La psychologie : laisser le système gérer
- Le journal de trading automatique

---

## CONCLUSION

#### Chapitre 57 : Les limites du modèle
- Ce que le système ne peut pas faire
- Les risques de l'automatisation
- L'importance de la surveillance humaine
- Les marchés changent : l'adaptation permanente

#### Chapitre 58 : La roadmap
- Phase 1 : Paper trading (validé)
- Phase 2 : Live trading basique (en cours)
- Phase 3 : Scaling (futur)
- Les améliorations envisagées

#### Chapitre 59 : La règle d'or
- Ne jamais dépenser plus en infra que ce que le système génère
- La patience comme stratégie
- Le compound effect : le temps est votre allié

---

## ANNEXES

### Annexe A — Glossaire des termes techniques
### Annexe B — Les 20 indicateurs techniques en détail
### Annexe C — Les formules mathématiques (Kelly, Sharpe, Piotroski, DCF)
### Annexe D — Les paramètres configurables du système
### Annexe E — Les API et sources de données
### Annexe F — FAQ : questions fréquentes

---

## MENTIONS LÉGALES

*Ce document est fourni à titre informatif et éducatif uniquement. Il ne constitue en aucun cas un conseil en investissement, une recommandation d'achat ou de vente, ni une incitation à effectuer une quelconque transaction financière. Les performances passées ne préjugent pas des performances futures. Tout investissement comporte des risques de perte en capital. L'auteur et Bilok-TradePilot déclinent toute responsabilité quant aux décisions prises sur la base de ce document. Consultez un conseiller financier agréé avant toute décision d'investissement.*

---

**Bilok-TradePilot** — *Le Système*
© 2026 Alain Bilok — Tous droits réservés
