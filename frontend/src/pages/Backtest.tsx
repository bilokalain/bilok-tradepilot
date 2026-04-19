import { useEffect, useState } from "react";
import { FlaskConical, TrendingUp, GitBranch, Lightbulb, BarChart3 } from "lucide-react";
import api, { scannerApi } from "../services/api";
import EquityCurve from "../components/EquityCurve";
import InfoCard from "../components/ui/InfoCard";

const ALL_STRATEGIES: Record<string, string> = {
  trend_following: "Trend Following",
  mean_reversion: "Mean Reversion",
  breakout: "Breakout",
  momentum: "Momentum",
  adaptive_trend: "Adaptive Trend",
  multi_signal: "Multi-Signal",
  keltner_breakout: "Keltner Breakout",
  vwap_reversion: "VWAP Reversion",
  momentum_rotation: "Momentum Rotation",
  mean_reversion_v2: "Mean Reversion V2",
  fibonacci: "Fibonacci",
  ichimoku: "Ichimoku",
  regime_cascade: "Regime Cascade",
  volatility_explosion: "Volatility Explosion",
  anti_consensus: "Anti-Consensus Alpha",
};

type Tab = "strategies" | "correlation" | "walkforward" | "thesis" | "deepanalysis";

export default function Backtest() {
  const [tab, setTab] = useState<Tab>("strategies");

  const tabs = [
    { id: "strategies" as Tab, label: "Stratégies", icon: TrendingUp },
    { id: "correlation" as Tab, label: "Corrélation", icon: GitBranch },
    { id: "walkforward" as Tab, label: "Walk-Forward", icon: BarChart3 },
    { id: "thesis" as Tab, label: "Thèse", icon: Lightbulb },
    { id: "deepanalysis" as Tab, label: "Analyse profonde", icon: FlaskConical },
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold mb-2">Backtesting</h2>
      <p className="text-text-secondary text-sm mb-6 max-w-3xl">
        Validation historique des stratégies — walk-forward testing sur 10 ans avec fenêtre glissante, simulation Monte Carlo (10 000 runs), et métriques professionnelles (Sharpe, Sortino, Calmar, Profit Factor). Intègre les frais de transaction et le slippage pour des résultats réalistes.
      </p>

      {/* Onglets */}
      <div className="flex border-b border-border mb-6 overflow-x-auto">
        {tabs.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-5 py-3 text-sm whitespace-nowrap border-b-2 transition-colors ${
                tab === t.id
                  ? "border-gold text-gold font-semibold"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              }`}
            >
              <Icon size={15} />
              {t.label}
            </button>
          );
        })}
      </div>

      {tab === "strategies" && <StrategiesBacktest />}
      {tab === "correlation" && <CorrelationBacktest />}
      {tab === "walkforward" && <WalkForwardBacktest />}
      {tab === "thesis" && <ThesisBacktest />}
      {tab === "deepanalysis" && <DeepAnalysis />}
    </div>
  );
}


// ============================================================
// 1. STRATÉGIES
// ============================================================

function StrategiesBacktest() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState("AAPL");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<any>(null);

  useEffect(() => {
    scannerApi.getAssets().then((res) => setSymbols(res.data.map((a: any) => a.symbol)));
  }, []);

  const runBacktest = () => {
    setLoading(true);
    api.get(`/backtest/compare/${selectedSymbol}`)
      .then((res) => {
        setResults(res.data.strategies || []);
        if (res.data.strategies?.length > 0) setSelected(res.data.strategies[0]);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  return (
    <InfoCard title="Backtest Stratégies" icon={<TrendingUp size={18} />} description="Teste les 9 stratégies sur un actif et compare les résultats (Sharpe, Win Rate, Drawdown). Utilise tout l'historique disponible (jusqu'à 64 ans).">
      <div className="flex items-center gap-3 mb-4">
        <select value={selectedSymbol} onChange={(e) => setSelectedSymbol(e.target.value)} className="bg-surface border border-border rounded-lg px-3 py-2 text-sm font-mono">
          {symbols.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <button onClick={runBacktest} disabled={loading} className="px-4 py-2 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm hover:bg-gold/20 disabled:opacity-50">
          {loading ? "Calcul..." : "Lancer"}
        </button>
      </div>

      {results.length > 0 && (
        <>
          {/* Interprétation intelligente */}
          <BacktestInterpretation results={results} symbol={selectedSymbol} />

          <div className="overflow-x-auto mb-4">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-text-secondary border-b border-border">
                  <th className="pb-2 pr-3">Stratégie</th>
                  <th className="pb-2 pr-3 text-right">Return</th>
                  <th className="pb-2 pr-3 text-right">Sharpe</th>
                  <th className="pb-2 pr-3 text-right">Win Rate</th>
                  <th className="pb-2 pr-3 text-right">Max DD</th>
                  <th className="pb-2 pr-3 text-right">Trades</th>
                  <th className="pb-2 text-right">PF</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r: any) => (
                  <tr key={r.strategy} onClick={() => setSelected(r)} className={`border-b border-border/30 cursor-pointer hover:bg-surface ${selected?.strategy === r.strategy ? "bg-gold/5" : ""}`}>
                    <td className="py-2 pr-3 font-semibold">{ALL_STRATEGIES[r.strategy] || r.strategy}</td>
                    <td className={`py-2 pr-3 text-right font-mono ${r.total_return >= 0 ? "text-gold" : "text-red-400"}`}>{r.total_return >= 0 ? "+" : ""}{r.total_return}%</td>
                    <td className={`py-2 pr-3 text-right font-mono ${r.sharpe_ratio >= 1 ? "text-gold" : r.sharpe_ratio < 0 ? "text-red-400" : ""}`}>{r.sharpe_ratio}</td>
                    <td className="py-2 pr-3 text-right font-mono">{r.win_rate}%</td>
                    <td className="py-2 pr-3 text-right font-mono text-red-400">{r.max_drawdown}%</td>
                    <td className="py-2 pr-3 text-right font-mono">{r.num_trades}</td>
                    <td className={`py-2 text-right font-mono ${r.profit_factor >= 1.5 ? "text-gold" : r.profit_factor < 1 ? "text-red-400" : ""}`}>{r.profit_factor}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Détail par stratégie cliquée */}
          {selected && <StrategyDetail strategy={selected} symbol={selectedSymbol} />}

          {selected?.equity_curve && (
            <EquityCurve data={selected.equity_curve} label={`${ALL_STRATEGIES[selected.strategy] || selected.strategy} — ${selectedSymbol}`} />
          )}
        </>
      )}
    </InfoCard>
  );
}


// ============================================================
// Interprétation intelligente du backtest
// ============================================================

function BacktestInterpretation({ results, symbol }: { results: any[]; symbol: string }) {
  if (!results.length) return null;

  const sorted = [...results].sort((a, b) => (b.sharpe_ratio || 0) - (a.sharpe_ratio || 0));
  const best = sorted[0];
  const worst = sorted[sorted.length - 1];
  const profitable = results.filter((r) => (r.total_return || 0) > 0);
  const avgSharpe = results.reduce((s, r) => s + (r.sharpe_ratio || 0), 0) / results.length;
  const avgWinRate = results.reduce((s, r) => s + (r.win_rate || 0), 0) / results.length;
  const bestName = ALL_STRATEGIES[best.strategy] || best.strategy;
  const worstName = ALL_STRATEGIES[worst.strategy] || worst.strategy;

  // Verdict global
  let verdict = "";
  let verdictColor = "";
  if (avgSharpe >= 1.0 && profitable.length >= results.length * 0.7) {
    verdict = "EXCELLENT";
    verdictColor = "text-emerald-400 bg-emerald-400/10 border-emerald-400/20";
  } else if (avgSharpe >= 0.5 && profitable.length >= results.length * 0.5) {
    verdict = "BON";
    verdictColor = "text-gold bg-gold/10 border-gold/20";
  } else if (avgSharpe >= 0 && profitable.length >= results.length * 0.3) {
    verdict = "MOYEN";
    verdictColor = "text-yellow-400 bg-yellow-400/10 border-yellow-400/20";
  } else {
    verdict = "FAIBLE";
    verdictColor = "text-red-400 bg-red-400/10 border-red-400/20";
  }

  return (
    <div className="mb-5 bg-surface border border-border rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold">Analyse du backtest — {symbol}</h4>
        <span className={`text-xs px-2 py-1 rounded-lg font-bold border ${verdictColor}`}>{verdict}</span>
      </div>

      <div className="text-sm text-text-secondary leading-relaxed space-y-3">
        {/* Résumé global */}
        <p>
          Sur les <b className="text-text-primary">{results.length} stratégies</b> testées,{" "}
          <b className="text-text-primary">{profitable.length}</b> sont profitables ({Math.round(profitable.length / results.length * 100)}%).
          Le Sharpe ratio moyen est de <b className={avgSharpe >= 0.5 ? "text-gold" : "text-red-400"}>{avgSharpe.toFixed(2)}</b>{" "}
          {avgSharpe >= 1.0 ? "— excellent, le rendement ajusté au risque est très bon." :
           avgSharpe >= 0.5 ? "— correct, le rendement compense le risque pris." :
           avgSharpe >= 0 ? "— faible, le rendement ne compense pas suffisamment le risque." :
           "— négatif, les stratégies perdent de l'argent en moyenne."}
        </p>

        {/* Meilleure stratégie */}
        <div className="bg-card border border-border rounded-lg p-3">
          <p className="text-xs text-gold font-semibold mb-1">Meilleure stratégie : {bestName}</p>
          <p>
            Avec un rendement de <b className={best.total_return >= 0 ? "text-gold" : "text-red-400"}>{best.total_return >= 0 ? "+" : ""}{best.total_return}%</b>,
            un Sharpe de <b>{best.sharpe_ratio}</b>,
            et un win rate de <b>{best.win_rate}%</b> sur <b>{best.num_trades} trades</b>.
            {best.sharpe_ratio >= 1.0
              ? " C'est un excellent résultat — cette stratégie a historiquement bien fonctionné sur cet actif."
              : best.sharpe_ratio >= 0.5
                ? " Un résultat honorable — cette stratégie a un avantage mesurable mais modéré."
                : " Un résultat modeste — cette stratégie n'a pas d'avantage clair sur cet actif."}
            {best.max_drawdown && ` Le drawdown maximum a été de ${best.max_drawdown}%`}
            {best.max_drawdown && Number(best.max_drawdown) < -20
              ? " — attention, c'est un drawdown sévère qui peut être psychologiquement difficile à supporter."
              : best.max_drawdown ? " — un niveau de risque acceptable." : "."}
          </p>
        </div>

        {/* Pire stratégie */}
        {worst.strategy !== best.strategy && (
          <div className="bg-card border border-border rounded-lg p-3">
            <p className="text-xs text-red-400 font-semibold mb-1">Pire stratégie : {worstName}</p>
            <p>
              Rendement de <b className="text-red-400">{worst.total_return >= 0 ? "+" : ""}{worst.total_return}%</b>,
              Sharpe de <b>{worst.sharpe_ratio}</b>.
              {Number(worst.sharpe_ratio) < 0
                ? " Cette stratégie perd de l'argent sur cet actif — à éviter absolument."
                : ` Performance médiocre comparée à ${bestName}.`}
            </p>
          </div>
        )}

        {/* Recommandation */}
        <div className="bg-card border border-gold/20 rounded-lg p-3">
          <p className="text-xs text-gold font-semibold mb-1">Recommandation</p>
          <p>
            {avgSharpe >= 0.5 && profitable.length >= results.length * 0.5
              ? `${symbol} est un actif qui répond bien aux stratégies systématiques. La stratégie ${bestName} est la plus adaptée. En production, le pipeline utilisera automatiquement la meilleure stratégie selon le régime de marché en cours.`
              : avgSharpe >= 0
                ? `${symbol} est un actif difficile pour les stratégies systématiques. Le rendement ajusté au risque est faible. Considérez : (1) réduire la taille de position, (2) utiliser uniquement en combinaison avec d'autres actifs plus prévisibles, (3) attendre un régime de marché plus favorable.`
                : `${symbol} n'est pas adapté aux stratégies systématiques testées. Les résultats historiques sont négatifs. Il vaut mieux ne pas trader cet actif avec ces stratégies et chercher des opportunités ailleurs.`
            }
          </p>
        </div>

        {/* Mise en garde */}
        <p className="text-[10px] text-text-secondary italic">
          Les performances passées ne préjugent pas des résultats futurs. Ce backtest utilise des données historiques et ne prend pas en compte les coûts de transaction, le slippage, ni les conditions de marché futures. Utilisez ces résultats comme guide, pas comme garantie.
        </p>
      </div>
    </div>
  );
}


// ============================================================
// Détail d'une stratégie sélectionnée
// ============================================================

function StrategyDetail({ strategy: s, symbol }: { strategy: any; symbol: string }) {
  const name = ALL_STRATEGIES[s.strategy] || s.strategy;
  const sharpe = Number(s.sharpe_ratio) || 0;
  const wr = Number(s.win_rate) || 0;
  const pf = Number(s.profit_factor) || 0;
  const dd = Number(s.max_drawdown) || 0;
  const ret = Number(s.total_return) || 0;
  const trades = Number(s.num_trades) || 0;

  // Calculs dérivés
  const avgTradeReturn = trades > 0 ? ret / trades : 0;
  const riskReward = pf > 0 && pf !== 1 ? pf : 0;
  const calmar = dd !== 0 ? Math.abs(ret / dd) : 0;

  return (
    <div className="mb-4 bg-surface border border-gold/10 rounded-xl p-4 space-y-3">
      <h4 className="text-sm font-semibold text-gold">{name} — Détail</h4>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricBox label="Rendement total" value={`${ret >= 0 ? "+" : ""}${ret}%`} color={ret >= 0 ? "text-gold" : "text-red-400"} />
        <MetricBox label="Sharpe Ratio" value={sharpe.toFixed(2)} color={sharpe >= 1 ? "text-emerald-400" : sharpe >= 0.5 ? "text-gold" : sharpe >= 0 ? "text-yellow-400" : "text-red-400"}
          sub={sharpe >= 1.5 ? "Excellent" : sharpe >= 1 ? "Bon" : sharpe >= 0.5 ? "Correct" : sharpe >= 0 ? "Faible" : "Négatif"} />
        <MetricBox label="Win Rate" value={`${wr}%`} color={wr >= 55 ? "text-emerald-400" : wr >= 45 ? "text-gold" : "text-red-400"}
          sub={`${trades} trades au total`} />
        <MetricBox label="Profit Factor" value={pf.toFixed(2)} color={pf >= 1.5 ? "text-emerald-400" : pf >= 1 ? "text-gold" : "text-red-400"}
          sub={pf >= 1 ? `${pf.toFixed(1)}$ gagné par $ perdu` : "Perd de l'argent"} />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricBox label="Max Drawdown" value={`${dd}%`} color="text-red-400"
          sub={Math.abs(dd) <= 10 ? "Risque faible" : Math.abs(dd) <= 20 ? "Risque modéré" : Math.abs(dd) <= 30 ? "Risque élevé" : "Risque extrême"} />
        <MetricBox label="Calmar Ratio" value={calmar.toFixed(2)} color={calmar >= 1 ? "text-emerald-400" : calmar >= 0.5 ? "text-gold" : "text-red-400"}
          sub="Rendement / Drawdown" />
        <MetricBox label="Gain moyen/trade" value={`${avgTradeReturn >= 0 ? "+" : ""}${avgTradeReturn.toFixed(2)}%`} color={avgTradeReturn >= 0 ? "text-gold" : "text-red-400"}
          sub="Rendement par trade" />
        <MetricBox label="Risque/Récompense" value={riskReward > 0 ? `1:${riskReward.toFixed(1)}` : "—"} color={riskReward >= 1.5 ? "text-emerald-400" : "text-text-secondary"}
          sub={riskReward >= 2 ? "Excellent R:R" : riskReward >= 1.5 ? "Bon R:R" : riskReward >= 1 ? "R:R moyen" : ""} />
      </div>

      <p className="text-xs text-text-secondary leading-relaxed">
        {sharpe >= 1.0 && wr >= 50 && pf >= 1.5
          ? `${name} est la stratégie idéale pour ${symbol}. Avec un Sharpe de ${sharpe.toFixed(2)}, un win rate de ${wr}% et un profit factor de ${pf.toFixed(1)}, elle génère un rendement ajusté au risque excellent. Le drawdown de ${dd}% ${Math.abs(dd) <= 15 ? "est contenu" : "reste à surveiller"}.`
          : sharpe >= 0.5 && pf >= 1.0
            ? `${name} fonctionne sur ${symbol} avec un avantage modéré. Le Sharpe de ${sharpe.toFixed(2)} indique un rendement supérieur au risque, mais le ${wr < 50 ? `win rate de ${wr}% est faible (les trades gagnants sont plus gros que les perdants, ce qui compense)` : `win rate de ${wr}% est correct`}. ${Math.abs(dd) > 20 ? `Attention au drawdown de ${dd}% — utilisez un sizing prudent.` : ""}`
            : `${name} n'a pas d'avantage clair sur ${symbol}. ${sharpe < 0 ? `Le Sharpe négatif (${sharpe.toFixed(2)}) signifie que cette stratégie perd de l'argent.` : `Le Sharpe de ${sharpe.toFixed(2)} est trop faible pour justifier le risque.`} ${pf < 1 ? `Le profit factor de ${pf.toFixed(2)} confirme que les pertes dépassent les gains.` : ""} Cherchez une autre stratégie ou un autre actif.`
        }
      </p>
    </div>
  );
}


function MetricBox({ label, value, color = "", sub = "" }: { label: string; value: string; color?: string; sub?: string }) {
  return (
    <div className="bg-card border border-border rounded-lg p-2.5 text-center">
      <p className="text-[9px] text-text-secondary uppercase tracking-wider">{label}</p>
      <p className={`text-lg font-mono font-bold mt-0.5 ${color}`}>{value}</p>
      {sub && <p className="text-[9px] text-text-secondary mt-0.5">{sub}</p>}
    </div>
  );
}


// ============================================================
// 2. CORRÉLATION
// ============================================================

function CorrelationBacktest() {
  const [symbolA, setSymbolA] = useState("CL=F");
  const [symbolB, setSymbolB] = useState("XOM");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const PRESETS = [
    { a: "CL=F", b: "XOM", label: "Pétrole → ExxonMobil" },
    { a: "BTC-USD", b: "ETH-USD", label: "Bitcoin → Ethereum" },
    { a: "GC=F", b: "SPY", label: "Or → S&P 500" },
    { a: "NVDA", b: "AMD", label: "NVIDIA → AMD" },
    { a: "EURUSD=X", b: "GC=F", label: "EUR/USD → Or" },
    { a: "CL=F", b: "XLU", label: "Pétrole → Utilities (hedge)" },
  ];

  const runBacktest = (a?: string, b?: string) => {
    setLoading(true);
    api.get(`/scanner/correlation-backtest?a=${encodeURIComponent(a || symbolA)}&b=${encodeURIComponent(b || symbolB)}`)
      .then((res) => setResult(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  return (
    <InfoCard title="Backtest Corrélation" icon={<GitBranch size={18} />} description="Vérifie si la corrélation entre deux actifs est stable dans le temps. Teste sur les 9 périodes historiques (crises, bull markets) et valide le beta.">
      <div className="flex flex-wrap gap-2 mb-4">
        {PRESETS.map((p) => (
          <button key={p.label} onClick={() => { setSymbolA(p.a); setSymbolB(p.b); runBacktest(p.a, p.b); }}
            className="px-3 py-1 text-xs bg-surface border border-border rounded-lg hover:border-gold/20 hover:text-gold transition-colors"
          >{p.label}</button>
        ))}
      </div>
      <div className="flex items-center gap-3 mb-4">
        <input type="text" value={symbolA} onChange={(e) => setSymbolA(e.target.value)} placeholder="Actif A (ex: petrole)" className="bg-surface border border-border rounded-lg px-3 py-2 text-sm font-mono w-40" />
        <span className="text-text-secondary">↔</span>
        <input type="text" value={symbolB} onChange={(e) => setSymbolB(e.target.value)} placeholder="Actif B (ex: XOM)" className="bg-surface border border-border rounded-lg px-3 py-2 text-sm font-mono w-40" />
        <button onClick={() => runBacktest()} disabled={loading} className="px-4 py-2 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm hover:bg-gold/20 disabled:opacity-50">
          {loading ? "Analyse..." : "Backtester"}
        </button>
      </div>

      {result && !result.error && (
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className={`text-3xl font-mono font-bold ${result.global_reliability_score >= 70 ? "text-gold" : result.global_reliability_score >= 50 ? "text-yellow-400" : "text-red-400"}`}>
              {result.global_reliability_score}/100
            </div>
            <div>
              <p className="text-sm font-semibold">Fiabilité globale</p>
              <p className="text-xs text-text-secondary">{result.verdict}</p>
            </div>
          </div>

          {result.rolling_correlation?.statistics && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatBox label="Corrélation moyenne" value={result.rolling_correlation.statistics.mean} />
              <StatBox label="Minimum" value={result.rolling_correlation.statistics.min} />
              <StatBox label="Maximum" value={result.rolling_correlation.statistics.max} />
              <StatBox label="Actuelle" value={result.rolling_correlation.statistics.current} />
            </div>
          )}

          {result.by_period?.periods && (
            <div>
              <h4 className="text-xs text-text-secondary font-semibold mb-2 uppercase tracking-wider">Par période historique (stabilité {result.by_period.stability_score}/100)</h4>
              <div className="space-y-1">
                {Object.entries(result.by_period.periods).map(([name, data]: [string, any]) => (
                  <div key={name} className="flex items-center justify-between bg-surface rounded-lg p-2 text-xs">
                    <span className="w-36">{name}</span>
                    <span className={`font-mono w-14 text-right ${data.correlation > 0.5 ? "text-gold" : data.correlation < 0 ? "text-red-400" : ""}`}>{data.correlation > 0 ? "+" : ""}{data.correlation}</span>
                    <span className={`w-14 text-right ${data.moved_together ? "text-gold" : "text-red-400"}`}>{data.moved_together ? "Oui" : "Non"}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.beta_backtest && !result.beta_backtest.error && (
            <div className="p-3 bg-surface rounded-xl text-xs">
              <p className="font-semibold mb-1">Beta Backtest</p>
              <p className="text-text-secondary">{result.beta_backtest.interpretation}</p>
            </div>
          )}
        </div>
      )}
      {result?.error && <p className="text-red-400 text-sm">{result.error}</p>}
    </InfoCard>
  );
}


// ============================================================
// 3. WALK-FORWARD
// ============================================================

function WalkForwardBacktest() {
  const [symbol, setSymbol] = useState("AAPL");
  const [strategy, setStrategy] = useState("momentum");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const run = () => {
    setLoading(true);
    api.get(`/backtest/walk-forward/${symbol}?strategy=${strategy}`)
      .then((res) => setResult(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  return (
    <InfoCard title="Walk-Forward Testing" icon={<BarChart3 size={18} />} description="Le test le plus sévère : découpe l'historique en fenêtres glissantes et teste chaque sous-période séparément. Une stratégie qui ne passe pas le walk-forward n'est pas fiable.">
      <div className="flex items-center gap-3 mb-4">
        <input type="text" value={symbol} onChange={(e) => setSymbol(e.target.value)} className="bg-surface border border-border rounded-lg px-3 py-2 text-sm font-mono w-32" />
        <select value={strategy} onChange={(e) => setStrategy(e.target.value)} className="bg-surface border border-border rounded-lg px-3 py-2 text-sm">
          {Object.entries(ALL_STRATEGIES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <button onClick={run} disabled={loading} className="px-4 py-2 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm hover:bg-gold/20 disabled:opacity-50">
          {loading ? "Calcul (~2min)..." : "Lancer Walk-Forward"}
        </button>
      </div>

      {result && !result.error && (
        <div className="space-y-4">
          {/* Interprétation Walk-Forward */}
          <WalkForwardInterpretation result={result} symbol={symbol} strategy={strategy} />

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <StatBox label="Consistance" value={`${result.summary?.consistency}%`} highlight={result.summary?.consistency > 60} />
            <StatBox label="Rendement moyen" value={`${result.summary?.avg_return}%`} />
            <StatBox label="Sharpe moyen" value={result.summary?.avg_sharpe} />
            <StatBox label="Win Rate moyen" value={`${result.summary?.avg_win_rate}%`} />
            <StatBox label="Folds testés" value={result.n_folds} />
          </div>

          {result.folds?.length > 0 && (
            <div>
              <h4 className="text-xs text-text-secondary font-semibold mb-2 uppercase tracking-wider">Résultats par fenêtre</h4>
              <div className="space-y-1">
                {result.folds.map((f: any) => {
                  const ret = Number(f.total_return) || 0;
                  const sh = Number(f.sharpe_ratio) || 0;
                  return (
                    <div key={f.fold} className={`flex items-center justify-between rounded-lg p-2 text-xs border ${ret >= 0 ? "bg-emerald-400/5 border-emerald-400/10" : "bg-red-400/5 border-red-400/10"}`}>
                      <span className="text-text-secondary font-semibold">Fold {f.fold}</span>
                      <span className="text-text-secondary w-40 truncate">{f.test_period}</span>
                      <span className={`font-mono w-16 text-right font-bold ${ret >= 0 ? "text-emerald-400" : "text-red-400"}`}>{ret >= 0 ? "+" : ""}{f.total_return}%</span>
                      <span className={`font-mono w-14 text-right ${sh >= 0.5 ? "text-gold" : ""}`}>{f.sharpe_ratio}</span>
                      <span className="font-mono w-14 text-right">{f.win_rate}%</span>
                      <span className="font-mono w-14 text-right text-text-secondary">{f.num_trades}t</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
      {result?.error && <p className="text-red-400 text-sm">{result.error}</p>}
    </InfoCard>
  );
}


// ============================================================
// 4. THÈSE
// ============================================================

function ThesisBacktest() {
  const [theme, setTheme] = useState("PETROLE");
  const [movePct, setMovePct] = useState(20);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const THEMES = [
    { value: "CL=F", label: "Pétrole" }, { value: "GC=F", label: "Or" },
    { value: "BTC-USD", label: "Bitcoin" }, { value: "NVDA", label: "NVIDIA" },
    { value: "SPY", label: "S&P 500" }, { value: "TLT", label: "Obligations" },
  ];

  const run = () => {
    setLoading(true);
    api.get(`/scanner/impact-simulation?q=${encodeURIComponent(theme)}&move_pct=${movePct}`)
      .then((res) => setResult(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  return (
    <InfoCard title="Backtest de Thèse" icon={<Lightbulb size={18} />} description="Simulez l'impact d'un scénario : 'Si le pétrole fait +20%, quels actifs profitent et lesquels souffrent ?' Basé sur les corrélations historiques et le beta.">
      <div className="flex items-center gap-3 mb-4">
        <select value={theme} onChange={(e) => setTheme(e.target.value)} className="bg-surface border border-border rounded-lg px-3 py-2 text-sm">
          {THEMES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
        <span className="text-text-secondary text-sm">fait</span>
        <input type="number" value={movePct} onChange={(e) => setMovePct(Number(e.target.value))} className="bg-surface border border-border rounded-lg px-3 py-2 text-sm font-mono w-20 text-center" />
        <span className="text-text-secondary text-sm">%</span>
        <button onClick={run} disabled={loading} className="px-4 py-2 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm hover:bg-gold/20 disabled:opacity-50">
          {loading ? "Simulation..." : "Simuler"}
        </button>
      </div>

      {result && !result.error && (
        <div className="space-y-4">
          <p className="text-sm font-semibold text-gold">{result.scenario}</p>
          <div className="grid grid-cols-2 gap-3">
            <StatBox label="Bénéficient" value={result.summary?.actifs_qui_montent} highlight />
            <StatBox label="Souffrent" value={result.summary?.actifs_qui_baissent} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {result.beneficiaires?.length > 0 && (
              <div>
                <h4 className="text-xs text-gold font-semibold mb-2">BÉNÉFICIENT</h4>
                <div className="space-y-1">
                  {result.beneficiaires.slice(0, 10).map((i: any) => (
                    <div key={i.symbol} className="flex justify-between bg-surface rounded-lg p-2 text-xs">
                      <span className="font-mono font-semibold">{i.symbol}</span>
                      <span className="font-mono text-gold">+{i.expected_move_pct}% → ${i.expected_price}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {result.victimes?.length > 0 && (
              <div>
                <h4 className="text-xs text-red-400 font-semibold mb-2">SOUFFRENT</h4>
                <div className="space-y-1">
                  {result.victimes.slice(0, 10).map((i: any) => (
                    <div key={i.symbol} className="flex justify-between bg-surface rounded-lg p-2 text-xs">
                      <span className="font-mono font-semibold">{i.symbol}</span>
                      <span className="font-mono text-red-400">{i.expected_move_pct}% → ${i.expected_price}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </InfoCard>
  );
}


// ============================================================
// 5. ANALYSE PROFONDE
// ============================================================

function DeepAnalysis() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Charger le fichier d'analyse profonde s'il existe
    api.get("/performance/report-v2")
      .then((res) => setResult(res.data))
      .catch(() => {});
  }, []);

  return (
    <InfoCard title="Analyse profonde" icon={<FlaskConical size={18} />} description="Résultats du backtest sur 10 ans (218 actifs × 9 stratégies). Inclut la saisonnalité, les cycles économiques et le walk-forward global. Calculé en arrière-plan (~5h).">
      {result ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatBox label="Equity" value={`$${result.equity?.current?.toFixed(0)}`} />
            <StatBox label="Trades ouverts" value={result.trading_stats?.open_trades} />
            <StatBox label="Trades fermés" value={result.trading_stats?.closed_trades} />
            <StatBox label="Win Rate" value={`${result.trading_stats?.win_rate}%`} />
          </div>

          {result.benchmarks && (
            <div>
              <h4 className="text-xs text-text-secondary font-semibold mb-2 uppercase tracking-wider">vs Benchmarks</h4>
              <div className="grid grid-cols-3 gap-3">
                <StatBox label="Notre return" value={`${result.benchmarks.our_return}%`} />
                <StatBox label="SPY Buy&Hold 1m" value={`${result.benchmarks.benchmarks?.spy_buy_hold_1m}%`} />
                <StatBox label="60/40 1m" value={`${result.benchmarks.benchmarks?.balanced_60_40_1m}%`} />
              </div>
            </div>
          )}

          {result.by_asset_class && Object.keys(result.by_asset_class).length > 0 && (
            <div>
              <h4 className="text-xs text-text-secondary font-semibold mb-2 uppercase tracking-wider">Par classe d'actif</h4>
              <div className="space-y-1">
                {Object.entries(result.by_asset_class).map(([ac, data]: [string, any]) => (
                  <div key={ac} className="flex items-center justify-between bg-surface rounded-lg p-2 text-xs">
                    <span className="font-semibold">{ac}</span>
                    <div className="flex gap-4">
                      <span>{data.positions} positions</span>
                      <span className={`font-mono ${data.pnl >= 0 ? "text-gold" : "text-red-400"}`}>${data.pnl}</span>
                      <span className="text-text-secondary">${data.value}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="p-3 bg-surface rounded-xl text-xs text-text-secondary">
            <p>Pour lancer une analyse profonde complète (backtest 10 ans + saisonnalité + cycles) :</p>
            <code className="text-gold block mt-1">python scripts/run_deep_analysis.py</code>
            <p className="mt-1">Durée : ~5 heures. Résultats dans data/deep_analysis.json</p>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-text-secondary">
          <p>Chargement des données de performance...</p>
        </div>
      )}
    </InfoCard>
  );
}


// ============================================================
// COMPOSANT UTILITAIRE
// ============================================================

function StatBox({ label, value, highlight }: { label: string; value: any; highlight?: boolean }) {
  return (
    <div className="bg-surface rounded-xl p-3 text-center">
      <p className={`text-xl font-mono font-bold ${highlight ? "text-gold" : ""}`}>{value}</p>
      <p className="text-[10px] text-text-secondary mt-0.5">{label}</p>
    </div>
  );
}


// ============================================================
// Walk-Forward Interpretation
// ============================================================

function WalkForwardInterpretation({ result, symbol, strategy }: { result: any; symbol: string; strategy: string }) {
  const consistency = Number(result.summary?.consistency) || 0;
  const avgSharpe = Number(result.summary?.avg_sharpe) || 0;
  const avgReturn = Number(result.summary?.avg_return) || 0;
  const avgWR = Number(result.summary?.avg_win_rate) || 0;
  const folds = result.folds || [];
  const nFolds = folds.length;
  const stratName = ALL_STRATEGIES[strategy] || strategy;

  const profitableFolds = folds.filter((f: any) => Number(f.total_return) > 0).length;
  const bestFold = folds.length > 0 ? folds.reduce((best: any, f: any) => Number(f.sharpe_ratio) > Number(best.sharpe_ratio) ? f : best, folds[0]) : null;
  const worstFold = folds.length > 0 ? folds.reduce((worst: any, f: any) => Number(f.sharpe_ratio) < Number(worst.sharpe_ratio) ? f : worst, folds[0]) : null;

  let verdict = "";
  let verdictColor = "";
  if (consistency >= 70 && avgSharpe >= 0.5) {
    verdict = "ROBUSTE";
    verdictColor = "text-emerald-400 bg-emerald-400/10 border-emerald-400/20";
  } else if (consistency >= 50 && avgSharpe >= 0) {
    verdict = "ACCEPTABLE";
    verdictColor = "text-gold bg-gold/10 border-gold/20";
  } else if (consistency >= 30) {
    verdict = "FRAGILE";
    verdictColor = "text-yellow-400 bg-yellow-400/10 border-yellow-400/20";
  } else {
    verdict = "NON FIABLE";
    verdictColor = "text-red-400 bg-red-400/10 border-red-400/20";
  }

  const parts: string[] = [];

  parts.push(`La stratégie ${stratName} a été testée sur ${nFolds} sous-périodes indépendantes de ${symbol}.`);
  parts.push(`${profitableFolds} sur ${nFolds} fenêtres sont profitables (consistance de ${consistency}%).`);

  if (consistency >= 70) {
    parts.push(`C'est un excellent résultat — la stratégie fonctionne dans la majorité des conditions de marché, pas seulement sur une période favorable.`);
  } else if (consistency >= 50) {
    parts.push(`La stratégie fonctionne dans la moitié des conditions, ce qui est acceptable mais pas exceptionnel. Elle dépend du régime de marché.`);
  } else if (consistency >= 30) {
    parts.push(`La stratégie ne fonctionne que dans certaines conditions spécifiques. Le risque d'overfitting est élevé — les bons résultats sur la période complète pourraient ne pas se reproduire.`);
  } else {
    parts.push(`La stratégie échoue dans la majorité des sous-périodes. Les résultats du backtest complet sont probablement du sur-ajustement (overfitting) et ne se reproduiront pas en live.`);
  }

  if (avgSharpe >= 0.5) {
    parts.push(`Le Sharpe moyen de ${avgSharpe.toFixed(2)} sur les fenêtres out-of-sample confirme un avantage réel.`);
  } else if (avgSharpe >= 0) {
    parts.push(`Le Sharpe moyen de ${avgSharpe.toFixed(2)} est faible — l'avantage existe mais il est mince.`);
  } else {
    parts.push(`Le Sharpe moyen négatif (${avgSharpe.toFixed(2)}) signifie que la stratégie perd de l'argent en moyenne sur les périodes de test.`);
  }

  if (bestFold && worstFold) {
    parts.push(`Meilleure fenêtre : Fold ${bestFold.fold} (${bestFold.test_period}) avec un Sharpe de ${bestFold.sharpe_ratio}. Pire : Fold ${worstFold.fold} avec ${worstFold.sharpe_ratio}.`);
  }

  return (
    <div className={`p-4 rounded-xl border ${verdictColor} mb-4`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold">Diagnostic Walk-Forward</span>
        <span className={`text-xs px-2 py-1 rounded-lg font-bold border ${verdictColor}`}>{verdict}</span>
      </div>
      <p className="text-sm text-text-secondary leading-relaxed">{parts.join(" ")}</p>
      {consistency < 50 && (
        <p className="text-xs text-yellow-400 mt-2 italic">
          Recommandation : testez d'autres stratégies sur cet actif, ou réduisez le sizing si vous utilisez celle-ci en production.
        </p>
      )}
    </div>
  );
}
