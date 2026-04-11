import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import axios from "axios";
import TradingChart from "../components/TradingChart";
import { scannerApi, analyserApi, scoringApi } from "../services/api";
import type { ScanResult, AnalysisResult, TradeThesis, OHLCVData } from "../services/api";

const CRITERIA_LABELS: Record<string, string> = {
  correlation: "Corrélation",
  sentiment: "Sentiment",
  technical: "Analyse Technique",
  genome: "Génome Explosif",
  ipi: "Capital Institutionnel",
  ivf: "Vélocité Fondamentale",
  mts: "Macro Tailwind",
  sgi: "Topologie Sociale",
  sus: "Unicité du Signal",
};

const CRITERIA_ICONS: Record<string, string> = {
  correlation: "🔗",
  sentiment: "💬",
  technical: "📊",
  genome: "🧬",
  ipi: "🏦",
  ivf: "⚡",
  mts: "🌍",
  sgi: "👥",
  sus: "💎",
};

const REGIME_COLORS: Record<string, string> = {
  BULL: "text-gold bg-gold/10 border-gold/20",
  BEAR: "text-red-400 bg-red-400/10 border-red-400/20",
  RANGE: "text-blue-400 bg-blue-400/10 border-blue-400/20",
  CRISIS: "text-red-600 bg-red-600/10 border-red-600/20",
  TRANSITION: "text-yellow-400 bg-yellow-400/10 border-yellow-400/20",
};

export default function AssetDetail() {
  const { symbol } = useParams<{ symbol: string }>();
  const [ohlcv, setOhlcv] = useState<OHLCVData | null>(null);
  const [scan, setScan] = useState<any>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [thesis, setThesis] = useState<TradeThesis | null>(null);
  const [mta, setMta] = useState<any>(null);
  const [sentiment, setSentiment] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState<"daily" | "1h">("daily");

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);

    Promise.all([
      scannerApi.getOhlcv(symbol, 250),
      axios.get(`/api/scanner/results/${symbol}`),
      axios.get(`/api/analyser/analyse/${symbol}`),
      axios.get(`/api/scoring/thesis/${symbol}`),
      axios.get(`/api/scanner/mta/${symbol}`),
      axios.get(`/api/scanner/sentiment/${symbol}`),
    ])
      .then(([ohlcvRes, scanRes, analysisRes, thesisRes, mtaRes, sentRes]) => {
        setOhlcv(ohlcvRes.data);
        setScan(scanRes.data);
        setAnalysis(analysisRes.data);
        setThesis(thesisRes.data);
        setMta(mtaRes.data);
        setSentiment(sentRes.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [symbol]);

  const loadTimeframe = (tf: "daily" | "1h") => {
    setTimeframe(tf);
    if (!symbol) return;
    if (tf === "1h") {
      axios.get(`/api/scanner/ohlcv-1h/${symbol}?limit=168`).then((res) => {
        setOhlcv({
          symbol,
          name: scan?.name || symbol,
          count: res.data.count,
          data: res.data.data.map((d: any) => ({
            date: d.datetime.split("T")[0],
            ...d,
          })),
        });
      });
    } else {
      scannerApi.getOhlcv(symbol, 250).then((res) => setOhlcv(res.data));
    }
  };

  if (loading) return <p className="text-text-secondary p-6">Chargement...</p>;
  if (!scan || scan.error) return <p className="text-red-400 p-6">Actif non trouvé</p>;

  const scores = scan.scores || {};
  const details = scan.details || {};

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link to="/scanner" className="text-text-secondary hover:text-text-primary">
          <ArrowLeft size={20} />
        </Link>
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold font-mono text-gold">{symbol}</h2>
            <span className="text-xs px-2 py-0.5 bg-surface border border-border rounded">
              {scan.asset_class}
            </span>
            {analysis?.regime && (
              <span className={`text-xs px-2 py-0.5 border rounded font-semibold ${REGIME_COLORS[analysis.regime.regime] || ""}`}>
                {analysis.regime.regime}
              </span>
            )}
          </div>
          <p className="text-text-secondary text-sm">{scan.name}</p>
        </div>
        <div className="ml-auto text-right">
          <p className="text-3xl font-mono font-bold">${scan.last_close?.toFixed(2)}</p>
          <p className="text-xs text-text-secondary">{scan.data_points} jours de données</p>
        </div>
      </div>

      {/* Score Final + Thèse */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-text-secondary mb-1">Score Scanner</p>
          <p className="text-3xl font-mono font-bold text-gold">{scores.final?.toFixed(1)}</p>
          <p className="text-xs text-text-secondary mt-1">/100</p>
        </div>
        {thesis && thesis.action !== undefined && (
          <>
            <div className="bg-card border border-border rounded-xl p-4">
              <p className="text-xs text-text-secondary mb-1">Action</p>
              <p className={`text-2xl font-bold ${
                thesis.action === "GO" ? "text-gold" : thesis.action === "WAIT" ? "text-yellow-400" : "text-text-secondary"
              }`}>{thesis.action}</p>
              {thesis.thesis_score && (
                <p className="text-xs text-text-secondary mt-1">Score thèse: {thesis.thesis_score.toFixed(1)}</p>
              )}
            </div>
            <div className="bg-card border border-border rounded-xl p-4">
              <p className="text-xs text-text-secondary mb-1">Stratégie</p>
              <p className="text-sm font-semibold mt-1">{thesis.strategy || "—"}</p>
              {thesis.direction && thesis.direction !== "NEUTRAL" && (
                <span className={`text-xs px-2 py-0.5 border rounded font-semibold mt-2 inline-block ${
                  thesis.direction === "LONG" ? "text-gold bg-gold/10 border-gold/20" : "text-red-400 bg-red-400/10 border-red-400/20"
                }`}>{thesis.direction}</span>
              )}
            </div>
            {thesis.sizing && thesis.sizing.position_size_usd > 0 && (
              <div className="bg-card border border-border rounded-xl p-4">
                <p className="text-xs text-text-secondary mb-1">Sizing Kelly</p>
                <p className="text-xl font-mono font-semibold">${thesis.sizing.position_size_usd.toFixed(0)}</p>
                <p className="text-xs text-text-secondary mt-1">
                  R:R {thesis.sizing.risk_reward_ratio} | WR {(thesis.sizing.win_rate_estimate * 100).toFixed(0)}%
                </p>
              </div>
            )}
          </>
        )}
      </div>

      {/* Chart */}
      <div className="bg-card border border-border rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-text-secondary">Graphique</h3>
          <div className="flex gap-1">
            {(["daily", "1h"] as const).map((tf) => (
              <button
                key={tf}
                onClick={() => loadTimeframe(tf)}
                className={`px-3 py-1 text-xs rounded transition-colors ${
                  timeframe === tf
                    ? "bg-gold/10 text-gold border border-gold/20"
                    : "text-text-secondary hover:text-text-primary bg-surface"
                }`}
              >
                {tf === "daily" ? "Daily" : "1H"}
              </button>
            ))}
          </div>
        </div>
        {ohlcv?.data && ohlcv.data.length > 0 ? (
          <TradingChart data={ohlcv.data} height={450} />
        ) : (
          <div className="h-96 flex items-center justify-center text-text-secondary">
            Pas de données
          </div>
        )}
        {/* Niveaux de prix si thèse GO */}
        {thesis && thesis.entry && thesis.action === "GO" && (
          <div className="flex gap-6 mt-4 text-sm">
            <div><span className="text-text-secondary">Entry </span><span className="font-mono">${thesis.entry.toFixed(2)}</span></div>
            <div><span className="text-text-secondary">SL </span><span className="font-mono text-red-400">${thesis.stop_loss.toFixed(2)}</span></div>
            <div><span className="text-text-secondary">TP1 </span><span className="font-mono text-gold">${thesis.take_profit_1.toFixed(2)}</span></div>
            <div><span className="text-text-secondary">TP2 </span><span className="font-mono text-gold">${thesis.take_profit_2.toFixed(2)}</span></div>
          </div>
        )}
      </div>

      {/* 9 Critères */}
      <div className="bg-card border border-border rounded-xl p-6 mb-6">
        <h3 className="text-sm font-medium text-text-secondary mb-4">9 Critères du Scanner</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(CRITERIA_LABELS).map(([key, label]) => {
            const score = scores[key] ?? 0;
            const weight = scan.weights?.[key] ?? 0;
            return (
              <div key={key} className="bg-surface rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span>{CRITERIA_ICONS[key]}</span>
                    <span className="text-sm font-medium">{label}</span>
                  </div>
                  <span className={`text-lg font-mono font-bold ${
                    score >= 70 ? "text-gold" : score >= 50 ? "text-text-primary" : "text-red-400"
                  }`}>
                    {score.toFixed(1)}
                  </span>
                </div>
                <div className="h-2 bg-background rounded-full overflow-hidden mb-1">
                  <div
                    className={`h-full rounded-full transition-all ${
                      score >= 70 ? "bg-gold" : score >= 50 ? "bg-text-secondary" : "bg-red-400"
                    }`}
                    style={{ width: `${score}%` }}
                  />
                </div>
                <p className="text-[10px] text-text-secondary">Poids: {(weight * 100).toFixed(0)}%</p>
              </div>
            );
          })}
        </div>
        {scan.vetoed && (
          <div className="mt-4 p-3 bg-red-400/10 border border-red-400/20 rounded-lg">
            <p className="text-sm text-red-400 font-semibold">VETO actif</p>
            {scan.veto_reasons?.map((r: string, i: number) => (
              <p key={i} className="text-xs text-red-400/80 mt-1">{r}</p>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Détails enrichis */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Détails</h3>
          <div className="space-y-3 text-sm">
            {details.genome && (
              <DetailRow label="Cycle Wyckoff" value={`Phase ${details.genome.cycle_phase}`} sub={`${details.genome.seismograph_active} micro-signaux actifs`} />
            )}
            {details.ipi && (
              <DetailRow label="A/D Line" value={details.ipi.ad_trend} sub={`Smart Money: ${details.ipi.smart_money}`} />
            )}
            {details.ivf && (
              <DetailRow label="Accélération prix" value={details.ivf.acceleration.toFixed(1)} sub={`Force relative: ${details.ivf.relative_strength.toFixed(1)}`} />
            )}
            {details.mts && (
              <DetailRow label="Macro" value={details.mts.cycle} sub={`Taux: ${details.mts.rates} | Risk: ${details.mts.risk}`} />
            )}
            {details.sgi && (
              <DetailRow label="Social" value={`${details.sgi.mentions} mentions`} sub={`Signal/Bruit: ${details.sgi.signal_noise}`} />
            )}
            {details.sus && (
              <DetailRow label="Unicité" value={`Crowding: ${details.sus.crowding}`} sub={`Novelty: ${details.sus.novelty}`} />
            )}
          </div>
        </div>

        {/* Multi-Timeframe + Sentiment */}
        <div className="space-y-6">
          {mta && !mta.error && (
            <div className="bg-card border border-border rounded-xl p-6">
              <h3 className="text-sm font-medium text-text-secondary mb-4">Multi-Timeframe</h3>
              <div className="flex items-center gap-4 mb-3">
                <span className={`text-lg font-mono font-bold ${mta.mta_score >= 60 ? "text-gold" : "text-text-primary"}`}>
                  {mta.mta_score.toFixed(1)}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  mta.alignment === "ALIGNED" ? "bg-gold/10 text-gold" :
                  mta.alignment === "DIVERGENT" ? "bg-red-400/10 text-red-400" :
                  "bg-surface text-text-secondary"
                }`}>{mta.alignment}</span>
              </div>
              {Object.entries(mta.timeframes || {}).map(([tf, data]: [string, any]) => (
                <div key={tf} className="flex items-center justify-between text-sm mb-1">
                  <span className="text-text-secondary">{tf}</span>
                  <span className={data.direction === "BULLISH" ? "text-gold" : data.direction === "BEARISH" ? "text-red-400" : "text-text-secondary"}>
                    {data.direction} ({data.strength.toFixed(0)}%)
                  </span>
                </div>
              ))}
            </div>
          )}

          {sentiment && !sentiment.error && (
            <div className="bg-card border border-border rounded-xl p-6">
              <h3 className="text-sm font-medium text-text-secondary mb-4">Sentiment</h3>
              <div className="flex items-center gap-4 mb-3">
                <span className="text-lg font-mono font-bold">{sentiment.score.toFixed(1)}</span>
                <span className="text-xs text-text-secondary">{sentiment.num_mentions} mentions</span>
              </div>
              <div className="flex gap-3 text-xs">
                <span className="text-gold">{sentiment.sentiment_breakdown?.positive || 0} positifs</span>
                <span className="text-text-secondary">{sentiment.sentiment_breakdown?.neutral || 0} neutres</span>
                <span className="text-red-400">{sentiment.sentiment_breakdown?.negative || 0} négatifs</span>
              </div>
            </div>
          )}

          {/* Régime détaillé */}
          {analysis?.regime && (
            <div className="bg-card border border-border rounded-xl p-6">
              <h3 className="text-sm font-medium text-text-secondary mb-4">Régime de marché</h3>
              <div className="space-y-2">
                {Object.entries(analysis.regime.probabilities)
                  .sort(([, a], [, b]) => b - a)
                  .map(([regime, prob]) => (
                    <div key={regime}>
                      <div className="flex justify-between text-sm mb-1">
                        <span>{regime}</span>
                        <span className="font-mono">{(prob * 100).toFixed(1)}%</span>
                      </div>
                      <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                        <div className="h-full bg-gold rounded-full" style={{ width: `${prob * 100}%` }} />
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Backtest ranking */}
      {analysis?.strategy_ranking && analysis.strategy_ranking.length > 0 && (
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Classement stratégies (backtest)</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {analysis.strategy_ranking.map((r: any, i: number) => (
              <div key={r.strategy} className={`bg-surface rounded-lg p-3 ${i === 0 ? "border border-gold/20" : ""}`}>
                <p className="text-sm font-semibold">{r.strategy.replace("_", " ")}</p>
                <p className={`text-lg font-mono font-bold mt-1 ${r.adjusted_sharpe > 0 ? "text-gold" : "text-red-400"}`}>
                  {r.adjusted_sharpe.toFixed(3)}
                </p>
                <p className="text-[10px] text-text-secondary mt-1">
                  BT: {r.backtest_sharpe.toFixed(3)} | Boost: {r.regime_boost > 0 ? "+" : ""}{r.regime_boost.toFixed(3)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function DetailRow({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-text-secondary">{label}</span>
      <div className="text-right">
        <span className="font-mono">{value}</span>
        {sub && <p className="text-[10px] text-text-secondary">{sub}</p>}
      </div>
    </div>
  );
}
