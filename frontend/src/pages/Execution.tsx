import { useEffect, useState } from "react";
import { Play, Square, RefreshCw, Zap, AlertTriangle, X } from "lucide-react";
import api, {
  executionApi,
  scoringApi,
  type OpenPosition,
  type TradeThesis,
  type ExecutionResult,
} from "../services/api";
import InfoCard from "../components/ui/InfoCard";

const BIAS_STYLES: Record<string, string> = {
  OK: "text-gold bg-gold/10",
  WARNING: "text-yellow-400 bg-yellow-400/10",
  BLOCK: "text-red-400 bg-red-400/10",
};

export default function Execution() {
  const [positions, setPositions] = useState<OpenPosition[]>([]);
  const [signals, setSignals] = useState<TradeThesis[]>([]);
  const [brokerStatus, setBrokerStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState<string | null>(null);
  const [executingAll, setExecutingAll] = useState(false);
  const [lastResult, setLastResult] = useState<ExecutionResult | null>(null);
  const [allResults, setAllResults] = useState<any>(null);
  const [closing, setClosing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [posFilter, setPosFilter] = useState<"all" | "alpaca" | "ibkr" | "local">("all");
  const [healthData, setHealthData] = useState<any[]>([]);
  const [queueData, setQueueData] = useState<any>(null);
  const [arbiter, setArbiter] = useState<any>(null);

  const loadData = async () => {
    setLoading(true);

    // 1. Broker status (rapide, timeout 5s)
    try {
      const brokerRes = await api.get("/broker/status", { timeout: 5000 });
      setBrokerStatus(brokerRes.data);
    } catch {
      setBrokerStatus(null);
    }

    // 2. Positions (rapide)
    try {
      const posRes = await executionApi.getPositions();
      setPositions(Array.isArray(posRes.data) ? posRes.data : []);
    } catch {
      setPositions([]);
    }

    // 3. Signaux (peut être lent)
    try {
      const sigRes = await scoringApi.getSignals();
      setSignals(Array.isArray(sigRes.data) ? sigRes.data : []);
    } catch {
      setSignals([]);
    }

    // 4. Health check
    try {
      const healthRes = await api.get("/execution/health-check", { timeout: 15000 });
      setHealthData(Array.isArray(healthRes.data) ? healthRes.data : []);
    } catch {
      setHealthData([]);
    }

    // 5. Queue
    try {
      const queueRes = await api.get("/execution/queue", { timeout: 5000 });
      setQueueData(queueRes.data);
    } catch {
      setQueueData(null);
    }

    // 6. Opportunity Arbiter
    try {
      const arbRes = await api.get("/execution/opportunity-arbiter", { timeout: 30000 });
      setArbiter(arbRes.data);
    } catch {
      setArbiter(null);
    }

    setLoading(false);
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh P/L toutes les 30s
    return () => clearInterval(interval);
  }, []);

  const showError = (e: any) => {
    const msg = e.response?.data?.detail || e.message || "Erreur";
    setError(msg);
    setTimeout(() => setError(null), 5000);
  };

  const handleExecute = (symbol: string) => {
    setExecuting(symbol);
    executionApi
      .execute(symbol)
      .then((res) => {
        setLastResult(res.data);
        loadData();
      })
      .catch(showError)
      .finally(() => setExecuting(null));
  };

  const handleExecuteAll = () => {
    setExecutingAll(true);
    setAllResults(null);
    executionApi
      .executeAll()
      .then((res) => {
        setAllResults(res.data);
        loadData();
      })
      .catch(showError)
      .finally(() => setExecutingAll(false));
  };

  const handleClosePosition = (symbol: string) => {
    if (!confirm(`Fermer la position ${symbol} ? L'ordre sera envoyé au broker.`)) return;
    setClosing(symbol);
    api.post(`/execution/close/${symbol}`)
      .then(() => loadData())
      .catch(showError)
      .finally(() => setClosing(null));
  };

  const totalPnl = positions.reduce((s, p) => s + p.pnl, 0);
  const totalValue = positions.reduce((s, p) => s + (p.current_price * p.quantity), 0);

  // Filtrer les signaux : exclure les actifs déjà en position
  const positionSymbols = new Set(positions.map((p) => p.symbol));
  const positionBrokers: Record<string, string> = {};
  positions.forEach((p: any) => { positionBrokers[p.symbol] = p.source === "ibkr_live" ? "IBKR" : p.source === "alpaca_live" ? "ALPACA" : "LOCAL"; });
  // Un signal est "bloqué" seulement s'il est déjà en position chez un vrai broker (IBKR ou ALPACA)
  const realPositionSymbols = new Set(positions.filter((p: any) => p.source === "ibkr_live" || p.source === "alpaca_live").map((p: any) => p.symbol));
  const availableSignals = signals.filter((s) => !realPositionSymbols.has(s.symbol));

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">Exécution des Ordres</h2>
          <p className="text-text-secondary text-sm mt-1 max-w-3xl">
            Centre de commande des opérations de trading — positions ouvertes en temps réel, signaux GO du pipeline, file d'attente intelligente et arbitrage d'opportunité. Exécution via IBKR (argent réel) et Alpaca (paper trading) avec bracket orders et protection SL/TP serveur-side.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            className="p-2 text-text-secondary hover:text-text-primary bg-surface rounded-lg transition-colors"
            title="Rafraîchir"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Erreur */}
      {error && (
        <div className="mb-6 p-4 rounded-xl border bg-red-500/10 border-red-500 text-red-400 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300"><X size={14} /></button>
        </div>
      )}

      {/* Statut Brokers — IBKR en premier (live), puis Alpaca (paper) */}
      <div className="mb-6 space-y-3">
        {/* IBKR — Live Trading */}
        <div className={`p-4 rounded-xl border flex items-center justify-between ${
          brokerStatus?.ibkr?.status === "connected"
            ? "bg-blue-500/5 border-blue-500/20"
            : "bg-surface border-border"
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${
              brokerStatus?.ibkr?.status === "connected" ? "bg-blue-400 animate-pulse" :
              brokerStatus?.ibkr?.status === "disconnected" ? "bg-yellow-400" : "bg-zinc-500"
            }`} />
            <div>
              <p className="text-sm font-semibold">
                {brokerStatus?.ibkr?.status === "connected" ? "Connecté à IBKR" :
                 brokerStatus?.ibkr?.status === "disconnected" ? "IBKR déconnecté" :
                 brokerStatus?.ibkr?.status === "error" ? "IBKR erreur" :
                 "IBKR non configuré"}
              </p>
              {brokerStatus?.ibkr?.status === "connected" && brokerStatus.ibkr.equity && (
                <p className="text-xs text-text-secondary">
                  {brokerStatus.ibkr.paper ? "Paper" : "Live"} Trading — Capital : {brokerStatus.ibkr.equity?.toLocaleString()}€
                </p>
              )}
              {brokerStatus?.ibkr?.status === "not_configured" && (
                <p className="text-xs text-text-secondary">Configurez IBKR_ACCOUNT_ID dans .env pour activer le trading réel</p>
              )}
              {brokerStatus?.ibkr?.status === "disconnected" && (
                <p className="text-xs text-text-secondary">Lancez IB Gateway ou TWS pour vous connecter</p>
              )}
            </div>
          </div>
          <span className={`text-xs px-2 py-1 rounded-lg font-semibold ${
            brokerStatus?.ibkr?.status === "connected"
              ? brokerStatus.ibkr.paper ? "bg-blue-400/10 text-blue-400 border border-blue-400/20" : "bg-emerald-400/10 text-emerald-400 border border-emerald-400/20"
              : "bg-zinc-500/10 text-zinc-400 border border-zinc-500/20"
          }`}>
            {brokerStatus?.ibkr?.status === "connected" ? (brokerStatus.ibkr.paper ? "PAPER" : "LIVE") : "OFF"}
          </span>
        </div>

        {/* Alpaca — Paper Trading */}
        <div className={`p-4 rounded-xl border flex items-center justify-between ${
          brokerStatus?.alpaca?.status === "connected"
            ? "bg-gold/5 border-gold/20"
            : brokerStatus?.connected ? "bg-gold/5 border-gold/20" : "bg-red-400/5 border-red-400/20"
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${
              (brokerStatus?.alpaca?.status === "connected" || brokerStatus?.connected) ? "bg-gold animate-pulse" : "bg-red-400"
            }`} />
            <div>
              <p className="text-sm font-semibold">
                {(brokerStatus?.alpaca?.status === "connected" || brokerStatus?.connected) ? "Connecté à Alpaca" : "Alpaca non connecté"}
              </p>
              {brokerStatus?.alpaca?.status === "connected" && (
                <p className="text-xs text-text-secondary">
                  Paper Trading — Capital : ${Number(brokerStatus.alpaca.equity).toLocaleString()}
                </p>
              )}
              {!brokerStatus?.alpaca && brokerStatus?.account && (
                <p className="text-xs text-text-secondary">
                  Paper Trading — Capital : ${brokerStatus.account.equity?.toLocaleString()} — Buying Power : ${brokerStatus.account.buying_power?.toLocaleString()}
                </p>
              )}
            </div>
          </div>
          <span className="text-xs px-2 py-1 bg-gold/10 text-gold border border-gold/20 rounded-lg font-semibold">
            PAPER
          </span>
        </div>
      </div>

      {/* Boutons d'action + métriques */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <button
          onClick={handleExecuteAll}
          disabled={executingAll || availableSignals.length === 0}
          className="flex items-center justify-center gap-3 p-5 bg-gold/10 border-2 border-gold/30 rounded-2xl text-gold hover:bg-gold/20 transition-all disabled:opacity-40 disabled:cursor-not-allowed group"
        >
          <div className="w-10 h-10 rounded-xl bg-gold/20 flex items-center justify-center group-hover:scale-110 transition-transform">
            <Play size={20} fill="currentColor" />
          </div>
          <div className="text-left">
            <p className="text-sm font-bold">
              {executingAll ? "Exécution..." : "Lancer le Trading"}
            </p>
            <p className="text-[10px] text-gold/70">
              {availableSignals.length > 0
                ? `${availableSignals.length} signal${availableSignals.length > 1 ? "s" : ""} GO`
                : signals.length > 0
                  ? `${signals.length} déjà en position`
                  : "Aucun signal GO"}
            </p>
          </div>
        </button>

        <button
          onClick={() => {
            api.post("/pipeline/run-light").then(() => {
              alert("Pipeline léger lancé — refresh des signaux en ~5 min (sans rescanner les 500 actifs)");
            }).catch(() => alert("Erreur lancement pipeline"));
          }}
          className="flex items-center justify-center gap-3 p-5 bg-surface border border-border rounded-2xl text-text-secondary hover:text-gold hover:border-gold/30 transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-gold/10 flex items-center justify-center group-hover:scale-110 transition-transform">
            <RefreshCw size={18} className="text-gold" />
          </div>
          <div className="text-left">
            <p className="text-sm font-bold">Refresh Léger</p>
            <p className="text-[10px] text-text-secondary">Scoring + Signaux (~5 min)</p>
          </div>
        </button>

        <button
          onClick={() => {
            api.post("/pipeline/run").then(() => {
              alert("Pipeline complet lancé — scan des 500 actifs + analyse + scoring (~35 min)");
            }).catch(() => alert("Erreur lancement pipeline"));
          }}
          className="flex items-center justify-center gap-3 p-5 bg-surface border border-border rounded-2xl text-text-secondary hover:text-gold hover:border-gold/30 transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center group-hover:scale-110 transition-transform">
            <RefreshCw size={18} className="text-blue-400" />
          </div>
          <div className="text-left">
            <p className="text-sm font-bold">Pipeline Complet</p>
            <p className="text-[10px] text-text-secondary">Scanner 500 actifs (~35 min)</p>
          </div>
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs text-text-secondary mb-1">Positions ouvertes</p>
            <p className="text-2xl font-mono font-semibold text-gold">{positions.length}</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs text-text-secondary mb-1">P&L Total</p>
            <p className={`text-2xl font-mono font-semibold ${totalPnl >= 0 ? "text-gold" : "text-red-400"}`}>
              ${totalPnl.toFixed(2)}
            </p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs text-text-secondary mb-1">Nouveaux signaux</p>
            <p className="text-2xl font-mono font-semibold text-gold">{availableSignals.length}</p>
            {signals.length > availableSignals.length && (
              <p className="text-[10px] text-text-secondary mt-0.5">{signals.length - availableSignals.length} déjà en position</p>
            )}
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs text-text-secondary mb-1">Valeur positions</p>
            <p className="text-2xl font-mono font-semibold">${totalValue.toFixed(0)}</p>
          </div>
      </div>

      {/* Résultat exécution globale */}
      {allResults && (
        <div className="mb-6">
          <InfoCard
            title="Résultat de l'exécution"
            icon={<Zap size={18} />}
            description="Résumé de l'exécution de tous les signaux GO. Chaque signal passe par la vérification des biais comportementaux avant d'être exécuté."
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-surface rounded-lg p-3 text-center">
                <p className="text-2xl font-mono font-bold text-gold">{allResults.executed}</p>
                <p className="text-xs text-text-secondary">Exécutés</p>
              </div>
              <div className="bg-surface rounded-lg p-3 text-center">
                <p className="text-2xl font-mono font-bold text-text-secondary">{allResults.skipped}</p>
                <p className="text-xs text-text-secondary">Non exécutés</p>
              </div>
              <div className="bg-surface rounded-lg p-3 text-center">
                <p className="text-2xl font-mono font-bold text-gold">${allResults.capital_deployed?.toFixed(0)}</p>
                <p className="text-xs text-text-secondary">Capital déployé</p>
              </div>
              <div className="bg-surface rounded-lg p-3 text-center">
                <p className="text-2xl font-mono font-bold">${allResults.capital_remaining?.toFixed(0)}</p>
                <p className="text-xs text-text-secondary">Capital restant</p>
              </div>
            </div>
            <div className="space-y-2">
              {allResults.results?.map((r: any) => (
                <div key={r.symbol} className="flex items-center justify-between bg-surface rounded-lg p-3 text-sm">
                  <div className="flex items-center gap-3">
                    <span className={`w-2 h-2 rounded-full ${r.executed ? "bg-gold" : "bg-red-400"}`} />
                    <span className="font-mono font-semibold text-gold">{r.symbol}</span>
                    <span className="text-text-secondary">{r.direction || ""}</span>
                  </div>
                  <span className={r.executed ? "text-gold text-xs" : "text-red-400 text-xs"}>
                    {r.executed ? "EXÉCUTÉ" : r.reason?.slice(0, 50) || "Non exécuté"}
                  </span>
                </div>
              ))}
            </div>
          </InfoCard>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Positions ouvertes */}
        <InfoCard
          title={`Positions ouvertes (${posFilter === "all" ? positions.length : positions.filter((p: any) => posFilter === "alpaca" ? p.source === "alpaca_live" : p.source !== "alpaca_live").length})`}
          icon={<Zap size={18} />}
          description="Filtrez par broker. ALPACA = positions réelles chez le broker. LOCAL = simulation BDD."
        >
          <div className="flex gap-1 mb-3">
            {(["all", "alpaca", "ibkr", "local"] as const).map((f) => (
              <button key={f} onClick={() => setPosFilter(f)} className={`text-[10px] px-2.5 py-1 rounded-lg border font-semibold transition-colors ${
                posFilter === f
                  ? f === "alpaca" ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/20" : f === "ibkr" ? "text-blue-400 bg-blue-400/10 border-blue-400/20" : f === "local" ? "text-text-secondary bg-surface border-border" : "text-gold bg-gold/10 border-gold/20"
                  : "text-text-secondary border-border hover:text-text-primary"
              }`}>
                {f === "all" ? "Toutes" : f === "alpaca" ? "Alpaca" : f === "ibkr" ? "IBKR" : "Local"}
              </button>
            ))}
          </div>
          {positions.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-text-secondary mb-2">Aucune position ouverte</p>
              <p className="text-xs text-text-secondary">
                Cliquez sur "Lancer le Trading" pour exécuter les signaux GO
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {positions.filter((p: any) => posFilter === "all" ? true : posFilter === "alpaca" ? p.source === "alpaca_live" : posFilter === "ibkr" ? p.source === "ibkr_live" : p.source === "database").map((p) => (
                <div key={p.id} className="bg-surface rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-gold text-lg">{p.symbol}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-lg border font-semibold ${
                        p.direction === "LONG" ? "text-gold bg-gold/10 border-gold/20" : "text-red-400 bg-red-400/10 border-red-400/20"
                      }`}>{p.direction}</span>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded border font-semibold ${
                        (p as any).source === "alpaca_live"
                          ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/20"
                          : (p as any).source === "ibkr_live"
                          ? "text-blue-400 bg-blue-400/10 border-blue-400/20"
                          : "text-text-secondary bg-surface border-border"
                      }`}>{(p as any).source === "alpaca_live" ? "ALPACA" : (p as any).source === "ibkr_live" ? "IBKR" : "LOCAL"}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-lg font-mono font-bold ${p.pnl >= 0 ? "text-gold" : "text-red-400"}`}>
                        ${p.pnl.toFixed(2)}
                        <span className="text-xs ml-1">({p.pnl_pct.toFixed(2)}%)</span>
                      </span>
                      <button
                        onClick={() => handleClosePosition(p.symbol)}
                        disabled={closing === p.symbol}
                        className="flex items-center gap-1 px-2.5 py-1.5 text-[11px] font-semibold rounded-lg border transition-colors bg-red-400/5 text-red-400 border-red-400/20 hover:bg-red-400/15 disabled:opacity-50"
                        title="Fermer cette position chez le broker"
                      >
                        <X size={12} />
                        {closing === p.symbol ? "Fermeture..." : "Fermer"}
                      </button>
                    </div>
                  </div>
                  <div className="grid grid-cols-4 gap-3 text-xs">
                    <div>
                      <span className="text-text-secondary block">Entrée</span>
                      <span className="font-mono">${p.entry_price.toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="text-text-secondary block">Actuel</span>
                      <span className="font-mono">${p.current_price.toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="text-text-secondary block">Stop Loss</span>
                      <span className="font-mono text-red-400">${p.stop_loss.toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="text-text-secondary block">Take Profit</span>
                      <span className="font-mono text-gold">${p.take_profit.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </InfoCard>

        {/* Signaux GO ou File d'attente */}
        {signals.length > 0 ? (
          <InfoCard
            title={`Signaux GO (${signals.length}) — ${availableSignals.length} nouveau${availableSignals.length > 1 ? "x" : ""}`}
            icon={<Zap size={18} />}
            description="Signaux validés par le pipeline. Les signaux déjà en position sont marqués."
          >
            <div className="space-y-2">
              {signals.map((s) => {
                const broker = positionBrokers[s.symbol];
                const isRealPosition = broker === "IBKR" || broker === "ALPACA";
                const isLocalOnly = broker === "LOCAL";
                return (
                  <div key={s.symbol} className={`flex items-center justify-between rounded-xl p-3 ${isRealPosition ? "bg-surface/50 opacity-60" : "bg-surface"}`}>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`font-mono font-semibold ${isRealPosition ? "text-text-secondary" : "text-gold"}`}>{s.symbol}</span>
                        {isRealPosition && (
                          <span className={`text-[9px] px-1.5 py-0.5 rounded border font-semibold ${
                            broker === "IBKR" ? "bg-blue-400/10 text-blue-400 border-blue-400/20"
                            : "bg-emerald-400/10 text-emerald-400 border-emerald-400/20"
                          }`}>{broker}</span>
                        )}
                        {isLocalOnly && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-yellow-400/10 text-yellow-400 border border-yellow-400/20 font-semibold">PAPER</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold ${
                          s.direction === "LONG" ? "text-gold bg-gold/10 border-gold/20" : "text-red-400 bg-red-400/10 border-red-400/20"
                        }`}>{s.direction}</span>
                        <span className="text-xs text-text-secondary">Score {s.thesis_score.toFixed(1)}</span>
                      </div>
                    </div>
                    {!isRealPosition ? (
                      <button
                        onClick={() => handleExecute(s.symbol)}
                        disabled={executing !== null}
                        className="text-xs px-4 py-2 bg-gold/10 text-gold border border-gold/20 rounded-lg hover:bg-gold/20 transition-colors disabled:opacity-50"
                      >
                        {executing === s.symbol ? "..." : "Exécuter"}
                      </button>
                    ) : (
                      <span className="text-[10px] text-text-secondary">Déjà ouvert</span>
                    )}
                  </div>
                );
              })}
            </div>
          </InfoCard>
        ) : queueData && queueData.queue_size > 0 ? (
          <InfoCard
            title={`File d'attente — ${queueData.queue_size} signaux`}
            icon={<Zap size={18} />}
            description={`${queueData.open_positions}/${queueData.max_positions} positions. Exécution auto quand un slot se libère.`}
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="flex-1 h-2 bg-surface rounded-full overflow-hidden">
                <div className="h-full bg-gold rounded-full" style={{ width: `${(queueData.open_positions / queueData.max_positions) * 100}%` }} />
              </div>
              <span className="text-xs font-mono text-text-secondary">{queueData.open_positions}/{queueData.max_positions}</span>
            </div>
            <div className="space-y-1.5 max-h-[600px] overflow-y-auto">
              {queueData.queue.map((q: any, i: number) => {
                const isNext = i < queueData.slots_available;
                return (
                  <div key={`${q.symbol}-${i}`} className={`flex items-center justify-between py-2 px-3 rounded-lg text-xs ${
                    isNext ? "bg-gold/5 border border-gold/20" : "bg-surface"
                  }`}>
                    <div className="flex items-center gap-2">
                      <span className={`w-5 text-right font-mono ${isNext ? "text-gold font-bold" : "text-text-secondary"}`}>{i + 1}</span>
                      <span className="font-mono font-semibold text-gold">{q.symbol}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold ${
                        q.direction === "LONG" || !q.direction ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/20" : "text-red-400 bg-red-400/10 border-red-400/20"
                      }`}>{q.direction || "LONG"}</span>
                      {isNext && <span className="text-[9px] px-1.5 py-0.5 rounded bg-gold/10 text-gold border border-gold/20 font-semibold">PROCHAIN</span>}
                    </div>
                    <span className="font-mono font-semibold">{(q.score ?? 0).toFixed(1)}</span>
                  </div>
                );
              })}
            </div>
          </InfoCard>
        ) : (
          <InfoCard title="Signaux GO" icon={<Zap size={18} />} description="Aucun signal actif.">
            <p className="text-text-secondary text-sm text-center py-4">De nouveaux signaux apparaîtront après le prochain scan.</p>
          </InfoCard>
        )}
      </div>

      {/* Opportunity Arbiter — Arbitrage d'opportunité */}
      {arbiter && arbiter.ranking && arbiter.ranking.length > 0 && (
        <div className="mt-6">
          <InfoCard
            title="Arbitrage d'Opportunité — Positions vs Signaux"
            icon={<Zap size={18} />}
            description="Classement unifié par Espérance de Valeur/jour. Les signaux au-dessus des positions = swap recommandé."
          >
            {/* Swaps recommandés */}
            {arbiter.swaps_recommended && arbiter.swaps_recommended.length > 0 && (
              <div className="mb-4 p-3 bg-gold/5 border border-gold/20 rounded-xl">
                <p className="text-xs font-semibold text-gold mb-2 uppercase tracking-wider">
                  {arbiter.swaps_recommended.length} Swap{arbiter.swaps_recommended.length > 1 ? "s" : ""} recommandé{arbiter.swaps_recommended.length > 1 ? "s" : ""}
                </p>
                {arbiter.swaps_recommended.map((sw: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-xs py-1.5">
                    <span className="text-red-400 font-mono font-bold">{sw.close}</span>
                    <span className="text-text-secondary">→</span>
                    <span className="text-emerald-400 font-mono font-bold">{sw.open}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-400/10 text-emerald-400 border border-emerald-400/20 font-semibold">
                      +{sw.ev_gain_per_day.toFixed(2)} EV/j
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Classement */}
            <div className="space-y-1">
              <div className="flex items-center text-[10px] text-text-secondary px-3 py-1 uppercase tracking-wider">
                <span className="w-6">#</span>
                <span className="w-20">Type</span>
                <span className="flex-1">Symbole</span>
                <span className="w-16 text-right">EV/jour</span>
                <span className="w-14 text-right">Santé</span>
                <span className="w-14 text-right">→TP%</span>
                <span className="w-14 text-right">Prob</span>
              </div>
              {arbiter.ranking.map((r: any, i: number) => {
                const isPosition = r.type === "POSITION";
                const isSwapClose = arbiter.swaps_recommended?.some((sw: any) => sw.close === r.symbol);
                const isSwapOpen = arbiter.swaps_recommended?.some((sw: any) => sw.open === r.symbol);
                return (
                  <div key={`${r.symbol}-${r.type}-${i}`} className={`flex items-center text-xs px-3 py-2 rounded-lg ${
                    isSwapClose ? "bg-red-400/5 border border-red-400/10" :
                    isSwapOpen ? "bg-emerald-400/5 border border-emerald-400/10" :
                    isPosition ? "bg-blue-400/5" : "bg-surface"
                  }`}>
                    <span className="w-6 font-mono text-text-secondary">{i + 1}</span>
                    <span className="w-20">
                      <span className={`text-[9px] px-1.5 py-0.5 rounded font-semibold ${
                        isPosition ? "bg-blue-400/10 text-blue-400" : "bg-gold/10 text-gold"
                      }`}>{isPosition ? "POS" : "SIGNAL"}</span>
                    </span>
                    <span className="flex-1 flex items-center gap-2">
                      <span className={`font-mono font-bold ${isSwapClose ? "text-red-400" : isSwapOpen ? "text-emerald-400" : "text-gold"}`}>{r.symbol}</span>
                      {isSwapClose && <span className="text-[9px] px-1 py-0.5 rounded bg-red-400/10 text-red-400">FERMER</span>}
                      {isSwapOpen && <span className="text-[9px] px-1 py-0.5 rounded bg-emerald-400/10 text-emerald-400">OUVRIR</span>}
                      {r.alerts && r.alerts.length > 0 && (
                        <span className="text-[9px] text-yellow-400">{r.alerts[0]}</span>
                      )}
                    </span>
                    <span className={`w-16 text-right font-mono font-bold ${r.ev_per_day > 0.5 ? "text-emerald-400" : r.ev_per_day > 0 ? "text-text-primary" : "text-red-400"}`}>
                      {r.ev_per_day > 0 ? "+" : ""}{r.ev_per_day.toFixed(3)}
                    </span>
                    <span className={`w-14 text-right font-mono ${r.health_score >= 65 ? "text-emerald-400" : r.health_score >= 50 ? "text-yellow-400" : "text-red-400"}`}>
                      {r.health_score}
                    </span>
                    <span className="w-14 text-right font-mono text-text-secondary">
                      +{r.remaining_to_tp_pct.toFixed(1)}%
                    </span>
                    <span className="w-14 text-right font-mono text-text-secondary">
                      {r.prob_tp.toFixed(0)}%
                    </span>
                  </div>
                );
              })}
            </div>
          </InfoCard>
        </div>
      )}

      {/* Health Check — Essoufflement */}
      {healthData.length > 0 && (
        <div className="mt-6">
          <InfoCard
            title="Santé des positions — Essoufflement"
            icon={<AlertTriangle size={18} />}
            description="Évalue si vos trades ont encore du potentiel ou s'ils s'essoufflent. Score 0-100 : FORT (>70), MODÉRÉ (50-70), FAIBLE (35-50), ÉPUISÉ (<35)."
          >
            <div className="space-y-3">
              {healthData.map((h: any) => {
                const levelColor = h.level === "FORT" ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/20" :
                  h.level === "MODÉRÉ" ? "text-yellow-400 bg-yellow-400/10 border-yellow-400/20" :
                  h.level === "FAIBLE" ? "text-orange-400 bg-orange-400/10 border-orange-400/20" :
                  "text-red-400 bg-red-400/10 border-red-400/20";
                const barColor = h.level === "FORT" ? "bg-emerald-400" :
                  h.level === "MODÉRÉ" ? "bg-yellow-400" :
                  h.level === "FAIBLE" ? "bg-orange-400" : "bg-red-400";

                return (
                  <div key={h.symbol} className="bg-surface rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-semibold text-gold">{h.symbol}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold ${
                          h.direction === "LONG" ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/20" : "text-red-400 bg-red-400/10 border-red-400/20"
                        }`}>{h.direction}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold ${levelColor}`}>{h.level}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`font-mono text-sm font-bold ${h.pnl_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                          {h.pnl_pct >= 0 ? "+" : ""}{h.pnl_pct}%
                        </span>
                        <span className="font-mono text-lg font-bold">{h.score}</span>
                      </div>
                    </div>
                    {/* Barre de score */}
                    <div className="h-1.5 bg-background rounded-full overflow-hidden mb-2">
                      <div className={`h-full rounded-full transition-all ${barColor}`} style={{ width: `${h.score}%` }} />
                    </div>
                    {/* Signaux détaillés */}
                    <div className="flex flex-wrap gap-2">
                      {(h.signals ?? []).map((s: any, i: number) => (
                        <div key={i} className={`text-[10px] px-2 py-1 rounded border ${
                          s.status === "FORT" ? "text-emerald-400 border-emerald-400/20 bg-emerald-400/5" :
                          s.status === "FAIBLE" ? "text-red-400 border-red-400/20 bg-red-400/5" :
                          "text-text-secondary border-border"
                        }`}>
                          <span className="font-semibold">{s.name}</span>: {s.value}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </InfoCard>
        </div>
      )}

      {/* Dernier résultat individuel */}
      {lastResult && (
        <div className="mt-6 bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">
            Dernière exécution — {lastResult.symbol}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm">
                Statut :{" "}
                <span className={lastResult.executed ? "text-gold font-semibold" : "text-red-400"}>
                  {lastResult.executed ? "EXÉCUTÉ" : "NON EXÉCUTÉ"}
                </span>
              </p>
              {lastResult.reason && (
                <p className="text-xs text-text-secondary mt-1">{lastResult.reason}</p>
              )}
              {lastResult.position && (
                <div className="mt-2 text-sm space-y-1">
                  <p>Entry : <span className="font-mono">${lastResult.position.entry_price.toFixed(2)}</span></p>
                  <p>Qty : <span className="font-mono">{lastResult.position.quantity.toFixed(2)}</span></p>
                </div>
              )}
            </div>
            {lastResult.bias_check && (
              <div>
                <p className="text-xs text-text-secondary mb-2">Biais comportementaux</p>
                <div className="space-y-1">
                  {lastResult.bias_check.biases.map((b) => (
                    <div key={b.bias} className="flex items-center justify-between text-xs">
                      <span className="capitalize">{b.bias}</span>
                      <span className={`px-1.5 py-0.5 rounded ${BIAS_STYLES[b.level] || ""}`}>
                        {b.level} ({b.score})
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
