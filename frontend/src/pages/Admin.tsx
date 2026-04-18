import { useEffect, useState } from "react";
import api from "../services/api";
import {
  Server, Database, RefreshCw, Trash2, Users, FileText,
  Wifi, WifiOff, HardDrive, Clock, Shield, AlertTriangle,
  TrendingUp, BarChart3, PieChart, Activity, Flame, Snowflake,
  DollarSign, Landmark,
} from "lucide-react";

interface ServiceStatus {
  status: string;
  [key: string]: any;
}

export default function Admin() {
  const [status, setStatus] = useState<any>(null);
  const [dbStats, setDbStats] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [positions, setPositions] = useState<any[]>([]);
  const [logs, setLogs] = useState<{ name: string; lines: string[] } | null>(null);
  const [logFiles, setLogFiles] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [ibkrStats, setIbkrStats] = useState<any>(null);
  const [tradesHistory, setTradesHistory] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState("");
  const [tab, setTab] = useState<"ibkr" | "history" | "stats" | "system">("ibkr");

  const refresh = () => {
    setLoading(true);
    Promise.all([
      api.get("/admin/status").catch(() => ({ data: null })),
      api.get("/admin/db/stats").catch(() => ({ data: null })),
      api.get("/admin/users").catch(() => ({ data: [] })),
      api.get("/admin/positions").catch(() => ({ data: [] })),
      api.get("/admin/logs/list").catch(() => ({ data: [] })),
      api.get("/admin/trading-stats").catch(() => ({ data: null })),
      api.get("/admin/ibkr-stats").catch(() => ({ data: null })),
      api.get("/admin/trades-history").catch(() => ({ data: null })),
    ]).then(([s, db, u, p, l, ts, ibkr, history]) => {
      setStatus(s.data);
      setDbStats(db.data);
      setUsers(Array.isArray(u.data) ? u.data : []);
      setPositions(Array.isArray(p.data) ? p.data : []);
      setLogFiles(Array.isArray(l.data) ? l.data : []);
      setStats(ts.data);
      setIbkrStats(ibkr.data);
      setTradesHistory(history.data);
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000); // Refresh toutes les 30s
    return () => clearInterval(interval);
  }, []);

  const flash = (msg: string) => { setActionMsg(msg); setTimeout(() => setActionMsg(""), 3000); };

  const clearCache = (name: string) => {
    api.post(`/admin/cache/clear/${name}`).then((r) => {
      flash(`Cache ${name} vidé`);
      refresh();
    });
  };

  const rebuildCache = () => {
    api.post("/admin/cache/rebuild").then(() => flash("Recalcul lancé en arrière-plan"));
  };

  const closePosition = (id: number) => {
    api.delete(`/admin/positions/${id}`).then(() => { flash(`Position ${id} fermée`); refresh(); });
  };

  const cleanPhantoms = () => {
    api.delete("/admin/positions/clean/phantoms").then((r) => {
      flash(`${r.data.closed} positions fantômes fermées`);
      refresh();
    });
  };

  const deleteUser = (email: string) => {
    if (email === "admin@tradepilot.local") return flash("Impossible de supprimer l'admin");
    api.delete(`/admin/users/${email}`).then(() => { flash(`Utilisateur ${email} supprimé`); refresh(); });
  };

  const toggleAdmin = (email: string, currentStatus: boolean) => {
    api.put(`/admin/users/${email}/admin`, { is_admin: !currentStatus }).then(() => {
      flash(`${email} est maintenant ${!currentStatus ? "admin" : "utilisateur standard"}`);
      refresh();
    });
  };

  const viewLog = (name: string) => {
    api.get(`/admin/logs?name=${name}&lines=80`).then((r) => setLogs(r.data));
  };

  const StatusDot = ({ s }: { s: string }) => (
    <div className={`w-2 h-2 rounded-full ${s === "ok" ? "bg-green-400" : s === "down" ? "bg-red-400" : s === "not_configured" ? "bg-yellow-400" : "bg-gray-500"}`} />
  );

  if (loading && !status) return <p className="text-text-secondary p-8">Chargement...</p>;

  const services = status?.services || {};
  const caches = status?.caches || {};

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">Administration</h2>
          <p className="text-text-secondary text-sm mt-1">
            Monitoring, cache, positions, utilisateurs, logs
          </p>
        </div>
        <button onClick={refresh} className="flex items-center gap-2 px-4 py-2 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm hover:bg-gold/20 transition-colors">
          <RefreshCw size={14} /> Actualiser
        </button>
      </div>

      {actionMsg && (
        <div className="mb-4 p-3 bg-gold/10 border border-gold/20 rounded-xl text-sm text-gold">{actionMsg}</div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-card border border-border rounded-xl p-1">
        <button onClick={() => setTab("ibkr")} className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-colors ${tab === "ibkr" ? "bg-gold/10 text-gold" : "text-text-secondary hover:text-text-primary"}`}>
          <TrendingUp size={15} /> IBKR Live
        </button>
        <button onClick={() => setTab("history")} className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-colors ${tab === "history" ? "bg-gold/10 text-gold" : "text-text-secondary hover:text-text-primary"}`}>
          <FileText size={15} /> Historique
        </button>
        <button onClick={() => setTab("stats")} className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-colors ${tab === "stats" ? "bg-gold/10 text-gold" : "text-text-secondary hover:text-text-primary"}`}>
          <BarChart3 size={15} /> Alpaca Paper
        </button>
        <button onClick={() => setTab("system")} className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-colors ${tab === "system" ? "bg-gold/10 text-gold" : "text-text-secondary hover:text-text-primary"}`}>
          <Server size={15} /> Système
        </button>
      </div>

      {tab === "ibkr" && <IBKRLiveStats data={ibkrStats} />}
      {tab === "history" && <TradesHistory data={tradesHistory} />}
      {tab === "stats" && stats && <TradingStats stats={stats} />}
      {tab === "system" && <>

      {/* Export CSV */}
      <div className="bg-card border border-border rounded-xl p-4 mb-6">
        <h3 className="text-sm font-semibold mb-3">Export de données</h3>
        <div className="flex flex-wrap gap-2">
          <a href="/api/admin/export/trades-csv" className="px-3 py-1.5 bg-gold/10 text-gold border border-gold/20 rounded-lg text-xs font-semibold hover:bg-gold/20 transition-colors">
            Trades CSV
          </a>
          <a href="/api/admin/export/signals-csv" className="px-3 py-1.5 bg-gold/10 text-gold border border-gold/20 rounded-lg text-xs font-semibold hover:bg-gold/20 transition-colors">
            Signaux GO CSV
          </a>
          <a href="/api/admin/export/backtest-csv" className="px-3 py-1.5 bg-gold/10 text-gold border border-gold/20 rounded-lg text-xs font-semibold hover:bg-gold/20 transition-colors">
            Backtest CSV
          </a>
        </div>
      </div>

      {/* Services */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        {Object.entries(services).map(([name, svc]) => {
          const s = svc as ServiceStatus;
          return (
            <div key={name} className="bg-card border border-border rounded-xl p-3">
              <div className="flex items-center gap-2 mb-1">
                <StatusDot s={s.status} />
                <span className="text-xs font-semibold capitalize">{name}</span>
              </div>
              <p className="text-[10px] text-text-secondary">
                {s.status === "ok" ? (
                  name === "alpaca" ? `$${s.equity?.toLocaleString()} — ${s.positions} pos` :
                  name === "tunnel" && s.url ? s.url.replace("https://","").split(".")[0] :
                  "En ligne"
                ) : s.status === "not_configured" ? "Non configuré" : s.error || s.status}
              </p>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Caches */}
        <div className="bg-card border border-border rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold flex items-center gap-2"><HardDrive size={16} /> Caches</h3>
            <div className="flex gap-2">
              <button onClick={() => clearCache("all")} className="text-[10px] px-2 py-1 text-red-400 border border-red-400/20 rounded hover:bg-red-400/10 transition-colors">
                Tout vider
              </button>
              <button onClick={rebuildCache} className="text-[10px] px-2 py-1 text-gold border border-gold/20 rounded hover:bg-gold/10 transition-colors">
                Recalculer tout
              </button>
            </div>
          </div>
          <div className="space-y-2">
            {Object.entries(caches).map(([name, c]: [string, any]) => (
              <div key={name} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <StatusDot s={c.exists ? "ok" : "down"} />
                  <span className="font-mono text-xs">{name}</span>
                </div>
                <div className="flex items-center gap-3">
                  {c.exists ? (
                    <>
                      <span className="text-[10px] text-text-secondary">{c.size_kb} KB — {c.age_minutes < 60 ? `${c.age_minutes}m` : `${Math.round(c.age_minutes/60)}h`}</span>
                      <button onClick={() => clearCache(name)} className="text-red-400 hover:text-red-300"><Trash2 size={12} /></button>
                    </>
                  ) : (
                    <span className="text-[10px] text-red-400">absent</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Base de données */}
        <div className="bg-card border border-border rounded-xl p-5">
          <h3 className="text-sm font-semibold flex items-center gap-2 mb-4"><Database size={16} /> Base de données</h3>
          {dbStats ? (
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(dbStats).map(([key, val]) => (
                <div key={key} className="flex justify-between text-sm">
                  <span className="text-text-secondary text-xs">{key.replace(/_/g, " ")}</span>
                  <span className="font-mono text-xs">{(val as number).toLocaleString()}</span>
                </div>
              ))}
            </div>
          ) : <p className="text-text-secondary text-sm">Indisponible</p>}
          {status?.uptime_seconds && (
            <p className="text-[10px] text-text-secondary mt-3 pt-2 border-t border-border">
              Uptime : {Math.floor(status.uptime_seconds / 3600)}h {Math.floor((status.uptime_seconds % 3600) / 60)}m
            </p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Positions */}
        <div className="bg-card border border-border rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold flex items-center gap-2"><Shield size={16} /> Positions ({positions.filter(p => p.status === "OPEN").length} ouvertes)</h3>
            <button onClick={cleanPhantoms} className="text-[10px] px-2 py-1 text-yellow-400 border border-yellow-400/20 rounded hover:bg-yellow-400/10 transition-colors">
              Nettoyer fantômes
            </button>
          </div>
          <div className="space-y-1 max-h-[280px] overflow-y-auto">
            {positions.length === 0 ? <p className="text-text-secondary text-sm">Aucune position</p> : null}
            {positions.map((p) => (
              <div key={p.id} className={`flex items-center justify-between text-xs py-1.5 px-2 rounded ${p.status === "OPEN" ? "bg-surface" : ""}`}>
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${p.status === "OPEN" ? "bg-green-400" : "bg-gray-500"}`} />
                  <span className="font-mono font-semibold text-gold">{p.symbol}</span>
                  <span className={`text-[10px] ${p.direction === "LONG" ? "text-green-400" : "text-red-400"}`}>{p.direction}</span>
                  <span className="text-text-secondary">×{p.quantity}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-text-secondary">{p.status}</span>
                  {p.status === "OPEN" && (
                    <button onClick={() => closePosition(p.id)} className="text-red-400 hover:text-red-300"><Trash2 size={11} /></button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Utilisateurs */}
        <div className="bg-card border border-border rounded-xl p-5">
          <h3 className="text-sm font-semibold flex items-center gap-2 mb-4"><Users size={16} /> Utilisateurs ({users.length})</h3>
          <div className="space-y-2">
            {users.map((u: any) => (
              <div key={u.email} className="flex items-center justify-between text-sm bg-surface rounded-lg px-3 py-2">
                <div className="flex items-center gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs">{u.name}</span>
                      {u.is_admin && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-gold/10 text-gold border border-gold/20 font-semibold uppercase">Admin</span>
                      )}
                    </div>
                    <p className="text-[10px] text-text-secondary font-mono">{u.email}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-text-secondary">{u.created_at ? new Date(u.created_at).toLocaleDateString("fr-FR") : ""}</span>
                  <button
                    onClick={() => toggleAdmin(u.email, u.is_admin ?? false)}
                    className={`flex items-center gap-1 text-[10px] px-2 py-1 rounded border transition-colors ${
                      u.is_admin
                        ? "text-gold border-gold/20 bg-gold/5 hover:bg-gold/10"
                        : "text-text-secondary border-border hover:text-gold hover:border-gold/20 hover:bg-gold/5"
                    }`}
                  >
                    <Shield size={10} />
                    {u.is_admin ? "Retirer admin" : "Rendre admin"}
                  </button>
                  {u.email !== "admin@tradepilot.local" && (
                    <button onClick={() => deleteUser(u.email)} className="text-red-400 hover:text-red-300"><Trash2 size={12} /></button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Logs */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-sm font-semibold flex items-center gap-2 mb-4"><FileText size={16} /> Logs</h3>
        <div className="flex flex-wrap gap-2 mb-4">
          {logFiles.map((l: any) => (
            <button
              key={l.name}
              onClick={() => viewLog(l.name)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                logs?.name === l.name ? "bg-gold/10 text-gold border-gold/20" : "bg-surface border-border text-text-secondary hover:text-text-primary"
              }`}
            >
              {l.name} <span className="text-[10px] text-text-secondary ml-1">{l.size_kb}KB</span>
            </button>
          ))}
        </div>
        {logs && (
          <div className="bg-[#050505] rounded-lg p-4 max-h-[300px] overflow-auto font-mono text-[11px] leading-5 text-text-secondary">
            {logs.lines.map((line, i) => (
              <div key={i} className={`${line.includes("ERROR") || line.includes("error") ? "text-red-400" : line.includes("WARNING") || line.includes("warning") ? "text-yellow-400" : ""}`}>
                {line}
              </div>
            ))}
          </div>
        )}
      </div>
      </>}
    </div>
  );
}

// ============================================================
// Trading Stats Pro
// ============================================================

function TradingStats({ stats }: { stats: any }) {
  const p = stats.portfolio ?? {};
  const r = stats.ratios ?? {};
  const e = stats.exposure ?? {};
  const risk = stats.risk ?? {};
  const sectors = stats.by_sector ?? {};
  const positions = stats.positions ?? [];
  const history = stats.history ?? {};

  const pnlColor = (v: number) => v > 0 ? "text-emerald-400" : v < 0 ? "text-red-400" : "text-text-secondary";
  const pnlBg = (v: number) => v > 0 ? "bg-emerald-400" : "bg-red-400";

  return (
    <div className="space-y-6">
      {/* KPI Cards Row 1 */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        <KPI label="Equity" value={`$${(p.equity ?? 0).toLocaleString()}`} sub={`${(p.total_return ?? 0) >= 0 ? "+" : ""}${(p.total_return ?? 0).toFixed(3)}%`} subColor={pnlColor(p.total_return ?? 0)} />
        <KPI label="P/L Jour" value={`${(p.total_pnl ?? 0) >= 0 ? "+" : ""}$${(p.total_pnl ?? 0).toFixed(2)}`} valueColor={pnlColor(p.total_pnl ?? 0)} sub="Unrealized" />
        <KPI label="Cash" value={`$${(p.cash ?? 0).toLocaleString()}`} sub={`${(p.cash_pct ?? 0).toFixed(0)}% du capital`} />
        <KPI label="Win Rate" value={`${(r.win_rate ?? 0).toFixed(0)}%`} sub={`${r.winners ?? 0}W / ${r.losers ?? 0}L`} valueColor={r.win_rate >= 50 ? "text-emerald-400" : "text-red-400"} />
        <KPI label="Profit Factor" value={`${r.profit_factor === Infinity ? "∞" : r.profit_factor ?? "—"}`} sub="Gain / Perte" valueColor={r.profit_factor > 1 ? "text-emerald-400" : "text-red-400"} />
        <KPI label="Risk:Reward" value={`1:${r.risk_reward === Infinity ? "∞" : r.risk_reward ?? "—"}`} sub={`Exp. $${(r.expectancy ?? 0).toFixed(2)}/trade`} valueColor={r.risk_reward > 1 ? "text-emerald-400" : "text-red-400"} />
      </div>

      {/* Risk + Exposure */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Risk Score */}
        <div className="bg-card border border-border rounded-xl p-5">
          <h3 className="text-sm font-semibold flex items-center gap-2 mb-4">
            <AlertTriangle size={16} /> Score de Risque
          </h3>
          <div className="flex items-center gap-4 mb-4">
            <div className={`text-4xl font-mono font-bold ${
              risk.level === "FAIBLE" ? "text-emerald-400" : risk.level === "MODÉRÉ" ? "text-yellow-400" : risk.level === "ÉLEVÉ" ? "text-orange-400" : "text-red-500"
            }`}>{risk.score ?? 0}</div>
            <div>
              <span className={`text-xs px-2 py-1 rounded font-semibold ${
                risk.level === "FAIBLE" ? "bg-emerald-400/10 text-emerald-400" : risk.level === "MODÉRÉ" ? "bg-yellow-400/10 text-yellow-400" : risk.level === "ÉLEVÉ" ? "bg-orange-400/10 text-orange-400" : "bg-red-500/10 text-red-500"
              }`}>{risk.level}</span>
            </div>
          </div>
          {(risk.flags ?? []).length > 0 ? (
            <div className="space-y-1">
              {risk.flags.map((f: string, i: number) => (
                <p key={i} className="text-xs text-yellow-400 flex items-center gap-1.5">
                  <span className="w-1 h-1 rounded-full bg-yellow-400" />{f}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-xs text-emerald-400">Aucun signal de risque</p>
          )}
        </div>

        {/* Exposure */}
        <div className="bg-card border border-border rounded-xl p-5">
          <h3 className="text-sm font-semibold flex items-center gap-2 mb-4">
            <Activity size={16} /> Exposition
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-text-secondary">Long</span>
              <span className="font-mono text-emerald-400">${(e.long ?? 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-text-secondary">Short</span>
              <span className="font-mono text-red-400">${(e.short ?? 0).toLocaleString()}</span>
            </div>
            <div className="border-t border-border pt-2 flex justify-between text-sm">
              <span className="text-text-secondary">Net</span>
              <span className="font-mono font-semibold">{(e.net_pct ?? 0).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-text-secondary">Positions</span>
              <span className="font-mono">{e.n_positions ?? 0} / {e.max_positions ?? 10}</span>
            </div>
            {/* Bar progression */}
            <div className="h-2 bg-surface rounded-full overflow-hidden">
              <div className="h-full bg-gold rounded-full transition-all" style={{ width: `${((e.n_positions ?? 0) / (e.max_positions ?? 10)) * 100}%` }} />
            </div>
            <div className="flex justify-between text-[10px]">
              <span className="text-text-secondary">Concentration : {e.concentration}</span>
              <span className="text-text-secondary">HHI: {(e.herfindahl ?? 0).toFixed(3)}</span>
            </div>
          </div>
        </div>

        {/* Best / Worst */}
        <div className="bg-card border border-border rounded-xl p-5">
          <h3 className="text-sm font-semibold flex items-center gap-2 mb-4">
            <Flame size={16} /> Best & Worst
          </h3>
          <div className="space-y-4">
            <div className="bg-emerald-400/5 border border-emerald-400/10 rounded-lg p-3">
              <p className="text-[10px] text-emerald-400 uppercase tracking-wider mb-1">Meilleur trade</p>
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-emerald-400">{r.best_trade?.symbol ?? "—"}</span>
                <div className="text-right">
                  <span className="font-mono text-emerald-400 text-sm">+${(r.best_trade?.pnl ?? 0).toFixed(2)}</span>
                  <p className="text-[10px] text-emerald-400/60">+{(r.best_trade?.pnl_pct ?? 0).toFixed(2)}%</p>
                </div>
              </div>
            </div>
            <div className="bg-red-400/5 border border-red-400/10 rounded-lg p-3">
              <p className="text-[10px] text-red-400 uppercase tracking-wider mb-1">Pire trade</p>
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-red-400">{r.worst_trade?.symbol ?? "—"}</span>
                <div className="text-right">
                  <span className="font-mono text-red-400 text-sm">${(r.worst_trade?.pnl ?? 0).toFixed(2)}</span>
                  <p className="text-[10px] text-red-400/60">{(r.worst_trade?.pnl_pct ?? 0).toFixed(2)}%</p>
                </div>
              </div>
            </div>
            <div className="pt-2 border-t border-border text-xs text-text-secondary">
              <div className="flex justify-between"><span>Gain moyen</span><span className="font-mono text-emerald-400">${(r.avg_win ?? 0).toFixed(2)}</span></div>
              <div className="flex justify-between"><span>Perte moyenne</span><span className="font-mono text-red-400">-${(r.avg_loss ?? 0).toFixed(2)}</span></div>
            </div>
          </div>
        </div>
      </div>

      {/* Sector Breakdown */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-sm font-semibold flex items-center gap-2 mb-4">
          <PieChart size={16} /> Performance par secteur
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.entries(sectors).map(([sector, data]: [string, any]) => (
            <div key={sector} className="bg-surface rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold">{sector}</span>
                <span className={`text-xs font-mono font-bold ${pnlColor(data.pnl)}`}>
                  {data.pnl >= 0 ? "+" : ""}${data.pnl.toFixed(2)}
                </span>
              </div>
              {/* Weight bar */}
              <div className="h-1.5 bg-background rounded-full overflow-hidden mb-2">
                <div className={`h-full rounded-full ${pnlBg(data.pnl)}`} style={{ width: `${Math.min(data.weight, 100)}%` }} />
              </div>
              <div className="flex justify-between text-[10px] text-text-secondary mb-2">
                <span>{data.count} position{data.count > 1 ? "s" : ""}</span>
                <span>{data.weight}% du portefeuille</span>
              </div>
              {/* Positions dans le secteur */}
              <div className="space-y-1">
                {(data.positions ?? []).map((pos: any) => (
                  <div key={pos.symbol} className="flex items-center justify-between text-xs">
                    <span className="font-mono text-gold">{pos.symbol}</span>
                    <span className={`font-mono ${pnlColor(pos.pnl)}`}>{pos.pnl >= 0 ? "+" : ""}{pos.pnl_pct.toFixed(2)}%</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Positions Heatmap */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-sm font-semibold flex items-center gap-2 mb-4">
          <TrendingUp size={16} /> Positions — Heatmap P/L
        </h3>
        <div className="flex flex-wrap gap-2">
          {positions.map((pos: any) => {
            const intensity = Math.min(Math.abs(pos.pnl_pct) * 20, 100);
            const bg = pos.pnl >= 0
              ? `rgba(52, 211, 153, ${intensity / 100 * 0.3 + 0.05})`
              : `rgba(248, 113, 113, ${intensity / 100 * 0.3 + 0.05})`;
            const border = pos.pnl >= 0
              ? `rgba(52, 211, 153, ${intensity / 100 * 0.4 + 0.1})`
              : `rgba(248, 113, 113, ${intensity / 100 * 0.4 + 0.1})`;
            return (
              <div key={pos.symbol} className="rounded-xl p-3 min-w-[120px] transition-transform hover:scale-105" style={{ backgroundColor: bg, border: `1px solid ${border}` }}>
                <div className="font-mono font-bold text-sm">{pos.symbol}</div>
                <div className={`font-mono text-lg font-bold ${pnlColor(pos.pnl)}`}>
                  {pos.pnl >= 0 ? "+" : ""}{pos.pnl_pct.toFixed(2)}%
                </div>
                <div className="text-[10px] text-text-secondary">${pos.market_value.toLocaleString()} — {pos.weight}%</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* History footer */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KPI label="Trades fermés" value={String(history.closed_trades ?? 0)} sub={`WR: ${(history.closed_win_rate ?? 0).toFixed(0)}%`} />
        <KPI label="Ordres totaux" value={String(history.total_orders ?? 0)} sub={`Fill rate: ${(history.fill_rate ?? 0).toFixed(0)}%`} />
        <KPI label="Invested" value={`$${(p.invested ?? 0).toLocaleString()}`} sub={`${((p.invested ?? 0) / (p.equity ?? 100000) * 100).toFixed(0)}% déployé`} />
        <KPI label="Capital initial" value={`$${(p.initial_capital ?? 100000).toLocaleString()}`} sub={`Return: ${(p.total_return ?? 0) >= 0 ? "+" : ""}${(p.total_return ?? 0).toFixed(3)}%`} subColor={pnlColor(p.total_return ?? 0)} />
      </div>
    </div>
  );
}

// ============================================================
// Trades History — Historique professionnel
// ============================================================

function TradesHistory({ data }: { data: any }) {
  const [filter, setFilter] = useState<"all" | "open" | "closed" | "wins" | "losses">("all");
  const [brokerFilter, setBrokerFilter] = useState<"all" | "alpaca" | "ibkr" | "local">("all");
  const pnlColor = (v: number) => v > 0 ? "text-emerald-400" : v < 0 ? "text-red-400" : "text-text-secondary";

  if (!data) return <p className="text-text-secondary p-8 text-center">Chargement...</p>;

  const trades = data.trades ?? [];
  const summary = data.summary ?? {};

  const filtered = trades.filter((t: any) => {
    // Filtre statut
    if (filter === "open" && t.status !== "OPEN") return false;
    if (filter === "closed" && t.status !== "CLOSED") return false;
    if (filter === "wins" && !(t.status === "CLOSED" && t.pnl > 0)) return false;
    if (filter === "losses" && !(t.status === "CLOSED" && t.pnl < 0)) return false;
    // Filtre broker
    if (brokerFilter !== "all" && t.broker !== brokerFilter) return false;
    return true;
  });

  // Stats par broker
  const brokerCounts = { alpaca: 0, ibkr: 0, local: 0 };
  trades.forEach((t: any) => { if (t.broker in brokerCounts) (brokerCounts as any)[t.broker]++; });

  return (
    <div className="space-y-6">
      {/* KPIs résumé */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        <KPI label="Total trades" value={String(summary.total ?? 0)} sub={`${summary.open ?? 0} ouvertes`} />
        <KPI label="Fermées" value={String(summary.closed ?? 0)} sub={`${summary.wins ?? 0}W / ${summary.losses ?? 0}L`} />
        <KPI label="Win Rate" value={`${(summary.win_rate ?? 0).toFixed(0)}%`} valueColor={(summary.win_rate ?? 0) >= 50 ? "text-emerald-400" : "text-red-400"} sub="Trades fermés" />
        <KPI label="P/L Total" value={`$${(summary.total_pnl ?? 0).toFixed(2)}`} valueColor={pnlColor(summary.total_pnl ?? 0)} sub="Trades fermés" />
        <KPI label="Gain moyen" value={`$${(summary.avg_win ?? 0).toFixed(2)}`} valueColor="text-emerald-400" sub="Par trade gagnant" />
        <KPI label="Perte moyenne" value={`$${(summary.avg_loss ?? 0).toFixed(2)}`} valueColor="text-red-400" sub="Par trade perdant" />
        <KPI label="Meilleur" value={summary.best_trade?.symbol ?? "—"} sub={`$${(summary.best_trade?.pnl ?? 0).toFixed(2)}`} subColor="text-emerald-400" />
      </div>

      {/* Filtres statut */}
      <div className="flex gap-1 bg-card border border-border rounded-xl p-1">
        {([
          ["all", `Tous (${trades.length})`],
          ["open", `Ouvertes (${trades.filter((t: any) => t.status === "OPEN").length})`],
          ["closed", `Fermées (${summary.closed ?? 0})`],
          ["wins", `Gains (${summary.wins ?? 0})`],
          ["losses", `Pertes (${summary.losses ?? 0})`],
        ] as const).map(([f, label]) => (
          <button key={f} onClick={() => setFilter(f as any)} className={`flex-1 py-2 rounded-lg text-xs font-medium transition-colors ${
            filter === f ? "bg-gold/10 text-gold" : "text-text-secondary hover:text-text-primary"
          }`}>{label}</button>
        ))}
      </div>

      {/* Filtres broker */}
      <div className="flex gap-2">
        {([
          ["all", `Tous`, "text-gold border-gold/20 bg-gold/10"],
          ["alpaca", `Alpaca (${brokerCounts.alpaca})`, "text-emerald-400 border-emerald-400/20 bg-emerald-400/10"],
          ["ibkr", `IBKR (${brokerCounts.ibkr})`, "text-blue-400 border-blue-400/20 bg-blue-400/10"],
          ["local", `Local (${brokerCounts.local})`, "text-text-secondary border-border bg-surface"],
        ] as const).map(([f, label, activeStyle]) => (
          <button key={f} onClick={() => setBrokerFilter(f as any)} className={`text-[10px] px-3 py-1.5 rounded-lg border font-semibold transition-colors ${
            brokerFilter === f ? activeStyle : "text-text-secondary border-border hover:text-text-primary"
          }`}>{label}</button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border bg-surface/50">
                <th className="text-left py-3 px-3 font-medium text-text-secondary">Actif</th>
                <th className="text-left py-3 px-2 font-medium text-text-secondary">Dir.</th>
                <th className="text-left py-3 px-2 font-medium text-text-secondary">Statut</th>
                <th className="text-right py-3 px-2 font-medium text-text-secondary">Entry</th>
                <th className="text-right py-3 px-2 font-medium text-text-secondary">Exit/Current</th>
                <th className="text-right py-3 px-2 font-medium text-text-secondary">SL</th>
                <th className="text-right py-3 px-2 font-medium text-text-secondary">TP</th>
                <th className="text-right py-3 px-2 font-medium text-text-secondary">Qty</th>
                <th className="text-right py-3 px-2 font-medium text-text-secondary">P/L</th>
                <th className="text-right py-3 px-2 font-medium text-text-secondary">P/L%</th>
                <th className="text-left py-3 px-2 font-medium text-text-secondary">Ouverture</th>
                <th className="text-left py-3 px-2 font-medium text-text-secondary">Fermeture</th>
                <th className="text-left py-3 px-2 font-medium text-text-secondary">Durée</th>
                <th className="text-left py-3 px-2 font-medium text-text-secondary">Raison</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t: any) => (
                <tr key={t.id} className={`border-b border-border/30 hover:bg-surface/30 transition-colors ${
                  t.status === "OPEN" ? "bg-gold/[0.02]" : ""
                }`}>
                  <td className="py-2.5 px-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-gold">{t.symbol}</span>
                      <span className={`text-[8px] px-1 py-0.5 rounded font-semibold ${
                        t.broker === "alpaca" ? "text-emerald-400 bg-emerald-400/10" :
                        t.broker === "ibkr" ? "text-blue-400 bg-blue-400/10" :
                        "text-text-secondary bg-surface"
                      }`}>{t.broker === "alpaca" ? "ALP" : t.broker === "ibkr" ? "IBKR" : "LOC"}</span>
                    </div>
                  </td>
                  <td className="py-2.5 px-2">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold ${
                      t.direction === "LONG" ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/20" : "text-red-400 bg-red-400/10 border-red-400/20"
                    }`}>{t.direction}</span>
                  </td>
                  <td className="py-2.5 px-2">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold ${
                      t.result === "WIN" ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/20" :
                      t.result === "LOSS" ? "text-red-400 bg-red-400/10 border-red-400/20" :
                      t.result === "OPEN" ? "text-gold bg-gold/10 border-gold/20" :
                      "text-text-secondary bg-surface border-border"
                    }`}>{t.result === "OPEN" ? "EN COURS" : t.result}</span>
                  </td>
                  <td className="py-2.5 px-2 text-right font-mono">${t.entry_price}</td>
                  <td className="py-2.5 px-2 text-right font-mono">{t.exit_price ? `$${t.exit_price}` : t.current_price ? <span className="text-text-secondary">${t.current_price}</span> : "—"}</td>
                  <td className="py-2.5 px-2 text-right font-mono text-red-400">{t.stop_loss ? `$${t.stop_loss}` : "—"}</td>
                  <td className="py-2.5 px-2 text-right font-mono text-emerald-400">{t.take_profit ? `$${t.take_profit}` : "—"}</td>
                  <td className="py-2.5 px-2 text-right font-mono">{t.quantity}</td>
                  <td className={`py-2.5 px-2 text-right font-mono font-bold ${pnlColor(t.pnl)}`}>${t.pnl >= 0 ? "+" : ""}{t.pnl}</td>
                  <td className={`py-2.5 px-2 text-right font-mono ${pnlColor(t.pnl_pct)}`}>{t.pnl_pct >= 0 ? "+" : ""}{t.pnl_pct}%</td>
                  <td className="py-2.5 px-2 text-text-secondary">{t.opened_at ? new Date(t.opened_at).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "—"}</td>
                  <td className="py-2.5 px-2 text-text-secondary">{t.closed_at ? new Date(t.closed_at).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "—"}</td>
                  <td className="py-2.5 px-2 text-text-secondary">{t.duration ?? "—"}</td>
                  <td className="py-2.5 px-2">
                    {t.close_reason && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        t.close_reason === "Take Profit" ? "bg-emerald-400/10 text-emerald-400" :
                        t.close_reason === "Stop Loss" ? "bg-red-400/10 text-red-400" :
                        "bg-surface text-text-secondary"
                      }`}>{t.close_reason}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <p className="text-text-secondary text-sm text-center py-8">Aucun trade dans ce filtre</p>
        )}
      </div>
    </div>
  );
}


// ============================================================
// IBKR Live Stats — Argent réel
// ============================================================

function IBKRLiveStats({ data }: { data: any }) {
  const pnlColor = (v: number) => v > 0 ? "text-emerald-400" : v < 0 ? "text-red-400" : "text-text-secondary";
  const pnlBg = (v: number) => v > 0 ? "bg-emerald-400" : "bg-red-400";

  if (!data) {
    return (
      <div className="bg-card border border-border rounded-xl p-8 text-center">
        <Landmark size={32} className="mx-auto text-text-secondary mb-3" />
        <p className="text-text-secondary">Chargement des données IBKR...</p>
      </div>
    );
  }

  if (data.status === "not_configured") {
    return (
      <div className="bg-card border border-border rounded-xl p-8 text-center">
        <Landmark size={32} className="mx-auto text-yellow-400 mb-3" />
        <p className="text-lg font-semibold mb-2">IBKR non configuré</p>
        <p className="text-text-secondary text-sm mb-4">{data.message}</p>
        <div className="bg-surface rounded-xl p-4 text-left max-w-md mx-auto">
          <p className="text-xs font-semibold mb-2">Pour activer :</p>
          <ol className="text-xs text-text-secondary space-y-1 list-decimal pl-4">
            <li>Créez un compte sur <span className="text-gold">interactivebrokers.co.uk</span></li>
            <li>Installez IB Gateway sur votre Mac</li>
            <li>Ajoutez <code className="text-gold bg-surface px-1 rounded">IBKR_ACCOUNT_ID=xxx</code> dans <code>.env</code></li>
            <li>Changez <code className="text-gold bg-surface px-1 rounded">IBKR_PORT=7496</code> pour le live</li>
          </ol>
        </div>
      </div>
    );
  }

  if (data.status === "disconnected") {
    return (
      <div className="bg-card border border-border rounded-xl p-8 text-center">
        <Landmark size={32} className="mx-auto text-red-400 mb-3" />
        <p className="text-lg font-semibold mb-2">IBKR déconnecté</p>
        <p className="text-text-secondary text-sm">{data.message}</p>
      </div>
    );
  }

  if (data.status !== "connected") {
    return (
      <div className="bg-card border border-border rounded-xl p-8 text-center">
        <Landmark size={32} className="mx-auto text-red-400 mb-3" />
        <p className="text-text-secondary">{data.message || "Erreur IBKR"}</p>
      </div>
    );
  }

  const a = data.account ?? {};
  const r = data.ratios ?? {};
  const e = data.exposure ?? {};
  const positions = data.positions ?? [];
  const totalPnl = positions.reduce((s: number, p: any) => s + (p.pnl || 0), 0);
  const investedTotal = positions.reduce((s: number, p: any) => s + (p.market_value || 0), 0);

  return (
    <div className="space-y-5">
      {/* Header Pro */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-400/10 border border-emerald-400/20 rounded-lg">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-semibold text-emerald-400">LIVE</span>
          </div>
          <div>
            <span className="text-sm font-semibold">Interactive Brokers</span>
            <span className="text-[10px] text-text-secondary ml-2">U25304486 — {a.currency || "EUR"}</span>
          </div>
        </div>
        <div className="text-right">
          <p className={`text-3xl font-mono font-bold ${pnlColor(totalPnl)}`}>€{(a.equity ?? 0).toFixed(2)}</p>
          <p className={`text-xs font-mono ${pnlColor(totalPnl)}`}>{totalPnl >= 0 ? "+" : ""}€{totalPnl.toFixed(2)}{a.initial_capital ? ` (${((a.equity / a.initial_capital) * 100 - 100).toFixed(2)}%)` : ""}</p>
        </div>
      </div>

      {/* KPI Row 1 — Capital */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-card border border-border rounded-xl p-3">
          <p className="text-[10px] text-text-secondary uppercase tracking-wider">Investi</p>
          <p className="text-lg font-mono font-bold">€{investedTotal.toFixed(0)}</p>
          <div className="h-1 bg-surface rounded-full mt-2 overflow-hidden">
            <div className="h-full bg-gold rounded-full" style={{ width: `${Math.min((investedTotal / (a.equity || 1)) * 100, 100)}%` }} />
          </div>
        </div>
        <div className="bg-card border border-border rounded-xl p-3">
          <p className="text-[10px] text-text-secondary uppercase tracking-wider">Cash</p>
          <p className="text-lg font-mono font-bold">€{(a.cash ?? 0).toFixed(2)}</p>
          <p className="text-[10px] text-text-secondary mt-1">{(a.cash_pct ?? 0).toFixed(0)}% disponible</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-3">
          <p className="text-[10px] text-text-secondary uppercase tracking-wider">Positions</p>
          <p className="text-lg font-mono font-bold text-gold">{positions.length}</p>
          <p className="text-[10px] text-text-secondary mt-1">{positions.filter((p: any) => p.pnl > 0).length}W / {positions.filter((p: any) => p.pnl < 0).length}L</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-3">
          <p className="text-[10px] text-text-secondary uppercase tracking-wider">Initial</p>
          <p className="text-lg font-mono font-bold">{a.initial_capital ? `€${a.initial_capital.toFixed(0)}` : "N/A"}</p>
          {a.initial_capital ? (
            <p className={`text-[10px] mt-1 ${pnlColor((a.equity ?? 0) - a.initial_capital)}`}>{((a.equity ?? 0) - a.initial_capital) >= 0 ? "+" : ""}€{((a.equity ?? 0) - a.initial_capital).toFixed(2)}</p>
          ) : (
            <p className="text-[10px] mt-1 text-text-secondary">Non défini</p>
          )}
        </div>
      </div>

      {/* Positions — Table Pro */}
      {positions.length > 0 && (
        <div className="bg-card border border-border rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-border flex items-center justify-between">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <TrendingUp size={14} /> Positions Live
            </h3>
            <span className="text-[10px] text-text-secondary">{positions.length} ouvertes — €{investedTotal.toFixed(0)} investis</span>
          </div>
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border/50 bg-surface/30">
                <th className="text-left py-2.5 px-4 font-medium text-text-secondary">Actif</th>
                <th className="text-right py-2.5 px-3 font-medium text-text-secondary">Qty</th>
                <th className="text-right py-2.5 px-3 font-medium text-text-secondary">Entry</th>
                <th className="text-right py-2.5 px-3 font-medium text-text-secondary">Current</th>
                <th className="text-right py-2.5 px-3 font-medium text-text-secondary">P/L €</th>
                <th className="text-right py-2.5 px-3 font-medium text-text-secondary">P/L %</th>
                <th className="text-right py-2.5 px-3 font-medium text-text-secondary">Valeur</th>
                <th className="text-right py-2.5 px-4 font-medium text-text-secondary">Poids</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos: any) => (
                <tr key={pos.symbol} className="border-b border-border/20 hover:bg-surface/30 transition-colors">
                  <td className="py-2.5 px-4">
                    <div className="flex items-center gap-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${pos.pnl >= 0 ? "bg-emerald-400" : "bg-red-400"}`} />
                      <span className="font-mono font-bold text-gold">{pos.symbol}</span>
                      <span className={`text-[9px] px-1 py-0.5 rounded font-semibold ${pos.side === "long" ? "text-emerald-400 bg-emerald-400/10" : "text-red-400 bg-red-400/10"}`}>
                        {pos.side === "long" ? "L" : "S"}
                      </span>
                    </div>
                    <p className="text-[9px] text-text-secondary mt-0.5">{pos.sector}</p>
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono">{pos.quantity}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-text-secondary">${(pos.entry ?? pos.entry_price ?? 0).toFixed(2)}</td>
                  <td className="py-2.5 px-3 text-right font-mono">${(pos.current ?? pos.current_price ?? 0).toFixed(2)}</td>
                  <td className={`py-2.5 px-3 text-right font-mono font-bold ${pnlColor(pos.pnl)}`}>
                    {pos.pnl >= 0 ? "+" : ""}€{(pos.pnl ?? 0).toFixed(2)}
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <span className={`font-mono font-bold px-1.5 py-0.5 rounded ${
                      pos.pnl_pct > 0 ? "text-emerald-400 bg-emerald-400/10" : pos.pnl_pct < 0 ? "text-red-400 bg-red-400/10" : "text-text-secondary"
                    }`}>
                      {pos.pnl_pct >= 0 ? "+" : ""}{(pos.pnl_pct ?? 0).toFixed(2)}%
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono">€{(pos.market_value ?? 0).toFixed(0)}</td>
                  <td className="py-2.5 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-12 h-1.5 bg-surface rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${pos.pnl >= 0 ? "bg-emerald-400" : "bg-red-400"}`} style={{ width: `${Math.min(pos.weight || 0, 100)}%` }} />
                      </div>
                      <span className="text-[10px] font-mono text-text-secondary w-8 text-right">{(pos.weight ?? 0).toFixed(0)}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t border-border bg-surface/20">
                <td className="py-2.5 px-4 font-semibold text-xs" colSpan={4}>Total</td>
                <td className={`py-2.5 px-3 text-right font-mono font-bold ${pnlColor(totalPnl)}`}>
                  {totalPnl >= 0 ? "+" : ""}€{totalPnl.toFixed(2)}
                </td>
                <td className={`py-2.5 px-3 text-right font-mono font-bold ${pnlColor(totalPnl)}`}>
                  {totalPnl >= 0 ? "+" : ""}{investedTotal > 0 ? (totalPnl / investedTotal * 100).toFixed(2) : "0.00"}%
                </td>
                <td className="py-2.5 px-3 text-right font-mono font-bold">€{investedTotal.toFixed(0)}</td>
                <td className="py-2.5 px-4 text-right font-mono text-text-secondary text-[10px]">100%</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}

      {/* Heatmap Visuelle */}
      {positions.length > 0 && (
        <div className="bg-card border border-border rounded-xl p-4">
          <h3 className="text-xs font-semibold text-text-secondary mb-3 uppercase tracking-wider">Heatmap P/L</h3>
          <div className="flex flex-wrap gap-2">
            {positions.map((pos: any) => {
              const intensity = Math.min(Math.abs(pos.pnl_pct || 0) * 20, 100);
              const bg = (pos.pnl || 0) >= 0
                ? `rgba(52, 211, 153, ${intensity / 100 * 0.4 + 0.05})`
                : `rgba(248, 113, 113, ${intensity / 100 * 0.4 + 0.05})`;
              const bd = (pos.pnl || 0) >= 0
                ? `rgba(52, 211, 153, ${intensity / 100 * 0.5 + 0.1})`
                : `rgba(248, 113, 113, ${intensity / 100 * 0.5 + 0.1})`;
              return (
                <div key={pos.symbol} className="rounded-xl p-3 min-w-[100px] transition-all hover:scale-105 cursor-default" style={{ backgroundColor: bg, border: `1px solid ${bd}` }}>
                  <div className="font-mono font-bold text-xs">{pos.symbol}</div>
                  <div className={`font-mono text-base font-bold ${pnlColor(pos.pnl || 0)}`}>
                    {(pos.pnl || 0) >= 0 ? "+" : ""}{(pos.pnl_pct || 0).toFixed(1)}%
                  </div>
                  <div className="text-[9px] text-text-secondary">€{(pos.market_value || 0).toFixed(0)}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Allocation Sectorielle */}
      {positions.length > 0 && (() => {
        const sectors: Record<string, { value: number; pnl: number; count: number }> = {};
        positions.forEach((p: any) => {
          const sec = p.sector || "Autre";
          if (!sectors[sec]) sectors[sec] = { value: 0, pnl: 0, count: 0 };
          sectors[sec].value += p.market_value || 0;
          sectors[sec].pnl += p.pnl || 0;
          sectors[sec].count++;
        });
        return (
          <div className="bg-card border border-border rounded-xl p-4">
            <h3 className="text-xs font-semibold text-text-secondary mb-3 uppercase tracking-wider">Allocation Sectorielle</h3>
            <div className="space-y-2">
              {Object.entries(sectors).sort((a, b) => b[1].value - a[1].value).map(([sec, d]) => {
                const pct = investedTotal > 0 ? (d.value / investedTotal * 100) : 0;
                return (
                  <div key={sec} className="flex items-center gap-3">
                    <span className="text-xs w-16 text-text-secondary truncate">{sec}</span>
                    <div className="flex-1 h-2 bg-surface rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${d.pnl >= 0 ? "bg-emerald-400" : "bg-red-400"}`} style={{ width: `${pct}%` }} />
                    </div>
                    <span className="text-[10px] font-mono w-10 text-right">{pct.toFixed(0)}%</span>
                    <span className={`text-[10px] font-mono w-14 text-right ${pnlColor(d.pnl)}`}>{d.pnl >= 0 ? "+" : ""}€{d.pnl.toFixed(1)}</span>
                    <span className="text-[10px] text-text-secondary w-6 text-right">{d.count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })()}

      {/* Best / Worst */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-emerald-400/5 border border-emerald-400/10 rounded-xl p-4">
          <p className="text-[10px] text-emerald-400 uppercase tracking-wider mb-2">Meilleur trade</p>
          {positions.length > 0 ? (() => {
            const best = [...positions].sort((a: any, b: any) => (b.pnl || 0) - (a.pnl || 0))[0];
            return (
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-mono font-bold text-lg text-emerald-400">{best?.symbol}</span>
                  <p className="text-[10px] text-text-secondary">{best?.sector}</p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-lg font-bold text-emerald-400">+€{(best?.pnl || 0).toFixed(2)}</p>
                  <p className="text-[10px] text-emerald-400/60">+{(best?.pnl_pct || 0).toFixed(2)}%</p>
                </div>
              </div>
            );
          })() : <p className="text-text-secondary text-xs">—</p>}
        </div>
        <div className="bg-red-400/5 border border-red-400/10 rounded-xl p-4">
          <p className="text-[10px] text-red-400 uppercase tracking-wider mb-2">Pire trade</p>
          {positions.length > 0 ? (() => {
            const worst = [...positions].sort((a: any, b: any) => (a.pnl || 0) - (b.pnl || 0))[0];
            return (
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-mono font-bold text-lg text-red-400">{worst?.symbol}</span>
                  <p className="text-[10px] text-text-secondary">{worst?.sector}</p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-lg font-bold text-red-400">€{(worst?.pnl || 0).toFixed(2)}</p>
                  <p className="text-[10px] text-red-400/60">{(worst?.pnl_pct || 0).toFixed(2)}%</p>
                </div>
              </div>
            );
          })() : <p className="text-text-secondary text-xs">—</p>}
        </div>
      </div>

      {/* Protection Status */}
      <div className="bg-card border border-border rounded-xl p-4">
        <h3 className="text-xs font-semibold text-text-secondary mb-3 uppercase tracking-wider">Protection Automatique</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-surface rounded-lg p-3 text-center">
            <Shield size={16} className="mx-auto text-emerald-400 mb-1" />
            <p className="text-[10px] text-text-secondary">Stop Loss</p>
            <p className="text-xs font-semibold text-emerald-400">2×ATR</p>
          </div>
          <div className="bg-surface rounded-lg p-3 text-center">
            <TrendingUp size={16} className="mx-auto text-gold mb-1" />
            <p className="text-[10px] text-text-secondary">Take Profit</p>
            <p className="text-xs font-semibold text-gold">3×ATR</p>
          </div>
          <div className="bg-surface rounded-lg p-3 text-center">
            <Activity size={16} className="mx-auto text-blue-400 mb-1" />
            <p className="text-[10px] text-text-secondary">Trailing Stop</p>
            <p className="text-xs font-semibold text-blue-400">Dynamique</p>
          </div>
          <div className="bg-surface rounded-lg p-3 text-center">
            <AlertTriangle size={16} className="mx-auto text-yellow-400 mb-1" />
            <p className="text-[10px] text-text-secondary">Essoufflement</p>
            <p className="text-xs font-semibold text-yellow-400">Auto-close</p>
          </div>
        </div>
        <p className="text-[10px] text-text-secondary text-center mt-3">Vérifié toutes les 5 minutes pendant les heures de marché US (15h30-22h Paris)</p>
      </div>

      {positions.length === 0 && (
        <div className="bg-card border border-border rounded-xl p-8 text-center">
          <DollarSign size={32} className="mx-auto text-text-secondary mb-3" />
          <p className="text-text-secondary">Aucune position ouverte sur IBKR</p>
          <p className="text-xs text-text-secondary mt-1">Les trades s'ouvriront automatiquement quand le pipeline détectera des signaux GO</p>
        </div>
      )}
    </div>
  );
}


function KPI({ label, value, sub, valueColor, subColor }: {
  label: string; value: string; sub?: string; valueColor?: string; subColor?: string;
}) {
  return (
    <div className="bg-card border border-border rounded-xl p-3">
      <p className="text-[10px] text-text-secondary uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-xl font-mono font-bold ${valueColor || "text-text-primary"}`}>{value}</p>
      {sub && <p className={`text-[10px] mt-0.5 ${subColor || "text-text-secondary"}`}>{sub}</p>}
    </div>
  );
}
