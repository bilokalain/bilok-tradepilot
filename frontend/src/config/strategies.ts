export const STRATEGY_LABELS: Record<string, string> = {
  trend_following: "Trend Following", mean_reversion: "Mean Reversion", breakout: "Breakout",
  momentum: "Momentum Adaptatif", mean_reversion_v2: "Mean Reversion V2", fibonacci: "Fibonacci",
  ichimoku: "Ichimoku", adaptive_trend: "Adaptive Trend", multi_signal: "Multi-Signal",
  keltner_breakout: "Keltner Breakout", vwap_reversion: "VWAP Reversion",
  momentum_rotation: "Momentum Rotation", regime_cascade: "Regime Cascade",
  volatility_explosion: "Volatility Explosion", anti_consensus: "Anti-Consensus Alpha",
};

export interface StrategyConfig {
  type: string;
  icon: string;
  edge: string;
  when: string;
  description: string;
  interpret: (conv: number, dir: string) => string;
}

export const STRAT_CONFIG: Record<string, StrategyConfig> = {
  trend_following: { type: "Classic", icon: "📈", edge: "Croisement EMA 9/21 confirmé par SMA 50", when: "Marché en tendance claire",
    description: "Suit la tendance dominante via les moyennes mobiles exponentielles. Détecte les croisements EMA 9/21 confirmés par la SMA 50 et le volume.",
    interpret: (c, d) => c >= 75 ? `Signal ${d} fort. Les moyennes mobiles sont alignées et le prix accélère dans la direction de la tendance. Forte conviction.` : c >= 50 ? `Tendance ${d} modérée. Les EMA se croisent mais la SMA 50 n'a pas encore confirmé. Signal à surveiller.` : c > 0 ? `Faible signal de tendance. Les moyennes mobiles hésitent, pas de direction claire. Attendre une confirmation.` : "Aucun signal de tendance détecté. Les moyennes mobiles sont plates ou contradictoires." },
  mean_reversion: { type: "Classic", icon: "🔄", edge: "Bollinger + RSI survendu/suracheté", when: "Prix en excès par rapport à sa moyenne",
    description: "Détecte les excès de prix par rapport à la moyenne via les bandes de Bollinger et le RSI. Parie sur un retour à la moyenne.",
    interpret: (c, d) => c >= 75 ? `Excès extrême détecté — ${d === "LONG" ? "survendu" : "suracheté"} avec forte probabilité de retour à la moyenne. Signal très fiable.` : c >= 50 ? `Prix éloigné de sa moyenne. ${d === "LONG" ? "RSI en zone de survente" : "RSI en zone de surachat"}. Retour probable mais pas imminent.` : c > 0 ? "Légère déviation par rapport à la moyenne. Pas assez d'excès pour un signal fiable." : "Prix proche de sa moyenne. Aucun excès détecté — la stratégie mean reversion n'est pas applicable." },
  breakout: { type: "Classic", icon: "💥", edge: "Cassure de range avec confirmation volume", when: "Sortie d'une zone de consolidation",
    description: "Détecte les cassures de zones de consolidation (support/résistance) confirmées par une explosion de volume.",
    interpret: (c, d) => c >= 75 ? `Cassure ${d} confirmée ! Volume en forte hausse et prix au-delà du range. Mouvement impulsif en cours.` : c >= 50 ? `Le prix teste les bornes du range. Volume en hausse mais la cassure n'est pas encore confirmée.` : c > 0 ? "Le prix est dans un range sans signal de cassure imminente. Volatilité en compression." : "Pas de structure de range détectée. La stratégie breakout n'est pas applicable actuellement." },
  momentum: { type: "Classic", icon: "🚀", edge: "RSI + MACD + Stochastic alignés", when: "Momentum fort et soutenu",
    description: "Mesure la force du mouvement en cours via RSI, MACD et Stochastic. Signal quand les 3 indicateurs convergent.",
    interpret: (c, d) => c >= 75 ? `Momentum ${d} puissant ! RSI, MACD et Stochastic sont tous alignés dans la même direction. Mouvement fort et soutenu.` : c >= 50 ? `Momentum ${d} modéré. 2 indicateurs sur 3 convergent. Le signal se construit mais n'est pas unanime.` : c > 0 ? "Momentum faible. Les indicateurs divergent — RSI et MACD donnent des signaux contradictoires." : "Aucun momentum détecté. Les oscillateurs sont neutres et sans direction." },
  mean_reversion_v2: { type: "Avancé", icon: "🔬", edge: "Z-Score + Stochastic + Keltner", when: "Excès confirmé par 3 indicateurs",
    description: "Version améliorée du mean reversion. Utilise le Z-Score statistique, le Stochastic lent et les canaux de Keltner pour tripler la confirmation.",
    interpret: (c, d) => c >= 75 ? `Triple confirmation d'excès ! Z-Score, Stochastic et Keltner s'accordent — ${d === "LONG" ? "survente" : "surachat"} extrême avec forte probabilité de rebond.` : c >= 50 ? `Excès détecté par 2 indicateurs sur 3. Signal solide mais attendre la triple confirmation pour maximiser le taux de réussite.` : c > 0 ? "Un seul indicateur détecte un excès. Pas assez de convergence pour un signal V2 fiable." : "Aucun excès détecté par les 3 indicateurs. Marché en équilibre." },
  fibonacci: { type: "Avancé", icon: "🌀", edge: "Rebond sur niveaux 38.2% / 50% / 61.8%", when: "Pullback dans une tendance",
    description: "Identifie les rebonds sur les niveaux de Fibonacci (38.2%, 50%, 61.8%) lors des corrections dans une tendance établie.",
    interpret: (c, d) => c >= 75 ? `Le prix rebondit sur un niveau Fibonacci clé avec confirmation de volume. Zone de ${d === "LONG" ? "support" : "résistance"} Fibonacci respectée.` : c >= 50 ? `Le prix approche d'un niveau Fibonacci. Réaction probable mais pas encore confirmée par le volume.` : c > 0 ? "Le prix est entre deux niveaux Fibonacci. Pas de zone de rebond identifiée clairement." : "Aucune structure Fibonacci exploitable dans le mouvement actuel." },
  ichimoku: { type: "Avancé", icon: "☁️", edge: "Nuage Kumo + Tenkan/Kijun crossover", when: "Tendance confirmée par le nuage",
    description: "Système japonais complet : nuage Kumo (support/résistance dynamique), croisement Tenkan/Kijun et position du Chikou Span.",
    interpret: (c, d) => c >= 75 ? `Signal Ichimoku fort ! Prix ${d === "LONG" ? "au-dessus" : "en-dessous"} du nuage, croisement Tenkan/Kijun confirmé, Chikou aligné. Tendance claire.` : c >= 50 ? `Le prix évolue dans ou près du nuage. Tendance ${d} en formation mais pas encore confirmée par tous les composants.` : c > 0 ? "Le prix est dans le nuage Kumo — zone d'indécision. Attendre une sortie claire." : "Aucun signal Ichimoku. Le prix est en zone neutre par rapport au nuage et aux lignes." },
  adaptive_trend: { type: "Pro", icon: "🎯", edge: "EMA dynamiques selon la volatilité", when: "Toutes conditions — auto-ajusté",
    description: "Moyennes mobiles dont la période s'adapte automatiquement à la volatilité. En haute volatilité : périodes longues. En basse volatilité : périodes courtes.",
    interpret: (c, d) => c >= 75 ? `Tendance adaptative ${d} confirmée. Les EMA dynamiques ont convergé et le filtre de volatilité valide le signal. Stratégie auto-ajustée à la condition de marché.` : c >= 50 ? `Signal adaptatif ${d} en construction. La volatilité est en transition — les EMA s'ajustent. Conviction modérée.` : c > 0 ? "Les EMA adaptatives hésitent. La volatilité change rapidement et les périodes s'ajustent — signal instable." : "Pas de tendance détectée par les EMA adaptatives. Marché latéral ou en transition." },
  multi_signal: { type: "Pro", icon: "🔗", edge: "4/6 indicateurs d'accord — -60% faux signaux", when: "Forte convergence de signaux",
    description: "Combine 6 indicateurs indépendants et ne signale que si 4+ convergent. Réduit les faux signaux de 60% par rapport aux stratégies simples.",
    interpret: (c, d) => c >= 75 ? `Convergence forte ! 5-6 indicateurs sur 6 donnent le même signal ${d}. Taux de faux signaux très bas — haute fiabilité.` : c >= 50 ? `4 indicateurs sur 6 convergent en ${d}. Signal solide avec marge de sécurité.` : c > 0 ? "Moins de 4 indicateurs convergent. Le multi-signal refuse de valider — trop de désaccord entre les sources." : "Aucune convergence. Les 6 indicateurs sont dispersés — aucun consensus directionnel." },
  keltner_breakout: { type: "Pro", icon: "📊", edge: "Canaux ATR adaptatifs", when: "Breakout de volatilité",
    description: "Utilise les canaux de Keltner (basés sur l'ATR) pour détecter les expansions de volatilité. Signal quand le prix sort des canaux avec volume.",
    interpret: (c, d) => c >= 75 ? `Breakout Keltner ${d} confirmé ! Le prix a cassé le canal avec expansion de l'ATR et confirmation volume. Mouvement explosif.` : c >= 50 ? `Le prix touche les bornes du canal Keltner. Expansion de volatilité en cours mais pas encore de cassure franche.` : c > 0 ? "Le prix est dans les canaux Keltner. La volatilité est en compression — breakout possible mais pas imminent." : "Prix au centre des canaux. Aucune expansion de volatilité détectée." },
  vwap_reversion: { type: "Pro", icon: "⚖️", edge: "Retour au VWAP institutionnel", when: "Écart excessif par rapport au VWAP",
    description: "Le VWAP (Volume Weighted Average Price) est le prix moyen pondéré par le volume — c'est le prix de référence des institutionnels. Signal quand le prix s'en écarte trop.",
    interpret: (c, d) => c >= 75 ? `Écart excessif au VWAP ! Le prix est ${d === "LONG" ? "très en-dessous" : "très au-dessus"} du VWAP institutionnel. Forte probabilité de retour.` : c >= 50 ? `Le prix s'éloigne du VWAP. Écart notable mais pas encore extrême. Les institutionnels pourraient intervenir.` : c > 0 ? "Léger écart au VWAP. Pas assez significatif pour un signal de reversion fiable." : "Prix collé au VWAP. Aucun écart exploitable — le marché est en équilibre institutionnel." },
  momentum_rotation: { type: "Pro", icon: "🔄", edge: "Classement relatif des 500 actifs", when: "Achète top 20%, vend bottom 20%",
    description: "Compare le momentum de cet actif aux 500 autres. Signal si l'actif est dans le top 20% (LONG) ou bottom 20% (SHORT) en momentum relatif.",
    interpret: (c, d) => c >= 75 ? `L'actif est dans le top 10% en momentum relatif ! ${d === "LONG" ? "Surperformance" : "Sous-performance"} marquée par rapport au reste du marché.` : c >= 50 ? `L'actif est dans le ${d === "LONG" ? "top 20%" : "bottom 20%"} en momentum. Position relative favorable mais pas exceptionnelle.` : c > 0 ? "Momentum moyen — l'actif est dans la médiane du marché. Pas de surperformance ni de sous-performance notable." : "Aucun signal de rotation. L'actif n'est ni leader ni retardataire en momentum relatif." },
  regime_cascade: { type: "Genius", icon: "🌊", edge: "Changement régime court vs moyen terme", when: "Leader a bougé, suiveurs pas encore",
    description: "Détecte quand le régime de marché change sur le court terme mais pas encore sur le moyen terme — signe que les suiveurs n'ont pas encore réagi.",
    interpret: (c, d) => c >= 75 ? `Cascade de régime détectée ! Le court terme a basculé en ${d} mais le moyen terme ne suit pas encore. Fenêtre d'opportunité avant que le consensus rattrape.` : c >= 50 ? `Divergence de régime émergente. Le court terme montre des signes de changement — les suiveurs commencent à réagir.` : c > 0 ? "Léger décalage entre régimes court et moyen terme. Pas assez de divergence pour un signal exploitable." : "Régimes alignés. Pas de cascade — le marché est en phase sur tous les horizons." },
  volatility_explosion: { type: "Genius", icon: "🌋", edge: "3+ signaux de compression simultanés", when: "ATR + Bollinger + volume comprimés",
    description: "Détecte les compressions extrêmes de volatilité (ATR, Bollinger, volume tous au minimum) — précurseur d'un mouvement explosif imminent.",
    interpret: (c, d) => c >= 75 ? `Compression extrême ! ATR, Bollinger et volume sont tous au plancher. Explosion de volatilité imminente — direction ${d} probable. Mouvement majeur attendu.` : c >= 50 ? `2 signaux de compression sur 3 détectés. La volatilité se contracte — un mouvement approche mais le timing n'est pas encore optimal.` : c > 0 ? "Volatilité en légère compression. Pas assez de signaux convergents pour anticiper une explosion." : "Volatilité normale ou en expansion. Aucun setup de compression détecté." },
  anti_consensus: { type: "Genius", icon: "🎭", edge: "Contrarian sur euphorie/panique extrême", when: "RSI >78 + volume déclinant + crowdé",
    description: "Stratégie contrariante qui se positionne à l'opposé du consensus quand l'euphorie ou la panique est extrême (RSI extrême + volume déclinant + crowding élevé).",
    interpret: (c, d) => c >= 75 ? `Sentiment extrême détecté ! Le marché est en ${d === "LONG" ? "panique" : "euphorie"} avec volume déclinant et position crowdée. Signal contrarian fort — le retournement approche.` : c >= 50 ? `Excès de sentiment modéré. Le consensus est ${d === "LONG" ? "trop baissier" : "trop haussier"} mais les conditions de retournement ne sont pas toutes réunies.` : c > 0 ? "Léger biais de sentiment mais pas assez extrême pour un signal contrarian fiable." : "Sentiment équilibré. Pas d'excès de consensus détecté — la stratégie anti-consensus n'est pas applicable." },
};

export const TYPE_COLORS: Record<string, string> = {
  Classic: "text-text-secondary bg-surface border-border",
  "Avancé": "text-blue-400 bg-blue-400/10 border-blue-400/20",
  Pro: "text-purple-400 bg-purple-400/10 border-purple-400/20",
  Genius: "text-gold bg-gold/10 border-gold/20",
};

export interface CriterionConfig {
  label: string;
  icon: string;
  description: string;
}

export const CRITERIA_CONFIG: Record<string, CriterionConfig> = {
  technical: { label: "Analyse Technique", icon: "📊", description: "20 indicateurs en 7 familles — tendance, momentum, volatilité, volume, structure, divergences, force." },
  correlation: { label: "Corrélation", icon: "🔗", description: "Comportement de l'actif par rapport aux autres. Score élevé = comportement indépendant." },
  sentiment: { label: "Sentiment", icon: "💬", description: "Analyse NLP des discussions Reddit et actualités via FinBERT." },
  genome: { label: "Génome Explosif", icon: "🧬", description: "ADN comportemental — phases de cycle, sismographe, mémoire fractale." },
  ipi: { label: "Capital Institutionnel", icon: "🏦", description: "Accumulation/distribution par les institutionnels, smart money flow." },
  ivf: { label: "Vélocité Fondamentale", icon: "⚡", description: "Accélération des fondamentaux — les fondamentaux s'améliorent-ils de plus en plus vite ?" },
  mts: { label: "Macro Tailwind", icon: "🌍", description: "Vent macro-économique — cycle, taux, VIX, appétit pour le risque." },
  sgi: { label: "Topologie Sociale", icon: "👥", description: "Qualité de la communauté — ratio signal/bruit, Network Effect." },
  sus: { label: "Unicité du Signal", icon: "💎", description: "Un signal que tout le monde voit est un mauvais signal. Crowding + novelty." },
  fundamental: { label: "Fondamental", icon: "📋", description: "Valorisation, profitabilité, croissance, santé financière, Piotroski, DCF." },
};
