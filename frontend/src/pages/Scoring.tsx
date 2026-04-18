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
      <p className="text-text-secondary text-sm mb-6 max-w-3xl">
        Fusion de 8 sources en un score unique (0-100) — Scanner, Stratégie/Backtest, Régime Global, Fondamentaux, Catalyseurs, Corrélation Portefeuille, Rotation Sectorielle et Lead-Lag. Génère des thèses de trade complètes avec direction, entrée, SL, TP et sizing Kelly optimal. Score ≥65 = GO, 50-65 = WAIT, &lt;50 = NO_TRADE.
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
  const stratName = STRATEGY_LABELS[t.strategy] || t.strategy;
  const score = t.thesis_score;
  const rr = t.sizing?.risk_reward_ratio || 0;
  const wr = t.sizing?.win_rate_estimate ? t.sizing.win_rate_estimate * 100 : 0;
  const ev = t.sizing?.expected_value || 0;
  const kelly = t.sizing?.kelly_fraction ? t.sizing.kelly_fraction * 100 : 0;
  const slPct = t.entry && t.stop_loss ? Math.abs((t.stop_loss - t.entry) / t.entry * 100) : 0;
  const tp1Pct = t.entry && t.take_profit_1 ? Math.abs((t.take_profit_1 - t.entry) / t.entry * 100) : 0;
  const tp2Pct = t.entry && t.take_profit_2 ? Math.abs((t.take_profit_2 - t.entry) / t.entry * 100) : 0;
  const bayPost = t.bayesian?.posterior || 0;
  const sqc = t.sqc?.sqc || 0;

  // Verdict narratif
  const verdictParts: string[] = [];
  if (score >= 75) verdictParts.push(`Signal très fort (${score.toFixed(1)}/100) — convergence rare des 8 sources de scoring.`);
  else if (score >= 65) verdictParts.push(`Signal validé (${score.toFixed(1)}/100) — les conditions sont réunies pour un trade.`);
  else if (score >= 50) verdictParts.push(`Signal en attente (${score.toFixed(1)}/100) — presque prêt mais il manque de la conviction.`);
  else verdictParts.push(`Pas de signal (${score.toFixed(1)}/100) — les conditions ne sont pas favorables.`);

  if (t.direction === "LONG") verdictParts.push(`La stratégie ${stratName} détecte un potentiel haussier.`);
  else if (t.direction === "SHORT") verdictParts.push(`La stratégie ${stratName} détecte un potentiel baissier.`);

  if (ev > 0.1) verdictParts.push(`L'espérance mathématique est positive (+${ev.toFixed(3)}) — ce trade est statistiquement profitable à long terme.`);
  else if (ev > 0) verdictParts.push(`L'espérance est légèrement positive (+${ev.toFixed(3)}) — avantage faible mais réel.`);
  else verdictParts.push(`L'espérance est négative (${ev.toFixed(3)}) — ce trade n'est pas rentable mathématiquement.`);

  if (rr >= 2) verdictParts.push(`Excellent ratio risque/récompense de 1:${rr.toFixed(1)} — chaque dollar risqué peut rapporter ${rr.toFixed(1)}$.`);
  else if (rr >= 1.5) verdictParts.push(`Bon ratio R:R de 1:${rr.toFixed(1)}.`);
  else if (rr > 0) verdictParts.push(`R:R de 1:${rr.toFixed(1)} — correct mais pas exceptionnel.`);

  if (bayPost >= 70) verdictParts.push(`Le score bayésien (${bayPost.toFixed(0)}/100) confirme : l'historique ET les signaux actuels convergent.`);
  else if (bayPost >= 50) verdictParts.push(`Le bayésien (${bayPost.toFixed(0)}/100) est neutre — pas de conviction forte de l'historique.`);

  if (sqc >= 80) verdictParts.push(`Contexte de marché excellent (SQC ${sqc.toFixed(0)}) — bonne liquidité et timing favorable.`);
  else if (sqc < 50) verdictParts.push(`Attention : le contexte de marché est défavorable (SQC ${sqc.toFixed(0)}) — liquidité faible ou mauvais timing.`);

  return (
    <div className="bg-card border border-border rounded-xl p-6 space-y-5 sticky top-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-gold">{t.symbol}</h3>
          <p className="text-xs text-text-secondary">{t.name}</p>
        </div>
        <div className="text-right">
          <span className={`text-sm font-bold px-3 py-1.5 border rounded-lg ${ACTION_STYLES[t.action]}`}>
            {t.action === "GO" ? "SIGNAL GO" : t.action === "WAIT" ? "EN ATTENTE" : "PAS DE TRADE"}
          </span>
          <p className="text-lg font-mono font-semibold mt-1">${t.last_close.toFixed(2)}</p>
        </div>
      </div>

      {/* Score V2 — jauge visuelle */}
      <div className="bg-surface rounded-xl p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-text-secondary uppercase tracking-wider font-semibold">Score V2</span>
          <span className={`text-2xl font-mono font-bold ${score >= 65 ? "text-gold" : score >= 50 ? "text-yellow-400" : "text-text-secondary"}`}>
            {score.toFixed(1)}<span className="text-sm text-text-secondary">/100</span>
          </span>
        </div>
        <div className="h-3 bg-background rounded-full overflow-hidden relative">
          <div className="h-full rounded-full transition-all" style={{ width: `${score}%`, background: score >= 65 ? "linear-gradient(90deg, #B8960C, #D4AF37, #F5D060)" : score >= 50 ? "linear-gradient(90deg, #92400E, #F59E0B)" : "#555" }} />
          <div className="absolute top-0 h-full w-px bg-gold/50" style={{ left: "65%" }} title="Seuil GO (65)" />
        </div>
        <div className="flex justify-between mt-1 text-[9px] text-text-secondary">
          <span>0</span>
          <span className="text-gold">GO ≥ 65</span>
          <span>100</span>
        </div>
      </div>

      {/* Verdict narratif */}
      <div className="bg-surface border border-gold/10 rounded-xl p-4">
        <p className="text-xs text-gold font-semibold uppercase tracking-wider mb-2">Interprétation</p>
        <p className="text-sm text-text-secondary leading-relaxed">{verdictParts.join(" ")}</p>
      </div>

      {/* Direction + Stratégie */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-surface rounded-lg p-3 text-center">
          <p className="text-[9px] text-text-secondary uppercase mb-1">Direction</p>
          <DirectionBadge direction={t.direction} />
        </div>
        <div className="bg-surface rounded-lg p-3 text-center">
          <p className="text-[9px] text-text-secondary uppercase mb-1">Stratégie</p>
          <p className="text-sm font-semibold">{stratName}</p>
        </div>
      </div>

      {/* Niveaux de prix avec % */}
      <div>
        <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold mb-2">Plan de Trade</p>
        <div className="space-y-2">
          <PriceLevelBar label="Entrée" value={t.entry} pct={null} color="bg-white/20" />
          <PriceLevelBar label="Stop Loss" value={t.stop_loss} pct={-slPct} color="bg-red-500" />
          <PriceLevelBar label="TP1" value={t.take_profit_1} pct={tp1Pct} color="bg-gold" />
          <PriceLevelBar label="TP2" value={t.take_profit_2} pct={tp2Pct} color="bg-emerald-500" />
        </div>
        <p className="text-[10px] text-text-secondary mt-2 italic">
          Risque de {slPct.toFixed(1)}% pour un gain potentiel de {tp1Pct.toFixed(1)}% (TP1) à {tp2Pct.toFixed(1)}% (TP2).
          {rr >= 1.5 ? " Le ratio est favorable." : " Le ratio est serré — prudence sur le sizing."}
        </p>
      </div>

      {/* Score Bayésien — barres */}
      <div>
        <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold mb-2">Score Bayésien</p>
        <div className="space-y-2">
          <ScoreBar label="Prior (historique)" value={t.bayesian.prior} explain={t.bayesian.prior >= 65 ? "Historique favorable — l'actif performe bien" : t.bayesian.prior >= 45 ? "Historique neutre" : "Historique défavorable"} />
          <ScoreBar label="Likelihood (signaux actuels)" value={t.bayesian.likelihood} explain={t.bayesian.likelihood >= 65 ? "Signaux actuels convergents" : "Signaux faibles ou contradictoires"} />
          <ScoreBar label="Postérieur (fusion)" value={t.bayesian.posterior} highlight explain={bayPost >= 65 ? "Historique + signaux = conviction forte" : bayPost >= 50 ? "Conviction modérée" : "Pas de conviction"} />
        </div>
      </div>

      {/* SQC — Contexte */}
      <div>
        <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold mb-2">Qualité du Contexte (SQC)</p>
        <div className="space-y-2">
          <ScoreBar label="Liquidité" value={t.sqc.components.liquidity} explain={t.sqc.components.liquidity >= 80 ? "Volume élevé — exécution facile" : t.sqc.components.liquidity >= 50 ? "Volume correct" : "Volume faible — slippage probable"} />
          <ScoreBar label="Timing de marché" value={t.sqc.components.time} explain={t.sqc.components.time >= 70 ? "Heures de marché optimales" : t.sqc.components.time >= 40 ? "Timing acceptable" : "Hors marché ou heures creuses"} />
          <ScoreBar label="Volatilité" value={t.sqc.components.volatility_context} explain={t.sqc.components.volatility_context >= 70 ? "Volatilité normale — conditions stables" : t.sqc.components.volatility_context >= 40 ? "Volatilité modérée" : "Volatilité extrême — danger"} />
          <ScoreBar label="SQC Total" value={t.sqc.sqc} highlight explain={sqc >= 70 ? "Contexte favorable au trade" : sqc >= 50 ? "Contexte acceptable" : "Contexte défavorable — attendre"} />
        </div>
      </div>

      {/* Shelf Life */}
      <div className="bg-surface rounded-lg p-3">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[9px] text-text-secondary uppercase">Durée de vie du signal</p>
            <p className="text-sm font-mono font-semibold">{t.shelf_life.shelf_life_label}</p>
          </div>
          <div className="text-right">
            <p className="text-[9px] text-text-secondary uppercase">Type d'ordre</p>
            <p className="text-sm font-mono font-semibold text-gold">{t.shelf_life.order_type}</p>
          </div>
        </div>
        <p className="text-[10px] text-text-secondary mt-1 italic">
          {t.shelf_life.order_type === "MARKET" ? "Le signal est urgent — exécution immédiate recommandée." :
           "Le signal a le temps — un ordre Limit permet d'obtenir un meilleur prix d'entrée."}
        </p>
      </div>

      {/* Sizing Kelly — pro */}
      <div>
        <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold mb-2">Position Sizing (Kelly)</p>
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-surface rounded-lg p-3 text-center">
            <p className="text-[9px] text-text-secondary uppercase">Position</p>
            <p className="text-lg font-mono font-bold text-gold">${t.sizing.position_size_usd.toFixed(0)}</p>
            <p className="text-[9px] text-text-secondary">{t.sizing.quantity.toFixed(2)} unités</p>
          </div>
          <div className="bg-surface rounded-lg p-3 text-center">
            <p className="text-[9px] text-text-secondary uppercase">Risque max</p>
            <p className="text-lg font-mono font-bold text-red-400">${t.sizing.risk_per_trade_usd.toFixed(0)}</p>
            <p className="text-[9px] text-text-secondary">{t.sizing.risk_pct_of_capital.toFixed(2)}% du capital</p>
          </div>
        </div>
        <div className="grid grid-cols-4 gap-2 mt-2">
          <MiniMetric label="Kelly ¼" value={`${kelly.toFixed(1)}%`} />
          <MiniMetric label="R:R" value={`1:${rr.toFixed(1)}`} color={rr >= 1.5 ? "text-emerald-400" : ""} />
          <MiniMetric label="Win Rate" value={`${wr.toFixed(0)}%`} color={wr >= 55 ? "text-emerald-400" : ""} />
          <MiniMetric label="E[R]" value={ev >= 0 ? `+${ev.toFixed(3)}` : ev.toFixed(3)} color={ev > 0 ? "text-gold" : "text-red-400"} />
        </div>
        <p className="text-[10px] text-text-secondary mt-2 italic">
          {ev > 0
            ? `Pour chaque dollar risqué, l'espérance de gain est de ${(ev * 100).toFixed(1)} centimes. Avec un win rate de ${wr.toFixed(0)}% et un R:R de 1:${rr.toFixed(1)}, le critère de Kelly recommande ${kelly.toFixed(1)}% du capital.`
            : "L'espérance est négative — le sizing Kelly recommande de ne pas prendre ce trade."}
        </p>
      </div>
    </div>
  );
}

function PriceLevelBar({ label, value, pct, color }: { label: string; value: number | null; pct: number | null; color: string }) {
  if (value == null) return null;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-text-secondary w-14 text-right">{label}</span>
      <span className="font-mono font-semibold w-20">${value.toFixed(2)}</span>
      {pct !== null && (
        <span className={`font-mono text-[10px] ${pct >= 0 ? "text-gold" : "text-red-400"}`}>
          {pct >= 0 ? "+" : ""}{pct.toFixed(1)}%
        </span>
      )}
    </div>
  );
}

function ScoreBar({ label, value, highlight, explain }: { label: string; value: number; highlight?: boolean; explain?: string }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-0.5">
        <span className={`text-xs ${highlight ? "font-semibold text-text-primary" : "text-text-secondary"}`}>{label}</span>
        <span className={`text-xs font-mono ${highlight ? "text-gold font-bold" : ""}`}>{value.toFixed(1)}</span>
      </div>
      <div className="h-1.5 bg-background rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${highlight ? "bg-gold" : "bg-gold/40"}`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      {explain && <p className="text-[9px] text-text-secondary mt-0.5 italic">{explain}</p>}
    </div>
  );
}

function MiniMetric({ label, value, color = "" }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-surface rounded-lg p-2 text-center">
      <p className="text-[8px] text-text-secondary uppercase">{label}</p>
      <p className={`text-xs font-mono font-bold mt-0.5 ${color}`}>{value}</p>
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
