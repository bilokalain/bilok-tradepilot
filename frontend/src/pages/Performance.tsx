import { useEffect, useState } from "react";
import axios from "axios";

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

export default function Performance() {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get("/api/performance/report")
      .then((res) => setReport(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-text-secondary">Chargement...</p>;
  if (!report) return <p className="text-text-secondary">Erreur de chargement</p>;

  const meta = report.meta_score;
  const ews = report.ews;
  const equity = report.equity;
  const trades = report.trades;
  const feedback = report.feedback_loop;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Suivi de Rentabilité</h2>
      <p className="text-text-secondary mb-6 text-sm">
        Attribution P&L — Monte Carlo — Early Warning System — Feedback Loop
      </p>

      {/* Meta-Score + Métriques */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary mb-1">Meta-Score</p>
          <p className="text-3xl font-mono font-bold text-gold">{meta.meta_score}</p>
          <span className={`text-xs px-2 py-0.5 border rounded mt-2 inline-block ${ENGAGEMENT_COLORS[meta.engagement] || ""}`}>
            {meta.engagement}
          </span>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary mb-1">Equity</p>
          <p className="text-2xl font-mono font-semibold">${equity.current.toFixed(0)}</p>
          <p className={`text-xs mt-1 ${equity.pnl >= 0 ? "text-gold" : "text-red-400"}`}>
            {equity.pnl >= 0 ? "+" : ""}${equity.pnl.toFixed(2)} ({equity.pnl_pct}%)
          </p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary mb-1">Win Rate</p>
          <p className="text-2xl font-mono font-semibold">{trades.win_rate}%</p>
          <p className="text-xs text-text-secondary mt-1">{trades.total} trades</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary mb-1">EWS</p>
          <p className={`text-2xl font-bold ${EWS_COLORS[ews.overall_level]}`}>
            {ews.overall_level}
          </p>
          {ews.should_pause && (
            <p className="text-xs text-red-400 mt-1">PAUSE RECOMMANDÉE</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* EWS Détail */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Early Warning System</h3>
          <div className="space-y-3">
            {ews.indicators.map((ind: any) => (
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
          {report.attribution.num_trades === 0 ? (
            <p className="text-text-secondary text-sm">
              Aucun trade fermé — l'attribution se remplira avec le temps
            </p>
          ) : (
            <div className="space-y-2">
              {Object.entries(report.attribution.attribution_pct).map(([key, pct]: [string, any]) => (
                <div key={key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="capitalize">{key}</span>
                    <span className="font-mono">{pct}%</span>
                  </div>
                  <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${pct >= 0 ? "bg-gold" : "bg-red-400"}`}
                      style={{ width: `${Math.abs(pct)}%` }}
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
          {report.monte_carlo.status !== "ok" ? (
            <p className="text-text-secondary text-sm">{report.monte_carlo.message}</p>
          ) : (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-text-secondary">Percentile 10</span>
                <span className="font-mono text-red-400">${report.monte_carlo.percentiles.p10}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Percentile 50 (médiane)</span>
                <span className="font-mono">${report.monte_carlo.percentiles.p50}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Percentile 90</span>
                <span className="font-mono text-gold">${report.monte_carlo.percentiles.p90}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-border">
                <span className="text-text-secondary">P(ruine)</span>
                <span className="font-mono text-red-400">{report.monte_carlo.p_ruin}%</span>
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
                {feedback.action}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Engagement</span>
              <span className={`text-xs px-2 py-1 border rounded font-semibold ${ENGAGEMENT_COLORS[feedback.pipeline_engagement] || ""}`}>
                {feedback.pipeline_engagement}
              </span>
            </div>
            <p className="text-xs text-text-secondary mt-2">{meta.description}</p>
            {feedback.reason && (
              <p className="text-xs text-red-400 mt-1">{feedback.reason}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
