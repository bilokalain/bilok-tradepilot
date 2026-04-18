import { useState } from "react";
import { Search, TrendingUp, TrendingDown, Shield, Zap } from "lucide-react";
import api from "../services/api";
import InfoCard from "../components/ui/InfoCard";

const SUGGESTIONS = [
  { label: "Pétrole (Oil)", symbol: "CL=F" },
  { label: "Or (Gold)", symbol: "GC=F" },
  { label: "Bitcoin", symbol: "BTC-USD" },
  { label: "NVIDIA", symbol: "NVDA" },
  { label: "S&P 500", symbol: "SPY" },
  { label: "EUR/USD", symbol: "EURUSD=X" },
  { label: "Argent", symbol: "SI=F" },
  { label: "Tesla", symbol: "TSLA" },
  { label: "Apple", symbol: "AAPL" },
  { label: "Gaz Naturel", symbol: "NG=F" },
];

export default function Correlation() {
  const [symbol, setSymbol] = useState("");
  const [movePct, setMovePct] = useState(10);
  const [corrData, setCorrData] = useState<any>(null);
  const [impactData, setImpactData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = (sym?: string) => {
    const s = sym || symbol;
    if (!s.trim()) return;
    setLoading(true);
    setError("");
    setCorrData(null);
    setImpactData(null);

    Promise.all([
      api.get(`/scanner/correlation-map?q=${encodeURIComponent(s)}&lookback=120`),
      api.get(`/scanner/impact-simulation?q=${encodeURIComponent(s)}&move_pct=${movePct}`),
    ])
      .then(([corrRes, impactRes]) => {
        if (corrRes.data.error) setError(corrRes.data.error);
        else setCorrData(corrRes.data);
        if (!impactRes.data.error) setImpactData(impactRes.data);
      })
      .catch((err) => setError(err.response?.data?.detail || "Erreur"))
      .finally(() => setLoading(false));
  };

  return (
    <div className="max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold mb-2">Corrélation rapide</h2>
      <p className="text-text-secondary text-sm mb-6 max-w-3xl">
        Matrice de corrélation multi-temporelle — analyse les co-mouvements entre actifs sur 5 horizons (jour, semaine, mois, trimestre, année). Détecte les ruptures de corrélation et les décrochages sectoriels qui signalent des opportunités de trading.
      </p>

      {/* Recherche */}
      <div className="flex gap-3 mb-4">
        <div className="flex-1 relative">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-secondary" />
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="CL=F (pétrole), GC=F (or), BTC-USD, NVDA, SPY..."
            className="w-full bg-card border border-border rounded-xl pl-10 pr-4 py-3 text-sm font-mono focus:outline-none focus:border-gold/50"
          />
        </div>
        <div className="flex items-center gap-2 bg-card border border-border rounded-xl px-3">
          <span className="text-xs text-text-secondary">Choc :</span>
          <input
            type="number"
            value={movePct}
            onChange={(e) => setMovePct(Number(e.target.value))}
            className="w-16 bg-transparent text-sm font-mono text-center focus:outline-none"
          />
          <span className="text-xs text-text-secondary">%</span>
        </div>
        <button
          onClick={() => handleSearch()}
          disabled={loading}
          className="px-6 py-3 bg-gold/10 text-gold border border-gold/20 rounded-xl text-sm font-semibold hover:bg-gold/20 transition-colors disabled:opacity-50"
        >
          {loading ? "Analyse..." : "Chercher"}
        </button>
      </div>

      {/* Suggestions */}
      <div className="flex flex-wrap gap-2 mb-6">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.symbol}
            onClick={() => { setSymbol(s.symbol); handleSearch(s.symbol); }}
            className="px-3 py-1 text-xs bg-surface border border-border rounded-lg text-text-secondary hover:text-gold hover:border-gold/20 transition-colors"
          >
            {s.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="p-4 bg-red-400/10 border border-red-400/20 rounded-xl text-sm text-red-400 mb-6">{error}</div>
      )}

      {loading && (
        <div className="flex items-center justify-center h-40">
          <div className="w-10 h-10 rounded-full border-2 border-transparent border-t-gold animate-spin" />
        </div>
      )}

      {corrData && (
        <>
          {/* Header cible */}
          <div className="bg-card border border-border rounded-xl p-5 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold font-mono text-gold">{corrData.target.symbol}</h3>
                <p className="text-text-secondary text-sm">{corrData.target.name}</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-mono font-bold">${corrData.target.last_price}</p>
                <p className="text-xs text-text-secondary">{corrData.total_compared} actifs comparés sur {corrData.lookback_days} jours</p>
              </div>
            </div>
            <div className="flex gap-4 mt-3 text-xs">
              <span className="text-gold">{corrData.num_positive} corrélés positivement</span>
              <span className="text-red-400">{corrData.num_negative} corrélés négativement</span>
              <span className="text-text-secondary">{corrData.num_neutral} neutres</span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Corrélations positives */}
            <InfoCard
              title={`Bougent AVEC ${corrData.target.symbol} (${corrData.num_positive})`}
              icon={<TrendingUp size={18} />}
              description={`Ces actifs ont tendance à monter quand ${corrData.target.symbol} monte, et à baisser quand il baisse. Plus la corrélation est proche de 1.0, plus le lien est fort.`}
            >
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {corrData.positive_correlated.map((c: any) => (
                  <CorrRow key={c.symbol} data={c} type="positive" />
                ))}
                {corrData.positive_correlated.length === 0 && (
                  <p className="text-text-secondary text-sm py-4">Aucun actif fortement corrélé positivement</p>
                )}
              </div>
            </InfoCard>

            {/* Corrélations négatives */}
            <InfoCard
              title={`Bougent CONTRE ${corrData.target.symbol} (${corrData.num_negative})`}
              icon={<Shield size={18} />}
              description={`Ces actifs bougent dans le sens inverse. Si ${corrData.target.symbol} monte, ils ont tendance à baisser. Utile pour se couvrir (hedge).`}
            >
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {corrData.negative_correlated.map((c: any) => (
                  <CorrRow key={c.symbol} data={c} type="negative" />
                ))}
                {corrData.negative_correlated.length === 0 && (
                  <p className="text-text-secondary text-sm py-4">Aucun actif fortement corrélé négativement</p>
                )}
              </div>
            </InfoCard>
          </div>
        </>
      )}

      {/* Simulation d'impact */}
      {impactData && !impactData.error && (
        <InfoCard
          title={`Simulation : ${impactData.scenario}`}
          icon={<Zap size={18} />}
          description={`Si ${impactData.target.symbol} fait ${impactData.move_pct > 0 ? '+' : ''}${impactData.move_pct}%, voici l'impact estimé sur les actifs corrélés. Le calcul utilise le beta de corrélation (sensibilité historique).`}
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <div className="bg-surface rounded-xl p-3 text-center">
              <p className="text-2xl font-mono font-bold text-gold">{impactData.summary.actifs_qui_montent}</p>
              <p className="text-xs text-text-secondary">Bénéficient</p>
            </div>
            <div className="bg-surface rounded-xl p-3 text-center">
              <p className="text-2xl font-mono font-bold text-red-400">{impactData.summary.actifs_qui_baissent}</p>
              <p className="text-xs text-text-secondary">Souffrent</p>
            </div>
            {impactData.summary.plus_gros_impact_positif && (
              <div className="bg-surface rounded-xl p-3 text-center">
                <p className="text-sm font-mono font-bold text-gold">{impactData.summary.plus_gros_impact_positif.symbol}</p>
                <p className="text-xs text-gold">+{impactData.summary.plus_gros_impact_positif.expected_move_pct}%</p>
              </div>
            )}
            {impactData.summary.plus_gros_impact_negatif && (
              <div className="bg-surface rounded-xl p-3 text-center">
                <p className="text-sm font-mono font-bold text-red-400">{impactData.summary.plus_gros_impact_negatif.symbol}</p>
                <p className="text-xs text-red-400">{impactData.summary.plus_gros_impact_negatif.expected_move_pct}%</p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Bénéficiaires */}
            {impactData.beneficiaires.length > 0 && (
              <div>
                <h4 className="text-xs text-gold font-semibold mb-2">BÉNÉFICIENT ({impactData.beneficiaires.length})</h4>
                <div className="space-y-1.5">
                  {impactData.beneficiaires.slice(0, 15).map((i: any) => (
                    <ImpactRow key={i.symbol} data={i} positive />
                  ))}
                </div>
              </div>
            )}

            {/* Victimes */}
            {impactData.victimes.length > 0 && (
              <div>
                <h4 className="text-xs text-red-400 font-semibold mb-2">SOUFFRENT ({impactData.victimes.length})</h4>
                <div className="space-y-1.5">
                  {impactData.victimes.slice(0, 15).map((i: any) => (
                    <ImpactRow key={i.symbol} data={i} />
                  ))}
                </div>
              </div>
            )}
          </div>
        </InfoCard>
      )}
    </div>
  );
}

function CorrRow({ data, type }: { data: any; type: "positive" | "negative" }) {
  const color = type === "positive" ? "text-gold" : "text-red-400";
  const barColor = type === "positive" ? "bg-gold" : "bg-red-400";
  const width = Math.abs(data.correlation) * 100;

  return (
    <div className="bg-surface rounded-lg p-2.5 flex items-center gap-3">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-mono font-semibold text-sm">{data.symbol}</span>
          <span className="text-[10px] px-1.5 py-0.5 bg-background rounded">{data.asset_class}</span>
        </div>
        <p className="text-[10px] text-text-secondary truncate">{data.name}</p>
      </div>
      <div className="w-20">
        <div className="h-1.5 bg-background rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${barColor}`} style={{ width: `${width}%` }} />
        </div>
      </div>
      <div className="text-right w-16">
        <span className={`text-sm font-mono font-bold ${color}`}>{data.correlation > 0 ? '+' : ''}{data.correlation}</span>
        <p className="text-[9px] text-text-secondary">beta {data.beta}</p>
      </div>
    </div>
  );
}

function ImpactRow({ data, positive }: { data: any; positive?: boolean }) {
  return (
    <div className="flex items-center justify-between bg-surface rounded-lg p-2 text-xs">
      <div className="flex items-center gap-2">
        <span className="font-mono font-semibold">{data.symbol}</span>
        <span className="text-text-secondary">${data.current_price}</span>
      </div>
      <div className="text-right">
        <span className={`font-mono font-bold ${positive ? "text-gold" : "text-red-400"}`}>
          {data.expected_move_pct > 0 ? '+' : ''}{data.expected_move_pct}%
        </span>
        <span className="text-text-secondary ml-2">→ ${data.expected_price}</span>
      </div>
    </div>
  );
}
