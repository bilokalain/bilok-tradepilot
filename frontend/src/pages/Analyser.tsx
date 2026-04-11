import { useEffect, useState } from "react";
import { analyserApi, type AnalysisResult, type RegimeSummary } from "../services/api";

const REGIME_COLORS: Record<string, string> = {
  BULL: "text-gold",
  BEAR: "text-red-400",
  RANGE: "text-blue-400",
  CRISIS: "text-red-600",
  TRANSITION: "text-yellow-400",
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
  breakout: "Breakout",
  momentum: "Momentum Adaptatif",
  microstructure: "Microstructure",
  cnn_pattern: "CNN Pattern",
};

export default function Analyser() {
  const [regime, setRegime] = useState<RegimeSummary | null>(null);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<AnalysisResult | null>(null);

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
      <h2 className="text-2xl font-bold mb-6">Analyseur de Stratégies</h2>

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

      {loading ? (
        <p className="text-text-secondary">Analyse en cours...</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Liste des résultats */}
          <div className="lg:col-span-2 space-y-2">
            {results.map((r) => (
              <button
                key={r.symbol}
                onClick={() => setSelected(r)}
                className={`w-full flex items-center justify-between p-4 rounded-xl transition-colors text-left ${
                  selected?.symbol === r.symbol
                    ? "bg-gold/10 border border-gold/20"
                    : "bg-card border border-border hover:bg-surface"
                }`}
              >
                <div className="flex items-center gap-4">
                  <span className="font-mono font-semibold text-gold w-20">
                    {r.symbol}
                  </span>
                  <div>
                    <span className="text-sm">{r.name}</span>
                    <div className="flex items-center gap-2 mt-1">
                      <span
                        className={`text-xs font-semibold ${REGIME_COLORS[r.regime.regime]}`}
                      >
                        {REGIME_LABELS[r.regime.regime]}
                      </span>
                      <span className="text-xs text-text-secondary">
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
                        <span className="text-xs text-text-secondary">
                          {STRATEGY_LABELS[r.best_strategy.name] || r.best_strategy.name}
                        </span>
                      </div>
                      <span className="text-sm font-mono">
                        Conviction : {r.best_strategy.conviction.toFixed(0)}
                      </span>
                    </>
                  ) : (
                    <span className="text-xs text-text-secondary">Aucun signal</span>
                  )}
                </div>
              </button>
            ))}
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
