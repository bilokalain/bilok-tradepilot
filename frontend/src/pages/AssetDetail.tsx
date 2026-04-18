import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, TrendingUp, Shield, Brain, Crosshair, BarChart3, Globe, Users, Fingerprint, Sparkles } from "lucide-react";
import api from "../services/api";
import TradingChart from "../components/TradingChart";
import ScoreGauge from "../components/ui/ScoreGauge";
import RadarChart from "../components/ui/RadarChart";
import InfoCard from "../components/ui/InfoCard";
import SignalBadge from "../components/ui/SignalBadge";
import { scannerApi } from "../services/api";

// ============================================================
// Descriptions pédagogiques pour chaque critère
// ============================================================

const CRITERIA_CONFIG: Record<string, {
  label: string;
  icon: any;
  color: string;
  description: string;
  interpret: (score: number) => string;
}> = {
  technical: {
    label: "Analyse Technique",
    icon: "📊",
    color: "#D4AF37",
    description: "L'analyse technique étudie les mouvements de prix passés pour prédire les mouvements futurs. On regarde les moyennes mobiles (tendance), le RSI (est-ce que l'actif est suracheté ou survendu ?), le MACD (le momentum accélère-t-il ?) et les bandes de Bollinger (la volatilité est-elle anormale ?).",
    interpret: (s) =>
      s >= 75 ? "Forte dynamique haussière. Les indicateurs sont bien alignés : le prix est au-dessus de ses moyennes, le momentum est positif." :
      s >= 60 ? "Dynamique modérément positive. La tendance est favorable mais pas encore explosive." :
      s >= 45 ? "Situation neutre. Pas de tendance claire, le marché hésite." :
      s >= 30 ? "Dynamique légèrement négative. La tendance commence à se retourner." :
      "Dynamique baissière. Les indicateurs pointent vers le bas, le momentum est négatif.",
  },
  correlation: {
    label: "Corrélation",
    icon: "🔗",
    color: "#60A5FA",
    description: "La corrélation mesure comment cet actif bouge par rapport aux autres. Un score élevé signifie que l'actif se découple du groupe — c'est souvent le signe qu'il se passe quelque chose d'unique (en bien ou en mal).",
    interpret: (s) =>
      s >= 70 ? "L'actif se démarque fortement du marché. Il montre un comportement indépendant, ce qui peut signaler une opportunité unique." :
      s >= 50 ? "Corrélation normale. L'actif suit à peu près le marché, rien d'inhabituel." :
      "Forte corrélation. L'actif copie les mouvements du marché — difficile de trouver un avantage ici.",
  },
  sentiment: {
    label: "Sentiment",
    icon: "💬",
    color: "#A78BFA",
    description: "Le sentiment analyse ce que les gens disent de cet actif sur Reddit et les réseaux. Un sentiment positif (les gens sont optimistes) peut précéder une hausse. Un sentiment négatif peut précéder une baisse. Attention : un sentiment extrême peut aussi signaler un retournement.",
    interpret: (s) =>
      s >= 70 ? "Sentiment très positif. Les discussions sont majoritairement optimistes, avec beaucoup de mentions." :
      s >= 55 ? "Sentiment légèrement positif. L'ambiance est plutôt bonne mais sans euphorie." :
      s >= 45 ? "Sentiment neutre. Pas d'opinion dominante dans la communauté." :
      "Sentiment négatif. Les discussions sont pessimistes — attention au risque ou opportunité contrariante.",
  },
  genome: {
    label: "Génome Explosif",
    icon: "🧬",
    color: "#F472B6",
    description: "Le Génome analyse l'ADN comportemental de l'actif. Il détecte les phases de cycle (accumulation avant hausse, distribution avant baisse), les micro-signaux de compression (l'actif se prépare à exploser ?), et compare avec ses patterns historiques (mémoire fractale).",
    interpret: (s) =>
      s >= 70 ? "Configuration pré-explosive ! Plusieurs micro-signaux sont actifs : compression de volatilité, volume en contraction, divergences. Un mouvement majeur est probable." :
      s >= 55 ? "L'actif montre quelques signes d'accumulation. La volatilité se comprime progressivement." :
      s >= 40 ? "Pas de configuration explosive. L'actif est dans une phase normale de son cycle." :
      "Phase de distribution ou de déclin. L'énergie explosive est absente.",
  },
  ipi: {
    label: "Capital Institutionnel",
    icon: "🏦",
    color: "#34D399",
    description: "L'IPI (Institutional Positioning Index) détecte si les gros investisseurs (fonds, banques) achètent ou vendent discrètement. On regarde les anomalies de volume (dark pools), la ligne d'accumulation/distribution, et le smart money flow (gros volumes sans mouvement de prix = accumulation silencieuse).",
    interpret: (s) =>
      s >= 70 ? "Les institutionnels accumulent ! Volume anormal détecté, la ligne A/D monte. Les gros acteurs se positionnent à l'achat." :
      s >= 55 ? "Activité institutionnelle modérée. Quelques signes d'intérêt des gros acteurs." :
      s >= 45 ? "Pas d'activité institutionnelle notable. Le marché est dominé par les particuliers." :
      "Distribution institutionnelle probable. Les gros acteurs semblent vendre — signal d'alerte.",
  },
  ivf: {
    label: "Vélocité Fondamentale",
    icon: "⚡",
    color: "#FBBF24",
    description: "L'IVF (Index de Vélocité Fondamentale) mesure l'accélération des fondamentaux. Ce n'est pas \"les fondamentaux sont-ils bons ?\" mais \"les fondamentaux s'améliorent-ils de plus en plus vite ?\". On regarde l'accélération du prix (proxy du chiffre d'affaires), la force relative vs le marché, et les gaps de surprise post-résultats.",
    interpret: (s) =>
      s >= 70 ? "Les fondamentaux accélèrent fortement ! L'actif surperforme son benchmark et montre des surprises positives répétées." :
      s >= 55 ? "Amélioration fondamentale modérée. La trajectoire est positive mais pas exceptionnelle." :
      s >= 45 ? "Fondamentaux stables. Ni amélioration ni détérioration notable." :
      "Décélération fondamentale. Les fondamentaux se détériorent — l'actif sous-performe.",
  },
  mts: {
    label: "Macro Tailwind",
    icon: "🌍",
    color: "#38BDF8",
    description: "Le MTS (Macro Tailwind Score) évalue si le vent macro-économique souffle dans le bon sens pour cet actif. On regarde le cycle économique (expansion ou récession ?), le régime de taux d'intérêt (la banque centrale aide-t-elle ?), et l'appétit pour le risque (les investisseurs sont-ils en mode risk-on ou risk-off ?).",
    interpret: (s) =>
      s >= 70 ? "Vent macro très favorable ! L'économie est en expansion, les taux sont accommodants, les investisseurs prennent des risques." :
      s >= 55 ? "Environnement macro plutôt favorable. Pas de vent contraire majeur." :
      s >= 40 ? "Macro neutre ou mitigée. Certains facteurs sont favorables, d'autres non." :
      "Vent macro contraire ! Récession, hausse des taux, ou aversion au risque — conditions défavorables.",
  },
  sgi: {
    label: "Topologie Sociale",
    icon: "👥",
    color: "#C084FC",
    description: "Le SGI (Social Graph Index) mesure la qualité de la communauté autour de l'actif. Ce n'est pas juste le volume de mentions, mais aussi le ratio signal/bruit (les gens disent-ils des choses utiles ?), le network effect (pour les crypto : plus d'utilisateurs = plus de valeur), et la tendance de l'intérêt.",
    interpret: (s) =>
      s >= 70 ? "Communauté très active et de qualité. Fort ratio signal/bruit, intérêt en hausse, discussions pertinentes." :
      s >= 55 ? "Communauté active. Les discussions sont présentes mais sans tendance forte." :
      s >= 40 ? "Communauté modeste. Peu de mentions et discussions de qualité variable." :
      "Communauté faible ou négative. Peu d'intérêt social, ou discussions majoritairement négatives.",
  },
  sus: {
    label: "Unicité du Signal",
    icon: "💎",
    color: "#FB923C",
    description: "Le SUS (Signal Uniqueness Score) mesure si ce signal est unique ou si tout le monde voit la même chose. Un signal que tout le monde voit est déjà dans le prix ! On regarde le crowding (combien d'actifs ont le même signal ?), la novelty (est-ce inhabituel ?), le timeframe neglect (visible uniquement sur des TF non-populaires ?), et la complexity premium (le signal nécessite-t-il une analyse complexe ?).",
    interpret: (s) =>
      s >= 70 ? "Signal très unique ! Peu de crowding, comportement inhabituel, avantage informationnel probable." :
      s >= 50 ? "Signal moyennement unique. Quelques éléments distinctifs mais pas exceptionnel." :
      s >= 35 ? "Signal assez commun. Beaucoup d'autres actifs montrent le même pattern — déjà dans le prix." :
      "Signal très crowdé. Tout le monde voit la même chose, aucun avantage — danger de piège.",
  },
  fundamental: {
    label: "Analyse Fondamentale",
    icon: "📈",
    color: "#10B981",
    description: "L'analyse fondamentale évalue la valeur intrinsèque de l'entreprise. 8 dimensions : Valorisation (P/E vs secteur, PEG, DCF), Profitabilité (marges, ROE + tendance trimestrielle), Croissance (accélération revenue/earnings), Santé financière (dette, FCF, liquidité), Dividendes, Score Piotroski (qualité comptable), Earnings Quality (surprises, consensus analystes), et DCF simplifié.",
    interpret: (s) =>
      s >= 75 ? "Excellents fondamentaux. Entreprise rentable, en croissance, bien valorisée. Les analystes sont bullish et les earnings battent les estimations." :
      s >= 60 ? "Bons fondamentaux. L'entreprise est solide avec quelques points d'attention (valorisation ou dette)." :
      s >= 45 ? "Fondamentaux moyens. Certaines dimensions sont faibles (croissance, valorisation ou santé financière)." :
      s >= 30 ? "Fondamentaux fragiles. Profitabilité ou croissance en question, ou valorisation excessive." :
      "Fondamentaux faibles. L'entreprise est en difficulté financière ou très surévaluée.",
  },
};

function _buildFundamentalBreakdown(data: any): { families: any[] } | null {
  if (!data?.dimensions) return null;
  const dims = data.dimensions;
  const families: any[] = [];

  const WEIGHTS: Record<string, number> = {
    valuation: 15, profitability: 20, growth: 20, financial_health: 10,
    dividends: 5, quality_piotroski: 10, earnings_quality: 10, dcf_simplified: 10,
  };
  const LABELS: Record<string, string> = {
    valuation: "Valorisation", profitability: "Profitabilité", growth: "Croissance",
    financial_health: "Santé Financière", dividends: "Dividendes",
    quality_piotroski: "Qualité Piotroski", earnings_quality: "Earnings Quality",
    dcf_simplified: "DCF Simplifié",
  };

  for (const [key, dim] of Object.entries(dims) as [string, any][]) {
    const indicators: any[] = [];
    if (dim.details) {
      for (const [dk, dv] of Object.entries(dim.details) as [string, any][]) {
        if (typeof dv === "object" && dv !== null) {
          indicators.push({
            name: dk.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()),
            value: dv.value ?? dv.score ?? "",
            signal: dv.signal ?? (dv.score != null ? (dv.score >= 65 ? "Bon" : dv.score >= 45 ? "Moyen" : "Faible") : ""),
          });
        } else {
          indicators.push({ name: dk.replace(/_/g, " "), value: String(dv) });
        }
      }
    }
    // Piotroski : ajouter les checks
    if (key === "quality_piotroski" && dim.checks) {
      for (const check of dim.checks) {
        indicators.push({
          name: check.name,
          signal: check.pass ? "Validé" : "Échoué",
        });
      }
    }
    families.push({
      name: LABELS[key] || key,
      score: dim.score ?? 50,
      weight: WEIGHTS[key] || 0,
      signal: dim.interpretation || (dim.score >= 70 ? "Solide" : dim.score >= 50 ? "Correct" : "Faible"),
      indicators,
    });
  }
  return { families };
}

export default function AssetDetail() {
  const { symbol } = useParams<{ symbol: string }>();
  const [ohlcv, setOhlcv] = useState<any>(null);
  const [scan, setScan] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [thesis, setThesis] = useState<any>(null);
  const [mta, setMta] = useState<any>(null);
  const [sentiment, setSentiment] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState<"daily" | "1h">("daily");
  const [techBreakdown, setTechBreakdown] = useState<any>(null);
  const [expandedCriterion, setExpandedCriterion] = useState<string | null>(null);
  const [criterionBreakdowns, setCriterionBreakdowns] = useState<Record<string, any>>({});
  const [fundamentalData, setFundamentalData] = useState<any>(null);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    Promise.all([
      scannerApi.getOhlcv(symbol, 250).catch(() => ({ data: null })),
      api.get(`/scanner/results/${symbol}`).catch(() => ({ data: null })),
      api.get(`/analyser/analyse/${symbol}`).catch(() => ({ data: null })),
      api.get(`/scoring/thesis/${symbol}`).catch(() => ({ data: null })),
      api.get(`/scanner/mta/${symbol}`).catch(() => ({ data: null })),
      api.get(`/scanner/sentiment/${symbol}`).catch(() => ({ data: null })),
      api.get(`/scanner/technical-breakdown/${symbol}`).catch(() => ({ data: null })),
    ])
      .then(([ohlcvRes, scanRes, analysisRes, thesisRes, mtaRes, sentRes, techRes]) => {
        if (ohlcvRes.data) setOhlcv(ohlcvRes.data);
        if (scanRes.data) setScan(scanRes.data);
        if (analysisRes.data) setAnalysis(analysisRes.data);
        if (thesisRes.data) setThesis(thesisRes.data);
        if (mtaRes.data) setMta(mtaRes.data);
        if (sentRes.data) setSentiment(sentRes.data);
        if (techRes.data) setTechBreakdown(techRes.data);
        // Fetch fondamental
        if (symbol) {
          api.get(`/scanner/fundamental/${symbol}`).then(r => {
            if (r.data && r.data.applicable) setFundamentalData(r.data);
          }).catch(() => {});
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [symbol]);

  const loadTimeframe = (tf: "daily" | "1h") => {
    setTimeframe(tf);
    if (!symbol) return;
    if (tf === "1h") {
      api.get(`/scanner/ohlcv-1h/${symbol}?limit=168`).then((res) => {
        setOhlcv({ ...res.data, data: res.data.data.map((d: any) => ({ ...d, date: d.datetime.split("T")[0] })) });
      });
    } else {
      scannerApi.getOhlcv(symbol, 250).then((res) => setOhlcv(res.data));
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-text-secondary">Analyse en cours...</div>;
  if (!scan || scan.error) return (
    <div className="p-6 space-y-4">
      <div className="bg-card border border-border rounded-xl p-6 text-center">
        <p className="text-text-secondary mb-2">L'actif <span className="text-gold font-mono font-bold">{symbol}</span> n'est pas dans les 500 actifs du pipeline.</p>
        <p className="text-sm text-text-secondary mb-4">Utilisez l'<b>Analyse Rapide</b> pour analyser n'importe quel actif au monde.</p>
        <div className="flex gap-3 justify-center">
          <Link to={`/analyse?q=${symbol}`} className="px-4 py-2 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm font-semibold hover:bg-gold/20 transition-colors">
            Analyser {symbol}
          </Link>
          <Link to="/" className="px-4 py-2 bg-surface border border-border rounded-lg text-sm text-text-secondary hover:text-text-primary transition-colors">
            Retour au Dashboard
          </Link>
        </div>
      </div>
    </div>
  );

  const scores = { ...(scan.scores || {}), fundamental: fundamentalData?.score ?? 0 };
  const details = scan.details || {};

  // Données pour le radar chart
  const radarData = Object.entries(CRITERIA_CONFIG).map(([key, config]) => ({
    label: config.label.length > 12 ? config.label.slice(0, 12) + "." : config.label,
    value: scores[key] ?? 50,
    icon: config.icon,
  }));

  return (
    <div className="max-w-7xl mx-auto">
      {/* ============ HEADER ============ */}
      <div className="flex items-start justify-between mb-8">
        <div className="flex items-center gap-5">
          <Link to="/scanner" className="text-text-secondary hover:text-gold transition-colors p-2 hover:bg-surface rounded-lg">
            <ArrowLeft size={20} />
          </Link>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-3xl font-bold font-mono text-gold">{symbol}</h1>
              <span className="text-xs px-2.5 py-1 bg-surface border border-border rounded-lg">{scan.asset_class}</span>
              {analysis?.regime && (
                <span className={`text-xs px-2.5 py-1 border rounded-lg font-semibold ${
                  analysis.regime.regime === "BULL" ? "text-gold bg-gold/10 border-gold/20" :
                  analysis.regime.regime === "BEAR" ? "text-red-400 bg-red-400/10 border-red-400/20" :
                  "text-yellow-400 bg-yellow-400/10 border-yellow-400/20"
                }`}>
                  {analysis.regime.regime === "BULL" ? "Marché haussier" :
                   analysis.regime.regime === "BEAR" ? "Marché baissier" :
                   analysis.regime.regime === "RANGE" ? "Marché latéral" :
                   analysis.regime.regime === "CRISIS" ? "Crise" : "Transition"}
                </span>
              )}
            </div>
            <p className="text-text-secondary">{scan.name}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-4xl font-mono font-bold">${scan.last_close?.toFixed(2)}</p>
          <p className="text-xs text-text-secondary mt-1">{scan.data_points} jours de données historiques</p>
        </div>
      </div>

      {/* ============ VERDICT ============ */}
      <InfoCard
        title="Verdict Bilok-TradePilot"
        icon={<Crosshair size={18} />}
        description="Le verdict combine tous les critères d'analyse (9 au total) pour produire une recommandation claire. Le score global va de 0 à 100 : au-dessus de 65, le système considère que les conditions sont favorables pour entrer en position. Le signal GO/ATTENTE/PAS DE TRADE indique la recommandation finale."
      >
        <div className="flex items-center gap-8 flex-wrap">
          <ScoreGauge score={scores.final ?? 0} size={140} sublabel="/100" label="Score Global" />

          {thesis && thesis.action && (
            <div className="flex-1 min-w-[200px]">
              <SignalBadge action={thesis.action} direction={thesis.direction} size="lg" showExplanation />

              {thesis.strategy && thesis.action !== "NO_TRADE" && (
                <div className="mt-4 p-4 bg-surface rounded-xl">
                  <p className="text-xs text-text-secondary mb-2">Stratégie sélectionnée</p>
                  <p className="font-semibold">{formatStrategy(thesis.strategy)}</p>
                  <p className="text-xs text-text-secondary mt-1">
                    {thesis.strategy === "trend_following" ? "Suit la tendance en cours — entre quand les moyennes mobiles se croisent." :
                     thesis.strategy === "mean_reversion" ? "Parie sur un retour à la moyenne — entre quand le prix est en excès." :
                     thesis.strategy === "breakout" ? "Entre sur la cassure d'un niveau clé avec confirmation par le volume." :
                     "Suit la force relative et le momentum des indicateurs."}
                  </p>
                  {analysis?.best_strategy?.backtest_sharpe !== undefined && (
                    <p className="text-xs mt-2">
                      <span className="text-text-secondary">Performance historique : </span>
                      <span className={`font-mono font-semibold ${analysis.best_strategy.backtest_sharpe > 1 ? "text-gold" : analysis.best_strategy.backtest_sharpe > 0 ? "text-text-primary" : "text-red-400"}`}>
                        Sharpe {analysis.best_strategy.backtest_sharpe.toFixed(2)}
                      </span>
                      <span className="text-text-secondary ml-1">
                        {analysis.best_strategy.backtest_sharpe > 1.5 ? "(excellent)" :
                         analysis.best_strategy.backtest_sharpe > 1 ? "(bon)" :
                         analysis.best_strategy.backtest_sharpe > 0.5 ? "(correct)" :
                         analysis.best_strategy.backtest_sharpe > 0 ? "(faible)" : "(non profitable)"}
                      </span>
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Niveaux de prix */}
          {thesis && thesis.entry && thesis.action === "GO" && (
            <div className="bg-surface rounded-xl p-4 min-w-[220px]">
              <p className="text-xs text-text-secondary mb-3">Niveaux de prix suggérés</p>
              <div className="space-y-2.5">
                <PriceLevel label="Entrée" price={thesis.entry} color="#FFFFFF" description="Prix recommandé pour ouvrir la position" />
                <PriceLevel label="Stop Loss" price={thesis.stop_loss} color="#EF4444" description="Sortie automatique si le prix va contre nous (protection)" />
                <PriceLevel label="Objectif 1" price={thesis.take_profit_1} color="#D4AF37" description="Premier objectif de profit (prendre une partie des gains)" />
                <PriceLevel label="Objectif 2" price={thesis.take_profit_2} color="#F5D060" description="Objectif optimiste (laisser courir les gains)" />
              </div>
              {thesis.sizing && thesis.sizing.risk_reward_ratio > 0 && (
                <div className="mt-3 pt-3 border-t border-border/50 text-xs">
                  <span className="text-text-secondary">Ratio risque/récompense : </span>
                  <span className="font-mono font-semibold text-gold">1:{thesis.sizing.risk_reward_ratio.toFixed(1)}</span>
                  <p className="text-text-secondary mt-1">
                    Pour chaque dollar risqué, le gain potentiel est de {thesis.sizing.risk_reward_ratio.toFixed(1)}$.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </InfoCard>

      {/* ============ GRAPHIQUE ============ */}
      <div className="mt-6">
        <InfoCard
          title="Graphique des prix"
          icon={<BarChart3 size={18} />}
          description="Le graphique en chandeliers japonais montre l'évolution du prix. Chaque bougie représente une période (1 jour ou 1 heure). Une bougie dorée = le prix a monté. Une bougie grise = le prix a baissé. Les lignes sont les moyennes mobiles : elles lissent le prix pour montrer la tendance. Quand le prix est au-dessus des moyennes, la tendance est haussière."
        >
          <div className="flex justify-end gap-1 mb-3">
            {(["daily", "1h"] as const).map((tf) => (
              <button
                key={tf}
                onClick={() => loadTimeframe(tf)}
                className={`px-4 py-1.5 text-xs rounded-lg transition-colors ${
                  timeframe === tf ? "bg-gold/10 text-gold border border-gold/20" : "text-text-secondary hover:text-text-primary bg-surface"
                }`}
              >
                {tf === "daily" ? "Journalier" : "Horaire (1H)"}
              </button>
            ))}
          </div>
          {ohlcv?.data?.length > 0 ? (
            <TradingChart data={ohlcv.data} height={480} />
          ) : (
            <div className="h-96 flex items-center justify-center text-text-secondary">Pas de données</div>
          )}
        </InfoCard>
      </div>

      {/* ============ RADAR 9 CRITÈRES ============ */}
      <div className="mt-6">
        <InfoCard
          title="Radar des 9 critères"
          icon={<Sparkles size={18} />}
          description="Ce radar montre les 9 dimensions d'analyse de Bilok-TradePilot. Plus la forme dorée est large, plus l'actif est fort sur ce critère. Un radar bien rempli = un actif solide sur tous les plans. Un radar déséquilibré = des forces et des faiblesses à prendre en compte. Cliquez sur 'Comment lire cette section ?' sur chaque critère pour en savoir plus."
        >
          <RadarChart data={radarData} size={320} />
        </InfoCard>
      </div>

      {/* ============ DÉTAIL DES 9 CRITÈRES ============ */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(CRITERIA_CONFIG).map(([key, config]) => {
          const score = scores[key] ?? 0;
          const weight = (scan.weights?.[key] ?? 0) * 100;
          const interpretation = config.interpret(score);

          const isExpanded = expandedCriterion === key;
          const breakdown = key === "technical" ? techBreakdown
            : key === "fundamental" ? (fundamentalData ? _buildFundamentalBreakdown(fundamentalData) : null)
            : criterionBreakdowns[key];
          const handleClick = () => {
            if (isExpanded) { setExpandedCriterion(null); return; }
            setExpandedCriterion(key);
            if (key === "technical" && !techBreakdown) {
              api.get(`/scanner/technical-breakdown/${symbol}`).then(r => setTechBreakdown(r.data)).catch(() => {});
            } else if (key === "fundamental") {
              // Déjà chargé via fundamentalData
            } else if (!criterionBreakdowns[key]) {
              api.get(`/scanner/criterion-breakdown/${symbol}/${key}`).then(r => {
                setCriterionBreakdowns(prev => ({ ...prev, [key]: r.data }));
              }).catch(() => {});
            }
          };
          return (
            <div key={key} onClick={handleClick} className="cursor-pointer">
            <InfoCard
              title={`${config.label} ${isExpanded ? "▼" : "▶"}`}
              icon={<span className="text-base">{config.icon}</span>}
              description={config.description}
              accentColor={config.color}
            >
              <div className="flex items-center justify-between mb-3">
                <ScoreGauge score={score} size={80} sublabel="/100" />
                <div className="text-right flex-1 ml-4">
                  <p className="text-xs text-text-secondary leading-relaxed">{interpretation}</p>
                  <p className="text-[10px] text-text-secondary mt-2 opacity-60">
                    Poids dans le score final : {weight.toFixed(0)}%
                  </p>
                </div>
              </div>

              {/* Breakdown détaillé (tous critères) */}
              {isExpanded && breakdown?.families && (
                <div className="space-y-2 mt-2 border-t border-border/50 pt-2" onClick={e => e.stopPropagation()}>
                  {breakdown.families.map((fam: any, fi: number) => (
                    <div key={`${fam.name}-${fi}`} className="bg-surface rounded-lg p-2">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-semibold">{fam.name}</span>
                        <div className="flex items-center gap-2">
                          {fam.score != null && <span className={`text-xs font-mono font-bold ${fam.score >= 65 ? "text-emerald-400" : fam.score >= 45 ? "text-yellow-400" : "text-red-400"}`}>{fam.score}</span>}
                          {fam.weight > 0 && <span className="text-[9px] text-text-secondary">({fam.weight}%)</span>}
                        </div>
                      </div>
                      {fam.signal && <p className="text-[10px] text-text-secondary mb-1">{fam.signal}</p>}
                      {fam.indicators && fam.indicators.length > 0 && (
                        <div className="space-y-0.5">
                          {fam.indicators.map((ind: any, ii: number) => (
                            <div key={`${ind.name}-${ii}`} className="flex items-center justify-between text-[10px]">
                              <span className="text-text-secondary">{ind.name}</span>
                              <div className="flex items-center gap-2">
                                {ind.value != null && <span className="font-mono">{typeof ind.value === "number" ? ind.value.toFixed(2) : ind.value}</span>}
                                {ind.signal && <span className={`px-1 py-0.5 rounded ${
                                  /Haussier|Fort|Hausse|Acheteurs|Au-dessus|Actif|Bullish|Positif|Accumul|Expansion|risk.on|Unique|Inhabituel/i.test(ind.signal) ? "text-emerald-400 bg-emerald-400/10" :
                                  /Baissier|Faible|Baisse|Vendeurs|En dessous|Inactif|Bearish|Négatif|Contraction|Markdown|Capitulation/i.test(ind.signal) ? "text-red-400 bg-red-400/10" :
                                  /Suracheté|Attention|Modéré/i.test(ind.signal) ? "text-yellow-400 bg-yellow-400/10" :
                                  "text-text-secondary bg-surface"
                                }`}>{ind.signal}</span>}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
              {isExpanded && !breakdown && (
                <p className="text-[10px] text-text-secondary mt-2 text-center animate-pulse">Chargement du détail...</p>
              )}

              {/* Détails spécifiques par critère */}
              {key === "genome" && details.genome && (
                <CriterionDetail items={[
                  { label: "Phase du cycle", value: `Phase ${details.genome.cycle_phase}/5`, note: details.genome.cycle_phase <= 2 ? "Accumulation/Markup" : details.genome.cycle_phase >= 4 ? "Distribution/Markdown" : "Distribution" },
                  { label: "Micro-signaux actifs", value: `${details.genome.seismograph_active}`, note: details.genome.seismograph_active >= 3 ? "Forte compression !" : "Normal" },
                ]} />
              )}
              {key === "ipi" && details.ipi && (
                <CriterionDetail items={[
                  { label: "Accumulation/Distribution", value: details.ipi.ad_trend, note: details.ipi.ad_trend === "UP" ? "Les institutionnels achètent" : "Les institutionnels vendent" },
                  { label: "Smart Money Flow", value: details.ipi.smart_money.toFixed(0), note: details.ipi.smart_money > 70 ? "Accumulation silencieuse" : "Pas d'activité" },
                ]} />
              )}
              {key === "mts" && details.mts && (
                <CriterionDetail items={[
                  { label: "Cycle économique", value: capitalize(details.mts.cycle) },
                  { label: "Régime de taux", value: capitalize(details.mts.rates) },
                  { label: "Appétit risque", value: capitalize(details.mts.risk.replace("_", " ")) },
                ]} />
              )}
              {key === "sgi" && details.sgi && (
                <CriterionDetail items={[
                  { label: "Mentions", value: `${details.sgi.mentions}`, note: details.sgi.mentions > 20 ? "Beaucoup de buzz" : "Peu de buzz" },
                  { label: "Signal/Bruit", value: details.sgi.signal_noise.toFixed(0), note: details.sgi.signal_noise > 70 ? "Discussions de qualité" : "Beaucoup de bruit" },
                ]} />
              )}
              {key === "sus" && details.sus && (
                <CriterionDetail items={[
                  { label: "Crowding", value: details.sus.crowding.toFixed(0), note: details.sus.crowding > 60 ? "Signal unique" : "Signal commun" },
                  { label: "Novelty", value: details.sus.novelty.toFixed(0), note: details.sus.novelty > 60 ? "Comportement inhabituel" : "Comportement normal" },
                ]} />
              )}
            </InfoCard>
            </div>
          );
        })}
      </div>

      {/* ============ SIZING KELLY ============ */}
      {thesis?.sizing && thesis.sizing.position_size_usd > 0 && (
        <div className="mt-6">
          <InfoCard
            title="Position Sizing (critère de Kelly)"
            icon={<Shield size={18} />}
            description="Le critère de Kelly calcule la taille optimale de la position pour maximiser la croissance du capital à long terme, sans risquer trop. C'est un calcul mathématique basé sur la probabilité de gain et le ratio risque/récompense. Nous utilisons un quart du Kelly optimal (Fractional Kelly) pour être conservateur."
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <SizingCard
                label="Taille de position"
                value={`$${thesis.sizing.position_size_usd.toFixed(0)}`}
                note={`${(thesis.sizing.kelly_fraction * 100).toFixed(1)}% du capital`}
              />
              <SizingCard
                label="Risque par trade"
                value={`$${thesis.sizing.risk_per_trade_usd.toFixed(0)}`}
                note={`${thesis.sizing.risk_pct_of_capital.toFixed(2)}% du capital`}
                color="text-red-400"
              />
              <SizingCard
                label="Win rate estimé"
                value={`${(thesis.sizing.win_rate_estimate * 100).toFixed(0)}%`}
                note="Probabilité de gain"
              />
              <SizingCard
                label="Expected Value"
                value={thesis.sizing.expected_value.toFixed(3)}
                note={thesis.sizing.expected_value > 0 ? "Avantage positif" : "Pas d'avantage"}
                color={thesis.sizing.expected_value > 0 ? "text-gold" : "text-red-400"}
              />
            </div>
          </InfoCard>
        </div>
      )}

      {/* ============ MULTI-TIMEFRAME ============ */}
      {mta && !mta.error && (
        <div className="mt-6">
          <InfoCard
            title="Analyse Multi-Timeframe"
            icon={<Brain size={18} />}
            description="L'analyse multi-timeframe compare le signal sur différentes échelles de temps (journalier et horaire). Quand les deux timeframes sont alignés (même direction), le signal est plus fiable. Quand ils divergent, il y a de l'incertitude — mieux vaut être prudent."
          >
            <div className="flex items-center gap-6">
              <ScoreGauge score={mta.mta_score} size={90} sublabel="/100" />
              <div>
                <span className={`text-sm px-3 py-1 rounded-lg font-semibold ${
                  mta.alignment === "ALIGNED" ? "bg-gold/10 text-gold" :
                  mta.alignment === "DIVERGENT" ? "bg-red-400/10 text-red-400" :
                  "bg-surface text-text-secondary"
                }`}>
                  {mta.alignment === "ALIGNED" ? "Aligné (signal fort)" :
                   mta.alignment === "DIVERGENT" ? "Divergent (prudence)" : "Partiellement aligné"}
                </span>
                <div className="mt-3 space-y-1">
                  {Object.entries(mta.timeframes || {}).map(([tf, data]: [string, any]) => (
                    <div key={tf} className="flex items-center gap-3 text-sm">
                      <span className="text-text-secondary w-16">{tf === "daily" ? "Journalier" : "Horaire"}</span>
                      <span className={data.direction === "BULLISH" ? "text-gold" : data.direction === "BEARISH" ? "text-red-400" : "text-text-secondary"}>
                        {data.direction === "BULLISH" ? "Haussier" : data.direction === "BEARISH" ? "Baissier" : "Neutre"}
                      </span>
                      <span className="text-xs text-text-secondary">({data.strength.toFixed(0)}%)</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </InfoCard>
        </div>
      )}

      {/* ============ STRATÉGIES BACKTEST ============ */}
      {analysis?.strategy_ranking?.length > 0 && (
        <div className="mt-6 mb-8">
          <InfoCard
            title="Performance historique des stratégies"
            icon={<TrendingUp size={18} />}
            description="Ce classement montre quelle stratégie a le mieux fonctionné pour cet actif dans le passé (backtest sur 2 ans). Le Sharpe ratio mesure le rendement ajusté au risque : au-dessus de 1 c'est bon, au-dessus de 1.5 c'est excellent. La stratégie en tête est celle que Bilok-TradePilot utilise pour cet actif."
          >
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              {analysis.strategy_ranking.map((r: any, i: number) => (
                <div key={r.strategy} className={`bg-surface rounded-xl p-4 ${i === 0 ? "ring-1 ring-gold/30" : ""}`}>
                  {i === 0 && <p className="text-[10px] text-gold font-semibold mb-1">SÉLECTIONNÉE</p>}
                  <p className="text-sm font-semibold">{formatStrategy(r.strategy)}</p>
                  <p className={`text-2xl font-mono font-bold mt-1 ${r.adjusted_sharpe > 1 ? "text-gold" : r.adjusted_sharpe > 0 ? "text-text-primary" : "text-red-400"}`}>
                    {r.adjusted_sharpe.toFixed(2)}
                  </p>
                  <p className="text-[10px] text-text-secondary mt-1">
                    Sharpe ajusté au régime
                  </p>
                </div>
              ))}
            </div>
          </InfoCard>
        </div>
      )}
    </div>
  );
}

// ============================================================
// Sous-composants
// ============================================================

function PriceLevel({ label, price, color, description }: { label: string; price: number; color: string; description: string }) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <span className="text-xs text-text-secondary">{label}</span>
        <p className="text-[10px] text-text-secondary opacity-60">{description}</p>
      </div>
      <span className="font-mono font-bold text-lg" style={{ color }}>${price.toFixed(2)}</span>
    </div>
  );
}

function CriterionDetail({ items }: { items: Array<{ label: string; value: string; note?: string }> }) {
  return (
    <div className="mt-3 pt-3 border-t border-border/30 space-y-1.5">
      {items.map((item) => (
        <div key={item.label} className="flex items-center justify-between text-xs">
          <span className="text-text-secondary">{item.label}</span>
          <div className="text-right">
            <span className="font-mono">{item.value}</span>
            {item.note && <span className="text-text-secondary ml-1.5 text-[10px]">({item.note})</span>}
          </div>
        </div>
      ))}
    </div>
  );
}

function SizingCard({ label, value, note, color }: { label: string; value: string; note: string; color?: string }) {
  return (
    <div className="bg-surface rounded-xl p-4">
      <p className="text-xs text-text-secondary mb-1">{label}</p>
      <p className={`text-xl font-mono font-bold ${color || "text-gold"}`}>{value}</p>
      <p className="text-[10px] text-text-secondary mt-1">{note}</p>
    </div>
  );
}

function formatStrategy(s: string): string {
  const map: Record<string, string> = {
    trend_following: "Trend Following",
    mean_reversion: "Mean Reversion",
    breakout: "Breakout",
    momentum: "Momentum Adaptatif",
  };
  return map[s] || s;
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
