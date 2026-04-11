import { useEffect, useState } from "react";
import { Play, Square, RefreshCw, Zap, AlertTriangle } from "lucide-react";
import {
  executionApi,
  scoringApi,
  type OpenPosition,
  type TradeThesis,
  type ExecutionResult,
} from "../services/api";
import axios from "axios";
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

  const loadData = async () => {
    setLoading(true);

    // 1. Broker status (rapide, timeout 5s)
    try {
      const brokerRes = await axios.get("/api/broker/status", { timeout: 5000 });
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

    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleExecute = (symbol: string) => {
    setExecuting(symbol);
    executionApi
      .execute(symbol)
      .then((res) => {
        setLastResult(res.data);
        loadData();
      })
      .catch(console.error)
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
      .catch(console.error)
      .finally(() => setExecutingAll(false));
  };

  const totalPnl = positions.reduce((s, p) => s + p.pnl, 0);
  const totalValue = positions.reduce((s, p) => s + (p.current_price * p.quantity), 0);

  // Filtrer les signaux : exclure les actifs déjà en position
  const positionSymbols = new Set(positions.map((p) => p.symbol));
  const availableSignals = signals.filter((s) => !positionSymbols.has(s.symbol));

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">Exécution des Ordres</h2>
          <p className="text-text-secondary text-sm mt-1">
            Paper Trading Alpaca — Scaling 3 tranches — Détection biais
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

      {/* Statut Broker */}
      <div className={`mb-6 p-4 rounded-xl border flex items-center justify-between ${
        brokerStatus?.connected
          ? "bg-gold/5 border-gold/20"
          : "bg-red-400/5 border-red-400/20"
      }`}>
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${brokerStatus?.connected ? "bg-gold animate-pulse" : "bg-red-400"}`} />
          <div>
            <p className="text-sm font-semibold">
              {brokerStatus?.connected ? "Connecté à Alpaca" : "Non connecté"}
            </p>
            {brokerStatus?.account && (
              <p className="text-xs text-text-secondary">
                Paper Trading — Capital : ${brokerStatus.account.equity?.toLocaleString()} — Buying Power : ${brokerStatus.account.buying_power?.toLocaleString()}
              </p>
            )}
          </div>
        </div>
        {brokerStatus?.connected && (
          <span className="text-xs px-2 py-1 bg-gold/10 text-gold border border-gold/20 rounded-lg font-semibold">
            PAPER
          </span>
        )}
      </div>

      {/* Boutons d'action principaux */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <button
          onClick={handleExecuteAll}
          disabled={executingAll || availableSignals.length === 0}
          className="flex items-center justify-center gap-3 p-5 bg-gold/10 border-2 border-gold/30 rounded-2xl text-gold hover:bg-gold/20 transition-all disabled:opacity-40 disabled:cursor-not-allowed group"
        >
          <div className="w-12 h-12 rounded-xl bg-gold/20 flex items-center justify-center group-hover:scale-110 transition-transform">
            <Play size={24} fill="currentColor" />
          </div>
          <div className="text-left">
            <p className="text-lg font-bold">
              {executingAll ? "Exécution en cours..." : "Lancer le Trading"}
            </p>
            <p className="text-xs text-gold/70">
              {availableSignals.length > 0
                ? `Exécuter ${availableSignals.length} nouveau${availableSignals.length > 1 ? "x" : ""} signal${availableSignals.length > 1 ? "s" : ""} GO`
                : signals.length > 0
                  ? `${signals.length} signal${signals.length > 1 ? "s" : ""} déjà en position`
                  : "Aucun signal GO disponible actuellement"}
            </p>
          </div>
        </button>

        <div className="grid grid-cols-2 gap-4">
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
          title="Positions ouvertes"
          icon={<Zap size={18} />}
          description="Vos positions actuelles en paper trading. Le P&L se met à jour avec les dernières données de marché."
        >
          {positions.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-text-secondary mb-2">Aucune position ouverte</p>
              <p className="text-xs text-text-secondary">
                Cliquez sur "Lancer le Trading" pour exécuter les signaux GO
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {positions.map((p) => (
                <div key={p.id} className="bg-surface rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-gold text-lg">{p.symbol}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-lg border font-semibold ${
                        p.direction === "LONG" ? "text-gold bg-gold/10 border-gold/20" : "text-red-400 bg-red-400/10 border-red-400/20"
                      }`}>{p.direction}</span>
                    </div>
                    <span className={`text-lg font-mono font-bold ${p.pnl >= 0 ? "text-gold" : "text-red-400"}`}>
                      ${p.pnl.toFixed(2)}
                      <span className="text-xs ml-1">({p.pnl_pct.toFixed(2)}%)</span>
                    </span>
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

        {/* Signaux disponibles */}
        <InfoCard
          title={`Signaux GO — Nouveaux (${availableSignals.length})`}
          icon={<Zap size={18} />}
          description="Les signaux validés par les 6 modules du pipeline. Vous pouvez exécuter chaque signal individuellement ou tous d'un coup."
        >
          {loading ? (
            <p className="text-text-secondary text-sm py-4">Chargement...</p>
          ) : availableSignals.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-text-secondary mb-2">
                {signals.length > 0
                  ? "Tous les signaux sont déjà en position"
                  : "Aucun signal actif"}
              </p>
              <p className="text-xs text-text-secondary">
                De nouveaux signaux apparaîtront quand le scanner détectera de nouvelles opportunités.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {availableSignals.map((s) => (
                <div key={s.symbol} className="flex items-center justify-between bg-surface rounded-xl p-3">
                  <div>
                    <span className="font-mono font-semibold text-gold">{s.symbol}</span>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold ${
                        s.direction === "LONG" ? "text-gold bg-gold/10 border-gold/20" : "text-red-400 bg-red-400/10 border-red-400/20"
                      }`}>{s.direction}</span>
                      <span className="text-xs text-text-secondary">
                        Score {s.thesis_score.toFixed(1)}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleExecute(s.symbol)}
                    disabled={executing !== null}
                    className="text-xs px-4 py-2 bg-gold/10 text-gold border border-gold/20 rounded-lg hover:bg-gold/20 transition-colors disabled:opacity-50"
                  >
                    {executing === s.symbol ? "..." : "Exécuter"}
                  </button>
                </div>
              ))}
            </div>
          )}
        </InfoCard>
      </div>

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
