import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { scannerApi, analyserApi, type ScanResult, type RegimeSummary } from "../services/api";
import TradingChart from "../components/TradingChart";
import axios from "axios";

export default function Dashboard() {
  const [results, setResults] = useState<ScanResult[]>([]);
  const [regime, setRegime] = useState<RegimeSummary | null>(null);
  const [metaScore, setMetaScore] = useState<any>(null);
  const [ohlcv, setOhlcv] = useState<any>(null);
  const [selectedSymbol, setSelectedSymbol] = useState("AAPL");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      scannerApi.scan(),
      analyserApi.getRegime(),
      axios.get("/api/performance/meta-score"),
    ])
      .then(([scanRes, regimeRes, metaRes]) => {
        setResults(scanRes.data);
        setRegime(regimeRes.data);
        setMetaScore(metaRes.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    scannerApi.getOhlcv(selectedSymbol, 60).then((res) => setOhlcv(res.data));
  }, [selectedSymbol]);

  const topBuy = results.filter((r) => r.scores.final >= 65);
  const avgScore = results.length
    ? (results.reduce((s, r) => s + r.scores.final, 0) / results.length).toFixed(1)
    : "—";

  const REGIME_COLORS: Record<string, string> = {
    BULL: "text-gold",
    BEAR: "text-red-400",
    RANGE: "text-blue-400",
    CRISIS: "text-red-600",
    TRANSITION: "text-yellow-400",
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      {/* Métriques */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <MetricCard label="Actifs scannés" value={loading ? "..." : String(results.length)} />
        <MetricCard label="Score moyen" value={loading ? "..." : avgScore} unit="/100" />
        <MetricCard label="Signaux achat" value={loading ? "..." : String(topBuy.length)} />
        <MetricCard
          label="Régime"
          value={regime?.dominant_regime || "—"}
          color={REGIME_COLORS[regime?.dominant_regime || ""] || ""}
        />
        <MetricCard
          label="Meta-Score"
          value={metaScore ? String(metaScore.meta_score) : "—"}
          unit="/100"
          sub={metaScore?.engagement}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Chart */}
        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-text-secondary">Graphique des prix</h3>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="bg-surface border border-border rounded px-2 py-1 text-xs font-mono"
            >
              {results.map((r) => (
                <option key={r.symbol} value={r.symbol}>{r.symbol}</option>
              ))}
            </select>
          </div>
          {ohlcv?.data ? (
            <TradingChart data={ohlcv.data} height={300} />
          ) : (
            <div className="h-64 flex items-center justify-center text-text-secondary text-sm">Chargement...</div>
          )}
        </div>

        {/* Pipeline status */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Pipeline Status</h3>
          <div className="space-y-3">
            {[
              { name: "Scanner", status: "Actif", active: true },
              { name: "Analyseur", status: "Actif", active: true },
              { name: "Scoring", status: "Actif", active: true },
              { name: "Exécution", status: "Actif", active: true },
              { name: "Portefeuille", status: "Actif", active: true },
              { name: "Rentabilité", status: "Actif", active: true },
            ].map((module, i) => (
              <div key={module.name} className="flex items-center justify-between">
                <span className="text-sm">Module {i + 1} — {module.name}</span>
                <span className="text-xs text-gold px-2 py-1 bg-gold/10 border border-gold/20 rounded">
                  {module.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top actifs */}
      <div className="bg-card border border-border rounded-xl p-6">
        <h3 className="text-sm font-medium text-text-secondary mb-4">Top actifs par score</h3>
        {loading ? (
          <p className="text-text-secondary text-sm">Scan en cours...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-text-secondary border-b border-border">
                  <th className="pb-3 pr-4">#</th>
                  <th className="pb-3 pr-4">Symbole</th>
                  <th className="pb-3 pr-4">Nom</th>
                  <th className="pb-3 pr-4 text-right">Prix</th>
                  <th className="pb-3 pr-4 text-right">Score AT</th>
                  <th className="pb-3 pr-4 text-right">Corrélation</th>
                  <th className="pb-3 text-right">Final</th>
                </tr>
              </thead>
              <tbody>
                {results.slice(0, 10).map((r, i) => (
                  <tr key={r.symbol} className="border-b border-border/50 hover:bg-surface transition-colors">
                    <td className="py-2.5 pr-4 font-mono text-text-secondary">{i + 1}</td>
                    <td className="py-2.5 pr-4 font-mono font-semibold text-gold">
                      <Link to={`/asset/${r.symbol}`} className="hover:underline">{r.symbol}</Link>
                    </td>
                    <td className="py-2.5 pr-4 text-sm">{r.name}</td>
                    <td className="py-2.5 pr-4 text-right font-mono">${r.last_close.toFixed(2)}</td>
                    <td className="py-2.5 pr-4 text-right font-mono">{r.scores.technical.toFixed(1)}</td>
                    <td className="py-2.5 pr-4 text-right font-mono">{r.scores.correlation.toFixed(1)}</td>
                    <td className={`py-2.5 text-right font-mono font-semibold ${r.scores.final >= 70 ? "text-gold" : ""}`}>
                      {r.scores.final.toFixed(1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value, unit, sub, color }: {
  label: string; value: string; unit?: string; sub?: string; color?: string;
}) {
  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <p className="text-xs text-text-secondary mb-1">{label}</p>
      <p className={`text-2xl font-mono font-semibold ${color || "text-gold"}`}>
        {value}
        {unit && <span className="text-sm text-text-secondary ml-1">{unit}</span>}
      </p>
      {sub && <p className="text-xs text-text-secondary mt-0.5">{sub}</p>}
    </div>
  );
}
