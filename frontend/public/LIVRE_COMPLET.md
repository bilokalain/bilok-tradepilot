# BILOK-TRADEPILOT — Le Système

### Architecture d'un Pipeline de Trading Automatisé à 6 Modules avec Feedback Loop

---

## À PROPOS DE L'AUTEUR

**BILOK EVANG Alain**

*Économiste quantitatif | Analyste de risques financiers | Entrepreneur*

---

Alain Bilok Evang est un économiste et analyste financier camerounais basé en Belgique, dont le parcours académique et professionnel se situe à l'intersection de la finance quantitative, de l'analyse de données et de l'entrepreneuriat.

**Formation académique :**

- **Master complémentaire en Analyse de Risques Financiers** — HEC Liège, Université de Liège (Belgique). Spécialisation dans la modélisation des risques de marché, de crédit et opérationnels. Méthodologies VaR, stress testing, simulation Monte Carlo.

- **Master 2 en Sciences Économiques, option Finance** — HEC Liège, Université de Liège (Belgique). Approfondissement en théorie de portefeuille, évaluation d'actifs, marchés dérivés et ingénierie financière.

- **Maîtrise en Économie Monétaire et Bancaire** — Université de Douala (Cameroun). Fondements en politique monétaire, systèmes bancaires, macroéconomie et économétrie.

**Parcours professionnel :**

Alain évolue dans le secteur de la Data Analyse appliquée au domaine financier, au service d'institutions bancaires et d'assurances. Son expertise couvre l'exploitation de données massives, la construction de modèles prédictifs et l'automatisation de processus décisionnels — compétences qu'il a transposées dans la conception de Bilok-TradePilot.

**Vision entrepreneuriale :**

Entrepreneur chrétien, Alain est convaincu que l'excellence professionnelle et la foi ne sont pas des trajectoires parallèles mais convergentes. Bilok-TradePilot est né de cette conviction : construire un système rigoureux, discipliné et transparent — un outil de gestion fidèle des ressources, au service d'une vision qui dépasse les rendements financiers.

Ce livre est le fruit de plusieurs années de recherche, de développement et de confrontation aux marchés réels. Il reflète un parcours qui va de la théorie économique classique (Douala) à la finance quantitative moderne (Liège), en passant par la pratique quotidienne de l'analyse de données dans l'industrie financière.

---

*Première édition — 2026*

*Bruxelles, Belgique*

---

## DÉDICACES

---

### À Dieu

*Ce livre est dédié avant tout à Celui qui est la source de toute sagesse, de toute intelligence et de toute vision.*

*Seigneur, Tu m'as mis sur ce chemin bien avant que je n'en comprenne le sens. Chaque ligne de code, chaque algorithme, chaque nuit passée à construire ce système — tout cela n'est que la réponse obéissante à une vision que Tu as semée en moi : devenir un gestionnaire fidèle des ressources que Tu me confieras.*

*Ce projet n'est pas une fin. C'est un outil au service d'un dessein plus grand. Car Tu ne confies pas l'abondance à ceux qui la cherchent pour eux-mêmes, mais à ceux qui ont appris à la gérer pour Ton Royaume.*

*Que ce travail soit le témoignage d'une gestion diligente, en attendant le jour où Tu diras : « C'est bien, bon et fidèle serviteur ; tu as été fidèle en peu de chose, je te confierai beaucoup. »*

*À Toi seul revient la gloire.*

> *« La richesse des pécheurs est réservée pour le juste. »*
> — Proverbes 13:22

> *« Tu te souviendras de l'Éternel, ton Dieu, car c'est lui qui te donne de la force pour les acquérir, afin de confirmer son alliance. »*
> — Deutéronome 8:18

---

### À Anna

*À toi, Anna Tshiunza, mon épouse, mon ancre, mon silence quand le monde est trop bruyant.*

*Ce livre porte mon nom, mais il porte ton empreinte. Car derrière chaque nuit que j'ai passée devant un écran, il y avait une femme qui veillait sur notre foyer. Derrière chaque ligne de code écrite au petit matin, il y avait une mère qui avait déjà nourri, consolé, accompagné — sans jamais demander de reconnaissance.*

*Tu portes sur tes épaules ce que je suis trop souvent absorbé pour porter moi-même. Tu le fais avec une grâce et un courage que je n'ai pas les mots pour décrire — mais que nos enfants, eux, n'oublieront jamais.*

*À Grace, qui porte si bien son prénom — que tu grandisses dans la lumière.*
*À Freddy, dont la force tranquille nous inspire tous.*
*À Johanna, dont le rire remplit la maison même quand je suis trop loin pour l'entendre.*
*À Elikya — Espérance — dont le nom est la promesse que le meilleur est devant nous.*

*Anna, ce que je construis la nuit, c'est toi qui le rends possible le jour. Ce livre, comme tout le reste, est aussi le tien.*

*Avec tout mon amour et ma gratitude infinie.*

*— Alain*

---

> *"Les marchés ne récompensent pas l'intelligence. Ils récompensent la discipline."*

---

# AVANT-PROPOS

Ce livre documente la construction, l'architecture et le fonctionnement de Bilok-TradePilot — un système de trading automatisé conçu pour éliminer les biais émotionnels de la prise de décision financière.

Ce n'est pas un livre de théorie. Chaque concept décrit ici a été implémenté, testé et confronté aux marchés réels. Les 59 chapitres qui suivent retracent le parcours d'un signal depuis sa naissance (une thèse de trading) jusqu'à sa conclusion (un P&L attribué et analysé), en passant par les 6 modules du pipeline.

**À qui s'adresse ce livre :**
- Aux traders qui cherchent à systématiser leur approche
- Aux développeurs qui veulent comprendre l'architecture d'un système de trading complet
- Aux étudiants en finance quantitative qui cherchent un cas d'étude concret
- À toute personne curieuse de comprendre comment un algorithme peut prendre des décisions d'investissement

**Ce que ce livre n'est pas :**
- Un conseil en investissement
- Une promesse de performance
- Un raccourci vers la richesse

Les marchés financiers sont intrinsèquement incertains. Aucun système, aussi sophistiqué soit-il, ne peut garantir des rendements positifs. Ce livre décrit une méthodologie, pas une certitude.

---

# INTRODUCTION — La Philosophie du Système

## Le Problème

Les statistiques sont implacables : entre 70% et 90% des traders particuliers perdent de l'argent sur les marchés financiers. Ce chiffre n'a pratiquement pas changé depuis que les marchés existent. La technologie a évolué — des carnets d'ordres physiques aux algorithmes haute fréquence — mais le taux d'échec des traders retail reste remarquablement stable.

Pourquoi ?

La réponse ne se trouve pas dans un manque de connaissance technique. La plupart des traders connaissent les indicateurs, les patterns, les stratégies. Le problème est plus fondamental : le cerveau humain n'est pas câblé pour trader.

La neuroscience a identifié les mécanismes précis :

**Le Disposition Effect** — nous vendons trop tôt nos gagnants (pour "sécuriser le gain") et gardons trop longtemps nos perdants (en espérant qu'ils remontent). Le cortex préfrontal, siège de la rationalité, est court-circuité par l'amygdale, siège de la peur, dès que de l'argent réel est en jeu.

**Le FOMO (Fear Of Missing Out)** — quand un actif monte de 20% sans nous, la douleur de l'opportunité manquée est neurologiquement identique à une perte réelle. Nous entrons alors au pire moment : quand le mouvement est presque terminé.

**Le Revenge Trading** — après une perte, la tentation de "se refaire" pousse à prendre des positions plus grosses, moins réfléchies. La perte initiale se transforme en spirale.

**L'Over-Trading** — l'illusion que l'activité égale la productivité. Chaque trade a un coût (commission, spread, slippage). Trop de trades, même médiocrement profitables, mangent le capital par friction.

Ces biais ne sont pas des faiblesses de caractère. Ce sont des réponses évolutives parfaitement adaptées à la survie dans la savane — et parfaitement inadaptées aux marchés financiers.

## La Solution

Bilok-TradePilot est né d'une conviction simple : si le problème est humain, la solution doit être systématique.

Le système ne remplace pas l'intelligence du trader. Il remplace ses émotions. La vision, la thèse directionnelle, le choix des marchés — tout cela reste humain. Mais une fois la thèse formulée, le pipeline prend le relais : il filtre, analyse, score, exécute, gère et apprend sans jamais ressentir la peur, l'avidité ou l'impatience.

L'architecture repose sur 6 modules enchaînés en pipeline, avec une boucle de feedback qui permet au système d'apprendre de ses propres erreurs :

```
[ Scanner ] → [ Analyseur ] → [ Scoring ] → [ Exécution ] → [ Portefeuille ] → [ Performance ]
     ↑______________________________________________feedback loop___________________________________________|
```

Chaque module a une responsabilité unique et une question à laquelle il répond :

| Module | Question |
|--------|----------|
| **Scanner** | Quels actifs méritent notre attention ? |
| **Analyseur** | Comment les trader ? |
| **Scoring** | Doit-on y aller, et avec combien ? |
| **Exécution** | Comment passer l'ordre de manière optimale ? |
| **Portefeuille** | Le risque global est-il maîtrisé ? |
| **Performance** | Qu'avons-nous appris ? |

Le principe est celui d'un entonnoir intelligent. On commence avec 335 actifs. Le Scanner en retient une poignée. L'Analyseur choisit la stratégie. Le Scoring décide si le rapport risque/rendement justifie l'action. L'Exécution passe l'ordre. Le Portefeuille vérifie que le risque global reste acceptable. Et la Performance analyse le résultat pour améliorer le cycle suivant.

Chaque étape filtre, affine et valide. Un actif qui passe tous les filtres a été examiné sous 10 angles différents, évalué par 8 sources de scoring, validé contre le risque portefeuille, et exécuté avec les protections appropriées.

## Le Parcours d'un Signal

Pour comprendre le système, suivons le parcours concret d'un signal — de sa naissance à sa conclusion.

**Jour 1, 00h00 UTC** — Le pipeline nocturne se déclenche. Le Scanner passe en revue les 335 actifs de l'univers d'investissement. Pour chacun, il calcule 10 scores indépendants : technique, corrélation, sentiment, génome explosif, capital institutionnel, vélocité fondamentale, macro tailwind, topologie sociale, unicité du signal et analyse fondamentale. L'action HIMS obtient un score final de 70.1/100. Elle est promue dans la shortlist.

**00h57** — L'Analyseur détecte le régime de HIMS : BULL avec 68% de confiance. Il teste les 12 stratégies disponibles et sélectionne Momentum Adaptatif, avec une conviction de 72% et une direction LONG. Entrée estimée à 28.39$, SL à 24.80$, TP à 33.77$.

**00h58** — Le Scoring fusionne les 8 sources : scanner 63.4, stratégie/backtest 72, régime global RISK_ON, fondamentaux 49.2, pas de catalyseur imminent, corrélation portefeuille OK, rotation sectorielle neutre, pas de lead-lag. Score V2 final : 68.2 → **GO**. Kelly sizing : 1 action (compte IBKR de 304€).

**00h59** — L'Exécution vérifie les biais (pas de revenge trading, pas de FOMO), vérifie la marge IBKR (insuffisante — l'ordre est mis en queue), et place un bracket order Alpaca en paper trading.

**Toutes les 5 minutes** — Le TP/SL Monitor surveille les positions ouvertes. Il vérifie les prix, calcule l'essoufflement, et ajuste les trailing stops.

**15h45 Paris** — Le scan intraday détecte HIMS à +25.9% sur la journée. Le signal GO est confirmé en temps réel, pas seulement sur les données de la veille.

**Module 6** — La Performance enregistre le résultat. Si HIMS a été tradé, le P&L est attribué à ses sources : le Scanner a-t-il bien détecté l'actif ? Le timing était-il bon ? Le sizing était-il approprié ? Ce feedback remonte au Module 1 pour ajuster les poids du prochain scan.

C'est ce cycle — détection, analyse, décision, exécution, contrôle, apprentissage — qui tourne en continu, 24 heures sur 24, 7 jours sur 7. Le système ne dort pas, ne doute pas et n'oublie jamais ce qu'il a appris.

Les 59 chapitres qui suivent décortiquent chaque étape de ce processus.

---

# PARTIE I — LA VISION

---

## Section 1 — Les Thèses de Trading

---

### Chapitre 1 : Qu'est-ce qu'une thèse de trading

Avant le premier scan, avant le premier indicateur, avant le premier ordre — il y a une idée. Un trader observe le monde et formule une conviction : "Je pense que X va se produire, et cela devrait faire bouger le prix de Y dans la direction Z."

Cette conviction structurée, c'est une **thèse de trading**.

La distinction entre une thèse et une opinion est fondamentale. Une opinion est vague : "Je pense que la tech va monter." Une thèse est précise, testable et réfutable :

> *"L'adoption de l'IA générative par les entreprises va accélérer au second semestre 2026, portée par la baisse des coûts d'inférence. Les entreprises qui fournissent l'infrastructure (NVDA, AMD, AVGO) et les plateformes cloud (AMZN, MSFT, GOOGL) devraient surperformer le S&P 500 de 15-25% sur les 6 prochains mois."*

Une thèse de trading se compose de quatre éléments :

**1. Le Thème** — le narratif macro qui sous-tend la conviction. "L'IA transforme l'industrie", "Le cycle crypto repart", "L'Europe entre en récession". Le thème fournit le contexte et la durée de vie du signal.

**2. La Direction** — LONG (on parie sur la hausse) ou SHORT (on parie sur la baisse). Une thèse sans direction n'est pas actionable. La direction découle logiquement du thème : si l'IA accélère, les fournisseurs d'infrastructure montent → LONG.

**3. L'Horizon** — sur quelle durée la thèse devrait se réaliser. Un scalp (minutes), un swing (jours), une position (semaines), ou un investissement (mois). L'horizon détermine quels indicateurs techniques sont pertinents, quelle volatilité est acceptable, et quel sizing est approprié.

**4. La Conviction** — un chiffre entre 0 et 100 qui quantifie la certitude. 90 signifie "j'en suis quasi certain, toutes les données convergent". 50 signifie "c'est possible mais je n'ai pas d'edge clair". La conviction influence directement le sizing : plus la conviction est élevée, plus la position est grande (dans les limites du Kelly).

Le système Bilok-TradePilot permet au trader de formaliser ses thèses et de les injecter dans le pipeline. Le scoring les intègre comme un filtre supplémentaire : les actifs alignés avec une thèse active reçoivent un boost de score, ceux qui la contredisent sont pénalisés.

Mais — et c'est crucial — le système a le dernier mot. Si les données contredisent la thèse (l'analyse technique est baissière, le sentiment est négatif, les institutionnels vendent), le signal est bloqué même si le trader est convaincu. C'est précisément là que le système protège le trader de lui-même.

---

### Chapitre 2 : Construire une thèse solide

Une thèse solide ne naît pas dans le vide. Elle émerge d'une analyse structurée qui part du plus large (la macroéconomie) pour aller au plus précis (l'actif individuel). C'est l'approche **top-down**.

**Niveau 1 : Le Macro**

Où en sommes-nous dans le cycle économique ? L'économie est-elle en expansion (les entreprises embauchent, les consommateurs dépensent) ou en contraction (les licenciements augmentent, la confiance baisse) ? Les banques centrales accommodent-elles (taux bas, liquidité abondante) ou resserrent-elles (taux hauts, réduction du bilan) ?

Ces questions déterminent le terrain de jeu. En expansion avec politique accommodante, les actifs risqués (actions tech, crypto) tendent à surperformer. En contraction avec politique restrictive, les actifs défensifs (obligations, or, utilities) sont favorisés.

Le Module 7 du scanner (Macro Tailwind) quantifie exactement cela.

**Niveau 2 : Le Secteur**

Au sein du cycle macro, tous les secteurs ne réagissent pas de la même manière. Il existe une rotation sectorielle classique :

- Début de cycle : finance, industrie, consommation cyclique
- Milieu de cycle : technologie, communication
- Fin de cycle : énergie, matériaux
- Récession : santé, utilities, consommation défensive

Identifier le secteur en momentum, c'est nager avec le courant plutôt que contre lui.

**Niveau 3 : L'Actif**

Une fois le macro et le secteur identifiés, on sélectionne les actifs spécifiques qui incarnent le mieux la thèse. Les critères varient selon la thèse : leader du secteur ? Meilleure valorisation ? Plus forte croissance ? Plus de momentum ?

C'est ici que les 10 critères du scanner entrent en jeu.

**Les Catalyseurs**

Une thèse sans catalyseur est une idée qui peut rester dormante indéfiniment. Le catalyseur est l'événement qui transforme la thèse en mouvement de prix :

- **Earnings** — les résultats trimestriels confirment ou infirment la trajectoire
- **Annonces Fed** — un changement de politique monétaire reprend tout
- **Événements géopolitiques** — conflits, sanctions, accords commerciaux
- **Événements spécifiques** — approbation FDA, contrat majeur, changement de direction
- **Événements crypto** — halving Bitcoin, upgrade réseau, décisions réglementaires

Le système intègre la proximité des catalyseurs dans le scoring via l'ajustement catalyseur. Un signal GO la veille d'un earnings est traité différemment d'un signal GO en période calme.

**L'Horizon Temporel**

L'horizon détermine tout le reste :

| Horizon | Durée | Timeframes | Volatilité acceptable | Sizing |
|---------|-------|------------|----------------------|--------|
| Scalp | Minutes-heures | 1min, 5min | 0.5-1% | Très petit |
| Swing | 2-10 jours | 1H, 4H, Daily | 2-5% | Modéré |
| Position | 2-8 semaines | Daily, Weekly | 5-15% | Standard |
| Investissement | Mois-années | Weekly, Monthly | 15-30% | Large |

Bilok-TradePilot est optimisé pour le **swing trading** (2-10 jours), avec des capacités de position trading. C'est le sweet spot pour un système automatisé : assez court pour capturer les mouvements techniques, assez long pour que les frais de transaction ne mangent pas les gains.

---

### Chapitre 3 : Intégrer les thèses dans le pipeline

Le système permet de créer des thèses manuelles via l'interface. Chaque thèse est définie par :

```
Thème : "IA Infrastructure"
Direction : LONG
Symboles : NVDA, AMD, AVGO, MSFT, GOOGL, AMZN
Horizon : 90 jours
Conviction : 75/100
```

Une fois créée, la thèse influence le pipeline de plusieurs manières :

**Amplification** — les actifs listés dans la thèse reçoivent un bonus de score proportionnel à la conviction. À 75% de conviction, le bonus est d'environ +5 points sur le score V2. Ça ne suffit pas à transformer un mauvais actif en signal GO, mais ça peut faire passer un actif de WAIT (63) à GO (68).

**Filtrage** — si une thèse SHORT est active sur un actif, un signal LONG est pénalisé (et vice versa). Le système ne vous empêche pas de trader contre votre thèse, mais il vous le signale clairement.

**Expiration** — les thèses ont un horizon. Passé la date, elles sont désactivées automatiquement. Cela évite les thèses zombies qui traînent et influencent le scoring longtemps après avoir perdu leur pertinence.

**Invalidation** — c'est la partie la plus importante. Si les données contredisent systématiquement la thèse (l'actif baisse alors que la thèse est LONG, les fondamentaux se dégradent, le sentiment tourne négatif), le système réduit progressivement l'influence de la thèse jusqu'à la désactiver.

Cette tension entre conviction humaine et validation algorithmique est au coeur du système. Le trader apporte la vision. Le système apporte la discipline.

> *"Plan the trade, trade the plan."* — Mais laissez le système exécuter le plan.

---

# PARTIE II — LE SCANNER (Module 1)

---

## Section 2 — Le Scanner de Marché : Filtrer le Bruit

---

### Chapitre 4 : Architecture du Scanner

Chaque jour de bourse, des milliers d'actifs s'échangent à travers le monde. Actions américaines, européennes, crypto-monnaies, devises, matières premières, ETF — l'univers d'investissement est vaste. Le défi n'est pas de trouver quelque chose à trader. C'est de trouver la bonne chose.

Le Scanner de Marché est le premier module du pipeline. Sa mission : réduire l'univers de 335 actifs à une poignée de candidats qui méritent une analyse approfondie. Pour cela, il utilise 10 critères indépendants — chacun mesurant une dimension différente de la qualité d'un signal.

**Pourquoi 10 critères ?**

Un seul critère ne suffit jamais. Un actif peut avoir une analyse technique parfaite (tendance haussière, RSI favorable, volume en hausse) mais être détesté par le marché (sentiment négatif), surévalué fondamentalement, et corrélé à tout le reste du portefeuille. À l'inverse, un actif fondamentalement excellent peut être dans une tendance baissière de longue durée.

La force du scanner est dans la **convergence**. Quand les 10 critères s'alignent — les indicateurs techniques sont positifs, le sentiment est bon, les institutionnels accumulent, le macro est favorable, le signal est unique — la probabilité de succès augmente significativement.

**Le principe d'orthogonalité**

Les 10 critères sont conçus pour être **orthogonaux** — c'est-à-dire indépendants les uns des autres. L'analyse technique ne dit rien du sentiment. Le capital institutionnel ne dit rien de l'unicité du signal. Chaque critère apporte une information que les autres ne capturent pas.

Cette orthogonalité est essentielle. Si deux critères mesuraient la même chose (par exemple, deux indicateurs de momentum), ils créeraient une fausse convergence. On penserait avoir deux signaux positifs alors qu'on n'en a qu'un, compté deux fois.

En pratique, une orthogonalité parfaite est impossible — tous les critères sont corrélés à un certain degré par le prix sous-jacent. Mais la diversité des sources (technique, sentiment, fondamental, macro, social, institutionnel) minimise cette corrélation.

**La matrice de pondération adaptative**

Tous les critères n'ont pas le même poids. Et ces poids ne sont pas fixes. La matrice de pondération s'adapte selon 5 axes :

*1. La classe d'actif*

Une action US, une crypto et une paire forex ne se comportent pas de la même manière. Pour une action, l'analyse fondamentale est pertinente. Pour une crypto, la topologie sociale (effet réseau) compte davantage. Pour le forex, le macro tailwind est dominant.

| Critère | Actions US | Crypto | Forex | ETF |
|---------|-----------|--------|-------|-----|
| Technique | 15% | 18% | 13% | 15% |
| Corrélation | 12% | 7% | 10% | 16% |
| Sentiment | 8% | 13% | 4% | 5% |
| Fondamental | 10% | 0% | 0% | 5% |
| Macro | 10% | 6% | 18% | 12% |
| ... | ... | ... | ... | ... |

*2. Le régime de marché*

En marché haussier, la tendance est votre amie — le poids de l'analyse technique augmente. En crise, le macro et le sentiment deviennent dominants. En range, la mean reversion et la corrélation prennent de l'importance.

*3. L'horizon de trading*

En scalp, seule l'analyse technique court terme compte. En position trading, les fondamentaux et le macro gagnent en poids.

*4. La phase du cycle macro*

En expansion, les critères de croissance (IVF, croissance fondamentale) sont amplifiés. En contraction, les critères de risque (MTS, corrélation) sont renforcés.

*5. La capitalisation*

Les mega caps (AAPL, MSFT) sont plus prévisibles par les fondamentaux. Les small caps sont plus réactives au sentiment et aux flux institutionnels.

**Les vetos croisés**

Certaines situations sont si défavorables qu'aucun score élevé sur d'autres critères ne peut les compenser. Le scanner implémente des **vetos automatiques** :

- **MTS < 20** → Le vent macro est trop contraire. Rejet automatique.
- **SUS < 25** → Le signal est trop crowdé. Tout le monde voit la même chose. Rejet.
- **IPI < 20** → Les institutionnels distribuent massivement. Rejet.

Un actif peut avoir un score technique de 95/100, mais si le macro est à 15, il est rejeté. C'est un mécanisme de protection contre les pièges où un indicateur brillant masque un danger fondamental.

---

### Chapitre 5 : Critère 1 — Analyse Technique

L'analyse technique est la pierre angulaire du scanner. Elle étudie les mouvements de prix passés pour identifier des patterns reproductibles et des signaux de continuation ou de retournement.

Bilok-TradePilot utilise **20 indicateurs** répartis en **7 familles**, chacune capturant un aspect différent du comportement du prix.

#### Famille 1 : Tendance (Poids : 20%)

La tendance est la force la plus puissante des marchés. Un actif en tendance haussière a statistiquement plus de chances de continuer à monter que de se retourner. L'inverse est vrai pour une tendance baissière.

**Les Moyennes Mobiles** sont l'outil le plus simple et le plus robuste pour identifier une tendance :

- **SMA 20** (Simple Moving Average 20 jours) — la tendance court terme. Le prix au-dessus de sa SMA 20 est en dynamique positive à court terme.
- **SMA 50** — la tendance intermédiaire. Utilisée par la majorité des gestionnaires de fonds.
- **SMA 200** — la tendance long terme. Le "golden cross" (SMA 50 croise au-dessus de la SMA 200) est considéré comme un signal haussier majeur.

L'**alignement** des moyennes donne la force du signal :

| Configuration | Score | Interprétation |
|--------------|-------|----------------|
| Prix > SMA20 > SMA50 > SMA200 | 90 | Tendance haussière forte — toutes les temporalités alignées |
| Prix > SMA50 > SMA200 | 70 | Tendance haussière — le court terme peut corriger |
| Prix < SMA20 < SMA50 < SMA200 | 10 | Tendance baissière forte — ne pas acheter |
| Prix < SMA50 < SMA200 | 30 | Tendance baissière — prudence |

#### Famille 2 : Momentum (Poids : 25%)

Le momentum mesure la **vitesse** du mouvement de prix. Une tendance peut exister sans momentum (mouvement lent et régulier) ou avec un fort momentum (mouvement rapide et accéléré).

**RSI (Relative Strength Index, période 14)** — l'oscillateur le plus utilisé au monde. Il mesure la force relative des hausses par rapport aux baisses sur les 14 dernières périodes.

- RSI > 70 : **suracheté** — le mouvement haussier est peut-être excessif
- RSI 60-70 : **haussier** — le momentum est positif
- RSI 40-60 : **neutre** — pas de direction claire
- RSI 30-40 : **baissier** — le momentum est négatif
- RSI < 30 : **survendu** — le mouvement baissier est peut-être excessif

Attention : suracheté ne signifie pas "va baisser". En tendance forte, le RSI peut rester suracheté pendant des semaines. Le RSI est un indicateur de **conditions**, pas de **timing**.

**MACD (Moving Average Convergence Divergence)** — mesure la convergence/divergence entre deux moyennes mobiles exponentielles (12 et 26 périodes). L'histogramme MACD est positif quand le momentum court terme accélère par rapport au momentum long terme.

**Williams %R** — similaire au RSI mais inversé. Au-dessus de -20 : suracheté. En dessous de -80 : survendu.

**CCI (Commodity Channel Index)** — mesure l'écart du prix par rapport à sa moyenne statistique. CCI > 100 indique un mouvement fort (haussier ou baissier selon la direction).

**ROC (Rate of Change, 12 périodes)** — le pourcentage de changement du prix sur 12 périodes. Simple mais efficace pour mesurer l'accélération.

Le score de momentum combine ces 5 indicateurs : chaque signal haussier ajoute +1, chaque signal baissier soustrait -1. Le score final est normalisé entre 0 et 100.

#### Famille 3 : Volatilité (Poids : 10%)

La volatilité mesure l'**amplitude** des mouvements. Un actif très volatil offre plus d'opportunités mais aussi plus de risque.

**Bandes de Bollinger** — deux bandes placées à 2 écarts-types au-dessus et en dessous d'une SMA 20. La position du prix dans les bandes indique si l'actif est "cher" (proche de la bande haute) ou "bon marché" (proche de la bande basse) par rapport à sa propre histoire récente.

**ATR (Average True Range, 14 périodes)** — mesure la volatilité moyenne quotidienne. Un ATR de 5$ signifie que l'actif bouge en moyenne de 5$ par jour. L'ATR est utilisé pour le calcul du Stop-Loss (2 × ATR) et du Take-Profit (3 × ATR).

#### Famille 4 : Volume (Poids : 20%)

Le volume confirme ou infirme les mouvements de prix. Un mouvement haussier accompagné d'un volume élevé est plus fiable qu'un mouvement sur volume faible.

**OBV (On-Balance Volume)** — cumule le volume des jours de hausse et soustrait le volume des jours de baisse. Un OBV en hausse indique une accumulation. Un OBV en baisse indique une distribution.

**CMF (Chaikin Money Flow)** — mesure la pression d'achat vs de vente en considérant où le prix ferme dans le range journalier. CMF > 0.1 : forte pression acheteuse. CMF < -0.1 : forte pression vendeuse.

**VWAP (Volume Weighted Average Price)** — le prix moyen pondéré par le volume. Les institutionnels utilisent le VWAP comme référence. Un prix au-dessus du VWAP signifie que les acheteurs récents sont en profit — ce qui crée un support psychologique.

**Ratio de Volume** — le volume actuel divisé par la moyenne 20 jours. Un ratio > 1.5x indique une activité anormale (breakout possible ou événement en cours).

#### Famille 5 : Structure (Poids : 10%)

**Points Pivots** — les niveaux de support et résistance calculés à partir du high, low et close de la veille. Les traders institutionnels les utilisent massivement.

- Au-dessus de R1 (résistance 1) → très fort, tendance haussière confirmée
- Au-dessus de PP (point pivot) → positif
- Entre S1 et PP → neutre, zone d'hésitation
- En dessous de S2 → très faible

#### Famille 6 : Divergences (Poids : 10%)

Les divergences sont parmi les signaux les plus puissants de l'analyse technique. Une divergence se produit quand le prix et un indicateur vont dans des directions opposées :

- **Divergence haussière** : le prix fait un nouveau bas mais le RSI fait un bas plus haut → le momentum ne confirme pas la baisse → retournement probable
- **Divergence baissière** : le prix fait un nouveau haut mais le RSI fait un haut plus bas → le momentum faiblit → correction probable

Le système détecte automatiquement les divergences RSI et MACD.

#### Famille 7 : Force de Tendance — ADX (Poids : 5%)

L'ADX (Average Directional Index) ne dit pas si la tendance est haussière ou baissière — il mesure sa **force** :

- ADX > 40 : tendance très forte (ne pas trader en contre-tendance)
- ADX 25-40 : tendance forte
- ADX 20-25 : tendance faible
- ADX < 20 : pas de tendance (range) → les stratégies de mean reversion sont favorisées

#### Le Score Composite

Le score technique final est la somme pondérée des 7 familles :

```
Score = Tendance × 0.20 + Momentum × 0.25 + Volatilité × 0.10
      + Volume × 0.20 + Structure × 0.10 + Divergences × 0.10
      + ADX × 0.05
```

Un score de 80+ signifie que la grande majorité des indicateurs sont alignés dans la même direction. C'est rare et significatif.

#### L'Analyse Multi-Timeframe V2

Un signal sur un seul timeframe est fragile. Un signal confirmé sur **4 timeframes** est robuste.

Le système analyse chaque actif sur 4 horizons temporels :

| Timeframe | Poids | Rôle |
|-----------|-------|------|
| **Weekly** | 35% | Direction de fond — le courant dominant |
| **Daily** | 30% | Tendance principale — la vague |
| **4H** | 20% | Tendance intermédiaire — le timing |
| **1H** | 15% | Timing d'entrée — le point précis |

Le score MTA (Multi-Timeframe Analysis) mesure l'**alignement** entre ces 4 niveaux :

- **4/4 alignés** (score 85-95) → signal très fort, haute confiance
- **3/4 alignés** (score 65-85) → signal fort
- **2/4 alignés** (score 50-65) → signal modéré, prudence
- **Divergence** (score < 50) → pas de conviction, attendre

Le principe hiérarchique est important : le weekly a le dernier mot. Si le weekly est baissier mais le daily et le 1H sont haussiers, c'est probablement un rebond technique dans une tendance baissière — pas une opportunité d'achat.

Les barres 4H sont construites à partir des barres 1H (agrégation) et les barres weekly à partir des barres daily. Pas besoin de données supplémentaires.

---

### Chapitre 6 : Critère 2 — Corrélation

La corrélation mesure comment deux actifs bougent l'un par rapport à l'autre. Si AAPL et MSFT montent et baissent toujours ensemble, leur corrélation est proche de +1. S'ils bougent en sens inverse, elle est proche de -1. S'il n'y a aucun lien, elle est proche de 0.

**Pourquoi la corrélation est un critère du scanner ?**

Parce qu'une **rupture de corrélation** est l'un des signaux les plus fiables en trading. Quand un actif qui suit habituellement son secteur commence soudainement à se démarquer, c'est que quelque chose change. Soit l'actif a une information que le secteur n'a pas encore intégrée (opportunité), soit il est en train de corriger un excès (risque).

Le système calcule la corrélation sur **5 horizons temporels** :

| Horizon | Période | Ce qu'il mesure |
|---------|---------|-----------------|
| Jour | 5 jours | Mouvements de très court terme |
| Semaine | 20 jours | Dynamique hebdomadaire |
| Mois | 60 jours | Tendance mensuelle |
| Trimestre | 260 jours | Régime structurel |
| Année | 1300 jours | Corrélation de fond |

Une rupture de corrélation se produit quand la corrélation court terme (5-20 jours) diverge significativement de la corrélation long terme (260-1300 jours). Par exemple : AAPL a une corrélation de 0.85 avec le Nasdaq sur un an, mais seulement 0.30 sur les 5 derniers jours. Cet écart de 0.55 est un signal fort.

Le score de corrélation est d'autant plus élevé que l'actif se **démarque** de son groupe. Un score de 90 signifie : "cet actif fait quelque chose de très différent de ses pairs — regardez-le de plus près."

---

### Chapitre 7 : Critère 3 — Sentiment

Le sentiment mesure l'humeur collective autour d'un actif. Ce que les gens disent, pensent et ressentent influence leurs actions — et donc le prix.

Le système utilise **FinBERT**, un modèle d'intelligence artificielle spécialisé dans l'analyse de sentiment financier. Entraîné sur des milliers de documents financiers, FinBERT comprend les nuances du langage financier : "les résultats sont en ligne avec les attentes" n'est pas la même chose que "les résultats dépassent largement les attentes", même si les deux sont techniquement "positifs".

**Les sources analysées :**

- **Reddit** (r/wallstreetbets, r/stocks, r/investing) — le sentiment retail
- **Flux d'actualités** (NewsAPI) — le sentiment média
- **Mentions et discussions** — le volume d'attention

**Le score de sentiment se décompose en deux axes :**

1. **Volume de mentions** (40%) — beaucoup de gens en parlent-ils ? Un actif très mentionné attire l'attention, ce qui peut précéder un mouvement de prix.

2. **Polarité** (60%) — ce qu'ils disent est-il positif, négatif ou neutre ? Le ratio positif/négatif donne la direction du sentiment.

**Les limites du sentiment :**

Le sentiment est un indicateur **contrarian** aux extrêmes. Quand tout le monde est euphorique (sentiment très positif), c'est souvent le moment de vendre — pas d'acheter. À l'inverse, quand le pessimisme est maximal, les meilleures opportunités apparaissent.

Le système ne prend pas le sentiment au premier degré. Il le pondère avec les autres critères. Un sentiment très positif + RSI suracheté + volume en baisse = signal de prudence, pas d'achat.

---

### Chapitre 8 : Critère 4 — Génome Explosif

Le Génome Explosif est le critère le plus original du scanner. Il analyse l'**ADN comportemental** d'un actif — les patterns récurrents dans son histoire qui précèdent les mouvements explosifs.

L'idée est que chaque actif a une "personnalité". Certains explosent après une longue période de compression. D'autres grimpent régulièrement sans explosion. D'autres encore alternent entre des phases de calme et des phases de chaos.

**Les 5 phases de Wyckoff**

Le modèle de Wyckoff, développé dans les années 1930, identifie 5 phases dans le cycle d'un actif :

1. **Accumulation** — les institutionnels achètent discrètement. Le prix est stable, le volume est faible. Le public ne s'intéresse pas encore.

2. **Markup** — la tendance haussière commence. Les premiers acheteurs sont récompensés. Le volume augmente progressivement.

3. **Distribution** — les institutionnels vendent à ceux qui achètent en retard. Le prix stagne à un niveau élevé, le volume est élevé mais le prix ne monte plus.

4. **Markdown** — la baisse commence. Les retardataires sont piégés. Le volume augmente dans la panique.

5. **Capitulation** — la vente panique finale. Tout le monde veut sortir en même temps. C'est souvent le meilleur moment pour acheter.

Le système détecte la phase actuelle de chaque actif et favorise les actifs en phase 1 (accumulation) — c'est-à-dire ceux qui sont sur le point d'exploser.

**Le Sismographe**

Le sismographe détecte 6 **micro-signaux** qui précèdent les mouvements explosifs :

1. **Bollinger Squeeze** — les bandes de Bollinger se contractent (volatilité minimale). Comme un ressort compressé, l'actif va "exploser" dans une direction.

2. **Contraction de Volume** — le volume baisse progressivement. Le calme avant la tempête.

3. **Spike de Volume** — une journée avec un volume anormalement élevé sans mouvement de prix significatif. Quelqu'un se positionne discrètement.

4. **Inside Bars** — plusieurs bougies dont le range (high-low) est contenu dans le range de la bougie précédente. Compression maximale.

5. **Compression ATR** — l'ATR atteint un niveau historiquement bas. La volatilité est comprimée — elle va revenir.

6. **Divergence RSI** — le prix ne bouge pas mais le RSI montre un changement de momentum sous la surface.

Quand 3 ou plus de ces micro-signaux sont actifs simultanément, la probabilité d'un mouvement explosif dans les 1-5 jours suivants augmente significativement.

**La Mémoire Fractale**

Les marchés ont une mémoire. Les patterns qui ont précédé de grands mouvements dans le passé ont tendance à se reproduire — pas à l'identique, mais avec des similitudes structurelles.

Le système utilise la **cosine similarity** (similitude cosinus) pour comparer le pattern actuel de l'actif avec ses patterns historiques qui ont précédé des mouvements de +10% ou plus. Si la similarité est élevée (> 0.7), le système considère que les conditions d'un mouvement explosif sont réunies.

---

### Chapitre 9 : Critère 5 — Capital Institutionnel (IPI)

Les marchés sont dominés par les institutionnels — fonds de pension, hedge funds, banques d'investissement. Ils représentent plus de 80% des volumes. Quand ils bougent, les prix bougent.

Le problème : les institutionnels ne veulent pas que vous sachiez ce qu'ils font. Ils accumulent ou distribuent progressivement, sur des jours ou des semaines, pour ne pas faire bouger le prix.

Le scanner tente de détecter cette activité invisible à travers 3 indicateurs :

**La ligne d'Accumulation/Distribution** — si le prix ferme dans la moitié haute de son range journalier avec un volume élevé, c'est un signe d'accumulation (les acheteurs sont plus agressifs). Si le prix ferme dans la moitié basse, c'est un signe de distribution (les vendeurs dominent).

La tendance de la ligne A/D sur 20 jours indique si les institutionnels accumulent (UP) ou distribuent (DOWN).

**Le Smart Money Flow** — détecte les journées avec un volume anormalement élevé mais un mouvement de prix faible. C'est la signature des institutionnels : ils achètent assez pour accumuler une position, mais pas assez pour faire monter le prix. Quand vous voyez un volume 3x la normale avec un prix qui bouge de 0.5%, quelqu'un se positionne.

**Le Short Interest** — le pourcentage de l'actif qui est vendu à découvert. Un short interest élevé (> 15% du flottant) crée un potentiel de "short squeeze" — si le prix monte, les vendeurs à découvert sont forcés de racheter, ce qui amplifie la hausse.

Un score IPI élevé (> 70) signifie : les gros acteurs se positionnent à l'achat. C'est un signal fort car les institutionnels ont des ressources analytiques que les particuliers n'ont pas. Quand ils achètent, ils ont probablement une bonne raison.

---

### Chapitre 10 : Critère 6 — Vélocité Fondamentale (IVF)

Ce critère ne demande pas "les fondamentaux sont-ils bons ?" mais "les fondamentaux **s'améliorent-ils de plus en plus vite** ?"

La distinction est cruciale. Un actif peut avoir d'excellents fondamentaux (ROE de 25%, croissance de 15%) et pourtant stagner en bourse — si tout le monde sait déjà que les fondamentaux sont bons, c'est dans le prix. Ce qui fait bouger le prix, c'est le **changement** : quand les fondamentaux passent de "bons" à "encore meilleurs", ou de "mauvais" à "moins mauvais".

L'IVF mesure cette accélération à travers :

**L'accélération du prix** — proxy de l'accélération du chiffre d'affaires. Si le prix accélère à la hausse (la pente de la tendance augmente), les marchés anticipent une accélération des fondamentaux.

**La force relative** — la performance de l'actif vs le benchmark (SPY pour les actions US, BTC pour les crypto). Un actif qui surperforme son benchmark de manière croissante est en phase d'accélération fondamentale.

**Les surprises** — les gaps de prix après les earnings ou les annonces. Des surprises positives répétées (le prix saute de 5% après les résultats, trimestre après trimestre) indiquent que les analystes sous-estiment systématiquement la dynamique de l'entreprise.

---

### Chapitre 11 : Critère 7 — Macro Tailwind (MTS)

Un actif ne vit pas dans le vide. Il évolue dans un environnement macroéconomique qui peut le porter (tailwind) ou le freiner (headwind).

Le MTS évalue cet environnement à travers 3 axes :

**Le cycle économique** — en expansion (PIB en hausse, emploi fort), les actifs cycliques (tech, consommation discrétionnaire) surperforment. En contraction, les défensifs (utilities, santé, obligations) sont favorisés.

Le système utilise les données de la Fed (FRED API) pour déterminer la phase du cycle : expansion, pic, contraction, creux.

**Le régime de taux** — les taux d'intérêt sont le paramètre le plus important de la macroéconomie. Des taux bas favorisent les actifs risqués (les investisseurs cherchent du rendement ailleurs que dans les obligations). Des taux hauts favorisent les obligations et les actifs de qualité.

**L'appétit pour le risque** — mesuré par le VIX (indice de volatilité du S&P 500, surnommé "l'indice de la peur"), le DXY (force du dollar), et les flux de liquidité globale. En mode "risk-on", les investisseurs prennent des risques. En mode "risk-off", ils fuient vers les valeurs refuges.

L'adaptation par classe d'actif est importante : la macro n'affecte pas la crypto de la même manière que les actions. Les crypto sont plus sensibles à la liquidité globale qu'aux taux d'intérêt. Les matières premières réagissent davantage au cycle économique qu'au sentiment.

---

### Chapitre 12 : Critère 8 — Topologie Sociale (SGI)

Le SGI mesure la **qualité** de la communauté autour d'un actif — pas seulement le volume de bruit, mais le ratio signal/bruit.

100 mentions sur Reddit ne valent rien si 95 sont des mèmes et des blagues. 10 mentions détaillées avec une analyse fondamentale solide valent beaucoup plus.

Le système évalue :

**Le volume de mentions** — combien de gens en parlent ? Un actif dont les mentions explosent (+200% en une semaine) attire l'attention. Mais attention : un pic de mentions peut aussi signaler un sommet (tout le monde en parle = tout le monde a déjà acheté).

**Le ratio Signal/Bruit** — quelle proportion des discussions est pertinente ? Le NLP (traitement du langage naturel) classe chaque mention comme "signal" (analyse, données, argumentation) ou "bruit" (émotion, mèmes, spam).

**Le Network Effect** — spécifique aux crypto-monnaies. La Loi de Metcalfe stipule que la valeur d'un réseau est proportionnelle au carré du nombre de ses utilisateurs. Plus un réseau crypto a d'utilisateurs actifs, plus sa valeur fondamentale augmente.

**Le momentum d'intérêt** — la tendance de l'intérêt via Google Trends. Un intérêt en hausse régulière est plus sain qu'un pic soudain (qui précède souvent un crash).

---

### Chapitre 13 : Critère 9 — Unicité du Signal (SUS)

C'est peut-être le critère le plus contre-intuitif : un signal que tout le monde voit est un mauvais signal.

Si un actif a un score technique de 90, un sentiment positif, un momentum fort — et que tous les screeners du monde le détectent — alors des millions de traders ont déjà acheté. Le mouvement est dans le prix. Acheter maintenant, c'est acheter au sommet.

Le SUS mesure à quel point votre signal est **unique** :

**Le Crowding Score** — combien d'autres actifs montrent le même pattern ? Si 50 actifs ont un RSI survendu et un MACD qui croise à la hausse, le signal n'est pas unique. Si seulement 3 actifs montrent ce pattern, vous avez potentiellement un avantage.

**Le Novelty Score** — le comportement actuel de l'actif est-il inhabituel par rapport à son historique ? Un actif qui se comporte "normalement" n'offre pas d'avantage. Un actif qui montre un pattern jamais vu est potentiellement intéressant.

**Le Timeframe Neglect** — le signal est-il visible uniquement sur un timeframe non-populaire ? Si le signal n'apparaît que sur le graphique 4H (que peu de traders regardent) mais pas sur le daily (que tout le monde regarde), vous avez un avantage temporel.

**Le Complexity Premium** — le signal nécessite-t-il une analyse complexe pour être identifié ? Les signaux simples (croisement de moyennes mobiles) sont détectés par tout le monde. Les signaux complexes (convergence de corrélation multi-temporelle + sismographe + divergence fractale) sont détectés par très peu.

Un score SUS élevé ne signifie pas "le signal est bon". Il signifie "le signal est rare" — ce qui est une condition nécessaire mais pas suffisante pour un avantage.

---

### Chapitre 14 : Critère 10 — Analyse Fondamentale V2

L'analyse fondamentale évalue la **valeur intrinsèque** d'une entreprise — combien vaut-elle réellement, indépendamment de son prix de marché ?

La version 2 du module fondamental de Bilok-TradePilot couvre **8 dimensions**, avec des données trimestrielles historiques et des comparables sectoriels.

#### Dimension 1 : Valorisation (15%)

La question centrale : payez-vous le juste prix ?

- **P/E (Price/Earnings)** — le prix divisé par le bénéfice par action. Un P/E de 20 signifie que vous payez 20 fois les bénéfices annuels. Mais un P/E n'a de sens que par rapport au secteur : un P/E de 30 est cher pour une banque (médiane secteur : 13) mais normal pour la tech (médiane : 28).

- **PEG (Price/Earnings to Growth)** — le P/E divisé par le taux de croissance. Un PEG < 1 signifie que vous payez moins cher que la croissance ne le justifie — c'est souvent une bonne affaire.

- **EV/EBITDA (Enterprise Value / EBITDA)** — une mesure de valorisation qui neutralise les différences de structure de capital entre entreprises.

- **Forward P/E vs Trailing P/E** — si le forward P/E est significativement inférieur au trailing P/E, le marché attend une amélioration des bénéfices.

Le score de valorisation compare chaque métrique à la **médiane sectorielle**, pas à des seuils absolus.

#### Dimension 2 : Profitabilité (20%)

L'entreprise gagne-t-elle de l'argent efficacement ?

- **Marge nette** — le bénéfice net divisé par le chiffre d'affaires. Une marge de 27% (comme AAPL) signifie que pour chaque dollar de vente, l'entreprise garde 27 cents de profit.

- **ROE (Return on Equity)** — le bénéfice divisé par les capitaux propres. Mesure l'efficacité avec laquelle l'entreprise utilise l'argent des actionnaires.

- **Tendance trimestrielle** — la marge s'améliore-t-elle sur les 8 derniers trimestres ? Une marge en amélioration constante est un signal très positif.

#### Dimension 3 : Croissance (20%)

Les revenus et bénéfices augmentent-ils, et à quelle vitesse ?

- **Revenue Growth** — le taux de croissance du chiffre d'affaires
- **Earnings Growth** — le taux de croissance des bénéfices
- **Accélération YoY** — la croissance accélère-t-elle d'un trimestre à l'autre ? Une accélération est le signal le plus puissant (la croissance passe de 10% à 15% à 22%)

#### Dimension 4 : Santé financière (10%)

L'entreprise peut-elle survivre à un choc ?

- **Debt/Equity** — le ratio dette/capitaux propres. En dessous de 60 : sain. Au-dessus de 200 : risqué.
- **Current Ratio** — les actifs court terme divisés par les passifs court terme. En dessous de 1 : l'entreprise ne peut pas payer ses dettes à court terme.
- **Free Cash Flow** — le cash réellement généré par l'activité après les investissements. Un FCF positif est essentiel.
- **Tendance dette** — la dette baisse-t-elle trimestre après trimestre ? Le désendettement est un signal positif.

#### Dimension 5 : Dividendes (5%)

- **Dividend Yield** — le rendement annuel en dividendes
- **Payout Ratio** — quel pourcentage des bénéfices est distribué. Entre 30% et 70% est soutenable. Au-dessus de 90% est risqué.

#### Dimension 6 : Score Piotroski (10%)

Le score de Piotroski est un classique de l'analyse fondamentale. 9 critères binaires (oui/non) qui évaluent la qualité comptable :

1. ROA positif
2. Cash flow opérationnel positif
3. ROA en amélioration (vs trimestre précédent)
4. Qualité des bénéfices (OCF > Net Income — les bénéfices sont en cash, pas en écriture comptable)
5. Dette en baisse
6. Liquidité suffisante (Current Ratio > 1.5)
7. Pas de dilution (pas d'émission de nouvelles actions)
8. Marge brute en amélioration
9. Revenus en croissance

Score 7-9 : excellente qualité. Score 3-4 : moyenne. Score 0-2 : éviter.

#### Dimension 7 : Earnings Quality (10%)

- **Beat Rate** — sur les 4 derniers trimestres, combien de fois l'entreprise a-t-elle battu les estimations des analystes ? Un beat rate de 4/4 (100%) est exceptionnel.
- **Surprise moyenne** — de combien l'entreprise bat-elle les estimations ? +5% en moyenne est excellent.
- **Consensus analystes** — le ratio buy/hold/sell et surtout son **évolution** (upgrade ou downgrade par rapport au mois précédent).

#### Dimension 8 : DCF simplifié (10%)

Le DCF (Discounted Cash Flow) est la méthode de référence pour estimer la valeur intrinsèque d'une entreprise. Le principe : une entreprise vaut la somme de tous ses flux de trésorerie futurs, actualisés au présent.

Le système calcule un DCF simplifié :
1. Projette le FCF par action sur 5 ans (au taux de croissance actuel)
2. Calcule la valeur terminale (croissance de 2.5% à l'infini)
3. Actualise le tout à 10% (taux de rendement exigé)

La **marge de sécurité** est la différence entre la valeur DCF et le prix actuel. Si la valeur DCF est supérieure de 30% au prix → sous-évalué. Si elle est inférieure de 30% → surévalué.

**Pourquoi le fondamental ne pèse que 8% dans le scoring :**

Parce que Bilok-TradePilot est un système de **swing trading**, pas d'investissement long terme. Les fondamentaux sont importants pour éviter les pièges (ne pas acheter une entreprise en faillite), mais le timing et le momentum sont plus déterminants pour les trades de 2-10 jours.

---

### Chapitre 15 : Critère 11 — Narrative Momentum

La Narrative mesure la **force du récit** autour d'un mouvement de prix. Un mouvement de prix sans récit est fragile. Un mouvement porté par un récit puissant peut durer beaucoup plus longtemps que ce que les indicateurs techniques suggèrent.

Le score Narrative combine :

- **Volume Acceleration** — le volume augmente-t-il de manière accélérée ? Un volume qui double chaque jour crée un effet boule de neige.
- **Price Momentum** — la vitesse de progression du prix. Un rendement 5 jours supérieur au rendement 20 jours indique une accélération.
- **Structure** — la qualité du mouvement. Des bougies haussières propres (fermeture proche du high) sont plus saines que des bougies avec de longues mèches.
- **Breakout** — le prix est-il en train de casser un niveau technique important (résistance, range, moyenne mobile) ?
- **Persistance** — le mouvement se maintient-il après le breakout ou retombe-t-il immédiatement ?

Un score Narrative de 90+ signifie : "un récit puissant est en train de se construire, le mouvement a de l'énergie et de la structure — il peut continuer."

Un score qui tombe en dessous de 50 signifie : "la narrative s'épuise — le mouvement touche à sa fin."

---

### Chapitre 16 : Le Score Scanner Final

Les 10 critères sont calculés. Chacun a produit un score entre 0 et 100. Le moment est venu de les combiner en un **score final** qui détermine si l'actif mérite une analyse plus approfondie.

**La formule :**

```
Score Final = Σ (Score_i × Poids_i)
```

Où les poids s'adaptent selon la matrice de pondération adaptative (classe d'actif × régime × horizon × macro × capitalisation).

**Les vetos :**

Avant le calcul du score final, les vetos sont vérifiés :
- MTS < 20 → score final = 0 (vent macro trop contraire)
- SUS < 25 → score final = 0 (signal trop crowdé)
- IPI < 20 → score final = 0 (distribution institutionnelle massive)

Un seul veto suffit à rejeter l'actif, quel que soit son score sur les autres critères.

**L'interprétation :**

| Score | Interprétation |
|-------|----------------|
| 75+ | Signal très fort — convergence rare de multiples critères |
| 65-75 | Signal fort — candidat GO pour le scoring |
| 55-65 | Signal modéré — à surveiller, pas encore prêt |
| 45-55 | Neutre — rien de remarquable |
| < 45 | Signal faible ou contraire — éviter |

Le scanner transforme 335 actifs en une shortlist de 10-30 candidats. Ces candidats passent ensuite au Module 2 — l'Analyseur de Stratégies — qui déterminera **comment** les trader.

Le taux de détection du scanner (combien de top movers du jour étaient dans la shortlist) est mesuré quotidiennement. Dans sa configuration actuelle, le système détecte environ 90% des mouvements significatifs du jour — ce qui signifie que les actifs qui bougent le plus étaient dans le radar du scanner.

Le 10% manquant est souvent dû à des événements non prévisibles (annonces surprise, tweets, événements géopolitiques) — des choses qu'aucun modèle ne peut anticiper.

---

# PARTIE III — L'ANALYSEUR (Module 2)

---

## Section 3 — Comprendre le Marché Avant d'Agir

---

### Chapitre 17 : Détection Probabiliste du Régime de Marché

Le Scanner a identifié une poignée d'actifs prometteurs. Avant de décider *comment* les trader, il faut comprendre *dans quel contexte* on trade. Un même actif, avec les mêmes indicateurs techniques, peut nécessiter une stratégie radicalement différente selon que le marché est en tendance haussière, en range ou en crise.

La plupart des systèmes de trading classifient le marché de manière binaire : haussier ou baissier. C'est une simplification dangereuse. En réalité, le marché est souvent dans un état intermédiaire — en transition entre deux régimes, ou dans un range qui pourrait basculer dans n'importe quelle direction.

Bilok-TradePilot utilise une **détection probabiliste** : au lieu de dire "le marché est BULL", il dit "le marché est BULL à 65%, RANGE à 20%, TRANSITION à 10%, BEAR à 4%, CRISIS à 1%". Cette distribution de probabilités est infiniment plus utile qu'une étiquette binaire.

**Les 5 régimes :**

| Régime | Description | Stratégies favorisées |
|--------|-------------|----------------------|
| **BULL** | Tendance haussière soutenue, SMA 50 > SMA 200, pente positive | Trend Following, Momentum |
| **BEAR** | Tendance baissière soutenue, SMA 50 < SMA 200, pente négative | Mean Reversion, couverture |
| **RANGE** | Marché latéral, les SMA convergent, pas de direction claire | Mean Reversion, Breakout |
| **CRISIS** | Chute brutale + volatilité extrême (ATR > 2x la moyenne) | Cash, couverture, positions réduites |
| **TRANSITION** | Changement de régime en cours, signaux contradictoires | Keltner Breakout, prudence |

**Les 4 signaux de détection :**

Le système combine 4 sources indépendantes pour estimer les probabilités :

**1. Signal de Tendance** — compare la position du prix par rapport aux SMA 50 et 200, et mesure la pente de la SMA 50 sur 20 jours. Prix > SMA 50 > SMA 200 avec une pente positive de plus de 2% → BULL à 80%. Prix < SMA 50 < SMA 200 avec pente négative → BEAR à 80%. Les SMA convergent (écart < 2%) → RANGE à 50%.

**2. Signal de Volatilité** — compare l'ATR actuel à sa moyenne sur 3 mois. Un ratio ATR > 2.0 signale une CRISIS (70% de probabilité). Un ratio entre 1.3 et 2.0 indique une TRANSITION (40%). Un ratio < 0.7 (compression) suggère un RANGE (60%) — le calme avant la tempête.

**3. Signal de Momentum** — combine le RSI et la direction du MACD. RSI > 60 avec MACD positif → BULL. RSI < 40 avec MACD négatif → BEAR. RSI entre 40 et 60 → RANGE ou TRANSITION selon la volatilité.

**4. Signal de Structure** — la position du prix dans son range de 52 semaines. Proche du high annuel (> 80%) → BULL. Proche du low (< 20%) → BEAR ou CRISIS. Au milieu → RANGE.

Le régime final est la **moyenne pondérée** des 4 signaux. Le signal de tendance pèse le plus (30%), suivi de la volatilité (25%), du momentum (25%) et de la structure (20%). Le régime dominant est celui avec la probabilité la plus élevée, et la **confiance** est cette probabilité elle-même.

Une confiance de 80% signifie que les 4 signaux convergent — on peut être agressif avec la stratégie sélectionnée. Une confiance de 40% signifie que les signaux divergent — il faut être prudent et réduire la taille des positions.

---

### Chapitre 18 : Les Stratégies Adaptatives

Bilok-TradePilot dispose de **14 stratégies** qui couvrent l'ensemble des conditions de marché. Chacune est conçue pour exploiter un type spécifique de mouvement de prix. Voici les principales.

**1. Trend Following** — la plus ancienne et la plus éprouvée des stratégies. Le principe : "La tendance est ton amie." Le système utilise un croisement EMA 9/21 confirmé par la SMA 50. Quand l'EMA rapide (9) croise au-dessus de l'EMA lente (21) et que le prix est au-dessus de la SMA 50, un signal LONG est généré. La conviction augmente avec la distance entre le prix et la SMA 50 — plus le prix est au-dessus, plus la tendance est forte. Stop-Loss à 2 ATR sous l'entrée, Take-Profit à 3 ATR au-dessus.

**2. Mean Reversion** — l'inverse du trend following. Quand un actif s'écarte trop de sa moyenne, il a tendance à y revenir. Le système utilise les bandes de Bollinger et le RSI : un prix qui touche la bande basse de Bollinger avec un RSI < 30 génère un signal LONG (survente extrême). Un prix sur la bande haute avec RSI > 70 → SHORT. L'entrée se fait sur la bande, le TP sur la moyenne mobile centrale.

**3. Mean Reversion V2** — version améliorée qui ajoute le stochastique comme confirmation et utilise un Z-Score pour mesurer l'écart à la moyenne. Un Z-Score < -2 (2 écarts-types sous la moyenne) est un signal de survente plus robuste que les bandes de Bollinger seules.

**4. Breakout** — détecte les cassures de range. Quand le prix sort d'une zone de consolidation (20 jours de range étroit) avec un volume supérieur à 1.5x la moyenne, un breakout est confirmé. Le système attend la confirmation : le prix doit clôturer au-dessus de la résistance, pas seulement la toucher. Entrée au niveau du breakout, SL juste sous le range cassé.

**5. Momentum Adaptatif** — mesure la force relative de l'actif par rapport au benchmark. Un actif qui surperforme systématiquement SPY (actions) ou BTC (crypto) sur les 5, 10 et 20 derniers jours montre un momentum positif. Le score augmente quand les trois horizons sont alignés.

**6. Adaptive Trend** — une version sophistiquée du trend following qui ajuste dynamiquement les périodes des EMA selon la volatilité. En période de forte volatilité, les EMA sont allongées (plus lentes, moins de faux signaux). En période calme, elles sont raccourcies (plus réactives).

**7. Fibonacci Retracement** — identifie les niveaux de support et résistance basés sur les ratios de Fibonacci (23.6%, 38.2%, 50%, 61.8%). Un pullback vers le niveau 61.8% dans une tendance haussière est un point d'entrée classique. La conviction est maximale quand le prix rebondit exactement sur un niveau Fibonacci avec confirmation RSI.

**8. Ichimoku Cloud** — le système Ichimoku produit des signaux LONG quand le prix est au-dessus du nuage (Kumo), que la Tenkan-sen croise la Kijun-sen à la hausse, et que le Chikou Span confirme. La force du signal dépend de l'épaisseur du nuage : un nuage épais = support/résistance fort.

**9. Keltner Breakout** — similaire aux bandes de Bollinger mais utilise l'ATR au lieu de l'écart-type. Plus adapté pour détecter les breakouts de volatilité car l'ATR est moins sensible aux gaps.

**10. VWAP Reversion** — retour à la moyenne pondérée par le volume. Quand le prix s'écarte significativement du VWAP, il tend à y revenir. Très utilisé par les institutionnels.

**11. Multi-Signal** — combine plusieurs indicateurs en un méta-signal. Ne génère un GO que quand au moins 4 indicateurs sur 6 sont alignés. Moins de trades, mais meilleure qualité.

**12. Momentum Rotation** — détecte les rotations sectorielles en comparant la force relative de différents secteurs. Quand un secteur passe de sous-performance à surperformance, les actifs du secteur reçoivent un boost.

Les deux dernières — **Microstructure** (analyse du carnet d'ordres) et **CNN Pattern Recognition** (détection de patterns graphiques par réseau neuronal) — sont des placeholders pour les phases ultérieures du développement.

---

### Chapitre 19 : Sélection de Stratégie et Strategy Decay

Avec 14 stratégies disponibles, le système doit choisir la meilleure pour chaque actif dans le contexte actuel. Ce choix repose sur deux piliers : la **matrice de performance empirique** et la **détection du decay**.

**La matrice de sélection**

Chaque stratégie est évaluée pour chaque actif via un backtest historique. Le résultat est un Sharpe ratio par combinaison stratégie × actif. Par exemple :

| Actif | Trend | Mean Rev | Breakout | Momentum | Fibonacci | Ichimoku |
|-------|-------|----------|----------|----------|-----------|----------|
| AAPL | 1.85 | 0.42 | 1.12 | 1.95 | 1.30 | 0.89 |
| BTC-USD | 0.92 | 1.45 | 1.78 | 0.88 | 0.65 | 0.72 |
| EURUSD | 0.45 | 1.65 | 0.55 | 0.38 | 1.20 | 1.10 |

Le Sharpe de backtest est ensuite ajusté par un **boost de régime**. Si le régime actuel est BULL, les stratégies de tendance reçoivent un bonus (+0.15 pour Trend Following, +0.10 pour Momentum). Si c'est un RANGE, Mean Reversion reçoit +0.20.

Le classement ajusté détermine quelle stratégie est sélectionnée.

**Le Strategy Decay**

Les marchés évoluent. Une stratégie qui fonctionnait parfaitement pendant 5 ans peut perdre son edge du jour au lendemain. Le système surveille 4 métriques de santé pour chaque stratégie :

- **Win Rate** — le taux de trades gagnants. En dessous de 35%, la stratégie est suspecte.
- **Profit Factor** — les gains bruts divisés par les pertes brutes. En dessous de 0.8, la stratégie perd de l'argent.
- **Sharpe Live** — le Sharpe calculé sur les trades réels (pas le backtest). Si le Sharpe live diverge fortement du Sharpe backtest, la stratégie ne se comporte plus comme prévu.
- **Consistance** — l'écart-type des rendements par trade. Une consistance trop faible (écart-type > 0.15) signifie que les résultats sont erratiques.

Quand une stratégie échoue sur 2 ou plus de ces 4 critères, son score de santé tombe sous 40/100 et elle est mise en **QUARANTINE**. Elle est alors automatiquement exclue de la sélection — le système choisit la stratégie suivante dans le classement.

La quarantaine n'est pas permanente. Chaque semaine, le système réévalue les stratégies en quarantaine avec les données les plus récentes. Si les conditions de marché changent (par exemple, un passage de RANGE à BULL peut redonner vie à une stratégie de tendance), la stratégie peut être réhabilitée.

Le minimum de 20 trades est requis avant toute évaluation — on ne juge pas une stratégie sur 5 trades.

---

### Chapitre 20 : Les Catalyseurs

Un catalyseur est un événement qui transforme un potentiel de mouvement en mouvement réel. Sans catalyseur, même un actif parfaitement configuré (bons fondamentaux, bonne technique, bon sentiment) peut stagner indéfiniment.

Le système intègre les catalyseurs à deux niveaux : comme filtre de timing dans le scoring, et comme signal d'alerte dans le monitoring des positions.

**Types de catalyseurs :**

**Les Earnings** — les résultats trimestriels sont le catalyseur le plus prévisible et le plus puissant pour les actions. Un signal GO la veille des earnings est traité avec une prudence spéciale : la conviction est réduite de 20% et la taille de position est plafonnée, car le mouvement post-earnings est binaire et imprévisible.

**Les décisions de la Fed (FOMC)** — 8 réunions par an qui décident des taux directeurs. Un changement de taux inattendu peut faire bouger l'ensemble du marché de 2-3% en quelques minutes. Le système augmente les trailing stops la veille d'un FOMC et réduit les nouvelles entrées.

**Les données économiques** — NFP (emploi), CPI (inflation), PIB. Chaque donnée a un impact potentiel sur des classes d'actifs spécifiques. Un CPI plus élevé que prévu → baissier pour les actions tech (anticipation de hausse des taux), haussier pour le dollar.

**Les événements crypto** — halving Bitcoin (tous les 4 ans), upgrades réseau (Ethereum Shanghai, Solana Firedancer), décisions réglementaires (approbation d'ETF). Ces événements sont souvent annoncés longtemps à l'avance mais leur impact sur le prix peut être explosif.

**Les événements corporate** — approbation FDA, contrat majeur, changement de CEO, spin-off. Moins prévisibles mais souvent détectés en amont par le module Sentiment (mentions anormales sur Reddit ou dans les news).

**L'ajustement catalyseur dans le scoring :**

Le Signal Shelf Life (durée de vie du signal) est directement impacté par la proximité d'un catalyseur. Un signal de Trend Following a normalement une durée de vie de 72 heures. Mais si un FOMC est dans 24 heures, cette durée est réduite à 36 heures — le contexte va changer, le signal pourrait être invalidé.

À l'inverse, un catalyseur confirmé (earnings beat de +20%, approbation FDA) peut *allonger* la durée de vie du signal : le mouvement impulsé par le catalyseur peut durer plusieurs jours.

---

### Chapitre 21 : Signaux Inter-Marchés

Les marchés ne sont pas des silos isolés. Les actions tech réagissent aux taux d'intérêt. L'or monte quand le dollar baisse. Le Bitcoin suit parfois le Nasdaq, parfois l'or, parfois rien du tout. Ces relations inter-marchés sont une source de signaux puissante — et sous-exploitée.

**Le Lead-Lag**

Certains actifs bougent *avant* d'autres. L'indice des semi-conducteurs (SMH) tend à anticiper les mouvements du Nasdaq de 1-3 jours. Le cuivre (HG) anticipe parfois les cycles économiques. Le VIX se retourne avant le S&P 500.

Le système détecte automatiquement ces relations lead-lag en calculant la corrélation décalée entre paires d'actifs. Si la corrélation entre SMH(t) et QQQ(t+2) est plus élevée que la corrélation simultanée SMH(t)/QQQ(t), alors SMH *lead* QQQ de 2 jours. Un mouvement significatif de SMH aujourd'hui peut prédire un mouvement de QQQ dans 2 jours.

**La Rotation Sectorielle**

Le modèle de rotation sectorielle suit un cycle classique lié aux phases de l'économie :

```
Creux économique → Finance, Industrie
Reprise          → Tech, Consommation cyclique
Expansion        → Énergie, Matériaux
Pic              → Défensif (Santé, Utilities)
Contraction      → Cash, Obligations
```

Le système mesure la performance relative de chaque secteur sur 1, 4 et 12 semaines. Quand un secteur sous-performant commence à surperformer (rotation positive), les actifs de ce secteur reçoivent un bonus dans le scanner. Quand un secteur surperformant commence à sous-performer (rotation négative), les positions dans ce secteur sont signalées pour un resserrement des stops.

**La Contagion Cross-Asset**

Le Reversal Guard du Module 5 surveille 5 benchmarks cross-asset : SPY (actions US), QQQ (tech), IWM (small caps), GLD (or), TLT (obligations). Quand 4 ou 5 de ces benchmarks baissent simultanément de plus de 2% sur 5 jours, c'est un signal de sell-off généralisé — une situation rare et dangereuse où les corrélations entre classes d'actifs augmentent brutalement (tout baisse en même temps, même les actifs théoriquement décorrélés).

Dans ce cas, le système passe en mode défensif : fermeture de toutes les positions LONG, pas de nouvelle entrée, resserrement maximal des stops sur les positions restantes.

---

# PARTIE IV — LE SCORING (Module 3)

---

## Section 4 — La Décision : Aller ou Ne Pas Aller

---

### Chapitre 22 : Architecture du Score V2

Le Module 1 a filtré les actifs. Le Module 2 a identifié le régime et la stratégie. Le Module 3 doit maintenant répondre à la question la plus importante : **faut-il y aller, et avec combien ?**

Le Score V2 est le coeur décisionnel du pipeline. Il fusionne 4 sources d'information en un score unique entre 0 et 100, assorti d'une recommandation : **GO**, **WAIT** ou **NO_TRADE**.

**Les 4 sources du Score V2 :**

| Source | Poids par défaut | Ce qu'elle mesure |
|--------|-----------------|-------------------|
| **Conviction stratégie** | 35% | La confiance du Module 2 dans sa stratégie sélectionnée |
| **Score Bayésien** | 30% | La combinaison prior historique + observations actuelles |
| **Qualité du Contexte (SQC)** | 20% | Les conditions de marché sont-elles favorables à un trade ? |
| **Score Scanner** | 15% | Le score composite du Module 1 (convergence des 10 critères) |

**Les poids ne sont pas fixes.** Le Scoring Calibrator (Module d'apprentissage) ajuste ces poids quotidiennement en se basant sur le taux de détection des top movers. Si le système rate trop de grands mouvements (taux de détection < 30%), les poids sont modifiés : la conviction et le scanner gagnent du poids, le bayésien en perd. Si le taux est bon (> 50%), les poids sont maintenus. Les ajustements sont progressifs (max ±5% par itération) et les poids sont renormalisés pour totaliser 100%.

**La formule :**

```
Score V2 = Conviction × w₁ + Bayésien × w₂ + SQC × w₃ + Scanner × w₄
```

**Les seuils de décision :**

| Score V2 | Décision | Action |
|----------|----------|--------|
| ≥ 65 | **GO** | Signal validé — passer à l'exécution |
| 50-64 | **WAIT** | Signal potentiel — surveiller, pas encore prêt |
| < 50 | **NO_TRADE** | Pas d'avantage — ne pas trader |

Un score de 65 peut sembler modeste. Mais souvenez-vous : pour atteindre 65, il faut que la conviction soit élevée (la stratégie a un bon backtest et le régime est favorable), que le bayésien soit positif (l'historique de l'actif est bon ET les observations actuelles confirment), que le contexte soit correct (liquidité, pas de volatilité extrême), et que le scanner ait détecté l'actif en premier lieu.

Un **filtre supplémentaire** vérifie que le Kelly sizing est positif — c'est-à-dire que le ratio risque/rendement justifie mathématiquement le trade. Si le Kelly est à zéro (R:R insuffisant ou win rate estimé trop bas), le signal est rejeté même si le Score V2 dépasse 65.

---

### Chapitre 23 : Le Score Bayésien Adaptatif

Le théorème de Bayes est l'un des outils les plus puissants de la statistique. Il permet de combiner une croyance préalable (le *prior*) avec de nouvelles observations (le *likelihood*) pour produire une croyance mise à jour (le *posterior*).

Appliqué au trading :

- **Prior** = ce que l'historique de l'actif nous dit. L'actif a-t-il tendance à monter ? Ses rendements mensuels sont-ils consistants ? Où est-il dans son range de 52 semaines ?

- **Likelihood** = ce que les observations actuelles nous disent. Le scanner lui donne un bon score, la stratégie a une forte conviction, le régime est identifié avec confiance.

- **Posterior** = notre croyance mise à jour. L'actif mérite-t-il un trade *maintenant* ?

**Le calcul du prior historique :**

```
Prior = Performance 6 mois × 0.40 + Consistance mensuelle × 0.30 + Position dans range × 0.30
```

La performance 6 mois est le rendement de l'actif sur 126 jours, mappé sur une échelle 0-100. La consistance mesure le pourcentage de mois positifs sur les 6 derniers mois (6/6 mois positifs = score de 100). La position dans le range 52 semaines indique si l'actif est proche de ses plus hauts (momentum positif) ou de ses plus bas.

**Le calcul du likelihood :**

```
Likelihood = Scanner × 0.40 + Conviction stratégie × 0.40 + Confiance régime × 0.20
```

Le likelihood est ensuite modulé par la confiance du régime. Si le régime est détecté avec une haute confiance (> 80%), on fait davantage confiance aux observations actuelles. Si la confiance est faible (< 30%), on s'appuie davantage sur l'historique.

**L'adaptation des poids :**

C'est la partie la plus élégante. Les poids entre prior et likelihood s'ajustent automatiquement :

```
Poids observations = 0.4 + confiance_régime × 0.4    (entre 0.4 et 0.8)
Poids prior = 1.0 - poids_observations               (entre 0.2 et 0.6)
```

En régime BULL avec 85% de confiance → les observations pèsent 74%, le prior 26%. Le système "écoute" davantage les signaux actuels car le contexte est clair.

En régime TRANSITION avec 35% de confiance → les observations pèsent 54%, le prior 46%. Le système "se souvient" de l'historique car le contexte est incertain.

Le posterior final est clippé entre 0 et 100. Un posterior de 75+ combiné à une forte conviction est un signal robuste.

---

### Chapitre 24 : Qualité du Contexte et Shelf Life

Le SQC (Score de Qualité du Contexte) répond à une question que la plupart des systèmes ignorent : **les conditions sont-elles favorables à un trade, même si le signal est bon ?**

Un signal parfait à 2h du matin sur un actif illiquide est un piège. Le spread sera large, l'exécution sera mauvaise, et le slippage mangera le profit potentiel.

**Les 3 composantes du SQC :**

**1. Liquidité (40%)** — compare le volume actuel à la moyenne sur 20 jours. Un ratio > 2.0 = 95/100 (volume exceptionnel, exécution parfaite). Un ratio < 0.5 = 25/100 (volume très faible, mauvais contexte). Le volume est le sang du marché : sans volume, les ordres ne sont pas exécutés correctement.

**2. Heure de marché (20%)** — les heures ne se valent pas toutes. L'ouverture (9h30-10h30 EST) et la clôture (15h-16h EST) sont les moments les plus liquides. Le déjeuner (12h-14h EST) est le pire moment pour trader — volume faible, mouvements erratiques. Hors marché = 30/100.

**3. Contexte de volatilité (40%)** — mesure le range intraday normalisé (high - low / close) par rapport à sa moyenne sur 20 jours. Un ratio entre 0.8 et 1.5 est normal → 80/100. Au-dessus de 2.5 → volatilité extrême, danger → 20/100. En dessous de 0.5 → marché mort → 45/100.

```
SQC = Liquidité × 0.40 + Heure × 0.20 + Volatilité × 0.40
```

**Le Signal Shelf Life :**

Chaque signal a une durée de vie. Un signal de breakout est éphémère (8 heures) — si le breakout n'est pas exploité rapidement, le prix peut retomber dans le range. Un signal de trend following dure plus longtemps (72 heures) — la tendance ne s'inverse pas en quelques heures.

La durée de base est modifiée par 3 facteurs :

| Facteur | Effet |
|---------|-------|
| Régime CRISIS | × 0.5 (tout va vite en crise) |
| Régime BULL | × 1.2 (les tendances durent) |
| Conviction > 80 | × 1.3 (on peut attendre le bon prix) |
| Conviction < 40 | × 0.6 (agir vite ou pas du tout) |

La durée de vie détermine le **type d'ordre optimal** :
- < 4 heures → ordre Market (exécution immédiate)
- 4-24 heures + bon SQC → ordre Limit (patience pour un meilleur prix)
- > 24 heures → ordre Limit (pas d'urgence)

---

### Chapitre 25 : La Thèse de Trade Complète

Le output du Module 3 n'est pas un simple "acheter" ou "vendre". C'est une **Thèse de Trade** structurée qui contient toutes les informations nécessaires pour l'exécution :

```
═══════════════════════════════════════════════
THÈSE DE TRADE — HIMS
═══════════════════════════════════════════════
Action       : GO
Direction    : LONG
Stratégie    : Momentum Adaptatif
Score V2     : 68.2 / 100

Régime       : BULL (confiance 65%)
Conviction   : 72%

Prix :
  Entrée     : $28.39
  Stop-Loss  : $24.80  (−12.6%)
  TP1        : $33.77  (+18.9%)
  TP2        : $36.46  (+28.4%)
  R:R ratio  : 1.50

Scores :
  Scanner    : 63.4
  Bayésien   : 61.8 (prior 55.2, likelihood 68.1)
  SQC        : 72.0 (liquidité 85, heure 70, vol 65)
  Shelf Life : Moyen (48h) → Ordre LIMIT

Sizing :
  Kelly frac : 4.2%
  Taille     : 1 action ($28.39)
  Risque     : $3.59 (1.2% du capital)
═══════════════════════════════════════════════
```

**Le Stop-Loss** est placé à 2 × ATR sous le prix d'entrée. L'ATR (Average True Range) mesure la volatilité moyenne quotidienne. Un SL à 2 ATR laisse assez de marge pour les fluctuations normales tout en protégeant contre un mouvement adverse significatif. Si l'ATR est de $1.80, le SL est à $28.39 - 2 × $1.80 = $24.80.

**Le Take-Profit 1** est à 3 × ATR au-dessus de l'entrée, soit un ratio R:R de 1.5. Le **TP2** est à 1.5 × la distance du TP1 — une cible plus ambitieuse pour le cas où le mouvement serait explosif.

**Le ratio R:R minimum** est de 1.0. En dessous, le Kelly est négatif et le trade est rejeté, quel que soit le score. C'est une protection mathématique fondamentale : même avec un win rate de 60%, un R:R de 0.5 est un trade perdant à long terme.

La thèse complète est envoyée au Module 4 (Exécution) qui se charge de la transformer en ordres concrets.

---

### Chapitre 26 : Le Sizing Kelly

Combien risquer sur chaque trade ? C'est peut-être la question la plus importante — et la plus souvent mal gérée — du trading. Trop peu et les gains sont insignifiants. Trop et une série de pertes peut être fatale.

**Le critère de Kelly** fournit la réponse mathématiquement optimale :

```
f* = (p × b − q) / b
```

Où :
- `p` = probabilité de gain (win rate estimé)
- `q` = probabilité de perte (1 − p)
- `b` = ratio gain/perte (R:R)

**Exemple :** avec un win rate de 55% et un R:R de 1.5 :
```
f* = (0.55 × 1.5 − 0.45) / 1.5 = (0.825 − 0.45) / 1.5 = 0.25 = 25%
```

Kelly recommande de risquer 25% du capital sur ce trade. C'est mathématiquement optimal pour maximiser la croissance du capital à long terme.

**Le problème du Kelly pur :**

25% sur un seul trade est terriblement agressif. Une série de 3 pertes consécutives (qui arrivera tôt ou tard) réduit le capital de 42%. Le Kelly pur maximise la croissance *à l'infini* — mais le chemin pour y arriver est une montagne russe insupportable.

**Le Fractional Kelly :**

Bilok-TradePilot utilise un **Kelly fractionnaire à 25%** — c'est-à-dire 1/4 du Kelly optimal. Dans notre exemple, au lieu de 25%, on risque 6.25%. C'est plus conservateur, la croissance est plus lente, mais le drawdown maximum est drastiquement réduit.

```
Fraction Kelly = f* × 0.25
```

**Les gardes-fous supplémentaires :**

| Règle | Valeur | Raison |
|-------|--------|--------|
| **Plafond par trade** | 15% du capital | Même un score parfait ne justifie pas plus |
| **Win rate minimum** | 35% | En dessous, aucun sizing n'est profitable |
| **R:R minimum** | 1.0 | En dessous, le Kelly est négatif |
| **Base minimum** | 5% du capital | Chaque trade a au moins un poids significatif |

**L'estimation du win rate :**

En Phase 1 (paper trading, pas d'historique), le win rate est estimé à partir du score bayésien et de la conviction. Un score de 50 → win rate estimé de ~45%. Un score de 70 → ~55%. Un score de 90 → ~65%.

En Phase 2+ (historique de trades réels), le win rate est remplacé par le **win rate live** de la stratégie pour cet actif — une mesure directe et empirique.

**L'Expected Value :**

Chaque signal GO est accompagné d'une valeur attendue (EV) :

```
EV = win_rate × R:R − (1 − win_rate)
```

Un EV positif signifie que le trade est mathématiquement profitable à long terme. Un EV de 0.3 signifie que pour chaque dollar risqué, on s'attend à gagner 0.30$ en moyenne. Les signaux sont triés par EV décroissante — les meilleurs trades en premier.

---

# PARTIE V — L'EXÉCUTION (Module 4)

---

## Section 5 — De la Décision à l'Ordre

---

### Chapitre 27 : Architecture Multi-Broker

Le Module 3 produit une thèse de trade. Le Module 4 doit la transformer en ordres concrets chez un ou plusieurs brokers. Bilok-TradePilot utilise une architecture multi-broker pour combiner les avantages de chaque plateforme.

**Alpaca** — le broker principal pour le paper trading et les actions US. API REST simple, pas de minimum de compte, paper trading gratuit. Supporte les bracket orders (entry + SL + TP en une seule commande), ce qui garantit que le SL et le TP sont actifs même si le système tombe en panne. Limité aux actions et ETF cotés aux États-Unis.

**Interactive Brokers (IBKR)** — le broker pour le trading réel et les marchés internationaux. Supporte les actions US et européennes (Paris, Francfort, Zurich, Londres), le forex, les futures sur matières premières (or, pétrole, cuivre), et les cryptomonnaies via Paxos. Nécessite TWS ou IB Gateway en cours d'exécution sur la machine locale.

**La logique de priorité :**

Quand un signal GO est validé, le système l'envoie aux deux brokers simultanément :

1. **IBKR en priorité** — les meilleurs signaux (triés par score décroissant) sont d'abord alloués à IBKR car c'est le compte réel. Maximum 10 positions IBKR.

2. **Alpaca en parallèle** — reçoit les mêmes signaux pour le paper trading et le suivi. Alpaca sert aussi de filet de sécurité : si IBKR échoue (connexion perdue, marge insuffisante), la position est quand même tracée chez Alpaca.

**Le mapping des symboles :**

Les symboles varient entre brokers. Yahoo Finance utilise `BTC-USD`, IBKR utilise le symbole `BTC` avec le type de contrat `CRYPTO` sur l'échange `PAXOS`. Le système maintient une table de correspondance qui traduit automatiquement :

```
TradePilot     →  IBKR
BTC-USD        →  BTC / CRYPTO / PAXOS / USD
EURUSD=X       →  EUR / CASH / IDEALPRO / USD
GC=F           →  GC / FUT / COMEX / USD
MC.PA          →  MC / STK / SBF / EUR
SAP.DE         →  SAP / STK / IBIS / EUR
```

**Les Client IDs :**

IBKR ne supporte qu'une connexion par Client ID. Pour éviter les conflits entre les différentes fonctions du système, chaque usage a un ID unique : le broker singleton (ID 1), le TP/SL monitor (ID 10), et l'achat depuis la queue (ID 11).

---

### Chapitre 28 : L'Entrée en 3 Tranches

Entrer dans une position en une seule fois est risqué : si le prix se retourne immédiatement après l'entrée, la perte est maximale. Le scaling in — entrer progressivement — réduit ce risque en moyennant le prix d'entrée.

Bilok-TradePilot utilise un plan de 3 tranches avec des conditions de progression :

| Tranche | Taille | Condition | Logique |
|---------|--------|-----------|---------|
| **T1** | 40% | Signal GO | Pied dans la porte — tester le mouvement |
| **T2** | 35% | Prix confirme (direction favorable) | Le mouvement démarre — renforcer |
| **T3** | 25% | Momentum soutenu | Le mouvement est solide — compléter |

**Pourquoi 40/35/25 et pas 33/33/34 ?**

La première tranche est la plus grande car c'est elle qui a le meilleur prix moyen (le signal vient d'être généré). Les tranches suivantes sont plus petites car le risque de retournement augmente avec le temps et le mouvement déjà accompli.

**En pratique :**

Avec un capital alloué de $1,000 et un prix d'entrée de $28.39 :
- T1 : 14 actions × $28.39 = $397 (40%)
- T2 : 12 actions × $29.50 = $354 (si le prix a monté de 4%)
- T3 : 9 actions × $30.20 = $272 (si le momentum est soutenu)

Le prix moyen d'entrée (14 × 28.39 + 12 × 29.50 + 9 × 30.20) / 35 = $29.24 au lieu de $28.39. Le prix moyen est légèrement plus haut, mais le risque est considérablement réduit : si le prix se retourne après T1, la perte est limitée à 40% de la position prévue.

**Le bracket order Alpaca :**

Pour chaque tranche, un bracket order est envoyé — c'est un ordre composite qui inclut l'entrée + le SL + le TP dans une seule commande côté serveur. Même si le Mac s'éteint, perd la connexion internet, ou plante, le SL et le TP restent actifs chez Alpaca. C'est une protection critique contre les pannes techniques.

---

### Chapitre 29 : Correction des Biais Comportementaux

L'une des promesses fondamentales de Bilok-TradePilot est de protéger le trader de ses propres émotions. Le Bias Detector est un sous-module qui analyse le comportement récent du système (et de l'utilisateur, le cas échéant) pour détecter 4 biais classiques.

**1. Le Disposition Effect**

Le biais : on vend trop tôt les gagnants et on garde trop longtemps les perdants. Neurologiquement, le plaisir de sécuriser un gain est plus fort que le plaisir d'un gain supplémentaire potentiel. Et la douleur de réaliser une perte est si forte qu'on préfère espérer un retournement.

La correction : le système ne ferme *jamais* un trade gagnant avant le TP (sauf si le trailing stop est touché). Et il ferme *toujours* un trade perdant au SL, sans exception. Pas de "juste un peu plus" ni de "ça va remonter".

**2. Le Revenge Trading**

Le biais : après une perte, la tentation de "se refaire" pousse à prendre un trade immédiat, souvent plus gros et moins réfléchi. C'est la recette du désastre.

La correction : le Bias Detector vérifie si la dernière position fermée était perdante. Si oui, et si un nouveau signal GO apparaît dans les 30 minutes, un avertissement est émis. La taille de la position suivante est automatiquement réduite de 20%. Le temps de cooling-off laisse les émotions se dissiper.

**3. Le FOMO (Fear Of Missing Out)**

Le biais : quand un actif monte de 15% sans nous, la douleur de l'opportunité manquée nous pousse à acheter — au pire moment, quand le mouvement est presque terminé.

La correction : le système ne poursuit jamais un mouvement. Si un actif a déjà bougé de plus de 10% dans la journée, le signal est marqué comme "potentiellement FOMO" et la conviction est réduite. Le système attend un pullback plutôt que de courir après le prix.

**4. L'Over-Trading**

Le biais : l'illusion que l'activité égale la productivité. Chaque trade a un coût (commission, spread, slippage). Trop de trades, même médiocrement profitables, mangent le capital par friction.

La correction : le système compte le nombre de trades passés aujourd'hui et sur la semaine. Si le rythme dépasse le seuil normal (configuré selon le style de trading), un avertissement est émis et la conviction minimale pour un GO est relevée temporairement.

**L'impact concret :**

Avant chaque exécution, le Bias Detector produit un rapport :

```
Biais vérifiés : 4/4
- Disposition : OK (pas de trade gagnant fermé prématurément)
- Revenge : OK (dernière fermeture il y a 3h, profitable)
- FOMO : ATTENTION (HIMS +8.2% aujourd'hui — prudence)
- Over-trading : OK (3 trades cette semaine, seuil 10)
```

Les avertissements ne bloquent pas l'exécution (sauf en cas d'over-trading extrême), mais ils ajustent la taille de position à la baisse.

---

### Chapitre 30 : La Gestion Post-Entrée

Une fois la position ouverte, le travail ne fait que commencer. Le Module 4 surveille en continu chaque position à travers trois mécanismes complémentaires.

**Le Trailing Stop**

Le trailing stop est un SL qui *remonte avec le prix* mais ne redescend jamais. C'est le mécanisme le plus efficace pour protéger les gains tout en laissant le trade respirer.

La logique est simple :
- **LONG** : si le prix fait un nouveau plus haut, le SL monte à (nouveau plus haut − 2 × ATR). Si le prix baisse ensuite, le SL ne bouge pas.
- **SHORT** : si le prix fait un nouveau plus bas, le SL descend à (nouveau plus bas + 2 × ATR).

Le trailing stop ne s'active que quand la position est en profit (prix actuel > prix d'entrée). Tant que la position est en perte, le SL initial reste en place.

Le monitor vérifie les positions toutes les 5 minutes pendant les heures de marché. À chaque vérification, il recalcule l'ATR et ajuste le trailing stop si nécessaire.

**L'Exhaustion Checker**

Un trade peut atteindre ni son TP ni son SL mais simplement... s'essouffler. Le mouvement ralentit, le volume sèche, le momentum s'éteint. Rester dans un trade essoufflé, c'est immobiliser du capital pour rien.

L'Exhaustion Checker évalue la santé de chaque position ouverte à travers **5 signaux** :

| Signal | Ce qu'il mesure | FORT | MODÉRÉ | FAIBLE |
|--------|----------------|------|--------|--------|
| **Momentum** | Rendement 5j vs 20j | +5% accélérant | +2% ralentit | Négatif |
| **Volume** | Volume 5j / moyenne 20j | > 1.2x | 0.8-1.2x | < 0.8x |
| **Narrative** | Score narrative du mouvement | > 65/100 | 50-65 | < 50 |
| **RSI** | Zone de l'oscillateur | 60-70 haussier | 40-60 neutre | > 75 suracheté |
| **P/L** | Progression du profit | > +5% | 0 à +5% | Négatif |

Le score de santé est la moyenne des 5 composantes. **4 niveaux** d'action :

- **FORT (≥ 70)** — le trade a encore du jus. Garder la position, trailing stop normal.
- **MODÉRÉ (50-69)** — ça ralentit. Resserrer le trailing stop de 2 ATR à 1.5 ATR.
- **FAIBLE (35-49)** — essoufflé. Si en profit → resserrer à 1 ATR. Si en perte → fermer.
- **ÉPUISÉ (< 35)** — le mouvement est fini. Fermer la position immédiatement.

Une protection d'urgence supplémentaire ferme toute position en perte de plus de 10%, quel que soit le score de santé.

**Le TP/SL Monitor**

Le TP/SL Monitor est le gardien de dernière ligne. Il vérifie toutes les 5 minutes que les bracket orders Alpaca fonctionnent correctement. Les bracket orders peuvent parfois échouer silencieusement (bug d'API, problème réseau), laissant une position sans protection.

Le monitor vérifie le prix actuel par rapport au SL et TP enregistrés en base de données. Si le SL ou TP est atteint mais que le bracket order n'a pas exécuté, le monitor ferme la position manuellement. C'est un filet de sécurité critique — la dernière ligne de défense contre une perte non contrôlée.

Le monitor vérifie aussi les **signaux GO inverses** : si une position LONG est ouverte sur AAPL et qu'un nouveau signal GO SHORT apparaît pour AAPL, la position LONG est fermée et une position SHORT est ouverte automatiquement (retournement).

---

### Chapitre 31 : L'Arbitrage d'Opportunité

Le capital est limité. Chaque dollar immobilisé dans une position est un dollar qui ne peut pas saisir une meilleure opportunité. L'arbitrage d'opportunité compare en continu les positions ouvertes avec les signaux en attente.

**L'EV/jour (Expected Value par jour)**

Chaque position ouverte et chaque signal en attente est évalué par sa valeur attendue divisée par la durée prévue du trade :

```
EV/jour = (win_rate × R:R − (1 − win_rate)) / durée_estimée_jours
```

Un trade avec un EV de 0.30 sur 10 jours a un EV/jour de 0.03. Un nouveau signal avec un EV de 0.25 sur 3 jours a un EV/jour de 0.083 — presque 3 fois plus efficace en termes de rendement du capital.

**Le classement unifié**

Le système maintient un classement unifié de toutes les positions ouvertes et de tous les signaux en attente, trié par EV/jour décroissant. Si un signal en attente a un EV/jour significativement supérieur à une position ouverte, le système recommande un swap : fermer la position existante pour ouvrir la nouvelle.

Le swap n'est pas automatique — il y a un seuil minimum d'amélioration (le nouveau signal doit avoir un EV/jour au moins 50% supérieur) pour couvrir les frais de transaction du swap.

---

### Chapitre 32 : La File d'Attente Intelligente

Bilok-TradePilot limite le nombre de positions simultanées à **20** (configurable). Quand toutes les positions sont prises, les nouveaux signaux GO ne sont pas perdus — ils sont placés dans une **file d'attente** triée par score décroissant.

**Le fonctionnement :**

1. Un signal GO arrive mais les 20 slots sont occupés → le signal est ajouté à la queue avec son score et son timestamp.

2. La queue est maintenue triée par score décroissant. Le meilleur signal est toujours en première position.

3. Les doublons sont évités : si un symbole est déjà dans la queue, il n'est pas ajouté une deuxième fois.

**Le remplacement automatique :**

Quand une position se ferme (SL touché, TP atteint, essoufflement détecté, ou fermeture manuelle), le système remplit automatiquement le slot libéré :

1. Vérifier que la santé du premier signal en attente est suffisante (seuil appris par l'Entry Quality Tracker, par défaut 45/100).
2. Calculer le sizing centralisé (basé sur l'equity actuelle, pas le capital initial).
3. Placer un bracket order chez les deux brokers.
4. Enregistrer la position en base de données.
5. Retirer le signal de la queue.

**La priorité IBKR :**

IBKR (le compte réel) a la priorité sur Alpaca (paper trading). Les premiers signaux de la queue sont d'abord alloués à IBKR (jusqu'à 10 positions), puis les suivants vont chez Alpaca. Cela garantit que le compte réel reçoit toujours les meilleurs signaux disponibles.

Si IBKR échoue (connexion perdue, marge insuffisante), le signal est quand même exécuté chez Alpaca pour le tracking.

---

# PARTIE VI — LE PORTEFEUILLE (Module 5)

---

## Section 6 — Gérer le Risque Global

---

### Chapitre 33 : Risk Parity Dynamique

Le Module 4 gère les positions individuelles. Le Module 5 gère le **portefeuille** — l'ensemble des positions comme un tout. La question n'est plus "ce trade est-il bon ?" mais "l'ensemble de mes trades crée-t-il un risque que je ne vois pas ?"

Le Risk Parity repose sur un principe simple mais puissant : répartir le **risque** de manière égale, pas le **capital**. Un actif très volatil (BTC, ATR quotidien de 5%) devrait avoir une plus petite position en dollars qu'un actif stable (JNJ, ATR quotidien de 0.8%) pour que les deux contribuent de manière égale au risque total du portefeuille.

**Le filtre de corrélation :**

Avant d'ajouter une nouvelle position, le système vérifie la corrélation entre le nouvel actif et toutes les positions existantes sur les 60 derniers jours :

| Corrélation | Action | Sizing Modifier |
|-------------|--------|-----------------|
| > 0.85 | Position fortement réduite | × 0.3 |
| 0.70 - 0.85 | Position réduite de moitié | × 0.5 |
| 0.50 - 0.70 | Légère réduction | × 0.8 |
| 0.30 - 0.50 | Position normale | × 1.0 |
| < 0.30 | Bonus de diversification | × 1.1 |

Si 3 positions ou plus sont fortement corrélées (> 0.7), l'ajout d'une nouvelle position corrélée est **bloqué**. Le risque de concentration est trop élevé — un seul mouvement de marché affecterait 4+ positions simultanément.

Le bonus de diversification (× 1.1) récompense les actifs qui réduisent le risque global du portefeuille. Ajouter de l'or (GLD) à un portefeuille d'actions tech est presque toujours bénéfique car la corrélation est historiquement faible.

**L'allocation dynamique :**

Les poids du portefeuille ne sont pas fixés une fois pour toutes. Chaque nuit, le pipeline recalcule l'allocation optimale en fonction des corrélations actuelles, de la volatilité de chaque actif, et du régime de marché. En période de crise (corrélations qui augmentent brutalement), le système réduit automatiquement l'exposition globale.

---

### Chapitre 34 : Stress Testing

Comment le portefeuille se comporterait-il si Mars 2020 se reproduisait ? Si les cryptos crashaient de 60% en une semaine ? Si la Fed montait les taux de 100 points de base d'un coup ?

Le stress testing répond à ces questions en simulant des scénarios historiques et hypothétiques :

**Scénarios historiques :**

| Scénario | Période | Impact typique |
|----------|---------|----------------|
| **COVID Crash** | Mars 2020 | SPY −34% en 23 jours |
| **Crypto Winter** | Nov 2021 - Nov 2022 | BTC −77%, ETH −82% |
| **Volmageddon** | Février 2018 | VIX de 10 à 50 en 1 jour |
| **Flash Crash** | Mai 2010 | SPY −9% en 36 minutes |
| **Taper Tantrum** | Mai-juin 2013 | Obligations −4%, EM −15% |

Pour chaque scénario, le système recalcule les rendements de chaque position en appliquant les beta historiques de l'actif par rapport au benchmark pendant la période de stress. Un portefeuille diversifié (actions + or + obligations) résistera mieux qu'un portefeuille concentré en tech.

**Scénarios hypothétiques :**

- **Black Swan** — toutes les corrélations passent à 1.0 (tout baisse en même temps), volatilité × 3. Perte estimée : drawdown maximum.
- **Taux +200bps** — hausse brutale des taux d'intérêt. Les actions growth et les obligations chutent, les financières montent.
- **Dollar collapse** — DXY −15%. Les actifs libellés en non-USD et l'or montent, les actifs US baissent en valeur réelle.

Le résultat du stress test est un **drawdown maximum estimé** pour le portefeuille actuel sous chaque scénario. Si ce drawdown dépasse un seuil configurable (par défaut −25%), le système réduit l'exposition.

---

### Chapitre 35 : Détection du Régime Portefeuille

Le Module 2 détecte le régime de chaque actif individuel. Le Module 5 détecte le régime du **portefeuille dans son ensemble** — ce qui est une information différente et complémentaire.

**Les 3 régimes portefeuille :**

**ALPHA** — le portefeuille surperforme son benchmark (SPY). Le Sharpe ratio est > 1.0, le win rate est > 50%, les positions en profit dépassent largement les positions en perte. Le système fonctionne comme prévu. Action : maintenir ou augmenter l'exposition.

**BETA** — le portefeuille performe comme son benchmark. Pas de surperformance significative. Le Sharpe est entre 0 et 1.0. Le système capture le beta du marché mais pas d'alpha. Action : revoir les stratégies, chercher des optimisations.

**STRESS** — le portefeuille sous-performe significativement. Le drawdown est > −10%, les positions en perte s'accumulent, le Sharpe est négatif. Le système est en difficulté. Action : réduire l'exposition de 30-50%, resserrer tous les stops, suspendre les nouvelles entrées jusqu'à stabilisation.

La détection utilise le Sharpe ratio sur fenêtre glissante de 20 jours, le drawdown depuis le peak, et le ratio positions gagnantes/perdantes.

Le régime portefeuille influence directement le Meta-Score (Module 6) et la boucle de feedback. En régime STRESS, le Meta-Score baisse, ce qui réduit automatiquement la taille des nouvelles positions et augmente les seuils de conviction minimum pour un GO.

---

### Chapitre 36 : Contrôle du Drawdown

Le drawdown est la mesure de risque la plus intuitive : c'est la perte depuis le plus haut point (peak equity). Un drawdown de −15% signifie que le capital a perdu 15% depuis son maximum historique.

Bilok-TradePilot mesure le drawdown quotidiennement grâce à l'Equity Tracker, qui enregistre l'equity du compte chaque jour :

```
Drawdown = (Equity actuelle / Peak Equity − 1) × 100
```

**Les niveaux d'intervention :**

| Drawdown | Niveau | Action |
|----------|--------|--------|
| 0% à −5% | **Normal** | Trading normal |
| −5% à −10% | **Attention** | Réduire sizing de 20%, resserrer stops |
| −10% à −15% | **Alerte** | Réduire sizing de 50%, pas de nouvelles positions |
| −15% à −20% | **Critique** | Fermer 50% des positions |
| > −20% | **Urgence** | Fermer toutes les positions, pause pipeline |

Le drawdown est suivi par broker (Alpaca et IBKR séparément) et pour le portefeuille global. L'equity est comparée à SPY (buy & hold) sur la même période pour vérifier si le drawdown est spécifique au système ou s'il reflète un mouvement général du marché.

**Le recovery ratio :**

Le drawdown est aussi mesuré en temps : combien de jours depuis le peak ? Un drawdown de −10% qui dure 5 jours est moins inquiétant qu'un drawdown de −5% qui dure 30 jours. Le second suggère une dégradation structurelle, pas un choc temporaire.

---

### Chapitre 37 : Le Reversal Guard

Le Reversal Guard est le bouclier ultime du portefeuille. Il surveille 5 signaux macro de retournement en temps réel et déclenche des actions de protection automatiques.

**Les 5 signaux :**

**1. Régime BEAR/CRISIS** (sévérité 2) — le Module 2 détecte un régime baissier ou de crise avec une probabilité combinée Bear + Crisis supérieure à 50%.

**2. Volatilité extrême** (sévérité 1-2) — la volatilité annualisée du SPY dépasse 20% (sévérité 1) ou 30% (sévérité 2). Le VIX est un indicateur de peur — quand il spike, les marchés sont en panique.

**3. Drawdown portefeuille** (sévérité 1-2) — le drawdown dépasse −5% (sévérité 1) ou −10% (sévérité 2) depuis le peak equity.

**4. Cassure SMA 200 sur SPY** (sévérité 1-2) — le S&P 500 passe sous sa moyenne mobile 200 jours. C'est l'un des signaux techniques les plus suivis au monde. Quand SPY est sous sa SMA 200, les probabilités de continuation baissière augmentent significativement.

**5. Sell-off généralisé** (sévérité 1-2) — au moins 3 des 5 benchmarks (SPY, QQQ, IWM, GLD, TLT) baissent de plus de 2% sur 5 jours. Quand tout baisse en même temps — actions, or et obligations — c'est le signe d'une panique systémique.

**Les 4 niveaux d'alerte :**

| Niveau | Condition | Action |
|--------|-----------|--------|
| **VERT** | 0-1 signal | Tout va bien. Trading normal. |
| **JAUNE** | 2 signaux | Vigilance. Resserrer les trailing stops. |
| **ORANGE** | 3 signaux | Réduire 30% de chaque position LONG. |
| **ROUGE** | 4-5 signaux | Fermer toutes les positions LONG immédiatement. |

L'action ROUGE est drastique mais nécessaire. Quand 4 signaux de retournement s'activent simultanément, la probabilité d'un crash majeur est très élevée. La protection du capital prime sur tout le reste. On pourra toujours revenir quand les conditions seront meilleures — mais seulement si le capital est encore là.

Le Reversal Guard est exécuté automatiquement par le pipeline nocturne et peut aussi être déclenché manuellement. Les ordres de protection sont envoyés à Alpaca et IBKR simultanément.

---

# PARTIE VII — LA PERFORMANCE (Module 6)

---

## Section 7 — Mesurer, Analyser, Apprendre

---

### Chapitre 38 : Attribution Causale du P&L

Savoir combien on a gagné ou perdu ne suffit pas. La question qui compte est : **pourquoi** ?

Le Module 6 décompose chaque dollar de profit ou de perte en **6 facteurs causaux** :

**1. Scanner (sélection)** — la qualité de la sélection d'actifs par le Module 1. Mesurée par la corrélation entre le score scanner et le P&L du trade. Si les actifs avec un score élevé produisent systématiquement de meilleurs résultats, le Scanner contribue positivement.

**2. Timing (entrée)** — la qualité du point d'entrée. Comparaison entre le prix d'entrée effectif et le meilleur prix possible pendant la journée d'entrée. Un bon timing signifie acheter proche du plus bas de la journée (en LONG).

**3. Sizing (taille)** — l'adéquation de la taille de position. Si le Kelly suggérait 8% et qu'on a mis 5%, on a sous-performé sur les trades gagnants. Si on a mis 12%, on a sur-risqué sur les trades perdants.

**4. Sortie** — la qualité du point de sortie. Le SL a-t-il été touché trop tôt ? Le TP était-il trop ambitieux ? Le trailing stop a-t-il capturé le maximum du mouvement ?

**5. Régime** — l'effet du contexte de marché. En bull market, même des trades médiocres peuvent être profitables (le marché porte tout). Le facteur régime isole la contribution du contexte.

**6. Friction** — les coûts de transaction : commissions, spread, slippage. C'est toujours négatif. Le système minimise la friction en utilisant des ordres limit quand le contexte le permet et en évitant l'over-trading.

**L'utilisation pratique :**

Si l'attribution montre que le Scanner est le facteur dominant positif (+40% du P&L total), les poids du scanner méritent d'être augmentés. Si le Timing est négatif (−15%), le système d'entrée doit être amélioré — peut-être utiliser plus d'ordres limit au lieu de market orders.

---

### Chapitre 39 : Métriques Professionnelles

Au-delà du P&L brut, le système calcule les métriques utilisées par les gestionnaires de fonds professionnels :

**Sharpe Ratio** — le rendement excédentaire (au-dessus du taux sans risque) divisé par la volatilité des rendements :

```
Sharpe = (Rendement moyen − Taux sans risque) / Écart-type des rendements × √252
```

Un Sharpe > 1.0 est bon, > 2.0 est excellent, > 3.0 est exceptionnel (et suspect — vérifier s'il n'y a pas de biais de survivant).

**Sortino Ratio** — comme le Sharpe, mais ne pénalise que la volatilité *baissière*. Un fonds qui monte de 5% un jour et baisse de 1% le suivant a un Sharpe moyen mais un Sortino excellent — seule la baisse est un "problème". Le Sortino est plus pertinent que le Sharpe car les traders cherchent à maximiser les gains *et* à minimiser les pertes, pas à réduire toute volatilité.

**Calmar Ratio** — le rendement annualisé divisé par le drawdown maximum. Mesure l'efficacité du capital par unité de risque extrême. Un Calmar de 2.0 signifie que pour chaque 1% de drawdown maximum, le système génère 2% de rendement annuel.

**Profit Factor** — la somme des gains bruts divisée par la somme des pertes brutes (en valeur absolue). Un PF de 1.5 signifie que pour chaque dollar perdu, le système gagne 1.50$.

```
Profit Factor = Σ Gains / |Σ Pertes|
```

Un PF > 1.0 est profitable. Un PF > 2.0 est excellent. Un PF < 1.0 signifie que le système perd de l'argent.

**Win Rate** — le pourcentage de trades gagnants. Un win rate de 55% avec un R:R de 1.5 est très bon. Un win rate de 80% avec un R:R de 0.3 est trompeur — les gains sont mangés par les quelques grosses pertes.

Le win rate seul ne veut rien dire. C'est la combinaison Win Rate × R:R qui détermine la profitabilité. Le Kelly capture exactement cette interaction.

---

### Chapitre 40 : Le Meta-Score

Le Meta-Score est l'indicateur de santé global du système. Un nombre unique entre 0 et 100 qui répond à la question : **le système fonctionne-t-il correctement ?**

**Les composantes :**

| Composante | Poids | Mesure |
|------------|-------|--------|
| **EWS** | 30% | Niveau d'alerte du Early Warning System |
| **Régime portefeuille** | 25% | ALPHA (100), BETA (50), STRESS (10) |
| **Win Rate** | 25% | Taux de trades gagnants × 100 |
| **Sharpe** | 20% | Sharpe ratio normalisé (0 → 0, 1 → 50, 2 → 100) |

**L'interprétation :**

| Meta-Score | État | Action |
|------------|------|--------|
| 80-100 | **Excellent** | Système performant, maintenir ou augmenter l'exposition |
| 60-79 | **Bon** | Fonctionnement normal, optimisations mineures possibles |
| 40-59 | **Attention** | Performance dégradée, réduire l'exposition, analyser les causes |
| 20-39 | **Critique** | Système en difficulté, réduire fortement, revoir les stratégies |
| 0-19 | **Urgence** | Pause automatique du pipeline, intervention humaine requise |

Le Meta-Score pilote directement le **niveau d'engagement** du pipeline. Un Meta-Score de 85 permet des positions à taille normale et un seuil GO de 65. Un Meta-Score de 35 réduit automatiquement les positions de 50% et relève le seuil GO à 75 — seuls les signaux les plus forts sont exécutés.

Cette boucle de rétroaction crée un système auto-régulateur : quand les choses vont mal, le système se protège automatiquement en réduisant son exposition. Quand les choses vont bien, il capitalise sur ses forces.

---

### Chapitre 41 : Le Early Warning System

Le EWS est le système d'alerte précoce du Module 6. Il surveille **5 indicateurs** en permanence pour détecter les signes de dégradation *avant* qu'ils ne se transforment en pertes significatives.

**Les 5 indicateurs :**

**1. Drawdown** — la perte depuis le peak equity.
- Attention : −5%
- Alerte : −10%
- Critique : −20%

**2. Série de pertes (Losing Streak)** — le nombre de trades perdants consécutifs.
- Attention : 3 trades
- Alerte : 5 trades
- Critique : 8 trades

**3. Déclin du Win Rate** — la baisse du win rate par rapport à la moyenne historique.
- Attention : −10 points (de 55% à 45%)
- Alerte : −20 points
- Critique : −30 points

**4. Spike de Volatilité** — l'augmentation de la volatilité du portefeuille par rapport à sa moyenne.
- Attention : 1.5x la normale
- Alerte : 2.5x
- Critique : 4.0x

**5. Rupture de Corrélation** — les corrélations inter-actifs changent brutalement (augmentation soudaine, signe de risque systémique).
- Attention : changement de 0.3
- Alerte : changement de 0.5
- Critique : changement de 0.7

**Les 4 niveaux :**

| Niveau | Condition | Action automatique |
|--------|-----------|-------------------|
| **NORMAL** | Aucun indicateur en alerte | Pipeline normal |
| **ATTENTION** | 1-2 indicateurs en attention | Log + notification |
| **ALERTE** | 1+ indicateur en alerte | Sizing réduit de 30% |
| **CRITIQUE** | 1+ indicateur en critique | **Pause automatique du pipeline** |

Le passage en CRITIQUE déclenche une pause automatique : plus aucun nouveau trade n'est ouvert jusqu'à ce que les indicateurs redescendent en zone ALERTE ou NORMAL. Les positions existantes sont maintenues (avec trailing stops) mais aucune nouvelle exposition n'est ajoutée.

C'est le mécanisme de survie du système. Quand tout va mal, la meilleure chose à faire est souvent... rien.

---

### Chapitre 42 : Le Taux de Détection

Le taux de détection mesure l'efficacité du scanner : combien des **top movers** de la journée (les actifs qui ont le plus bougé) étaient dans la shortlist du scanner ?

**La méthodologie :**

1. Chaque soir, le système identifie les 20 actifs qui ont le plus monté (> +2% sur la journée).
2. Pour chacun, il vérifie s'il était en signal GO dans le cache des signaux.
3. Le taux de détection = nombre de top movers détectés / nombre total de top movers.

**L'interprétation :**

| Taux | Qualité | Action |
|------|---------|--------|
| > 50% | Excellent | Le scanner capture la majorité des mouvements |
| 30-50% | Bon | Performance correcte |
| 20-30% | Moyen | Les poids du scoring doivent être ajustés |
| < 20% | Mauvais | Revoir les critères du scanner |

**L'optimisation automatique :**

Le Scoring Calibrator utilise le taux de détection pour ajuster les poids du Score V2. Si le taux est bas (< 30%), les poids évoluent : la conviction et le scanner gagnent en importance (ce sont les composantes qui détectent les mouvements de prix), le bayésien perd du poids (il est trop conservateur, trop ancré dans l'historique).

Les ajustements sont progressifs et bornés — jamais plus de ±5% par jour, les poids restent dans des bornes raisonnables. L'historique des ajustements est conservé sur 90 jours pour détecter les tendances.

---

### Chapitre 43 : Benchmarking

Un système de trading qui gagne 15% par an semble excellent — jusqu'à ce qu'on découvre que le S&P 500 a gagné 25% sur la même période. Sans benchmark, il est impossible de savoir si la performance provient de la compétence (alpha) ou du marché (beta).

**Les benchmarks :**

**1. Buy & Hold SPY** — le benchmark le plus simple. Investir la totalité du capital dans le SPY le jour 1 et ne rien faire. C'est le "coût d'opportunité" de base : si le système ne bat pas le buy & hold, il ne justifie pas sa complexité.

**2. Portefeuille 60/40** — 60% actions (SPY) + 40% obligations (TLT), rééquilibré trimestriellement. C'est le benchmark institutionnel classique, optimisé pour le risque/rendement à long terme.

**3. Momentum Simple** — acheter les 10 actifs qui ont le plus monté sur les 12 derniers mois, rééquilibrer mensuellement. C'est une stratégie systématique simple qui a historiquement surperformé le buy & hold.

**Les métriques comparatives :**

Pour chaque benchmark, le système calcule :
- La performance relative (rendement du système − rendement du benchmark)
- Le Sharpe relatif
- Le drawdown maximum comparé
- Le nombre de jours où le système surperforme vs sous-performe

La comparaison n'est significative qu'avec un historique suffisant (minimum 3 mois de trades). Avant cela, les benchmarks sont marqués "N/A — données insuffisantes".

---

# PARTIE VIII — LA BOUCLE DE FEEDBACK

---

## Section 8 — Le Système Qui Apprend

---

### Chapitre 44 : La Boucle Module 6 → Module 1

Le feedback loop est ce qui transforme Bilok-TradePilot d'un système statique en un système **adaptatif**. Chaque trade fermé produit des données qui remontent à travers le pipeline pour améliorer les décisions futures.

Le chemin du feedback :

```
Module 6 (Performance)
    ↓ Meta-Score, attribution P&L, EWS
Module 1 (Scanner)
    ↓ Poids ajustés, seuils recalibrés
Module 2 (Analyseur)
    ↓ Stratégies en quarantaine, boost régime ajusté
Module 3 (Scoring)
    ↓ Poids V2 recalibrés
Module 4 (Exécution)
    ↓ Seuils de santé ajustés, biais détectés
```

**Les signaux de feedback :**

**1. Meta-Score → Niveau d'engagement** — un Meta-Score bas (< 40) réduit automatiquement le sizing et augmente les seuils de conviction. Le pipeline devient plus sélectif quand il ne performe pas bien.

**2. Attribution → Poids du scanner** — si l'attribution P&L montre que le scanner est le principal contributeur positif, ses critères sont valorisés. Si le timing est le principal détracteur, le système privilégie les ordres limit aux ordres market.

**3. EWS → Pause pipeline** — un indicateur EWS en CRITIQUE stoppe les nouvelles entrées. Le pipeline ne reprend que quand les conditions se normalisent.

**4. Détection rate → Calibration V2** — le taux de détection des top movers recalibre les poids du Score V2 pour mieux capturer les grands mouvements.

**Le cycle temporel :**

| Fréquence | Action de feedback |
|-----------|-------------------|
| **Toutes les 5 min** | TP/SL monitor, trailing stop, exhaustion check |
| **Quotidienne** | Calibration scoring, taux de détection, equity tracking |
| **Hebdomadaire** | Strategy Decay check, matrice performance live, poids scanner |
| **Mensuelle** | Monte Carlo (10 000 simulations), benchmarking complet |

---

### Chapitre 45 : Le Scoring Calibrator

Le Scoring Calibrator est le mécanisme d'auto-apprentissage le plus direct du système. Il ajuste les poids du Score V2 en se basant sur une métrique simple : le taux de capture des top movers.

**Le principe :**

Chaque jour, le système pose la question : "Parmi les 20 actifs qui ont le plus monté aujourd'hui (> +2%), combien étaient en signal GO ?"

Si la réponse est "15/20" (75%), les poids actuels sont excellents — ne rien changer. Si la réponse est "3/20" (15%), les poids doivent être ajustés pour mieux capturer les mouvements.

**L'algorithme d'ajustement :**

| Taux moyen (14j) | Ajustement | Step |
|-------------------|-----------|------|
| ≥ 50% | Aucun | 0 |
| 30-50% | Léger | ±2% |
| 20-30% | Modéré | ±3% |
| < 20% | Fort | ±5% |

La direction de l'ajustement : **réduire** le poids du bayésien (trop conservateur, ancré dans le passé), **augmenter** le poids de la conviction (0.6 du step) et du scanner (0.4 du step). Les poids sont ensuite renormalisés pour totaliser 100%.

**Les bornes de sécurité :**

- Bayésien : minimum 15% (ne jamais ignorer l'historique)
- Conviction : maximum 45% (ne pas tout mettre sur une seule source)
- Scanner : maximum 30% (le scanner seul ne suffit pas)
- SQC : stable (le contexte de qualité ne change pas avec le calibrage)

L'historique de calibration est conservé sur 90 jours, avec les poids utilisés chaque jour et le taux de détection correspondant. Cela permet de voir l'évolution et de détecter si les ajustements améliorent effectivement la détection.

---

### Chapitre 46 : L'Entry Quality Tracker

L'Entry Quality Tracker apprend quels signaux de santé pré-trade prédisent le mieux la réussite d'un trade. C'est un apprentissage empirique : on observe, on mesure, on ajuste.

**Le processus :**

1. **À l'entrée** — quand un trade est ouvert, le système enregistre le score de santé (Exhaustion Checker) et l'état de chaque composante (Momentum FORT, Volume MODÉRÉ, RSI FAIBLE, etc.).

2. **À la sortie** — quand le trade est fermé, le P&L est associé aux données d'entrée. Le trade est classé comme gagnant ou perdant.

3. **L'analyse** — avec un minimum de 5 trades fermés, le système calcule :
   - Le **win rate par tranche de santé** : les trades entrés avec une santé de 70+ gagnent-ils plus souvent que ceux entrés avec une santé de 40 ?
   - L'**accuracy par composante** : quand le Momentum était FORT à l'entrée, le trade a-t-il gagné ? Quand le Volume était FAIBLE, a-t-il perdu ?
   - Les **combinaisons dangereuses** : RSI FAIBLE + Volume FAIBLE ensemble prédisent-ils systématiquement un échec ?

**Le seuil optimal :**

Le système teste différents seuils de santé minimum (de 35 à 60, par pas de 5) et calcule pour chacun le win rate des trades qui auraient été acceptés. Le seuil qui maximise le score = win_rate × min(trades, 20) / 20 est sélectionné. Ce score équilibre entre un bon win rate et un nombre suffisant de trades (un seuil à 95 donnerait un win rate de 100% mais zéro trade).

Le seuil optimal est utilisé par le TP/SL Monitor et la queue d'attente : tout signal dont la santé pré-trade est inférieure au seuil appris est rejeté.

**Le pouvoir prédictif :**

Pour chaque composante de santé, le système calcule le **pouvoir prédictif** = win rate FORT − win rate FAIBLE. Si le Momentum FORT a un win rate de 65% et le Momentum FAIBLE un win rate de 30%, le pouvoir prédictif est de +35 points. Les composantes avec un fort pouvoir prédictif devraient peser plus dans le score de santé.

---

### Chapitre 47 : La Détection du Strategy Decay

Les marchés changent. Les régulations évoluent. Les algorithmes des autres participants s'adaptent. Une stratégie qui fonctionnait il y a un an peut avoir perdu son edge aujourd'hui — c'est le **strategy decay**.

Le système surveille 4 métriques pour chaque stratégie :

| Métrique | Seuil de quarantaine | Pourquoi |
|----------|---------------------|----------|
| **Win Rate** | < 35% | Perd plus de 2 trades sur 3 |
| **Profit Factor** | < 0.8 | Les pertes dépassent les gains de 25% |
| **Sharpe Live** | Divergence significative vs backtest | Le live ne confirme pas le backtest |
| **Consistance** | Écart-type > 0.15 | Résultats trop erratiques |

Quand 2 ou plus de ces critères sont en échec, la stratégie est mise en **QUARANTINE**. Elle est retirée de la sélection du Module 2, et la stratégie suivante dans le classement prend sa place.

Le score de santé d'une stratégie :

```
Santé = 100 − 30 × (WR < seuil) − 30 × (PF < seuil) − 20 × (Consistance > seuil) − 20 × (Sharpe diverge)
```

Santé < 40 → QUARANTINE. Santé > 60 → ACTIVE. Entre 40 et 60 → SURVEILLANCE.

**Le Adaptive Engine** va plus loin en enregistrant chaque trade fermé avec sa stratégie et en calculant un Sharpe live par combinaison stratégie × actif. Après 5 trades, le Sharpe live remplace progressivement le Sharpe de backtest dans la sélection. Après 20 trades, le Sharpe live a priorité totale.

Cela crée un système qui commence par faire confiance au backtest, puis apprend de l'expérience réelle, puis ajuste ses choix en conséquence. Les stratégies qui fonctionnent sont amplifiées. Celles qui échouent sont écartées. Automatiquement, sans intervention humaine.

---

# PARTIE IX — L'INFRASTRUCTURE

---

## Section 9 — La Machine Derrière le Système

---

### Chapitre 48 : La Stack Technique

Bilok-TradePilot est construit sur une stack technique choisie pour la performance, la fiabilité et la maintenabilité.

**Backend — Python FastAPI :**

FastAPI est le framework web le plus rapide de l'écosystème Python (performance comparable à Go et Node.js). Il supporte nativement les WebSockets pour le streaming temps réel, la validation des données via Pydantic, et la génération automatique de documentation OpenAPI. Le backend expose les API REST pour le dashboard et les WebSockets pour les notifications en temps réel.

**Base de données — PostgreSQL :**

PostgreSQL stocke les données structurées : actifs, OHLCV quotidien, positions, ordres, signaux. SQLAlchemy 2.0 avec Alembic pour les migrations de schéma. Les requêtes les plus fréquentes (derniers prix, positions ouvertes) sont optimisées avec des index sur les colonnes `asset_id`, `date` et `status`.

**Pipeline — Celery + Redis :**

Celery orchestre les tâches asynchrones : scan nocturne, mise à jour des données, monitoring des positions. Redis sert de message broker et de stockage de résultats. Les tâches sont chaînées : `update_data → scan → analyse → scoring → execution`.

**Frontend — React + TailwindCSS + Recharts :**

Le dashboard React affiche en temps réel l'état du système : positions ouvertes, signaux actifs, métriques de performance, equity curve. TailwindCSS pour le style, Recharts pour les graphiques. Le frontend est déployé sur Vercel.

**Machine Learning — PyTorch (MPS) + FinBERT :**

Le NLP de sentiment utilise FinBERT, un modèle BERT fine-tuné sur du texte financier. Le MacBook M3 utilise Metal Performance Shaders (MPS) comme accélérateur GPU pour l'inférence. La RAM unifiée CPU/GPU du M3 élimine les transferts de données qui ralentiraient un GPU discret.

**Données marché — Yahoo Finance + Alpaca :**

Yahoo Finance (via yfinance) pour les données historiques quotidiennes (gratuit, 335 actifs). Alpaca pour les prix temps réel pendant les heures de marché. Alpha Vantage et Polygon.io pour les données supplémentaires (fondamentaux, intraday).

---

### Chapitre 49 : Le Pipeline Celery

Le pipeline Celery est le coeur automatisé du système. Il s'exécute chaque nuit à 22h UTC et enchaîne les 6 modules dans l'ordre.

**Les tâches planifiées :**

| Tâche | Horaire (UTC) | Durée | Description |
|-------|---------------|-------|-------------|
| `update_market_data` | 21h30 | ~15 min | Télécharger les OHLCV du jour pour les 335 actifs |
| `daily_pipeline` | 22h00 | ~45 min | Scan + Analyse + Scoring + Exécution |
| `intraday_scan` | 13h45, 15h45 | ~10 min | Scan rapide pendant les heures de marché |
| `tp_sl_monitor` | Toutes les 5 min | ~2 min | Vérifier SL/TP + trailing stop + essoufflement |
| `weekly_genome` | Dimanche 3h | ~30 min | Recalcul du génome explosif |
| `nightly_monte_carlo` | 2h00 | ~5 min | Simulation Monte Carlo (10 000 trajectoires) |

**La chaîne du pipeline quotidien :**

```python
chain(
    task_update_market_data.s(),      # 1. Données fraîches
    task_scan_all.s(),                 # 2. Scanner 335 actifs
    task_analyse_shortlist.s(),        # 3. Analyser la shortlist
    task_score_and_execute.s(),        # 4. Scoring + exécution
    task_portfolio_check.s(),          # 5. Vérification portefeuille
    task_performance_report.s(),       # 6. Rapport + feedback
)
```

Chaque tâche reçoit en entrée le résultat de la tâche précédente. Si une tâche échoue, elle est retentée automatiquement (3 retries max). Si elle échoue définitivement, le pipeline s'arrête proprement et une notification d'erreur est envoyée.

**Le monitoring :**

Les workers Celery sont configurés selon le nombre de coeurs du processeur :
- M3 standard (8 coeurs) → 4 workers
- M3 Pro (12 coeurs) → 6 workers
- M3 Max (16 coeurs) → 8 workers

Le nombre de workers ne doit pas dépasser 50% des coeurs pour laisser de la puissance au système d'exploitation et aux autres services (PostgreSQL, Redis).

---

### Chapitre 50 : Intégration Multi-Broker

L'intégration de deux brokers (Alpaca et IBKR) dans un même pipeline crée des défis techniques significatifs.

**La synchronisation :**

Chaque position existe potentiellement chez 3 entités : la base de données du système, Alpaca et IBKR. Ces 3 sources doivent rester synchronisées. En cas de divergence (une position est fermée chez Alpaca mais encore ouverte en BDD), le TP/SL Monitor détecte l'incohérence et corrige.

**La gestion des erreurs :**

Les connexions aux brokers sont fragiles. IBKR se déconnecte après 24h d'inactivité. Alpaca a des limites de rate (200 requêtes par minute). Le système implémente :

- **Retry avec backoff** — si une requête échoue, elle est retentée après 1s, puis 2s, puis 4s. Maximum 3 retries.
- **Fallback** — si IBKR est injoignable, Alpaca prend le relais pour le monitoring. Si Alpaca est injoignable, le système utilise les prix de la BDD (dernière clôture).
- **Timeout** — chaque connexion IBKR a un timeout de 15s pour l'ouverture et 90s pour le monitoring. Dépasser ces limites déclenche une déconnexion propre et un retry.
- **Validation croisée des prix** — si le prix reçu d'un broker dévie de plus de 50% par rapport au prix d'entrée, le système suspecte une erreur (post-split, bug d'API) et utilise le prix BDD comme arbitre.

**Le sizing centralisé :**

Le module `sizing.py` est le point unique de calcul de la taille de position. Tous les modules (router, TP/SL monitor, position manager) appellent `compute_position_size()` au lieu de recalculer localement. Cela garantit la cohérence : si on change la règle de sizing, elle s'applique partout.

Les paramètres centralisés :
- Base : 5% du capital par position
- Maximum : 15% du capital par position
- Le score ajoute 0-10% (score 50 → 5%, score 80+ → 15%)
- Le modifier V2 (corrélation, catalyseur, régime) ajuste le résultat

---

### Chapitre 51 : Déploiement

Le système est conçu pour fonctionner 24/7 sur un MacBook M3, avec un accès distant via Cloudflare Tunnel et un frontend déployé sur Vercel.

**La stack de déploiement :**

```
Internet ←→ Cloudflare Tunnel ←→ Mac local (FastAPI :8001)
                                         ↓
                                    PostgreSQL
                                    Redis
                                    Celery workers
                                    IB Gateway (port 7497)

Vercel ←→ Frontend React (tradepilot.bilok.io)
```

**Cloudflare Tunnel** crée un tunnel sécurisé entre le Mac et Internet, sans ouvrir de port sur le routeur. L'API backend est accessible via un sous-domaine (api.tradepilot.bilok.io) avec HTTPS automatique et protection DDoS de Cloudflare.

**Vercel** héberge le frontend React avec déploiement automatique à chaque push sur la branche main. Le frontend appelle l'API backend via le tunnel Cloudflare.

**Le keep_alive :**

Le script `scripts/keep_alive.sh` empêche le Mac de se mettre en veille (`caffeinate -s`) et vérifie régulièrement que tous les services sont en cours d'exécution :

1. PostgreSQL en cours d'exécution ?
2. Redis en cours d'exécution ?
3. FastAPI répond-il sur le port 8001 ?
4. Les workers Celery sont-ils actifs ?
5. IB Gateway est-il connecté ?

Si un service est tombé, le script le redémarre automatiquement.

---

### Chapitre 52 : Robustesse

Un système de trading automatisé qui plante est un système qui perd de l'argent. La robustesse est un impératif, pas un luxe.

**Les NaN Guards :**

Les données financières sont truffées de valeurs manquantes. Un actif sans volume un jour férié, un prix à zéro après un split non ajusté, un indicateur technique qui retourne NaN parce que la série est trop courte. Chaque calcul inclut des guards `np.isnan()` et des valeurs par défaut :

```python
if np.isnan(atr_val) or atr_val == 0:
    return {"direction": "NEUTRAL", "conviction": 0}
```

Un NaN qui se propage dans un calcul de position peut causer un ordre absurde (acheter -3 actions, SL à 0$). Les guards empêchent cela.

**Le logging structuré :**

Chaque action significative est loggée avec un préfixe identifiant le module :

```
[SCANNER] AAPL — Score 72.3/100, shortlist
[ANALYSER] AAPL — Régime BULL (65%), stratégie momentum
[SCORING] AAPL — Score V2 68.2, GO
[EXECUTION] AAPL — Bracket order Alpaca, 14 actions @ $172.50
[TRAILING] AAPL — SL: $165.30 → $168.40 (protège 3.5%)
[TP/SL] AAPL — TP atteint ($180.20 >= $179.50), P/L +$107.80
```

Ce logging permet le debugging en production (pourquoi un trade a-t-il été pris ? Pourquoi a-t-il été fermé ?) et l'analyse post-hoc (quel module a le mieux performé ?).

**Les frais dans le backtester :**

Un backtest qui ignore les frais de transaction est un mensonge. Le système inclut systématiquement les commissions (0.1% par trade), le slippage estimé (0.05%), et le spread (variable selon la liquidité). Un backtest avec un Sharpe de 2.0 avant frais peut tomber à 1.2 après frais — et c'est le 1.2 qui compte.

**Le sizing centralisé :**

Comme mentionné au chapitre 50, un seul module calcule le sizing. Cela élimine le risque de modules qui calculeraient des tailles différentes et se contrediraient. Le point unique de vérité est `compute_position_size()`.

---

# PARTIE X — LA PRATIQUE

---

## Section 10 — Vivre avec le Système

---

### Chapitre 53 : Une Journée Type

À quoi ressemble une journée avec Bilok-TradePilot ?

**21h30 UTC — Mise à jour des données.** Le pipeline télécharge les OHLCV du jour pour les 335 actifs. Yahoo Finance est interrogé actif par actif avec un délai de 0.3s entre chaque requête pour éviter le rate limiting. ~15 minutes pour tout mettre à jour.

**22h00 UTC — Le pipeline nocturne.** Le scan complet démarre. Les 335 actifs passent à travers les 10 critères du scanner. Chaque actif prend 2-3 secondes à analyser. La shortlist de 10-30 candidats est transmise à l'analyseur. Les régimes sont détectés, les stratégies sélectionnées, les thèses de trade générées. Les signaux GO sont envoyés aux brokers.

**22h45 UTC — Résultats.** Le dashboard affiche les nouvelles positions ouvertes, les signaux en attente, les positions existantes avec leur état de santé. Un email de résumé est envoyé si des trades significatifs ont été passés.

**Pendant la nuit (US overnight, Asie open) — Monitoring passif.** Le TP/SL monitor vérifie les positions toutes les 5 minutes. Les trailing stops sont ajustés si nécessaire. Pas d'intervention humaine.

**9h30 EST (15h30 Paris) — Ouverture du marché US.** Le volume explose. C'est le moment le plus dangereux et le plus opportun. Le système est en alerte maximale. Les bracket orders sont en place. Les stops sont actifs côté serveur (Alpaca).

**13h45 UTC (15h45 Paris) — Scan intraday.** Un scan rapide détecte les actifs qui ont bougé significativement depuis le scan nocturne. Les signaux intraday sont moins fiables que les signaux nocturnes (moins de données) mais permettent de capturer les mouvements de la journée.

**20h00 UTC — Fin de journée US.** Le marché ferme. L'Equity Tracker enregistre l'equity du jour. Le Scoring Calibrator mesure le taux de détection. Le cycle se termine.

**Le rôle de l'humain :**

Le trader n'a pas besoin d'intervenir dans les opérations quotidiennes. Son rôle est stratégique :

1. **Le matin** — consulter le dashboard, vérifier les positions ouvertes, lire les alertes du Reversal Guard.
2. **Hebdomadaire** — analyser le rapport de performance, créer ou ajuster les thèses de trading.
3. **Mensuel** — revoir les résultats Monte Carlo, comparer aux benchmarks, décider si le système mérite plus ou moins de capital.

---

### Chapitre 54 : Lire le Dashboard

Le dashboard est l'interface entre le trader et le système. Il est organisé en pages thématiques.

**La page Portfolio** — vue d'ensemble des positions ouvertes avec le P&L en temps réel (Alpaca) et le P&L de la base de données. Les positions sont colorées : vert pour les positions en profit, rouge pour les positions en perte. Le niveau du Reversal Guard est affiché (VERT/JAUNE/ORANGE/ROUGE).

**La page Dashboard** — les métriques clés du jour : nombre d'actifs scannés, shortlist du jour, signaux GO générés, Meta-Score, EWS, positions ouvertes vs maximum, equity courante.

**La page Analyse** — permet de lancer une analyse rapide sur un actif spécifique. Le trader entre un symbole et le système retourne en quelques secondes le score scanner, le régime, la stratégie recommandée, et la thèse de trade. Pratique pour vérifier rapidement une idée.

**La page Performance** — les métriques professionnelles (Sharpe, Sortino, Calmar, Profit Factor), la courbe d'equity, l'attribution P&L, le statut du calibrage, et les benchmarks.

**La page Corrélation** — la matrice de corrélation du portefeuille, les niveaux de corrélation entre chaque paire de positions ouvertes, et la détection de concentration.

**La page Exécution** — l'état des ordres envoyés, le statut des bracket orders, la file d'attente des signaux en attente, les biais détectés.

**La page Thèses** — les thèses de trading manuelles actives, leur horizon restant, et leur influence sur le scoring.

---

### Chapitre 55 : Prendre une Décision

Quand le système affiche un signal GO, que doit faire le trader ?

**En mode full auto** — rien. Le signal est envoyé directement aux brokers, les bracket orders sont en place, le TP/SL monitor surveille. Le trader n'a aucune action à prendre.

**En mode semi-auto** — le trader reçoit la thèse de trade et décide d'approuver ou non. Il peut :
- Approuver tel quel (le système exécute)
- Modifier le sizing (réduire ou augmenter la position)
- Modifier le SL/TP (s'il a une conviction forte sur un niveau technique)
- Rejeter (s'il a une information que le système n'a pas)

**La règle d'or du semi-auto :**

Le trader peut **réduire** le risque (plus petit sizing, SL plus serré) mais ne devrait jamais **augmenter** le risque (plus gros sizing, SL plus large). Le système a calculé le risque optimal ; l'ajuster à la hausse est presque toujours un biais émotionnel déguisé en conviction.

**Les cas de rejet légitime :**
- Une information non publique (insider trading exclu, évidemment — mais une connaissance sectorielle que le système ne capte pas)
- Un événement imminent non capté par le système (annonce réglementaire, géopolitique)
- Un bug évident dans les données (prix aberrant, volume à zéro)

---

### Chapitre 56 : Gérer les Pertes

Les pertes sont inévitables. Même le meilleur système au monde a un win rate inférieur à 100%. La question n'est pas "vais-je perdre ?" mais "comment vais-je gérer la perte quand elle arrivera ?"

**Les pertes individuelles :**

Un trade qui touche son SL est un trade réussi — il a fait exactement ce qu'il devait faire. Le SL a limité la perte à un montant prédéfini (2 × ATR). Sans SL, cette perte pourrait être 5x ou 10x plus grande.

Ne jamais :
- Déplacer le SL vers le bas pour "donner plus de marge" au trade
- Moyenner à la baisse (ajouter à une position perdante)
- Espérer un retournement après le SL touché
- Prendre un trade de revenge dans les 30 minutes suivantes

**Les séries de pertes :**

3 pertes consécutives → normal. Ça arrive statistiquement ~10% du temps avec un win rate de 55%.
5 pertes consécutives → attention. Le EWS passe en ALERTE. Réduire le sizing.
8 pertes consécutives → critique. Pause du pipeline. Analyser ce qui ne va pas.

**Les drawdowns :**

Un drawdown de −10% est psychologiquement douloureux mais statistiquement normal pour un système de swing trading. Un drawdown de −20% nécessite une analyse approfondie et probablement une réduction significative de l'exposition.

Le temps de recovery est aussi important que la magnitude. Un drawdown de −10% nécessite un gain de +11.1% pour revenir au peak. Un drawdown de −25% nécessite +33.3%. Plus le drawdown est profond, plus il est difficile et long de s'en remettre.

---

### Chapitre 57 : Les Limites du Modèle

Bilok-TradePilot est un système sophistiqué, mais il a des limites fondamentales qu'il est essentiel de comprendre.

**1. Les événements imprévisibles** — aucun modèle ne peut anticiper un tweet présidentiel, une guerre, une pandémie, ou un hack d'exchange crypto. Ces "cygnes noirs" peuvent causer des pertes instantanées que les stops ne peuvent pas limiter (gaps d'ouverture).

**2. Le biais de backtest** — les performances passées ne garantissent pas les performances futures. Un backtest sur 10 ans montre ce qui *aurait* marché, pas ce qui *va* marcher. Le walk-forward et le Strategy Decay tentent de mitiger ce risque, mais ne l'éliminent pas.

**3. Les changements de régime** — le système est optimisé pour le swing trading en marchés développés. Un changement structurel du marché (hyperinflation, contrôle des capitaux, interdiction du trading algorithmique) pourrait rendre le système obsolète.

**4. Les coûts cachés** — le spread réel peut être plus large que le spread estimé en backtest. Le slippage augmente en période de volatilité. Les commissions varient. Ces coûts mangent la performance — et sont systématiquement sous-estimés.

**5. La dépendance technologique** — le système repose sur des services tiers (Alpaca, IBKR, Yahoo Finance, Cloudflare). La panne de l'un de ces services peut bloquer le pipeline. Les fallbacks existent mais ne sont pas parfaits.

**6. La taille du compte** — avec un petit compte ($300-1000), le sizing Kelly produit des positions minuscules (1-3 actions). Les frais de transaction en pourcentage sont disproportionnés. Le système est plus efficace avec un capital de $10,000+.

---

### Chapitre 58 : La Roadmap

Le développement de Bilok-TradePilot suit un plan progressif en 3 phases.

**Phase 1 — Paper Trading (en cours)**

L'objectif est de valider le pipeline complet sans risquer de capital réel. Les positions sont passées en paper trading chez Alpaca et en très petites positions réelles chez IBKR. Les métriques sont collectées pendant 3-6 mois pour établir une baseline statistiquement significative.

Critères de passage en Phase 2 :
- Win rate > 50% sur 100+ trades
- Sharpe > 1.0 sur 3+ mois
- Drawdown maximum < 15%
- Meta-Score moyen > 60
- Taux de détection moyen > 40%

**Phase 2 — Live Trading**

Si les critères de Phase 1 sont remplis, le capital alloué au trading réel augmente progressivement. L'allocation commence à 10% du capital total et augmente de 10% chaque mois si les performances restent dans les normes.

Ajouts prévus :
- Sources de données premium (Polygon.io, Unusual Whales)
- Module de microstructure (carnet d'ordres)
- CNN Pattern Recognition (PyTorch + ResNet18)
- Tax Loss Harvesting

**Phase 3 — Scaling**

Si la Phase 2 confirme un edge durable :
- Marchés additionnels (options, futures)
- Stratégies intraday
- Déploiement cloud (latence réduite)
- Dashboards avancés (attribution temps réel, streaming WebSocket)

**La règle absolue :**

Ne jamais dépenser plus en infrastructure que ce que le système génère. Chaque upgrade doit être justifié par une amélioration mesurable de la performance.

---

### Chapitre 59 : La Règle d'Or

Si ce livre devait se résumer en une seule phrase, ce serait celle-ci :

> *Le système protège le trader de lui-même.*

Tous les modules, tous les filtres, tous les mécanismes de feedback convergent vers un seul objectif : éliminer les décisions émotionnelles et les remplacer par des décisions systématiques.

Le trader apporte la vision. Le système apporte la discipline. La vision sans discipline est de la spéculation. La discipline sans vision est de l'automatisation aveugle. Les deux ensemble forment un avantage durable.

Les règles d'or du trader systématique :

1. **Respecter le SL.** Toujours. Sans exception. C'est la protection du capital.
2. **Respecter le sizing.** Ne jamais augmenter la taille parce qu'on "sent" que ça va marcher.
3. **Accepter les pertes.** Elles font partie du système. Un win rate de 55% signifie 45 pertes sur 100 trades.
4. **Mesurer, pas ressentir.** Le Sharpe, le Profit Factor, le drawdown sont des faits. Les émotions sont des bruits.
5. **Laisser le temps au système.** 10 trades ne prouvent rien. 100 trades commencent à donner une image. 500 trades donnent une certitude statistique.
6. **Ne pas intervenir.** Si le système est en mode auto, le laisser faire. Chaque intervention humaine est un risque de biais émotionnel.
7. **Ne jamais arrêter de mesurer.** Le jour où on arrête de tracker les métriques est le jour où les mauvaises habitudes reviennent.

Le trading n'est pas un sprint. C'est un marathon. Et dans un marathon, celui qui gagne n'est pas le plus rapide — c'est celui qui ne s'arrête pas.

---

# ANNEXES

---

## Annexe A : Glossaire

| Terme | Définition |
|-------|-----------|
| **ATR** | Average True Range — mesure de la volatilité quotidienne moyenne |
| **Bracket Order** | Ordre composite : entrée + SL + TP en une seule commande serveur |
| **Drawdown** | Perte depuis le peak equity, exprimée en pourcentage |
| **EMA** | Exponential Moving Average — moyenne mobile qui pondère plus les données récentes |
| **EV** | Expected Value — valeur attendue d'un trade (win_rate × R:R − loss_rate) |
| **EWS** | Early Warning System — système d'alerte précoce à 5 indicateurs |
| **Kelly** | Critère de Kelly — formule qui détermine la fraction optimale du capital à risquer |
| **MTS** | Macro Tailwind Score — mesure du vent macro favorable ou contraire |
| **OHLCV** | Open, High, Low, Close, Volume — les 5 données de base d'une bougie |
| **PF** | Profit Factor — gains bruts / pertes brutes |
| **R:R** | Risk:Reward ratio — ratio entre le risque (SL) et la récompense (TP) |
| **RSI** | Relative Strength Index — oscillateur de momentum (0-100) |
| **Sharpe** | Sharpe Ratio — rendement excédentaire / volatilité (annualisé) |
| **SL** | Stop-Loss — ordre de vente automatique pour limiter les pertes |
| **SMA** | Simple Moving Average — moyenne mobile simple |
| **SQC** | Score de Qualité du Contexte — liquidité, heure, volatilité |
| **SUS** | Score d'Unicité du Signal — mesure de la rareté du signal |
| **TP** | Take-Profit — ordre de vente automatique pour sécuriser les gains |
| **Trailing Stop** | SL qui remonte avec le prix mais ne redescend jamais |
| **Win Rate** | Pourcentage de trades gagnants |

---

## Annexe B : Formules Clés

**Score Scanner Final :**
```
Score = Σ (Score_i × Poids_i) × Vetos
Veto si MTS < 20 OU SUS < 25 OU IPI < 20
```

**Score V2 :**
```
V2 = Conviction × 0.35 + Bayésien × 0.30 + SQC × 0.20 + Scanner × 0.15
GO si V2 ≥ 65 ET Kelly > 0
```

**Score Bayésien :**
```
Prior = Perf_6m × 0.40 + Consistance × 0.30 + Position_range × 0.30
Likelihood = Scanner × 0.40 + Conviction × 0.40 + Confiance_regime × 0.20
Posterior = Prior × (1 − w) + Likelihood × w
w = 0.4 + confiance_regime × 0.4
```

**Kelly Fractionnaire :**
```
f* = (p × b − q) / b
Fraction = f* × 0.25
Position = Capital × min(Fraction, 0.15)
```

**Exhaustion Score :**
```
Santé = (Momentum + Volume + Narrative + RSI + P/L) / 5
FORT ≥ 70 | MODÉRÉ ≥ 50 | FAIBLE ≥ 35 | ÉPUISÉ < 35
```

**Meta-Score :**
```
Meta = EWS × 0.30 + Régime_portf × 0.25 + Win_rate × 0.25 + Sharpe_norm × 0.20
```

---

## Annexe C : Univers d'Investissement

L'univers de Bilok-TradePilot couvre 335 actifs répartis en 5 classes :

| Classe | Nombre | Exemples |
|--------|--------|----------|
| **Actions US** | ~200 | AAPL, MSFT, NVDA, TSLA, META, AMZN, GOOGL |
| **Actions EU** | ~30 | MC.PA, SAP.DE, NESN.SW, AZN.L, BNP.PA |
| **ETF** | ~40 | SPY, QQQ, IWM, GLD, TLT, XLK, XLF |
| **Crypto** | ~20 | BTC-USD, ETH-USD, SOL-USD, ADA-USD |
| **Forex / Commodities** | ~45 | EURUSD=X, GC=F, CL=F, SI=F |

La sélection est réévaluée trimestriellement. Les actifs qui ne génèrent jamais de signal (score scanner < 30 pendant 90 jours) sont retirés. Les actifs qui émergent (IPO prometteuses, nouvelles cryptos majeures) sont ajoutés.

---

## Annexe D : Configuration des Seuils

Tous les seuils du système sont configurables. Voici les valeurs par défaut :

| Paramètre | Valeur | Module | Justification |
|-----------|--------|--------|---------------|
| Score GO minimum | 65 | Scoring | Équilibre entre sélectivité et volume de trades |
| Kelly fraction | 0.25 | Scoring | Conservateur (1/4 du Kelly optimal) |
| Max position | 15% capital | Sizing | Diversification minimale |
| Max positions | 20 | Execution | Gestion manageable |
| SL distance | 2 × ATR | Execution | Absorbe le bruit quotidien normal |
| TP distance | 3 × ATR | Execution | R:R minimum de 1.5 |
| Trailing SL | 2 × ATR | Execution | Protège les gains sans couper trop tôt |
| Essoufflement critique | < 35 | Execution | Fermer les positions mortes |
| Max corrélation | 0.85 | Portfolio | Éviter la concentration |
| Drawdown critique | −20% | Portfolio | Pause pipeline |
| EWS losing streak | 8 | Performance | Pause pipeline |
| Strategy decay trades min | 20 | Analyser | Évaluation statistiquement significative |
| Calibration window | 14 jours | Learning | Réactivité vs stabilité |

---

## Annexe E : Architecture Technique

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  React + TailwindCSS + Recharts (Vercel)                    │
│  Dashboard | Portfolio | Analyse | Performance | Exécution  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS (Cloudflare Tunnel)
┌──────────────────────────▼──────────────────────────────────┐
│                        BACKEND                               │
│  FastAPI (Python 3.11)                                       │
│  ├── /api/scanner/     → Module 1                           │
│  ├── /api/analyser/    → Module 2                           │
│  ├── /api/scoring/     → Module 3                           │
│  ├── /api/execution/   → Module 4                           │
│  ├── /api/portfolio/   → Module 5                           │
│  ├── /api/performance/ → Module 6                           │
│  └── /api/admin/       → Monitoring                         │
└──────┬──────────┬───────────┬──────────┬────────────────────┘
       │          │           │          │
  ┌────▼────┐ ┌──▼───┐ ┌────▼────┐ ┌──▼──────────┐
  │PostgreSQL│ │Redis │ │Celery   │ │Brokers      │
  │  Assets  │ │Broker│ │Workers  │ │├─ Alpaca    │
  │  OHLCV   │ │Queue │ │Pipeline │ │├─ IBKR     │
  │  Trades  │ │Cache │ │Monitor  │ │└─ (future) │
  └─────────┘ └──────┘ └─────────┘ └─────────────┘
```

---

## Annexe F : Ressources

**Livres recommandés :**
- *Trading Systems* — Emilio Tomasini & Urban Jaekle
- *Quantitative Trading* — Ernest Chan
- *Advances in Financial Machine Learning* — Marcos López de Prado
- *The Man Who Solved the Market* — Gregory Zuckerman
- *Thinking, Fast and Slow* — Daniel Kahneman

**APIs et services :**
- Yahoo Finance (yfinance) — données historiques gratuites
- Alpaca — broker API, paper trading
- Interactive Brokers — trading multi-marchés
- FRED (Federal Reserve) — données macro
- Reddit API — sentiment retail
- NewsAPI — flux d'actualités

**Technologies :**
- FastAPI — framework web Python
- SQLAlchemy — ORM Python
- Celery + Redis — orchestration de tâches
- React + TailwindCSS — frontend
- PyTorch (MPS) — machine learning sur Apple Silicon
- FinBERT — NLP financier

---

# CONCLUSION

Ce livre a décortiqué les 6 modules du pipeline Bilok-TradePilot — du premier scan d'un actif jusqu'à l'attribution causale de son P&L. Chaque chapitre a révélé un mécanisme, une formule, une logique.

Mais le système n'est pas la fin en soi. C'est un outil — un outil sophistiqué, certes, mais un outil quand même. Sa valeur dépend de la rigueur avec laquelle il est utilisé, de l'honnêteté avec laquelle ses résultats sont mesurés, et de la discipline avec laquelle ses règles sont suivies.

Les marchés ne récompensent ni l'intelligence, ni l'effort, ni la passion. Ils récompensent la discipline. Et la discipline, c'est précisément ce qu'un système automatisé fait le mieux.

Le parcours n'est pas terminé. Le système continue d'apprendre, de s'adapter, de s'améliorer. Chaque trade fermé est une donnée supplémentaire. Chaque erreur est une leçon. Chaque ajustement de poids rapproche le modèle de la réalité.

La seule chose que le système ne fera jamais, c'est garantir un profit. Les marchés sont fondamentalement incertains. Mais dans cette incertitude, un système qui mesure, qui apprend et qui se protège a un avantage sur celui qui espère, qui devine et qui panique.

C'est cet avantage — systématique, reproductible, quantifiable — qui justifie chaque ligne de code.

> *"In God we trust. All others must bring data."*
> — W. Edwards Deming

---

## MENTIONS LÉGALES

*Ce document est fourni à titre informatif et éducatif uniquement. Il ne constitue en aucun cas un conseil en investissement, une recommandation d'achat ou de vente, ni une incitation à effectuer une quelconque transaction financière. Les performances passées ne préjugent pas des performances futures. Tout investissement comporte des risques de perte en capital. L'auteur et Bilok-TradePilot déclinent toute responsabilité quant aux décisions prises sur la base de ce document. Consultez un conseiller financier agréé avant toute décision d'investissement.*

---

*© 2026 Alain Bilok — Tous droits réservés*
