import { useEffect, useState } from "react";
import { Lightbulb, Plus, Trash2, Eye, X } from "lucide-react";
import axios from "axios";
import InfoCard from "../components/ui/InfoCard";

const THEMES = [
  { value: "PETROLE", label: "Pétrole / Énergie" },
  { value: "OR", label: "Or / Métaux précieux" },
  { value: "TECH", label: "Tech / Croissance" },
  { value: "IA", label: "Intelligence Artificielle" },
  { value: "BITCOIN", label: "Bitcoin / Crypto" },
  { value: "RECESSION", label: "Récession" },
  { value: "INFLATION", label: "Inflation" },
  { value: "TAUX", label: "Hausse des taux" },
  { value: "GUERRE", label: "Conflit géopolitique" },
  { value: "PHARMA", label: "Pharma / Santé" },
  { value: "LUXE", label: "Luxe européen" },
];

const DIRECTIONS = [
  { value: "HAUSSE", label: "Va monter", color: "text-gold" },
  { value: "BAISSE", label: "Va baisser", color: "text-red-400" },
];

const CONVICTIONS = [
  { value: "FAIBLE", label: "Faible (25%)", color: "text-text-secondary" },
  { value: "MOYENNE", label: "Moyenne (50%)", color: "text-yellow-400" },
  { value: "FORTE", label: "Forte (75%)", color: "text-gold" },
  { value: "CERTAINE", label: "Certaine (90%)", color: "text-gold font-bold" },
];

export default function Theses() {
  const [theses, setTheses] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [plan, setPlan] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Form state
  const [theme, setTheme] = useState("PETROLE");
  const [customTheme, setCustomTheme] = useState("");
  const [direction, setDirection] = useState("HAUSSE");
  const [conviction, setConviction] = useState("MOYENNE");
  const [reason, setReason] = useState("");
  const [horizon, setHorizon] = useState(30);

  const loadTheses = () => {
    axios.get("/api/analyser/theses").then((res) => setTheses(res.data)).catch(() => {});
  };

  useEffect(() => { loadTheses(); }, []);

  const handleCreate = () => {
    setLoading(true);
    axios.post("/api/analyser/thesis", {
      theme: customTheme || theme,
      direction, conviction, reason,
      horizon_days: horizon,
    })
      .then(() => { loadTheses(); setShowForm(false); setReason(""); setCustomTheme(""); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  const handleDelete = (id: string) => {
    axios.delete(`/api/analyser/thesis/${id}`).then(() => loadTheses());
  };

  const handleViewPlan = (id: string) => {
    setPlan(null);
    axios.get(`/api/analyser/thesis/${id}/plan`).then((res) => setPlan(res.data));
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">Mes Thèses</h2>
          <p className="text-text-secondary text-sm mt-1">
            Vos convictions personnelles intégrées au modèle. Sans thèse, le système fonctionne normalement.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-gold/10 text-gold border border-gold/20 rounded-xl text-sm font-semibold hover:bg-gold/20 transition-colors"
        >
          {showForm ? <X size={16} /> : <Plus size={16} />}
          {showForm ? "Annuler" : "Nouvelle thèse"}
        </button>
      </div>

      {/* Formulaire */}
      {showForm && (
        <div className="bg-card border border-border rounded-2xl p-6 mb-6 space-y-4">
          <h3 className="font-semibold">Créer une thèse</h3>

          {/* Thème */}
          <div>
            <label className="text-xs text-text-secondary mb-1.5 block">Thème ou actif</label>
            <div className="flex gap-2">
              <select
                value={theme}
                onChange={(e) => { setTheme(e.target.value); setCustomTheme(""); }}
                className="flex-1 bg-surface border border-border rounded-lg px-3 py-2 text-sm"
              >
                {THEMES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
                <option value="CUSTOM">Symbole personnalisé...</option>
              </select>
              {theme === "CUSTOM" && (
                <input
                  type="text"
                  value={customTheme}
                  onChange={(e) => setCustomTheme(e.target.value)}
                  placeholder="AAPL, NVDA, BTC-USD..."
                  className="flex-1 bg-surface border border-border rounded-lg px-3 py-2 text-sm font-mono"
                />
              )}
            </div>
          </div>

          {/* Direction + Conviction */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-text-secondary mb-1.5 block">Direction</label>
              <div className="flex gap-2">
                {DIRECTIONS.map((d) => (
                  <button
                    key={d.value}
                    onClick={() => setDirection(d.value)}
                    className={`flex-1 py-2 text-sm rounded-lg border transition-colors ${
                      direction === d.value
                        ? d.value === "HAUSSE" ? "bg-gold/10 text-gold border-gold/20" : "bg-red-400/10 text-red-400 border-red-400/20"
                        : "border-border text-text-secondary"
                    }`}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-xs text-text-secondary mb-1.5 block">Conviction</label>
              <select
                value={conviction}
                onChange={(e) => setConviction(e.target.value)}
                className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm"
              >
                {CONVICTIONS.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Raison + Horizon */}
          <div>
            <label className="text-xs text-text-secondary mb-1.5 block">Raison (optionnel)</label>
            <input
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Ex: Guerre en Iran, embargo OPEP, résultats Q3..."
              className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm"
            />
          </div>

          <div className="flex items-center gap-4">
            <div>
              <label className="text-xs text-text-secondary mb-1.5 block">Horizon</label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={horizon}
                  onChange={(e) => setHorizon(Number(e.target.value))}
                  className="w-20 bg-surface border border-border rounded-lg px-3 py-2 text-sm font-mono"
                />
                <span className="text-xs text-text-secondary">jours</span>
              </div>
            </div>
            <button
              onClick={handleCreate}
              disabled={loading}
              className="mt-5 px-6 py-2 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm font-semibold hover:bg-gold/20 disabled:opacity-50"
            >
              {loading ? "Création..." : "Créer la thèse"}
            </button>
          </div>
        </div>
      )}

      {/* Liste des thèses actives */}
      {theses.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-8 text-center">
          <Lightbulb size={32} className="mx-auto text-text-secondary mb-3" />
          <p className="text-text-secondary">Aucune thèse active</p>
          <p className="text-xs text-text-secondary mt-1">
            Le système fonctionne normalement avec ses algorithmes. Ajoutez une thèse pour influencer les scores selon vos convictions.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {theses.map((t) => (
            <div key={t.id} className="bg-card border border-border rounded-xl p-5">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-lg font-bold">{t.theme}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-lg border font-semibold ${
                      t.direction === "HAUSSE" ? "text-gold bg-gold/10 border-gold/20" : "text-red-400 bg-red-400/10 border-red-400/20"
                    }`}>{t.direction}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-lg bg-surface border border-border ${
                      t.conviction === "CERTAINE" ? "text-gold font-bold" : t.conviction === "FORTE" ? "text-gold" : "text-text-secondary"
                    }`}>{t.conviction}</span>
                  </div>
                  {t.reason && <p className="text-sm text-text-secondary">{t.reason}</p>}
                  <p className="text-xs text-text-secondary mt-1">{t.description}</p>
                  <div className="flex gap-4 mt-2 text-[10px] text-text-secondary">
                    <span>Horizon : {t.horizon_days}j</span>
                    <span>Expire : {t.expires_at}</span>
                    <span>Long : {t.symbols_long?.join(", ")}</span>
                    {t.symbols_short?.length > 0 && <span>Short : {t.symbols_short.join(", ")}</span>}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleViewPlan(t.id)}
                    className="p-2 text-text-secondary hover:text-gold transition-colors"
                    title="Voir le plan de trade"
                  >
                    <Eye size={16} />
                  </button>
                  <button
                    onClick={() => handleDelete(t.id)}
                    className="p-2 text-text-secondary hover:text-red-400 transition-colors"
                    title="Supprimer"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Plan de trade */}
      {plan && !plan.error && (
        <div className="mt-6">
          <InfoCard
            title={`Plan de trade — ${plan.thesis.theme} ${plan.thesis.direction}`}
            icon={<Lightbulb size={18} />}
            description={`Ce plan est généré automatiquement selon votre thèse. ${plan.total_positions} positions, ${plan.total_sizing_pct}% du capital total.`}
          >
            {plan.plan_long.length > 0 && (
              <>
                <h4 className="text-xs text-gold font-semibold mb-2">ACHETER ({plan.plan_long.length})</h4>
                <div className="space-y-2 mb-4">
                  {plan.plan_long.map((p: any) => (
                    <div key={p.symbol} className="flex items-center justify-between bg-surface rounded-lg p-3">
                      <div>
                        <span className="font-mono font-semibold">{p.symbol}</span>
                        <span className="text-xs text-text-secondary ml-2">{p.name}</span>
                      </div>
                      <div className="flex items-center gap-4 text-xs">
                        <span>Entry ${p.price}</span>
                        <span className="text-red-400">SL ${p.stop_loss}</span>
                        <span className="text-gold">TP ${p.take_profit}</span>
                        <span className="text-text-secondary">{p.sizing_pct}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
            {plan.plan_short.length > 0 && (
              <>
                <h4 className="text-xs text-red-400 font-semibold mb-2">SHORTER ({plan.plan_short.length})</h4>
                <div className="space-y-2">
                  {plan.plan_short.map((p: any) => (
                    <div key={p.symbol} className="flex items-center justify-between bg-surface rounded-lg p-3">
                      <div>
                        <span className="font-mono font-semibold">{p.symbol}</span>
                        <span className="text-xs text-text-secondary ml-2">{p.name}</span>
                      </div>
                      <div className="flex items-center gap-4 text-xs">
                        <span>Entry ${p.price}</span>
                        <span className="text-red-400">SL ${p.stop_loss}</span>
                        <span className="text-gold">TP ${p.take_profit}</span>
                        <span className="text-text-secondary">{p.sizing_pct}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </InfoCard>
        </div>
      )}
    </div>
  );
}
