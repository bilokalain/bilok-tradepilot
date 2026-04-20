import { useEffect, useState } from "react";
import { Search, Target, TrendingUp, Shield, Clock } from "lucide-react";
import { Link } from "react-router-dom";
import { scoringApi, type TradeThesis } from "../services/api";
import ScoreGauge from "../components/ui/ScoreGauge";

const ACTION_STYLES: Record<string, string> = {
  GO: "text-gold bg-gold/10 border-gold/20",
  WAIT: "text-yellow-400 bg-yellow-400/10 border-yellow-400/20",
  NO_TRADE: "text-text-secondary bg-surface border-border",
};

const STRATEGY_LABELS: Record<string, string> = {
  trend_following: "Trend Following", mean_reversion: "Mean Reversion", breakout: "Breakout",
  momentum: "Momentum Adaptatif", mean_reversion_v2: "Mean Rev. V2", fibonacci: "Fibonacci",
  ichimoku: "Ichimoku", adaptive_trend: "Adaptive Trend", multi_signal: "Multi-Signal",
  keltner_breakout: "Keltner Breakout", vwap_reversion: "VWAP Reversion",
  momentum_rotation: "Mom. Rotation", regime_cascade: "Regime Cascade",
  volatility_explosion: "Vol. Explosion", anti_consensus: "Anti-Consensus",
};

export default function Scoring() {
  const [theses, setTheses] = useState<TradeThesis[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<TradeThesis | null>(null);
  const [tab, setTab] = useState<"GO" | "WAIT" | "NO_TRADE">("GO");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    scoringApi
      .getAllTheses()
      .then((res) => setTheses(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const goTheses = theses.filter((t) => t.action === "GO");
  const waitTheses = theses.filter((t) => t.action === "WAIT");
  const noTradeTheses = theses.filter((t) => t.action === "NO_TRADE");

  const filteredTheses = (tab === "GO" ? goTheses : tab === "WAIT" ? waitTheses : noTradeTheses)
    .filter((t) => !searchQuery || t.symbol.toLowerCase().includes(searchQuery.toLowerCase()) || t.name?.toLowerCase().includes(searchQuery.toLowerCase()))
    .sort((a, b) => (b.thesis_score || 0) - (a.thesis_score || 0));

  // KPIs
  const avgScore = goTheses.length > 0 ? goTheses.reduce((s, t) => s + (t.thesis_score || 0), 0) / goTheses.length : 0;
  const bestGo = goTheses.length > 0 ? goTheses.reduce((best, t) => (t.thesis_score || 0) > (best.thesis_score || 0) ? t : best, goTheses[0]) : null;
  const avgRR = goTheses.filter((t) => t.sizing?.risk_reward_ratio > 0).length > 0
    ? goTheses.filter((t) => t.sizing?.risk_reward_ratio > 0).reduce((s, t) => s + t.sizing.risk_reward_ratio, 0) / goTheses.filter((t) => t.sizing?.risk_reward_ratio > 0).length : 0;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Moteur de Scoring</h2>
      <p className="text-text-secondary text-sm mb-6 max-w-3xl">
        Module 3 du pipeline — fusionne 9 composantes en un score unique (0-100). Génère des thèses de trade complètes avec direction, entrée, SL, TP1/TP2, sizing Kelly et espérance mathématique.
      </p>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        <div className="bg-card border border-gold/20 rounded-xl p-4">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider">Signaux GO</p>
          <p className="text-3xl font-mono font-bold text-gold mt-1">{loading ? "..." : goTheses.length}</p>
          <p className="text-[10px] text-text-secondary">Score ≥ 65</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider">En attente</p>
          <p className="text-3xl font-mono font-bold text-yellow-400 mt-1">{loading ? "..." : waitTheses.length}</p>
          <p className="text-[10px] text-text-secondary">Score 50-64</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider">Score GO moyen</p>
          <p className="text-2xl font-mono font-bold mt-1">{avgScore.toFixed(1)}</p>
          <p className="text-[10px] text-text-secondary">/100</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider">R:R moyen</p>
          <p className="text-2xl font-mono font-bold text-gold mt-1">1:{avgRR.toFixed(1)}</p>
          <p className="text-[10px] text-text-secondary">Risque/Récompense</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider">Meilleur GO</p>
          <p className="text-lg font-mono font-bold text-gold mt-1">{bestGo?.symbol || "—"}</p>
          <p className="text-[10px] text-text-secondary">{bestGo ? `${bestGo.thesis_score?.toFixed(1)}/100` : ""}</p>
        </div>
      </div>

      {/* Onglets + Recherche */}
      <div className="flex items-center gap-3 mb-4">
        {([
          { key: "GO" as const, label: "GO", count: goTheses.length, color: "text-gold bg-gold/10 border-gold/20" },
          { key: "WAIT" as const, label: "ATTENTE", count: waitTheses.length, color: "text-yellow-400 bg-yellow-400/10 border-yellow-400/20" },
          { key: "NO_TRADE" as const, label: "PAS DE TRADE", count: noTradeTheses.length, color: "text-text-secondary bg-surface border-border" },
        ]).map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`text-xs px-3 py-2 rounded-lg border font-semibold transition-colors ${tab === t.key ? t.color : "text-text-secondary border-border hover:text-text-primary"}`}>
            {t.label} <span className="ml-1 opacity-60">{t.count}</span>
          </button>
        ))}
        <div className="flex-1" />
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
          <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Rechercher..." className="bg-card border border-border rounded-lg pl-8 pr-3 py-1.5 text-xs w-48 focus:outline-none focus:border-gold/50" />
        </div>
      </div>

      {loading ? (
        <p className="text-text-secondary">Calcul des thèses en cours...</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Liste */}
          <div className="lg:col-span-2">
            <p className="text-[10px] text-text-secondary mb-2">{filteredTheses.length} thèses</p>
            <div className="space-y-1.5 max-h-[700px] overflow-y-auto">
              {filteredTheses.length === 0 ? (
                <p className="text-text-secondary text-sm text-center py-8">Aucune thèse dans cette catégorie</p>
              ) : filteredTheses.map((t) => (
                <button key={t.symbol} onClick={() => setSelected(t)}
                  className={`w-full flex items-center justify-between p-3.5 rounded-xl transition-colors text-left ${
                    selected?.symbol === t.symbol ? "bg-gold/10 border border-gold/20" : "bg-card border border-border hover:bg-surface"
                  }`}>
                  <div className="flex items-center gap-3">
                    <span className={`text-[10px] font-bold px-2 py-1 border rounded ${ACTION_STYLES[t.action]}`}>{t.action}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-semibold text-gold">{t.symbol}</span>
                        {t.action !== "NO_TRADE" && <DirectionBadge direction={t.direction} />}
                      </div>
                      <span className="text-[10px] text-text-secondary">{t.name}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    {t.action !== "NO_TRADE" && (
                      <>
                        <span className="text-[10px] text-text-secondary">{STRATEGY_LABELS[t.strategy] || t.strategy}</span>
                        <span className={`font-mono font-bold ${t.thesis_score >= 70 ? "text-gold" : t.thesis_score >= 65 ? "text-emerald-400" : ""}`}>
                          {t.thesis_score?.toFixed(1)}
                        </span>
                      </>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Détail thèse */}
          <div>
            {selected && selected.action !== "NO_TRADE" ? (
              <ThesisDetail thesis={selected} />
            ) : selected ? (
              <div className="bg-card border border-border rounded-xl p-6">
                <h3 className="text-lg font-bold text-gold mb-2">{selected.symbol}</h3>
                <p className="text-text-secondary text-sm">{selected.reason || "Aucun signal directionnel détecté"}</p>
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


// ═══════════════════════════════════════════
// Détail d'une thèse — version ultra-pro
// ═══════════════════════════════════════════

function ThesisDetail({ thesis: t }: { thesis: TradeThesis }) {
  const stratName = STRATEGY_LABELS[t.strategy] || t.strategy;
  const score = t.thesis_score || (t as any).score_v2 || 0;
  const rr = t.sizing?.risk_reward_ratio || 0;
  const wr = t.sizing?.win_rate_estimate ? t.sizing.win_rate_estimate * 100 : 0;
  const ev = t.sizing?.expected_value || 0;
  const kelly = t.sizing?.kelly_fraction ? t.sizing.kelly_fraction * 100 : 0;

  const bayPost = t.bayesian?.posterior || 0;
  const sqc = t.sqc?.sqc || 0;

  // Verdict narratif complet
  const parts: string[] = [];
  if (score >= 75) parts.push(`Signal très fort (${score.toFixed(1)}/100) — convergence rare des 9 sources de scoring. Les conditions sont exceptionnellement favorables.`);
  else if (score >= 65) parts.push(`Signal validé (${score.toFixed(1)}/100) — les critères convergent suffisamment pour justifier une entrée en position.`);
  else if (score >= 50) parts.push(`Signal en attente (${score.toFixed(1)}/100) — presque prêt mais il manque de la conviction. Surveiller l'évolution.`);
  else parts.push(`Pas de signal (${score.toFixed(1)}/100) — les conditions ne sont pas favorables.`);

  if (t.direction === "LONG") parts.push(`La stratégie ${stratName} détecte un potentiel haussier sur ${t.symbol}.`);
  else if (t.direction === "SHORT") parts.push(`La stratégie ${stratName} détecte un potentiel baissier sur ${t.symbol}.`);

  if (ev > 0.1) parts.push(`L'espérance mathématique est positive (+${ev.toFixed(3)}) — pour chaque dollar risqué, le gain moyen attendu est de ${(ev * 100).toFixed(1)} centimes.`);
  else if (ev > 0) parts.push(`L'espérance est légèrement positive (+${ev.toFixed(3)}) — avantage faible mais réel.`);
  else if (ev <= 0 && t.action === "GO") parts.push(`Attention : l'espérance est négative (${ev.toFixed(3)}) — le R:R devrait être amélioré.`);

  if (rr >= 2) parts.push(`Excellent ratio risque/récompense de 1:${rr.toFixed(1)} — chaque dollar risqué peut rapporter ${rr.toFixed(1)}$.`);
  else if (rr >= 1.5) parts.push(`Bon ratio R:R de 1:${rr.toFixed(1)}.`);

  if (bayPost >= 70) parts.push(`Le score bayésien (${bayPost.toFixed(0)}/100) confirme : l'historique ET les signaux actuels convergent.`);
  else if (bayPost < 40 && bayPost > 0) parts.push(`Le bayésien est faible (${bayPost.toFixed(0)}/100) — l'historique ne soutient pas fortement ce signal.`);

  if (sqc >= 80) parts.push(`Contexte de marché excellent (SQC ${sqc.toFixed(0)}) — bonne liquidité et timing favorable.`);
  else if (sqc < 50 && sqc > 0) parts.push(`Attention : contexte défavorable (SQC ${sqc.toFixed(0)}) — liquidité faible ou mauvais timing.`);

  return (
    <div className="bg-card border border-border rounded-xl p-5 space-y-4 sticky top-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-gold">{t.symbol}</h3>
          <p className="text-xs text-text-secondary">{t.name}</p>
        </div>
        <div className="text-right">
          <span className={`text-sm font-bold px-3 py-1.5 border rounded-lg ${ACTION_STYLES[t.action]}`}>
            {t.action === "GO" ? "SIGNAL GO" : "EN ATTENTE"}
          </span>
          <p className="text-lg font-mono font-semibold mt-1">${t.last_close?.toFixed(2)}</p>
        </div>
      </div>

      {/* Score V2 jauge */}
      <div className="flex items-center gap-4">
        <ScoreGauge score={score} size={80} sublabel="/100" />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <DirectionBadge direction={t.direction} />
            <span className="text-sm font-semibold">{stratName}</span>
          </div>
          <p className="text-[10px] text-text-secondary">{parts.join(" ")}</p>
        </div>
      </div>

      {/* Niveaux de prix */}
      {t.entry && t.stop_loss && (
        <div className="bg-surface rounded-xl p-4 space-y-2">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider font-semibold">Plan de trade</p>
          <PriceRow label="Entrée" price={t.entry} description="Prix recommandé" />
          <PriceRow label="Stop Loss" price={t.stop_loss} color="text-red-400" description="Protection automatique" />
          <PriceRow label="TP1" price={t.take_profit_1} color="text-gold" description="Premier objectif" />
          <PriceRow label="TP2" price={t.take_profit_2} color="text-emerald-400" description="Objectif optimiste" />
          {rr > 0 && (
            <div className="pt-2 border-t border-border/50 flex justify-between text-xs">
              <span className="text-text-secondary">R:R</span>
              <span className="font-mono font-bold text-gold">1:{rr.toFixed(1)}</span>
            </div>
          )}
        </div>
      )}

      {/* Bayesian */}
      {t.bayesian && (
        <div className="bg-surface rounded-xl p-4 space-y-2">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider font-semibold">Score Bayésien</p>
          <p className="text-[10px] text-text-secondary italic">Combine l'historique de l'actif (prior) avec les signaux actuels (likelihood) pour estimer la probabilité de succès.</p>
          <ScoreBar label="Prior (historique)" value={t.bayesian.prior}
            explain={t.bayesian.prior >= 65 ? "Historique favorable — l'actif performe bien sur 6 mois" : t.bayesian.prior >= 45 ? "Historique neutre" : "Historique défavorable — prudence"} />
          <ScoreBar label="Likelihood (signaux actuels)" value={t.bayesian.likelihood}
            explain={t.bayesian.likelihood >= 65 ? "Signaux actuels convergents — scanner + stratégie + régime" : "Signaux faibles ou contradictoires"} />
          <ScoreBar label="Postérieur (fusion)" value={t.bayesian.posterior} highlight
            explain={t.bayesian.posterior >= 70 ? "Forte conviction — historique ET signaux convergent" : t.bayesian.posterior >= 50 ? "Conviction modérée" : "Pas de conviction bayésienne"} />
        </div>
      )}

      {/* SQC */}
      {t.sqc && (
        <div className="bg-surface rounded-xl p-4 space-y-2">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider font-semibold">Qualité du Contexte (SQC)</p>
          <p className="text-[10px] text-text-secondary italic">Les conditions de marché sont-elles favorables pour entrer ? Un bon signal dans un mauvais contexte = mauvais trade.</p>
          <ScoreBar label="Liquidité" value={t.sqc.components?.liquidity || 0}
            explain={(t.sqc.components?.liquidity || 0) >= 80 ? "Volume élevé — exécution facile, spread serré" : (t.sqc.components?.liquidity || 0) >= 50 ? "Volume correct" : "Volume faible — risque de slippage"} />
          <ScoreBar label="Timing de marché" value={t.sqc.components?.time || 0}
            explain={(t.sqc.components?.time || 0) >= 70 ? "Heures de marché optimales" : (t.sqc.components?.time || 0) >= 40 ? "Timing acceptable" : "Hors marché ou heures creuses"} />
          <ScoreBar label="Volatilité" value={t.sqc.components?.volatility_context || 0}
            explain={(t.sqc.components?.volatility_context || 0) >= 70 ? "Volatilité normale — conditions stables" : (t.sqc.components?.volatility_context || 0) >= 40 ? "Volatilité modérée" : "Volatilité extrême — danger"} />
          <ScoreBar label="SQC Total" value={t.sqc.sqc || 0} highlight
            explain={(t.sqc.sqc || 0) >= 70 ? "Contexte favorable au trade" : (t.sqc.sqc || 0) >= 50 ? "Contexte acceptable" : "Contexte défavorable — attendre"} />
        </div>
      )}

      {/* Sizing Kelly */}
      {t.sizing && (
        <div className="bg-surface rounded-xl p-4 space-y-3">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider font-semibold">Position Sizing (Kelly)</p>
          <p className="text-[10px] text-text-secondary italic">Taille de position optimale basée sur le critère de Kelly — maximise la croissance du capital à long terme.</p>
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-card rounded-lg p-3 text-center">
              <p className="text-[9px] text-text-secondary">Position recommandée</p>
              <p className="text-lg font-mono font-bold text-gold">${t.sizing.position_size_usd?.toFixed(0)}</p>
              <p className="text-[9px] text-text-secondary">{t.sizing.quantity?.toFixed(2)} unités</p>
            </div>
            <div className="bg-card rounded-lg p-3 text-center">
              <p className="text-[9px] text-text-secondary">Risque maximum</p>
              <p className="text-lg font-mono font-bold text-red-400">${t.sizing.risk_per_trade_usd?.toFixed(0)}</p>
              <p className="text-[9px] text-text-secondary">{t.sizing.risk_pct_of_capital?.toFixed(2)}% du capital</p>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-1.5">
            <MiniMetric label="Kelly ¼" value={`${kelly.toFixed(1)}%`} />
            <MiniMetric label="R:R" value={`1:${rr.toFixed(1)}`} color={rr >= 1.5 ? "text-emerald-400" : ""} />
            <MiniMetric label="Win Rate" value={`${wr.toFixed(0)}%`} color={wr >= 55 ? "text-emerald-400" : ""} />
            <MiniMetric label="E[R]" value={ev >= 0 ? `+${ev.toFixed(3)}` : ev.toFixed(3)} color={ev > 0 ? "text-gold" : "text-red-400"} />
          </div>
          <p className="text-[9px] text-text-secondary italic">
            {ev > 0
              ? `Pour chaque dollar risqué, l'espérance de gain est de ${(ev * 100).toFixed(1)} centimes. Avec un win rate de ${wr.toFixed(0)}% et un R:R de 1:${rr.toFixed(1)}, le critère de Kelly recommande ${kelly.toFixed(1)}% du capital.`
              : "L'espérance est négative — le sizing Kelly recommande de ne pas prendre ce trade."}
          </p>
        </div>
      )}

      {/* Shelf Life */}
      {t.shelf_life && (
        <div className="bg-surface rounded-xl p-4">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider font-semibold mb-2">Durée de vie du signal</p>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Clock size={14} className="text-gold" />
              <span className="text-sm font-mono font-semibold">{t.shelf_life.shelf_life_label}</span>
            </div>
            <span className="text-sm font-mono font-bold text-gold">{t.shelf_life.order_type}</span>
          </div>
          <p className="text-[9px] text-text-secondary italic">
            {t.shelf_life.order_type === "MARKET" ? "Le signal est urgent — exécution immédiate recommandée. Le prix peut bouger rapidement." :
             "Le signal a le temps — un ordre Limit permet d'obtenir un meilleur prix d'entrée. Patience recommandée."}
          </p>
        </div>
      )}

      {/* Liens */}
      <div className="flex gap-2">
        <Link to={`/analyser/${t.symbol}`} className="flex-1 text-center px-3 py-2 bg-surface border border-border rounded-lg text-xs text-text-secondary hover:text-gold hover:border-gold/30 transition-colors">
          Stratégies →
        </Link>
        <Link to={`/asset/${t.symbol}`} className="flex-1 text-center px-3 py-2 bg-surface border border-border rounded-lg text-xs text-text-secondary hover:text-gold hover:border-gold/30 transition-colors">
          Scanner →
        </Link>
        <Link to={`/analyse?q=${t.symbol}`} className="flex-1 text-center px-3 py-2 bg-gold/10 border border-gold/20 rounded-lg text-xs text-gold font-semibold hover:bg-gold/20 transition-colors">
          Analyse →
        </Link>
      </div>
    </div>
  );
}


function PriceRow({ label, price, color = "", description = "" }: { label: string; price: number | null; color?: string; description?: string }) {
  if (price == null) return null;
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className={`text-xs font-semibold ${color}`}>{label}</p>
        {description && <p className="text-[8px] text-text-secondary">{description}</p>}
      </div>
      <p className={`text-sm font-mono font-bold ${color}`}>${price.toFixed(2)}</p>
    </div>
  );
}


function ScoreBar({ label, value, highlight, explain }: { label: string; value: number; highlight?: boolean; explain?: string }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-0.5">
        <span className={`text-[10px] ${highlight ? "font-semibold text-text-primary" : "text-text-secondary"}`}>{label}</span>
        <span className={`text-[10px] font-mono ${highlight ? "text-gold font-bold" : ""}`}>{value.toFixed(1)}</span>
      </div>
      <div className="h-1.5 bg-background rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${highlight ? "bg-gold" : "bg-gold/40"}`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      {explain && <p className="text-[8px] text-text-secondary mt-0.5 italic">{explain}</p>}
    </div>
  );
}

function MiniMetric({ label, value, color = "" }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-card rounded-lg p-1.5 text-center">
      <p className="text-[7px] text-text-secondary uppercase">{label}</p>
      <p className={`text-xs font-mono font-bold ${color}`}>{value}</p>
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
    <span className={`text-[10px] px-2 py-0.5 border rounded font-semibold ${styles[direction] || styles.NEUTRAL}`}>
      {direction}
    </span>
  );
}
