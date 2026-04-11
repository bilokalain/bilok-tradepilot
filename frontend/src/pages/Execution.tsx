import { useEffect, useState } from "react";
import {
  executionApi,
  scoringApi,
  type OpenPosition,
  type TradeThesis,
  type ExecutionResult,
} from "../services/api";

const BIAS_STYLES: Record<string, string> = {
  OK: "text-gold bg-gold/10",
  WARNING: "text-yellow-400 bg-yellow-400/10",
  BLOCK: "text-red-400 bg-red-400/10",
};

export default function Execution() {
  const [positions, setPositions] = useState<OpenPosition[]>([]);
  const [signals, setSignals] = useState<TradeThesis[]>([]);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<ExecutionResult | null>(null);

  const loadData = () => {
    setLoading(true);
    Promise.all([executionApi.getPositions(), scoringApi.getSignals()])
      .then(([posRes, sigRes]) => {
        setPositions(posRes.data);
        setSignals(sigRes.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
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

  const totalPnl = positions.reduce((s, p) => s + p.pnl, 0);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Exécution des Ordres</h2>
      <p className="text-text-secondary mb-6 text-sm">
        Paper Trading — Scaling 3 tranches — Détection biais comportementaux
      </p>

      {/* Métriques */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
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
          <p className="text-xs text-text-secondary mb-1">Signaux GO</p>
          <p className="text-2xl font-mono font-semibold">{signals.length}</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary mb-1">Mode</p>
          <p className="text-sm font-semibold text-gold mt-1">Paper Trading</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Positions ouvertes */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Positions ouvertes</h3>
          {positions.length === 0 ? (
            <p className="text-text-secondary text-sm">Aucune position</p>
          ) : (
            <div className="space-y-3">
              {positions.map((p) => (
                <div key={p.id} className="bg-surface rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-gold">{p.symbol}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded border font-semibold ${
                        p.direction === "LONG" ? "text-gold bg-gold/10 border-gold/20" : "text-red-400 bg-red-400/10 border-red-400/20"
                      }`}>{p.direction}</span>
                    </div>
                    <span className={`font-mono font-semibold ${p.pnl >= 0 ? "text-gold" : "text-red-400"}`}>
                      ${p.pnl.toFixed(2)} ({p.pnl_pct.toFixed(2)}%)
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-xs text-text-secondary">
                    <div>Entry <span className="font-mono text-text-primary">${p.entry_price.toFixed(2)}</span></div>
                    <div>Now <span className="font-mono text-text-primary">${p.current_price.toFixed(2)}</span></div>
                    <div>SL <span className="font-mono text-red-400">${p.stop_loss.toFixed(2)}</span></div>
                    <div>TP <span className="font-mono text-gold">${p.take_profit.toFixed(2)}</span></div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Signaux disponibles */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">
            Signaux GO — Prêts à exécuter
          </h3>
          {loading ? (
            <p className="text-text-secondary text-sm">Chargement...</p>
          ) : signals.length === 0 ? (
            <p className="text-text-secondary text-sm">Aucun signal actif</p>
          ) : (
            <div className="space-y-2">
              {signals.map((s) => (
                <div key={s.symbol} className="flex items-center justify-between bg-surface rounded-lg p-3">
                  <div>
                    <span className="font-mono font-semibold text-gold">{s.symbol}</span>
                    <span className="text-xs text-text-secondary ml-2">{s.direction}</span>
                    <span className="text-xs text-text-secondary ml-2">
                      Score {s.thesis_score.toFixed(1)}
                    </span>
                  </div>
                  <button
                    onClick={() => handleExecute(s.symbol)}
                    disabled={executing !== null}
                    className="text-xs px-3 py-1.5 bg-gold/10 text-gold border border-gold/20 rounded-lg hover:bg-gold/20 transition-colors disabled:opacity-50"
                  >
                    {executing === s.symbol ? "..." : "Exécuter"}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Dernier résultat */}
      {lastResult && (
        <div className="mt-6 bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">
            Dernière exécution — {lastResult.symbol}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm">
                Statut :{" "}
                <span className={lastResult.executed ? "text-gold" : "text-red-400"}>
                  {lastResult.executed ? "EXÉCUTÉ" : "NON EXÉCUTÉ"}
                </span>
              </p>
              {lastResult.reason && (
                <p className="text-xs text-text-secondary mt-1">{lastResult.reason}</p>
              )}
              {lastResult.position && (
                <div className="mt-2 text-sm">
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
          {lastResult.orders && lastResult.orders.length > 0 && (
            <div className="mt-4">
              <p className="text-xs text-text-secondary mb-2">Ordres</p>
              <div className="space-y-1">
                {lastResult.orders.map((o) => (
                  <div key={o.tranche} className="flex items-center gap-3 text-xs">
                    <span className="font-mono w-6">T{o.tranche}</span>
                    <span className="w-16">{o.order_type}</span>
                    <span className="font-mono w-16">qty={o.quantity.toFixed(2)}</span>
                    <span className={o.status === "FILLED" ? "text-gold" : "text-text-secondary"}>
                      {o.status}
                    </span>
                    {o.filled_price && (
                      <span className="font-mono text-gold">@${o.filled_price.toFixed(2)}</span>
                    )}
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
