import { useEffect, useState } from "react";
import { FlaskConical, TrendingUp, GitBranch, Lightbulb, BarChart3 } from "lucide-react";
import axios from "axios";
import EquityCurve from "../components/EquityCurve";
import InfoCard from "../components/ui/InfoCard";
import { scannerApi } from "../services/api";

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
      <p className="text-text-secondary text-sm mb-6">
        5 modules de backtest pour valider chaque dimension du modèle sur l'historique
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
    axios.get(`/api/backtest/compare/${selectedSymbol}`)
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
          {selected?.equity_curve && (
            <EquityCurve data={selected.equity_curve} label={`${ALL_STRATEGIES[selected.strategy] || selected.strategy} — ${selectedSymbol}`} />
          )}
        </>
      )}
    </InfoCard>
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
    axios.get(`/api/scanner/correlation-backtest?a=${encodeURIComponent(a || symbolA)}&b=${encodeURIComponent(b || symbolB)}`)
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
    axios.get(`/api/backtest/walk-forward/${symbol}?strategy=${strategy}`)
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
                {result.folds.map((f: any) => (
                  <div key={f.fold} className="flex items-center justify-between bg-surface rounded-lg p-2 text-xs">
                    <span className="text-text-secondary">Fold {f.fold}</span>
                    <span className="text-text-secondary w-40 truncate">{f.test_period}</span>
                    <span className={`font-mono w-16 text-right ${f.total_return >= 0 ? "text-gold" : "text-red-400"}`}>{f.total_return >= 0 ? "+" : ""}{f.total_return}%</span>
                    <span className="font-mono w-14 text-right">{f.sharpe_ratio}</span>
                    <span className="font-mono w-14 text-right">{f.win_rate}%</span>
                  </div>
                ))}
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
    axios.get(`/api/scanner/impact-simulation?q=${encodeURIComponent(theme)}&move_pct=${movePct}`)
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
    axios.get("/api/performance/report-v2")
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
