import { useEffect, useState } from "react";
import { scoringApi, type TradeThesis } from "../services/api";

const ACTION_STYLES: Record<string, string> = {
  GO: "text-gold bg-gold/10 border-gold/20",
  WAIT: "text-yellow-400 bg-yellow-400/10 border-yellow-400/20",
  NO_TRADE: "text-text-secondary bg-surface border-border",
};

const STRATEGY_LABELS: Record<string, string> = {
  trend_following: "Trend Following",
  mean_reversion: "Mean Reversion",
  breakout: "Breakout",
  momentum: "Momentum Adaptatif",
};

export default function Scoring() {
  const [theses, setTheses] = useState<TradeThesis[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<TradeThesis | null>(null);

  useEffect(() => {
    scoringApi
      .getAllTheses()
      .then((res) => setTheses(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const goCount = theses.filter((t) => t.action === "GO").length;
  const waitCount = theses.filter((t) => t.action === "WAIT").length;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Moteur de Scoring</h2>
      <p className="text-text-secondary mb-6 text-sm">
        Thèses de Trade — Score Bayésien + Qualité du Contexte + Sizing Kelly
      </p>

      {/* Métriques */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary mb-1">Signaux GO</p>
          <p className="text-2xl font-mono font-semibold text-gold">
            {loading ? "..." : goCount}
          </p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary mb-1">En attente</p>
          <p className="text-2xl font-mono font-semibold text-yellow-400">
            {loading ? "..." : waitCount}
          </p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary mb-1">Total analysé</p>
          <p className="text-2xl font-mono font-semibold">{loading ? "..." : theses.length}</p>
        </div>
      </div>

      {loading ? (
        <p className="text-text-secondary">Calcul des thèses en cours...</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Liste */}
          <div className="lg:col-span-2 space-y-2">
            {theses.map((t) => (
              <button
                key={t.symbol}
                onClick={() => setSelected(t)}
                className={`w-full flex items-center justify-between p-4 rounded-xl transition-colors text-left ${
                  selected?.symbol === t.symbol
                    ? "bg-gold/10 border border-gold/20"
                    : "bg-card border border-border hover:bg-surface"
                }`}
              >
                <div className="flex items-center gap-4">
                  <span
                    className={`text-[10px] font-bold px-2 py-1 border rounded ${ACTION_STYLES[t.action]}`}
                  >
                    {t.action}
                  </span>
                  <div>
                    <span className="font-mono font-semibold text-gold">{t.symbol}</span>
                    <span className="text-sm text-text-secondary ml-2">{t.name}</span>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  {t.action !== "NO_TRADE" && (
                    <>
                      <DirectionBadge direction={t.direction} />
                      <span className="font-mono">{t.thesis_score.toFixed(1)}</span>
                    </>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Détail thèse */}
          <div>
            {selected && selected.action !== "NO_TRADE" ? (
              <ThesisDetail thesis={selected} />
            ) : selected ? (
              <div className="bg-card border border-border rounded-xl p-6">
                <h3 className="text-lg font-bold text-gold mb-2">{selected.symbol}</h3>
                <p className="text-text-secondary text-sm">
                  {selected.reason || "Aucun signal directionnel détecté"}
                </p>
              </div>
            ) : (
              <div className="bg-card border border-border rounded-xl p-6 text-center text-text-secondary text-sm">
                Sélectionnez un actif pour voir la thèse de trade
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function ThesisDetail({ thesis: t }: { thesis: TradeThesis }) {
  return (
    <div className="bg-card border border-border rounded-xl p-6 space-y-5 sticky top-6">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-gold">{t.symbol}</h3>
          <span
            className={`text-xs font-bold px-2 py-1 border rounded ${ACTION_STYLES[t.action]}`}
          >
            {t.action}
          </span>
        </div>
        <p className="text-sm text-text-secondary">{t.name}</p>
        <p className="text-2xl font-mono font-semibold mt-1">${t.last_close.toFixed(2)}</p>
      </div>

      {/* Thesis Score */}
      <div className="bg-surface rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-semibold">Score Thèse</span>
          <span className="text-xl font-mono font-bold text-gold">
            {t.thesis_score.toFixed(1)}
          </span>
        </div>
        <div className="h-2 bg-background rounded-full overflow-hidden">
          <div
            className="h-full bg-gold rounded-full"
            style={{ width: `${t.thesis_score}%` }}
          />
        </div>
      </div>

      {/* Direction + Stratégie */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <span className="text-xs text-text-secondary">Direction</span>
          <div className="mt-1">
            <DirectionBadge direction={t.direction} />
          </div>
        </div>
        <div>
          <span className="text-xs text-text-secondary">Stratégie</span>
          <p className="text-sm font-semibold mt-1">
            {STRATEGY_LABELS[t.strategy] || t.strategy}
          </p>
        </div>
      </div>

      {/* Prix */}
      <div>
        <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
          Niveaux
        </h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <PriceRow label="Entrée" value={t.entry} />
          <PriceRow label="Stop Loss" value={t.stop_loss} color="text-red-400" />
          <PriceRow label="TP1" value={t.take_profit_1} color="text-gold" />
          <PriceRow label="TP2" value={t.take_profit_2} color="text-gold" />
        </div>
      </div>

      {/* Bayesian */}
      <div>
        <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
          Score Bayésien
        </h4>
        <div className="space-y-1 text-sm">
          <ScoreRow label="Prior (historique)" value={t.bayesian.prior} />
          <ScoreRow label="Likelihood (actuel)" value={t.bayesian.likelihood} />
          <ScoreRow label="Postérieur" value={t.bayesian.posterior} highlight />
        </div>
      </div>

      {/* SQC */}
      <div>
        <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
          Qualité du Contexte
        </h4>
        <div className="space-y-1 text-sm">
          <ScoreRow label="Liquidité" value={t.sqc.components.liquidity} />
          <ScoreRow label="Timing" value={t.sqc.components.time} />
          <ScoreRow label="Volatilité" value={t.sqc.components.volatility_context} />
          <ScoreRow label="SQC Total" value={t.sqc.sqc} highlight />
        </div>
      </div>

      {/* Shelf Life */}
      <div>
        <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
          Signal Shelf Life
        </h4>
        <div className="text-sm space-y-1">
          <div className="flex justify-between">
            <span className="text-text-secondary">Durée de vie</span>
            <span className="font-mono">{t.shelf_life.shelf_life_label}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-secondary">Type d'ordre</span>
            <span className="font-mono text-gold">{t.shelf_life.order_type}</span>
          </div>
        </div>
      </div>

      {/* Sizing Kelly */}
      <div>
        <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
          Position Sizing (Kelly)
        </h4>
        <div className="bg-surface rounded-lg p-3 space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-text-secondary">Kelly fraction</span>
            <span className="font-mono">{(t.sizing.kelly_fraction * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-secondary">Taille position</span>
            <span className="font-mono font-semibold text-gold">
              ${t.sizing.position_size_usd.toFixed(0)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-secondary">Quantité</span>
            <span className="font-mono">{t.sizing.quantity.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-secondary">Risque</span>
            <span className="font-mono text-red-400">
              ${t.sizing.risk_per_trade_usd.toFixed(0)} ({t.sizing.risk_pct_of_capital.toFixed(2)}%)
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-secondary">R:R</span>
            <span className="font-mono">{t.sizing.risk_reward_ratio.toFixed(1)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-secondary">Win rate est.</span>
            <span className="font-mono">{(t.sizing.win_rate_estimate * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-secondary">Expected Value</span>
            <span className="font-mono text-gold">{t.sizing.expected_value.toFixed(3)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function DirectionBadge({ direction }: { direction: string }) {
  const styles: Record<string, string> = {
    LONG: "text-gold bg-gold/10 border-gold/20",
    SHORT: "text-red-400 bg-red-400/10 border-red-400/20",
    NEUTRAL: "text-text-secondary bg-surface border-border",
  };
  return (
    <span
      className={`text-xs px-2 py-0.5 border rounded font-semibold ${styles[direction] || styles.NEUTRAL}`}
    >
      {direction}
    </span>
  );
}

function PriceRow({
  label,
  value,
  color,
}: {
  label: string;
  value: number | null;
  color?: string;
}) {
  return (
    <div>
      <span className="text-text-secondary text-xs">{label}</span>
      <p className={`font-mono ${color || ""}`}>
        {value != null ? `$${value.toFixed(2)}` : "—"}
      </p>
    </div>
  );
}

function ScoreRow({
  label,
  value,
  highlight,
}: {
  label: string;
  value: number;
  highlight?: boolean;
}) {
  return (
    <div className="flex justify-between">
      <span className={highlight ? "font-semibold" : "text-text-secondary"}>{label}</span>
      <span className={`font-mono ${highlight ? "text-gold font-semibold" : ""}`}>
        {value.toFixed(1)}
      </span>
    </div>
  );
}
