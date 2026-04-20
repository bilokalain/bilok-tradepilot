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

const STRAT_INFO: Record<string, { type: string; edge: string; when: string }> = {
  trend_following: { type: "Classic", edge: "Croisement EMA 9/21 confirmé par SMA 50", when: "Marché en tendance claire" },
  mean_reversion: { type: "Classic", edge: "Bollinger + RSI survendu/suracheté", when: "Prix en excès par rapport à sa moyenne" },
  breakout: { type: "Classic", edge: "Cassure de range avec confirmation volume", when: "Sortie d'une zone de consolidation" },
  momentum: { type: "Classic", edge: "RSI + MACD + Stochastic alignés", when: "Momentum fort et soutenu" },
  mean_reversion_v2: { type: "Avancé", edge: "Z-Score + Stochastic + Keltner", when: "Excès confirmé par 3 indicateurs" },
  fibonacci: { type: "Avancé", edge: "Rebond sur niveaux 38.2% / 50% / 61.8%", when: "Pullback dans une tendance" },
  ichimoku: { type: "Avancé", edge: "Nuage Kumo + Tenkan/Kijun crossover", when: "Tendance confirmée par le nuage" },
  adaptive_trend: { type: "Pro", edge: "EMA dynamiques selon la volatilité", when: "Toutes conditions — auto-ajusté" },
  multi_signal: { type: "Pro", edge: "4/6 indicateurs d'accord — -60% faux signaux", when: "Forte convergence de signaux" },
  keltner_breakout: { type: "Pro", edge: "Canaux ATR adaptatifs", when: "Breakout de volatilité" },
  vwap_reversion: { type: "Pro", edge: "Retour au VWAP institutionnel", when: "Écart excessif par rapport au VWAP" },
  momentum_rotation: { type: "Pro", edge: "Classement relatif des 500 actifs", when: "Achète top 20%, vend bottom 20%" },
  regime_cascade: { type: "Genius", edge: "Changement régime court vs moyen terme", when: "Leader a bougé, suiveurs pas encore" },
  volatility_explosion: { type: "Genius", edge: "3+ signaux de compression simultanés", when: "ATR + Bollinger + volume comprimés" },
  anti_consensus: { type: "Genius", edge: "Contrarian sur euphorie/panique extrême", when: "RSI >78 + volume déclinant + crowdé" },
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
  const activeStrats = strategies.filter((s: any) => s.direction !== "NEUTRAL" && s.conviction > 0);
  const sorted = [...activeStrats].sort((a: any, b: any) => (b.conviction || 0) - (a.conviction || 0));
  const top6 = sorted.slice(0, 6);
  const others = sorted.slice(6);
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

      {/* ═══ 4. ONGLETS STRATÉGIES (Top 6 + autres) ═══ */}
      <div className="mt-6">
        <InfoCard title={`Top ${top6.length} Stratégies`} icon={<TrendingUp size={18} />} description="Les stratégies les plus convaincantes. Cliquez pour voir le détail : edge, plan de trade, interprétation.">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
            {top6.map((s: any, i: number) => {
              const info = STRAT_INFO[s.strategy] || { type: "?", edge: "", when: "" };
              const typeColor = TYPE_COLORS[info.type] || TYPE_COLORS.Classic;
              const isExpanded = expandedStrat === s.strategy;
              return (
                <button key={s.strategy} onClick={() => setExpandedStrat(isExpanded ? null : s.strategy)}
                  className={`text-left p-4 rounded-xl border transition-all ${isExpanded ? "border-gold bg-gold/5 ring-1 ring-gold/30" : "border-border hover:border-gold/20"}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold border ${typeColor}`}>{info.type}</span>
                    <span className="text-lg font-bold text-gold">#{i + 1}</span>
                  </div>
                  <p className="text-sm font-semibold">{STRATEGY_LABELS[s.strategy] || s.strategy}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${s.direction === "LONG" ? "bg-gold/10 text-gold" : "bg-red-400/10 text-red-400"}`}>{s.direction}</span>
                    <span className="text-xs text-text-secondary">Conv. {s.conviction}/100</span>
                  </div>
                  <p className="text-[9px] text-text-secondary mt-2 italic">{info.edge}</p>
                </button>
              );
            })}
          </div>

          {/* Détail stratégie sélectionnée */}
          {expandedStrat && (() => {
            const s = strategies.find((st: any) => st.strategy === expandedStrat);
            if (!s) return null;
            const info = STRAT_INFO[s.strategy] || { type: "?", edge: "", when: "" };
            return (
              <div className="bg-surface border border-gold/10 rounded-xl p-5 space-y-3 mb-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-lg font-bold text-gold">{STRATEGY_LABELS[s.strategy]}</h4>
                  <button onClick={() => setExpandedStrat(null)} className="text-xs text-text-secondary hover:text-text-primary">Fermer</button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-card rounded-lg p-3 text-center">
                    <p className="text-[9px] text-text-secondary">Direction</p>
                    <p className={`text-lg font-bold ${s.direction === "LONG" ? "text-gold" : "text-red-400"}`}>{s.direction}</p>
                  </div>
                  <div className="bg-card rounded-lg p-3 text-center">
                    <p className="text-[9px] text-text-secondary">Conviction</p>
                    <p className="text-lg font-bold">{s.conviction}<span className="text-sm text-text-secondary">/100</span></p>
                  </div>
                </div>
                {s.entry && s.stop_loss && (
                  <div className="grid grid-cols-4 gap-2 text-xs">
                    <div className="bg-card rounded-lg p-2 text-center"><p className="text-[8px] text-text-secondary">Entrée</p><p className="font-mono font-bold">${s.entry}</p></div>
                    <div className="bg-card rounded-lg p-2 text-center"><p className="text-[8px] text-text-secondary">SL</p><p className="font-mono font-bold text-red-400">${s.stop_loss}</p></div>
                    <div className="bg-card rounded-lg p-2 text-center"><p className="text-[8px] text-text-secondary">TP</p><p className="font-mono font-bold text-gold">${s.take_profit}</p></div>
                    <div className="bg-card rounded-lg p-2 text-center"><p className="text-[8px] text-text-secondary">R:R</p><p className="font-mono font-bold">1:{(Math.abs(s.take_profit - s.entry) / Math.abs(s.entry - s.stop_loss)).toFixed(1)}</p></div>
                  </div>
                )}
                <div className="text-xs space-y-1">
                  <p><span className="text-text-secondary">Edge :</span> {info.edge}</p>
                  <p><span className="text-text-secondary">Fonctionne quand :</span> {info.when}</p>
                </div>
              </div>
            );
          })()}

          {/* Autres stratégies */}
          {others.length > 0 && (
            <div className="space-y-1">
              <p className="text-[10px] text-text-secondary uppercase tracking-wider font-semibold mb-2">Autres stratégies ({others.length})</p>
              {others.map((s: any) => {
                const info = STRAT_INFO[s.strategy] || { type: "?" };
                const typeColor = TYPE_COLORS[info.type] || TYPE_COLORS.Classic;
                return (
                  <button key={s.strategy} onClick={() => setExpandedStrat(expandedStrat === s.strategy ? null : s.strategy)}
                    className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-surface text-left">
                    <div className="flex items-center gap-2">
                      <span className={`text-[8px] px-1 py-0.5 rounded font-bold border ${typeColor}`}>{info.type}</span>
                      <span className="text-xs">{STRATEGY_LABELS[s.strategy]}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] px-1 py-0.5 rounded font-semibold ${s.direction === "LONG" ? "bg-gold/10 text-gold" : "bg-red-400/10 text-red-400"}`}>{s.direction}</span>
                      <span className="text-xs font-mono">{s.conviction}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
          {strategies.length > activeStrats.length && (
            <p className="text-[10px] text-text-secondary text-center mt-2">{strategies.length - activeStrats.length} stratégies sans signal</p>
          )}
        </InfoCard>
      </div>

      {/* ═══ 5. RADAR 10 CRITÈRES ═══ */}
      <div className="mt-6">
        <InfoCard title="Radar des 10 critères" icon={<Sparkles size={18} />} description="Les 10 dimensions d'analyse du Scanner (Module 1). Contexte pour comprendre pourquoi les stratégies donnent ce signal.">
          <div className="flex justify-center">
            <RadarChart data={criteriaRadar} size={380} />
          </div>
        </InfoCard>
      </div>

      {/* ═══ 6. ONGLETS CRITÈRES ═══ */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(CRITERIA_CONFIG).map(([key, config]) => {
          const score = scores[key] ?? 50;
          const isExpanded = expandedCriterion === key;
          return (
            <button key={key} onClick={() => setExpandedCriterion(isExpanded ? null : key)}
              className={`text-left p-4 rounded-xl border transition-all ${isExpanded ? "border-gold bg-gold/5" : "border-border hover:border-gold/20"}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-lg">{config.icon}</span>
                <span className={`text-xl font-mono font-bold ${score >= 70 ? "text-gold" : score >= 50 ? "text-text-primary" : "text-red-400"}`}>{score.toFixed(0)}</span>
              </div>
              <p className="text-sm font-semibold">{config.label}</p>
              {isExpanded && <p className="text-[10px] text-text-secondary mt-2">{config.description}</p>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
