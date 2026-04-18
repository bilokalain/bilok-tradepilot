import { useEffect, useState, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Search, Filter, ArrowUpDown } from "lucide-react";
import { scannerApi, type ScanResult } from "../services/api";

const MARKET_FILTERS = [
  { key: "all", label: "Tous", count: 0 },
  { key: "ACTION_US", label: "Actions US", count: 0 },
  { key: "ACTION_EU", label: "Actions EU", count: 0 },
  { key: "ETF", label: "ETF", count: 0 },
  { key: "CRYPTO", label: "Crypto", count: 0 },
  { key: "FOREX", label: "Forex", count: 0 },
  { key: "COMMODITY", label: "Matières 1ères", count: 0 },
];

const SCORE_FILTERS = [
  { key: "all", label: "Tous" },
  { key: "go", label: "GO (≥65)" },
  { key: "wait", label: "WAIT (50-65)" },
  { key: "no", label: "NO (<50)" },
];

const SORT_OPTIONS = [
  { key: "score_desc", label: "Score ↓" },
  { key: "score_asc", label: "Score ↑" },
  { key: "name_asc", label: "Nom A→Z" },
  { key: "name_desc", label: "Nom Z→A" },
];

export default function Scanner() {
  const [results, setResults] = useState<ScanResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<ScanResult | null>(null);
  const [expandedCriterion, setExpandedCriterion] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [marketFilter, setMarketFilter] = useState("all");
  const [scoreFilter, setScoreFilter] = useState("all");
  const [sortBy, setSortBy] = useState("score_desc");
  const navigate = useNavigate();

  // Compteurs par marché
  const marketCounts = useMemo(() => {
    const counts: Record<string, number> = { all: results.length };
    results.forEach((r) => { counts[r.asset_class] = (counts[r.asset_class] || 0) + 1; });
    return counts;
  }, [results]);

  // Filtrage + tri
  const filteredResults = useMemo(() => {
    let filtered = results;

    // Recherche texte
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter((r) =>
        r.symbol.toLowerCase().includes(q) ||
        r.name.toLowerCase().includes(q)
      );
    }

    // Filtre marché
    if (marketFilter !== "all") {
      filtered = filtered.filter((r) => r.asset_class === marketFilter);
    }

    // Filtre score
    if (scoreFilter === "go") filtered = filtered.filter((r) => r.scores.final >= 65);
    else if (scoreFilter === "wait") filtered = filtered.filter((r) => r.scores.final >= 50 && r.scores.final < 65);
    else if (scoreFilter === "no") filtered = filtered.filter((r) => r.scores.final < 50);

    // Tri
    const sorted = [...filtered];
    if (sortBy === "score_desc") sorted.sort((a, b) => b.scores.final - a.scores.final);
    else if (sortBy === "score_asc") sorted.sort((a, b) => a.scores.final - b.scores.final);
    else if (sortBy === "name_asc") sorted.sort((a, b) => a.symbol.localeCompare(b.symbol));
    else if (sortBy === "name_desc") sorted.sort((a, b) => b.symbol.localeCompare(a.symbol));

    return sorted;
  }, [results, searchQuery, marketFilter, scoreFilter, sortBy]);

  useEffect(() => {
    scannerApi
      .scan()
      .then((res) => setResults(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Scanner de Marché</h2>
      <p className="text-text-secondary text-sm mb-6 max-w-3xl">
        Filtrage systématique de 335 actifs selon 10 critères orthogonaux — Analyse Technique, Corrélation, Sentiment, Génome Explosif, Capital Institutionnel, Vélocité Fondamentale, Macro Tailwind, Topologie Sociale, Unicité du Signal et Analyse Fondamentale. Les poids s'adaptent automatiquement au régime de marché, à la classe d'actif et à l'horizon de trading.
      </p>

      {/* Barre de recherche + filtres */}
      <div className="space-y-3 mb-6">
        {/* Recherche */}
        <div className="relative">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-secondary" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Rechercher un symbole ou un nom..."
            className="w-full bg-card border border-border rounded-xl pl-10 pr-4 py-2.5 text-sm font-mono focus:outline-none focus:border-gold/50 transition-colors"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary text-xs">✕</button>
          )}
        </div>

        {/* Filtres marché */}
        <div className="flex flex-wrap gap-2">
          {MARKET_FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setMarketFilter(f.key)}
              className={`text-[11px] px-3 py-1.5 rounded-lg border font-semibold transition-colors ${
                marketFilter === f.key
                  ? "text-gold bg-gold/10 border-gold/20"
                  : "text-text-secondary border-border hover:text-text-primary hover:border-border"
              }`}
            >
              {f.label}
              <span className="ml-1.5 text-[10px] opacity-60">{marketCounts[f.key] || 0}</span>
            </button>
          ))}

          {/* Séparateur */}
          <div className="w-px bg-border mx-1" />

          {/* Filtres score */}
          {SCORE_FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setScoreFilter(f.key)}
              className={`text-[11px] px-3 py-1.5 rounded-lg border font-semibold transition-colors ${
                scoreFilter === f.key
                  ? f.key === "go" ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/20"
                  : f.key === "wait" ? "text-yellow-400 bg-yellow-400/10 border-yellow-400/20"
                  : f.key === "no" ? "text-red-400 bg-red-400/10 border-red-400/20"
                  : "text-gold bg-gold/10 border-gold/20"
                  : "text-text-secondary border-border hover:text-text-primary"
              }`}
            >
              {f.label}
            </button>
          ))}

          {/* Séparateur */}
          <div className="w-px bg-border mx-1" />

          {/* Tri */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="text-[11px] px-2 py-1.5 rounded-lg border border-border bg-card text-text-secondary font-semibold cursor-pointer"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.key} value={o.key}>{o.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Liste des résultats */}
        <div className="lg:col-span-2">
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-sm font-medium text-text-secondary mb-4">
              {filteredResults.length} actifs{searchQuery || marketFilter !== "all" || scoreFilter !== "all" ? ` (filtré sur ${results.length})` : ""}
            </h3>
            {loading ? (
              <p className="text-text-secondary text-sm">Scan en cours...</p>
            ) : filteredResults.length === 0 ? (
              <p className="text-text-secondary text-sm text-center py-8">Aucun actif ne correspond à vos filtres</p>
            ) : (
              <div className="space-y-1 max-h-[700px] overflow-y-auto">
                {filteredResults.map((r) => (
                  <button
                    key={r.symbol}
                    onClick={() => setSelected(r)}
                    className={`w-full flex items-center justify-between p-3 rounded-lg transition-colors text-left ${
                      selected?.symbol === r.symbol
                        ? "bg-gold/10 border border-gold/20"
                        : "hover:bg-surface border border-transparent"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Link to={`/asset/${r.symbol}`} className="font-mono font-semibold text-gold w-20 hover:underline">
                        {r.symbol}
                    </Link>
                      <span className="text-sm text-text-secondary">{r.name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] text-text-secondary px-1.5 py-0.5 bg-surface rounded border border-border/50">
                        {r.asset_class.replace("ACTION_", "").replace("COMMODITY", "COMMO")}
                      </span>
                      <span className={`font-mono font-bold w-12 text-right ${
                        r.scores.final >= 65 ? "text-emerald-400" : r.scores.final >= 50 ? "text-yellow-400" : "text-red-400"
                      }`}>
                        {r.scores.final.toFixed(1)}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Détail actif sélectionné */}
        <div>
          {selected ? (
            <div className="bg-card border border-border rounded-xl p-6 space-y-6">
              <div>
                <h3 className="text-lg font-bold text-gold">{selected.symbol}</h3>
                <p className="text-sm text-text-secondary">{selected.name}</p>
                <p className="text-2xl font-mono font-semibold mt-2">
                  ${selected.last_close.toFixed(2)}
                </p>
              </div>

              <div className="space-y-2">
                <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider">
                  9 Critères — cliquez pour le détail
                </h4>
                {[
                  { key: "technical", label: "Analyse Technique", desc: "20 indicateurs : SMA, EMA, RSI, MACD, Bollinger, ATR, Stochastique, Volume" },
                  { key: "correlation", label: "Corrélation", desc: "Matrice multi-temporelle (5 horizons). Détecte les décrochages sectoriels" },
                  { key: "sentiment", label: "Sentiment", desc: "FinBERT NLP + Reddit mentions + signal de retournement" },
                  { key: "genome", label: "Génome Explosif", desc: "ADN comportemental : phase de cycle, sismographe, mémoire fractale" },
                  { key: "ipi", label: "Capital Institutionnel", desc: "Dark pools, options flow, short interest, 13F filings" },
                  { key: "ivf", label: "Vélocité Fondamentale", desc: "Accélération CA, expansion marges, révisions analystes" },
                  { key: "mts", label: "Macro Tailwind", desc: "Phase cycle économique, régime taux, DXY, liquidité globale" },
                  { key: "sgi", label: "Topologie Sociale", desc: "Qualité communauté, Network Effect, momentum d'intérêt" },
                  { key: "sus", label: "Unicité du Signal", desc: "Crowding score, novelty, timeframe neglect" },
                  { key: "narrative", label: "Narrative", desc: "Force du récit : volume acceleration, price momentum, structure" },
                ].map(({ key, label, desc }) => {
                  const score = (selected.scores as any)[key] ?? 0;
                  const details = (selected as any).details?.[key];
                  const isExpanded = expandedCriterion === key;
                  return (
                    <div key={key}>
                      <button
                        onClick={() => setExpandedCriterion(isExpanded ? null : key)}
                        className="w-full text-left"
                      >
                        <ScoreBar label={label} score={score} />
                      </button>
                      {isExpanded && (
                        <div className="ml-2 mt-1 mb-2 p-2 bg-surface rounded-lg border border-border/50 text-xs space-y-1">
                          <p className="text-text-secondary">{desc}</p>
                          {details && Object.entries(details).map(([k, v]) => (
                            <div key={k} className="flex justify-between">
                              <span className="text-text-secondary">{k.replace(/_/g, " ")}</span>
                              <span className="font-mono text-text-primary">{typeof v === "number" ? (v as number).toFixed(1) : String(v)}</span>
                            </div>
                          ))}
                          {(key === "technical" || key === "correlation") && (
                            <button
                              onClick={() => navigate(`/asset/${selected.symbol}`)}
                              className="mt-1 w-full text-center text-[10px] px-2 py-1 bg-gold/10 text-gold border border-gold/20 rounded hover:bg-gold/20 transition-colors"
                            >
                              Voir le détail complet →
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
                <div className="pt-2 border-t border-border">
                  <ScoreBar label="Score Final" score={selected.scores.final} highlight />
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-xs text-text-secondary">{selected.data_points} jours de données</span>
                <button
                  onClick={() => navigate(`/asset/${selected.symbol}`)}
                  className="text-xs px-3 py-1.5 bg-gold/10 text-gold border border-gold/20 rounded-lg hover:bg-gold/20 transition-colors"
                >
                  Fiche complète →
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-card border border-border rounded-xl p-6 text-center text-text-secondary text-sm">
              Sélectionnez un actif pour voir le détail
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ScoreBar({
  label,
  score,
  highlight,
}: {
  label: string;
  score: number;
  highlight?: boolean;
}) {
  const color = score >= 70 ? "bg-gold" : score >= 50 ? "bg-text-secondary" : "bg-red-500";

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className={highlight ? "font-semibold" : "text-text-secondary"}>{label}</span>
        <span className={`font-mono ${highlight ? "text-gold font-semibold" : ""}`}>
          {score.toFixed(1)}
        </span>
      </div>
      <div className="h-1.5 bg-surface rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}
