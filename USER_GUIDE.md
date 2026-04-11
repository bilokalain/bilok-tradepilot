# TradePilot — Guide Utilisateur Complet

> **Votre copilote de trading intelligent.** Ce guide vous explique comment lire, comprendre et utiliser chaque module de TradePilot, même si vous n'avez aucune expérience en trading.

---

## Table des matières

1. [Premiers pas](#1-premiers-pas)
2. [Module 1 — Scanner de Marché](#2-module-1--scanner-de-marché)
3. [Module 2 — Analyseur de Stratégies](#3-module-2--analyseur-de-stratégies)
4. [Module 3 — Moteur de Scoring](#4-module-3--moteur-de-scoring)
5. [Module 4 — Exécution des Ordres](#5-module-4--exécution-des-ordres)
6. [Module 5 — Gestion du Portefeuille](#6-module-5--gestion-du-portefeuille)
7. [Module 6 — Suivi de Rentabilité](#7-module-6--suivi-de-rentabilité)
8. [La page Détail Actif](#8-la-page-détail-actif)
9. [Glossaire](#9-glossaire)
10. [Paramètres et Configuration](#10-paramètres-et-configuration)

---

## 1. Premiers pas

### Connexion

- Ouvrez **http://localhost:5173** dans votre navigateur
- Connectez-vous avec : `admin@tradepilot.local` / `tradepilot2024`
- Vous arrivez sur le **Dashboard** — la vue d'ensemble de tout le système

### Ce que vous voyez sur le Dashboard

| Élément | Ce que ça signifie |
|---------|-------------------|
| **Actifs scannés** | Nombre d'actifs analysés (51 = actions, crypto, forex, matières premières) |
| **Score moyen** | La "note" moyenne de tous les actifs (0-100). Au-dessus de 60 = le marché est globalement favorable |
| **Signaux GO** | Nombre d'actifs qui remplissent TOUTES les conditions pour trader. C'est le chiffre le plus important |
| **Régime** | L'état général du marché : Haussier (les prix montent), Baissier (ils descendent), Latéral (ils stagnent) |
| **Santé système** | Note de 0 à 100 de la fiabilité du système lui-même. En dessous de 40 = le système se met en pause |

### Le pipeline en un mot

```
Vous avez 51 actifs → Le scanner les note sur 9 critères → L'analyseur choisit
la bonne stratégie → Le scoring décide si on y va → L'exécution passe l'ordre
→ Le portefeuille gère le risque → La rentabilité vérifie que tout fonctionne
→ Le feedback améliore le scanner pour la prochaine fois
```

---

## 2. Module 1 — Scanner de Marché

**Page : Scanner** | **Ce qu'il fait :** Note chaque actif sur 9 dimensions indépendantes

Le scanner est le **filtre d'entrée**. Sur 51 actifs, il identifie ceux qui méritent votre attention. Chaque actif reçoit une note globale de 0 à 100.

### Les 9 critères expliqués

#### 1. Analyse Technique (AT) — "Le prix, qu'est-ce qu'il fait ?"

C'est l'étude des graphiques de prix. On regarde :

| Indicateur | Ce qu'il mesure | Comment le lire |
|-----------|----------------|-----------------|
| **SMA 20/50/200** | Les moyennes mobiles (tendance lissée) | Prix > SMA 200 = tendance haussière long terme |
| **RSI** | Le momentum (0-100) | > 70 = suracheté (risque de baisse), < 30 = survendu (opportunité d'achat) |
| **MACD** | L'accélération de la tendance | Histogramme positif = la hausse accélère |
| **Bollinger** | La volatilité | Prix qui touche la bande basse = possible rebond |
| **ATR** | La volatilité en dollars | Sert à calculer les stop-loss |
| **Stochastic** | Le timing d'entrée | Croisement en zone basse = signal d'achat |
| **OBV** | Le volume confirme-t-il le mouvement ? | OBV monte + prix monte = mouvement sain |

**Score AT > 70** = Forte dynamique, les indicateurs sont alignés.
**Score AT < 40** = Dynamique faible ou baissière.

#### 2. Corrélation — "Cet actif se démarque-t-il ?"

Compare le comportement de l'actif avec les autres. Un actif qui se **découple** du groupe est intéressant — quelque chose d'unique se passe.

**Score > 70** = L'actif a un comportement très indépendant.
**Score ~ 50** = Comportement normal, suit le marché.

#### 3. Sentiment — "Qu'est-ce que les gens en disent ?"

Analyse ce qui se dit sur Reddit, les forums et les actualités. Utilise **FinBERT** (intelligence artificielle spécialisée en finance) pour comprendre si les gens sont optimistes ou pessimistes.

**Score > 70** = Sentiment très positif, beaucoup de buzz optimiste.
**Score ~ 50** = Neutre, pas d'opinion dominante.
**Score < 35** = Sentiment négatif — prudence ou opportunité contrariante.

#### 4. Génome Explosif — "L'actif va-t-il exploser ?"

Analyse l'ADN comportemental de l'actif pour détecter les configurations **pré-explosives** :

| Composante | Ce qu'elle cherche |
|-----------|-------------------|
| **Phase de cycle** | Accumulation (phase 1) = les gros investisseurs achètent discrètement |
| **Sismographe** | 6 micro-signaux : compression Bollinger, contraction volume, inside bars... |
| **Mémoire fractale** | L'actif répète-t-il un pattern qui a précédé une explosion dans le passé ? |

**Score > 70** = Configuration explosive ! Plusieurs micro-signaux actifs.
**Score ~ 50** = Rien de spécial.

#### 5. Capital Institutionnel (IPI) — "Les gros achètent-ils ?"

Détecte si les fonds d'investissement et les banques achètent ou vendent discrètement :

| Signal | Ce que ça signifie |
|--------|-------------------|
| **Ligne A/D en hausse** | Plus d'argent entre qu'il n'en sort = accumulation |
| **Smart Money Flow** | Gros volumes sans mouvement de prix = quelqu'un accumule en silence |
| **Anomalie de volume** | Volume > 2x la normale = activité institutionnelle probable |

**Score > 70** = Les institutionnels achètent. Suivez l'argent intelligent.
**Score < 40** = Distribution — les gros vendent.

#### 6. Vélocité Fondamentale (IVF) — "Les fondamentaux accélèrent-ils ?"

Ne regarde pas si les fondamentaux sont "bons" mais si ils **s'améliorent de plus en plus vite** :

- **Accélération du prix** = le momentum accélère
- **Force relative** = l'actif bat-il le marché ?
- **Gaps de surprise** = les résultats surprennent-ils positivement à répétition ?

**Score > 70** = Accélération fondamentale forte.
**Score < 40** = Décélération — l'actif perd de l'élan.

#### 7. Macro Tailwind (MTS) — "Le vent macro souffle-t-il dans le bon sens ?"

Évalue l'environnement économique global :

| Facteur | Source | Impact |
|---------|--------|--------|
| **Cycle économique** | SPY (proxy de l'économie US) | Expansion = favorable |
| **Régime de taux** | TLT (obligations) ou FRED API | Taux en baisse = favorable pour les actions |
| **Appétit pour le risque** | Ratio SPY/GLD | SPY > GLD = risk-on (favorable) |
| **VIX** | FRED API (indice de peur) | VIX < 20 = marché calme |

**Score > 70** = Environnement macro très favorable.
**Score < 40** = Vent contraire — conditions défavorables.

#### 8. Topologie Sociale (SGI) — "La communauté est-elle de qualité ?"

Mesure la **qualité** des discussions, pas juste la quantité :

- **Signal/Bruit** = les gens disent-ils des choses utiles ou c'est du bruit ?
- **Network Effect** = pour les crypto : plus d'utilisateurs = plus de valeur
- **Momentum d'intérêt** = l'intérêt est-il en hausse ou en chute ?

**Score > 70** = Communauté active et de qualité.

#### 9. Unicité du Signal (SUS) — "Est-ce que tout le monde voit la même chose ?"

**C'est le critère le plus subtil.** Un signal que tout le monde voit est déjà dans le prix = pas d'avantage.

| Composante | Ce qu'elle mesure |
|-----------|-------------------|
| **Crowding** | Combien d'actifs ont le même score ? Moins il y en a, mieux c'est |
| **Novelty** | Le comportement est-il inhabituel historiquement ? |
| **Timeframe Neglect** | Le signal est-il visible uniquement sur des timeframes que personne ne regarde ? |
| **Complexity Premium** | Faut-il une analyse complexe pour voir le signal ? Si oui, peu de gens l'ont vu |

**Score > 70** = Signal unique. Vous avez un avantage informationnel.
**Score < 35** = Signal crowdé. Tout le monde l'a vu — pas d'avantage.

### Matrice de poids adaptatifs

Les 9 critères n'ont **pas le même poids** selon la classe d'actif :

| Critère | Actions US | Crypto | Forex | Commodities |
|---------|-----------|--------|-------|-------------|
| AT | 18% | 15% | 20% | 18% |
| IPI | **15%** | 5% | 5% | 10% |
| Sentiment | 8% | **15%** | 5% | 8% |
| MTS | 10% | 7% | **20%** | **15%** |
| SGI | 5% | **18%** | 2% | 5% |

*Le système adapte automatiquement les poids. Pour les crypto, le sentiment et la communauté pèsent plus. Pour le forex, la macro domine.*

### Vetos

Certains critères peuvent **bloquer** un actif même si son score global est bon :

| Critère | Seuil de veto | Signification |
|---------|--------------|---------------|
| MTS < 20 | Vent macro trop contraire — trop risqué |
| SUS < 25 | Signal trop crowdé — pas d'avantage |
| IPI < 20 | Distribution institutionnelle massive — les gros fuient |

---

## 3. Module 2 — Analyseur de Stratégies

**Page : Analyseur** | **Ce qu'il fait :** Détecte le régime de marché et choisit la meilleure stratégie

### Régime de marché

Le marché n'est pas toujours dans le même état. L'analyseur détecte 5 régimes :

| Régime | Ce que ça signifie | Probabilité affichée |
|--------|-------------------|---------------------|
| 🟢 **BULL** (Haussier) | Les prix montent, la tendance est positive | Ex: BULL 46% |
| 🔴 **BEAR** (Baissier) | Les prix descendent, la tendance est négative | |
| 🔵 **RANGE** (Latéral) | Le prix oscille entre deux bornes, pas de tendance | |
| ⚫ **CRISIS** (Crise) | Chute brutale + volatilité extrême | |
| 🟡 **TRANSITION** | Changement de régime en cours — incertitude | |

**Important :** La détection est **probabiliste**, pas binaire. Un actif peut être "BULL à 46%, TRANSITION à 30%, RANGE à 24%". Plus la probabilité est haute, plus on est sûr du régime.

### Les 7 stratégies

| Stratégie | Quand elle fonctionne | Comment elle entre |
|-----------|----------------------|-------------------|
| **Trend Following** | Marché en tendance claire | Quand les moyennes mobiles se croisent |
| **Mean Reversion** | Marché en excès (suracheté/survendu) | Quand le prix est trop loin de sa moyenne |
| **Mean Reversion V2** | Idem mais avec plus de confirmations | Z-score + Keltner + volume exhaustion |
| **Breakout** | Cassure d'un range | Quand le prix sort d'une zone de consolidation |
| **Momentum** | Force relative | Quand plusieurs indicateurs pointent dans la même direction |
| **Fibonacci** | Niveaux naturels de support | Quand le prix atteint un niveau Fibonacci clé (0.618) |
| **Ichimoku** | Système japonais complet | Quand le prix est au-dessus du "nuage" avec confirmation |

### Sélection par backtest

Le système ne choisit **pas au hasard**. Il a testé chaque stratégie sur 2 ans de données pour chaque actif et sait laquelle fonctionne le mieux :

*Exemples :*
- GOOGL → **Trend Following** (Sharpe 1.81)
- AMZN → **Mean Reversion** (Sharpe 1.70)
- Silver → **Trend Following** (Sharpe 2.06)

Le **Sharpe Ratio** mesure le rendement ajusté au risque :
- \> 1.5 = Excellent
- \> 1.0 = Bon
- \> 0.5 = Correct
- < 0 = La stratégie perd de l'argent

### Ensemble Voting

Au lieu de choisir UNE stratégie, le système peut combiner les votes de TOUTES les stratégies profitables. Plus les stratégies sont d'accord, plus le signal est fiable.

---

## 4. Module 3 — Moteur de Scoring

**Page : Scoring** | **Ce qu'il fait :** Produit la Thèse de Trade — la décision finale

### Le Verdict : GO / ATTENTE / PAS DE TRADE

| Signal | Ce que ça signifie | Quoi faire |
|--------|-------------------|------------|
| 🟢 **GO** | Toutes les conditions sont réunies | Vous pouvez exécuter le trade |
| 🟡 **ATTENTE** | Presque bon mais pas parfait | Surveiller, ne pas entrer |
| ⚪ **PAS DE TRADE** | Aucun signal clair | Rester à l'écart |

### Score de la thèse

Le score final combine 3 composantes :

#### 1. Score Bayésien (50% du score)

Combine l'**historique** de l'actif (prior) avec les **observations actuelles** (likelihood) :

- **Prior** = Comment cet actif s'est-il comporté sur 6 mois ? Consistant ? En hausse ?
- **Likelihood** = Que disent le scanner et l'analyseur en ce moment ?
- **Postérieur** = La combinaison des deux, pondérée par la confiance

*Si le régime est détecté avec haute confiance, on fait plus confiance aux observations actuelles.*

#### 2. Qualité du Contexte — SQC (20% du score)

Évalue si les **conditions pratiques** sont bonnes pour trader :

| Composante | Ce qu'elle mesure | Score élevé = |
|-----------|-------------------|---------------|
| **Liquidité** | Volume par rapport à la moyenne | Facile d'entrer/sortir |
| **Timing** | Heure du marché (ouverture/clôture) | Meilleure exécution |
| **Volatilité** | Le mouvement de prix est-il normal ? | Conditions stables |

#### 3. Conviction de la stratégie (30% du score)

À quel point la stratégie sélectionnée est-elle sûre de son signal.

### Signal Shelf Life — Durée de vie du signal

Chaque signal a une **date de péremption** :

| Durée | Type d'ordre recommandé | Explication |
|-------|------------------------|-------------|
| < 4h | **MARKET** (immédiat) | Le signal est urgent, exécutez maintenant |
| 4h-24h | **LIMIT** (au bon prix) | Attendez le prix idéal |
| 1-3 jours | **LIMIT** | Patience, le prix viendra |

### Position Sizing — Kelly

**La taille de position est CRUCIALE.** Le critère de Kelly calcule la taille optimale :

| Paramètre | Ce que ça signifie |
|-----------|-------------------|
| **Kelly fraction** | Pourcentage du capital à risquer (ex: 8.9%) |
| **Position size** | Montant en dollars (ex: $8 932) |
| **Risque par trade** | Combien vous pouvez perdre au maximum (ex: $492) |
| **R:R** | Ratio risque/récompense. 1:1.5 = pour 1$ risqué, 1.50$ de gain potentiel |
| **Win rate estimé** | Probabilité de gain (ex: 61%) |
| **Expected Value** | Si positif = le trade est statistiquement rentable à long terme |

**Règle d'or :** Ne risquez JAMAIS plus de 2% de votre capital sur un seul trade.

---

## 5. Module 4 — Exécution des Ordres

**Page : Exécution** | **Ce qu'il fait :** Passe les ordres en paper trading

### Le bouton "Lancer le Trading"

Exécute **tous les signaux GO** d'un coup. Chaque trade passe par :

1. **Vérification des biais** — le système vérifie que vous ne faites pas d'erreur psychologique
2. **Sizing** — calcule la taille de position optimale (5% du capital par trade)
3. **Scaling 3 tranches** — n'entre pas tout d'un coup :
   - **Tranche 1 (40%)** : exécution immédiate
   - **Tranche 2 (35%)** : ordre limit légèrement au-dessus
   - **Tranche 3 (25%)** : ordre stop sur confirmation

### Détection des biais comportementaux

Le système vous protège contre **4 erreurs psychologiques** courantes :

| Biais | Ce que c'est | Comment le système le détecte |
|-------|-------------|------------------------------|
| 🎰 **Disposition** | Couper les gains trop tôt, garder les pertes trop longtemps | Compare la durée des trades gagnants vs perdants |
| 😤 **Revenge Trading** | Augmenter le risque après une perte pour "se refaire" | Détecte si la taille de position augmente après une perte |
| 😱 **FOMO** | Entrer tard dans un mouvement par peur de rater | Vérifie si le prix a déjà beaucoup bougé (> 25%) |
| 🔄 **Over-Trading** | Trop de trades = les frais mangent la performance | Compte les trades par jour |

**Niveaux :**
- **OK** = Pas de problème
- **WARNING** = Attention, taille de position réduite recommandée
- **BLOCK** = Trade bloqué — risque trop élevé

### Statut Alpaca

Le bandeau en haut montre votre connexion au broker :

- 🟢 **Connecté à Alpaca** — Paper Trading — Capital : $100 000
- 🔴 **Non connecté** — Le broker n'est pas configuré

---

## 6. Module 5 — Gestion du Portefeuille

**Page : Portefeuille** | **Ce qu'il fait :** Gère le risque global

### Risk Parity

Au lieu de mettre le même **montant** sur chaque position, le système met le même **risque**. Un actif volatile (crypto) aura une plus petite position qu'un actif stable (obligation).

### Stress Tests

Le système simule **4 catastrophes** sur votre portefeuille :

| Scénario | Ce qui se passe | Perte typique |
|----------|----------------|---------------|
| **COVID Mars 2020** | Crash de -34% en 23 jours | La pire perte possible sur les actions |
| **Bear Market 2022** | Baisse prolongée, hausse des taux | -25% actions, -65% crypto |
| **Black Swan Crypto** | Effondrement type Luna/FTX | -80% sur les crypto |
| **Flash Crash** | Chute brutale intraday -10% | Recovery partiel |

*Cela vous montre combien vous pourriez perdre dans le pire des cas.*

### Régime du portefeuille

| Régime | Signification | Action |
|--------|--------------|--------|
| **ALPHA** | Le portefeuille surperforme | Maintenir les positions |
| **BETA** | Performance proche du marché | Normal |
| **STRESS** | Drawdown > 10% ou volatilité extrême | Réduire les positions |

### Liquidation Score

Note de 0 à 100 mesurant la facilité à **sortir** d'une position :
- **> 80** = Très liquide, sortie facile
- **< 40** = Difficile à sortir sans impact sur le prix

---

## 7. Module 6 — Suivi de Rentabilité

**Page : Performance** | **Ce qu'il fait :** Vérifie que le système fonctionne et s'améliore

### Meta-Score (0-100)

La note de santé globale du système. **C'est le chiffre le plus important** car il pilote le niveau d'engagement :

| Score | Engagement | Ce que fait le système |
|-------|-----------|----------------------|
| **> 80** | FULL | Taille de position maximale, toutes stratégies actives |
| **60-80** | NORMAL | Paramètres standard |
| **40-60** | PRUDENT | Taille de position réduite de moitié |
| **< 40** | MINIMAL | Pause partielle — le système se protège |

### Early Warning System (EWS)

5 indicateurs d'alerte avec 4 niveaux :

| Indicateur | NORMAL | ATTENTION | ALERTE | CRITIQUE |
|-----------|--------|-----------|--------|----------|
| **Drawdown** | > -5% | -5% à -10% | -10% à -20% | < -20% |
| **Série de pertes** | < 3 trades | 3-5 trades | 5-8 trades | > 8 trades |
| **Déclin Win Rate** | Stable | -10pp | -20pp | -30pp |
| **Spike Volatilité** | < 1.5x | 1.5-2.5x | 2.5-4x | > 4x |
| **Rupture Corrélation** | < 0.3 | 0.3-0.5 | 0.5-0.7 | > 0.7 |

**CRITIQUE = le pipeline se met en pause automatiquement.**

### Attribution P&L

Décompose votre performance en **6 causes** :

| Facteur | Ce que ça mesure | Si négatif, que faire |
|---------|-----------------|----------------------|
| **Scanner** | Qualité de la sélection d'actifs | Ajuster les poids des 9 critères |
| **Timing** | Qualité du point d'entrée | Utiliser plus d'ordres LIMIT |
| **Sizing** | Taille de position vs optimale | S'en tenir au Kelly |
| **Sortie** | Qualité du point de sortie | Ajuster les SL/TP |
| **Régime** | Impact du marché (chance/malchance) | Rien à faire — c'est le marché |
| **Friction** | Frais + slippage | Réduire la fréquence de trading |

### Monte Carlo

Simule **10 000 futurs possibles** pour votre portefeuille :

| Métrique | Ce que ça signifie |
|---------|-------------------|
| **Percentile 10** | Dans 90% des cas, vous ferez mieux que ça |
| **Percentile 50** | Le scénario médian (le plus probable) |
| **Percentile 90** | Le scénario optimiste |
| **P(ruine)** | Probabilité de perdre > 50% du capital. **Doit rester < 5%** |

### Feedback Loop

Le Module 6 renvoie des informations au Module 1 pour s'améliorer :

- Si le scanner sélectionne mal → réduire son poids
- Si le timing est mauvais → raccourcir la shelf life
- Si le système est en CRITIQUE → pause automatique

**C'est ce qui fait que le système apprend de ses erreurs.**

---

## 8. La page Détail Actif

**Accès :** Cliquez sur n'importe quel symbole (ex: AAPL) dans le Dashboard ou le Scanner.

C'est la page la plus complète. Elle contient :

### En haut
- **Symbole + nom** de l'actif
- **Prix actuel** (live via Alpaca si disponible)
- **Régime** détecté (Haussier/Baissier/etc.)

### Verdict TradePilot
- **Jauge circulaire** du score global (0-100)
- **Signal GO/ATTENTE/PAS DE TRADE** avec explication
- **Stratégie sélectionnée** avec sa performance backtest
- **Niveaux de prix** : Entrée, Stop Loss, TP1, TP2

### Graphique TradingView
- **Chandeliers japonais** interactifs (zoom, pan)
- **SMA 20** (ligne dorée) et **SMA 50** (ligne or clair)
- **Volume** coloré (doré = hausse, gris = baisse)
- Switch **Daily / Horaire**

### Radar des 9 critères
- Visualisation en radar de tous les scores
- Plus la forme est large, plus l'actif est fort

### Chaque critère avec explication
- Score sur jauge circulaire
- **Bouton "Comment lire cette section ?"** qui affiche l'explication
- **Interprétation dynamique** ("Ce score de 73 signifie que...")
- Détails spécifiques (phase de cycle, A/D line, etc.)

---

## 9. Glossaire

| Terme | Définition simple |
|-------|------------------|
| **ATR** | Average True Range — mesure la volatilité en dollars. Si ATR = $5, le prix bouge de ~$5 par jour |
| **Backtest** | Tester une stratégie sur des données du passé pour voir si elle aurait marché |
| **Bollinger Bands** | Bandes autour du prix qui montrent si la volatilité est normale ou extrême |
| **Breakout** | Quand le prix sort d'une zone de consolidation (casse un niveau) |
| **Drawdown** | La perte maximale depuis le plus haut. -10% drawdown = vous avez perdu 10% depuis le pic |
| **EMA** | Moyenne mobile exponentielle — plus réactive que la SMA, suit mieux le prix récent |
| **Fibonacci** | Niveaux naturels (0.382, 0.5, 0.618) où le prix a tendance à rebondir |
| **FOMO** | Fear Of Missing Out — peur de rater un mouvement, pousse à entrer trop tard |
| **Ichimoku** | Système japonais complet qui montre tendance + support + timing en un seul graphique |
| **Kelly** | Formule mathématique qui calcule la taille de position optimale |
| **LONG** | Parier que le prix va monter (acheter) |
| **MACD** | Indicateur de momentum — quand il croise vers le haut, la hausse accélère |
| **Mean Reversion** | Stratégie qui parie que le prix revient toujours vers sa moyenne |
| **Paper Trading** | Trading simulé avec de l'argent fictif — aucun risque réel |
| **P&L** | Profit & Loss — votre gain ou perte |
| **Risk Parity** | Répartir le même risque (pas le même montant) sur chaque position |
| **RSI** | Relative Strength Index (0-100) — > 70 suracheté, < 30 survendu |
| **R:R** | Risk/Reward ratio. 1:2 = vous risquez 1$ pour gagner 2$ |
| **Sharpe Ratio** | Rendement ajusté au risque. > 1 = bon, > 2 = excellent |
| **SHORT** | Parier que le prix va descendre (vendre à découvert) |
| **Slippage** | Différence entre le prix voulu et le prix obtenu à l'exécution |
| **SMA** | Simple Moving Average — moyenne des X derniers jours de prix |
| **Stop Loss (SL)** | Ordre automatique qui vous sort du trade si le prix va trop contre vous |
| **Take Profit (TP)** | Ordre automatique qui prend vos gains quand le prix atteint l'objectif |
| **Trailing Stop** | Stop loss qui monte avec le prix — protège les gains acquis |
| **TWAP** | Exécution découpée en tranches temporelles égales |
| **VIX** | "Indice de la peur" — mesure la volatilité attendue du marché |
| **VWAP** | Exécution pondérée par le volume — plus de volume = plus grosse tranche |
| **Walk-Forward** | Test de backtest avancé : on optimise sur une partie, on valide sur une autre |
| **Win Rate** | Pourcentage de trades gagnants. 55% = 55 trades gagnants sur 100 |
| **Z-score** | Mesure à combien d'écarts-types le prix est de sa moyenne. > 2 = extrême |

---

## 10. Paramètres et Configuration

### Fichier .env

| Variable | Où l'obtenir | Impact |
|----------|-------------|--------|
| `ALPACA_API_KEY` | app.alpaca.markets → API Keys | Connexion broker |
| `ALPACA_SECRET_KEY` | Idem (ne s'affiche qu'une fois) | Connexion broker |
| `FRED_API_KEY` | fred.stlouisfed.org/docs/api/api_key.html | Données macro réelles (VIX, taux) |
| `REDDIT_CLIENT_ID` | reddit.com/prefs/apps | Sentiment Reddit réel |
| `REDDIT_CLIENT_SECRET` | Idem | Sentiment Reddit réel |
| `NEWSAPI_KEY` | newsapi.org | Actualités financières |

### Commandes utiles

```bash
# Démarrer tout
bash scripts/start_all.sh

# Arrêter tout
bash scripts/stop_all.sh

# Vérifier l'état
bash scripts/status.sh

# Lancer le backend seul
make backend

# Lancer le frontend seul
make frontend

# Lancer le pipeline automatique (trading quotidien)
make worker    # Terminal 1
make beat      # Terminal 2

# Lancer les tests
pytest tests/

# Charger de nouvelles données
python scripts/load_historical_data.py
python scripts/load_intraday_data.py
python scripts/load_new_assets.py

# Configurer Alpaca
python scripts/setup_alpaca.py
```

### Ports utilisés

| Port | Service |
|------|---------|
| 5173 | Frontend (Vite/React) |
| 8000 | Backend (FastAPI) |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 8086 | InfluxDB |

### API Documentation

Accédez à la documentation interactive Swagger : **http://localhost:8000/docs**

Tous les endpoints y sont listés avec la possibilité de les tester directement.

---

> **Rappel important :** TradePilot est un outil d'**aide à la décision**, pas un conseil financier. Ne tradez jamais avec de l'argent que vous ne pouvez pas vous permettre de perdre. Commencez toujours par le paper trading.
