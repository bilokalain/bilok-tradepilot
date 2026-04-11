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
  Settings,
} from "lucide-react";
import Notifications from "./Notifications";
import ErrorBoundary from "./ErrorBoundary";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/scanner", icon: ScanSearch, label: "Scanner" },
  { to: "/analyser", icon: Brain, label: "Analyseur" },
  { to: "/scoring", icon: Target, label: "Scoring" },
  { to: "/execution", icon: Zap, label: "Exécution" },
  { to: "/backtest", icon: FlaskConical, label: "Backtesting" },
  { to: "/portfolio", icon: Briefcase, label: "Portefeuille" },
  { to: "/performance", icon: TrendingUp, label: "Performance" },
  { to: "/settings", icon: Settings, label: "Paramètres" },
];

export default function Layout() {
  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-card border-r border-border flex flex-col">
        <div className="p-6 border-b border-border">
          <h1 className="text-xl font-bold text-gold">TradePilot</h1>
          <p className="text-xs text-text-secondary mt-1">Trading automatisé</p>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? "bg-gold/10 text-gold border border-gold/20"
                    : "text-text-secondary hover:text-text-primary hover:bg-surface"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-gold animate-pulse" />
            <span className="text-xs text-text-secondary">Pipeline actif</span>
          </div>
        </div>
      </aside>
      <div className="flex-1 flex flex-col">
        {/* Top bar avec notifications */}
        <header className="h-12 bg-card border-b border-border flex items-center justify-end px-6">
          <Notifications />
        </header>
        <main className="flex-1 overflow-auto p-6">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
