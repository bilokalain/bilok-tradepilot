import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, TrendingUp, Target, Zap, Brain, Shield } from "lucide-react";
import axios from "axios";
import TradingChart from "../components/TradingChart";
import ScoreGauge from "../components/ui/ScoreGauge";
import InfoCard from "../components/ui/InfoCard";
import SignalBadge from "../components/ui/SignalBadge";
import LoadingScreen from "../components/LoadingScreen";
import { scannerApi, analyserApi, type ScanResult, type RegimeSummary } from "../services/api";

const REGIME_FR: Record<string, string> = {
  BULL: "Haussier", BEAR: "Baissier", RANGE: "Latéral", CRISIS: "Crise", TRANSITION: "Transition",
};

export default function Dashboard() {
  const [results, setResults] = useState<ScanResult[]>([]);
  const [regime, setRegime] = useState<RegimeSummary | null>(null);
  const [metaScore, setMetaScore] = useState<any>(null);
  const [signals, setSignals] = useState<any[]>([]);
  const [ohlcv, setOhlcv] = useState<any>(null);
  const [selectedSymbol, setSelectedSymbol] = useState("AAPL");
  const [loadingMain, setLoadingMain] = useState(true);
  const [loadingScan, setLoadingScan] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Étape 1 : données rapides
    Promise.all([
      analyserApi.getRegime().catch(() => ({ data: null })),
      axios.get("/api/performance/meta-score").catch(() => ({ data: null })),
      axios.get("/api/scoring/signals").catch(() => ({ data: [] })),
    ])
      .then(([regimeRes, metaRes, sigRes]) => {
        if (regimeRes.data) setRegime(regimeRes.data);
        if (metaRes.data) setMetaScore(metaRes.data);
        setSignals(Array.isArray(sigRes.data) ? sigRes.data : []);
      })
      .catch(() => setError("Erreur de connexion au serveur"))
      .finally(() => setLoadingMain(false));

    // Étape 2 : scan (retourne vite les données de base, puis re-fetch pour les vrais scores)
    const fetchScan = () => {
      scannerApi.scan()
        .then((res) => {
          if (Array.isArray(res.data)) {
            setResults(res.data);
            // Si les scores sont en loading (_loading), re-fetch dans 15s
            const stillLoading = res.data.some((r: any) => r._loading);
            if (stillLoading) {
              setTimeout(fetchScan, 15_000);
            } else {
              setLoadingScan(false);
            }
          }
        })
        .catch(() => setLoadingScan(false));
    };
    fetchScan();
  }, []);

  useEffect(() => {
    scannerApi.getOhlcv(selectedSymbol, 90).then((res) => setOhlcv(res.data)).catch(() => {});
  }, [selectedSymbol]);

  if (loadingMain && results.length === 0) {
    return <LoadingScreen message="Connexion au pipeline TradePilot..." />;
  }

  const avgScore = results.length ? results.reduce((s, r) => s + r.scores.final, 0) / results.length : 0;

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold">Dashboard</h2>
          <p className="text-text-secondary text-sm mt-1">
            Vue d'ensemble — {results.length > 0 ? `${results.length} actifs` : "chargement..."}
          </p>
        </div>
        {metaScore && <ScoreGauge score={metaScore.meta_score} size={90} sublabel="/100" label="Santé système" />}
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-400/10 border border-red-400/20 rounded-xl text-sm text-red-400">
          {error} — vérifiez que le backend tourne sur le port 8000.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <MetricCard icon={<Activity size={16} />} label="Actifs scannés" value={loadingScan ? "..." : String(results.length)} description="Analysés sur 9 critères" />
        <MetricCard icon={<Target size={16} />} label="Score moyen" value={loadingScan ? "..." : avgScore.toFixed(1)} unit="/100" description="Moyenne des 9 critères" color={avgScore >= 60 ? "text-gold" : ""} />
        <MetricCard icon={<Zap size={16} />} label="Signaux GO" value={String(signals.length)} description="Prêts pour l'exécution" color="text-gold" />
        <MetricCard icon={<Brain size={16} />} label="Régime" value={regime ? REGIME_FR[regime.dominant_regime] || regime.dominant_regime : "—"} description="Marché dominant" color={regime?.dominant_regime === "BULL" ? "text-gold" : regime?.dominant_regime === "BEAR" ? "text-red-400" : ""} />
        <MetricCard icon={<Shield size={16} />} label="Engagement" value={metaScore?.engagement || "—"} description={metaScore?.description || ""} color={metaScore?.engagement === "FULL" ? "text-gold" : metaScore?.engagement === "MINIMAL" ? "text-red-400" : ""} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <InfoCard title="Graphique des prix" icon={<TrendingUp size={18} />} description="Chandeliers : doré = hausse, gris = baisse. Lignes = moyennes mobiles.">
            <div className="flex justify-end mb-3">
              <select value={selectedSymbol} onChange={(e) => setSelectedSymbol(e.target.value)} className="bg-surface border border-border rounded-lg px-3 py-1.5 text-xs font-mono">
                {results.length > 0
                  ? results.map((r) => (<option key={r.symbol} value={r.symbol}>{r.symbol}</option>))
                  : <option value="AAPL">AAPL</option>}
              </select>
            </div>
            {ohlcv?.data ? <TradingChart data={ohlcv.data} height={350} /> : <div className="h-64 flex items-center justify-center text-text-secondary text-sm">Chargement...</div>}
          </InfoCard>
        </div>

        <InfoCard title="Signaux actifs" icon={<Zap size={18} />} description="Validés par les 6 modules. Cliquez pour le détail.">
          {signals.length === 0 ? (
            <p className="text-text-secondary text-sm py-4">Aucun signal GO actuellement.</p>
          ) : (
            <div className="space-y-2 max-h-[320px] overflow-y-auto">
              {signals.map((s: any) => (
                <Link key={s.symbol} to={`/asset/${s.symbol}`} className="flex items-center justify-between p-3 bg-surface rounded-xl hover:bg-gold/5 transition-colors group">
                  <div>
                    <span className="font-mono font-semibold text-gold group-hover:underline">{s.symbol}</span>
                    <div className="mt-1"><SignalBadge action="GO" direction={s.direction} size="sm" /></div>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-mono font-semibold">{s.thesis_score?.toFixed(1)}</span>
                    <p className="text-[10px] text-text-secondary">${s.entry?.toFixed(2)}</p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </InfoCard>
      </div>

      <InfoCard title="Pipeline TradePilot" icon={<Activity size={18} />} description="6 modules automatisés avec feedback loop.">
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {[
            { name: "Scanner", desc: "9 critères, 51 actifs", icon: "🔍" },
            { name: "Analyseur", desc: "Régime + stratégie", icon: "🧠" },
            { name: "Scoring", desc: "Bayésien + Kelly", icon: "🎯" },
            { name: "Exécution", desc: "3 tranches + anti-biais", icon: "⚡" },
            { name: "Portefeuille", desc: "Risk parity + stress", icon: "💼" },
            { name: "Rentabilité", desc: "P&L + feedback loop", icon: "📈" },
          ].map((m, i) => (
            <div key={m.name} className="flex items-center">
              <div className="bg-surface rounded-xl p-3 min-w-[140px] border border-gold/10">
                <div className="flex items-center gap-2 mb-1"><span>{m.icon}</span><span className="text-xs font-semibold">M{i+1} — {m.name}</span></div>
                <p className="text-[10px] text-text-secondary">{m.desc}</p>
                <div className="flex items-center gap-1 mt-2"><div className="w-1.5 h-1.5 rounded-full bg-gold animate-pulse" /><span className="text-[10px] text-gold">Actif</span></div>
              </div>
              {i < 5 && <span className="text-text-secondary mx-1">→</span>}
            </div>
          ))}
        </div>
      </InfoCard>

      {results.length > 0 && (
        <div className="mt-6">
          <InfoCard title="Classement des actifs" icon={<Target size={18} />} description="Score global = 9 critères pondérés. Cliquez pour l'analyse détaillée.">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-text-secondary border-b border-border">
                    <th className="pb-3 pr-3 w-8">#</th><th className="pb-3 pr-3">Actif</th><th className="pb-3 pr-3">Classe</th><th className="pb-3 pr-3 text-right">Prix</th><th className="pb-3 text-right">Score</th>
                  </tr>
                </thead>
                <tbody>
                  {results.slice(0, 15).map((r, i) => (
                    <tr key={r.symbol} className="border-b border-border/30 hover:bg-surface/50 transition-colors">
                      <td className="py-2.5 pr-3 font-mono text-text-secondary text-xs">{i + 1}</td>
                      <td className="py-2.5 pr-3">
                        <Link to={`/asset/${r.symbol}`} className="flex items-center gap-2 group">
                          <span className="font-mono font-semibold text-gold group-hover:underline">{r.symbol}</span>
                          <span className="text-xs text-text-secondary hidden md:inline">{r.name}</span>
                        </Link>
                      </td>
                      <td className="py-2.5 pr-3"><span className="text-[10px] px-2 py-0.5 bg-surface rounded">{r.asset_class}</span></td>
                      <td className="py-2.5 pr-3 text-right font-mono text-xs">${r.last_close.toFixed(2)}</td>
                      <td className="py-2.5 text-right"><span className={`font-mono font-bold ${r.scores.final >= 65 ? "text-gold" : r.scores.final >= 50 ? "" : "text-red-400"}`}>{r.scores.final.toFixed(1)}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {loadingScan && <p className="text-xs text-text-secondary mt-3 text-center animate-pulse">Scan en cours — les résultats se mettront à jour...</p>}
          </InfoCard>
        </div>
      )}
    </div>
  );
}

function MetricCard({ icon, label, value, unit, description, color }: {
  icon: React.ReactNode; label: string; value: string; unit?: string; description: string; color?: string;
}) {
  return (
    <div className="bg-card border border-border rounded-xl p-4 group">
      <div className="flex items-center gap-2 mb-2"><div className="text-text-secondary">{icon}</div><p className="text-xs text-text-secondary">{label}</p></div>
      <p className={`text-2xl font-mono font-semibold ${color || "text-text-primary"}`}>{value}{unit && <span className="text-sm text-text-secondary ml-1">{unit}</span>}</p>
      <p className="text-[10px] text-text-secondary mt-1 opacity-0 group-hover:opacity-100 transition-opacity">{description}</p>
    </div>
  );
}
