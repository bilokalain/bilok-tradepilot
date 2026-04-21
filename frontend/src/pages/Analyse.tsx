import { useState, useEffect, useRef } from "react";
import { Search, TrendingUp, Share2, MessageCircle, Mail, Copy, Check, Sparkles, BarChart3, Brain } from "lucide-react";
import api from "../services/api";
import TradingChart from "../components/TradingChart";
import ScoreGauge from "../components/ui/ScoreGauge";
import InfoCard from "../components/ui/InfoCard";
import SignalBadge from "../components/ui/SignalBadge";
import RadarChart from "../components/ui/RadarChart";
import AssetInfoCard from "../components/AssetInfoCard";
import { STRATEGY_LABELS, STRAT_CONFIG, TYPE_COLORS, CRITERIA_CONFIG } from "../config/strategies";

const SUGGESTIONS = [
  "AAPL", "TSLA", "NVDA", "PLTR", "COIN", "AMC", "GME",
  "S&P 500", "CAC 40", "DAX", "NASDAQ", "DOW JONES", "NIKKEI",
  "BITCOIN", "ETHEREUM", "GOLD", "OIL", "SILVER",
  "EUR/USD", "LVMH", "ASML",
];

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
  const [expandedStrat, setExpandedStrat] = useState<string | null>(null);
  const [expandedCriterion, setExpandedCriterion] = useState<string | null>(null);

  // Stratégies triées par conviction décroissante (NEUTRAL à 0 en bas)
  const strategies = [...(data.all_strategies || [])].sort((a: any, b: any) => {
    const ca = a.direction === "NEUTRAL" ? -1 : (a.conviction || 0);
    const cb = b.direction === "NEUTRAL" ? -1 : (b.conviction || 0);
    return cb - ca;
  });
  const best = data.best_strategy || {};
  const scores = data.scores || {};

  // Critères triés par score décroissant
  const criteriaEntries = Object.entries(CRITERIA_CONFIG).sort(([a], [b]) => (scores[b] ?? 50) - (scores[a] ?? 50));

  // Radar stratégies (15 branches, NEUTRAL min 8 pour rester visible)
  const stratRadar = strategies.map((s: any) => ({
    label: (STRATEGY_LABELS[s.strategy] || s.strategy).slice(0, 14),
    value: Math.max(s.conviction || 0, 8),
    icon: s.direction === "LONG" ? "📈" : s.direction === "SHORT" ? "📉" : "—",
  }));

  // Radar critères (10 branches)
  const criteriaRadar = Object.entries(CRITERIA_CONFIG).map(([key, config]) => ({
    label: config.label.length > 12 ? config.label.slice(0, 12) + "." : config.label,
    value: scores[key] ?? 50,
    icon: config.icon,
  }));

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

      {/* ═══ CARTE D'IDENTITÉ ═══ */}
      <AssetInfoCard symbol={data.symbol} />

      {/* ═══ 1. VERDICT ═══ */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center gap-8 flex-wrap">
          <ScoreGauge score={data.global_score || 0} size={120} sublabel="/100" label="Score V2" />
          <div>
            <SignalBadge action={data.action} direction={best.direction} size="lg" showExplanation />
            {best.name && (
              <div className="mt-3 p-3 bg-surface rounded-xl">
                <p className="text-xs text-text-secondary">Stratégie recommandée</p>
                <p className="font-semibold">{STRATEGY_LABELS[best.name] || best.name}</p>
                <p className="text-xs text-text-secondary mt-1">Conviction : {best.conviction}/100</p>
              </div>
            )}
          </div>
          {best.stop_loss > 0 && (() => {
            const entry = best.entry || data.last_price;
            const sl = best.stop_loss;
            const tp1 = best.take_profit_1 || best.take_profit;
            const tp2 = best.take_profit_2;
            const rr = sl && tp1 ? (Math.abs(tp1 - entry) / Math.abs(entry - sl)).toFixed(1) : "—";
            return (
              <div className="bg-surface rounded-xl p-4 min-w-[220px]">
                <p className="text-xs text-text-secondary mb-3">Niveaux de prix suggérés</p>
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div><p className="text-xs font-semibold">Entrée</p><p className="text-[9px] text-text-secondary">Prix recommandé pour ouvrir la position</p></div>
                    <p className="text-lg font-mono font-bold">${entry}</p>
                  </div>
                  <div className="flex items-center justify-between">
                    <div><p className="text-xs font-semibold text-red-400">Stop Loss</p><p className="text-[9px] text-text-secondary">Sortie automatique si le prix va contre nous</p></div>
                    <p className="text-lg font-mono font-bold text-red-400">${sl}</p>
                  </div>
                  <div className="flex items-center justify-between">
                    <div><p className="text-xs font-semibold text-gold">Objectif 1</p><p className="text-[9px] text-text-secondary">Premier objectif de profit</p></div>
                    <p className="text-lg font-mono font-bold text-gold">${tp1}</p>
                  </div>
                  {tp2 && (
                    <div className="flex items-center justify-between">
                      <div><p className="text-xs font-semibold text-emerald-400">Objectif 2</p><p className="text-[9px] text-text-secondary">Objectif optimiste (laisser courir)</p></div>
                      <p className="text-lg font-mono font-bold text-emerald-400">${tp2}</p>
                    </div>
                  )}
                </div>
                <div className="mt-3 pt-3 border-t border-border/50 text-xs">
                  <span className="text-text-secondary">Ratio risque/récompense : </span>
                  <span className="font-mono font-semibold text-gold">1:{rr}</span>
                  <p className="text-text-secondary mt-1">Pour chaque dollar risqué, le gain potentiel est de {rr}$.</p>
                </div>
              </div>
            );
          })()}
        </div>
      </div>

      {/* ═══ 2. GRAPHIQUE ═══ */}
      {data.ohlcv?.length > 0 && (
        <InfoCard title="Graphique" icon={<BarChart3 size={18} />} description="Historique des prix avec moyennes mobiles.">
          <TradingChart data={data.ohlcv} height={400} />
        </InfoCard>
      )}

      {/* ═══ 3. RADAR 15 STRATÉGIES ═══ */}
      {strategies.length >= 3 && (
        <InfoCard title={`Radar des 15 stratégies — ${data.symbol}`} icon={<Brain size={18} />} description="Conviction de chaque stratégie (0-100). Plus la forme est large, plus les stratégies convergent. Module 2 — Analyseur.">
          <div className="flex justify-center">
            <RadarChart data={stratRadar} size={420} />
          </div>
        </InfoCard>
      )}

      {/* ═══ 4. CARTES DES 15 STRATÉGIES ═══ */}
      {strategies.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-1 flex items-center gap-2"><TrendingUp size={18} /> Les 15 stratégies — {data.symbol}</h3>
          <p className="text-xs text-text-secondary mb-4">Cliquez sur une stratégie pour voir le détail : description, interprétation du score, plan de trade.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {strategies.map((s: any) => {
              const config = STRAT_CONFIG[s.strategy] || { type: "?", icon: "?", edge: "", when: "", description: "", interpret: () => "" };
              const typeColor = TYPE_COLORS[config.type] || TYPE_COLORS.Classic;
              const conv = s.conviction || 0;
              const isExpanded = expandedStrat === s.strategy;
              const interpretation = config.interpret(conv, s.direction);
              return (
                <button key={s.strategy} onClick={() => setExpandedStrat(isExpanded ? null : s.strategy)}
                  className={`text-left bg-card rounded-xl border p-5 transition-all ${isExpanded ? "border-gold bg-gold/5 ring-1 ring-gold/30" : "border-border hover:border-gold/20"}`}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{config.icon}</span>
                      <span className="text-sm font-semibold">{STRATEGY_LABELS[s.strategy] || s.strategy}</span>
                    </div>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold border ${typeColor}`}>{config.type}</span>
                  </div>
                  <div className="flex items-center gap-4 mb-3">
                    <ScoreGauge score={conv} size={70} />
                    <div className="flex-1">
                      {s.direction !== "NEUTRAL" ? (
                        <span className={`text-xs px-2 py-1 rounded font-semibold ${s.direction === "LONG" ? "bg-gold/10 text-gold" : "bg-red-400/10 text-red-400"}`}>
                          {s.direction === "LONG" ? "📈" : "📉"} {s.direction}
                        </span>
                      ) : (
                        <span className="text-xs px-2 py-1 rounded bg-surface text-text-secondary">— NEUTRAL</span>
                      )}
                      <p className="text-[10px] text-text-secondary mt-1">Poids dans le score final : {s.weight ? `${(s.weight * 100).toFixed(0)}%` : "—"}</p>
                    </div>
                  </div>
                  <p className="text-[11px] text-text-secondary leading-relaxed">{interpretation}</p>
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-border/50 space-y-3">
                      <p className="text-[11px] text-text-secondary">{config.description}</p>
                      <div className="text-xs space-y-1">
                        <p><span className="text-text-secondary">Edge :</span> {config.edge}</p>
                        <p><span className="text-text-secondary">Fonctionne quand :</span> {config.when}</p>
                      </div>
                      {s.entry && s.stop_loss && (
                        <div className="grid grid-cols-4 gap-2 text-xs">
                          <div className="bg-surface rounded-lg p-2 text-center"><p className="text-[8px] text-text-secondary">Entrée</p><p className="font-mono font-bold">${s.entry}</p></div>
                          <div className="bg-surface rounded-lg p-2 text-center"><p className="text-[8px] text-text-secondary">SL</p><p className="font-mono font-bold text-red-400">${s.stop_loss}</p></div>
                          <div className="bg-surface rounded-lg p-2 text-center"><p className="text-[8px] text-text-secondary">TP</p><p className="font-mono font-bold text-gold">${s.take_profit}</p></div>
                          <div className="bg-surface rounded-lg p-2 text-center"><p className="text-[8px] text-text-secondary">R:R</p><p className="font-mono font-bold">1:{(Math.abs(s.take_profit - s.entry) / Math.abs(s.entry - s.stop_loss)).toFixed(1)}</p></div>
                        </div>
                      )}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
          {strategies.filter((s: any) => s.direction === "NEUTRAL").length > 0 && (
            <p className="text-[10px] text-text-secondary text-center mt-3">{strategies.filter((s: any) => s.direction === "NEUTRAL").length} stratégies sans signal actif</p>
          )}
        </div>
      )}

      {/* ═══ 5. RADAR 10 CRITÈRES ═══ */}
      {Object.keys(scores).length > 0 && (
        <InfoCard title="Radar des 10 critères" icon={<Sparkles size={18} />} description="Les 10 dimensions d'analyse du Scanner (Module 1). Contexte pour comprendre pourquoi les stratégies donnent ce signal.">
          <div className="flex justify-center">
            <RadarChart data={criteriaRadar} size={380} />
          </div>
        </InfoCard>
      )}

      {/* ═══ 6. CARTES DES 10 CRITÈRES ═══ */}
      {Object.keys(scores).length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-1 flex items-center gap-2"><Sparkles size={18} /> Les 10 critères — {data.symbol}</h3>
          <p className="text-xs text-text-secondary mb-4">Contexte Scanner (Module 1). Triés par score décroissant. Cliquez pour voir la description détaillée.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {criteriaEntries.map(([key, config]) => {
              const score = scores[key] ?? 50;
              const isExpanded = expandedCriterion === key;
              return (
                <button key={key} onClick={() => setExpandedCriterion(isExpanded ? null : key)}
                  className={`text-left bg-card rounded-xl border p-5 transition-all ${isExpanded ? "border-gold bg-gold/5 ring-1 ring-gold/30" : "border-border hover:border-gold/20"}`}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{config.icon}</span>
                      <span className="text-sm font-semibold">{config.label}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 mb-3">
                    <ScoreGauge score={score} size={70} />
                    <div className="flex-1">
                      <p className="text-[10px] text-text-secondary">Score sur 100</p>
                    </div>
                  </div>
                  <p className="text-[11px] text-text-secondary leading-relaxed">
                    {score >= 75 ? `Score élevé — ce critère contribue fortement au signal positif.`
                      : score >= 60 ? `Score correct — contribution modérée au signal global.`
                      : score >= 40 ? `Score moyen — ce critère est neutre, ni positif ni négatif.`
                      : `Score faible — ce critère tire le signal vers le bas.`}
                  </p>
                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-border/50">
                      <p className="text-[11px] text-text-secondary">{config.description}</p>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* ═══ Lien vers analyse complète ═══ */}
      <a href={`/asset/${data.symbol}`} className="block bg-card border border-gold/30 rounded-xl p-4 text-center hover:bg-gold/5 transition-colors">
        <p className="text-gold font-semibold text-sm">Voir l'analyse complète dans Scanner →</p>
        <p className="text-[10px] text-text-secondary mt-1">Breakdowns détaillés, backtest, fondamentaux — actifs du pipeline uniquement</p>
      </a>

      {/* ═══ BOUTON PARTAGER ═══ */}
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

