import { useCallback, useEffect, useState } from "react";
import { RefreshCw, Shield, TrendingUp, AlertTriangle, PieChart, Activity } from "lucide-react";
import api from "../services/api";

interface StressResult {
  scenario: string;
  description?: string;
  total_impact_usd: number;
  total_impact_pct: number;
  portfolio_after: number;
}

const REGIME_CONFIG: Record<string, { color: string; bg: string; label: string; icon: string }> = {
  ALPHA: { color: "text-emerald-400", bg: "bg-emerald-400/10 border-emerald-400/20", label: "Surperformance", icon: "🏆" },
  BETA: { color: "text-blue-400", bg: "bg-blue-400/10 border-blue-400/20", label: "Performance marché", icon: "📊" },
  STRESS: { color: "text-red-400", bg: "bg-red-400/10 border-red-400/20", label: "Sous-performance", icon: "⚠️" },
};

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

  if (loading) return <p className="text-text-secondary p-8">Chargement du portefeuille...</p>;

  const regime = summary?.regime || {};
  const regimeConf = REGIME_CONFIG[regime?.regime] || REGIME_CONFIG.BETA;
  const positions = summary?.positions || [];
  const allocation = summary?.allocation || {};
  const totalVal = summary?.total_value || 0;
  const totalPnl = summary?.total_pnl || 0;
  const totalPnlPct = summary?.total_pnl_pct || 0;
  const numPos = summary?.num_positions || 0;
  const drawdown = summary?.drawdown ?? summary?.max_drawdown ?? 0;
  const var95 = summary?.var_95 ?? null;
  const riskBudget = summary?.risk_budget ?? null;
  const beta = summary?.beta ?? null;
  const correlation = summary?.correlation_matrix ?? null;

  // Positions gagnantes vs perdantes
  const winners = positions.filter((p: any) => p.pnl >= 0);
  const losers = positions.filter((p: any) => p.pnl < 0);
  const bestPos = positions.length > 0 ? [...positions].sort((a: any, b: any) => b.pnl - a.pnl)[0] : null;
  const worstPos = positions.length > 0 ? [...positions].sort((a: any, b: any) => a.pnl - b.pnl)[0] : null;

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-2xl font-bold">Portefeuille</h2>
        <button
          onClick={() => fetchData(true)}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-1.5 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm font-semibold hover:bg-gold/20 transition-colors disabled:opacity-50"
        >
          <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
          {refreshing ? "..." : "Rafraîchir"}
        </button>
      </div>
      <p className="text-text-secondary text-sm mb-6 max-w-3xl">
        Gestion dynamique du risque — Risk Parity, stress testing, contrôle du drawdown, détection de régime portefeuille et allocation par classe d'actif.
      </p>

      {/* Diagnostic narratif */}
      <PortfolioVerdict regime={regime} totalPnl={totalPnl} totalPnlPct={totalPnlPct} numPos={numPos} drawdown={drawdown} winners={winners.length} losers={losers.length} var95={var95} bestPos={bestPos} worstPos={worstPos} />

      {/* KPIs principaux */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider">Valeur totale</p>
          <p className="text-xl font-mono font-bold text-gold mt-1">${totalVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider">P&L non réalisé</p>
          <p className={`text-xl font-mono font-bold mt-1 ${totalPnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {totalPnl >= 0 ? "+" : ""}${totalPnl.toFixed(2)}
          </p>
          <p className={`text-[10px] font-mono ${totalPnlPct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {totalPnlPct >= 0 ? "+" : ""}{totalPnlPct.toFixed(2)}%
          </p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider">Positions</p>
          <p className="text-xl font-mono font-bold mt-1">{numPos}</p>
          <p className="text-[10px] text-text-secondary">
            <span className="text-emerald-400">{winners.length}W</span> / <span className="text-red-400">{losers.length}L</span>
          </p>
        </div>
        <div className={`bg-card border rounded-xl p-4 ${regimeConf.bg}`}>
          <p className="text-[9px] text-text-secondary uppercase tracking-wider">Régime</p>
          <p className={`text-xl font-bold mt-1 ${regimeConf.color}`}>{regimeConf.icon} {regime?.regime || "—"}</p>
          <p className={`text-[10px] ${regimeConf.color}`}>{regimeConf.label}</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider">Drawdown</p>
          <p className={`text-xl font-mono font-bold mt-1 ${Math.abs(drawdown) > 10 ? "text-red-400" : Math.abs(drawdown) > 5 ? "text-yellow-400" : "text-emerald-400"}`}>
            {drawdown}%
          </p>
          <p className="text-[10px] text-text-secondary">
            {Math.abs(drawdown) <= 5 ? "Normal" : Math.abs(drawdown) <= 10 ? "Attention" : Math.abs(drawdown) <= 15 ? "Alerte" : "Critique"}
          </p>
        </div>
      </div>

      {/* Risk Metrics */}
      {(var95 != null || riskBudget != null || beta != null) && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          {var95 != null && (
            <RiskMetric label="VaR 95%" value={`$${Math.abs(var95).toFixed(0)}`} explain="Perte max attendue par jour (95% confiance)" color="text-red-400" />
          )}
          {riskBudget != null && (
            <RiskMetric label="Risk Budget" value={`${riskBudget.used_pct?.toFixed(0) ?? 0}%`}
              explain={`${riskBudget.remaining_pct?.toFixed(0) ?? 100}% restant sur ${riskBudget.total_pct ?? 15}% max`}
              color={riskBudget.used_pct > 80 ? "text-red-400" : riskBudget.used_pct > 50 ? "text-yellow-400" : "text-emerald-400"} />
          )}
          {beta != null && (
            <RiskMetric label="Beta" value={beta.toFixed(2)}
              explain={beta > 1.3 ? "Trop agressif vs marché" : beta > 0.8 ? "Exposition normale" : "Défensif"}
              color={beta > 1.3 ? "text-red-400" : beta > 0.8 ? "text-gold" : "text-blue-400"} />
          )}
          <RiskMetric label="Max Positions" value={`${numPos}/15`}
            explain={numPos >= 14 ? "Quasi plein — file d'attente active" : `${15 - numPos} slots disponibles`}
            color={numPos >= 14 ? "text-yellow-400" : "text-emerald-400"} />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Positions ouvertes — version pro */}
        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Activity size={16} className="text-gold" />
            <h3 className="text-sm font-semibold">Positions ouvertes ({numPos})</h3>
          </div>
          {positions.length === 0 ? (
            <p className="text-text-secondary text-sm text-center py-4">Aucune position ouverte</p>
          ) : (
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {[...positions].sort((a: any, b: any) => b.pnl - a.pnl).map((p: any) => (
                <div key={p.id} className={`rounded-lg p-3 border ${p.pnl >= 0 ? "bg-emerald-400/5 border-emerald-400/10" : "bg-red-400/5 border-red-400/10"}`}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-gold text-sm">{p.symbol}</span>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded font-semibold ${p.direction === "LONG" ? "bg-gold/10 text-gold" : "bg-red-400/10 text-red-400"}`}>
                        {p.direction}
                      </span>
                    </div>
                    <span className={`font-mono font-bold text-sm ${p.pnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {p.pnl >= 0 ? "+" : ""}${p.pnl.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-text-secondary">
                    <span>Valeur: <span className="font-mono text-text-primary">${p.market_value?.toFixed(0)}</span></span>
                    <span>Liquidité: <span className={`font-mono ${p.liquidation_score >= 70 ? "text-emerald-400" : p.liquidation_score >= 40 ? "text-yellow-400" : "text-red-400"}`}>{p.liquidation_score}/100</span></span>
                    <span className="text-text-primary">{p.asset_class}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Allocation par classe — version pro */}
        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <PieChart size={16} className="text-gold" />
            <h3 className="text-sm font-semibold">Allocation par classe d'actif</h3>
          </div>
          {Object.keys(allocation).length === 0 ? (
            <p className="text-text-secondary text-sm text-center py-4">Aucune allocation</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(allocation)
                .sort(([, a]: any, [, b]: any) => b - a)
                .map(([ac, pct]: [string, any]) => {
                  const colors: Record<string, string> = {
                    ACTION_US: "bg-blue-400", CRYPTO: "bg-purple-400", ETF: "bg-gold",
                    ACTION_EU: "bg-emerald-400", FOREX: "bg-cyan-400", COMMODITY: "bg-orange-400",
                  };
                  const barColor = colors[ac] || "bg-gold";
                  const isConcentrated = pct > 40;
                  return (
                    <div key={ac}>
                      <div className="flex justify-between text-sm mb-1">
                        <div className="flex items-center gap-2">
                          <span>{ac}</span>
                          {isConcentrated && <span className="text-[9px] text-yellow-400 bg-yellow-400/10 px-1 rounded">CONCENTRÉ</span>}
                        </div>
                        <span className="font-mono font-semibold">{pct}%</span>
                      </div>
                      <div className="h-2.5 bg-surface rounded-full overflow-hidden">
                        <div className={`h-full ${barColor} rounded-full transition-all`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              <p className="text-[10px] text-text-secondary italic mt-2">
                Risk Parity : le système répartit le risque (pas le capital) de manière égale. Un actif volatile a une petite position, un actif stable a une grosse position.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Stress Tests — version pro */}
      <div className="bg-card border border-border rounded-xl p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Shield size={16} className="text-gold" />
          <h3 className="text-sm font-semibold">Stress Tests — Résistance aux crises</h3>
        </div>
        <p className="text-xs text-text-secondary mb-4">
          Simulation de l'impact de scénarios historiques sur votre portefeuille actuel. Ces tests mesurent combien vous perdriez si une crise similaire se reproduisait.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {stress.map((s) => {
            const severity = Math.abs(s.total_impact_pct);
            const severityColor = severity > 30 ? "border-red-500/30 bg-red-500/5" : severity > 15 ? "border-orange-400/30 bg-orange-400/5" : severity > 5 ? "border-yellow-400/30 bg-yellow-400/5" : "border-border bg-surface";
            return (
              <div key={s.scenario} className={`rounded-xl p-4 border ${severityColor}`}>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold">{s.scenario}</h4>
                  <span className={`text-xs font-mono font-bold ${severity > 20 ? "text-red-400" : severity > 10 ? "text-orange-400" : "text-yellow-400"}`}>
                    {s.total_impact_pct}%
                  </span>
                </div>
                {s.description && <p className="text-[10px] text-text-secondary mb-2">{s.description}</p>}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-text-secondary">Perte estimée</span>
                    <p className="font-mono text-red-400 font-semibold">${Math.abs(s.total_impact_usd).toFixed(0)}</p>
                  </div>
                  <div>
                    <span className="text-text-secondary">Capital après</span>
                    <p className="font-mono font-semibold">${s.portfolio_after?.toFixed(0)}</p>
                  </div>
                </div>
                {/* Barre d'impact */}
                <div className="h-1.5 bg-background rounded-full mt-2 overflow-hidden">
                  <div className={`h-full rounded-full ${severity > 20 ? "bg-red-400" : severity > 10 ? "bg-orange-400" : "bg-yellow-400"}`}
                    style={{ width: `${Math.min(severity, 100)}%` }} />
                </div>
                <p className="text-[9px] text-text-secondary mt-1 italic">
                  {severity <= 5 ? "Impact minimal — portefeuille résistant à ce scénario."
                    : severity <= 15 ? "Impact modéré — le portefeuille survit mais souffre."
                    : severity <= 30 ? "Impact sévère — le drawdown serait significatif."
                    : "Impact critique — risque de perte majeure. Diversifiez davantage."}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Drawdown Control */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle size={16} className="text-gold" />
          <h3 className="text-sm font-semibold">Contrôle du Drawdown</h3>
        </div>
        <div className="grid grid-cols-4 gap-2 mb-3">
          {[
            { label: "Normal", range: "0% à -5%", color: drawdown === 0 || Math.abs(drawdown) <= 5 ? "border-emerald-400 bg-emerald-400/10 text-emerald-400" : "border-border bg-surface text-text-secondary" },
            { label: "Warning", range: "-5% à -10%", color: Math.abs(drawdown) > 5 && Math.abs(drawdown) <= 10 ? "border-yellow-400 bg-yellow-400/10 text-yellow-400" : "border-border bg-surface text-text-secondary" },
            { label: "Alerte", range: "-10% à -15%", color: Math.abs(drawdown) > 10 && Math.abs(drawdown) <= 15 ? "border-orange-400 bg-orange-400/10 text-orange-400" : "border-border bg-surface text-text-secondary" },
            { label: "Critique", range: "> -20%", color: Math.abs(drawdown) > 15 ? "border-red-400 bg-red-400/10 text-red-400" : "border-border bg-surface text-text-secondary" },
          ].map((level) => (
            <div key={level.label} className={`rounded-lg p-2 text-center border text-xs ${level.color}`}>
              <p className="font-semibold">{level.label}</p>
              <p className="text-[9px] mt-0.5 opacity-75">{level.range}</p>
            </div>
          ))}
        </div>
        <p className="text-[10px] text-text-secondary italic">
          Le système réduit automatiquement l'exposition quand le drawdown atteint les seuils : -5% → sizing -20%, -10% → sizing -50%, -15% → fermeture 50% des positions, -20% → fermeture totale et pause pipeline.
        </p>
      </div>
    </div>
  );
}


// ============================================================
// Verdict narratif
// ============================================================

function PortfolioVerdict({ regime, totalPnl, totalPnlPct, numPos, drawdown, winners, losers, var95, bestPos, worstPos }: any) {
  const parts: string[] = [];
  const regimeLabel = regime?.regime || "BETA";

  if (regimeLabel === "ALPHA") parts.push("Le portefeuille surperforme son benchmark — le système génère de l'alpha.");
  else if (regimeLabel === "STRESS") parts.push("Le portefeuille est en régime STRESS — sous-performance significative. L'exposition est automatiquement réduite.");
  else parts.push("Le portefeuille performe comme le marché (régime BETA).");

  if (numPos === 0) {
    parts.push("Aucune position ouverte. Le capital est entièrement en cash.");
  } else {
    parts.push(`${numPos} position${numPos > 1 ? "s" : ""} ouverte${numPos > 1 ? "s" : ""} — ${winners} en profit, ${losers} en perte.`);
    if (totalPnl >= 0) parts.push(`P&L non réalisé de +$${totalPnl.toFixed(2)} (+${totalPnlPct.toFixed(2)}%).`);
    else parts.push(`P&L non réalisé de -$${Math.abs(totalPnl).toFixed(2)} (${totalPnlPct.toFixed(2)}%).`);
  }

  if (bestPos && numPos > 0) parts.push(`Meilleure position : ${bestPos.symbol} (${bestPos.pnl >= 0 ? "+" : ""}$${bestPos.pnl.toFixed(2)}).`);
  if (worstPos && numPos > 0 && worstPos.pnl < 0) parts.push(`Pire : ${worstPos.symbol} ($${worstPos.pnl.toFixed(2)}).`);

  if (var95 != null) parts.push(`La VaR à 95% est de $${Math.abs(var95).toFixed(0)}/jour — dans 95% des cas, la perte quotidienne ne dépassera pas ce montant.`);

  if (Math.abs(drawdown) > 10) parts.push(`Attention : le drawdown de ${drawdown}% est significatif.`);

  const verdictColor = regimeLabel === "ALPHA" ? "border-emerald-400/20 bg-emerald-400/5" :
    regimeLabel === "STRESS" ? "border-red-400/20 bg-red-400/5" :
    "border-gold/20 bg-gold/5";

  return (
    <div className={`mb-6 p-5 rounded-xl border ${verdictColor}`}>
      <div className="flex items-center gap-2 mb-2">
        <TrendingUp size={16} className="text-gold" />
        <span className="text-sm font-semibold">Diagnostic du portefeuille</span>
      </div>
      <p className="text-sm text-text-secondary leading-relaxed">{parts.join(" ")}</p>
    </div>
  );
}


function RiskMetric({ label, value, explain, color = "" }: { label: string; value: string; explain: string; color?: string }) {
  return (
    <div className="bg-card border border-border rounded-xl p-3 text-center">
      <p className="text-[9px] text-text-secondary uppercase tracking-wider">{label}</p>
      <p className={`text-lg font-mono font-bold mt-1 ${color}`}>{value}</p>
      <p className="text-[8px] text-text-secondary mt-1 italic">{explain}</p>
    </div>
  );
}
