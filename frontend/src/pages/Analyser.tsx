import { useEffect, useState, useMemo } from "react";
import { Search, Link as LinkIcon } from "lucide-react";
import { Link } from "react-router-dom";
import { analyserApi, type AnalysisResult, type RegimeSummary } from "../services/api";

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
  microstructure: "Microstructure",
  cnn_pattern: "CNN Pattern",
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
        Détection probabiliste du régime de marché et sélection adaptative parmi 12+ stratégies — Trend Following, Mean Reversion, Breakout, Momentum, Fibonacci, Ichimoku. La matrice performance régime×stratégie se met à jour automatiquement. Les stratégies en perte d'edge sont détectées et mises en quarantaine.
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
              <button
                key={r.symbol}
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
              </button>
            ))}
            </div>
          </div>

          {/* Détail */}
          <div>
            {selected ? (
              <div className="bg-card border border-border rounded-xl p-6 space-y-6 sticky top-6">
                <div>
                  <h3 className="text-lg font-bold text-gold">{selected.symbol}</h3>
                  <p className="text-sm text-text-secondary">{selected.name}</p>
                  <p className="text-2xl font-mono font-semibold mt-2">
                    ${selected.last_close.toFixed(2)}
                  </p>
                </div>

                {/* Régime */}
                <div>
                  <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-3">
                    Régime détecté
                  </h4>
                  <div className="space-y-2">
                    {Object.entries(selected.regime.probabilities)
                      .sort(([, a], [, b]) => b - a)
                      .map(([r, prob]) => (
                        <div key={r}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className={REGIME_COLORS[r]}>
                              {REGIME_LABELS[r]}
                            </span>
                            <span className="font-mono">
                              {(prob * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gold rounded-full"
                              style={{ width: `${prob * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Meilleure stratégie */}
                {selected.best_strategy.name && (
                  <div>
                    <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-3">
                      Stratégie recommandée
                    </h4>
                    <div className="bg-surface rounded-lg p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold">
                          {STRATEGY_LABELS[selected.best_strategy.name]}
                        </span>
                        <DirectionBadge direction={selected.best_strategy.direction} />
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-text-secondary">Entrée</span>
                          <p className="font-mono">${selected.best_strategy.entry?.toFixed(2)}</p>
                        </div>
                        <div>
                          <span className="text-text-secondary">Conviction</span>
                          <p className="font-mono">{selected.best_strategy.conviction.toFixed(0)}/100</p>
                        </div>
                        <div>
                          <span className="text-text-secondary">Stop Loss</span>
                          <p className="font-mono text-red-400">
                            ${selected.best_strategy.stop_loss?.toFixed(2)}
                          </p>
                        </div>
                        <div>
                          <span className="text-text-secondary">Take Profit</span>
                          <p className="font-mono text-gold">
                            ${selected.best_strategy.take_profit?.toFixed(2)}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Toutes les stratégies */}
                <div>
                  <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-3">
                    Toutes les stratégies
                  </h4>
                  <div className="space-y-2">
                    {selected.all_strategies.map((s) => (
                      <div
                        key={s.strategy}
                        className="flex items-center justify-between text-sm"
                      >
                        <div className="flex items-center gap-2">
                          <DirectionBadge direction={s.direction} small />
                          <span>
                            {STRATEGY_LABELS[s.strategy] || s.strategy}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-text-secondary">
                            w:{(s.weight * 100).toFixed(0)}%
                          </span>
                          <span className="font-mono w-8 text-right">
                            {s.conviction.toFixed(0)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
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
