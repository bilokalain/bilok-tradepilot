import { useEffect, useState } from "react";
import axios from "axios";
import EquityCurve from "../components/EquityCurve";
import { scannerApi } from "../services/api";

const STRATEGIES = ["trend_following", "mean_reversion", "breakout", "momentum"];
const STRATEGY_LABELS: Record<string, string> = {
  trend_following: "Trend Following",
  mean_reversion: "Mean Reversion",
  breakout: "Breakout",
  momentum: "Momentum Adaptatif",
};

interface BacktestResult {
  strategy: string;
  symbol: string;
  total_return: number;
  num_trades: number;
  winning_trades: number;
  win_rate: number;
  profit_factor: number;
  max_drawdown: number;
  sharpe_ratio: number;
  calmar_ratio: number;
  equity_curve: number[];
  trades: Array<{
    entry_date: string;
    exit_date: string;
    direction: string;
    entry_price: number;
    exit_price: number;
    pnl: number;
    pnl_pct: number;
    exit_reason: string;
  }>;
}

export default function Backtest() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState("AAPL");
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<BacktestResult | null>(null);

  useEffect(() => {
    scannerApi.getAssets().then((res) => {
      setSymbols(res.data.map((a) => a.symbol));
    });
  }, []);

  const runBacktest = () => {
    setLoading(true);
    axios
      .get(`/api/backtest/compare/${selectedSymbol}`)
      .then((res) => {
        setResults(res.data.strategies);
        if (res.data.strategies.length > 0) {
          setSelected(res.data.strategies[0]);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Backtesting</h2>
      <p className="text-text-secondary mb-6 text-sm">
        Test des stratégies sur données historiques — Walk-forward validation
      </p>

      {/* Sélecteur */}
      <div className="flex items-center gap-4 mb-6">
        <select
          value={selectedSymbol}
          onChange={(e) => setSelectedSymbol(e.target.value)}
          className="bg-card border border-border rounded-lg px-3 py-2 text-sm font-mono"
        >
          {symbols.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button
          onClick={runBacktest}
          disabled={loading}
          className="px-4 py-2 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm hover:bg-gold/20 transition-colors disabled:opacity-50"
        >
          {loading ? "Calcul en cours..." : "Lancer le backtest"}
        </button>
      </div>

      {results.length > 0 && (
        <>
          {/* Comparaison */}
          <div className="bg-card border border-border rounded-xl p-6 mb-6">
            <h3 className="text-sm font-medium text-text-secondary mb-4">
              Comparaison des stratégies — {selectedSymbol}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-text-secondary border-b border-border">
                    <th className="pb-3 pr-4">Stratégie</th>
                    <th className="pb-3 pr-4 text-right">Rendement</th>
                    <th className="pb-3 pr-4 text-right">Sharpe</th>
                    <th className="pb-3 pr-4 text-right">Win Rate</th>
                    <th className="pb-3 pr-4 text-right">Max DD</th>
                    <th className="pb-3 pr-4 text-right">Trades</th>
                    <th className="pb-3 text-right">Profit Factor</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r) => (
                    <tr
                      key={r.strategy}
                      onClick={() => setSelected(r)}
                      className={`border-b border-border/50 cursor-pointer transition-colors ${
                        selected?.strategy === r.strategy ? "bg-gold/5" : "hover:bg-surface"
                      }`}
                    >
                      <td className="py-3 pr-4 font-semibold">
                        {STRATEGY_LABELS[r.strategy] || r.strategy}
                      </td>
                      <td className={`py-3 pr-4 text-right font-mono ${r.total_return >= 0 ? "text-gold" : "text-red-400"}`}>
                        {r.total_return >= 0 ? "+" : ""}{r.total_return.toFixed(2)}%
                      </td>
                      <td className={`py-3 pr-4 text-right font-mono ${r.sharpe_ratio >= 1 ? "text-gold" : r.sharpe_ratio < 0 ? "text-red-400" : ""}`}>
                        {r.sharpe_ratio.toFixed(3)}
                      </td>
                      <td className="py-3 pr-4 text-right font-mono">{r.win_rate.toFixed(1)}%</td>
                      <td className="py-3 pr-4 text-right font-mono text-red-400">{r.max_drawdown.toFixed(2)}%</td>
                      <td className="py-3 pr-4 text-right font-mono">{r.num_trades}</td>
                      <td className={`py-3 text-right font-mono ${r.profit_factor >= 1.5 ? "text-gold" : r.profit_factor < 1 ? "text-red-400" : ""}`}>
                        {r.profit_factor.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Détail stratégie sélectionnée */}
          {selected && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Equity Curve */}
              <div className="bg-card border border-border rounded-xl p-6">
                <h3 className="text-sm font-medium text-text-secondary mb-2">
                  Equity Curve — {STRATEGY_LABELS[selected.strategy]}
                </h3>
                <EquityCurve data={selected.equity_curve} label="Backtest" />
              </div>

              {/* Derniers trades */}
              <div className="bg-card border border-border rounded-xl p-6">
                <h3 className="text-sm font-medium text-text-secondary mb-4">
                  Derniers trades ({selected.trades.length})
                </h3>
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {selected.trades.map((t, i) => (
                    <div key={i} className="flex items-center justify-between bg-surface rounded-lg p-2 text-xs">
                      <div className="flex items-center gap-2">
                        <span className={`px-1.5 py-0.5 rounded font-semibold ${
                          t.direction === "LONG" ? "text-gold bg-gold/10" : "text-red-400 bg-red-400/10"
                        }`}>{t.direction}</span>
                        <span className="text-text-secondary">{t.entry_date}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-text-secondary">{t.exit_reason}</span>
                        <span className={`font-mono font-semibold ${t.pnl >= 0 ? "text-gold" : "text-red-400"}`}>
                          ${t.pnl.toFixed(0)} ({t.pnl_pct.toFixed(1)}%)
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
