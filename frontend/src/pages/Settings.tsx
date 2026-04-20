import { useState, useEffect } from "react";
import { Palette, Monitor, Moon, Sun, Sparkles, Leaf, Gem, Clock, Shield, TrendingUp, Zap, Bell, Database, Settings2, ChevronDown } from "lucide-react";

// ════════════════════════════════════════════════
// THÈMES
// ════════════════════════════════════════════════

const THEMES = [
  { id: "dark-gold", name: "Dark Gold", icon: <Sparkles size={16} />, description: "Signature — noir + doré", preview: { bg: "#000000", card: "#0A0A0A", accent: "#D4AF37" } },
  { id: "dark-blue", name: "Ocean Blue", icon: <Moon size={16} />, description: "Style Bloomberg", preview: { bg: "#0B1120", card: "#111827", accent: "#3B82F6" } },
  { id: "dark-emerald", name: "Matrix Green", icon: <Leaf size={16} />, description: "Trading desk", preview: { bg: "#021A0A", card: "#062E16", accent: "#10B981" } },
  { id: "dark-purple", name: "Crypto Purple", icon: <Gem size={16} />, description: "Style DeFi", preview: { bg: "#0C0014", card: "#1A0033", accent: "#A855F7" } },
  { id: "light", name: "Light Mode", icon: <Sun size={16} />, description: "Noir sur blanc — élégant et lisible", preview: { bg: "#F5F5F5", card: "#FFFFFF", accent: "#1A1A1A" } },
];

function applyTheme(themeId: string) {
  document.documentElement.setAttribute("data-theme", themeId);
  localStorage.setItem("tradepilot_theme", themeId);
}

// Helper pour paramètres locaux
function useSetting<T>(key: string, defaultValue: T): [T, (v: T) => void] {
  const [value, setValue] = useState<T>(() => {
    const stored = localStorage.getItem(`tp_setting_${key}`);
    return stored ? JSON.parse(stored) : defaultValue;
  });
  const update = (v: T) => {
    setValue(v);
    localStorage.setItem(`tp_setting_${key}`, JSON.stringify(v));
  };
  return [value, update];
}

// ════════════════════════════════════════════════
// PAGE SETTINGS
// ════════════════════════════════════════════════

export default function Settings() {
  const [currentTheme, setCurrentTheme] = useState(localStorage.getItem("tradepilot_theme") || "dark-gold");
  const [openSections, setOpenSections] = useState<Set<string>>(new Set(["theme", "trading", "risk"]));

  // Trading parameters
  const [maxPositions, setMaxPositions] = useSetting("max_positions", 15);
  const [scoreGoThreshold, setScoreGoThreshold] = useSetting("score_go_threshold", 65);
  const [kellyFraction, setKellyFraction] = useSetting("kelly_fraction", 25);
  const [maxPositionPct, setMaxPositionPct] = useSetting("max_position_pct", 15);
  const [minPositionPct, setMinPositionPct] = useSetting("min_position_pct", 5);
  const [slMultiplier, setSlMultiplier] = useSetting("sl_multiplier", 2.0);
  const [tpMultiplier, setTpMultiplier] = useSetting("tp_multiplier", 3.0);

  // Risk parameters
  const [maxDrawdownPct, setMaxDrawdownPct] = useSetting("max_drawdown_pct", 20);
  const [riskBudgetPct, setRiskBudgetPct] = useSetting("risk_budget_pct", 15);
  const [maxCorrelation, setMaxCorrelation] = useSetting("max_correlation", 0.85);
  const [trailingStopAtr, setTrailingStopAtr] = useSetting("trailing_stop_atr", 2.0);
  const [exhaustionThreshold, setExhaustionThreshold] = useSetting("exhaustion_threshold", 35);

  // Notifications
  const [notifEmail, setNotifEmail] = useSetting("notif_email", true);
  const [notifTelegram, setNotifTelegram] = useSetting("notif_telegram", false);
  const [notifSignalGo, setNotifSignalGo] = useSetting("notif_signal_go", true);
  const [notifSlTp, setNotifSlTp] = useSetting("notif_sl_tp", true);
  const [notifWeeklyReport, setNotifWeeklyReport] = useSetting("notif_weekly_report", true);

  // Bias detection
  const [fomoThreshold, setFomoThreshold] = useSetting("fomo_threshold", 25);
  const [revengeCooldown, setRevengeCooldown] = useSetting("revenge_cooldown", 30);
  const [revengeReduction, setRevengeReduction] = useSetting("revenge_reduction", 20);

  // Scanner vetos
  const [vetoMts, setVetoMts] = useSetting("veto_mts", 20);
  const [vetoSus, setVetoSus] = useSetting("veto_sus", 25);
  const [vetoIpi, setVetoIpi] = useSetting("veto_ipi", 20);

  // Scaling
  const [tranche1, setTranche1] = useSetting("tranche_1", 40);
  const [tranche2, setTranche2] = useSetting("tranche_2", 35);
  const [tranche3, setTranche3] = useSetting("tranche_3", 25);

  // Strategy Decay
  const [decayMinTrades, setDecayMinTrades] = useSetting("decay_min_trades", 10);
  const [decayMinWinRate, setDecayMinWinRate] = useSetting("decay_min_winrate", 35);
  const [decayMinPF, setDecayMinPF] = useSetting("decay_min_pf", 0.8);

  // EWS
  const [ewsDrawdownAttention, setEwsDrawdownAttention] = useSetting("ews_dd_attention", 5);
  const [ewsLosingStreak, setEwsLosingStreak] = useSetting("ews_losing_streak", 3);

  // Cache TTLs
  const [scannerCacheTtl, setScannerCacheTtl] = useSetting("scanner_cache_ttl", 6);
  const [correlationCacheTtl, setCorrelationCacheTtl] = useSetting("correlation_cache_ttl", 12);

  useEffect(() => { applyTheme(currentTheme); }, [currentTheme]);

  const toggle = (id: string) => {
    setOpenSections((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold mb-2">Paramètres</h2>
      <p className="text-text-secondary text-sm mb-6">Configuration du système de trading — thème, risk management, exécution, notifications et infrastructure.</p>

      <div className="space-y-4">

        {/* ═══ THÈME ═══ */}
        <SettingsSection id="theme" title="Apparence" icon={<Palette size={18} />} open={openSections.has("theme")} toggle={toggle}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {THEMES.map((theme) => (
              <button
                key={theme.id}
                onClick={() => { setCurrentTheme(theme.id); applyTheme(theme.id); }}
                className={`flex items-center gap-3 p-3 rounded-xl border transition-all text-left ${
                  currentTheme === theme.id ? "border-gold bg-gold/5 ring-1 ring-gold/30" : "border-border hover:border-gold/30"
                }`}
              >
                <div className="w-10 h-10 rounded-lg flex items-center justify-center border" style={{ background: theme.preview.bg, borderColor: theme.preview.accent + "40" }}>
                  <div className="w-5 h-5 rounded" style={{ background: theme.preview.card, border: `2px solid ${theme.preview.accent}` }} />
                </div>
                <div>
                  <p className="text-sm font-semibold flex items-center gap-2">
                    <span style={{ color: theme.preview.accent }}>{theme.icon}</span> {theme.name}
                    {currentTheme === theme.id && <span className="text-[8px] px-1.5 py-0.5 bg-gold/10 text-gold border border-gold/20 rounded font-bold">ACTIF</span>}
                  </p>
                  <p className="text-[10px] text-text-secondary">{theme.description}</p>
                </div>
              </button>
            ))}
          </div>
        </SettingsSection>

        {/* ═══ TRADING ═══ */}
        <SettingsSection id="trading" title="Trading & Exécution" icon={<TrendingUp size={18} />} open={openSections.has("trading")} toggle={toggle}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ParamSlider label="Seuil GO (Score V2)" value={scoreGoThreshold} onChange={setScoreGoThreshold} min={50} max={80} step={1} unit="" explain="Score minimum pour déclencher un signal GO. Plus haut = moins de trades mais meilleure qualité." />
            <ParamSlider label="Positions max simultanées" value={maxPositions} onChange={setMaxPositions} min={5} max={30} step={1} unit="" explain="Nombre maximum de positions ouvertes. Au-delà, les signaux GO vont en file d'attente." />
            <ParamSlider label="Kelly fraction" value={kellyFraction} onChange={setKellyFraction} min={10} max={50} step={5} unit="%" explain="Fraction du Kelly optimal utilisée. 25% = conservateur. 50% = agressif. Ne jamais dépasser 50%." />
            <ParamSlider label="Position max" value={maxPositionPct} onChange={setMaxPositionPct} min={5} max={25} step={1} unit="% capital" explain="Taille maximale d'une position en % du capital. Plafond absolu même si le Kelly recommande plus." />
            <ParamSlider label="Position min" value={minPositionPct} onChange={setMinPositionPct} min={1} max={10} step={1} unit="% capital" explain="Taille minimale. En dessous, le trade n'est pas exécuté (les frais mangeraient le gain)." />
            <ParamSlider label="Stop Loss" value={slMultiplier} onChange={setSlMultiplier} min={1.0} max={4.0} step={0.5} unit="× ATR" explain="Distance du Stop Loss en multiples d'ATR. 2.0 = standard. Plus serré = plus de faux stops." />
            <ParamSlider label="Take Profit" value={tpMultiplier} onChange={setTpMultiplier} min={2.0} max={6.0} step={0.5} unit="× ATR" explain="Distance du Take Profit. Le ratio TP/SL détermine le R:R. 3.0/2.0 = R:R de 1.5." />
          </div>
          <div className="mt-3 p-3 bg-surface rounded-lg">
            <p className="text-[10px] text-text-secondary">R:R actuel : <span className="text-gold font-mono font-bold">1:{(tpMultiplier / slMultiplier).toFixed(1)}</span> — {tpMultiplier / slMultiplier >= 1.5 ? "Bon ratio" : tpMultiplier / slMultiplier >= 1.0 ? "Ratio minimal" : "Ratio défavorable"}</p>
          </div>
        </SettingsSection>

        {/* ═══ RISK MANAGEMENT ═══ */}
        <SettingsSection id="risk" title="Gestion du Risque" icon={<Shield size={18} />} open={openSections.has("risk")} toggle={toggle}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ParamSlider label="Drawdown max" value={maxDrawdownPct} onChange={setMaxDrawdownPct} min={10} max={30} step={1} unit="%" explain="Drawdown maximum avant pause du pipeline. -20% = fermeture de toutes les positions." />
            <ParamSlider label="Risk Budget" value={riskBudgetPct} onChange={setRiskBudgetPct} min={5} max={25} step={1} unit="% capital" explain="Budget de perte maximum sur la période. Quand il est consommé, le système passe en mode MINIMAL." />
            <ParamSlider label="Corrélation max" value={maxCorrelation} onChange={setMaxCorrelation} min={0.5} max={0.95} step={0.05} unit="" explain="Corrélation maximale entre deux positions. Au-dessus, le sizing est réduit ou bloqué." />
            <ParamSlider label="Trailing Stop" value={trailingStopAtr} onChange={setTrailingStopAtr} min={1.0} max={3.0} step={0.5} unit="× ATR" explain="Le stop remonte avec le prix. 2.0 ATR = standard. Ne redescend jamais." />
            <ParamSlider label="Seuil d'essoufflement" value={exhaustionThreshold} onChange={setExhaustionThreshold} min={20} max={50} step={5} unit="/100" explain="Score de santé en dessous duquel la position est fermée automatiquement." />
          </div>
          <div className="mt-3 grid grid-cols-4 gap-2">
            {[
              { label: "Normal", range: `0% à -${Math.round(maxDrawdownPct * 0.25)}%`, active: true },
              { label: "Warning", range: `-${Math.round(maxDrawdownPct * 0.25)}% à -${Math.round(maxDrawdownPct * 0.5)}%`, active: false },
              { label: "Alerte", range: `-${Math.round(maxDrawdownPct * 0.5)}% à -${Math.round(maxDrawdownPct * 0.75)}%`, active: false },
              { label: "Critique", range: `> -${maxDrawdownPct}%`, active: false },
            ].map((l) => (
              <div key={l.label} className={`rounded-lg p-2 text-center border text-[10px] ${l.active ? "border-emerald-400 bg-emerald-400/10 text-emerald-400" : "border-border bg-surface text-text-secondary"}`}>
                <p className="font-semibold">{l.label}</p>
                <p className="mt-0.5 opacity-75">{l.range}</p>
              </div>
            ))}
          </div>
        </SettingsSection>

        {/* ═══ SCHEDULER ═══ */}
        <SettingsSection id="scheduler" title="Scheduler & Pipeline" icon={<Clock size={18} />} open={openSections.has("scheduler")} toggle={toggle}>
          <div className="space-y-3">
            <ScheduleRow time="21h30 UTC" paris="23h30" task="MAJ Données Daily" description="Télécharge les OHLCV du jour pour les 500 actifs via Yahoo Finance" frequency="1×/jour" />
            <ScheduleRow time="22h00 UTC" paris="00h00" task="Pipeline Complet" description="Scanner → Corrélation → Analyseur → Scoring → Exécution → Portefeuille → Performance → Monte Carlo" frequency="1×/jour" />
            <ScheduleRow time="13h45 UTC" paris="15h45" task="Scan Intraday US" description="Détection des breakouts 15 min après l'ouverture du marché US" frequency="1×/jour" />
            <ScheduleRow time="*/5 min" paris="24/7" task="TP/SL Monitor" description="Trailing stop, SL/TP, essoufflement, signal inverse, file d'attente" frequency="288×/jour" />
          </div>
          <div className="mt-4 p-3 bg-surface rounded-lg text-xs text-text-secondary">
            <p><span className="text-gold font-semibold">15 stratégies</span> testées sur chaque actif : 4 classiques + 3 avancées + 5 pro + 3 genius</p>
            <p className="mt-1"><span className="text-gold font-semibold">500 actifs</span> × <span className="text-gold font-semibold">10 critères</span> = 5 000 scores calculés par run</p>
            <p className="mt-1">Matrice combinée <span className="text-gold font-semibold">V2 (5 ans, 60%) + V3 (10 ans, 40%)</span> — 497 actifs backtestés</p>
          </div>
        </SettingsSection>

        {/* ═══ NOTIFICATIONS ═══ */}
        <SettingsSection id="notifications" title="Notifications" icon={<Bell size={18} />} open={openSections.has("notifications")} toggle={toggle}>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 mb-4">
              <ToggleParam label="Email" value={notifEmail} onChange={setNotifEmail} explain="Notifications par email (SMTP configuré dans .env)" />
              <ToggleParam label="Telegram" value={notifTelegram} onChange={setNotifTelegram} explain="Bot Telegram (TELEGRAM_BOT_TOKEN dans .env)" />
            </div>
            <p className="text-[10px] text-text-secondary uppercase tracking-wider font-semibold mb-2">Événements notifiés</p>
            <ToggleParam label="Signaux GO" value={notifSignalGo} onChange={setNotifSignalGo} explain="Notification quand un signal GO est généré par le pipeline" />
            <ToggleParam label="SL / TP touchés" value={notifSlTp} onChange={setNotifSlTp} explain="Notification quand un Stop Loss ou Take Profit est atteint" />
            <ToggleParam label="Rapport hebdomadaire" value={notifWeeklyReport} onChange={setNotifWeeklyReport} explain="Rapport P&L + métriques chaque dimanche" />
          </div>
        </SettingsSection>

        {/* ═══ BROKERS & APIs ═══ */}
        <SettingsSection id="brokers" title="Brokers & APIs" icon={<Monitor size={18} />} open={openSections.has("brokers")} toggle={toggle}>
          <div className="space-y-2">
            {[
              { name: "Alpaca", type: "Broker", status: "configured", detail: "Paper Trading — actions US, ETF, crypto" },
              { name: "Interactive Brokers", type: "Broker", status: "configured", detail: "Live Trading — tous marchés (US, EU, forex, crypto, commodities)" },
              { name: "Yahoo Finance", type: "Données", status: "configured", detail: "OHLCV historique — gratuit, 500 actifs" },
              { name: "TradingView", type: "Données", status: "configured", detail: "Autocomplete + fallback données — gratuit" },
              { name: "FRED", type: "Macro", status: "optional", detail: "Données macro réelles (taux, VIX, CPI, M2) — clé gratuite" },
              { name: "Reddit API", type: "Sentiment", status: "optional", detail: "Sentiment retail (r/wallstreetbets, r/stocks) — clé gratuite" },
              { name: "NewsAPI", type: "Sentiment", status: "optional", detail: "Flux d'actualités financières — gratuit 100 req/jour" },
              { name: "Telegram Bot", type: "Notifications", status: "optional", detail: "Alertes push sur votre téléphone — gratuit" },
            ].map((api) => (
              <div key={api.name} className="flex items-center justify-between p-3 bg-surface rounded-lg">
                <div>
                  <p className="text-sm font-semibold">{api.name}</p>
                  <p className="text-[10px] text-text-secondary">{api.detail}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[9px] text-text-secondary">{api.type}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                    api.status === "configured" ? "bg-gold/10 text-gold border border-gold/20" : "bg-surface text-text-secondary border border-border"
                  }`}>{api.status === "configured" ? "Actif" : "Optionnel"}</span>
                </div>
              </div>
            ))}
          </div>
        </SettingsSection>

        {/* ═══ INFRASTRUCTURE ═══ */}
        <SettingsSection id="infra" title="Infrastructure" icon={<Database size={18} />} open={openSections.has("infra")} toggle={toggle}>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <InfoBox label="Base de données" value="PostgreSQL" sub="500 actifs, 2.4M barres" />
            <InfoBox label="Cache" value="Redis" sub="Sessions + Celery broker" />
            <InfoBox label="Pipeline" value="Celery" sub="4 workers + Beat scheduler" />
            <InfoBox label="Frontend" value="Vercel" sub="CDN mondial, HTTPS" />
            <InfoBox label="Backend" value="FastAPI" sub="Mac local + Cloudflare Tunnel" />
            <InfoBox label="ML/NLP" value="PyTorch MPS" sub="FinBERT + XGBoost" />
          </div>
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
            <InfoBox label="Actifs" value="500" sub="6 classes" />
            <InfoBox label="Stratégies" value="15" sub="4 niveaux" />
            <InfoBox label="Critères" value="10" sub="orthogonaux" />
            <InfoBox label="Score V2" value="9" sub="composantes" />
          </div>
        </SettingsSection>

        {/* ═══ SCORING V2 ═══ */}
        <SettingsSection id="scoring" title="Score V2 — Composantes" icon={<Settings2 size={18} />} open={openSections.has("scoring")} toggle={toggle}>
          <div className="space-y-2">
            {[
              { name: "Scanner (10 critères)", poids: 22, color: "bg-gold" },
              { name: "Conviction Stratégie", poids: 20, color: "bg-emerald-400" },
              { name: "Régime Global", poids: 10, color: "bg-blue-400" },
              { name: "Fondamentaux", poids: 10, color: "bg-purple-400" },
              { name: "Catalyseurs", poids: 10, color: "bg-orange-400" },
              { name: "Corrélation Portefeuille", poids: 10, color: "bg-cyan-400" },
              { name: "Lead-Lag", poids: 7, color: "bg-pink-400" },
              { name: "Rotation Sectorielle", poids: 6, color: "bg-yellow-400" },
              { name: "Multi-Timeframe (MTA)", poids: 5, color: "bg-indigo-400" },
            ].map((c) => (
              <div key={c.name}>
                <div className="flex justify-between text-xs mb-1">
                  <span>{c.name}</span>
                  <span className="font-mono font-semibold">{c.poids}%</span>
                </div>
                <div className="h-2 bg-surface rounded-full overflow-hidden">
                  <div className={`h-full ${c.color} rounded-full`} style={{ width: `${c.poids * 4}%` }} />
                </div>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-text-secondary mt-3 italic">
            Les poids sont auto-calibrés par le Scoring Calibrator (Module 6). Ils s'ajustent quotidiennement
            basé sur le taux de détection des top movers. Ajustements max ±5% par itération.
          </p>
        </SettingsSection>

        {/* ═══ BIAIS COMPORTEMENTAUX ═══ */}
        <SettingsSection id="bias" title="Détection de Biais" icon={<Shield size={18} />} open={openSections.has("bias")} toggle={toggle}>
          <p className="text-[10px] text-text-secondary mb-4">Le système détecte et corrige automatiquement les biais émotionnels avant chaque trade.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ParamSlider label="Seuil FOMO" value={fomoThreshold} onChange={setFomoThreshold} min={10} max={40} step={5} unit="%" explain="Si l'actif a déjà bougé de +X% avant l'entrée → alerte FOMO. Le trade est bloqué." />
            <ParamSlider label="Cooldown Revenge" value={revengeCooldown} onChange={setRevengeCooldown} min={10} max={60} step={5} unit=" min" explain="Temps d'attente après une perte avant de pouvoir reprendre un trade." />
            <ParamSlider label="Réduction Revenge" value={revengeReduction} onChange={setRevengeReduction} min={10} max={50} step={5} unit="%" explain="Le sizing est réduit de X% sur le trade suivant une perte (anti-revenge trading)." />
          </div>
        </SettingsSection>

        {/* ═══ VETOS SCANNER ═══ */}
        <SettingsSection id="vetos" title="Vetos du Scanner" icon={<Zap size={18} />} open={openSections.has("vetos")} toggle={toggle}>
          <p className="text-[10px] text-text-secondary mb-4">Un actif est automatiquement rejeté si un critère tombe sous son seuil de veto, quel que soit son score global.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ParamSlider label="MTS (Macro)" value={vetoMts} onChange={setVetoMts} min={10} max={40} step={5} unit="/100" explain="Vent macro trop contraire → rejet automatique." />
            <ParamSlider label="SUS (Unicité)" value={vetoSus} onChange={setVetoSus} min={15} max={40} step={5} unit="/100" explain="Signal trop crowdé (tout le monde le voit) → rejet." />
            <ParamSlider label="IPI (Institutionnel)" value={vetoIpi} onChange={setVetoIpi} min={10} max={40} step={5} unit="/100" explain="Distribution institutionnelle massive → rejet." />
          </div>
        </SettingsSection>

        {/* ═══ SCALING D'ENTRÉE ═══ */}
        <SettingsSection id="scaling" title="Scaling d'Entrée (3 tranches)" icon={<TrendingUp size={18} />} open={openSections.has("scaling")} toggle={toggle}>
          <p className="text-[10px] text-text-secondary mb-4">Le système n'entre pas tout d'un coup — il scale progressivement pour réduire le risque de timing.</p>
          <div className="grid grid-cols-3 gap-4">
            <ParamSlider label="Tranche 1" value={tranche1} onChange={setTranche1} min={20} max={60} step={5} unit="%" explain="Immédiatement — pied dans la porte." />
            <ParamSlider label="Tranche 2" value={tranche2} onChange={setTranche2} min={20} max={50} step={5} unit="%" explain="Quand le prix confirme la direction." />
            <ParamSlider label="Tranche 3" value={tranche3} onChange={setTranche3} min={10} max={40} step={5} unit="%" explain="Quand le momentum est soutenu." />
          </div>
          <div className="mt-3 p-3 bg-surface rounded-lg text-[10px] text-text-secondary">
            Total : <span className={`font-mono font-bold ${tranche1 + tranche2 + tranche3 === 100 ? "text-emerald-400" : "text-red-400"}`}>{tranche1 + tranche2 + tranche3}%</span>
            {tranche1 + tranche2 + tranche3 !== 100 && " — doit totaliser 100%"}
          </div>
        </SettingsSection>

        {/* ═══ STRATEGY DECAY ═══ */}
        <SettingsSection id="decay" title="Strategy Decay (Quarantaine)" icon={<Shield size={18} />} open={openSections.has("decay")} toggle={toggle}>
          <p className="text-[10px] text-text-secondary mb-4">Détecte les stratégies qui perdent leur edge et les met en quarantaine automatiquement.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ParamSlider label="Trades minimum" value={decayMinTrades} onChange={setDecayMinTrades} min={5} max={30} step={5} unit="" explain="Nombre minimum de trades avant d'évaluer une stratégie." />
            <ParamSlider label="Win Rate minimum" value={decayMinWinRate} onChange={setDecayMinWinRate} min={25} max={50} step={5} unit="%" explain="En dessous → la stratégie est suspecte." />
            <ParamSlider label="Profit Factor min" value={decayMinPF} onChange={setDecayMinPF} min={0.5} max={1.5} step={0.1} unit="" explain="En dessous de 1.0 → la stratégie perd de l'argent." />
          </div>
        </SettingsSection>

        {/* ═══ EWS (Early Warning) ═══ */}
        <SettingsSection id="ews" title="Early Warning System" icon={<Bell size={18} />} open={openSections.has("ews")} toggle={toggle}>
          <p className="text-[10px] text-text-secondary mb-4">Seuils d'alerte qui déclenchent des actions de protection automatiques.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ParamSlider label="Drawdown → Attention" value={ewsDrawdownAttention} onChange={setEwsDrawdownAttention} min={3} max={10} step={1} unit="%" explain="Premier niveau d'alerte. Au-delà → notification + sizing réduit." />
            <ParamSlider label="Losing Streak → Attention" value={ewsLosingStreak} onChange={setEwsLosingStreak} min={2} max={8} step={1} unit=" trades" explain="Nombre de pertes consécutives avant l'alerte." />
          </div>
        </SettingsSection>

        {/* ═══ CACHES ═══ */}
        <SettingsSection id="caches" title="Durée de vie des Caches" icon={<Database size={18} />} open={openSections.has("caches")} toggle={toggle}>
          <p className="text-[10px] text-text-secondary mb-4">Les caches évitent de recalculer les résultats à chaque requête. Un TTL plus long = moins de calcul, un TTL plus court = données plus fraîches.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ParamSlider label="Cache Scanner" value={scannerCacheTtl} onChange={setScannerCacheTtl} min={1} max={12} step={1} unit="h" explain="Durée de validité du scan des 500 actifs. 6h = standard." />
            <ParamSlider label="Cache Corrélation" value={correlationCacheTtl} onChange={setCorrelationCacheTtl} min={4} max={24} step={2} unit="h" explain="Matrice 500×500. Calcul lourd (~3 min). 12h = standard." />
          </div>
        </SettingsSection>
      </div>
    </div>
  );
}


// ════════════════════════════════════════════════
// COMPOSANTS
// ════════════════════════════════════════════════

function SettingsSection({ id, title, icon, open, toggle, children }: { id: string; title: string; icon: any; open: boolean; toggle: (id: string) => void; children: any }) {
  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      <button onClick={() => toggle(id)} className="w-full flex items-center gap-3 p-5 text-left hover:bg-surface/50 transition-colors">
        <div className="w-9 h-9 rounded-lg bg-gold/10 text-gold flex items-center justify-center flex-shrink-0">{icon}</div>
        <span className="text-sm font-semibold flex-1">{title}</span>
        <ChevronDown size={16} className={`text-text-secondary transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && <div className="px-5 pb-5 border-t border-border/30 pt-4">{children}</div>}
    </div>
  );
}

function ParamSlider({ label, value, onChange, min, max, step, unit, explain }: { label: string; value: number; onChange: (v: number) => void; min: number; max: number; step: number; unit: string; explain: string }) {
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-xs text-text-secondary">{label}</span>
        <span className="text-xs font-mono font-bold text-gold">{value}{unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 bg-surface rounded-full appearance-none cursor-pointer accent-gold" />
      <p className="text-[9px] text-text-secondary mt-1">{explain}</p>
    </div>
  );
}

function ToggleParam({ label, value, onChange, explain }: { label: string; value: boolean; onChange: (v: boolean) => void; explain: string }) {
  return (
    <div className="flex items-center justify-between p-3 bg-surface rounded-lg">
      <div className="flex-1">
        <p className="text-sm font-semibold">{label}</p>
        <p className="text-[9px] text-text-secondary">{explain}</p>
      </div>
      <button onClick={() => onChange(!value)} className={`w-10 h-5 rounded-full transition-colors flex items-center ${value ? "bg-gold justify-end" : "bg-border justify-start"}`}>
        <div className="w-4 h-4 bg-white rounded-full mx-0.5 shadow" />
      </button>
    </div>
  );
}

function ScheduleRow({ time, paris, task, description, frequency }: { time: string; paris: string; task: string; description: string; frequency: string }) {
  return (
    <div className="flex items-start gap-3 p-3 bg-surface rounded-lg">
      <div className="text-center min-w-[60px]">
        <p className="text-xs font-mono font-bold text-gold">{time}</p>
        <p className="text-[9px] text-text-secondary">{paris} Paris</p>
      </div>
      <div className="flex-1">
        <p className="text-sm font-semibold">{task}</p>
        <p className="text-[10px] text-text-secondary">{description}</p>
      </div>
      <span className="text-[9px] text-text-secondary bg-background px-2 py-0.5 rounded">{frequency}</span>
    </div>
  );
}

function InfoBox({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="bg-surface rounded-lg p-3 text-center">
      <p className="text-[9px] text-text-secondary uppercase tracking-wider">{label}</p>
      <p className="text-lg font-mono font-bold text-gold mt-0.5">{value}</p>
      <p className="text-[9px] text-text-secondary">{sub}</p>
    </div>
  );
}
