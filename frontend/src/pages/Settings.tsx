import { useState, useEffect } from "react";
import { Palette, Monitor, Moon, Sun, Sparkles, Leaf, Gem } from "lucide-react";

const THEMES = [
  {
    id: "dark-gold",
    name: "Dark Gold",
    icon: <Sparkles size={16} />,
    description: "Thème signature — noir profond et accents dorés",
    preview: { bg: "#000000", card: "#0A0A0A", accent: "#D4AF37", text: "#fff" },
  },
  {
    id: "dark-blue",
    name: "Ocean Blue",
    icon: <Moon size={16} />,
    description: "Bleu profond — style Bloomberg Terminal",
    preview: { bg: "#0B1120", card: "#111827", accent: "#3B82F6", text: "#F1F5F9" },
  },
  {
    id: "dark-emerald",
    name: "Matrix Green",
    icon: <Leaf size={16} />,
    description: "Vert émeraude — style trading desk",
    preview: { bg: "#021A0A", card: "#062E16", accent: "#10B981", text: "#ECFDF5" },
  },
  {
    id: "dark-purple",
    name: "Crypto Purple",
    icon: <Gem size={16} />,
    description: "Violet néon — style DeFi / Web3",
    preview: { bg: "#0C0014", card: "#1A0033", accent: "#A855F7", text: "#FAF5FF" },
  },
  {
    id: "light",
    name: "Light Mode",
    icon: <Sun size={16} />,
    description: "Thème clair — accents dorés sur fond blanc",
    preview: { bg: "#F8F9FA", card: "#FFFFFF", accent: "#D4AF37", text: "#212529" },
  },
];

function applyTheme(themeId: string) {
  document.documentElement.setAttribute("data-theme", themeId);
  localStorage.setItem("tradepilot_theme", themeId);
}

export default function Settings() {
  const [currentTheme, setCurrentTheme] = useState(
    localStorage.getItem("tradepilot_theme") || "dark-gold"
  );

  useEffect(() => {
    applyTheme(currentTheme);
  }, [currentTheme]);

  const selectTheme = (id: string) => {
    setCurrentTheme(id);
    applyTheme(id);
  };

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Paramètres</h2>

      <div className="space-y-6">
        {/* Thème */}
        <section className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Palette size={18} className="text-gold" />
            <h3 className="text-sm font-semibold">Thème de couleur</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {THEMES.map((theme) => (
              <button
                key={theme.id}
                onClick={() => selectTheme(theme.id)}
                className={`flex items-start gap-3 p-4 rounded-xl border transition-all text-left ${
                  currentTheme === theme.id
                    ? "border-gold bg-gold/5 ring-1 ring-gold/30"
                    : "border-border hover:border-gold/30 hover:bg-surface"
                }`}
              >
                {/* Preview */}
                <div
                  className="w-12 h-12 rounded-lg flex-shrink-0 flex items-center justify-center border"
                  style={{
                    background: theme.preview.bg,
                    borderColor: theme.preview.accent + "40",
                  }}
                >
                  <div
                    className="w-6 h-6 rounded-md"
                    style={{
                      background: theme.preview.card,
                      border: `2px solid ${theme.preview.accent}`,
                    }}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span style={{ color: theme.preview.accent }}>{theme.icon}</span>
                    <p className="text-sm font-semibold">{theme.name}</p>
                    {currentTheme === theme.id && (
                      <span className="text-[9px] px-1.5 py-0.5 bg-gold/10 text-gold border border-gold/20 rounded font-semibold">
                        ACTIF
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-text-secondary mt-0.5">{theme.description}</p>
                </div>
              </button>
            ))}
          </div>
        </section>

        {/* APIs */}
        <section className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Monitor size={18} className="text-gold" />
            <h3 className="text-sm font-semibold">APIs & Brokers</h3>
          </div>
          <div className="space-y-3">
            {[
              { name: "Alpaca (Paper Trading)", status: "configured" },
              { name: "Interactive Brokers (IBKR)", status: "configured" },
              { name: "FRED (Données Macro)", status: "optional" },
              { name: "Reddit (Sentiment)", status: "optional" },
              { name: "NewsAPI (Actualités)", status: "optional" },
            ].map((api) => (
              <div key={api.name} className="flex items-center justify-between">
                <span className="text-sm">{api.name}</span>
                <span className={`text-xs px-2 py-1 rounded font-medium ${
                  api.status === "configured"
                    ? "bg-gold/10 text-gold border border-gold/20"
                    : "bg-surface text-text-secondary border border-border"
                }`}>
                  {api.status === "configured" ? "Configuré" : "Optionnel"}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Pipeline */}
        <section className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-semibold mb-4">Pipeline</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm">Mode</span>
              <span className="text-xs text-gold px-2 py-1 bg-gold/10 border border-gold/20 rounded font-semibold">
                DUAL (IBKR + Alpaca)
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Actifs</span>
              <span className="text-xs text-text-secondary">500 actifs (6 classes)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Pipeline nocturne</span>
              <span className="text-xs text-text-secondary">22h00 UTC (minuit Paris)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">TP/SL Monitor</span>
              <span className="text-xs text-text-secondary">Toutes les 5 minutes</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
