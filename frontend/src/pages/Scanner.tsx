import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { scannerApi, type ScanResult } from "../services/api";

export default function Scanner() {
  const [results, setResults] = useState<ScanResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<ScanResult | null>(null);

  useEffect(() => {
    scannerApi
      .scan()
      .then((res) => setResults(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Scanner de Marché</h2>
      <p className="text-text-secondary mb-6">
        Filtrage des actifs selon 9 critères orthogonaux — Phase 1 : Analyse Technique + Corrélation
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Liste des résultats */}
        <div className="lg:col-span-2">
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-sm font-medium text-text-secondary mb-4">
              Résultats du scan ({results.length} actifs)
            </h3>
            {loading ? (
              <p className="text-text-secondary text-sm">Scan en cours...</p>
            ) : (
              <div className="space-y-2">
                {results.map((r) => (
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
                    <div className="flex items-center gap-4">
                      <span className="text-xs text-text-secondary px-2 py-0.5 bg-surface rounded">
                        {r.asset_class}
                      </span>
                      <span className="font-mono font-semibold w-12 text-right">
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

              <div className="space-y-3">
                <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Scores
                </h4>
                <ScoreBar label="Analyse Technique" score={selected.scores.technical} />
                <ScoreBar label="Corrélation" score={selected.scores.correlation} />
                <div className="pt-2 border-t border-border">
                  <ScoreBar label="Score Final" score={selected.scores.final} highlight />
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Critères Phase 2
                </h4>
                {[
                  "Sentiment",
                  "Génome Explosif",
                  "Capital Institutionnel",
                  "Vélocité Fondamentale",
                  "Macro Tailwind",
                  "Topologie Sociale",
                  "Unicité du Signal",
                ].map((c) => (
                  <div key={c} className="flex items-center justify-between text-sm">
                    <span className="text-text-secondary">{c}</span>
                    <span className="text-xs text-text-secondary px-2 py-0.5 bg-surface rounded">
                      —
                    </span>
                  </div>
                ))}
              </div>

              <div className="text-xs text-text-secondary">
                {selected.data_points} jours de données
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
