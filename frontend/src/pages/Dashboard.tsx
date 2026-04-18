import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, TrendingUp, Target, Zap, Brain, Shield, Lightbulb, Trash2, ArrowUp, ArrowDown, Play } from "lucide-react";
import TradingChart from "../components/TradingChart";
import ScoreGauge from "../components/ui/ScoreGauge";
import InfoCard from "../components/ui/InfoCard";
import SignalBadge from "../components/ui/SignalBadge";
import LoadingScreen from "../components/LoadingScreen";
import api, { scannerApi, analyserApi, type ScanResult, type RegimeSummary } from "../services/api";

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
  const [theses, setTheses] = useState<any[]>([]);
  const [loadingMain, setLoadingMain] = useState(true);
  const [loadingScan, setLoadingScan] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineMsg, setPipelineMsg] = useState("");
  const [pipelineStatus, setPipelineStatus] = useState<any>(null);
  const [topMovers, setTopMovers] = useState<any>(null);

  const refreshQuick = () => {
    Promise.all([
      analyserApi.getRegime().catch(() => ({ data: null })),
      api.get("/performance/meta-score").catch(() => ({ data: null })),
      api.get("/scoring/signals").catch(() => ({ data: [] })),
      api.get("/analyser/theses").catch(() => ({ data: [] })),
      api.get("/scanner/pipeline-status").catch(() => ({ data: null })),
      api.get("/scanner/top-movers").catch(() => ({ data: null })),
    ])
      .then(([regimeRes, metaRes, sigRes, thesesRes, pipeRes, moversRes]) => {
        if (regimeRes.data) setRegime(regimeRes.data);
        if (metaRes.data) setMetaScore(metaRes.data);
        setSignals(Array.isArray(sigRes.data) ? sigRes.data : []);
        setTheses(Array.isArray(thesesRes.data) ? thesesRes.data : []);
        if (pipeRes.data) setPipelineStatus(pipeRes.data);
        if (moversRes.data) setTopMovers(moversRes.data);
      })
      .catch(() => setError("Erreur de connexion au serveur"))
      .finally(() => setLoadingMain(false));
  };

  const deleteThesis = (id: string) => {
    api.delete(`/analyser/thesis/${id}`).then(() => refreshQuick());
  };

  useEffect(() => {
    // Chargement initial
    refreshQuick();

    // Scan (une seule fois)
    scannerApi.scan()
      .then((res) => {
        if (Array.isArray(res.data)) setResults(res.data);
      })
      .catch(() => {})
      .finally(() => setLoadingScan(false));

    // Auto-refresh données rapides toutes les 60s
    const interval = setInterval(refreshQuick, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    scannerApi.getOhlcv(selectedSymbol, 1000).then((res) => setOhlcv(res.data)).catch(() => {});
  }, [selectedSymbol]);

  if (loadingMain && results.length === 0) {
    return <LoadingScreen message="Connexion au pipeline Bilok-TradePilot..." />;
  }

  const avgScore = results.length ? results.reduce((s, r) => s + r.scores.final, 0) / results.length : 0;

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold">Dashboard</h2>
          <p className="text-text-secondary text-sm mt-1 max-w-3xl">
            Vue d'ensemble en temps réel du système Bilok-TradePilot — métriques clés, statut du pipeline, signaux GO actifs, top movers du jour et graphique de prix. Le tableau de bord centralise toutes les informations pour une prise de décision rapide.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setPipelineRunning(true);
              setPipelineMsg("");
              api.post("/scanner/launch-pipeline")
                .then((res) => setPipelineMsg(res.data.message || "Pipeline lancé"))
                .catch(() => setPipelineMsg("Erreur de lancement"))
                .finally(() => setTimeout(() => setPipelineRunning(false), 3000));
            }}
            disabled={pipelineRunning}
            className="flex items-center gap-2 px-4 py-2 bg-gold/10 text-gold border border-gold/20 rounded-xl text-sm font-semibold hover:bg-gold/20 transition-colors disabled:opacity-50"
          >
            <Play size={14} fill="currentColor" />
            {pipelineRunning ? "Lancement..." : "Lancer le pipeline"}
          </button>
          {metaScore && <ScoreGauge score={metaScore.meta_score} size={90} sublabel="/100" label="Santé système" />}
        </div>
      </div>

      {pipelineMsg && (
        <div className="mb-4 p-3 bg-gold/10 border border-gold/20 rounded-xl text-sm text-gold">{pipelineMsg}</div>
      )}

      {pipelineStatus?.running && (
        <div className="mb-4 p-4 bg-gold/5 border border-gold/20 rounded-xl">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-gold animate-pulse" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-gold">Pipeline en cours</p>
              <p className="text-xs text-text-secondary">
                {pipelineStatus.current_step
                  ? `Étape : ${pipelineStatus.current_step.replace("run_", "").replace("build_", "")}`
                  : "Traitement en cours..."}
                {pipelineStatus.cache_age_minutes != null && ` — Dernière MAJ il y a ${pipelineStatus.cache_age_minutes} min`}
              </p>
            </div>
            <div className="flex gap-1">
              {["scanner", "correlation_cache", "analyser", "scoring", "execution", "portfolio", "performance"].map((step) => (
                <div key={step} className={`w-2 h-2 rounded-full ${
                  pipelineStatus.current_step === step ? "bg-gold animate-pulse" :
                  pipelineStatus.current_step && ["scanner","correlation_cache","analyser","scoring","execution","portfolio","performance"].indexOf(step) < ["scanner","correlation_cache","analyser","scoring","execution","portfolio","performance"].indexOf(pipelineStatus.current_step) ? "bg-emerald-400" :
                  "bg-border"
                }`} title={step} />
              ))}
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-400/10 border border-red-400/20 rounded-xl text-sm text-red-400">
          {error} — vérifiez que le backend tourne sur le port 8000.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <MetricCard icon={<Lightbulb size={16} />} label="Thèses M0" value={String(theses.length)} description={theses.length > 0 ? `Conviction moy. : ${theses.reduce((s: number, t: any) => s + (t.conviction === "CERTAINE" ? 90 : t.conviction === "FORTE" ? 75 : t.conviction === "MOYENNE" ? 50 : 25), 0) / theses.length}%` : "Aucune conviction active"} color={theses.length > 0 ? "text-gold" : ""} />
        <MetricCard icon={<Activity size={16} />} label="Actifs scannés" value={loadingScan ? "..." : String(results.length)} description="Analysés sur 10 critères" />
        <MetricCard icon={<Target size={16} />} label="Score moyen" value={loadingScan ? "..." : avgScore.toFixed(1)} unit="/100" description="Moyenne des 10 critères" color={avgScore >= 60 ? "text-gold" : ""} />
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
            {ohlcv?.data ? <TradingChart data={ohlcv.data} height={400} symbol={selectedSymbol} /> : <div className="h-64 flex items-center justify-center text-text-secondary text-sm">Chargement...</div>}
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

      {/* Mes convictions M0 */}
      {theses.length > 0 && (
        <div className="mb-6">
          <InfoCard title="M0 — Mes Convictions" icon={<Lightbulb size={18} />} description="Thèses actives intégrées au scoring. Supprimez celles qui ne tiennent plus.">
            <div className="space-y-2">
              {theses.slice(0, 5).map((t: any) => (
                <div key={t.id} className="flex items-center justify-between bg-surface rounded-xl px-4 py-3 group">
                  <div className="flex items-center gap-3">
                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${t.direction === "HAUSSE" ? "bg-gold/10" : "bg-red-400/10"}`}>
                      {t.direction === "HAUSSE" ? <ArrowUp size={14} className="text-gold" /> : <ArrowDown size={14} className="text-red-400" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm">{t.theme}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold ${
                          t.conviction === "CERTAINE" ? "text-gold bg-gold/10 border-gold/20" :
                          t.conviction === "FORTE" ? "text-gold bg-gold/5 border-gold/10" :
                          t.conviction === "MOYENNE" ? "text-yellow-400 bg-yellow-400/5 border-yellow-400/10" :
                          "text-text-secondary bg-surface border-border"
                        }`}>{t.conviction}</span>
                      </div>
                      {t.reason && <p className="text-[10px] text-text-secondary mt-0.5">{t.reason}</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="text-[10px] text-text-secondary">{t.horizon_days}j restants</p>
                      <p className="text-[10px] text-text-secondary">{t.symbols_long?.length || 0} actifs</p>
                    </div>
                    <button
                      onClick={() => deleteThesis(t.id)}
                      className="p-1.5 text-text-secondary hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                      title="Supprimer cette thèse"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
              <p className="text-[10px] text-text-secondary">{theses.length} thèse{theses.length > 1 ? "s" : ""} active{theses.length > 1 ? "s" : ""} — influencent le scoring M3</p>
              <Link to="/theses" className="text-[10px] text-gold hover:underline">Gérer mes thèses →</Link>
            </div>
          </InfoCard>
        </div>
      )}

      {/* Top Movers du jour */}
      {topMovers && (topMovers.gainers?.length > 0 || topMovers.losers?.length > 0) && (
        <div className="mb-6">
          <InfoCard title="Top Movers du jour" icon={<TrendingUp size={18} />} description={`${topMovers.total_assets} actifs surveillés${topMovers.market_comparison ? ` — Taux de détection : ${topMovers.market_comparison.detection_rate}% des top movers du marché global` : ""}.`}>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Gainers */}
              <div>
                <p className="text-[10px] text-emerald-400 uppercase tracking-wider font-semibold mb-2">Hausse</p>
                <div className="space-y-1">
                  {(topMovers.gainers ?? []).slice(0, 10).map((m: any) => (
                    <div key={m.symbol} className="flex items-center justify-between py-1.5 px-2 rounded-lg hover:bg-surface/50 transition-colors">
                      <div className="flex items-center gap-2">
                        <Link to={`/asset/${m.symbol}`} className="font-mono font-semibold text-gold text-xs hover:underline">{m.symbol}</Link>
                        {m.in_position && <span className="text-[8px] px-1 py-0.5 rounded bg-gold/10 text-gold border border-gold/20 font-bold">EN POS</span>}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-text-secondary">${m.price}</span>
                        <span className="font-mono text-xs font-bold text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded">+{m.change_pct}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              {/* Losers */}
              <div>
                <p className="text-[10px] text-red-400 uppercase tracking-wider font-semibold mb-2">Baisse</p>
                <div className="space-y-1">
                  {(topMovers.losers ?? []).slice(0, 10).map((m: any) => (
                    <div key={m.symbol} className="flex items-center justify-between py-1.5 px-2 rounded-lg hover:bg-surface/50 transition-colors">
                      <div className="flex items-center gap-2">
                        <Link to={`/asset/${m.symbol}`} className="font-mono font-semibold text-gold text-xs hover:underline">{m.symbol}</Link>
                        {m.in_position && <span className="text-[8px] px-1 py-0.5 rounded bg-red-400/10 text-red-400 border border-red-400/20 font-bold">EN POS</span>}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-text-secondary">${m.price}</span>
                        <span className="font-mono text-xs font-bold text-red-400 bg-red-400/10 px-1.5 py-0.5 rounded">{m.change_pct}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            {/* Taux de détection + manqués */}
            {topMovers.market_comparison && (
              <div className="mt-4 pt-4 border-t border-border">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-[10px] text-text-secondary uppercase tracking-wider font-semibold">Couverture marché global</p>
                  <span className={`font-mono text-sm font-bold ${(topMovers.market_comparison.detection_rate ?? 0) >= 70 ? "text-emerald-400" : (topMovers.market_comparison.detection_rate ?? 0) >= 50 ? "text-yellow-400" : "text-red-400"}`}>
                    {topMovers.market_comparison.detection_rate ?? "—"}%
                  </span>
                </div>
                <div className="h-2 bg-surface rounded-full overflow-hidden mb-2">
                  <div className={`h-full rounded-full ${(topMovers.market_comparison.detection_rate ?? 0) >= 70 ? "bg-emerald-400" : (topMovers.market_comparison.detection_rate ?? 0) >= 50 ? "bg-yellow-400" : "bg-red-400"}`} style={{ width: `${topMovers.market_comparison.detection_rate ?? 0}%` }} />
                </div>
                <p className="text-[10px] text-text-secondary">
                  {topMovers.market_comparison.detected}/{topMovers.market_comparison.market_top_count} top movers du marché sont dans nos {topMovers.total_assets} actifs
                </p>
                {topMovers.market_comparison.missed?.length > 0 && (
                  <div className="mt-2">
                    <p className="text-[10px] text-red-400 font-semibold mb-1">Actifs manqués :</p>
                    <div className="flex flex-wrap gap-1">
                      {topMovers.market_comparison.missed.map((m: any) => (
                        <span key={m.symbol} className="text-[9px] px-1.5 py-0.5 rounded bg-red-400/10 text-red-400 border border-red-400/20 font-mono">{m.symbol}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </InfoCard>
        </div>
      )}

      <InfoCard title="Pipeline Bilok-TradePilot" icon={<Activity size={18} />} description="7 modules (M0→M6) avec feedback loop. Cliquez pour naviguer.">
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {[
            { name: "Thèses", desc: theses.length > 0 ? `${theses.length} conviction${theses.length > 1 ? "s" : ""} active${theses.length > 1 ? "s" : ""}` : "Aucune conviction", icon: "💡", link: "/theses" },
            { name: "Scanner", desc: "10 critères, 218 actifs", icon: "🔍", link: "/scanner" },
            { name: "Analyseur", desc: "Régime + 14 stratégies", icon: "🧠", link: "/analyser" },
            { name: "Scoring", desc: "V2 — 8 sources", icon: "🎯", link: "/scoring" },
            { name: "Exécution", desc: "Bracket Orders Alpaca", icon: "⚡", link: "/execution" },
            { name: "Portefeuille", desc: "VaR + Risk Budget", icon: "💼", link: "/portfolio" },
            { name: "Performance", desc: "P&L + feedback loop", icon: "📈", link: "/performance" },
          ].map((m, i) => (
            <div key={m.name} className="flex items-center">
              <Link to={m.link} className="bg-surface rounded-xl p-3 min-w-[130px] border border-gold/10 hover:border-gold/30 transition-colors">
                <div className="flex items-center gap-2 mb-1"><span>{m.icon}</span><span className="text-xs font-semibold">M{i} — {m.name}</span></div>
                <p className="text-[10px] text-text-secondary">{m.desc}</p>
                <div className="flex items-center gap-1 mt-2"><div className="w-1.5 h-1.5 rounded-full bg-gold animate-pulse" /><span className="text-[10px] text-gold">Actif</span></div>
              </Link>
              {i < 6 && <span className="text-text-secondary mx-1">→</span>}
            </div>
          ))}
          <span className="text-text-secondary mx-1">↩</span>
        </div>
        <p className="text-[10px] text-text-secondary mt-2 text-center">M0 Thèses → M1 Scanner → M2 Analyseur → M3 Scoring → M4 Exécution → M5 Portefeuille → M6 Performance → Feedback ↩ M0</p>
      </InfoCard>

      {results.length > 0 && (
        <div className="mt-6">
          <InfoCard title="Classement des actifs" icon={<Target size={18} />} description="Score global = 10 critères pondérés. Cliquez pour l'analyse détaillée.">
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
