import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, TrendingUp, Target, Zap, Brain, Shield } from "lucide-react";
import axios from "axios";
import TradingChart from "../components/TradingChart";
import ScoreGauge from "../components/ui/ScoreGauge";
import InfoCard from "../components/ui/InfoCard";
import SignalBadge from "../components/ui/SignalBadge";
import { scannerApi, analyserApi, type ScanResult, type RegimeSummary } from "../services/api";

const REGIME_FR: Record<string, string> = {
  BULL: "Haussier",
  BEAR: "Baissier",
  RANGE: "Latéral",
  CRISIS: "Crise",
  TRANSITION: "Transition",
};

export default function Dashboard() {
  const [results, setResults] = useState<ScanResult[]>([]);
  const [regime, setRegime] = useState<RegimeSummary | null>(null);
  const [metaScore, setMetaScore] = useState<any>(null);
  const [signals, setSignals] = useState<any[]>([]);
  const [ohlcv, setOhlcv] = useState<any>(null);
  const [selectedSymbol, setSelectedSymbol] = useState("AAPL");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      scannerApi.scan(),
      analyserApi.getRegime(),
      axios.get("/api/performance/report"),
      axios.get("/api/scoring/signals"),
    ])
      .then(([scanRes, regimeRes, perfRes, sigRes]) => {
        setResults(scanRes.data);
        setRegime(regimeRes.data);
        setMetaScore(perfRes.data.meta_score);
        setSignals(sigRes.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    scannerApi.getOhlcv(selectedSymbol, 90).then((res) => setOhlcv(res.data));
  }, [selectedSymbol]);

  const avgScore = results.length ? results.reduce((s, r) => s + r.scores.final, 0) / results.length : 0;

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold">Dashboard</h2>
          <p className="text-text-secondary text-sm mt-1">Vue d'ensemble — {results.length} actifs surveillés</p>
        </div>
        {metaScore && <ScoreGauge score={metaScore.meta_score} size={90} sublabel="/100" label="Santé système" />}
      </div>

      {/* Métriques */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <MetricCard icon={<Activity size={16} />} label="Actifs scannés" value={loading ? "..." : String(results.length)} description="Nombre d'actifs analysés sur 9 critères" />
        <MetricCard icon={<Target size={16} />} label="Score moyen" value={loading ? "..." : avgScore.toFixed(1)} unit="/100" description="Moyenne pondérée des 9 critères" color={avgScore >= 60 ? "text-gold" : ""} />
        <MetricCard icon={<Zap size={16} />} label="Signaux GO" value={loading ? "..." : String(signals.length)} description="Signaux validés prêts pour l'exécution" color="text-gold" />
        <MetricCard icon={<Brain size={16} />} label="Régime" value={regime ? REGIME_FR[regime.dominant_regime] || regime.dominant_regime : "—"} description="Régime de marché dominant détecté" color={regime?.dominant_regime === "BULL" ? "text-gold" : regime?.dominant_regime === "BEAR" ? "text-red-400" : ""} />
        <MetricCard icon={<Shield size={16} />} label="Engagement" value={metaScore?.engagement || "—"} description={metaScore?.description || ""} color={metaScore?.engagement === "FULL" ? "text-gold" : metaScore?.engagement === "MINIMAL" ? "text-red-400" : ""} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Graphique */}
        <div className="lg:col-span-2">
          <InfoCard title="Graphique des prix" icon={<TrendingUp size={18} />} description="Chandeliers japonais : doré = hausse, gris = baisse. Les lignes sont les moyennes mobiles (tendance lissée).">
            <div className="flex justify-end mb-3">
              <select value={selectedSymbol} onChange={(e) => setSelectedSymbol(e.target.value)} className="bg-surface border border-border rounded-lg px-3 py-1.5 text-xs font-mono">
                {results.map((r) => (<option key={r.symbol} value={r.symbol}>{r.symbol} — {r.name}</option>))}
              </select>
            </div>
            {ohlcv?.data ? <TradingChart data={ohlcv.data} height={350} /> : <div className="h-64 flex items-center justify-center text-text-secondary">Chargement...</div>}
          </InfoCard>
        </div>

        {/* Signaux GO */}
        <InfoCard title="Signaux actifs" icon={<Zap size={18} />} description="Actifs validés par les 6 modules du pipeline. Cliquez pour le détail complet.">
          {signals.length === 0 ? (
            <p className="text-text-secondary text-sm py-4">Aucun signal GO. Le système surveille en continu.</p>
          ) : (
            <div className="space-y-2 max-h-[320px] overflow-y-auto">
              {signals.map((s: any) => (
                <Link key={s.symbol} to={`/asset/${s.symbol}`} className="flex items-center justify-between p-3 bg-surface rounded-xl hover:bg-gold/5 transition-colors group">
                  <div>
                    <span className="font-mono font-semibold text-gold group-hover:underline">{s.symbol}</span>
                    <div className="mt-1"><SignalBadge action="GO" direction={s.direction} size="sm" /></div>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-mono font-semibold">{s.thesis_score.toFixed(1)}</span>
                    <p className="text-[10px] text-text-secondary">${s.entry?.toFixed(2)}</p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </InfoCard>
      </div>

      {/* Pipeline */}
      <InfoCard title="Pipeline TradePilot" icon={<Activity size={18} />} description="Chaîne de 6 modules automatisés. Chaque module alimente le suivant. Le Module 6 renvoie un feedback au Module 1 pour s'améliorer (feedback loop).">
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {[
            { name: "Scanner", desc: "9 critères sur 51 actifs", icon: "🔍", num: 1 },
            { name: "Analyseur", desc: "Régime + stratégie optimale", icon: "🧠", num: 2 },
            { name: "Scoring", desc: "Score bayésien + Kelly", icon: "🎯", num: 3 },
            { name: "Exécution", desc: "Ordres 3 tranches + anti-biais", icon: "⚡", num: 4 },
            { name: "Portefeuille", desc: "Risk parity + stress tests", icon: "💼", num: 5 },
            { name: "Rentabilité", desc: "P&L + Monte Carlo + feedback", icon: "📈", num: 6 },
          ].map((m, i) => (
            <div key={m.name} className="flex items-center">
              <div className="bg-surface rounded-xl p-3 min-w-[150px] border border-gold/10">
                <div className="flex items-center gap-2 mb-1">
                  <span>{m.icon}</span>
                  <span className="text-xs font-semibold">M{m.num} — {m.name}</span>
                </div>
                <p className="text-[10px] text-text-secondary">{m.desc}</p>
                <div className="flex items-center gap-1 mt-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-gold animate-pulse" />
                  <span className="text-[10px] text-gold">Actif</span>
                </div>
              </div>
              {i < 5 && <span className="text-text-secondary mx-1">→</span>}
            </div>
          ))}
        </div>
      </InfoCard>

      {/* Top actifs */}
      <div className="mt-6">
        <InfoCard title="Classement des actifs" icon={<Target size={18} />} description="Classés par score global (9 critères pondérés). Cliquez sur un symbole pour l'analyse détaillée.">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-text-secondary border-b border-border">
                  <th className="pb-3 pr-3 w-8">#</th>
                  <th className="pb-3 pr-3">Actif</th>
                  <th className="pb-3 pr-3">Classe</th>
                  <th className="pb-3 pr-3 text-right">Prix</th>
                  <th className="pb-3 pr-3 text-right">AT</th>
                  <th className="pb-3 text-right">Score</th>
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
                    <td className="py-2.5 pr-3 text-right font-mono text-xs">{r.scores.technical.toFixed(0)}</td>
                    <td className="py-2.5 text-right">
                      <span className={`font-mono font-bold ${r.scores.final >= 65 ? "text-gold" : r.scores.final >= 50 ? "text-text-primary" : "text-red-400"}`}>
                        {r.scores.final.toFixed(1)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </InfoCard>
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, unit, description, color }: {
  icon: React.ReactNode; label: string; value: string; unit?: string; description: string; color?: string;
}) {
  return (
    <div className="bg-card border border-border rounded-xl p-4 group">
      <div className="flex items-center gap-2 mb-2">
        <div className="text-text-secondary">{icon}</div>
        <p className="text-xs text-text-secondary">{label}</p>
      </div>
      <p className={`text-2xl font-mono font-semibold ${color || "text-text-primary"}`}>
        {value}{unit && <span className="text-sm text-text-secondary ml-1">{unit}</span>}
      </p>
      <p className="text-[10px] text-text-secondary mt-1 opacity-0 group-hover:opacity-100 transition-opacity">{description}</p>
    </div>
  );
}
