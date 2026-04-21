import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, TrendingUp, Sparkles, BarChart3, Brain } from "lucide-react";
import api from "../services/api";
import TradingChart from "../components/TradingChart";
import ScoreGauge from "../components/ui/ScoreGauge";
import RadarChart from "../components/ui/RadarChart";
import InfoCard from "../components/ui/InfoCard";
import SignalBadge from "../components/ui/SignalBadge";
import AssetInfoCard from "../components/AssetInfoCard";
import { scannerApi } from "../services/api";
import { STRATEGY_LABELS, STRAT_CONFIG, TYPE_COLORS, CRITERIA_CONFIG } from "../config/strategies";

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

  // Stratégies triées par conviction décroissante (NEUTRAL à 0 en bas)
  const strategies = [...(data.all_strategies || [])].sort((a: any, b: any) => {
    const ca = a.direction === "NEUTRAL" ? -1 : (a.conviction || 0);
    const cb = b.direction === "NEUTRAL" ? -1 : (b.conviction || 0);
    return cb - ca;
  });
  const best = data.best_strategy || {};
  const scores = data.scores || {};

  // Critères triés par score décroissant
  const criteriaEntries = Object.entries(CRITERIA_CONFIG).sort(([a], [b]) => (scores[b] ?? 50) - (scores[a] ?? 50));

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

      {/* ═══ CARTE D'IDENTITÉ ═══ */}
      <AssetInfoCard symbol={symbol!} />

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
        <p className="text-xs text-text-secondary mb-4">Contexte Scanner (Module 1). Triés par score décroissant. Cliquez pour voir la description détaillée.</p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {criteriaEntries.map(([key, config]) => {
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
