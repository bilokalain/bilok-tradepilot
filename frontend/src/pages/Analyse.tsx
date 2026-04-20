import { useState, useEffect, useRef } from "react";
import { Search, TrendingUp, TrendingDown, Minus, Share2, MessageCircle, Mail, Copy, Check } from "lucide-react";
import api from "../services/api";
import TradingChart from "../components/TradingChart";
import ScoreGauge from "../components/ui/ScoreGauge";
import InfoCard from "../components/ui/InfoCard";
import SignalBadge from "../components/ui/SignalBadge";
import RadarChart from "../components/ui/RadarChart";

const SUGGESTIONS = [
  "AAPL", "TSLA", "NVDA", "PLTR", "COIN", "AMC", "GME",
  "S&P 500", "CAC 40", "DAX", "NASDAQ", "DOW JONES", "NIKKEI",
  "BITCOIN", "ETHEREUM", "GOLD", "OIL", "SILVER",
  "EUR/USD", "LVMH", "ASML",
];

const STRATEGY_LABELS: Record<string, string> = {
  trend_following: "Trend Following",
  mean_reversion: "Mean Reversion",
  mean_reversion_v2: "Mean Reversion V2",
  breakout: "Breakout",
  momentum: "Momentum",
  fibonacci: "Fibonacci",
  ichimoku: "Ichimoku",
  adaptive_trend: "Adaptive Trend",
  multi_signal: "Multi-Signal",
  keltner_breakout: "Keltner Breakout",
  vwap_reversion: "VWAP Reversion",
  momentum_rotation: "Momentum Rotation",
  regime_cascade: "Regime Cascade",
  volatility_explosion: "Volatility Explosion",
  anti_consensus: "Anti-Consensus Alpha",
};

interface HistoryItem {
  symbol: string;
  name: string;
  score: number;
  action: string;
  direction: string;
  price: number;
  timestamp: string;
}

function loadHistory(): HistoryItem[] {
  try {
    return JSON.parse(localStorage.getItem("analyse_history") || "[]");
  } catch { return []; }
}

function saveToHistory(item: HistoryItem) {
  const history = loadHistory().filter((h) => h.symbol !== item.symbol);
  history.unshift(item);
  localStorage.setItem("analyse_history", JSON.stringify(history.slice(0, 20)));
}

interface SearchSuggestion {
  symbol: string;
  name: string;
  asset_class: string;
  source: string;
  relevance: number;
}

const CLASS_LABELS: Record<string, string> = {
  ACTION_US: "Action US",
  ACTION_EU: "Action EU",
  CRYPTO: "Crypto",
  FOREX: "Forex",
  COMMODITY: "Matière 1ère",
  ETF: "ETF",
  INDEX: "Indice",
};

export default function Analyse() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<HistoryItem[]>(loadHistory());
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState(-1);
  const searchRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Fermer suggestions au clic extérieur
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Recherche autocomplete avec debounce
  const searchSuggestions = (q: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (q.trim().length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    debounceRef.current = setTimeout(() => {
      api
        .get(`/scanner/search?q=${encodeURIComponent(q)}`)
        .then((res) => {
          if (Array.isArray(res.data) && res.data.length > 0) {
            setSuggestions(res.data);
            setShowSuggestions(true);
            setSelectedIdx(-1);
          } else {
            setSuggestions([]);
            setShowSuggestions(false);
          }
        })
        .catch(() => {});
    }, 300);
  };

  const handleInputChange = (val: string) => {
    setQuery(val);
    searchSuggestions(val);
  };

  const selectSuggestion = (s: SearchSuggestion) => {
    setQuery(s.symbol);
    setShowSuggestions(false);
    handleSearch(s.symbol);
  };

  const handleSearch = (q?: string) => {
    const searchQuery = q || query;
    if (!searchQuery.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);

    api
      .get(`/scanner/analyse?q=${encodeURIComponent(searchQuery)}`)
      .then((res) => {
        if (res.data.error) {
          setError(res.data.error);
        } else {
          setResult(res.data);
          const item: HistoryItem = {
            symbol: res.data.symbol,
            name: res.data.info?.name || res.data.symbol,
            score: res.data.global_score,
            action: res.data.action,
            direction: res.data.best_strategy?.direction || "NEUTRAL",
            price: res.data.last_price,
            timestamp: new Date().toLocaleString("fr-FR"),
          };
          saveToHistory(item);
          setHistory(loadHistory());
        }
      })
      .catch((err) => setError(err.response?.data?.detail || "Erreur de connexion"))
      .finally(() => setLoading(false));
  };

  return (
    <div className="max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold mb-2">Analyse rapide</h2>
      <p className="text-text-secondary text-sm mb-6 max-w-3xl">
        Analyse instantanée de n'importe quel actif — actions, crypto, indices, forex. Le moteur évalue les indicateurs techniques, détecte le régime de marché, sélectionne la stratégie optimale et génère une recommandation actionable avec niveaux d'entrée, stop-loss et take-profit.
      </p>

      {/* Barre de recherche avec autocomplete */}
      <div className="flex gap-3 mb-4" ref={searchRef}>
        <div className="flex-1 relative">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-secondary z-10" />
          <input
            type="text"
            value={query}
            onChange={(e) => handleInputChange(e.target.value)}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                if (selectedIdx >= 0 && selectedIdx < suggestions.length) {
                  selectSuggestion(suggestions[selectedIdx]);
                } else {
                  setShowSuggestions(false);
                  handleSearch();
                }
              } else if (e.key === "ArrowDown") {
                e.preventDefault();
                setSelectedIdx((i) => Math.min(i + 1, suggestions.length - 1));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setSelectedIdx((i) => Math.max(i - 1, -1));
              } else if (e.key === "Escape") {
                setShowSuggestions(false);
              }
            }}
            placeholder="Tapez un nom ou symbole : BNP, Apple, Bitcoin, CAC 40..."
            className="w-full bg-card border border-border rounded-xl pl-10 pr-4 py-3 text-sm font-mono focus:outline-none focus:border-gold/50 transition-colors"
          />

          {/* Dropdown suggestions */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-card border border-border rounded-xl shadow-xl z-50 overflow-hidden max-h-[320px] overflow-y-auto">
              {suggestions.map((s, i) => (
                <button
                  key={s.symbol}
                  onClick={() => selectSuggestion(s)}
                  className={`w-full flex items-center justify-between px-4 py-2.5 text-left transition-colors ${
                    i === selectedIdx ? "bg-gold/10" : "hover:bg-surface"
                  } ${i > 0 ? "border-t border-border/30" : ""}`}
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-semibold text-gold text-sm">{s.symbol}</span>
                    <span className="text-xs text-text-secondary truncate max-w-[200px]">{s.name}</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 bg-surface rounded text-text-secondary whitespace-nowrap">
                    {CLASS_LABELS[s.asset_class] || s.asset_class}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
        <button
          onClick={() => { setShowSuggestions(false); handleSearch(); }}
          disabled={loading || !query.trim()}
          className="px-6 py-3 bg-gold/10 text-gold border border-gold/20 rounded-xl text-sm font-semibold hover:bg-gold/20 transition-colors disabled:opacity-50"
        >
          {loading ? "Analyse..." : "Analyser"}
        </button>
      </div>

      {/* Suggestions */}
      <div className="flex flex-wrap gap-2 mb-6">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => { setQuery(s); handleSearch(s); }}
            className="px-3 py-1 text-xs bg-surface border border-border rounded-lg text-text-secondary hover:text-gold hover:border-gold/20 transition-colors"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Historique */}
      {history.length > 0 && !result && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs text-text-secondary font-semibold uppercase tracking-wider">Historique des analyses</p>
            <button
              onClick={() => { localStorage.removeItem("analyse_history"); setHistory([]); }}
              className="text-[10px] text-text-secondary hover:text-red-400 transition-colors"
            >
              Effacer
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {history.map((h) => (
              <button
                key={h.symbol + h.timestamp}
                onClick={() => { setQuery(h.symbol); handleSearch(h.symbol); }}
                className="flex items-center justify-between bg-card border border-border rounded-xl p-3 hover:border-gold/20 transition-colors text-left"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-semibold text-gold text-sm">{h.symbol}</span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded border font-semibold ${
                      h.action === "GO" ? "text-gold bg-gold/10 border-gold/20" :
                      h.action === "WAIT" ? "text-yellow-400 bg-yellow-400/10 border-yellow-400/20" :
                      "text-text-secondary bg-surface border-border"
                    }`}>{h.action}</span>
                    {h.direction !== "NEUTRAL" && (
                      <span className={`text-[9px] px-1.5 py-0.5 rounded border font-semibold ${
                        h.direction === "LONG" ? "text-gold bg-gold/10 border-gold/20" : "text-red-400 bg-red-400/10 border-red-400/20"
                      }`}>{h.direction}</span>
                    )}
                  </div>
                  <p className="text-[10px] text-text-secondary mt-0.5 truncate max-w-[180px]">{h.name}</p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-sm">{h.score.toFixed(1)}</p>
                  <p className="text-[9px] text-text-secondary">${h.price.toFixed(2)}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-400/10 border border-red-400/20 rounded-xl text-sm text-red-400 mb-6">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-12 h-12 rounded-full border-2 border-transparent border-t-gold animate-spin mx-auto mb-4" />
            <p className="text-text-secondary text-sm">Téléchargement des données et analyse en cours...</p>
          </div>
        </div>
      )}

      {result && <AnalyseResult data={result} />}
    </div>
  );
}

function AnalyseResult({ data }: { data: any }) {
  const perf = data.performance || {};
  const ind = data.indicators || {};
  const best = data.best_strategy || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h3 className="text-3xl font-bold font-mono text-gold">{data.symbol}</h3>
            {data.regime?.regime && data.regime.regime !== "UNKNOWN" && (
              <span className={`text-xs px-2.5 py-1 border rounded-lg font-semibold ${
                data.regime.regime === "BULL" ? "text-gold bg-gold/10 border-gold/20" :
                data.regime.regime === "BEAR" ? "text-red-400 bg-red-400/10 border-red-400/20" :
                "text-yellow-400 bg-yellow-400/10 border-yellow-400/20"
              }`}>
                {data.regime.regime}
              </span>
            )}
          </div>
          <p className="text-text-secondary">{data.info?.name}</p>
          {data.info?.sector && <p className="text-xs text-text-secondary">{data.info.sector} — {data.info.industry}</p>}
        </div>
        <div className="text-right">
          <p className="text-4xl font-mono font-bold">${data.last_price}</p>
          <div className="flex items-center justify-end gap-2 mt-1">
            <span className={`w-2 h-2 rounded-full ${data.price_source === "alpaca_live" ? "bg-gold animate-pulse" : "bg-text-secondary"}`} />
            <span className="text-xs text-text-secondary">
              {data.price_source === "alpaca_live" ? "Prix live Alpaca" : "Dernière clôture Yahoo"}
            </span>
          </div>
          <p className="text-[10px] text-text-secondary">{data.data_points} jours de données</p>
        </div>
      </div>

      {/* Verdict + Score */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border border-border rounded-xl p-5 flex items-center gap-5">
          <ScoreGauge score={data.global_score} size={100} sublabel="/100" />
          <div>
            <SignalBadge action={data.action} direction={best.direction} size="lg" showExplanation />
          </div>
        </div>

        {best.name && (
          <div className="bg-card border border-border rounded-xl p-5">
            <p className="text-xs text-text-secondary mb-2">Stratégie recommandée</p>
            <p className="font-semibold text-lg">{STRATEGY_LABELS[best.name] || best.name}</p>
            <p className="text-sm text-text-secondary mt-1">Conviction : {best.conviction}/100</p>
            {best.stop_loss > 0 && (
              <div className="mt-3 grid grid-cols-4 gap-2 text-xs">
                <div><span className="text-text-secondary">Entrée</span><p className="font-mono">${best.entry}</p></div>
                <div><span className="text-text-secondary">SL</span><p className="font-mono text-red-400">${best.stop_loss}</p></div>
                <div><span className="text-text-secondary">TP1</span><p className="font-mono text-gold">${best.take_profit_1 || best.take_profit}</p></div>
                <div><span className="text-text-secondary">TP2</span><p className="font-mono text-emerald-400">${best.take_profit_2 || "—"}</p></div>
              </div>
            )}
          </div>
        )}

        <div className="bg-card border border-border rounded-xl p-5">
          <p className="text-xs text-text-secondary mb-2">Performance</p>
          <div className="space-y-2">
            <PerfRow label="1 mois" value={perf["1_month"]} />
            <PerfRow label="3 mois" value={perf["3_months"]} />
            <PerfRow label="1 an" value={perf["1_year"]} />
          </div>
        </div>
      </div>

      {/* Sizing Kelly + MTA */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.sizing && (
          <div className="bg-card border border-border rounded-xl p-5">
            <p className="text-xs text-text-secondary mb-3">Position Sizing (Kelly)</p>
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div><span className="text-[10px] text-text-secondary block">R:R</span><p className="font-mono font-semibold">{data.sizing.risk_reward}x</p></div>
              <div><span className="text-[10px] text-text-secondary block">Win Rate est.</span><p className="font-mono font-semibold">{data.sizing.win_rate_est}%</p></div>
              <div><span className="text-[10px] text-text-secondary block">E[R]</span><p className={`font-mono font-semibold ${data.sizing.expected_value > 0 ? "text-emerald-400" : "text-red-400"}`}>{data.sizing.expected_value > 0 ? "+" : ""}{data.sizing.expected_value}</p></div>
              <div><span className="text-[10px] text-text-secondary block">Kelly complet</span><p className="font-mono">{data.sizing.kelly_full}%</p></div>
              <div><span className="text-[10px] text-text-secondary block">Kelly ¼</span><p className="font-mono text-gold">{data.sizing.kelly_fraction}%</p></div>
              <div><span className="text-[10px] text-text-secondary block">Position</span><p className="font-mono text-gold">{data.sizing.position_pct}%</p></div>
            </div>
          </div>
        )}

        {data.mta && (
          <div className="bg-card border border-border rounded-xl p-5">
            <p className="text-xs text-text-secondary mb-3">Multi-Timeframe Analysis</p>
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div><span className="text-[10px] text-text-secondary block">Score MTA</span><p className="font-mono font-semibold">{typeof data.mta.score === "number" ? data.mta.score.toFixed(0) : data.mta.score}/100</p></div>
              <div><span className="text-[10px] text-text-secondary block">Daily</span><p className={`font-mono font-semibold ${data.mta.daily === "BULLISH" ? "text-emerald-400" : data.mta.daily === "BEARISH" ? "text-red-400" : ""}`}>{data.mta.daily || "—"}</p></div>
              <div><span className="text-[10px] text-text-secondary block">Hourly</span><p className={`font-mono font-semibold ${data.mta.hourly === "BULLISH" ? "text-emerald-400" : data.mta.hourly === "BEARISH" ? "text-red-400" : ""}`}>{data.mta.hourly || "—"}</p></div>
            </div>
            <p className={`mt-2 text-xs font-medium ${data.mta.alignment === "ALIGNED" ? "text-emerald-400" : "text-amber-400"}`}>
              {data.mta.alignment === "ALIGNED" ? "✓ Timeframes alignés" : "⚠ Divergence entre timeframes"}
            </p>
          </div>
        )}
      </div>

      {/* Lien vers analyse complète (seulement si l'actif est dans le pipeline) */}
      <a href={`/asset/${data.symbol}`} className="block bg-card border border-gold/30 rounded-xl p-4 text-center hover:bg-gold/5 transition-colors">
        <p className="text-gold font-semibold text-sm">Voir l'analyse complète →</p>
        <p className="text-[10px] text-text-secondary mt-1">Radar 10 critères, breakdowns détaillés, backtest, fondamentaux — actifs du pipeline uniquement</p>
      </a>

      {/* Graphique */}
      {data.ohlcv?.length > 0 && (
        <InfoCard title="Graphique" icon={<TrendingUp size={18} />} description="100 derniers jours de prix avec moyennes mobiles.">
          <TradingChart data={data.ohlcv} height={400} />
        </InfoCard>
      )}

      {/* Stratégies — Top 3 + radar + détails cliquables */}
      {data.all_strategies?.length > 0 && (
        <StrategiesPanel strategies={data.all_strategies} bestName={best.name} lastPrice={data.last_price} symbol={data.symbol} />
      )}

      {/* Scores — cliquables */}
      <InfoCard title="Scores d'analyse" icon={<TrendingUp size={18} />} description="Cliquez sur chaque score pour voir sa définition et l'interprétation pour cet actif.">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {Object.entries(data.scores || {}).map(([key, value]: [string, any]) => (
            <ScoreCard key={key} name={key} score={value} price={data.last_price} />
          ))}
        </div>
      </InfoCard>

      {/* Indicateurs — cliquables */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <InfoCard title="Indicateurs techniques" icon={<TrendingUp size={18} />} description="Cliquez sur un indicateur pour comprendre ce qu'il mesure et ce que sa valeur signifie.">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <IndicatorCard label="RSI (14)" value={ind.rsi} definition="Le RSI mesure la vitesse et l'amplitude des mouvements de prix sur 14 jours. Il oscille entre 0 et 100." interpret={ind.rsi > 70 ? `RSI à ${ind.rsi?.toFixed(0)} = SURACHETÉ. Le prix a trop monté trop vite. Un repli est probable.` : ind.rsi < 30 ? `RSI à ${ind.rsi?.toFixed(0)} = SURVENDU. Le prix a trop baissé. Un rebond est possible.` : `RSI à ${ind.rsi?.toFixed(0)} = zone neutre. Pas de signal extrême.`} />
            <IndicatorCard label="MACD Hist." value={ind.macd_histogram?.toFixed(2)} definition="Le MACD mesure la différence entre deux moyennes mobiles. L'histogramme montre si le momentum accélère ou décélère." interpret={ind.macd_histogram > 0 ? `Histogramme positif (${ind.macd_histogram?.toFixed(2)}) = le momentum est HAUSSIER. La hausse accélère.` : `Histogramme négatif (${ind.macd_histogram?.toFixed(2)}) = le momentum est BAISSIER. La baisse accélère.`} />
            <IndicatorCard label="SMA 20" value={`$${ind.sma_20}`} definition="Moyenne mobile simple sur 20 jours. C'est la tendance à court terme. Le prix au-dessus = haussier, en dessous = baissier." interpret={data.last_price > ind.sma_20 ? `Prix ($${data.last_price}) > SMA 20 ($${ind.sma_20}) = tendance court terme HAUSSIÈRE.` : `Prix ($${data.last_price}) < SMA 20 ($${ind.sma_20}) = tendance court terme BAISSIÈRE.`} />
            <IndicatorCard label="SMA 50" value={`$${ind.sma_50}`} definition="Moyenne mobile sur 50 jours. C'est la tendance à moyen terme. Les institutionnels l'utilisent pour prendre des décisions." interpret={data.last_price > ind.sma_50 ? `Prix au-dessus de la SMA 50 = tendance moyen terme INTACTE.` : `Prix en dessous de la SMA 50 = la tendance moyen terme se DÉTÉRIORE.`} />
            <IndicatorCard label="SMA 200" value={`$${ind.sma_200}`} definition="Moyenne mobile sur 200 jours = la tendance long terme. C'est la frontière entre marché haussier et baissier." interpret={data.last_price > ind.sma_200 ? `Prix > SMA 200 = MARCHÉ HAUSSIER. Les investisseurs long terme restent acheteurs.` : `Prix < SMA 200 = MARCHÉ BAISSIER. Les investisseurs long terme deviennent prudents.`} />
            <IndicatorCard label="ATR (14)" value={`$${ind.atr}`} definition="Average True Range = la volatilité moyenne en dollars sur 14 jours. C'est combien le prix bouge par jour en moyenne." interpret={`L'actif bouge en moyenne de $${ind.atr} par jour. On utilise cette valeur pour calculer le Stop Loss (2×ATR = $${(ind.atr * 2)?.toFixed(2)}) et le Take Profit (3×ATR = $${(ind.atr * 3)?.toFixed(2)}).`} />
            <IndicatorCard label="Bollinger Haut" value={`$${ind.bb_upper}`} definition="Bande de Bollinger supérieure = SMA 20 + 2 écarts-types. Quand le prix la touche, il est en excès haussier." interpret={data.last_price > ind.bb_upper ? `Prix ($${data.last_price}) AU-DESSUS de la bande = EXCÈS HAUSSIER. Risque de correction.` : `Prix en dessous de la bande haute = pas de surachat.`} />
            <IndicatorCard label="Bollinger Bas" value={`$${ind.bb_lower}`} definition="Bande de Bollinger inférieure = SMA 20 - 2 écarts-types. Quand le prix la touche, il est en excès baissier." interpret={data.last_price < ind.bb_lower ? `Prix ($${data.last_price}) EN DESSOUS de la bande = EXCÈS BAISSIER. Rebond possible.` : `Prix au-dessus de la bande basse = pas de survente.`} />
          </div>
        </InfoCard>

        <InfoCard title="Détails" icon={<TrendingUp size={18} />} description="Informations complémentaires sur l'actif.">
          <div className="space-y-3 text-sm">
            {data.details?.genome_phase && (
              <DetailRow label="Phase de cycle" value={`Phase ${data.details.genome_phase}/5`} />
            )}
            {data.details?.seismograph_active !== undefined && (
              <DetailRow label="Micro-signaux actifs" value={String(data.details.seismograph_active)} />
            )}
            {data.details?.ipi_ad_trend && (
              <DetailRow label="A/D Line" value={data.details.ipi_ad_trend} />
            )}
            {data.regime?.regime && data.regime.regime !== "UNKNOWN" && (
              <DetailRow label="Régime" value={data.regime.regime} />
            )}
            {data.regime?.confidence > 0 && (
              <DetailRow label="Confiance régime" value={`${(data.regime.confidence * 100).toFixed(0)}%`} />
            )}
            {data.info?.market_cap > 0 && (
              <DetailRow label="Market Cap" value={`$${(data.info.market_cap / 1e9).toFixed(1)}B`} />
            )}
            {data.info?.currency && (
              <DetailRow label="Devise" value={data.info.currency} />
            )}
          </div>
        </InfoCard>
      </div>

      {/* ============ SCORES DES CRITÈRES ============ */}
      {data.scores && Object.keys(data.scores).length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-3">Scores par critère</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {[
              { key: "technical", label: "Technique", icon: "📊" },
              { key: "genome", label: "Génome", icon: "🧬" },
              { key: "ipi", label: "Institutionnel", icon: "🏦" },
              { key: "ivf", label: "Vélocité Fond.", icon: "⚡" },
              { key: "correlation", label: "Corrélation", icon: "🔗" },
              { key: "sentiment", label: "Sentiment", icon: "💬" },
              { key: "mts", label: "Macro", icon: "🌍" },
              { key: "sgi", label: "Social", icon: "👥" },
              { key: "sus", label: "Unicité", icon: "💎" },
              { key: "narrative", label: "Narrative", icon: "📖" },
            ].map(({ key, label, icon }) => {
              const score = data.scores[key] ?? (key === "sus" ? ((data.scores.novelty ?? 50) + (data.scores.complexity ?? 50)) / 2 : null);
              if (score === null) return null;
              return (
                <div key={key} className="bg-card border border-border rounded-xl p-3 text-center">
                  <span className="text-lg">{icon}</span>
                  <p className="text-[10px] text-text-secondary mt-1">{label}</p>
                  <p className={`text-lg font-mono font-bold mt-1 ${score >= 65 ? "text-emerald-400" : score >= 45 ? "text-yellow-400" : "text-red-400"}`}>
                    {score.toFixed(0)}
                  </p>
                  <div className="h-1 bg-surface rounded-full mt-1 overflow-hidden">
                    <div className={`h-full rounded-full ${score >= 65 ? "bg-emerald-400" : score >= 45 ? "bg-yellow-400" : "bg-red-400"}`} style={{ width: `${score}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ============ BOUTON PARTAGER ============ */}
      <ShareAnalysis data={data} />
    </div>
  );
}

function ShareAnalysis({ data }: { data: any }) {
  const [showMenu, setShowMenu] = useState(false);
  const [copied, setCopied] = useState(false);

  const buildMessage = () => {
    const scores = data.scores || {};
    const best = data.best_strategy || {};
    const lines = [
      `📊 *${data.symbol}* — Analyse Bilok-TradePilot`,
      ``,
      `💰 Prix: $${data.last_price}`,
      `📈 Score global: ${data.global_score?.toFixed(1)}/100 → *${data.action}*`,
      `🎯 Direction: ${best.direction || "NEUTRAL"}`,
      best.name ? `⚡ Stratégie: ${best.name} (conviction ${best.conviction?.toFixed(0)}%)` : "",
      data.regime?.regime ? `🌍 Régime: ${data.regime.regime}` : "",
      ``,
      `📊 Scores:`,
      scores.technical ? `  Technique: ${scores.technical.toFixed(0)}/100` : "",
      scores.genome ? `  Génome: ${scores.genome.toFixed(0)}/100` : "",
      scores.ipi ? `  Institutionnel: ${scores.ipi.toFixed(0)}/100` : "",
      scores.ivf ? `  Vélocité: ${scores.ivf.toFixed(0)}/100` : "",
      ``,
      `🔗 Analysé sur Bilok-TradePilot`,
      `https://app.bilok-tradepilot.be`,
      ``,
      `⚠️ Ce document est fourni à titre informatif uniquement et ne constitue en aucun cas un conseil en investissement, une recommandation d'achat ou de vente, ni une incitation à effectuer une quelconque transaction financière. Les performances passées ne préjugent pas des performances futures. Tout investissement comporte des risques de perte en capital. Consultez un conseiller financier agréé avant toute décision d'investissement.`,
    ].filter(Boolean);
    return lines.join("\n");
  };

  const shareWhatsApp = () => {
    const text = encodeURIComponent(buildMessage());
    window.open(`https://wa.me/?text=${text}`, "_blank");
    setShowMenu(false);
  };

  const shareEmail = () => {
    const subject = encodeURIComponent(`Analyse ${data.symbol} — Bilok-TradePilot`);
    const body = encodeURIComponent(buildMessage());
    window.open(`mailto:?subject=${subject}&body=${body}`, "_blank");
    setShowMenu(false);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(buildMessage());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="flex items-center gap-2 px-4 py-2.5 bg-gold/10 text-gold border border-gold/20 rounded-xl text-sm font-semibold hover:bg-gold/20 transition-colors"
      >
        <Share2 size={16} />
        Partager cette analyse
      </button>

      {showMenu && (
        <div className="absolute bottom-full left-0 mb-2 bg-card border border-border rounded-xl shadow-xl p-2 space-y-1 z-50 min-w-[220px]">
          <button onClick={shareWhatsApp} className="flex items-center gap-3 w-full px-3 py-2 rounded-lg hover:bg-surface transition-colors text-sm">
            <MessageCircle size={16} className="text-emerald-400" />
            <span>WhatsApp</span>
          </button>
          <button onClick={shareEmail} className="flex items-center gap-3 w-full px-3 py-2 rounded-lg hover:bg-surface transition-colors text-sm">
            <Mail size={16} className="text-blue-400" />
            <span>Email</span>
          </button>
          <button onClick={copyToClipboard} className="flex items-center gap-3 w-full px-3 py-2 rounded-lg hover:bg-surface transition-colors text-sm">
            {copied ? <Check size={16} className="text-emerald-400" /> : <Copy size={16} className="text-text-secondary" />}
            <span>{copied ? "Copié !" : "Copier le texte"}</span>
          </button>
        </div>
      )}
    </div>
  );
}

function PerfRow({ label, value }: { label: string; value: number }) {
  if (value === undefined || value === null) return null;
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-text-secondary">{label}</span>
      <span className={`text-sm font-mono font-semibold ${value >= 0 ? "text-gold" : "text-red-400"}`}>
        {value >= 0 ? "+" : ""}{value}%
      </span>
    </div>
  );
}

function IndicatorRow({ label, value, note }: { label: string; value: any; note?: string }) {
  return (
    <div className="bg-surface rounded-lg p-2.5">
      <p className="text-[10px] text-text-secondary">{label}</p>
      <p className="font-mono font-semibold">{value}</p>
      {note && <p className="text-[10px] text-text-secondary">{note}</p>}
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-text-secondary">{label}</span>
      <span className="font-mono">{value}</span>
    </div>
  );
}

// Définitions des stratégies
const STRATEGY_DEFINITIONS: Record<string, { definition: string; when: string; how: string }> = {
  trend_following: {
    definition: "Suit la tendance en cours. Quand les moyennes mobiles courtes (EMA 9) croisent au-dessus des longues (EMA 21), c'est un signal d'achat. Inversement pour la vente.",
    when: "Marché en tendance claire (ADX > 25). Ne fonctionne PAS en range.",
    how: "Croisement EMA 9/21 + prix au-dessus de la SMA 50 + confirmation OBV.",
  },
  mean_reversion: {
    definition: "Parie que le prix revient toujours vers sa moyenne. Quand le prix s'éloigne trop (touche les bandes de Bollinger + RSI extrême), il devrait revenir.",
    when: "Prix en excès (suracheté ou survendu). RSI < 30 ou > 70.",
    how: "Prix sous la bande Bollinger basse + RSI < 30 = achat. Prix au-dessus + RSI > 70 = vente.",
  },
  breakout: {
    definition: "Entre quand le prix casse un niveau clé (plus haut ou plus bas des 20 derniers jours) avec confirmation par le volume.",
    when: "Fin de consolidation. Le prix sort d'un range après une période calme.",
    how: "Prix > plus haut 20j + volume > 1.5x la moyenne = achat. Inversement pour la vente.",
  },
  momentum: {
    definition: "Suit la force relative. Quand plusieurs indicateurs de momentum (RSI, MACD, Stochastic) pointent dans la même direction, on entre.",
    when: "Momentum fort et cohérent sur plusieurs indicateurs.",
    how: "RSI > 55 + MACD positif + Stochastic croisement + performance 20j positive = 4 signaux alignés.",
  },
  mean_reversion_v2: {
    definition: "Version avancée du Mean Reversion. Utilise le Z-score (mesure statistique de l'excès), les canaux Keltner (plus robustes que Bollinger) et la contraction de volume (exhaustion du mouvement).",
    when: "Excès de prix confirmé par 3+ indicateurs. Plus précis que la V1.",
    how: "Z-score > 2 + sous Keltner + RSI < 25 + volume en contraction = signal fort.",
  },
  fibonacci: {
    definition: "Les niveaux de Fibonacci (0.382, 0.5, 0.618) sont des niveaux 'naturels' où le prix a tendance à rebondir. Le 0.618 (Golden Ratio) est le plus puissant.",
    when: "Après un mouvement fort, le prix retrace vers un niveau Fibonacci clé.",
    how: "Prix touche le niveau 0.618 du retracement = zone de rebond probable. SL sous le 0.786.",
  },
  ichimoku: {
    definition: "Système japonais complet qui combine 5 composantes : Tenkan (tendance courte), Kijun (tendance moyenne), nuage Senkou (support/résistance future), Chikou (confirmation).",
    when: "Prix au-dessus du nuage + Tenkan > Kijun + nuage vert = tout aligné.",
    how: "3 conditions : prix vs nuage, Tenkan vs Kijun, couleur du nuage. Minimum 2/3 pour un signal.",
  },
  adaptive_trend: {
    definition: "Trend Following intelligent : les paramètres (périodes EMA, RSI, multiplicateurs ATR) s'adaptent automatiquement à la volatilité de l'actif. Marché calme = périodes longues. Marché nerveux = périodes courtes.",
    when: "Tout marché — s'adapte automatiquement au contexte.",
    how: "EMA 5/13 en haute volatilité, EMA 13/34 en basse volatilité. Confirmation par OBV.",
  },
  multi_signal: {
    definition: "Exige que 4 indicateurs sur 6 soient d'accord AVANT d'entrer. C'est le filtre le plus strict — réduit les faux signaux de ~60%. Les 6 votes : EMA, RSI, MACD, SMA 50, OBV, Stochastic.",
    when: "Consensus fort entre les indicateurs. Conviction max = 95.",
    how: "6 indicateurs votent LONG ou SHORT. Minimum 4/6 d'accord pour agir.",
  },
  keltner_breakout: {
    definition: "Breakout adaptatif basé sur les canaux Keltner (EMA + ATR) au lieu d'un range fixe. Les canaux s'adaptent à la volatilité de chaque actif. Plus robuste que le breakout classique.",
    when: "Prix sort du canal Keltner avec volume > 1.5x la moyenne.",
    how: "Prix > canal Keltner haut + volume fort = achat. Stop Loss = milieu du canal.",
  },
  vwap_reversion: {
    definition: "Mean Reversion autour du VWAP (prix moyen pondéré par le volume). Le VWAP est le 'vrai' prix du marché utilisé par les institutionnels. Plus précis que les bandes de Bollinger.",
    when: "Prix dévie de > 2% du VWAP + RSI extrême.",
    how: "Prix sous VWAP de 3% + RSI < 30 = achat. Objectif = retour au VWAP.",
  },
  momentum_rotation: {
    definition: "Classement cross-sectionnel : compare le momentum de TOUS les actifs et achète les top 20%, vend les bottom 20%. Prouvé académiquement (facteur momentum). C'est la stratégie la plus performante du système (48 actifs gagnés).",
    when: "Toujours actif — classement mensuel des 218 actifs.",
    how: "Score = rendement 3 mois / volatilité. Top 20% = LONG, Bottom 20% = SHORT.",
  },
};

// Définitions des scores
const SCORE_DEFINITIONS: Record<string, { emoji: string; name: string; definition: string; interpret: (score: number) => string }> = {
  technical: {
    emoji: "📊", name: "Analyse Technique",
    definition: "Note composite de 20 indicateurs (RSI, MACD, SMA, ADX, VWAP, Bollinger, Pivots, divergences...). Mesure la dynamique de prix, le momentum et la force de la tendance.",
    interpret: (s) => s >= 70 ? "Forte dynamique haussière. La majorité des 20 indicateurs sont alignés à la hausse." : s >= 55 ? "Dynamique modérément positive. La tendance est favorable mais pas tous les indicateurs sont alignés." : s >= 45 ? "Zone neutre. Les indicateurs se contredisent — pas de tendance claire." : s >= 30 ? "Dynamique légèrement baissière. Attention, la tendance se retourne." : "Forte dynamique baissière. Les indicateurs sont alignés à la baisse.",
  },
  genome: {
    emoji: "🧬", name: "Génome Explosif",
    definition: "Détecte si l'actif est en phase pré-explosive : compression de volatilité (Bollinger squeeze), contraction de volume, inside bars, divergences RSI. Analyse le cycle de Wyckoff (accumulation → markup → distribution → markdown).",
    interpret: (s) => s >= 70 ? "Configuration explosive ! Plusieurs micro-signaux sont actifs. Un mouvement majeur est imminent." : s >= 50 ? "Quelques signes de compression. L'énergie s'accumule mais pas encore prête à exploser." : "Pas de configuration explosive. L'actif est dans une phase normale de son cycle.",
  },
  ipi: {
    emoji: "🏦", name: "Capital Institutionnel",
    definition: "Détecte si les gros investisseurs (fonds, banques) accumulent ou distribuent. Analyse la ligne Accumulation/Distribution, le Smart Money Flow (gros volumes sans mouvement de prix) et les anomalies de volume.",
    interpret: (s) => s >= 70 ? "Accumulation institutionnelle détectée ! Les gros acteurs achètent discrètement. Suivez l'argent intelligent." : s >= 50 ? "Activité institutionnelle neutre. Pas de signal clair d'accumulation ou de distribution." : "Distribution probable. Les institutionnels semblent vendre — signal d'alerte.",
  },
  ivf: {
    emoji: "⚡", name: "Vélocité Fondamentale",
    definition: "Mesure l'ACCÉLÉRATION des fondamentaux : le momentum accélère-t-il ? L'actif surperforme-t-il son benchmark ? Y a-t-il des gaps de surprise (résultats meilleurs que prévu) ?",
    interpret: (s) => s >= 70 ? "Les fondamentaux accélèrent ! L'actif surperforme son benchmark et montre des surprises positives." : s >= 50 ? "Fondamentaux stables. Ni amélioration ni détérioration notable." : "Décélération fondamentale. L'actif sous-performe et perd de l'élan.",
  },
  novelty: {
    emoji: "💎", name: "Novelty (Unicité)",
    definition: "Mesure si le comportement actuel de l'actif est INHABITUEL par rapport à son historique. Un comportement rare a plus de valeur informationnelle qu'un comportement normal.",
    interpret: (s) => s >= 70 ? "Comportement très inhabituel ! Le Z-score des rendements récents est élevé. Signal rare = potentiellement exploitable." : s >= 50 ? "Comportement dans la norme. Rien de spécial par rapport à l'historique." : "Comportement très normal. Pas d'avantage informationnel.",
  },
  complexity: {
    emoji: "🔬", name: "Complexité du Signal",
    definition: "Mesure si le signal nécessite une analyse complexe pour être vu. Un signal simple (croisement SMA) est vu par tout le monde et déjà dans le prix. Un signal complexe (divergence multi-indicateurs) est vu par peu de gens = avantage.",
    interpret: (s) => s >= 70 ? "Signal complexe — peu de traders l'ont vu. Avantage informationnel probable." : s >= 50 ? "Signal de complexité moyenne." : "Signal trop simple. Tout le monde le voit, probablement déjà dans le prix.",
  },
};

function ScoreCard({ name, score }: { name: string; score: number; price?: number }) {
  const [expanded, setExpanded] = useState(false);
  const config = SCORE_DEFINITIONS[name];

  return (
    <div
      onClick={() => setExpanded(!expanded)}
      className={`bg-surface rounded-xl p-4 cursor-pointer transition-all hover:bg-gold/5 ${expanded ? "ring-1 ring-gold/20 col-span-2 md:col-span-3" : ""}`}
    >
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs text-text-secondary capitalize flex items-center gap-1">
          {config?.emoji || "📊"} {config?.name || name.replace("_", " ")}
        </p>
        <span className="text-[10px] text-gold">{expanded ? "fermer" : "cliquez"}</span>
      </div>
      <div className="flex items-center gap-3">
        <span className={`text-2xl font-mono font-bold ${score >= 65 ? "text-gold" : score >= 45 ? "text-text-primary" : "text-red-400"}`}>
          {typeof score === 'number' ? score.toFixed(1) : score}
        </span>
        <div className="flex-1 h-2 bg-background rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${score >= 65 ? "bg-gold" : score >= 45 ? "bg-text-secondary" : "bg-red-400"}`} style={{ width: `${score}%` }} />
        </div>
      </div>
      {expanded && config && (
        <div className="mt-3 pt-3 border-t border-border/30 space-y-2">
          <p className="text-xs text-text-secondary leading-relaxed">{config.definition}</p>
          <div className="p-2 bg-gold/5 rounded-lg border-l-2 border-gold/30">
            <p className="text-xs leading-relaxed">{config.interpret(score)}</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════
// Panel des 15 stratégies — Top 3 + liste cliquable
// ═══════════════════════════════════════════

const STRATEGY_DESCRIPTIONS: Record<string, { type: string; edge: string; when: string }> = {
  trend_following: { type: "Classic", edge: "Suit la tendance via croisement EMA 9/21", when: "Marché en tendance claire (BULL/BEAR)" },
  mean_reversion: { type: "Classic", edge: "Achat sur excès baissier (Bollinger + RSI)", when: "Prix en excès par rapport à sa moyenne" },
  breakout: { type: "Classic", edge: "Cassure de range avec confirmation volume", when: "Sortie d'une zone de consolidation" },
  momentum: { type: "Classic", edge: "Force relative RSI + MACD + Stochastic", when: "Momentum fort et soutenu" },
  mean_reversion_v2: { type: "Avancé", edge: "Z-Score + Stochastic + Keltner — plus robuste que V1", when: "Excès confirmé par 3 indicateurs indépendants" },
  fibonacci: { type: "Avancé", edge: "Rebond sur niveaux 38.2% / 50% / 61.8%", when: "Pullback dans une tendance — Golden Ratio" },
  ichimoku: { type: "Avancé", edge: "Système japonais complet : nuage + Tenkan/Kijun", when: "Tendance confirmée par le nuage Kumo" },
  adaptive_trend: { type: "Pro", edge: "EMA dynamiques qui s'adaptent à la volatilité", when: "Toutes conditions — paramètres auto-ajustés" },
  multi_signal: { type: "Pro", edge: "Exige 4/6 indicateurs d'accord — réduit 60% faux signaux", when: "Forte convergence de signaux" },
  keltner_breakout: { type: "Pro", edge: "Canaux ATR adaptatifs au lieu de range fixe", when: "Breakout de volatilité avec confirmation" },
  vwap_reversion: { type: "Pro", edge: "Retour au prix moyen pondéré par volume", when: "Écart excessif par rapport au VWAP institutionnel" },
  momentum_rotation: { type: "Pro", edge: "Classement relatif des 500 actifs — prouvé académiquement", when: "Achète les top 20%, vend les bottom 20%" },
  regime_cascade: { type: "Genius", edge: "Détecte changement de régime court terme avant le moyen terme", when: "Le leader a bougé, les suiveurs n'ont pas encore réagi" },
  volatility_explosion: { type: "Genius", edge: "3+ signaux de compression simultanés → explosion imminente", when: "ATR au plus bas + Bollinger squeeze + volume en contraction" },
  anti_consensus: { type: "Genius", edge: "Parie contre l'euphorie/panique extrême — 5-10 trades/an", when: "RSI > 78 + volume déclinant + signal crowdé → retournement" },
};

const TYPE_COLORS: Record<string, string> = {
  Classic: "text-text-secondary bg-surface border-border",
  Avancé: "text-blue-400 bg-blue-400/10 border-blue-400/20",
  Pro: "text-purple-400 bg-purple-400/10 border-purple-400/20",
  Genius: "text-gold bg-gold/10 border-gold/20",
};

function StrategiesPanel({ strategies, bestName, lastPrice, symbol }: { strategies: any[]; bestName: string; lastPrice: number; symbol: string }) {
  const [selectedStrat, setSelectedStrat] = useState<string | null>(null);

  // Trier par conviction décroissante, exclure NEUTRAL
  const sorted = [...strategies]
    .filter((s) => s.direction !== "NEUTRAL")
    .sort((a, b) => (b.conviction || 0) - (a.conviction || 0));
  const neutrals = strategies.filter((s) => s.direction === "NEUTRAL");

  const top6 = sorted.slice(0, 6);
  const others = sorted.slice(6);
  const selected = strategies.find((s) => s.strategy === selectedStrat);

  // Données pour le radar — TOUTES les 15 stratégies
  // Les NEUTRAL ont un minimum de 8 pour être visibles sur le radar
  const radarData = strategies.map((s) => ({
    label: (STRATEGY_LABELS[s.strategy] || s.strategy).slice(0, 14),
    value: Math.max(s.conviction || 0, 8),
    icon: s.direction === "LONG" ? "📈" : s.direction === "SHORT" ? "📉" : "—",
  }));

  return (
    <div className="space-y-4">
      {/* Radar des stratégies */}
      {radarData.length >= 3 && (
        <InfoCard title={`Radar des ${strategies.length} stratégies — ${symbol}`} icon={<TrendingUp size={18} />} description="Conviction de chaque stratégie (0-100). Plus la forme est large, plus les stratégies convergent. Les icônes 📈/📉 indiquent la direction LONG/SHORT.">
          <div className="flex justify-center">
            <RadarChart data={radarData} size={420} />
          </div>
        </InfoCard>
      )}

      {/* Top 3 stratégies */}
      <InfoCard title={`Top 6 Stratégies — ${symbol}`} icon={<TrendingUp size={18} />} description="Les 6 stratégies les plus convaincantes pour cet actif. Cliquez pour voir le détail complet.">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {top6.map((s, i) => {
            const desc = STRATEGY_DESCRIPTIONS[s.strategy] || { type: "?", edge: "", when: "" };
            const typeColor = TYPE_COLORS[desc.type] || TYPE_COLORS.Classic;
            const isSelected = selectedStrat === s.strategy;
            return (
              <button key={s.strategy} onClick={() => setSelectedStrat(isSelected ? null : s.strategy)}
                className={`text-left p-4 rounded-xl border transition-all ${isSelected ? "border-gold bg-gold/5 ring-1 ring-gold/30" : s.strategy === bestName ? "border-gold/30 bg-gold/5" : "border-border hover:border-gold/20"}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold border ${typeColor}`}>{desc.type}</span>
                  <span className="text-lg font-bold text-gold">#{i + 1}</span>
                </div>
                <p className="text-sm font-semibold">{STRATEGY_LABELS[s.strategy] || s.strategy}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${s.direction === "LONG" ? "bg-gold/10 text-gold" : "bg-red-400/10 text-red-400"}`}>{s.direction}</span>
                  <span className="text-xs text-text-secondary">Conv. {s.conviction}/100</span>
                </div>
                {s.entry && s.stop_loss && (
                  <div className="mt-2 grid grid-cols-3 gap-1 text-[10px]">
                    <div><span className="text-text-secondary">Entry</span><p className="font-mono">${s.entry}</p></div>
                    <div><span className="text-text-secondary">SL</span><p className="font-mono text-red-400">${s.stop_loss}</p></div>
                    <div><span className="text-text-secondary">TP</span><p className="font-mono text-gold">${s.take_profit}</p></div>
                  </div>
                )}
                <p className="text-[9px] text-text-secondary mt-2 italic">{desc.edge}</p>
              </button>
            );
          })}
        </div>
      </InfoCard>

      {/* Détail de la stratégie sélectionnée */}
      {selected && (
        <div className="bg-card border border-gold/20 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-lg font-bold text-gold">{STRATEGY_LABELS[selected.strategy] || selected.strategy}</h4>
              <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold border ${TYPE_COLORS[(STRATEGY_DESCRIPTIONS[selected.strategy] || {}).type || "Classic"]}`}>
                {(STRATEGY_DESCRIPTIONS[selected.strategy] || {}).type}
              </span>
            </div>
            <button onClick={() => setSelectedStrat(null)} className="text-text-secondary hover:text-text-primary text-xs">Fermer</button>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[9px] text-text-secondary uppercase">Direction</p>
              <p className={`text-lg font-bold ${selected.direction === "LONG" ? "text-gold" : selected.direction === "SHORT" ? "text-red-400" : "text-text-secondary"}`}>{selected.direction}</p>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <p className="text-[9px] text-text-secondary uppercase">Conviction</p>
              <p className="text-lg font-bold">{selected.conviction}<span className="text-sm text-text-secondary">/100</span></p>
            </div>
          </div>

          {selected.entry && selected.stop_loss && (
            <div className="grid grid-cols-4 gap-2 text-xs">
              <div className="bg-surface rounded-lg p-2 text-center">
                <p className="text-[8px] text-text-secondary">Entrée</p>
                <p className="font-mono font-bold">${selected.entry}</p>
              </div>
              <div className="bg-surface rounded-lg p-2 text-center">
                <p className="text-[8px] text-text-secondary">Stop Loss</p>
                <p className="font-mono font-bold text-red-400">${selected.stop_loss}</p>
                <p className="text-[8px] text-red-400">{((selected.stop_loss - selected.entry) / selected.entry * 100).toFixed(1)}%</p>
              </div>
              <div className="bg-surface rounded-lg p-2 text-center">
                <p className="text-[8px] text-text-secondary">TP1</p>
                <p className="font-mono font-bold text-gold">${selected.take_profit}</p>
                <p className="text-[8px] text-gold">+{((selected.take_profit - selected.entry) / selected.entry * 100).toFixed(1)}%</p>
              </div>
              <div className="bg-surface rounded-lg p-2 text-center">
                <p className="text-[8px] text-text-secondary">R:R</p>
                <p className="font-mono font-bold">{selected.stop_loss && selected.take_profit ? `1:${(Math.abs(selected.take_profit - selected.entry) / Math.abs(selected.entry - selected.stop_loss)).toFixed(1)}` : "—"}</p>
              </div>
            </div>
          )}

          <div className="bg-surface rounded-lg p-3 space-y-2 text-xs">
            <p><span className="text-text-secondary">Edge :</span> {(STRATEGY_DESCRIPTIONS[selected.strategy] || {}).edge}</p>
            <p><span className="text-text-secondary">Fonctionne quand :</span> {(STRATEGY_DESCRIPTIONS[selected.strategy] || {}).when}</p>
            <p className="text-text-secondary italic">
              {selected.conviction >= 70 ? `Forte conviction (${selected.conviction}/100) — cette stratégie est très confiante sur ${symbol}. Le signal est clair et les conditions sont réunies.`
                : selected.conviction >= 50 ? `Conviction modérée (${selected.conviction}/100) — le signal existe mais n'est pas encore pleinement confirmé. Surveiller l'évolution.`
                : selected.conviction > 0 ? `Faible conviction (${selected.conviction}/100) — les conditions ne sont que partiellement réunies. Attendre une meilleure configuration.`
                : `Aucun signal — les conditions requises ne sont pas remplies pour ${symbol}.`}
            </p>
          </div>
        </div>
      )}

      {/* Autres stratégies — liste compacte */}
      {others.length > 0 && (
        <InfoCard title={`Autres stratégies (${others.length})`} icon={<TrendingUp size={18} />} description="Stratégies avec un signal mais une conviction plus faible. Cliquez pour voir le détail.">
          <div className="space-y-1">
            {others.map((s) => {
              const desc = STRATEGY_DESCRIPTIONS[s.strategy] || { type: "?", edge: "" };
              const typeColor = TYPE_COLORS[desc.type] || TYPE_COLORS.Classic;
              return (
                <button key={s.strategy} onClick={() => setSelectedStrat(selectedStrat === s.strategy ? null : s.strategy)}
                  className={`w-full flex items-center justify-between p-2.5 rounded-lg text-left transition-all ${selectedStrat === s.strategy ? "bg-gold/5 border border-gold/20" : "hover:bg-surface"}`}>
                  <div className="flex items-center gap-2">
                    <span className={`text-[8px] px-1 py-0.5 rounded font-bold border ${typeColor}`}>{desc.type}</span>
                    <span className="text-xs font-semibold">{STRATEGY_LABELS[s.strategy] || s.strategy}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    <span className={`px-1.5 py-0.5 rounded font-semibold ${s.direction === "LONG" ? "bg-gold/10 text-gold" : "bg-red-400/10 text-red-400"}`}>{s.direction}</span>
                    <span className="font-mono text-text-secondary">{s.conviction}/100</span>
                    {s.entry && <span className="font-mono">${s.entry}</span>}
                  </div>
                </button>
              );
            })}
          </div>
        </InfoCard>
      )}

      {/* Stratégies neutres */}
      {neutrals.length > 0 && (
        <p className="text-[10px] text-text-secondary text-center">{neutrals.length} stratégie{neutrals.length > 1 ? "s" : ""} sans signal (NEUTRAL) — conditions non réunies</p>
      )}
    </div>
  );
}


function StrategyCard({ strategy, isBest, lastPrice }: {
  strategy: any; isBest: boolean; lastPrice: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const s = strategy;
  const def = STRATEGY_DEFINITIONS[s.strategy];
  const label = STRATEGY_LABELS[s.strategy] || s.strategy;

  return (
    <div
      onClick={() => setExpanded(!expanded)}
      className={`bg-surface rounded-xl p-3 cursor-pointer transition-all hover:bg-gold/5 ${
        isBest ? "border border-gold/20" : ""
      } ${expanded ? "col-span-1 md:col-span-2 ring-1 ring-gold/20" : ""}`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold">{label}</p>
          {isBest && <p className="text-[10px] text-gold">Recommandée</p>}
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-xs px-2 py-0.5 border rounded font-semibold ${
            s.direction === "LONG" ? "text-gold bg-gold/10 border-gold/20" :
            s.direction === "SHORT" ? "text-red-400 bg-red-400/10 border-red-400/20" :
            "text-text-secondary bg-surface border-border"
          }`}>{s.direction}</span>
          <span className="font-mono text-sm w-8 text-right">{s.conviction}</span>
        </div>
      </div>

      {expanded && def && (
        <div className="mt-3 pt-3 border-t border-border/30 space-y-3">
          <div>
            <p className="text-[10px] text-gold font-semibold mb-1">QU'EST-CE QUE C'EST ?</p>
            <p className="text-xs text-text-secondary leading-relaxed">{def.definition}</p>
          </div>
          <div>
            <p className="text-[10px] text-gold font-semibold mb-1">QUAND ÇA FONCTIONNE</p>
            <p className="text-xs text-text-secondary leading-relaxed">{def.when}</p>
          </div>
          <div>
            <p className="text-[10px] text-gold font-semibold mb-1">COMMENT ÇA ENTRE</p>
            <p className="text-xs text-text-secondary leading-relaxed">{def.how}</p>
          </div>
          <div className="p-2 bg-gold/5 rounded-lg border-l-2 border-gold/30">
            <p className="text-xs leading-relaxed">
              {s.direction === "NEUTRAL"
                ? `Cette stratégie ne voit pas de signal clair actuellement sur cet actif. Les conditions d'entrée ne sont pas réunies.`
                : s.direction === "LONG"
                  ? `Signal ACHAT avec ${s.conviction}/100 de conviction. ${s.entry ? `Entrée suggérée à $${s.entry}` : ""} ${s.stop_loss ? `— Stop Loss $${s.stop_loss}` : ""} ${s.take_profit ? `— Objectif $${s.take_profit}` : ""}`
                  : `Signal VENTE avec ${s.conviction}/100 de conviction. ${s.entry ? `Entrée suggérée à $${s.entry}` : ""} ${s.stop_loss ? `— Stop Loss $${s.stop_loss}` : ""} ${s.take_profit ? `— Objectif $${s.take_profit}` : ""}`
              }
            </p>
          </div>
          {s.zscore !== undefined && <p className="text-[10px] text-text-secondary">Z-score: {s.zscore}</p>}
          {s.volume_ratio !== undefined && <p className="text-[10px] text-text-secondary">Volume ratio: {s.volume_ratio}x</p>}
          {s.signals && <p className="text-[10px] text-text-secondary">Signaux: {s.signals.join(", ")}</p>}
        </div>
      )}
    </div>
  );
}

function IndicatorCard({ label, value, definition, interpret }: {
  label: string; value: any; definition: string; interpret: string;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      onClick={() => setExpanded(!expanded)}
      className={`bg-surface rounded-lg p-2.5 cursor-pointer transition-all hover:bg-gold/5 ${expanded ? "col-span-2 ring-1 ring-gold/20" : ""}`}
    >
      <div className="flex items-center justify-between">
        <p className="text-[10px] text-text-secondary">{label}</p>
        <span className="text-[9px] text-gold">{expanded ? "×" : "?"}</span>
      </div>
      <p className="font-mono font-semibold">{value}</p>
      {expanded && (
        <div className="mt-2 pt-2 border-t border-border/30 space-y-1.5">
          <p className="text-[10px] text-text-secondary leading-relaxed">{definition}</p>
          <div className="p-1.5 bg-gold/5 rounded border-l-2 border-gold/30">
            <p className="text-[10px] leading-relaxed">{interpret}</p>
          </div>
        </div>
      )}
    </div>
  );
}
