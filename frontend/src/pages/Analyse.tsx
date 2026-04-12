import { useState } from "react";
import { Search, TrendingUp, TrendingDown, Minus } from "lucide-react";
import axios from "axios";
import TradingChart from "../components/TradingChart";
import ScoreGauge from "../components/ui/ScoreGauge";
import InfoCard from "../components/ui/InfoCard";
import SignalBadge from "../components/ui/SignalBadge";

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
};

export default function Analyse() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = (q?: string) => {
    const searchQuery = q || query;
    if (!searchQuery.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);

    axios
      .get(`/api/scanner/analyse?q=${encodeURIComponent(searchQuery)}`)
      .then((res) => {
        if (res.data.error) {
          setError(res.data.error);
        } else {
          setResult(res.data);
        }
      })
      .catch((err) => setError(err.response?.data?.detail || "Erreur de connexion"))
      .finally(() => setLoading(false));
  };

  return (
    <div className="max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold mb-2">Analyse rapide</h2>
      <p className="text-text-secondary text-sm mb-6">
        Tapez n'importe quel actif — analyse complète en quelques secondes
      </p>

      {/* Barre de recherche */}
      <div className="flex gap-3 mb-4">
        <div className="flex-1 relative">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-secondary" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="AAPL, S&P 500, BITCOIN, CAC 40, PLTR, AMC..."
            className="w-full bg-card border border-border rounded-xl pl-10 pr-4 py-3 text-sm font-mono focus:outline-none focus:border-gold/50 transition-colors"
          />
        </div>
        <button
          onClick={() => handleSearch()}
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
          <p className="text-xs text-text-secondary">{data.data_points} jours de données</p>
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
              <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                <div><span className="text-text-secondary">Entry</span><p className="font-mono">${best.entry}</p></div>
                <div><span className="text-text-secondary">SL</span><p className="font-mono text-red-400">${best.stop_loss}</p></div>
                <div><span className="text-text-secondary">TP</span><p className="font-mono text-gold">${best.take_profit}</p></div>
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

      {/* Graphique */}
      {data.ohlcv?.length > 0 && (
        <InfoCard title="Graphique" icon={<TrendingUp size={18} />} description="100 derniers jours de prix avec moyennes mobiles.">
          <TradingChart data={data.ohlcv} height={400} />
        </InfoCard>
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

      {/* Toutes les stratégies */}
      {data.all_strategies?.length > 0 && (
        <InfoCard title="Toutes les stratégies" icon={<TrendingUp size={18} />} description="Chaque stratégie donne son avis : LONG (acheter), SHORT (vendre) ou NEUTRAL (rien faire).">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {data.all_strategies.map((s: any) => (
              <div key={s.strategy} className={`bg-surface rounded-xl p-3 flex items-center justify-between ${s.strategy === best.name ? "border border-gold/20" : ""}`}>
                <div>
                  <p className="text-sm font-semibold">{STRATEGY_LABELS[s.strategy] || s.strategy}</p>
                  {s.strategy === best.name && <p className="text-[10px] text-gold">Recommandée</p>}
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
            ))}
          </div>
        </InfoCard>
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
