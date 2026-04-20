import { useEffect, useState, useMemo } from "react";
import { Search } from "lucide-react";
import { Link } from "react-router-dom";
import { analyserApi, type AnalysisResult, type RegimeSummary } from "../services/api";
import RadarChart from "../components/ui/RadarChart";

const REGIME_COLORS: Record<string, string> = {
  BULL: "text-gold",
  BEAR: "text-red-400",
  RANGE: "text-blue-400",
  CRISIS: "text-red-600",
  TRANSITION: "text-yellow-400",
};

const REGIME_BG: Record<string, string> = {
  BULL: "bg-gold/10 border-gold/20",
  BEAR: "bg-red-400/10 border-red-400/20",
  RANGE: "bg-blue-400/10 border-blue-400/20",
  CRISIS: "bg-red-600/10 border-red-600/20",
  TRANSITION: "bg-yellow-400/10 border-yellow-400/20",
};

const REGIME_LABELS: Record<string, string> = {
  BULL: "Haussier",
  BEAR: "Baissier",
  RANGE: "Latéral",
  CRISIS: "Crise",
  TRANSITION: "Transition",
};

const STRATEGY_LABELS: Record<string, string> = {
  trend_following: "Trend Following",
  mean_reversion: "Mean Reversion",
  mean_reversion_v2: "Mean Reversion V2",
  breakout: "Breakout",
  momentum: "Momentum Adaptatif",
  fibonacci: "Fibonacci",
  ichimoku: "Ichimoku",
  adaptive_trend: "Adaptive Trend",
  multi_signal: "Multi-Signal",
  keltner_breakout: "Keltner Breakout",
  vwap_reversion: "VWAP Reversion",
  momentum_rotation: "Momentum Rotation",
  regime_cascade: "Regime Cascade",
  volatility_explosion: "Vol. Explosion",
  anti_consensus: "Anti-Consensus",
};

export default function Analyser() {
  const [regime, setRegime] = useState<RegimeSummary | null>(null);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<AnalysisResult | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [regimeFilter, setRegimeFilter] = useState("all");
  const [directionFilter, setDirectionFilter] = useState("all");
  const [strategyFilter, setStrategyFilter] = useState("all");
  const [sortBy, setSortBy] = useState("conviction_desc");

  // Stratégies uniques détectées
  const uniqueStrategies = useMemo(() => {
    const strats = new Set<string>();
    results.forEach((r) => { if (r.best_strategy?.name) strats.add(r.best_strategy.name); });
    return Array.from(strats).sort();
  }, [results]);

  // Compteurs par régime
  const regimeCounts = useMemo(() => {
    const counts: Record<string, number> = { all: results.length };
    results.forEach((r) => { counts[r.regime.regime] = (counts[r.regime.regime] || 0) + 1; });
    return counts;
  }, [results]);

  // Filtrage + tri
  const filteredResults = useMemo(() => {
    let filtered = results;

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter((r) =>
        r.symbol.toLowerCase().includes(q) ||
        r.name.toLowerCase().includes(q)
      );
    }

    if (regimeFilter !== "all") {
      filtered = filtered.filter((r) => r.regime.regime === regimeFilter);
    }

    if (directionFilter !== "all") {
      filtered = filtered.filter((r) => r.best_strategy?.direction === directionFilter);
    }

    if (strategyFilter !== "all") {
      filtered = filtered.filter((r) => r.best_strategy?.name === strategyFilter);
    }

    const sorted = [...filtered];
    if (sortBy === "conviction_desc") sorted.sort((a, b) => (b.best_strategy?.conviction || 0) - (a.best_strategy?.conviction || 0));
    else if (sortBy === "conviction_asc") sorted.sort((a, b) => (a.best_strategy?.conviction || 0) - (b.best_strategy?.conviction || 0));
    else if (sortBy === "name_asc") sorted.sort((a, b) => a.symbol.localeCompare(b.symbol));
    else if (sortBy === "regime") sorted.sort((a, b) => a.regime.regime.localeCompare(b.regime.regime));

    return sorted;
  }, [results, searchQuery, regimeFilter, directionFilter, strategyFilter, sortBy]);

  useEffect(() => {
    Promise.all([analyserApi.getRegime(), analyserApi.analyseAll()])
      .then(([regimeRes, analysisRes]) => {
        setRegime(regimeRes.data);
        setResults(analysisRes.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Analyseur de Stratégies</h2>
      <p className="text-text-secondary text-sm mb-6 max-w-3xl">
        Module 2 du pipeline — détection probabiliste du régime de marché et sélection adaptative parmi 15 stratégies (4 classiques + 3 avancées + 5 pro + 3 genius). Cliquez sur un actif pour voir le radar des stratégies et les détails de chaque signal.
      </p>

      {/* Régime de marché global */}
      {regime && (
        <div className="bg-card border border-border rounded-xl p-6 mb-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">
            Régime de marché dominant
          </h3>
          <div className="flex items-center gap-6 mb-4">
            <span
              className={`text-3xl font-bold ${REGIME_COLORS[regime.dominant_regime] || ""}`}
            >
              {REGIME_LABELS[regime.dominant_regime] || regime.dominant_regime}
            </span>
            <span className="text-text-secondary text-sm">
              {regime.total_assets} actifs analysés
            </span>
          </div>
          <div className="flex gap-4">
            {Object.entries(regime.distribution).map(([r, count]) => (
              <div key={r} className="text-center">
                <div className={`text-lg font-mono font-semibold ${REGIME_COLORS[r]}`}>
                  {count}
                </div>
                <div className="text-xs text-text-secondary">{REGIME_LABELS[r]}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filtres */}
      <div className="space-y-3 mb-6">
        {/* Recherche */}
        <div className="relative">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-secondary" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Rechercher un actif..."
            className="w-full bg-card border border-border rounded-xl pl-10 pr-4 py-2.5 text-sm font-mono focus:outline-none focus:border-gold/50 transition-colors"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary text-xs">✕</button>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {/* Filtre régime */}
          {["all", "BULL", "BEAR", "RANGE", "TRANSITION"].map((r) => (
            <button
              key={r}
              onClick={() => setRegimeFilter(r)}
              className={`text-[11px] px-3 py-1.5 rounded-lg border font-semibold transition-colors ${
                regimeFilter === r
                  ? r === "all" ? "text-gold bg-gold/10 border-gold/20"
                  : `${REGIME_COLORS[r]} ${REGIME_BG[r]}`
                  : "text-text-secondary border-border hover:text-text-primary"
              }`}
            >
              {r === "all" ? "Tous" : REGIME_LABELS[r]}
              <span className="ml-1.5 text-[10px] opacity-60">{regimeCounts[r] || 0}</span>
            </button>
          ))}

          <div className="w-px bg-border mx-1" />

          {/* Filtre direction */}
          {[
            { key: "all", label: "Toutes dir." },
            { key: "LONG", label: "LONG" },
            { key: "SHORT", label: "SHORT" },
            { key: "NEUTRAL", label: "NEUTRAL" },
          ].map((d) => (
            <button
              key={d.key}
              onClick={() => setDirectionFilter(d.key)}
              className={`text-[11px] px-3 py-1.5 rounded-lg border font-semibold transition-colors ${
                directionFilter === d.key
                  ? d.key === "LONG" ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/20"
                  : d.key === "SHORT" ? "text-red-400 bg-red-400/10 border-red-400/20"
                  : d.key === "NEUTRAL" ? "text-text-secondary bg-surface border-border"
                  : "text-gold bg-gold/10 border-gold/20"
                  : "text-text-secondary border-border hover:text-text-primary"
              }`}
            >
              {d.label}
            </button>
          ))}

          <div className="w-px bg-border mx-1" />

          {/* Filtre stratégie */}
          <select
            value={strategyFilter}
            onChange={(e) => setStrategyFilter(e.target.value)}
            className="text-[11px] px-2 py-1.5 rounded-lg border border-border bg-card text-text-secondary font-semibold cursor-pointer"
          >
            <option value="all">Toutes stratégies</option>
            {uniqueStrategies.map((s) => (
              <option key={s} value={s}>{STRATEGY_LABELS[s] || s}</option>
            ))}
          </select>

          {/* Tri */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="text-[11px] px-2 py-1.5 rounded-lg border border-border bg-card text-text-secondary font-semibold cursor-pointer"
          >
            <option value="conviction_desc">Conviction ↓</option>
            <option value="conviction_asc">Conviction ↑</option>
            <option value="name_asc">Nom A→Z</option>
            <option value="regime">Par régime</option>
          </select>
        </div>
      </div>

      {loading ? (
        <p className="text-text-secondary">Analyse en cours...</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Liste des résultats */}
          <div className="lg:col-span-2">
            <div className="text-xs text-text-secondary mb-2">
              {filteredResults.length} actifs{filteredResults.length !== results.length ? ` (filtré sur ${results.length})` : ""}
            </div>
            <div className="space-y-1 max-h-[700px] overflow-y-auto">
            {filteredResults.length === 0 ? (
              <p className="text-text-secondary text-sm text-center py-8">Aucun actif ne correspond à vos filtres</p>
            ) : filteredResults.map((r) => (
              <Link
                key={r.symbol}
                to={`/analyser/${r.symbol}`}
                onClick={() => setSelected(r)}
                className={`w-full flex items-center justify-between p-3 rounded-xl transition-colors text-left ${
                  selected?.symbol === r.symbol
                    ? "bg-gold/10 border border-gold/20"
                    : "bg-card border border-border hover:bg-surface"
                }`}
              >
                <div className="flex items-center gap-4">
                  <Link to={`/asset/${r.symbol}`} className="font-mono font-semibold text-gold w-20 hover:underline" onClick={(e) => e.stopPropagation()}>
                    {r.symbol}
                  </Link>
                  <div>
                    <span className="text-sm">{r.name}</span>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold ${REGIME_COLORS[r.regime.regime]} ${REGIME_BG[r.regime.regime]}`}>
                        {REGIME_LABELS[r.regime.regime]}
                      </span>
                      <span className="text-[10px] text-text-secondary font-mono">
                        {(r.regime.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  {r.best_strategy.name ? (
                    <>
                      <div className="flex items-center gap-2 justify-end">
                        <DirectionBadge direction={r.best_strategy.direction} />
                        <span className="text-[10px] text-text-secondary">
                          {STRATEGY_LABELS[r.best_strategy.name] || r.best_strategy.name}
                        </span>
                      </div>
                      <span className={`text-sm font-mono font-bold ${
                        r.best_strategy.conviction >= 65 ? "text-emerald-400" : r.best_strategy.conviction >= 50 ? "text-yellow-400" : "text-text-secondary"
                      }`}>
                        {r.best_strategy.conviction.toFixed(0)}
                      </span>
                    </>
                  ) : (
                    <span className="text-xs text-text-secondary">Aucun signal</span>
                  )}
                </div>
              </Link>
            ))}
            </div>
          </div>

          {/* Détail — panneau pro avec radar + onglets stratégies */}
          <div>
            {selected ? (
              <AnalyserDetail selected={selected} />

            ) : (
              <div className="bg-card border border-border rounded-xl p-6 text-center text-text-secondary text-sm">
                Sélectionnez un actif pour voir l'analyse complète
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════
// Panneau de détail pro — radar + onglets stratégies
// ═══════════════════════════════════════════

const STRAT_DESCRIPTIONS: Record<string, { type: string; edge: string }> = {
  trend_following: { type: "Classic", edge: "Croisement EMA 9/21 confirmé par SMA 50" },
  mean_reversion: { type: "Classic", edge: "Bollinger + RSI survendu/suracheté" },
  breakout: { type: "Classic", edge: "Cassure de range + volume" },
  momentum: { type: "Classic", edge: "RSI + MACD + Stochastic alignés" },
  mean_reversion_v2: { type: "Avancé", edge: "Z-Score + Stochastic + Keltner" },
  fibonacci: { type: "Avancé", edge: "Rebond sur 38.2% / 50% / 61.8%" },
  ichimoku: { type: "Avancé", edge: "Nuage Kumo + Tenkan/Kijun" },
  adaptive_trend: { type: "Pro", edge: "EMA dynamiques selon la volatilité" },
  multi_signal: { type: "Pro", edge: "4/6 indicateurs d'accord" },
  keltner_breakout: { type: "Pro", edge: "Canaux ATR adaptatifs" },
  vwap_reversion: { type: "Pro", edge: "Retour au VWAP institutionnel" },
  momentum_rotation: { type: "Pro", edge: "Classement relatif des 500 actifs" },
  regime_cascade: { type: "Genius", edge: "Changement de régime court vs moyen terme" },
  volatility_explosion: { type: "Genius", edge: "3+ signaux de compression simultanés" },
  anti_consensus: { type: "Genius", edge: "Contrarian sur euphorie/panique extrême" },
};

const TYPE_COLORS: Record<string, string> = {
  Classic: "text-text-secondary bg-surface border-border",
  "Avancé": "text-blue-400 bg-blue-400/10 border-blue-400/20",
  Pro: "text-purple-400 bg-purple-400/10 border-purple-400/20",
  Genius: "text-gold bg-gold/10 border-gold/20",
};

function AnalyserDetail({ selected }: { selected: any }) {
  const [expandedStrat, setExpandedStrat] = useState<string | null>(null);

  const strategies = selected.all_strategies || [];
  const activeStrats = strategies.filter((s: any) => s.direction !== "NEUTRAL" && s.conviction > 0);
  const sorted = [...activeStrats].sort((a: any, b: any) => (b.conviction || 0) - (a.conviction || 0));
  const top6 = sorted.slice(0, 6);

  // Radar data
  const radarData = strategies.map((s: any) => ({
    label: (STRATEGY_LABELS[s.strategy] || s.strategy).slice(0, 14),
    value: Math.max(s.conviction || 0, 8),
    icon: s.direction === "LONG" ? "📈" : s.direction === "SHORT" ? "📉" : "—",
  }));

  return (
    <div className="space-y-4 sticky top-6">
      {/* Header */}
      <div className="bg-card border border-border rounded-xl p-5">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h3 className="text-xl font-bold text-gold">{selected.symbol}</h3>
            <p className="text-xs text-text-secondary">{selected.name}</p>
          </div>
          <p className="text-2xl font-mono font-bold">${selected.last_close?.toFixed(2)}</p>
        </div>
        {/* Régime compact */}
        <div className="flex items-center gap-3 mt-2">
          <span className={`text-xs px-2 py-1 border rounded-lg font-bold ${REGIME_COLORS[selected.regime.regime]} ${REGIME_BG[selected.regime.regime]}`}>
            {REGIME_LABELS[selected.regime.regime]}
          </span>
          <span className="text-xs text-text-secondary font-mono">{(selected.regime.confidence * 100).toFixed(0)}% confiance</span>
          <Link to={`/asset/${selected.symbol}`} className="text-xs text-gold hover:underline ml-auto">Vue Scanner →</Link>
        </div>
      </div>

      {/* Radar des stratégies */}
      {radarData.length >= 3 && (
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold mb-2">Radar des {strategies.length} stratégies</p>
          <div className="flex justify-center">
            <RadarChart data={radarData} size={320} />
          </div>
        </div>
      )}

      {/* Top 6 stratégies — onglets cliquables */}
      {top6.length > 0 && (
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold mb-3">Top {top6.length} stratégies</p>
          <div className="space-y-2">
            {top6.map((s: any, i: number) => {
              const desc = STRAT_DESCRIPTIONS[s.strategy] || { type: "?", edge: "" };
              const typeColor = TYPE_COLORS[desc.type] || TYPE_COLORS.Classic;
              const isExpanded = expandedStrat === s.strategy;
              return (
                <div key={s.strategy}>
                  <button
                    onClick={() => setExpandedStrat(isExpanded ? null : s.strategy)}
                    className={`w-full flex items-center justify-between p-3 rounded-xl text-left transition-all ${isExpanded ? "bg-gold/5 border border-gold/20" : "bg-surface hover:bg-gold/5"}`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-gold">#{i + 1}</span>
                      <span className={`text-[8px] px-1 py-0.5 rounded font-bold border ${typeColor}`}>{desc.type}</span>
                      <span className="text-sm font-semibold">{STRATEGY_LABELS[s.strategy] || s.strategy}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <DirectionBadge direction={s.direction} small />
                      <span className="text-sm font-mono font-bold">{s.conviction?.toFixed(0)}</span>
                    </div>
                  </button>
                  {isExpanded && (
                    <div className="p-3 bg-surface rounded-b-xl border-x border-b border-gold/10 space-y-2">
                      <p className="text-xs text-text-secondary"><span className="text-text-primary font-semibold">Edge :</span> {desc.edge}</p>
                      {s.entry && (
                        <div className="grid grid-cols-4 gap-2 text-xs">
                          <div className="bg-card rounded-lg p-2 text-center">
                            <p className="text-[8px] text-text-secondary">Entrée</p>
                            <p className="font-mono font-bold">${s.entry?.toFixed(2)}</p>
                          </div>
                          <div className="bg-card rounded-lg p-2 text-center">
                            <p className="text-[8px] text-text-secondary">SL</p>
                            <p className="font-mono font-bold text-red-400">${s.stop_loss?.toFixed(2)}</p>
                          </div>
                          <div className="bg-card rounded-lg p-2 text-center">
                            <p className="text-[8px] text-text-secondary">TP</p>
                            <p className="font-mono font-bold text-gold">${s.take_profit?.toFixed(2)}</p>
                          </div>
                          <div className="bg-card rounded-lg p-2 text-center">
                            <p className="text-[8px] text-text-secondary">R:R</p>
                            <p className="font-mono font-bold">
                              {s.stop_loss && s.take_profit ? `1:${(Math.abs(s.take_profit - s.entry) / Math.abs(s.entry - s.stop_loss)).toFixed(1)}` : "—"}
                            </p>
                          </div>
                        </div>
                      )}
                      <p className="text-[10px] text-text-secondary italic">
                        {s.conviction >= 70 ? "Forte conviction — conditions réunies pour cette stratégie." :
                         s.conviction >= 50 ? "Conviction modérée — signal présent mais pas pleinement confirmé." :
                         "Faible conviction — conditions partiellement réunies."}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Stratégies inactives (NEUTRAL) */}
      {strategies.length > activeStrats.length && (
        <p className="text-[10px] text-text-secondary text-center">
          {strategies.length - activeStrats.length} stratégie{strategies.length - activeStrats.length > 1 ? "s" : ""} sans signal (NEUTRAL)
        </p>
      )}

      {/* Lien vers analyse complète */}
      <Link to={`/analyse?q=${selected.symbol}`} className="block bg-card border border-gold/20 rounded-xl p-3 text-center hover:bg-gold/5 transition-colors">
        <p className="text-gold font-semibold text-xs">Analyse Rapide {selected.symbol} →</p>
      </Link>
    </div>
  );
}


function DirectionBadge({ direction, small }: { direction: string; small?: boolean }) {
  const styles: Record<string, string> = {
    LONG: "text-gold bg-gold/10 border-gold/20",
    SHORT: "text-red-400 bg-red-400/10 border-red-400/20",
    NEUTRAL: "text-text-secondary bg-surface border-border",
  };

  return (
    <span
      className={`${small ? "text-[10px] px-1.5 py-0.5" : "text-xs px-2 py-0.5"} border rounded font-semibold ${styles[direction] || styles.NEUTRAL}`}
    >
      {direction}
    </span>
  );
}
