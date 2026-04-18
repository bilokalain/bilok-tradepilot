import { useCallback, useEffect, useState } from "react";
import api from "../services/api";

interface StressResult {
  scenario: string;
  description?: string;
  total_impact_usd: number;
  total_impact_pct: number;
  portfolio_after: number;
}

export default function Portfolio() {
  const [summary, setSummary] = useState<any>(null);
  const [stress, setStress] = useState<StressResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback((isManual = false) => {
    if (isManual) setRefreshing(true);
    Promise.all([
      api.get("/portfolio/summary"),
      api.get("/portfolio/stress-test"),
    ])
      .then(([sumRes, stressRes]) => {
        setSummary(sumRes.data);
        setStress(stressRes.data);
      })
      .catch(console.error)
      .finally(() => {
        setLoading(false);
        if (isManual) setRefreshing(false);
      });
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => fetchData(), 60_000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) return <p className="text-text-secondary">Chargement...</p>;

  const regime = summary?.regime || {};

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-2xl font-bold">Portefeuille</h2>
        <button
          onClick={() => fetchData(true)}
          disabled={refreshing}
          className="px-3 py-1.5 text-sm bg-card border border-border rounded-lg hover:bg-surface transition-colors disabled:opacity-50"
        >
          {refreshing ? "Rafraîchissement..." : "Rafraîchir"}
        </button>
      </div>
      <p className="text-text-secondary text-sm mb-6 max-w-3xl">
        Gestion dynamique du risque et de l'allocation — Risk Parity, stress testing sur scénarios historiques (Mars 2020, crypto crash), détection de régime portefeuille (ALPHA/BETA/STRESS) et contrôle du drawdown depuis le peak equity.
      </p>

      {/* Métriques */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <MetricCard label="Valeur totale" value={`$${summary?.total_value?.toFixed(2) || 0}`} />
        <MetricCard
          label="P&L"
          value={`$${summary?.total_pnl?.toFixed(2) || 0}`}
          sub={`${summary?.total_pnl_pct?.toFixed(2) || 0}%`}
          color={summary?.total_pnl >= 0 ? "text-gold" : "text-red-400"}
        />
        <MetricCard label="Positions" value={String(summary?.num_positions || 0)} />
        <MetricCard label="Régime" value={regime?.regime || "—"} color={
          regime?.regime === "ALPHA" ? "text-gold" : regime?.regime === "STRESS" ? "text-red-400" : ""
        } />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Positions */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Positions ouvertes</h3>
          {(summary?.positions?.length || 0) === 0 ? (
            <p className="text-text-secondary text-sm">Aucune position</p>
          ) : (
            <div className="space-y-3">
              {summary.positions.map((p: any) => (
                <div key={p.id} className="bg-surface rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-gold">{p.symbol}</span>
                      <span className="text-xs text-text-secondary">{p.direction}</span>
                    </div>
                    <span className={`font-mono font-semibold ${p.pnl >= 0 ? "text-gold" : "text-red-400"}`}>
                      ${p.pnl.toFixed(2)}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs text-text-secondary">
                    <div>Valeur <span className="font-mono text-text-primary">${p.market_value.toFixed(0)}</span></div>
                    <div>Liq. <span className="font-mono text-text-primary">{p.liquidation_score}</span></div>
                    <div>Classe <span className="text-text-primary">{p.asset_class}</span></div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Allocation */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Allocation par classe</h3>
          {summary?.allocation && Object.keys(summary.allocation).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(summary.allocation).map(([ac, pct]: [string, any]) => (
                <div key={ac}>
                  <div className="flex justify-between text-sm mb-1">
                    <span>{ac}</span>
                    <span className="font-mono">{pct}%</span>
                  </div>
                  <div className="h-2 bg-surface rounded-full overflow-hidden">
                    <div className="h-full bg-gold rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-text-secondary text-sm">Aucune allocation</p>
          )}
        </div>
      </div>

      {/* Stress Tests */}
      <div className="bg-card border border-border rounded-xl p-6">
        <h3 className="text-sm font-medium text-text-secondary mb-4">Stress Tests</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {stress.map((s) => (
            <div key={s.scenario} className="bg-surface rounded-lg p-4">
              <h4 className="text-sm font-semibold mb-1">{s.scenario}</h4>
              {s.description && <p className="text-xs text-text-secondary mb-2">{s.description}</p>}
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-text-secondary text-xs">Impact</span>
                  <p className="font-mono text-red-400">${s.total_impact_usd?.toFixed(0)} ({s.total_impact_pct}%)</p>
                </div>
                <div>
                  <span className="text-text-secondary text-xs">Portefeuille après</span>
                  <p className="font-mono">${s.portfolio_after?.toFixed(0)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <p className="text-xs text-text-secondary mb-1">{label}</p>
      <p className={`text-2xl font-mono font-semibold ${color || "text-gold"}`}>{value}</p>
      {sub && <p className="text-xs text-text-secondary mt-0.5">{sub}</p>}
    </div>
  );
}
