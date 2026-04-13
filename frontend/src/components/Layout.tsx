import { Outlet, NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  ScanSearch,
  Brain,
  Target,
  Zap,
  FlaskConical,
  Briefcase,
  TrendingUp,
  LogOut,
  BookOpen,
  SearchCheck,
  GitBranch,
  Lightbulb,
  Settings,
} from "lucide-react";
import Notifications from "./Notifications";
import ErrorBoundary from "./ErrorBoundary";

const navSections = [
  {
    title: "PIPELINE",
    items: [
      { to: "/", icon: LayoutDashboard, label: "Dashboard" },
      { to: "/theses", icon: Lightbulb, label: "Mes Thèses" },
      { to: "/scanner", icon: ScanSearch, label: "Scanner" },
      { to: "/analyser", icon: Brain, label: "Analyseur" },
      { to: "/scoring", icon: Target, label: "Scoring" },
      { to: "/execution", icon: Zap, label: "Exécution" },
      { to: "/portfolio", icon: Briefcase, label: "Portefeuille" },
      { to: "/performance", icon: TrendingUp, label: "Performance" },
    ],
  },
  {
    title: "OUTILS",
    items: [
      { to: "/analyse", icon: SearchCheck, label: "Analyse rapide" },
      { to: "/correlation", icon: GitBranch, label: "Corrélation" },
      { to: "/backtest", icon: FlaskConical, label: "Backtesting" },
    ],
  },
  {
    title: "",
    items: [
      { to: "/settings", icon: Settings, label: "Paramètres" },
      { to: "/guide", icon: BookOpen, label: "Guide" },
    ],
  },
];

interface LayoutProps {
  onLogout?: () => void;
  user?: { email: string; name: string } | null;
}

export default function Layout({ onLogout, user }: LayoutProps) {
  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-card border-r border-border flex flex-col">
        {/* Logo */}
        <div className="p-5 border-b border-border">
          <h1 className="text-lg font-bold text-gold tracking-wide">BILOK</h1>
          <p className="text-[10px] text-text-secondary tracking-widest uppercase">TradePilot</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-2">
          {navSections.map((section, si) => (
            <div key={si}>
              {section.title && (
                <p className="px-5 pt-4 pb-1 text-[9px] font-semibold tracking-[0.2em] text-text-secondary uppercase">
                  {section.title}
                </p>
              )}
              {!section.title && <div className="border-t border-border/50 mx-4 my-2" />}
              <div className="px-3 space-y-0.5">
                {section.items.map(({ to, icon: Icon, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === "/"}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] transition-all ${
                        isActive
                          ? "bg-gold/10 text-gold border border-gold/20 font-medium"
                          : "text-text-secondary hover:text-text-primary hover:bg-surface"
                      }`
                    }
                  >
                    <Icon size={16} />
                    {label}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-border space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-gold animate-pulse" />
            <span className="text-[10px] text-text-secondary">Pipeline actif</span>
          </div>
          {onLogout && (
            <button
              onClick={onLogout}
              className="flex items-center gap-2 text-[11px] text-text-secondary hover:text-red-400 transition-colors w-full px-1"
            >
              <LogOut size={12} />
              Déconnexion
            </button>
          )}
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col">
        <header className="h-11 bg-card border-b border-border flex items-center justify-end px-6">
          <Notifications />
        </header>
        <main className="flex-1 overflow-auto p-6 bg-background">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
