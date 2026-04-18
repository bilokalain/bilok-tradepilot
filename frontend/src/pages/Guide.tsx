import { useState } from "react";
import { BookOpen, ChevronDown, ChevronRight, Zap, ScanSearch, Brain, Target, Briefcase, TrendingUp, Shield, BarChart3, Settings, HelpCircle } from "lucide-react";

const SECTIONS = [
  {
    id: "start",
    title: "Premiers pas",
    icon: <BookOpen size={18} />,
    content: (
      <>
        <H3>Connexion</H3>
        <P>Ouvrez <Code>http://localhost:5173</Code> (local) ou <Code>bilok-tradepilot.vercel.app</Code> (internet). Créez un compte ou utilisez le compte admin : <Code>admin@tradepilot.local</Code> / <Code>tradepilot2024</Code>.</P>
        <P>L'application est hébergée sur <B>Vercel</B> (frontend) avec le backend sur votre Mac exposé via Cloudflare Tunnel. Partageable avec n'importe qui via le lien Vercel.</P>

        <H3>Ce que vous voyez sur le Dashboard</H3>
        <Table headers={["Élément", "Signification"]}>
          <TR><TD b>Thèses M0</TD><TD>Nombre de convictions personnelles actives + conviction moyenne. Influence directement le scoring des actifs liés</TD></TR>
          <TR><TD b>Actifs scannés</TD><TD>500 actifs analysés (233 US, 76 EU, 53 crypto, 89 ETF, 30 forex, 19 commodities)</TD></TR>
          <TR><TD b>Score moyen</TD><TD>Moyenne des 10 critères sur les 500 actifs. Au-dessus de 60 = marché favorable</TD></TR>
          <TR><TD b>Signaux GO</TD><TD>Actifs qui remplissent les 8 conditions du Score V2. <B>C'est le chiffre le plus important</B></TD></TR>
          <TR><TD b>Régime</TD><TD>Régime global multi-assets : RISK-ON (favorable), RISK-OFF (prudence), STAGFLATION, GOLDILOCKS</TD></TR>
          <TR><TD b>Santé système</TD><TD>Meta-Score 0-100. Pilote l'engagement : FULL (&gt;80), NORMAL (60-80), PRUDENT (40-60), MINIMAL (&lt;40)</TD></TR>
        </Table>

        <H3>Section "Mes Convictions" (M0)</H3>
        <P>Si vous avez des thèses actives, elles s'affichent directement sur le Dashboard entre les signaux et le pipeline :</P>
        <Table headers={["Élément", "Détail"]}>
          <TR><TD b>Direction</TD><TD>Flèche dorée (hausse) ou rouge (baisse) pour chaque thèse</TD></TR>
          <TR><TD b>Conviction</TD><TD>Badge coloré : CERTAINE (doré vif), FORTE (doré), MOYENNE (jaune), FAIBLE (gris)</TD></TR>
          <TR><TD b>Horizon</TD><TD>Jours restants avant expiration de la thèse</TD></TR>
          <TR><TD b>Supprimer</TD><TD>Icône poubelle au survol — retire immédiatement une conviction qui ne tient plus</TD></TR>
        </Table>
        <Callout>Vous pouvez supprimer une thèse directement depuis le Dashboard quand elle n'est plus pertinente (ex: événement passé, marché a invalidé votre scénario). L'effet sur le scoring est immédiat.</Callout>

        <H3>Top Movers du jour</H3>
        <P>Le Dashboard affiche les <B>plus fortes variations</B> parmi les 500 actifs surveillés :</P>
        <Table headers={["Section", "Ce qu'elle montre"]}>
          <TR><TD b>Hausse</TD><TD>Top 10 des plus fortes hausses du jour — badge "EN POS" si vous êtes déjà en position</TD></TR>
          <TR><TD b>Baisse</TD><TD>Top 10 des plus fortes baisses — identifie les actifs à shorter ou éviter</TD></TR>
          <TR><TD b>Taux de détection</TD><TD>Barre de progression : combien de top movers du marché global sont dans nos 500 actifs. Vert &gt; 70%, jaune 50-70%, rouge &lt; 50%</TD></TR>
          <TR><TD b>Actifs manqués</TD><TD>Badges rouges des symboles qui performent mais ne sont pas dans le scanner</TD></TR>
        </Table>
        <Callout>Le taux de détection permet de savoir si notre sélection de 500 actifs couvre bien le marché. Si des actifs sont régulièrement manqués, ils peuvent être ajoutés au scanner.</Callout>

        <H3>Le pipeline complet</H3>
        <div className="bg-surface rounded-xl p-4 my-4 text-xs leading-relaxed">
          <div className="font-mono text-gold mb-3">
            M0 Thèses → M1 Scanner → M2 Analyseur → M3 Scoring V2 → M4 Exécution → M5 Portefeuille → M6 Performance → Feedback ↩ M0
          </div>
          <Table headers={["Module", "Ce qu'il fait"]}>
            <TR><TD b>M0 Mes Thèses</TD><TD>Vos convictions personnelles — boost les scores des actifs liés</TD></TR>
            <TR><TD b>M1 Scanner</TD><TD>500 actifs × 11 critères (dont Narrative Momentum) — note de 0 à 100</TD></TR>
            <TR><TD b>M2 Analyseur</TD><TD>Régime global + 14 stratégies + catalyseurs + sector rotation</TD></TR>
            <TR><TD b>M3 Scoring V2</TD><TD>4 composantes (Conviction 35% + Bayésien 30% + SQC 20% + Scanner 15%) — poids auto-calibrés</TD></TR>
            <TR><TD b>M4 Exécution</TD><TD>Multi-Broker IBKR (réel) + Alpaca (paper), SL/TP, trailing stop, sizing intelligent</TD></TR>
            <TR><TD b>M5 Portefeuille</TD><TD>VaR, Risk Budget, Drawdown Control, Reversal Guard, Equity Curve vs SPY</TD></TR>
            <TR><TD b>M6 Performance</TD><TD>Apprentissage autonome, Calibrage auto, Feedback loop, Rapport hebdo</TD></TR>
          </Table>
        </div>

        <H3>Les outils complémentaires</H3>
        <Table headers={["Outil", "Ce qu'il fait"]}>
          <TR><TD b>Analyse rapide</TD><TD>Autocomplete intelligent (TradingView) + double source Yahoo/TV + Score V2 cohérent pipeline</TD></TR>
          <TR><TD b>Corrélation</TD><TD>Trouvez tous les actifs liés à un thème + simulez l'impact d'un choc + backtest corrélation 25 ans</TD></TR>
          <TR><TD b>Backtesting</TD><TD>5 modules : stratégies, corrélation, walk-forward, thèse, analyse profonde</TD></TR>
        </Table>

        <H3>Le graphique</H3>
        <P>Le graphique professionnel inclut :</P>
        <Table headers={["Fonctionnalité", "Détail"]}>
          <TR><TD b>Périodes</TD><TD>1S, 1M, 3M, 6M, 1A, 2A, 5A, MAX (jusqu'à 64 ans)</TD></TR>
          <TR><TD b>Types</TD><TD>Chandeliers, Ligne, Zone</TD></TR>
          <TR><TD b>9 indicateurs</TD><TD>SMA 20/50/200, EMA 9/21, Bollinger, VWAP, Donchian, Volume</TD></TR>
          <TR><TD b>Plein écran</TD><TD>Bouton ⛶ pour agrandir, ESC pour quitter</TD></TR>
          <TR><TD b>TradingView</TD><TD>Bouton TV → 100+ indicateurs, outils de dessin, multi-timeframe</TD></TR>
          <TR><TD b>OHLCV au survol</TD><TD>Open, High, Low, Close, Volume en temps réel au passage de la souris</TD></TR>
        </Table>

        <H3>Données</H3>
        <Table headers={["Métrique", "Valeur"]}>
          <TR><TD b>Actifs</TD><TD>500 (233 US, 76 EU, 53 Crypto, 89 ETF, 30 Forex, 19 Commodities)</TD></TR>
          <TR><TD b>Historique</TD><TD>2.4M barres daily (jusqu'à 10 ans d'historique) + 412K barres 1H</TD></TR>
          <TR><TD b>Broker</TD><TD>Alpaca connecté (paper trading avec bracket orders)</TD></TR>
          <TR><TD b>IA</TD><TD>FinBERT (NLP 94%) + XGBoost (15K samples)</TD></TR>
          <TR><TD b>Notifications</TD><TD>Email + fichier log (scan, positions, rapport hebdo)</TD></TR>
        </Table>
      </>
    ),
  },
  {
    id: "scanner",
    title: "Module 1 — Scanner de Marché",
    icon: <ScanSearch size={18} />,
    content: (
      <>
        <P>Le scanner est le <B>filtre d'entrée</B>. Sur 500 actifs (US, EU, ETF, Crypto, Forex, Commodities, Biotech, Défense, Moonshots), il identifie ceux qui méritent votre attention. Chaque actif reçoit une note de 0 à 100 basée sur <B>11 dimensions indépendantes</B>.</P>
        <Callout>Les poids des 11 critères s'ajustent automatiquement avec le temps grâce au système d'apprentissage. Les critères qui prédisent bien les trades gagnants voient leur poids augmenter (+30% max).</Callout>

        <H3>Les 11 critères</H3>

        <CriterionCard emoji="📊" name="1. Analyse Technique (AT) — 20 indicateurs" description="Étudie les mouvements de prix avec 20 indicateurs répartis en 7 familles. C'est le critère le plus complet du scanner.">
          <Table headers={["Famille", "Indicateurs", "Ce qu'ils mesurent"]}>
            <TR><TD b>Tendance</TD><TD>SMA, EMA, ADX, Parabolic SAR, Donchian</TD><TD>Direction et force du mouvement</TD></TR>
            <TR><TD b>Momentum</TD><TD>RSI, MACD, Stochastic, Williams %R, CCI, ROC</TD><TD>Vitesse et accélération du prix</TD></TR>
            <TR><TD b>Volatilité</TD><TD>Bollinger Bands, ATR</TD><TD>Amplitude des mouvements</TD></TR>
            <TR><TD b>Volume</TD><TD>OBV, Chaikin Money Flow, VWAP</TD><TD>Confirmation par le volume + prix institutionnel</TD></TR>
            <TR><TD b>Structure</TD><TD>Pivot Points (PP, R1-R3, S1-S3)</TD><TD>Niveaux de support/résistance institutionnels</TD></TR>
            <TR><TD b>Divergences</TD><TD>RSI divergence, MACD divergence (auto)</TD><TD>Détecte les retournements avant qu'ils arrivent</TD></TR>
            <TR><TD b>Force</TD><TD>ADX</TD><TD>&gt; 25 = tendance forte, &lt; 20 = range (pas de tendance)</TD></TR>
          </Table>
          <ScoreGuide high="Forte dynamique haussière, 20 indicateurs alignés" low="Dynamique baissière, divergences détectées" />
        </CriterionCard>

        <CriterionCard emoji="🔗" name="2. Corrélation" description="Compare le comportement de l'actif avec les autres. Un actif qui se découple du groupe est intéressant.">
          <ScoreGuide high="L'actif a un comportement très indépendant — opportunité unique" low="Forte corrélation — suit le marché, difficile de trouver un avantage" />
        </CriterionCard>

        <CriterionCard emoji="💬" name="3. Sentiment" description="Analyse ce que les gens disent sur Reddit et les actualités. Utilise FinBERT (IA spécialisée en finance) qui comprend le langage financier avec 94% de précision.">
          <Table headers={["Source", "Méthode", "Statut"]}>
            <TR><TD b>Reddit</TD><TD>r/wallstreetbets, r/stocks, r/CryptoCurrency</TD><TD>Actif (simulé sans clé API)</TD></TR>
            <TR><TD b>FinBERT</TD><TD>IA NLP spécialisée finance (ProsusAI)</TD><TD>Actif sur votre Mac M3</TD></TR>
            <TR><TD b>Google Trends</TD><TD>Intérêt de recherche</TD><TD>Prêt (pytrends)</TD></TR>
          </Table>
          <ScoreGuide high="Sentiment très positif, beaucoup de buzz optimiste" low="Sentiment négatif — prudence ou opportunité contrariante" />
        </CriterionCard>

        <CriterionCard emoji="🧬" name="4. Génome Explosif" description="Analyse l'ADN comportemental pour détecter les configurations pré-explosives : compression de volatilité, volume en contraction, divergences.">
          <Table headers={["Composante", "Ce qu'elle cherche"]}>
            <TR><TD b>Phase de cycle</TD><TD>Accumulation = les gros investisseurs achètent discrètement</TD></TR>
            <TR><TD b>Sismographe</TD><TD>6 micro-signaux de compression (Bollinger squeeze, inside bars...)</TD></TR>
            <TR><TD b>Mémoire fractale</TD><TD>L'actif répète-t-il un pattern pré-explosion du passé ?</TD></TR>
          </Table>
          <ScoreGuide high="Configuration explosive ! Plusieurs micro-signaux actifs" low="Pas de configuration explosive" />
        </CriterionCard>

        <CriterionCard emoji="🏦" name="5. Capital Institutionnel (IPI)" description="Détecte si les fonds et banques achètent ou vendent discrètement.">
          <Table headers={["Signal", "Signification"]}>
            <TR><TD b>A/D Line en hausse</TD><TD>Plus d'argent entre qu'il n'en sort = accumulation</TD></TR>
            <TR><TD b>Smart Money Flow</TD><TD>Gros volumes sans mouvement de prix = accumulation silencieuse</TD></TR>
            <TR><TD b>Anomalie de volume</TD><TD>Volume &gt; 2x la normale = activité institutionnelle</TD></TR>
          </Table>
          <ScoreGuide high="Les institutionnels accumulent. Suivez l'argent intelligent." low="Distribution — les gros vendent" />
        </CriterionCard>

        <CriterionCard emoji="⚡" name="6. Vélocité Fondamentale (IVF)" description="Ne regarde pas si les fondamentaux sont bons mais s'ils s'améliorent de plus en plus vite.">
          <ScoreGuide high="Accélération fondamentale forte, surperformance du benchmark" low="Décélération — l'actif perd de l'élan" />
        </CriterionCard>

        <CriterionCard emoji="🌍" name="7. Macro Tailwind (MTS)" description="Le vent macro-économique souffle-t-il dans le bon sens ?">
          <Table headers={["Facteur", "Impact"]}>
            <TR><TD b>Cycle économique</TD><TD>Expansion = favorable aux actions</TD></TR>
            <TR><TD b>Taux d'intérêt</TD><TD>Taux en baisse = favorable</TD></TR>
            <TR><TD b>VIX</TD><TD>&lt; 20 = marché calme, &gt; 30 = panique</TD></TR>
            <TR><TD b>Appétit risque</TD><TD>SPY &gt; GLD = risk-on (favorable)</TD></TR>
          </Table>
          <ScoreGuide high="Vent macro très favorable" low="Vent contraire — conditions défavorables" />
        </CriterionCard>

        <CriterionCard emoji="👥" name="8. Topologie Sociale (SGI)" description="Mesure la qualité de la communauté, pas juste la quantité de mentions.">
          <ScoreGuide high="Communauté active et de qualité, discussions pertinentes" low="Peu d'intérêt social ou discussions négatives" />
        </CriterionCard>

        <CriterionCard emoji="💎" name="9. Unicité du Signal (SUS)" description="Un signal que tout le monde voit est déjà dans le prix = pas d'avantage.">
          <Table headers={["Composante", "Ce qu'elle mesure"]}>
            <TR><TD b>Crowding</TD><TD>Combien d'actifs ont le même signal ? Moins = mieux</TD></TR>
            <TR><TD b>Novelty</TD><TD>Comportement inhabituel historiquement ?</TD></TR>
            <TR><TD b>Timeframe Neglect</TD><TD>Signal visible sur des TF que personne ne regarde ?</TD></TR>
            <TR><TD b>Complexity Premium</TD><TD>Faut-il une analyse complexe pour le voir ?</TD></TR>
          </Table>
          <ScoreGuide high="Signal unique — avantage informationnel probable" low="Signal crowdé — tout le monde l'a vu, pas d'avantage" />
        </CriterionCard>

        <CriterionCard emoji="📋" name="10. Analyse Fondamentale" description="Évalue la santé financière réelle de l'entreprise : est-elle rentable ? en croissance ? bien valorisée ? endettée ? C'est l'analyse 'Warren Buffett'. Ne s'applique qu'aux actions (pas crypto, forex, commodities).">
          <Table headers={["Dimension", "Poids", "Ce qu'elle mesure", "Exemple AAPL"]}>
            <TR><TD b>Profitabilité</TD><TD>25%</TD><TD>Marge nette, ROE, ROA</TD><TD>88/100 (ROE 152%!)</TD></TR>
            <TR><TD b>Croissance</TD><TD>20%</TD><TD>Growth du CA et des bénéfices</TD><TD>78/100 (+15.7% CA)</TD></TR>
            <TR><TD b>Valorisation</TD><TD>20%</TD><TD>P/E, P/B, PEG — cher ou bon marché ?</TD><TD>28/100 (P/E 33 = cher)</TD></TR>
            <TR><TD b>Santé financière</TD><TD>15%</TD><TD>Debt/Equity, Current Ratio, FCF</TD><TD>42/100 (D/E 102)</TD></TR>
            <TR><TD b>Qualité (Piotroski)</TD><TD>10%</TD><TD>9 critères binaires de qualité comptable</TD><TD>78/100 (7/9 passés)</TD></TR>
            <TR><TD b>Dividendes</TD><TD>10%</TD><TD>Yield + soutenabilité du payout</TD><TD>73/100</TD></TR>
          </Table>
          <ScoreGuide high="Entreprise très rentable, en croissance, peu endettée" low="Perte, endettement excessif, valorisation extrême" />
          <Callout>AAPL : score fondamental 64.5/100 — très profitable (ROE 152%) mais chère (P/E 33). Le score équilibre les forces et faiblesses.</Callout>
        </CriterionCard>

        <CriterionCard emoji="🔥" name="11. Narrative Momentum (critère unique)" description="Mesure la vitesse de propagation d'une narrative sur un actif. Les marchés bougent sur les narratives avant les fondamentaux. Ce critère détecte les PLTR, SMCI, IONQ AVANT qu'ils n'explosent.">
          <Table headers={["Composante", "Ce qu'elle mesure"]}>
            <TR><TD b>Volume Acceleration</TD><TD>Le volume explose avant le prix — smart money</TD></TR>
            <TR><TD b>Momentum Shift</TD><TD>Changement de régime : de flat vers directionnel</TD></TR>
            <TR><TD b>Breakout Freshness</TD><TD>Cassure récente d'un range (dans les 5 derniers jours)</TD></TR>
            <TR><TD b>Cross-TF Alignment</TD><TD>Daily, weekly, monthly pointent dans la même direction</TD></TR>
            <TR><TD b>Anomaly Score</TD><TD>Comportement statistiquement inhabituel (Z-score)</TD></TR>
          </Table>
          <Table headers={["Signal", "Signification"]}>
            <TR><TD b>BULLISH_NARRATIVE (&gt; 65)</TD><TD>Narrative haussière en propagation — le mouvement commence</TD></TR>
            <TR><TD b>BUILDING (50-65)</TD><TD>Narrative en construction — accumulation en cours</TD></TR>
            <TR><TD b>EXHAUSTED (&lt; 50)</TD><TD>Narrative épuisée — le mouvement est fini</TD></TR>
          </Table>
          <ScoreGuide high="Narrative en explosion — volume + momentum + breakout alignés" low="Narrative épuisée — plus personne ne pousse" />
        </CriterionCard>

        <H3>Vetos</H3>
        <P>Certains critères peuvent <B>bloquer</B> un actif même si son score global est bon :</P>
        <Table headers={["Critère", "Seuil", "Raison"]}>
          <TR><TD b>MTS &lt; 20</TD><TD>Veto</TD><TD>Vent macro trop contraire</TD></TR>
          <TR><TD b>SUS &lt; 25</TD><TD>Veto</TD><TD>Signal trop crowdé</TD></TR>
          <TR><TD b>IPI &lt; 20</TD><TD>Veto</TD><TD>Distribution institutionnelle massive</TD></TR>
        </Table>
      </>
    ),
  },
  {
    id: "analyser",
    title: "Module 2 — Analyseur",
    icon: <Brain size={18} />,
    content: (
      <>
        <P>Détecte le <B>régime de marché</B> et choisit la meilleure <B>stratégie</B> pour chaque actif.</P>

        <H3>Les 5 régimes de marché</H3>
        <Table headers={["Régime", "Ce que ça signifie"]}>
          <TR><TD b>🟢 BULL</TD><TD>Les prix montent, tendance positive</TD></TR>
          <TR><TD b>🔴 BEAR</TD><TD>Les prix descendent, tendance négative</TD></TR>
          <TR><TD b>🔵 RANGE</TD><TD>Le prix oscille, pas de tendance</TD></TR>
          <TR><TD b>⚫ CRISIS</TD><TD>Chute brutale + volatilité extrême</TD></TR>
          <TR><TD b>🟡 TRANSITION</TD><TD>Changement de régime en cours</TD></TR>
        </Table>
        <P>La détection est <B>probabiliste</B>. Un actif peut être "BULL à 46%, TRANSITION à 30%". Plus c'est haut, plus on est sûr.</P>

        <H3>Les 14 stratégies</H3>
        <P>Le système dispose de 14 stratégies réparties en 3 niveaux :</P>

        <H3>Stratégies Pro (les plus puissantes)</H3>
        <Table headers={["Stratégie", "Edge", "Ce qui la rend supérieure"]}>
          <TR><TD b>Adaptive Trend</TD><TD>Paramètres s'ajustent à la volatilité</TD><TD>EMA courtes quand le marché est nerveux, longues quand il est calme</TD></TR>
          <TR><TD b>Multi-Signal</TD><TD>Exige 4+ indicateurs sur 6 d'accord</TD><TD>Réduit les faux signaux de ~60%. Conv. max = 95</TD></TR>
          <TR><TD b>Keltner Breakout</TD><TD>Canaux adaptatifs (ATR)</TD><TD>S'adapte à chaque actif au lieu d'un range fixe 20j</TD></TR>
          <TR><TD b>VWAP Reversion</TD><TD>Retour au prix moyen pondéré volume</TD><TD>Le "vrai" prix moyen du marché, plus précis que Bollinger</TD></TR>
          <TR><TD b>Momentum Rotation</TD><TD>Classement des 500 actifs</TD><TD>Achète les top 20%, vend les bottom 20%. Prouvé académiquement</TD></TR>
        </Table>

        <H3>Stratégies avancées</H3>
        <Table headers={["Stratégie", "Quand elle fonctionne", "Comment elle entre"]}>
          <TR><TD b>Mean Reversion V2</TD><TD>Excès de prix confirmé</TD><TD>Z-score + Keltner + volume exhaustion</TD></TR>
          <TR><TD b>Fibonacci</TD><TD>Niveaux de support naturels</TD><TD>Rebond sur 0.382 / 0.5 / 0.618 (Golden Ratio)</TD></TR>
          <TR><TD b>Ichimoku</TD><TD>Système complet japonais</TD><TD>Prix vs nuage + Tenkan/Kijun crossover</TD></TR>
          <TR><TD b>Regime-Aware</TD><TD>Filtre par régime</TD><TD>Refuse de trader en CRISIS et TRANSITION</TD></TR>
          <TR><TD b>Pairs Arbitrage</TD><TD>Deux actifs corrélés divergent</TD><TD>Z-score du spread + cointégration + half-life</TD></TR>
        </Table>

        <H3>Stratégies classiques</H3>
        <Table headers={["Stratégie", "Quand elle fonctionne", "Comment elle entre"]}>
          <TR><TD b>Trend Following</TD><TD>Marché en tendance claire</TD><TD>Croisement des moyennes mobiles</TD></TR>
          <TR><TD b>Mean Reversion</TD><TD>Prix en excès</TD><TD>Bollinger + RSI survendu/suracheté</TD></TR>
          <TR><TD b>Breakout</TD><TD>Cassure d'un range</TD><TD>Prix sort d'une zone + volume</TD></TR>
          <TR><TD b>Momentum</TD><TD>Force relative</TD><TD>RSI + MACD + Stochastic alignés</TD></TR>
        </Table>

        <Callout>Les stratégies Pro ont les poids les plus élevés dans la matrice (adaptive_trend 18%, multi_signal 15% en marché haussier). Les classiques sont maintenant des compléments.</Callout>

        <H3>Sharpe Ratio</H3>
        <P>Mesure le rendement ajusté au risque. C'est la métrique la plus importante pour comparer les stratégies :</P>
        <Table headers={["Sharpe", "Verdict"]}>
          <TR><TD b>&gt; 1.5</TD><TD>Excellent</TD></TR>
          <TR><TD b>&gt; 1.0</TD><TD>Bon</TD></TR>
          <TR><TD b>&gt; 0.5</TD><TD>Correct</TD></TR>
          <TR><TD b>&lt; 0</TD><TD>La stratégie perd de l'argent</TD></TR>
        </Table>
      </>
    ),
  },
  {
    id: "scoring",
    title: "Module 3 — Scoring",
    icon: <Target size={18} />,
    content: (
      <>
        <P>Produit la <B>Thèse de Trade</B> — la décision finale avec prix d'entrée, stop-loss et objectifs.</P>

        <H3>Le Verdict</H3>
        <div className="grid grid-cols-3 gap-3 my-4">
          <div className="bg-gold/10 border border-gold/20 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-gold">GO</p>
            <p className="text-xs text-text-secondary mt-1">Toutes les conditions réunies</p>
          </div>
          <div className="bg-yellow-400/10 border border-yellow-400/20 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-yellow-400">ATTENTE</p>
            <p className="text-xs text-text-secondary mt-1">Presque bon, surveiller</p>
          </div>
          <div className="bg-surface border border-border rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-text-secondary">PAS DE TRADE</p>
            <p className="text-xs text-text-secondary mt-1">Rester à l'écart</p>
          </div>
        </div>

        <H3>Composantes du score (poids dynamiques)</H3>
        <P>Les poids s'ajustent automatiquement via le <B>Calibrateur</B> basé sur les top movers du marché :</P>
        <Table headers={["Composante", "Poids initial", "Ce qu'elle mesure"]}>
          <TR><TD b>Conviction stratégie</TD><TD>35%</TD><TD>À quel point la stratégie est sûre de son signal — le plus important</TD></TR>
          <TR><TD b>Score Bayésien</TD><TD>30%</TD><TD>Historique de l'actif + observations actuelles</TD></TR>
          <TR><TD b>Qualité du Contexte (SQC)</TD><TD>20%</TD><TD>Liquidité + timing + volatilité</TD></TR>
          <TR><TD b>Score Scanner (11 critères)</TD><TD>15%</TD><TD>Résumé des 11 critères dont le Narrative Momentum</TD></TR>
        </Table>
        <Callout>Les poids sont ajustés automatiquement chaque nuit. Le calibrateur compare les signaux GO avec les top movers réels du marché. Si le taux de détection est faible, il augmente le poids du scanner et de la conviction, et réduit le bayésien. Suivi dans Performance → Calibrage.</Callout>

        <H3>Position Sizing — Kelly</H3>
        <P>La taille de position est <B>cruciale</B>. Le critère de Kelly calcule la taille optimale :</P>
        <Table headers={["Paramètre", "Signification"]}>
          <TR><TD b>Kelly fraction</TD><TD>% du capital à risquer (ex: 8.9%)</TD></TR>
          <TR><TD b>Position size</TD><TD>Montant en $ (ex: $8 932)</TD></TR>
          <TR><TD b>R:R</TD><TD>Ratio risque/récompense. 1:1.5 = 1$ risqué → 1.50$ de gain potentiel</TD></TR>
          <TR><TD b>Win rate</TD><TD>Probabilité de gain (ex: 61%)</TD></TR>
          <TR><TD b>Expected Value</TD><TD>Si positif = le trade est statistiquement rentable à long terme</TD></TR>
        </Table>
        <Callout>Règle d'or : ne risquez JAMAIS plus de 2% de votre capital sur un seul trade.</Callout>
      </>
    ),
  },
  {
    id: "execution",
    title: "Module 4 — Exécution",
    icon: <Zap size={18} />,
    content: (
      <>
        <P>Le système utilise un <B>Multi-Broker</B> : ordres envoyés en parallèle sur <B>IBKR</B> (argent réel) et <B>Alpaca</B> (paper trading). Si IBKR est indisponible, Alpaca prend le relais automatiquement.</P>

        <H3>Mode Dual Broker</H3>
        <Table headers={["Mode", "Ce qui se passe"]}>
          <TR><TD b>DUAL</TD><TD>IBKR (réel) + Alpaca (paper) en parallèle — chaque trade est exécuté sur les deux</TD></TR>
          <TR><TD b>IBKR_ONLY</TD><TD>Argent réel uniquement — Alpaca non configuré</TD></TR>
          <TR><TD b>ALPACA_ONLY</TD><TD>Paper trading uniquement — IBKR non connecté</TD></TR>
        </Table>

        <H3>Comment exécuter un trade</H3>
        <Table headers={["Action", "Ce qui se passe"]}>
          <TR><TD b>Bouton "Exécuter" (un actif)</TD><TD>Envoie l'ordre aux deux brokers en parallèle</TD></TR>
          <TR><TD b>Bouton "Lancer le Trading"</TD><TD>Exécute TOUS les signaux GO d'un coup</TD></TR>
          <TR><TD b>Pipeline nocturne</TD><TD>Les 6 modules s'enchaînent automatiquement à 22h UTC et exécutent les signaux GO</TD></TR>
        </Table>
        <P>Les actifs <B>déjà en position</B> sont automatiquement retirés de la liste — pas de double exécution.</P>

        <H3>Où sont envoyés les ordres ?</H3>
        <Table headers={["Type d'actif", "IBKR (réel)", "Alpaca (paper)"]}>
          <TR><TD b>Actions US (AAPL, MSFT...)</TD><TD>Oui</TD><TD>Oui</TD></TR>
          <TR><TD b>ETF (SPY, QQQ...)</TD><TD>Oui</TD><TD>Oui</TD></TR>
          <TR><TD b>Crypto (BTC, ETH, SOL)</TD><TD>Oui</TD><TD>Oui</TD></TR>
          <TR><TD b>Actions EU (.PA, .DE, .L)</TD><TD>Oui</TD><TD>Non (simulation)</TD></TR>
          <TR><TD b>Forex (EUR/USD...)</TD><TD>Oui</TD><TD>Non (simulation)</TD></TR>
          <TR><TD b>Commodities (Or, Pétrole...)</TD><TD>Oui</TD><TD>Non (simulation)</TD></TR>
        </Table>
        <Callout>IBKR supporte <B>tous les marchés</B> (US, EU, forex, crypto, commodities). Alpaca ne supporte que les actifs US et crypto. En mode DUAL, les actifs EU/forex/commodities sont exécutés uniquement sur IBKR.</Callout>

        <H3>1. Vérification des biais comportementaux</H3>
        <Table headers={["Biais", "Ce que c'est", "Comment le système le détecte"]}>
          <TR><TD b>🎰 Disposition</TD><TD>Couper les gains trop tôt, garder les pertes</TD><TD>Compare la durée gagnants vs perdants</TD></TR>
          <TR><TD b>😤 Revenge Trading</TD><TD>Augmenter le risque après une perte</TD><TD>Taille de position augmente après perte ?</TD></TR>
          <TR><TD b>😱 FOMO</TD><TD>Entrer tard dans un mouvement</TD><TD>Prix déjà bougé de &gt; 25% ?</TD></TR>
          <TR><TD b>🔄 Over-Trading</TD><TD>Trop de trades = frais excessifs</TD><TD>Compte les trades par jour</TD></TR>
        </Table>

        <H3>2. Scaling 3 tranches</H3>
        <P>Le système n'entre pas tout d'un coup :</P>
        <Table headers={["Tranche", "Taille", "Quand"]}>
          <TR><TD b>T1</TD><TD>40%</TD><TD>Immédiatement</TD></TR>
          <TR><TD b>T2</TD><TD>35%</TD><TD>Ordre limit — quand le prix confirme</TD></TR>
          <TR><TD b>T3</TD><TD>25%</TD><TD>Ordre stop — sur momentum fort</TD></TR>
        </Table>

        <H3>3. Bracket Orders Alpaca</H3>
        <P>Chaque ordre est envoyé à Alpaca comme <B>Bracket Order</B> : entrée + Stop Loss + Take Profit en une seule commande. Même si votre Mac s'éteint, Alpaca exécutera le SL et TP automatiquement.</P>

        <H3>4. Score V2 pré-trade</H3>
        <P>Avant chaque exécution, le système vérifie les <B>8 sources du Score V2</B> :</P>
        <Table headers={["Vérification", "Si échoue"]}>
          <TR><TD b>Score V2 &lt; 50</TD><TD>Trade refusé (NO_TRADE)</TD></TR>
          <TR><TD b>CPI/FOMC demain</TD><TD>Conviction réduite de 50%</TD></TR>
          <TR><TD b>Corrélation &gt; 0.7 avec positions</TD><TD>Sizing divisé par 2</TD></TR>
          <TR><TD b>3+ positions très corrélées</TD><TD>Trade bloqué</TD></TR>
          <TR><TD b>FOMO (&gt; 25% de mouvement)</TD><TD>Trade bloqué</TD></TR>
        </Table>

        <H3>5. Gestion post-entrée (toutes les 5 min)</H3>
        <P>Le <B>TP/SL Monitor</B> vérifie chaque position toutes les 5 minutes pendant les heures de marché :</P>
        <Table headers={["Vérification", "Action"]}>
          <TR><TD b>Trailing Stop</TD><TD>Le SL remonte avec le prix (2×ATR). Ne redescend jamais. Protège les gains automatiquement</TD></TR>
          <TR><TD b>Take Profit</TD><TD>Prix atteint le TP → position fermée, profit pris</TD></TR>
          <TR><TD b>Stop Loss</TD><TD>Prix touche le SL → position fermée, perte coupée</TD></TR>
          <TR><TD b>Essoufflement</TD><TD>5 signaux de santé (Momentum, Volume, Narrative, RSI, P/L). Score &lt; 35 = ÉPUISÉ → fermeture auto</TD></TR>
          <TR><TD b>Signal inverse</TD><TD>Un signal GO apparaît dans la direction opposée → ferme la position et retourne dans le nouveau sens</TD></TR>
          <TR><TD b>File d'attente</TD><TD>Slot libéré → le meilleur signal GO en attente est exécuté automatiquement</TD></TR>
        </Table>

        <H3>6. Détection d'essoufflement</H3>
        <Table headers={["Score santé", "En profit", "En perte"]}>
          <TR><TD b>&gt; 50 (FORT/MODÉRÉ)</TD><TD>Laisser courir</TD><TD>Laisser le SL protéger</TD></TR>
          <TR><TD b>35-50 (FAIBLE)</TD><TD>Resserrer SL à 1×ATR</TD><TD>Fermer — libérer le capital</TD></TR>
          <TR><TD b>&lt; 35 (ÉPUISÉ)</TD><TD>Fermer — prendre le profit</TD><TD>Fermer — couper la perte</TD></TR>
        </Table>

        <H3>7. Sizing intelligent</H3>
        <P>La taille de position dépend du score de conviction du signal :</P>
        <Table headers={["Score signal", "Taille position"]}>
          <TR><TD b>80+</TD><TD>15% du capital — forte conviction</TD></TR>
          <TR><TD b>65-80</TD><TD>10% du capital — conviction moyenne</TD></TR>
          <TR><TD b>58-65</TD><TD>5% du capital — conviction basse</TD></TR>
        </Table>
      </>
    ),
  },
  {
    id: "portfolio",
    title: "Module 5 — Portefeuille",
    icon: <Briefcase size={18} />,
    content: (
      <>
        <H3>Risk Parity</H3>
        <P>Au lieu de mettre le même <B>montant</B>, le système met le même <B>risque</B> sur chaque position. Un actif volatile (crypto) = petite position. Un actif stable (obligation) = grosse position.</P>

        <H3>Stress Tests</H3>
        <P>Simule 4 catastrophes sur votre portefeuille :</P>
        <Table headers={["Scénario", "Ce qui se passe", "Perte typique"]}>
          <TR><TD b>COVID 2020</TD><TD>Crash -34% en 23 jours</TD><TD>Actions -34%, Crypto -50%</TD></TR>
          <TR><TD b>Bear 2022</TD><TD>Baisse prolongée + hausse taux</TD><TD>Actions -25%, Crypto -65%</TD></TR>
          <TR><TD b>Black Swan Crypto</TD><TD>Effondrement type Luna/FTX</TD><TD>Crypto -80%</TD></TR>
          <TR><TD b>Flash Crash</TD><TD>Chute brutale intraday</TD><TD>Actions -10%</TD></TR>
        </Table>

        <H3>Régime du portefeuille</H3>
        <Table headers={["Régime", "Signification", "Action"]}>
          <TR><TD b>ALPHA</TD><TD>Surperformance</TD><TD>Maintenir les positions</TD></TR>
          <TR><TD b>BETA</TD><TD>Performance marché</TD><TD>Normal</TD></TR>
          <TR><TD b>STRESS</TD><TD>Drawdown &gt; 10%</TD><TD>Réduire les positions</TD></TR>
        </Table>

        <H3>Value at Risk (VaR)</H3>
        <P>Perte maximale attendue à 95% de confiance. Exemple : "VaR $629/jour" = il y a 5% de chance de perdre plus de $629 en un jour.</P>

        <H3>Risk Budget</H3>
        <P>Budget de perte maximum fixé à 15% du capital. Le système suit en temps réel combien de budget risque a été utilisé et combien reste. Quand le budget tombe sous 20%, il passe en mode CRITICAL.</P>

        <H3>Max Drawdown Control</H3>
        <Table headers={["Drawdown", "Niveau", "Action automatique"]}>
          <TR><TD b>&gt; -5%</TD><TD>NORMAL</TD><TD>Pas d'action</TD></TR>
          <TR><TD b>-5% à -10%</TD><TD>WARNING</TD><TD>Réduire les positions de 30%</TD></TR>
          <TR><TD b>-10% à -15%</TD><TD>ALERT</TD><TD>Réduire de 60%</TD></TR>
          <TR><TD b>&lt; -20%</TD><TD>CRITICAL</TD><TD>Fermer TOUTES les positions</TD></TR>
        </Table>

        <H3>Rebalancing</H3>
        <P>Quand les poids dérivent de plus de 5% par rapport aux cibles Risk Parity, le système recommande un rééquilibrage avec les ordres précis (acheter/vendre combien de chaque actif).</P>

        <H3>Beta et Exposition</H3>
        <P>Le <B>Beta</B> mesure combien le portefeuille suit le marché (1.0 = suit exactement, &gt; 1.3 = trop agressif). L'<B>exposition sectorielle</B> détecte la concentration (ex: 40% en Tech = risque HIGH).</P>
      </>
    ),
  },
  {
    id: "performance",
    title: "Module 6 — Rentabilité",
    icon: <TrendingUp size={18} />,
    content: (
      <>
        <H3>Meta-Score (0-100)</H3>
        <P>La note de santé globale du système. <B>C'est le chiffre le plus important</B> car il pilote tout :</P>
        <Table headers={["Score", "Engagement", "Ce que fait le système"]}>
          <TR><TD b>&gt; 80</TD><TD>FULL</TD><TD>Taille de position maximale</TD></TR>
          <TR><TD b>60-80</TD><TD>NORMAL</TD><TD>Paramètres standard</TD></TR>
          <TR><TD b>40-60</TD><TD>PRUDENT</TD><TD>Taille réduite de moitié</TD></TR>
          <TR><TD b>&lt; 40</TD><TD>MINIMAL</TD><TD>Pause partielle</TD></TR>
        </Table>

        <H3>Early Warning System (EWS)</H3>
        <P>5 indicateurs d'alerte. Si un atteint <B>CRITIQUE</B>, le pipeline se met en pause automatiquement :</P>
        <Table headers={["Indicateur", "ATTENTION", "ALERTE", "CRITIQUE"]}>
          <TR><TD b>Drawdown</TD><TD>-5%</TD><TD>-10%</TD><TD>-20%</TD></TR>
          <TR><TD b>Série de pertes</TD><TD>3 trades</TD><TD>5 trades</TD><TD>8 trades</TD></TR>
          <TR><TD b>Déclin Win Rate</TD><TD>-10pp</TD><TD>-20pp</TD><TD>-30pp</TD></TR>
          <TR><TD b>Spike Volatilité</TD><TD>1.5x</TD><TD>2.5x</TD><TD>4x</TD></TR>
        </Table>

        <H3>Equity Curve vs SPY</H3>
        <P>La page Performance affiche en temps réel :</P>
        <Table headers={["Métrique", "Ce qu'elle montre"]}>
          <TR><TD b>Equity Curve</TD><TD>Graphique du capital jour par jour — barres vertes (gain) / rouges (perte)</TD></TR>
          <TR><TD b>Return vs SPY</TD><TD>Votre rendement comparé au S&P 500 sur la même période</TD></TR>
          <TR><TD b>Alpha</TD><TD>La surperformance : Return - SPY. Positif = vous battez le marché</TD></TR>
          <TR><TD b>Max Drawdown</TD><TD>La pire perte depuis le pic — mesure le risque réel</TD></TR>
        </Table>

        <H3>Apprentissage Autonome</H3>
        <P>Le système <B>apprend de chaque trade fermé</B> via 3 mécanismes :</P>
        <Table headers={["Mécanisme", "Ce qu'il fait", "Fréquence"]}>
          <TR><TD b>Poids adaptatifs</TD><TD>Les 11 critères du scanner voient leur poids ajustés selon leur pouvoir prédictif réel (+30% max / -30% min)</TD><TD>Après chaque trade</TD></TR>
          <TR><TD b>Matrice live</TD><TD>La meilleure stratégie par actif est recalculée avec les résultats réels, pas juste les backtests</TD><TD>Après chaque trade</TD></TR>
          <TR><TD b>XGBoost retrain</TD><TD>Le modèle ML se ré-entraîne automatiquement avec les nouveaux trades</TD><TD>Hebdomadaire ou tous les 50 trades</TD></TR>
        </Table>
        <Callout>Plus le système trade, plus il devient précis. Après 20-30 trades fermés, les poids adaptatifs commencent à diverger des poids initiaux — le système a trouvé ce qui marche pour votre style.</Callout>

        <H3>Feedback Loop</H3>
        <P>Le Module 6 renvoie des informations au Module 1 pour s'améliorer :</P>
        <ul className="list-disc pl-5 space-y-1 text-sm text-text-secondary">
          <li>Scanner sélectionne mal → réduire son poids automatiquement</li>
          <li>Timing mauvais → raccourcir la shelf life</li>
          <li>Système CRITIQUE → pause automatique via Reversal Guard</li>
          <li>Trade épuisé → fermeture automatique et remplacement par le meilleur signal en queue</li>
        </ul>
        <Callout>Le système forme une boucle fermée : il trade, mesure ses résultats, ajuste ses paramètres, et re-trade avec les nouveaux paramètres.</Callout>

        <H3>Calibrage Automatique (Scoring V2)</H3>
        <P>Le calibrateur ajuste les poids du scoring en se basant sur les <B>top movers réels</B> du marché :</P>
        <Table headers={["Étape", "Ce qui se passe"]}>
          <TR><TD b>1. Mesure</TD><TD>Chaque nuit, identifie les top 20 movers (&gt; 2% de variation)</TD></TR>
          <TR><TD b>2. Évalue</TD><TD>Combien étaient en signal GO ? = taux de détection</TD></TR>
          <TR><TD b>3. Ajuste</TD><TD>Si détection &lt; 30% → augmente conviction + scanner, réduit bayésien</TD></TR>
          <TR><TD b>4. Apprend</TD><TD>Les poids convergent vers l'optimal après 2-3 semaines</TD></TR>
        </Table>
        <P>Visible dans la page Performance → section <B>Calibrage Automatique</B> avec graphique historique, poids actuels, et taux de détection jour par jour.</P>

        <H3>Benchmarks réels</H3>
        <P>Le système compare votre performance à 2 benchmarks :</P>
        <Table headers={["Benchmark", "Ce que c'est"]}>
          <TR><TD b>SPY Buy & Hold</TD><TD>Acheter le S&P 500 et ne rien faire — le benchmark de base</TD></TR>
          <TR><TD b>60/40</TD><TD>60% actions (SPY) + 40% obligations (TLT) — le benchmark conservateur</TD></TR>
        </Table>
        <P>Si vous battez SPY, votre système a de la valeur. Sinon, mieux vaut acheter un ETF.</P>

        <H3>Ratios live</H3>
        <Table headers={["Ratio", "Ce qu'il mesure", "Bon si"]}>
          <TR><TD b>Sharpe</TD><TD>Rendement / risque total</TD><TD>&gt; 0.5</TD></TR>
          <TR><TD b>Sortino</TD><TD>Rendement / risque de perte seulement</TD><TD>&gt; 0.7</TD></TR>
          <TR><TD b>Calmar</TD><TD>Rendement / max drawdown</TD><TD>&gt; 0.5</TD></TR>
        </Table>

        <H3>Rapport hebdomadaire</H3>
        <P>Chaque semaine, le système génère un rapport complet :</P>
        <Table headers={["Section", "Contenu"]}>
          <TR><TD b>Résumé</TD><TD>Equity, P&L, rendement de la semaine</TD></TR>
          <TR><TD b>Top/Flop</TD><TD>Meilleure et pire position</TD></TR>
          <TR><TD b>vs Benchmarks</TD><TD>Surperformez-vous SPY et 60/40 ?</TD></TR>
          <TR><TD b>Risques</TD><TD>VaR, drawdown, budget, beta, exposition</TD></TR>
          <TR><TD b>Recommandations</TD><TD>Actions automatiques (diversifier, réduire beta...)</TD></TR>
        </Table>
        <P>Accessible via <Code>/api/performance/weekly-report</Code>. Sauvegardé automatiquement.</P>
      </>
    ),
  },
  {
    id: "backtest",
    title: "Backtesting",
    icon: <BarChart3 size={18} />,
    content: (
      <>
        <P>Le backtesting teste les stratégies sur des <B>données du passé</B> pour vérifier si elles auraient gagné de l'argent. C'est l'étape de validation avant de risquer du capital.</P>

        <H3>Ce qu'on a testé</H3>
        <Table headers={["Paramètre", "Valeur"]}>
          <TR><TD b>Actifs testés</TD><TD>190 (ceux avec 10+ ans de données)</TD></TR>
          <TR><TD b>Période</TD><TD>10 ans (2 520 jours de trading)</TD></TR>
          <TR><TD b>Stratégies</TD><TD>4 par actif (trend, mean reversion, breakout, momentum)</TD></TR>
          <TR><TD b>Données totales</TD><TD>1.6 million de barres daily (depuis 1962)</TD></TR>
          <TR><TD b>Durée du calcul</TD><TD>~5 heures</TD></TR>
        </Table>

        <H3>Top 10 — Les actifs les plus profitables sur 10 ans</H3>
        <Table headers={["#", "Actif", "Stratégie", "Sharpe", "Return"]}>
          <TR><TD b>1</TD><TD>ARKK (ETF Innovation)</TD><TD>Trend Following</TD><TD>0.997</TD></TR>
          <TR><TD b>2</TD><TD>ETH (Ethereum)</TD><TD>Momentum</TD><TD>0.967</TD></TR>
          <TR><TD b>3</TD><TD>ADA (Cardano)</TD><TD>Breakout</TD><TD>0.888</TD></TR>
          <TR><TD b>4</TD><TD>DOGE (Dogecoin)</TD><TD>Trend Following</TD><TD>0.860</TD></TR>
          <TR><TD b>5</TD><TD>AZN.L (AstraZeneca)</TD><TD>Mean Reversion</TD><TD>0.848</TD></TR>
          <TR><TD b>6</TD><TD>BTC (Bitcoin)</TD><TD>Momentum</TD><TD>0.811</TD></TR>
          <TR><TD b>7</TD><TD>CAT (Caterpillar)</TD><TD>Breakout</TD><TD>0.786</TD></TR>
          <TR><TD b>8</TD><TD>MSFT (Microsoft)</TD><TD>Trend Following</TD><TD>0.706</TD></TR>
          <TR><TD b>9</TD><TD>SPY (S&P 500)</TD><TD>Trend Following</TD><TD>0.692</TD></TR>
          <TR><TD b>10</TD><TD>GOOGL (Google)</TD><TD>Trend Following</TD><TD>0.644</TD></TR>
        </Table>

        <H3>Saisonnalité — Quel mois trader ?</H3>
        <P>Analyse des rendements moyens par mois sur 5 à 64 ans de données (500 actifs) :</P>
        <Table headers={["Mois", "Rendement moyen", "% d'actifs positifs", "Verdict"]}>
          <TR><TD b>Janvier</TD><TD>+4.21%</TD><TD>78%</TD><TD>Meilleur mois — effet "January"</TD></TR>
          <TR><TD b>Avril</TD><TD>+2.49%</TD><TD>85%</TD><TD>Très bon — le plus régulier</TD></TR>
          <TR><TD b>Mai</TD><TD>+2.28%</TD><TD>81%</TD><TD>Bon — "Sell in May" est un mythe</TD></TR>
          <TR><TD b>Mars</TD><TD>+2.12%</TD><TD>75%</TD><TD>Bon</TD></TR>
          <TR><TD b>Février</TD><TD>+1.92%</TD><TD>72%</TD><TD>Correct</TD></TR>
          <TR><TD b>Août</TD><TD>+1.30%</TD><TD>58%</TD><TD>Moyen</TD></TR>
          <TR><TD b>Juin</TD><TD>-0.04%</TD><TD>55%</TD><TD>Neutre</TD></TR>
          <TR><TD b>Septembre</TD><TD>-0.42%</TD><TD>39%</TD><TD>Pire mois — éviter</TD></TR>
        </Table>
        <Callout>Conseil : privilégiez janvier et avril pour les nouvelles positions. Évitez septembre.</Callout>

        <H3>Cycles économiques — Comment le marché se comporte en crise</H3>
        <P>Performance de 500 actifs pendant les grandes périodes historiques :</P>
        <Table headers={["Période", "Rendement moyen", "Ce qui se passe"]}>
          <TR><TD b>Dot-com Crash (2000-02)</TD><TD>-16.7%</TD><TD>Tech s'effondre. UNH et LMT survivent (+255%)</TD></TR>
          <TR><TD b>Crise 2008 (2007-09)</TD><TD>-43.7%</TD><TD>Banques détruites (Citi -98%). NFLX +69%</TD></TR>
          <TR><TD b>COVID (Fév-Mars 2020)</TD><TD>-30.4%</TD><TD>Crash éclair. MRNA +40%, TLT +14%</TD></TR>
          <TR><TD b>Bull 2009-2020</TD><TD>+685%</TD><TD>11 ans de hausse. NVDA +4017%</TD></TR>
          <TR><TD b>Rally IA (2023-24)</TD><TD>+75%</TD><TD>NVDA +839%, PLTR +1084%, SOL +1796%</TD></TR>
        </Table>

        <H3>Walk-Forward — Le test de robustesse</H3>
        <P>Le walk-forward découpe les données en <B>10 fenêtres glissantes</B> et teste chaque sous-période séparément. C'est le test le plus sévère.</P>
        <P><B>Résultat : 0% de consistance.</B> Cela signifie que les stratégies qui marchent sur 10 ans ne marchent pas de façon régulière sur chaque sous-période. C'est un avertissement :</P>
        <Callout>Un backtest positif sur 10 ans ne garantit PAS un profit régulier. Les performances passées ne préjugent pas des résultats futurs. C'est pour ça que le paper trading de 3 mois est indispensable.</Callout>

        <H3>Backtest Pro vs Classique</H3>
        <P>Les 5 stratégies pro ont été comparées aux 4 classiques sur 500 actifs :</P>
        <Table headers={["", "Pro", "Classique", "Égalité"]}>
          <TR><TD b>Actifs gagnés</TD><TD>110</TD><TD>68</TD><TD>39</TD></TR>
        </Table>
        <P><B>Les pro gagnent sur 51% des actifs.</B> La stratégie la plus performante :</P>
        <Table headers={["Stratégie", "Actifs où elle gagne", "Type"]}>
          <TR><TD b>Momentum Rotation</TD><TD>48 actifs</TD><TD>Pro</TD></TR>
          <TR><TD b>VWAP Reversion</TD><TD>30 actifs</TD><TD>Pro</TD></TR>
          <TR><TD b>Mean Reversion</TD><TD>30 actifs</TD><TD>Classique</TD></TR>
          <TR><TD b>Trend Following</TD><TD>23 actifs</TD><TD>Classique</TD></TR>
          <TR><TD b>Multi-Signal</TD><TD>22 actifs</TD><TD>Pro</TD></TR>
        </Table>
        <Callout>Momentum Rotation domine largement (48 actifs) — acheter les actifs les plus forts et vendre les plus faibles est la stratégie prouvée académiquement la plus robuste.</Callout>

        <H3>Comment lire les résultats du backtest</H3>
        <Table headers={["Métrique", "Ce que ça mesure", "Bon signe si"]}>
          <TR><TD b>Sharpe Ratio</TD><TD>Rendement ajusté au risque</TD><TD>&gt; 0.5 (correct), &gt; 1.0 (bon)</TD></TR>
          <TR><TD b>Win Rate</TD><TD>% de trades gagnants</TD><TD>&gt; 50%</TD></TR>
          <TR><TD b>Max Drawdown</TD><TD>Pire perte depuis le pic</TD><TD>&gt; -20% (supportable)</TD></TR>
          <TR><TD b>Profit Factor</TD><TD>Gains bruts / pertes brutes</TD><TD>&gt; 1.5</TD></TR>
          <TR><TD b>Calmar Ratio</TD><TD>Rendement / drawdown</TD><TD>&gt; 0.5</TD></TR>
          <TR><TD b>Consistance (WF)</TD><TD>% de sous-périodes profitables</TD><TD>&gt; 60%</TD></TR>
        </Table>

        <H3>Page Backtesting dans l'app</H3>
        <P>Allez sur <B>/backtest</B> pour tester vous-même : choisissez un actif, lancez le backtest, et comparez les 4 stratégies avec les equity curves.</P>
      </>
    ),
  },
  {
    id: "ai",
    title: "Intelligence Artificielle",
    icon: <Shield size={18} />,
    content: (
      <>
        <P>Bilok-TradePilot utilise 3 couches d'IA pour améliorer les décisions :</P>

        <H3>1. FinBERT — Comprendre le langage financier</H3>
        <P>Modèle d'IA (BERT) entraîné spécifiquement sur des textes financiers. Il comprend que "beat expectations" est positif et "crash incoming" est négatif avec <B>94% de précision</B>.</P>
        <Table headers={["Texte", "Résultat FinBERT"]}>
          <TR><TD>"NVIDIA stock surging, great earnings"</TD><TD b>Positif (94.1%)</TD></TR>
          <TR><TD>"Market crash, sell everything"</TD><TD b>Négatif (68.3%)</TD></TR>
          <TR><TD>"Stock holding steady"</TD><TD b>Neutre</TD></TR>
        </Table>
        <P>Tourne sur votre Mac M3 via Metal/MPS (GPU Apple Silicon).</P>

        <H3>2. XGBoost — Prédire le succès d'un trade</H3>
        <P>Modèle de machine learning entraîné sur <B>15 739 échantillons</B> historiques. Il apprend quelles combinaisons des 9 critères mènent à des trades profitables.</P>
        <Table headers={["Paramètre", "Valeur"]}>
          <TR><TD b>Algorithme</TD><TD>XGBoost (Gradient Boosting)</TD></TR>
          <TR><TD b>Features</TD><TD>9 scores + régime + volatilité + volume = 14 features</TD></TR>
          <TR><TD b>Données</TD><TD>15 739 échantillons (51 actifs × ~300 jours)</TD></TR>
          <TR><TD b>Ré-entraînement</TD><TD>POST /api/scoring/ml/train</TD></TR>
        </Table>

        <H3>3. Ensemble Voting — Combiner les stratégies</H3>
        <P>Au lieu de choisir UNE stratégie, le système fait <B>voter</B> les 14 stratégies. Chaque vote est pondéré par le Sharpe historique. Plus les stratégies sont d'accord, plus le signal est fiable.</P>
        <Callout>Quand &gt; 80% des stratégies votent dans la même direction = bonus de conviction de +15%.</Callout>

        <H3>4. Stratégies Pro vs Basiques</H3>
        <P>Les 5 stratégies pro apportent un avantage que les classiques n'ont pas :</P>
        <Table headers={["Stratégie Pro", "Avantage vs basique"]}>
          <TR><TD b>Adaptive Trend</TD><TD>Paramètres qui changent avec la volatilité (au lieu de EMA 9/21 fixe pour tout)</TD></TR>
          <TR><TD b>Multi-Signal</TD><TD>Exige 4/6 indicateurs d'accord (au lieu d'un seul crossover)</TD></TR>
          <TR><TD b>Keltner Breakout</TD><TD>Canaux ATR adaptatifs (au lieu d'un range fixe 20 jours)</TD></TR>
          <TR><TD b>VWAP Reversion</TD><TD>Prix moyen pondéré par volume (au lieu de Bollinger simple)</TD></TR>
          <TR><TD b>Momentum Rotation</TD><TD>Classement relatif des 500 actifs (prouvé académiquement)</TD></TR>
        </Table>
        <P>Exemple : sur AAPL, les basiques (Trend Following, Breakout) donnaient <B>NEUTRAL</B>. Multi-Signal donne <B>LONG avec 95 de conviction</B> car 5 indicateurs sur 6 sont alignés.</P>
      </>
    ),
  },
  {
    id: "theses",
    title: "Mes Thèses (entrée du pipeline)",
    icon: <Shield size={18} />,
    content: (
      <>
        <P>Les thèses sont votre <B>entrée personnelle</B> dans le pipeline. Elles permettent d'intégrer des informations que le modèle ne peut pas voir seul : géopolitique, rumeurs, convictions sectorielles.</P>

        <H3>Comment ça marche</H3>
        <Table headers={["Étape", "Ce qui se passe"]}>
          <TR><TD b>1. Vous créez une thèse</TD><TD>"Le pétrole va monter — guerre en Iran" (conviction FORTE)</TD></TR>
          <TR><TD b>2. Le système identifie les actifs</TD><TD>XOM, CVX, COP, XLE, CL=F (long) + XLU (short)</TD></TR>
          <TR><TD b>3. Les scores sont boostés</TD><TD>+11 points sur les actifs liés (conviction FORTE = 75%)</TD></TR>
          <TR><TD b>4. Le sizing est ajusté</TD><TD>×1.22 sur les actifs de la thèse</TD></TR>
          <TR><TD b>5. Le plan de trade est généré</TD><TD>Entry, SL, TP pour chaque actif</TD></TR>
        </Table>

        <H3>11 thèmes prédéfinis</H3>
        <Table headers={["Thème", "Actifs Long", "Actifs Short"]}>
          <TR><TD b>Pétrole</TD><TD>CL=F, XOM, CVX, COP, XLE</TD><TD>XLU, NEE</TD></TR>
          <TR><TD b>Or</TD><TD>GC=F, GLD, SI=F, PL=F</TD><TD>SPY, QQQ</TD></TR>
          <TR><TD b>Tech / IA</TD><TD>NVDA, AMD, MSFT, GOOGL, PLTR</TD><TD>—</TD></TR>
          <TR><TD b>Bitcoin</TD><TD>BTC, ETH, SOL, COIN, DOGE</TD><TD>—</TD></TR>
          <TR><TD b>Récession</TD><TD>TLT, GLD, XLU, JNJ, KO</TD><TD>SPY, QQQ, ARKK</TD></TR>
          <TR><TD b>Guerre</TD><TD>LMT, RTX, BA, GC=F, CL=F</TD><TD>SPY, EEM</TD></TR>
          <TR><TD b>Inflation</TD><TD>GC=F, CL=F, XLE, ZW=F</TD><TD>TLT, QQQ, ARKK</TD></TR>
        </Table>

        <H3>4 niveaux de conviction</H3>
        <Table headers={["Niveau", "Boost score", "Boost sizing"]}>
          <TR><TD b>FAIBLE (25%)</TD><TD>+3.75 pts</TD><TD>×1.08</TD></TR>
          <TR><TD b>MOYENNE (50%)</TD><TD>+7.5 pts</TD><TD>×1.15</TD></TR>
          <TR><TD b>FORTE (75%)</TD><TD>+11.25 pts</TD><TD>×1.22</TD></TR>
          <TR><TD b>CERTAINE (90%)</TD><TD>+13.5 pts</TD><TD>×1.27</TD></TR>
        </Table>

        <Callout>Sans thèse active, le système fonctionne normalement avec ses algorithmes seuls. Vous pouvez avoir plusieurs thèses en même temps. Chaque thèse expire après l'horizon défini.</Callout>
      </>
    ),
  },
  {
    id: "correlation",
    title: "Corrélation rapide + Backtest",
    icon: <BarChart3 size={18} />,
    content: (
      <>
        <P>La page Corrélation permet de trouver <B>tous les actifs liés</B> à un actif donné et de <B>simuler l'impact d'un choc</B>.</P>

        <H3>Carte de corrélation</H3>
        <P>Tapez un actif (ou un nom en français : pétrole, or, bitcoin...) et le système compare les 500 actifs en base :</P>
        <Table headers={["Catégorie", "Corrélation", "Signification"]}>
          <TR><TD b>Corrélés positivement</TD><TD>&gt; 0.4</TD><TD>Bougent AVEC — si l'un monte, l'autre aussi</TD></TR>
          <TR><TD b>Corrélés négativement</TD><TD>&lt; -0.2</TD><TD>Bougent CONTRE — hedge naturel</TD></TR>
          <TR><TD b>Neutres</TD><TD>-0.2 à 0.4</TD><TD>Indépendants</TD></TR>
        </Table>

        <H3>Simulation d'impact</H3>
        <P>Entrez un choc (ex: pétrole +20%) et le système calcule l'impact sur chaque actif corrélé via le <B>beta de corrélation</B>. Exemple :</P>
        <Table headers={["Actif", "Beta", "Impact si Oil +20%"]}>
          <TR><TD b>XOM (ExxonMobil)</TD><TD>0.85</TD><TD>+17%</TD></TR>
          <TR><TD b>CVX (Chevron)</TD><TD>0.80</TD><TD>+16%</TD></TR>
          <TR><TD b>XLU (Utilities)</TD><TD>-0.30</TD><TD>-6%</TD></TR>
        </Table>

        <H3>Backtest de corrélation (25 ans)</H3>
        <P>Le backtest vérifie si la corrélation est <B>fiable dans le temps</B> :</P>
        <Table headers={["Analyse", "Ce qu'elle teste"]}>
          <TR><TD b>Rolling Correlation</TD><TD>La corrélation jour par jour sur 25 ans — quand elle casse</TD></TR>
          <TR><TD b>Par période</TD><TD>Corrélation pendant chaque crise (2008, COVID, Bear 2022...)</TD></TR>
          <TR><TD b>Beta Backtest</TD><TD>Quand A fait +2%, B fait-il vraiment +beta*2% ?</TD></TR>
          <TR><TD b>Score de fiabilité</TD><TD>0-100 — au-dessus de 70 = fiable pour trader</TD></TR>
        </Table>

        <Callout>Exemple réel : CL=F/XOM = fiabilité 62.5/100. La corrélation tient en crise (COVID 0.66) mais casse pendant le Rally IA (pétrole -7%, XOM +8%). Utiliser avec stops serrés.</Callout>
      </>
    ),
  },
  {
    id: "analyse_rapide",
    title: "Analyse Rapide",
    icon: <ScanSearch size={18} />,
    content: (
      <>
        <P>La page <B>Analyse Rapide</B> permet d'analyser <B>n'importe quel actif au monde</B> en tapant son nom ou symbole — même s'il n'est pas dans les 500 actifs suivis.</P>

        <H3>Recherche intelligente (autocomplete)</H3>
        <P>Tapez un <B>nom</B> ou un <B>symbole</B> et des suggestions apparaissent en temps réel :</P>
        <Table headers={["Vous tapez", "Le système propose"]}>
          <TR><TD b>BNP</TD><TD>BNP.PA (BNP Paribas) — trouvé en BDD</TD></TR>
          <TR><TD b>danone</TD><TD>BN.PA (Danone) — trouvé via les alias français</TD></TR>
          <TR><TD b>hermes</TD><TD>RMS.PA (Hermès) — alias + résultats TradingView</TD></TR>
          <TR><TD b>nvidia</TD><TD>NVDA (NVIDIA) — trouvé en BDD</TD></TR>
          <TR><TD b>petrole</TD><TD>CL=F (Crude Oil) — alias français</TD></TR>
          <TR><TD b>nestle</TD><TD>NESN.SW (Nestlé) — alias européen</TD></TR>
        </Table>
        <P>La recherche combine <B>3 sources</B> par ordre de priorité :</P>
        <Table headers={["Source", "Vitesse", "Couverture"]}>
          <TR><TD b>1. Base de données</TD><TD>Instantané</TD><TD>500 actifs du pipeline</TD></TR>
          <TR><TD b>2. Aliases français</TD><TD>Instantané</TD><TD>100+ noms courants (CAC 40, pétrole, or, Bitcoin, tout le DAX/SMI...)</TD></TR>
          <TR><TD b>3. TradingView</TD><TD>~100ms</TD><TD>Tous les marchés mondiaux (des milliers d'actifs)</TD></TR>
        </Table>
        <P>Navigation clavier : <Code>Flèches</Code> haut/bas pour naviguer, <Code>Entrée</Code> pour sélectionner, <Code>Échap</Code> pour fermer.</P>

        <H3>Comment ça marche</H3>
        <Table headers={["Étape", "Ce qui se passe"]}>
          <TR><TD b>1. Recherche</TD><TD>Autocomplete intelligent — tapez un nom ou symbole</TD></TR>
          <TR><TD b>2. Téléchargement</TD><TD>Yahoo Finance (priorité) ou TradingView (fallback) fournit 2 ans de données daily</TD></TR>
          <TR><TD b>3. Prix live</TD><TD>Si l'actif est sur Alpaca (US, ETF, crypto), le prix temps réel remplace la clôture</TD></TR>
          <TR><TD b>4. Analyse</TD><TD>20 indicateurs AT + 6 scores + 12 stratégies calculés sur les données fraîches</TD></TR>
          <TR><TD b>5. Score V2</TD><TD>Même scoring que le pipeline (8 sources pondérées) — cohérent avec les signaux GO</TD></TR>
          <TR><TD b>6. Verdict</TD><TD>GO / ATTENTE / PAS DE TRADE avec prix d'entrée, SL, TP</TD></TR>
        </Table>

        <H3>Double source de données</H3>
        <P>Si Yahoo Finance échoue (ticker inconnu, rate-limiting...), le système bascule automatiquement sur <B>TradingView</B> via websocket :</P>
        <Table headers={["Source", "Rôle", "Avantage"]}>
          <TR><TD b>Yahoo Finance</TD><TD>Source principale</TD><TD>Gratuit, 20+ ans d'historique, fiable</TD></TR>
          <TR><TD b>TradingView (fallback)</TD><TD>Backup automatique</TD><TD>Tous les marchés mondiaux, jamais en panne</TD></TR>
          <TR><TD b>Alpaca</TD><TD>Prix live</TD><TD>Temps réel pour US/ETF/Crypto</TD></TR>
        </Table>
        <P>Le champ <Code>price_source</Code> dans les résultats indique la source utilisée.</P>

        <H3>Ce que vous voyez</H3>
        <P>Tout est <B>cliquable</B> pour voir les définitions et interprétations :</P>
        <Table headers={["Section", "Cliquable ?", "Ce qui s'affiche"]}>
          <TR><TD b>6 scores (AT, Génome, IPI...)</TD><TD>Oui</TD><TD>Définition + interprétation dynamique du score pour cet actif</TD></TR>
          <TR><TD b>8 indicateurs (RSI, MACD, SMA...)</TD><TD>Oui</TD><TD>Définition + "RSI à 65 = zone neutre, pas de signal extrême"</TD></TR>
          <TR><TD b>12 stratégies</TD><TD>Oui</TD><TD>Qu'est-ce que c'est ? Quand ça fonctionne ? Comment ça entre ? + Signal avec Entry/SL/TP</TD></TR>
          <TR><TD b>Score V2</TD><TD>Oui</TD><TD>Détail des 8 composantes avec poids et scores individuels</TD></TR>
        </Table>

        <H3>Historique</H3>
        <P>Les 20 dernières analyses sont sauvegardées avec le score, la direction et le prix. Cliquez sur un historique pour relancer l'analyse.</P>
      </>
    ),
  },
  {
    id: "live",
    title: "Données temps réel",
    icon: <BarChart3 size={18} />,
    content: (
      <>
        <P>Bilok-TradePilot se connecte à <B>Alpaca</B> pour les prix en temps réel et à <B>FRED</B> pour les données macro-économiques.</P>

        <H3>Prix live (Alpaca)</H3>
        <Table headers={["Type", "Actifs supportés", "Fréquence"]}>
          <TR><TD b>Actions US</TD><TD>AAPL, MSFT, GOOGL, NVDA... (tous)</TD><TD>Temps réel</TD></TR>
          <TR><TD b>ETF</TD><TD>SPY, QQQ, GLD, TLT...</TD><TD>Temps réel</TD></TR>
          <TR><TD b>Crypto</TD><TD>BTC/USD, ETH/USD, SOL/USD</TD><TD>Temps réel 24/7</TD></TR>
          <TR><TD b>Actions EU / Forex / Commodities</TD><TD>—</TD><TD>Données historiques (BDD)</TD></TR>
        </Table>

        <H3>Données macro (FRED)</H3>
        <P>Avec une clé API FRED (gratuite), le système récupère les vrais indicateurs économiques :</P>
        <Table headers={["Indicateur", "Ce qu'il mesure"]}>
          <TR><TD b>Taux Fed Funds</TD><TD>Le taux directeur de la banque centrale américaine</TD></TR>
          <TR><TD b>Treasury 10Y</TD><TD>Taux des obligations d'État à 10 ans</TD></TR>
          <TR><TD b>VIX</TD><TD>L'indice de la peur du marché</TD></TR>
          <TR><TD b>Chômage</TD><TD>Taux de chômage américain</TD></TR>
          <TR><TD b>CPI</TD><TD>Inflation (prix à la consommation)</TD></TR>
          <TR><TD b>M2</TD><TD>Masse monétaire (liquidité dans le système)</TD></TR>
        </Table>
        <Callout>Sans clé FRED, le système utilise des estimations. Avec la clé (gratuite), il utilise les vraies données mise à jour chaque heure.</Callout>

        <H3>Horaires de marché</H3>
        <Table headers={["Marché", "Heures (Paris)", "Jours"]}>
          <TR><TD b>US (NYSE/NASDAQ)</TD><TD>15h30 — 22h00</TD><TD>Lundi — Vendredi</TD></TR>
          <TR><TD b>Europe</TD><TD>9h00 — 17h30</TD><TD>Lundi — Vendredi</TD></TR>
          <TR><TD b>Crypto</TD><TD>24h/24</TD><TD>7j/7</TD></TR>
          <TR><TD b>Forex</TD><TD>24h/24</TD><TD>Lundi — Vendredi</TD></TR>
        </Table>
      </>
    ),
  },
  {
    id: "glossary",
    title: "Glossaire",
    icon: <HelpCircle size={18} />,
    content: (
      <>
        <P>Les termes essentiels expliqués simplement :</P>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2 text-sm">
          <GlossaryItem term="ATR" def="Volatilité en dollars. ATR = $5 = le prix bouge de ~$5/jour" />
          <GlossaryItem term="Backtest" def="Tester une stratégie sur le passé" />
          <GlossaryItem term="Drawdown" def="Perte depuis le plus haut. -10% = vous avez perdu 10% depuis le pic" />
          <GlossaryItem term="FOMO" def="Peur de rater un mouvement → entrer trop tard" />
          <GlossaryItem term="Kelly" def="Formule pour la taille de position optimale" />
          <GlossaryItem term="LONG" def="Parier que le prix va monter (acheter)" />
          <GlossaryItem term="MACD" def="Indicateur de momentum — croisement haut = hausse accélère" />
          <GlossaryItem term="Paper Trading" def="Trading simulé, argent fictif, aucun risque" />
          <GlossaryItem term="P&L" def="Profit & Loss — votre gain ou perte" />
          <GlossaryItem term="RSI" def="Momentum 0-100. > 70 suracheté, < 30 survendu" />
          <GlossaryItem term="R:R" def="Risk/Reward. 1:2 = risquer 1$ pour gagner 2$" />
          <GlossaryItem term="Sharpe" def="Rendement ajusté au risque. > 1 = bon, > 2 = excellent" />
          <GlossaryItem term="SHORT" def="Parier que le prix va descendre (vendre)" />
          <GlossaryItem term="Slippage" def="Différence entre prix voulu et prix obtenu" />
          <GlossaryItem term="Stop Loss" def="Sortie automatique si le prix va contre vous" />
          <GlossaryItem term="Take Profit" def="Sortie automatique quand l'objectif est atteint" />
          <GlossaryItem term="Trailing Stop" def="Stop qui monte avec le prix — protège les gains" />
          <GlossaryItem term="VIX" def="Indice de la peur. < 20 calme, > 30 panique" />
          <GlossaryItem term="Win Rate" def="% de trades gagnants. 55% = 55 sur 100 gagnants" />
          <GlossaryItem term="XGBoost" def="Algorithme ML qui apprend quelles combinaisons de critères = trade profitable" />
          <GlossaryItem term="FinBERT" def="IA qui comprend le langage financier (positif/négatif/neutre)" />
          <GlossaryItem term="Ensemble" def="Combinaison des votes de plusieurs stratégies pour un signal plus fiable" />
          <GlossaryItem term="Fibonacci" def="Niveaux naturels (0.382, 0.5, 0.618) où le prix rebondit souvent" />
          <GlossaryItem term="Ichimoku" def="Système japonais complet : tendance + support + timing en un graphique" />
          <GlossaryItem term="Alpaca" def="Broker en ligne pour le paper trading (argent virtuel) et live trading" />
          <GlossaryItem term="FRED" def="Federal Reserve Economic Data — données macro gratuites (taux, VIX...)" />
          <GlossaryItem term="Meta-Score" def="Note 0-100 de la santé du système. Pilote le niveau d'engagement" />
          <GlossaryItem term="EWS" def="Early Warning System — 5 alertes qui peuvent pauser le pipeline" />
          <GlossaryItem term="Z-score" def="Mesure l'extrémité. > 2 = très loin de la moyenne" />
        </div>
      </>
    ),
  },
  {
    id: "settings",
    title: "Paramètres",
    icon: <Settings size={18} />,
    content: (
      <>
        <H3>Brokers</H3>
        <Table headers={["Variable", "Valeur", "Description"]}>
          <TR><TD b>ALPACA_API_KEY</TD><TD>Configuré</TD><TD>Paper trading US — ordres simulés</TD></TR>
          <TR><TD b>ALPACA_SECRET_KEY</TD><TD>Configuré</TD><TD>Idem</TD></TR>
          <TR><TD b>IBKR_ACCOUNT_ID</TD><TD>À configurer</TD><TD>Argent réel — tous les marchés (US, EU, forex, crypto, commodities)</TD></TR>
          <TR><TD b>IBKR_PORT</TD><TD>7497 (paper) / 7496 (live)</TD><TD>Port de connexion à IB Gateway ou TWS</TD></TR>
          <TR><TD b>IBKR_HOST</TD><TD>127.0.0.1</TD><TD>Adresse de IB Gateway (local)</TD></TR>
          <TR><TD b>IBKR_CLIENT_ID</TD><TD>1</TD><TD>ID client pour la connexion API</TD></TR>
        </Table>

        <H3>Configuration IBKR (argent réel)</H3>
        <P>Pour activer le trading réel :</P>
        <Table headers={["Étape", "Action"]}>
          <TR><TD b>1. Compte</TD><TD>Créer un compte sur interactivebrokers.co.uk (KYC 1-3 jours)</TD></TR>
          <TR><TD b>2. IB Gateway</TD><TD>Installer IB Gateway sur le Mac (plus léger que TWS)</TD></TR>
          <TR><TD b>3. Permissions</TD><TD>Activer : US Stocks, EU Stocks, Forex, Crypto, Commodities</TD></TR>
          <TR><TD b>4. .env</TD><TD>Ajouter IBKR_ACCOUNT_ID=xxx et IBKR_PORT=7496</TD></TR>
          <TR><TD b>5. Redémarrer</TD><TD>Le système passe automatiquement en mode DUAL (IBKR réel + Alpaca paper)</TD></TR>
        </Table>
        <Callout>En mode DUAL, chaque trade est exécuté en réel sur IBKR et en paper sur Alpaca. Vous pouvez comparer les deux dans /admin (onglets séparés). Budget initial recommandé : 200€.</Callout>

        <H3>Clés API supplémentaires</H3>
        <Table headers={["Variable", "Où l'obtenir", "Statut"]}>
          <TR><TD b>FRED_API_KEY</TD><TD>fred.stlouisfed.org (gratuit)</TD><TD>Optionnel — données macro réelles</TD></TR>
          <TR><TD b>REDDIT_CLIENT_ID</TD><TD>reddit.com/prefs/apps (gratuit)</TD><TD>Optionnel — sentiment réel</TD></TR>
          <TR><TD b>REDDIT_CLIENT_SECRET</TD><TD>Idem</TD><TD>Optionnel</TD></TR>
          <TR><TD b>NEWSAPI_KEY</TD><TD>newsapi.org</TD><TD>Optionnel — actualités financières</TD></TR>
        </Table>
        <Callout>Les clés FRED et Reddit sont gratuites et enrichissent fortement le modèle. Sans elles, le système utilise des estimations.</Callout>

        <H3>Hébergement</H3>
        <Table headers={["Couche", "Service", "Détail"]}>
          <TR><TD b>Frontend</TD><TD>Vercel (gratuit)</TD><TD>bilok-tradepilot.vercel.app — URL propre, HTTPS, CDN mondial</TD></TR>
          <TR><TD b>Backend API</TD><TD>Mac local + Cloudflare Tunnel</TD><TD>FastAPI exposé via tunnel sécurisé (HTTPS)</TD></TR>
          <TR><TD b>Base de données</TD><TD>PostgreSQL local</TD><TD>500 actifs, 2.4M barres daily, 412K barres 1H</TD></TR>
          <TR><TD b>Cache</TD><TD>Redis local</TD><TD>Sessions, Celery broker</TD></TR>
        </Table>
        <Callout>Le Mac doit rester allumé pour que le backend fonctionne. Si le tunnel redémarre, il faut rebuilder le frontend avec la nouvelle URL API puis redéployer sur Vercel.</Callout>

        <H3>Sources de données</H3>
        <Table headers={["Source", "Usage", "Coût"]}>
          <TR><TD b>Yahoo Finance</TD><TD>Données historiques OHLCV (2 ans daily)</TD><TD>Gratuit</TD></TR>
          <TR><TD b>TradingView</TD><TD>Recherche de symboles (autocomplete) + fallback données historiques</TD><TD>Gratuit</TD></TR>
          <TR><TD b>Alpaca</TD><TD>Prix live + exécution (paper trading)</TD><TD>Gratuit</TD></TR>
          <TR><TD b>FRED</TD><TD>Données macro (taux, VIX, chômage, M2)</TD><TD>Gratuit</TD></TR>
        </Table>

        <H3>Architecture du cache</H3>
        <P>Le système utilise un <B>cache disque persistant</B> pour afficher tous les résultats instantanément :</P>
        <Table headers={["Quand", "Ce qui se passe"]}>
          <TR><TD b>21h30 UTC</TD><TD>MAJ données daily (500 actifs)</TD></TR>
          <TR><TD b>22h UTC</TD><TD>Pipeline complet automatique : Scanner → Cache Corrélation → Analyseur → Scoring → Exécution → Portefeuille → Performance (~35 min)</TD></TR>
          <TR><TD b>Toutes les 4h</TD><TD>MAJ données intraday 1H</TD></TR>
          <TR><TD b>La journée</TD><TD>Tous les modules affichent instantanément depuis le cache disque — aucun calcul lourd</TD></TR>
          <TR><TD b>En temps réel</TD><TD>Seuls les calculs légers sont live : Analyse rapide (1 actif), Corrélation, Exécution d'un trade</TD></TR>
        </Table>
        <P>Le cache de corrélation (500×500 actifs) est calculé <B>une seule fois</B> après le scanner et partagé par tous les modules — ce qui réduit le pipeline de ~2h à ~35 min.</P>
        <P>Les fichiers cache sont dans <Code>data/*_cache.json</Code> et survivent aux redémarrages.</P>

        <H3>Administration</H3>
        <P>La page <B>/admin</B> donne accès au monitoring complet du système. Elle comprend trois onglets :</P>
        <Table headers={["Onglet", "Contenu"]}>
          <TR><TD b>IBKR Live</TD><TD>Argent réel — capital en €, P/L, Win Rate, Profit Factor, positions heatmap, best/worst trade. Badge "ARGENT RÉEL" vert</TD></TR>
          <TR><TD b>Historique</TD><TD>Tous les trades (ouverts + fermés) avec date/heure, Entry, Exit, SL, TP, P/L, durée, raison de fermeture (TP/SL/Manuel). Filtres par statut (Tous/Ouvertes/Fermées/Gains/Pertes) et par broker (Alpaca/IBKR/Local)</TD></TR>
          <TR><TD b>Alpaca Paper</TD><TD>Paper trading en $ — mêmes stats mais en simulation</TD></TR>
          <TR><TD b>Système</TD><TD>Services, Caches, BDD, Positions, Utilisateurs avec gestion admin, Logs</TD></TR>
        </Table>
        <Callout>L'onglet IBKR affiche les instructions de configuration tant que le compte n'est pas connecté. L'onglet Historique montre un tableau professionnel avec badges colorés par broker (ALP vert, IBKR bleu, LOC gris).</Callout>

        <H3>Gestion des utilisateurs</H3>
        <P>La section Utilisateurs dans l'onglet Système permet de :</P>
        <Table headers={["Action", "Comment"]}>
          <TR><TD b>Voir les utilisateurs</TD><TD>Liste avec nom, email, date d'inscription et badge Admin</TD></TR>
          <TR><TD b>Définir un admin</TD><TD>Cliquez sur l'icône bouclier à côté d'un utilisateur — le badge ADMIN doré apparaît</TD></TR>
          <TR><TD b>Retirer admin</TD><TD>Recliquez sur le bouclier — le statut admin est retiré</TD></TR>
          <TR><TD b>Supprimer</TD><TD>Icône poubelle (sauf le compte admin@tradepilot.local qui est protégé)</TD></TR>
        </Table>
        <Callout>Le compte <Code>admin@tradepilot.local</Code> est automatiquement admin et ne peut pas être supprimé. Les nouveaux comptes sont créés sans droit admin par défaut.</Callout>

        <H3>Commandes</H3>
        <div className="bg-surface rounded-xl p-4 font-mono text-xs space-y-2">
          <div><span className="text-gold">bash scripts/start_all.sh</span> <span className="text-text-secondary">— Démarrer tout (backend + frontend + Celery + tunnel)</span></div>
          <div><span className="text-gold">bash scripts/stop_all.sh</span> <span className="text-text-secondary">— Arrêter tout</span></div>
          <div><span className="text-gold">bash scripts/status.sh</span> <span className="text-text-secondary">— Vérifier l'état de tous les services</span></div>
          <div><span className="text-gold">python scripts/precompute_all.py</span> <span className="text-text-secondary">— Pré-calculer tous les modules (remplir le cache)</span></div>
          <div><span className="text-gold">bash scripts/keep_alive.sh</span> <span className="text-text-secondary">— Surveille et relance les services automatiquement</span></div>
          <div><span className="text-gold">pytest tests/</span> <span className="text-text-secondary">— Lancer les 123 tests</span></div>
        </div>

        <H3>Statistiques du système</H3>
        <Table headers={["Métrique", "Valeur"]}>
          <TR><TD b>Actifs en base</TD><TD>500 (233 US, 76 EU, 53 Crypto, 89 ETF, 30 Forex, 19 Commodities)</TD></TR>
          <TR><TD b>Barres daily</TD><TD>1.8M+ (depuis 1962 — 64 ans)</TD></TR>
          <TR><TD b>Barres intraday 1H</TD><TD>420K+</TD></TR>
          <TR><TD b>Stratégies</TD><TD>14 (5 pro + 5 avancées + 4 classiques)</TD></TR>
          <TR><TD b>Critères scanner</TD><TD>11 (dont Narrative Momentum — critère unique qui détecte les narratives en propagation)</TD></TR>
          <TR><TD b>Indicateurs AT</TD><TD>20 (7 familles : tendance, momentum, volatilité, volume, structure, divergences, force)</TD></TR>
          <TR><TD b>Scoring</TD><TD>V2 — seuil GO à 65, poids auto-calibrés (Conv 35% + Bay 30% + SQC 20% + Scan 15%), sizing 5-15%</TD></TR>
          <TR><TD b>Exécution</TD><TD>Multi-Broker : IBKR (réel) + Alpaca (paper) en parallèle, tous marchés</TD></TR>
          <TR><TD b>Trailing Stop</TD><TD>Dynamique 2×ATR, resserré à 1×ATR si position faible + en profit</TD></TR>
          <TR><TD b>Essoufflement</TD><TD>5 signaux (Momentum, Volume, Narrative, RSI, P/L) — fermeture auto si épuisé</TD></TR>
          <TR><TD b>Retournement</TD><TD>Fermeture + réouverture automatique si signal GO inverse</TD></TR>
          <TR><TD b>Reversal Guard</TD><TD>5 signaux macro (régime, VIX, drawdown, SMA200, sell-off) — protection automatique</TD></TR>
          <TR><TD b>Portefeuille</TD><TD>VaR, Risk Budget, DD Control, Rebalancing, Beta, Equity Curve vs SPY</TD></TR>
          <TR><TD b>Performance</TD><TD>Equity curve live, Alpha vs SPY, Benchmarks, Ratios, Rapport hebdo</TD></TR>
          <TR><TD b>Apprentissage</TD><TD>3 niveaux : poids des 11 critères (accuracy par trade), calibrage scoring V2 (top movers), XGBoost retrain hebdo</TD></TR>
          <TR><TD b>Top Movers</TD><TD>Dashboard : top 10 hausse/baisse du jour + taux de détection marché global + actifs manqués</TD></TR>
          <TR><TD b>Analyseur</TD><TD>Régime global, Catalyseurs, Sector Rotation, Lead-Lag, Anti-corrélation</TD></TR>
          <TR><TD b>Modèles IA</TD><TD>FinBERT (NLP 94%) + XGBoost (auto-retrain) + Narrative Momentum</TD></TR>
          <TR><TD b>Admin</TD><TD>4 onglets : IBKR Live, Historique des trades, Alpaca Paper, Système</TD></TR>
          <TR><TD b>Cache</TD><TD>Persistant sur disque + cache corrélation centralisé (500×500)</TD></TR>
          <TR><TD b>Keep-alive</TD><TD>Backend + Frontend + Celery Worker + Celery Beat + Tunnel</TD></TR>
          <TR><TD b>Max positions</TD><TD>15 simultanées + file d'attente + remplacement auto + positions SHORT</TD></TR>
          <TR><TD b>TP/SL Monitor</TD><TD>Toutes les 5 min : trailing stop, TP, SL, essoufflement, signal inverse, queue</TD></TR>
        </Table>

        <Callout>Bilok-TradePilot est un outil d'aide à la décision, pas un conseil financier. Ne tradez jamais avec de l'argent que vous ne pouvez pas perdre. Commencez toujours par le paper trading.</Callout>
      </>
    ),
  },
];

// ============================================================
// Page principale
// ============================================================

export default function Guide() {
  const [openSections, setOpenSections] = useState<Set<string>>(new Set(["start"]));

  const toggle = (id: string) => {
    setOpenSections((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const openAll = () => setOpenSections(new Set(SECTIONS.map(s => s.id)));
  const closeAll = () => setOpenSections(new Set());

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold">Guide Utilisateur</h2>
          <p className="text-text-secondary text-sm mt-1">
            Tout comprendre sur Bilok-TradePilot, même sans expérience en trading
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={openAll} className="text-xs px-3 py-1.5 bg-surface border border-border rounded-lg hover:bg-gold/10 transition-colors">
            Tout ouvrir
          </button>
          <button onClick={closeAll} className="text-xs px-3 py-1.5 bg-surface border border-border rounded-lg hover:bg-gold/10 transition-colors">
            Tout fermer
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {SECTIONS.map((section) => {
          const isOpen = openSections.has(section.id);
          return (
            <div key={section.id} className="bg-card border border-border rounded-xl overflow-hidden">
              <button
                onClick={() => toggle(section.id)}
                className="w-full flex items-center gap-3 p-5 text-left hover:bg-surface/50 transition-colors"
              >
                <div className="w-9 h-9 rounded-lg bg-gold/10 text-gold flex items-center justify-center flex-shrink-0">
                  {section.icon}
                </div>
                <span className="text-sm font-semibold flex-1">{section.title}</span>
                {isOpen ? <ChevronDown size={16} className="text-text-secondary" /> : <ChevronRight size={16} className="text-text-secondary" />}
              </button>
              {isOpen && (
                <div className="px-5 pb-5 border-t border-border/30 pt-4">
                  {section.content}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================
// Sous-composants
// ============================================================

function H3({ children }: { children: React.ReactNode }) {
  return <h3 className="text-sm font-semibold mt-5 mb-2">{children}</h3>;
}

function P({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-text-secondary leading-relaxed mb-3">{children}</p>;
}

function B({ children }: { children: React.ReactNode }) {
  return <strong className="text-text-primary font-semibold">{children}</strong>;
}

function Code({ children }: { children: React.ReactNode }) {
  return <code className="bg-surface px-1.5 py-0.5 rounded text-xs font-mono text-gold">{children}</code>;
}

function Callout({ children }: { children: React.ReactNode }) {
  return (
    <div className="my-4 p-4 bg-gold/5 border-l-4 border-gold/40 rounded-r-lg text-sm text-text-secondary">
      {children}
    </div>
  );
}

function Table({ headers, children }: { headers: string[]; children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto my-3">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-border">
            {headers.map((h) => (
              <th key={h} className="text-left pb-2 pr-3 text-text-secondary font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

function TR({ children }: { children: React.ReactNode }) {
  return <tr className="border-b border-border/30">{children}</tr>;
}

function TD({ children, b }: { children: React.ReactNode; b?: boolean }) {
  return <td className={`py-2 pr-3 ${b ? "font-semibold text-text-primary" : "text-text-secondary"}`}>{children}</td>;
}

function CriterionCard({ emoji, name, description, children }: {
  emoji: string; name: string; description: string; children: React.ReactNode;
}) {
  return (
    <div className="my-4 bg-surface rounded-xl p-4 border border-border/30">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{emoji}</span>
        <span className="text-sm font-semibold">{name}</span>
      </div>
      <p className="text-xs text-text-secondary mb-3">{description}</p>
      {children}
    </div>
  );
}

function ScoreGuide({ high, low }: { high: string; low: string }) {
  return (
    <div className="mt-2 space-y-1 text-xs">
      <div className="flex gap-2"><span className="text-gold font-semibold w-16">Score &gt; 70</span><span className="text-text-secondary">{high}</span></div>
      <div className="flex gap-2"><span className="text-red-400 font-semibold w-16">Score &lt; 40</span><span className="text-text-secondary">{low}</span></div>
    </div>
  );
}

function GlossaryItem({ term, def }: { term: string; def: string }) {
  return (
    <div className="py-1.5 border-b border-border/20">
      <span className="font-mono font-semibold text-gold">{term}</span>
      <span className="text-text-secondary ml-2">{def}</span>
    </div>
  );
}
