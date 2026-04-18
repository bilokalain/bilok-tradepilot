import { Component, useEffect, useState, useCallback } from "react";
import type { ReactNode, ErrorInfo } from "react";
import { RefreshCw } from "lucide-react";
import api from "../services/api";

const EWS_COLORS: Record<string, string> = {
  NORMAL: "text-gold",
  ATTENTION: "text-yellow-400",
  ALERTE: "text-orange-400",
  CRITIQUE: "text-red-500",
};

const ENGAGEMENT_COLORS: Record<string, string> = {
  FULL: "text-gold bg-gold/10 border-gold/20",
  NORMAL: "text-blue-400 bg-blue-400/10 border-blue-400/20",
  PRUDENT: "text-yellow-400 bg-yellow-400/10 border-yellow-400/20",
  MINIMAL: "text-red-400 bg-red-400/10 border-red-400/20",
};

class ErrorBoundary extends Component<{ children: ReactNode }, { error: string | null }> {
  state = { error: null as string | null };
  static getDerivedStateFromError(e: Error) { return { error: e.message }; }
  componentDidCatch(e: Error, info: ErrorInfo) { console.error("Performance error:", e, info); }
  render() {
    if (this.state.error) {
      return (
        <div className="p-8 text-center">
          <p className="text-red-400 mb-2">Erreur dans le module Performance</p>
          <p className="text-text-secondary text-sm mb-4">{this.state.error}</p>
          <button onClick={() => this.setState({ error: null })} className="px-4 py-2 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm">
            Réessayer
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function PerformanceContent() {
  const [report, setReport] = useState<any>(null);
  const [equityCurve, setEquityCurve] = useState<any>(null);
  const [learning, setLearning] = useState<any>(null);
  const [calibration, setCalibration] = useState<any>(null);
  const [entryQuality, setEntryQuality] = useState<any>(null);
  const [detection, setDetection] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(() => {
    Promise.all([
      api.get("/performance/report").catch(() => ({ data: null })),
      api.get("/performance/equity-curve").catch(() => ({ data: null })),
      api.get("/performance/learning").catch(() => ({ data: null })),
      api.get("/performance/calibration").catch(() => ({ data: null })),
      api.get("/performance/entry-quality").catch(() => ({ data: null })),
      api.get("/performance/detection").catch(() => ({ data: null })),
    ]).then(([rep, eq, learn, calib, eq2, det]) => {
      setReport(rep.data);
      setEquityCurve(eq.data);
      setCalibration(calib.data);
      setEntryQuality(eq2.data);
      setLearning(learn.data);
      setDetection(det.data);
    })
      .catch((e) => setError(e.message || "Erreur de connexion"))
      .finally(() => { setLoading(false); setRefreshing(false); });
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, [loadData]);

  if (loading) return <p className="text-text-secondary p-8">Chargement...</p>;
  if (error || !report) return <p className="text-red-400 p-8">{error || "Données indisponibles"}</p>;

  const meta = report.meta_score ?? {};
  const ews = report.ews ?? {};
  const equity = report.equity ?? {};
  const trades = report.trades ?? {};
  const feedback = report.feedback_loop ?? {};
  const attribution = report.attribution ?? {};
  const monteCarlo = report.monte_carlo ?? {};

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-2xl font-bold">Suivi de Rentabilité</h2>
        <button
          onClick={() => { setRefreshing(true); loadData(); }}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-1.5 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm font-semibold hover:bg-gold/20 transition-colors disabled:opacity-50"
        >
          <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
          {refreshing ? "Rafraîchissement..." : "Rafraîchir"}
        </button>
      </div>
      <p className="text-text-secondary text-sm mb-6 max-w-3xl">
        Attribution causale de la performance — décomposition du P&L par source (scanner, timing, sizing, sortie, régime, friction), benchmarking vs SPY et portefeuille 60/40, Early Warning System à 4 niveaux et taux de détection des top movers du jour.
      </p>

      {/* Meta-Score + Métriques */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary mb-1">Meta-Score</p>
          <p className="text-3xl font-mono font-bold text-gold">{meta.meta_score ?? "—"}</p>
          <span className={`text-xs px-2 py-0.5 border rounded mt-2 inline-block ${ENGAGEMENT_COLORS[meta.engagement] || ""}`}>
            {meta.engagement ?? "—"}
          </span>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary mb-1">Equity</p>
          <p className="text-2xl font-mono font-semibold">${(equity.current ?? 100000).toFixed(0)}</p>
          <p className={`text-xs mt-1 ${(equity.pnl ?? 0) >= 0 ? "text-gold" : "text-red-400"}`}>
            {(equity.pnl ?? 0) >= 0 ? "+" : ""}${(equity.pnl ?? 0).toFixed(2)} ({equity.pnl_pct ?? 0}%)
          </p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary mb-1">Win Rate</p>
          <p className="text-2xl font-mono font-semibold">{trades.win_rate ?? 0}%</p>
          <p className="text-xs text-text-secondary mt-1">{trades.total ?? 0} trades</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary mb-1">EWS</p>
          <p className={`text-2xl font-bold ${EWS_COLORS[ews.overall_level] || ""}`}>
            {ews.overall_level ?? "—"}
          </p>
          {ews.should_pause && (
            <p className="text-xs text-red-400 mt-1">PAUSE RECOMMANDÉE</p>
          )}
        </div>
      </div>

      {/* Equity Curve */}
      {equityCurve?.history?.length > 0 && (
        <div className="bg-card border border-border rounded-xl p-6 mb-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Equity Curve vs SPY</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Return</p>
              <p className={`text-lg font-mono font-bold ${(equityCurve.summary?.total_return ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {(equityCurve.summary?.total_return ?? 0) >= 0 ? "+" : ""}{equityCurve.summary?.total_return}%
              </p>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">SPY</p>
              <p className="text-lg font-mono font-bold text-text-secondary">
                {equityCurve.summary?.spy_return != null ? `${equityCurve.summary.spy_return >= 0 ? "+" : ""}${equityCurve.summary.spy_return}%` : "—"}
              </p>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Alpha</p>
              <p className={`text-lg font-mono font-bold ${(equityCurve.summary?.alpha ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {(equityCurve.summary?.alpha ?? 0) >= 0 ? "+" : ""}{equityCurve.summary?.alpha ?? "—"}%
              </p>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Max Drawdown</p>
              <p className="text-lg font-mono font-bold text-red-400">{equityCurve.summary?.max_drawdown ?? "—"}%</p>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Jours</p>
              <p className="text-lg font-mono font-bold">{equityCurve.summary?.days ?? 0}</p>
            </div>
          </div>
          {/* Mini chart */}
          <div className="flex items-end gap-1 h-24">
            {equityCurve.history.map((d: any, i: number) => {
              const val = d.return_pct;
              const maxVal = Math.max(...equityCurve.history.map((h: any) => Math.abs(h.return_pct || 0)), 1);
              const height = Math.abs(val) / maxVal * 80;
              return (
                <div key={i} className="flex-1 flex flex-col items-center justify-end" title={`${d.date}: ${val >= 0 ? "+" : ""}${val}%`}>
                  <div className={`w-full rounded-t ${val >= 0 ? "bg-emerald-400" : "bg-red-400"}`} style={{ height: `${Math.max(height, 2)}px` }} />
                  {i % Math.max(1, Math.floor(equityCurve.history.length / 7)) === 0 && (
                    <span className="text-[8px] text-text-secondary mt-1">{d.date?.slice(5)}</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Learning Status */}
      {learning && learning.trades_processed > 0 && (
        <div className="bg-card border border-border rounded-xl p-6 mb-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Apprentissage Autonome</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Trades analysés</p>
              <p className="text-lg font-mono font-bold text-gold">{learning.trades_processed}</p>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Actifs appris</p>
              <p className="text-lg font-mono font-bold">{learning.total_symbols_learned}</p>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Dernier retrain</p>
              <p className="text-xs font-mono">{learning.last_retrain ? new Date(learning.last_retrain).toLocaleDateString("fr-FR") : "Jamais"}</p>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Retrain nécessaire</p>
              <p className={`text-lg font-bold ${learning.should_retrain ? "text-yellow-400" : "text-emerald-400"}`}>{learning.should_retrain ? "Oui" : "Non"}</p>
            </div>
          </div>
          {/* Accuracy des critères */}
          {Object.keys(learning.criterion_accuracy ?? {}).length > 0 && (
            <div>
              <p className="text-xs text-text-secondary mb-2">Accuracy des critères du scanner</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {Object.entries(learning.criterion_accuracy).map(([criterion, acc]: [string, any]) => (
                  <div key={criterion} className="flex items-center justify-between bg-surface rounded-lg px-3 py-2">
                    <span className="text-xs font-semibold capitalize">{criterion}</span>
                    <span className={`text-xs font-mono font-bold ${acc.recent_accuracy >= 60 ? "text-emerald-400" : acc.recent_accuracy < 40 ? "text-red-400" : "text-text-secondary"}`}>
                      {acc.recent_accuracy}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Calibrage Scoring V2 */}
      {calibration && (
        <div className="bg-card border border-border rounded-xl p-6 mb-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Calibrage Automatique — Scoring V2</h3>

          {/* Poids actuels */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            {Object.entries(calibration.current_weights ?? {}).map(([key, value]: [string, any]) => {
              const labels: Record<string, string> = { bayesian: "Bayésien", sqc: "Contexte (SQC)", conviction: "Conviction", scanner: "Scanner (11 critères)" };
              const colors: Record<string, string> = { bayesian: "text-blue-400", sqc: "text-yellow-400", conviction: "text-emerald-400", scanner: "text-gold" };
              return (
                <div key={key} className="bg-surface rounded-lg p-3">
                  <p className="text-[10px] text-text-secondary">{labels[key] || key}</p>
                  <p className={`text-xl font-mono font-bold ${colors[key] || ""}`}>{(value * 100).toFixed(0)}%</p>
                  <div className="h-1.5 bg-background rounded-full mt-2 overflow-hidden">
                    <div className={`h-full rounded-full ${key === "bayesian" ? "bg-blue-400" : key === "sqc" ? "bg-yellow-400" : key === "conviction" ? "bg-emerald-400" : "bg-gold"}`} style={{ width: `${value * 100}%` }} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Taux de détection */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Jours suivis</p>
              <p className="text-lg font-mono font-bold">{calibration.days_tracked}</p>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Détection moyenne</p>
              <p className={`text-lg font-mono font-bold ${(calibration.avg_detection_rate ?? 0) >= 50 ? "text-emerald-400" : (calibration.avg_detection_rate ?? 0) >= 30 ? "text-yellow-400" : "text-red-400"}`}>
                {calibration.avg_detection_rate ?? 0}%
              </p>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Meilleur jour</p>
              <p className="text-lg font-mono font-bold text-emerald-400">{calibration.best_rate ?? 0}%</p>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Pire jour</p>
              <p className="text-lg font-mono font-bold text-red-400">{calibration.worst_rate ?? 0}%</p>
            </div>
          </div>

          {/* Dernière optimisation */}
          {calibration.last_optimization && (
            <div className="bg-gold/5 border border-gold/20 rounded-lg p-3 mb-4">
              <p className="text-[10px] text-gold uppercase tracking-wider font-semibold mb-1">Dernière optimisation — {calibration.last_optimization.date}</p>
              <div className="flex items-center gap-4 text-xs">
                <span className="text-text-secondary">Taux détection: {calibration.last_optimization.avg_detection_rate}%</span>
                <span className="text-text-secondary">→</span>
                {Object.entries(calibration.last_optimization.new_weights ?? {}).map(([k, v]: [string, any]) => {
                  const old = (calibration.last_optimization.old_weights ?? {})[k] ?? 0;
                  const diff = v - old;
                  return diff !== 0 ? (
                    <span key={k} className={diff > 0 ? "text-emerald-400" : "text-red-400"}>
                      {k}: {(old * 100).toFixed(0)}→{(v * 100).toFixed(0)}%
                    </span>
                  ) : null;
                })}
              </div>
            </div>
          )}

          {/* Historique récent */}
          {(calibration.recent_records ?? []).length > 0 && (
            <div>
              <p className="text-[10px] text-text-secondary uppercase tracking-wider font-semibold mb-2">Historique détection (7 derniers jours)</p>
              <div className="flex items-end gap-1 h-16">
                {(calibration.recent_records ?? []).map((r: any, i: number) => {
                  const rate = r.detection_rate ?? 0;
                  const color = rate >= 50 ? "bg-emerald-400" : rate >= 30 ? "bg-yellow-400" : "bg-red-400";
                  return (
                    <div key={i} className="flex-1 flex flex-col items-center justify-end" title={`${r.date}: ${rate}% (${r.detected}/${r.top_gainers_count})`}>
                      <div className={`w-full rounded-t ${color}`} style={{ height: `${Math.max(rate * 0.6, 3)}px` }} />
                      <span className="text-[7px] text-text-secondary mt-1">{r.date?.slice(5)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {calibration.days_tracked === 0 && (
            <p className="text-xs text-text-secondary text-center py-2">Le calibrage commence après le premier pipeline nocturne. Les poids s'ajustent automatiquement après 5 jours de données.</p>
          )}
        </div>
      )}

      {/* Qualité d'entrée */}
      {entryQuality && entryQuality.total_trades > 0 && (
        <div className="bg-card border border-border rounded-xl p-6 mb-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Qualité d'Entrée — Apprentissage Pré-Trade</h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Trades analysés</p>
              <p className="text-lg font-mono font-bold">{entryQuality.closed_trades}</p>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Win Rate global</p>
              <p className={`text-lg font-mono font-bold ${(entryQuality.overall_win_rate ?? 0) >= 50 ? "text-emerald-400" : "text-red-400"}`}>
                {entryQuality.overall_win_rate ?? 0}%
              </p>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">Seuil optimal appris</p>
              <p className="text-lg font-mono font-bold text-gold">{entryQuality.optimal_threshold}/100</p>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[10px] text-text-secondary">En cours</p>
              <p className="text-lg font-mono font-bold">{entryQuality.open_trades}</p>
            </div>
          </div>

          {/* Pouvoir prédictif des signaux */}
          {Object.keys(entryQuality.signal_accuracy ?? {}).length > 0 && (
            <div className="mb-4">
              <p className="text-[10px] text-text-secondary uppercase tracking-wider font-semibold mb-2">Pouvoir prédictif des signaux pré-trade</p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {Object.entries(entryQuality.signal_accuracy).map(([name, acc]: [string, any]) => (
                  <div key={name} className="bg-surface rounded-lg px-3 py-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold capitalize">{name}</span>
                      <span className={`text-xs font-mono font-bold ${(acc.predictive_power ?? 0) > 10 ? "text-emerald-400" : (acc.predictive_power ?? 0) < -10 ? "text-red-400" : "text-text-secondary"}`}>
                        {(acc.predictive_power ?? 0) > 0 ? "+" : ""}{acc.predictive_power ?? 0}pp
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px]">
                      <span className="text-emerald-400">FORT: {acc.fort_winrate ?? 0}%</span>
                      <span className="text-red-400">FAIBLE: {acc.faible_winrate ?? 0}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Combinaisons dangereuses */}
          {(entryQuality.dangerous_combos ?? []).length > 0 && (
            <div>
              <p className="text-[10px] text-red-400 uppercase tracking-wider font-semibold mb-2">Combinaisons dangereuses détectées</p>
              {entryQuality.dangerous_combos.map((c: any, i: number) => (
                <div key={i} className="flex items-center gap-2 bg-red-400/5 border border-red-400/10 rounded-lg px-3 py-2 mb-1">
                  <span className="text-[10px] text-red-400 font-mono">{c.combo}</span>
                  <span className="text-[10px] text-text-secondary">— {c.count} pertes</span>
                </div>
              ))}
            </div>
          )}

          {entryQuality.closed_trades === 0 && (
            <p className="text-xs text-text-secondary text-center py-2">L'apprentissage démarre après les premières fermetures de trades.</p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* EWS Détail */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Early Warning System</h3>
          <div className="space-y-3">
            {(ews.indicators ?? []).map((ind: any) => (
              <div key={ind.name} className="flex items-center justify-between">
                <span className="text-sm">{ind.name}</span>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-mono">{ind.value}{ind.unit}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    ind.level === "NORMAL" ? "bg-gold/10 text-gold" :
                    ind.level === "ATTENTION" ? "bg-yellow-400/10 text-yellow-400" :
                    ind.level === "ALERTE" ? "bg-orange-400/10 text-orange-400" :
                    "bg-red-500/10 text-red-500"
                  }`}>
                    {ind.level}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Attribution P&L */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Attribution P&L</h3>
          {(attribution.num_trades ?? 0) === 0 ? (
            <p className="text-text-secondary text-sm">
              Aucun trade fermé — l'attribution se remplira avec le temps
            </p>
          ) : (
            <div className="space-y-2">
              {Object.entries(attribution.attribution_pct ?? {}).map(([key, pct]: [string, any]) => (
                <div key={key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="capitalize">{key}</span>
                    <span className="font-mono">{pct}%</span>
                  </div>
                  <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${pct >= 0 ? "bg-gold" : "bg-red-400"}`}
                      style={{ width: `${Math.min(Math.abs(pct), 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monte Carlo */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Monte Carlo</h3>
          {monteCarlo.status !== "ok" ? (
            <p className="text-text-secondary text-sm">{monteCarlo.message ?? "Pas assez de données pour la simulation"}</p>
          ) : (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-text-secondary">Percentile 10</span>
                <span className="font-mono text-red-400">${monteCarlo.percentiles?.p10 ?? "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Percentile 50 (médiane)</span>
                <span className="font-mono">${monteCarlo.percentiles?.p50 ?? "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Percentile 90</span>
                <span className="font-mono text-gold">${monteCarlo.percentiles?.p90 ?? "—"}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-border">
                <span className="text-text-secondary">P(ruine)</span>
                <span className="font-mono text-red-400">{monteCarlo.p_ruin ?? "—"}%</span>
              </div>
            </div>
          )}
        </div>

        {/* Feedback Loop */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">
            Feedback Loop → Module 1
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm">Action pipeline</span>
              <span className={`text-xs px-2 py-1 rounded font-semibold ${
                feedback.action === "CONTINUE" ? "text-gold bg-gold/10" : "text-red-400 bg-red-400/10"
              }`}>
                {feedback.action ?? "—"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Engagement</span>
              <span className={`text-xs px-2 py-1 border rounded font-semibold ${ENGAGEMENT_COLORS[feedback.pipeline_engagement] || ""}`}>
                {feedback.pipeline_engagement ?? "—"}
              </span>
            </div>
            <p className="text-xs text-text-secondary mt-2">{meta.description ?? ""}</p>
            {feedback.reason && (
              <p className="text-xs text-red-400 mt-1">{feedback.reason}</p>
            )}
          </div>
        </div>
      </div>

    {/* Taux de Détection — Top Movers */}
    {detection && detection.movers && (
      <div className="bg-card border border-border rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold">Taux de Détection — Top Movers</h2>
          <div className="flex items-center gap-3">
            <span className={`text-2xl font-mono font-bold ${
              detection.detection_rate >= 70 ? "text-emerald-400" : detection.detection_rate >= 40 ? "text-yellow-400" : "text-red-400"
            }`}>
              {detection.detection_rate}%
            </span>
            <span className="text-xs text-text-secondary">
              {detection.detected}/{detection.total_movers} movers
            </span>
          </div>
        </div>

        {/* Barre de progression */}
        <div className="h-2 bg-surface rounded-full mb-4 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              detection.detection_rate >= 70 ? "bg-emerald-400" : detection.detection_rate >= 40 ? "bg-yellow-400" : "bg-red-400"
            }`}
            style={{ width: `${detection.detection_rate}%` }}
          />
        </div>

        {/* Liste des movers */}
        {detection.movers && detection.movers.length > 0 && (
          <div className="space-y-1 mb-4">
            {detection.movers.map((m: any) => (
              <div key={m.symbol} className={`flex items-center justify-between py-1.5 px-3 rounded-lg text-xs ${
                m.detected ? "bg-emerald-400/5" : "bg-red-400/5"
              }`}>
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${m.detected ? "bg-emerald-400" : "bg-red-400"}`} />
                  <span className="font-mono font-bold text-gold">{m.symbol}</span>
                  {m.is_go && (
                    <span className="text-[9px] px-1 py-0.5 rounded bg-emerald-400/10 text-emerald-400 font-semibold">GO</span>
                  )}
                </div>
                <div className="flex items-center gap-4">
                  <span className="font-mono text-emerald-400">+{m.change_pct.toFixed(1)}%</span>
                  <span className={`font-mono ${m.scanner_score >= 65 ? "text-emerald-400" : m.scanner_score >= 60 ? "text-yellow-400" : "text-red-400"}`}>
                    {m.scanner_score.toFixed(0)}/100
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Historique */}
        {detection.history && detection.history.length > 0 && (
          <div className="border-t border-border/50 pt-3">
            <p className="text-xs text-text-secondary mb-2 font-semibold uppercase tracking-wider">Historique</p>
            <div className="flex gap-2 flex-wrap">
              {detection.history.map((h: any) => (
                <div key={h.date} className={`text-[10px] px-2 py-1 rounded border font-mono ${
                  h.detection_rate >= 50 ? "border-emerald-400/20 text-emerald-400 bg-emerald-400/5"
                    : h.detection_rate >= 20 ? "border-yellow-400/20 text-yellow-400 bg-yellow-400/5"
                    : "border-red-400/20 text-red-400 bg-red-400/5"
                }`}>
                  {h.date.slice(5)} : {h.detection_rate}%
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )}
    </div>
  );
}

export default function Performance() {
  return (
    <ErrorBoundary>
      <PerformanceContent />
    </ErrorBoundary>
  );
}
