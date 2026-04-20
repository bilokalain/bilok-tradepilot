import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, TrendingUp, Sparkles, BarChart3, Brain } from "lucide-react";
import api from "../services/api";
import TradingChart from "../components/TradingChart";
import ScoreGauge from "../components/ui/ScoreGauge";
import RadarChart from "../components/ui/RadarChart";
import InfoCard from "../components/ui/InfoCard";
import SignalBadge from "../components/ui/SignalBadge";
import { scannerApi } from "../services/api";

// ─── Labels et descriptions des 15 stratégies ───
const STRATEGY_LABELS: Record<string, string> = {
  trend_following: "Trend Following", mean_reversion: "Mean Reversion", breakout: "Breakout",
  momentum: "Momentum Adaptatif", mean_reversion_v2: "Mean Reversion V2", fibonacci: "Fibonacci",
  ichimoku: "Ichimoku", adaptive_trend: "Adaptive Trend", multi_signal: "Multi-Signal",
  keltner_breakout: "Keltner Breakout", vwap_reversion: "VWAP Reversion",
  momentum_rotation: "Momentum Rotation", regime_cascade: "Regime Cascade",
  volatility_explosion: "Volatility Explosion", anti_consensus: "Anti-Consensus Alpha",
};

const STRAT_CONFIG: Record<string, { type: string; icon: string; edge: string; when: string; description: string; interpret: (conv: number, dir: string) => string }> = {
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

const TYPE_COLORS: Record<string, string> = {
  Classic: "text-text-secondary bg-surface border-border",
  "Avancé": "text-blue-400 bg-blue-400/10 border-blue-400/20",
  Pro: "text-purple-400 bg-purple-400/10 border-purple-400/20",
  Genius: "text-gold bg-gold/10 border-gold/20",
};

// ─── Critères Scanner ───
const CRITERIA_CONFIG: Record<string, { label: string; icon: string; description: string }> = {
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

export default function AssetAnalyseDetail() {
  const { symbol } = useParams<{ symbol: string }>();
  const [data, setData] = useState<any>(null);
  const [scanData, setScanData] = useState<any>(null);
  const [ohlcv, setOhlcv] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [expandedStrat, setExpandedStrat] = useState<string | null>(null);
  const [expandedCriterion, setExpandedCriterion] = useState<string | null>(null);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    Promise.all([
      api.get(`/scanner/analyse?q=${encodeURIComponent(symbol)}`).catch(() => ({ data: null })),
      api.get(`/scanner/results/${symbol}`).catch(() => ({ data: null })),
      scannerApi.getOhlcv(symbol, 250).catch(() => ({ data: null })),
    ]).then(([analyseRes, scanRes, ohlcvRes]) => {
      setData(analyseRes.data);
      setScanData(scanRes.data);
      if (ohlcvRes.data) setOhlcv(ohlcvRes.data);
    }).finally(() => setLoading(false));
  }, [symbol]);

  if (loading) return <div className="flex items-center justify-center h-64 text-text-secondary">Analyse en cours...</div>;
  if (!data) return <div className="p-6 text-red-400">Erreur de chargement pour {symbol}</div>;

  const strategies = data.all_strategies || [];
  const best = data.best_strategy || {};
  const scores = data.scores || {};

  // Radar stratégies
  const stratRadar = strategies.map((s: any) => ({
    label: (STRATEGY_LABELS[s.strategy] || s.strategy).slice(0, 14),
    value: Math.max(s.conviction || 0, 8),
    icon: s.direction === "LONG" ? "📈" : s.direction === "SHORT" ? "📉" : "—",
  }));

  // Radar critères
  const criteriaRadar = Object.entries(CRITERIA_CONFIG).map(([key, config]) => ({
    label: config.label.length > 12 ? config.label.slice(0, 12) + "." : config.label,
    value: scores[key] ?? 50,
    icon: config.icon,
  }));

  return (
    <div className="max-w-7xl mx-auto">
      {/* Navigation */}
      <div className="flex items-center gap-2 mb-4 text-xs text-text-secondary">
        <Link to="/" className="hover:text-gold transition-colors">Dashboard</Link>
        <span>/</span>
        <Link to="/analyser" className="hover:text-gold transition-colors">Analyseur</Link>
        <span>/</span>
        <span className="text-gold font-semibold">{symbol}</span>
      </div>
      <div className="flex items-center gap-2 mb-6">
        <button onClick={() => window.history.back()} className="flex items-center gap-1.5 px-3 py-1.5 bg-surface border border-border rounded-lg text-xs text-text-secondary hover:text-gold hover:border-gold/30 transition-colors">
          <ArrowLeft size={14} /> Retour
        </button>
        <Link to="/analyser" className="px-3 py-1.5 bg-surface border border-border rounded-lg text-xs text-text-secondary hover:text-gold transition-colors">Analyseur</Link>
        <Link to={`/asset/${symbol}`} className="px-3 py-1.5 bg-surface border border-border rounded-lg text-xs text-text-secondary hover:text-gold transition-colors">Vue Scanner</Link>
        <Link to={`/analyse?q=${symbol}`} className="px-3 py-1.5 bg-gold/10 border border-gold/20 rounded-lg text-xs text-gold font-semibold hover:bg-gold/20 transition-colors">Analyse Rapide</Link>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-3xl font-bold font-mono text-gold">{symbol}</h1>
            {data.info?.sector && <span className="text-xs px-2.5 py-1 bg-surface border border-border rounded-lg">{data.info.sector}</span>}
          </div>
          <p className="text-text-secondary">{data.info?.name || symbol}</p>
        </div>
        <div className="text-right">
          <p className="text-4xl font-mono font-bold">${data.last_price?.toFixed(2)}</p>
          <p className="text-xs text-text-secondary mt-1">{data.data_points} jours de données</p>
        </div>
      </div>

      {/* ═══ 1. VERDICT ═══ */}
      <div className="bg-card border border-border rounded-xl p-6 mb-6">
        <div className="flex items-center gap-8 flex-wrap">
          <ScoreGauge score={data.global_score || 0} size={120} sublabel="/100" label="Score V2" />
          <div>
            <SignalBadge action={data.action} direction={best.direction} size="lg" showExplanation />
            {best.name && (
              <div className="mt-3 p-3 bg-surface rounded-xl">
                <p className="text-xs text-text-secondary">Stratégie recommandée</p>
                <p className="font-semibold">{STRATEGY_LABELS[best.name] || best.name}</p>
                <p className="text-xs text-text-secondary mt-1">Conviction : {best.conviction}/100</p>
              </div>
            )}
          </div>
          {best.stop_loss > 0 && (() => {
            const entry = best.entry || data.last_price;
            const sl = best.stop_loss;
            const tp1 = best.take_profit_1 || best.take_profit;
            const tp2 = best.take_profit_2;
            const rr = sl && tp1 ? (Math.abs(tp1 - entry) / Math.abs(entry - sl)).toFixed(1) : "—";
            return (
              <div className="bg-surface rounded-xl p-4 min-w-[220px]">
                <p className="text-xs text-text-secondary mb-3">Niveaux de prix suggérés</p>
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div><p className="text-xs font-semibold">Entrée</p><p className="text-[9px] text-text-secondary">Prix recommandé pour ouvrir la position</p></div>
                    <p className="text-lg font-mono font-bold">${entry}</p>
                  </div>
                  <div className="flex items-center justify-between">
                    <div><p className="text-xs font-semibold text-red-400">Stop Loss</p><p className="text-[9px] text-text-secondary">Sortie automatique si le prix va contre nous</p></div>
                    <p className="text-lg font-mono font-bold text-red-400">${sl}</p>
                  </div>
                  <div className="flex items-center justify-between">
                    <div><p className="text-xs font-semibold text-gold">Objectif 1</p><p className="text-[9px] text-text-secondary">Premier objectif de profit</p></div>
                    <p className="text-lg font-mono font-bold text-gold">${tp1}</p>
                  </div>
                  {tp2 && (
                    <div className="flex items-center justify-between">
                      <div><p className="text-xs font-semibold text-emerald-400">Objectif 2</p><p className="text-[9px] text-text-secondary">Objectif optimiste (laisser courir)</p></div>
                      <p className="text-lg font-mono font-bold text-emerald-400">${tp2}</p>
                    </div>
                  )}
                </div>
                <div className="mt-3 pt-3 border-t border-border/50 text-xs">
                  <span className="text-text-secondary">Ratio risque/récompense : </span>
                  <span className="font-mono font-semibold text-gold">1:{rr}</span>
                  <p className="text-text-secondary mt-1">Pour chaque dollar risqué, le gain potentiel est de {rr}$.</p>
                </div>
              </div>
            );
          })()}
        </div>
      </div>

      {/* ═══ 2. GRAPHIQUE ═══ */}
      {(ohlcv?.data?.length > 0 || data.ohlcv?.length > 0) && (
        <InfoCard title="Graphique" icon={<BarChart3 size={18} />} description="Historique des prix avec moyennes mobiles.">
          <TradingChart data={ohlcv?.data || data.ohlcv} height={400} />
        </InfoCard>
      )}

      {/* ═══ 3. RADAR 15 STRATÉGIES ═══ */}
      <div className="mt-6">
        <InfoCard title={`Radar des 15 stratégies — ${symbol}`} icon={<Brain size={18} />} description="Conviction de chaque stratégie (0-100). Plus la forme est large, plus les stratégies convergent. Module 2 — Analyseur.">
          <div className="flex justify-center">
            <RadarChart data={stratRadar} size={420} />
          </div>
        </InfoCard>
      </div>

      {/* ═══ 4. CARTES DES 15 STRATÉGIES (style Scanner) ═══ */}
      <div className="mt-6">
        <h3 className="text-lg font-semibold mb-1 flex items-center gap-2"><TrendingUp size={18} /> Les 15 stratégies — {symbol}</h3>
        <p className="text-xs text-text-secondary mb-4">Cliquez sur une stratégie pour voir le détail : description, interprétation du score, plan de trade.</p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {strategies.map((s: any) => {
            const config = STRAT_CONFIG[s.strategy] || { type: "?", icon: "?", edge: "", when: "", description: "", interpret: () => "" };
            const typeColor = TYPE_COLORS[config.type] || TYPE_COLORS.Classic;
            const conv = s.conviction || 0;
            const isExpanded = expandedStrat === s.strategy;
            const interpretation = config.interpret(conv, s.direction);
            return (
              <button key={s.strategy} onClick={() => setExpandedStrat(isExpanded ? null : s.strategy)}
                className={`text-left bg-card rounded-xl border p-5 transition-all ${isExpanded ? "border-gold bg-gold/5 ring-1 ring-gold/30" : "border-border hover:border-gold/20"}`}>
                {/* Header : icône + titre + badge type */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{config.icon}</span>
                    <span className="text-sm font-semibold">{STRATEGY_LABELS[s.strategy] || s.strategy}</span>
                  </div>
                  <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold border ${typeColor}`}>{config.type}</span>
                </div>
                {/* Gauge + direction */}
                <div className="flex items-center gap-4 mb-3">
                  <ScoreGauge score={conv} size={70} />
                  <div className="flex-1">
                    {s.direction !== "NEUTRAL" ? (
                      <span className={`text-xs px-2 py-1 rounded font-semibold ${s.direction === "LONG" ? "bg-gold/10 text-gold" : "bg-red-400/10 text-red-400"}`}>
                        {s.direction === "LONG" ? "📈" : "📉"} {s.direction}
                      </span>
                    ) : (
                      <span className="text-xs px-2 py-1 rounded bg-surface text-text-secondary">— NEUTRAL</span>
                    )}
                    <p className="text-[10px] text-text-secondary mt-1">Poids dans le score final : {s.weight ? `${(s.weight * 100).toFixed(0)}%` : "—"}</p>
                  </div>
                </div>
                {/* Interprétation */}
                <p className="text-[11px] text-text-secondary leading-relaxed">{interpretation}</p>
                {/* Détails au clic */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-border/50 space-y-3">
                    <p className="text-[11px] text-text-secondary">{config.description}</p>
                    <div className="text-xs space-y-1">
                      <p><span className="text-text-secondary">Edge :</span> {config.edge}</p>
                      <p><span className="text-text-secondary">Fonctionne quand :</span> {config.when}</p>
                    </div>
                    {s.entry && s.stop_loss && (
                      <div className="grid grid-cols-4 gap-2 text-xs">
                        <div className="bg-surface rounded-lg p-2 text-center"><p className="text-[8px] text-text-secondary">Entrée</p><p className="font-mono font-bold">${s.entry}</p></div>
                        <div className="bg-surface rounded-lg p-2 text-center"><p className="text-[8px] text-text-secondary">SL</p><p className="font-mono font-bold text-red-400">${s.stop_loss}</p></div>
                        <div className="bg-surface rounded-lg p-2 text-center"><p className="text-[8px] text-text-secondary">TP</p><p className="font-mono font-bold text-gold">${s.take_profit}</p></div>
                        <div className="bg-surface rounded-lg p-2 text-center"><p className="text-[8px] text-text-secondary">R:R</p><p className="font-mono font-bold">1:{(Math.abs(s.take_profit - s.entry) / Math.abs(s.entry - s.stop_loss)).toFixed(1)}</p></div>
                      </div>
                    )}
                  </div>
                )}
              </button>
            );
          })}
        </div>
        {strategies.filter((s: any) => s.direction === "NEUTRAL").length > 0 && (
          <p className="text-[10px] text-text-secondary text-center mt-3">{strategies.filter((s: any) => s.direction === "NEUTRAL").length} stratégies sans signal actif</p>
        )}
      </div>

      {/* ═══ 5. RADAR 10 CRITÈRES ═══ */}
      <div className="mt-6">
        <InfoCard title="Radar des 10 critères" icon={<Sparkles size={18} />} description="Les 10 dimensions d'analyse du Scanner (Module 1). Contexte pour comprendre pourquoi les stratégies donnent ce signal.">
          <div className="flex justify-center">
            <RadarChart data={criteriaRadar} size={380} />
          </div>
        </InfoCard>
      </div>

      {/* ═══ 6. CARTES DES 10 CRITÈRES (style Scanner) ═══ */}
      <div className="mt-6">
        <h3 className="text-lg font-semibold mb-1 flex items-center gap-2"><Sparkles size={18} /> Les 10 critères — {symbol}</h3>
        <p className="text-xs text-text-secondary mb-4">Contexte Scanner (Module 1). Cliquez pour voir la description détaillée.</p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(CRITERIA_CONFIG).map(([key, config]) => {
            const score = scores[key] ?? 50;
            const isExpanded = expandedCriterion === key;
            return (
              <button key={key} onClick={() => setExpandedCriterion(isExpanded ? null : key)}
                className={`text-left bg-card rounded-xl border p-5 transition-all ${isExpanded ? "border-gold bg-gold/5 ring-1 ring-gold/30" : "border-border hover:border-gold/20"}`}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{config.icon}</span>
                    <span className="text-sm font-semibold">{config.label}</span>
                  </div>
                </div>
                <div className="flex items-center gap-4 mb-3">
                  <ScoreGauge score={score} size={70} />
                  <div className="flex-1">
                    <p className="text-[10px] text-text-secondary">Poids dans le score final : {((scanData?.weights?.[key] ?? 0.1) * 100).toFixed(0)}%</p>
                  </div>
                </div>
                <p className="text-[11px] text-text-secondary leading-relaxed">
                  {score >= 75 ? `Score élevé — ce critère contribue fortement au signal positif.`
                    : score >= 60 ? `Score correct — contribution modérée au signal global.`
                    : score >= 40 ? `Score moyen — ce critère est neutre, ni positif ni négatif.`
                    : `Score faible — ce critère tire le signal vers le bas.`}
                </p>
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-border/50">
                    <p className="text-[11px] text-text-secondary">{config.description}</p>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
