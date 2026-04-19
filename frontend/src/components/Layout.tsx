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
  ShieldCheck,
} from "lucide-react";
import { useState, useEffect } from "react";
import { Users } from "lucide-react";
import api from "../services/api";
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
      { to: "/admin", icon: ShieldCheck, label: "Admin" },
      { to: "/settings", icon: Settings, label: "Paramètres" },
      { to: "/guide", icon: BookOpen, label: "Guide" },
      { to: "/livres", icon: BookOpen, label: "Livre" },
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

        {/* Footer — Profil + Déconnexion */}
        <div className="p-4 border-t border-border space-y-2">
          {user && (
            <button
              onClick={() => {
                const event = new CustomEvent("open-profile");
                window.dispatchEvent(event);
              }}
              className="flex items-center gap-2 w-full px-1 py-1 rounded hover:bg-surface transition-colors"
            >
              <div className="w-7 h-7 rounded-full bg-gold/20 flex items-center justify-center text-gold text-xs font-bold">
                {(user.name || user.email)[0].toUpperCase()}
              </div>
              <div className="text-left flex-1 min-w-0">
                <p className="text-[11px] font-medium text-text-primary truncate">{user.name || "Utilisateur"}</p>
                <p className="text-[9px] text-text-secondary truncate">{user.email}</p>
              </div>
            </button>
          )}
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-gold animate-pulse" />
            <span className="text-[10px] text-text-secondary">Pipeline actif</span>
          </div>
          {onLogout && (
            <button
              onClick={onLogout}
              className="flex items-center gap-2 text-[11px] text-text-secondary hover:text-red-400 transition-colors w-full px-2 py-1.5 rounded hover:bg-red-400/5"
            >
              <LogOut size={13} />
              Se déconnecter
            </button>
          )}
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col">
        <header className="h-11 bg-card border-b border-border flex items-center justify-between px-6">
          <OnlineUsers />
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


function OnlineUsers() {
  const [online, setOnline] = useState<any[]>([]);
  const [show, setShow] = useState(false);

  useEffect(() => {
    const fetch = () => {
      api.get("/auth/online").then((res) => setOnline(res.data.online || [])).catch(() => {});
    };
    fetch();
    const interval = setInterval(fetch, 15000);
    return () => clearInterval(interval);
  }, []);

  const PAGE_LABELS: Record<string, string> = {
    "/": "Dashboard", "/scanner": "Scanner", "/analyse": "Analyse",
    "/scoring": "Scoring", "/execution": "Exécution", "/portfolio": "Portefeuille",
    "/performance": "Performance", "/backtest": "Backtest", "/correlation": "Corrélation",
    "/settings": "Paramètres", "/admin": "Admin", "/guide": "Guide", "/livres": "Livre",
    "/theses": "Thèses",
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShow(!show)}
        className="flex items-center gap-2 text-xs text-text-secondary hover:text-gold transition-colors"
      >
        <Users size={14} />
        <span className="font-semibold">{online.length}</span>
        <span>en ligne</span>
        {online.length > 0 && <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />}
      </button>

      {show && online.length > 0 && (
        <div className="absolute top-8 left-0 bg-card border border-border rounded-xl p-3 shadow-lg z-50 min-w-[220px]">
          <p className="text-[9px] text-text-secondary uppercase tracking-wider font-semibold mb-2">
            Utilisateurs connectés
          </p>
          <div className="space-y-2">
            {online.map((u: any) => (
              <div key={u.email} className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-gold/20 flex items-center justify-center text-gold text-[10px] font-bold">
                  {(u.name || u.email)[0].toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold truncate">{u.name || u.email}</p>
                  <p className="text-[9px] text-text-secondary">{PAGE_LABELS[u.page] || u.page || "—"}</p>
                </div>
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
