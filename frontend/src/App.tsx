import { useState, useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import ProfileModal from "./components/ProfileModal";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Scanner from "./pages/Scanner";
import AssetDetail from "./pages/AssetDetail";
import Analyser from "./pages/Analyser";
import Scoring from "./pages/Scoring";
import Execution from "./pages/Execution";
import Backtest from "./pages/Backtest";
import Portfolio from "./pages/Portfolio";
import Performance from "./pages/Performance";
import Settings from "./pages/Settings";
import Analyse from "./pages/Analyse";
import Correlation from "./pages/Correlation";
import Theses from "./pages/Theses";
import Guide from "./pages/Guide";
import Livres from "./pages/Livres";
import Admin from "./pages/Admin";

function App() {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("tradepilot_token")
  );
  const [user, setUser] = useState<{ email: string; name: string } | null>(null);
  const [showProfile, setShowProfile] = useState(false);

  // Charger le thème sauvegardé au démarrage
  useEffect(() => {
    const savedTheme = localStorage.getItem("tradepilot_theme") || "dark-gold";
    document.documentElement.setAttribute("data-theme", savedTheme);
  }, []);

  // Charger le profil utilisateur si un token existe déjà
  useEffect(() => {
    if (token && !user) {
      import("./services/api").then(({ default: api }) => {
        api.get("/auth/me").then((res) => {
          if (res.data) setUser(res.data);
        }).catch(() => {
          // Token invalide — déconnecter
          setToken(null);
          localStorage.removeItem("tradepilot_token");
        });
      });
    }
  }, [token, user]);

  // Heartbeat — signale au backend que l'utilisateur est actif (toutes les 30s)
  useEffect(() => {
    if (!token || !user) return;
    const sendHeartbeat = () => {
      import("./services/api").then(({ default: api }) => {
        const page = window.location.pathname;
        api.post(`/auth/heartbeat?page=${encodeURIComponent(page)}`).catch(() => {});
      });
    };
    sendHeartbeat();
    const interval = setInterval(sendHeartbeat, 30000);
    return () => clearInterval(interval);
  }, [token, user]);

  // Écouter l'événement "open-profile" du Layout
  useEffect(() => {
    const handler = () => setShowProfile(true);
    window.addEventListener("open-profile", handler);
    return () => window.removeEventListener("open-profile", handler);
  }, []);

  const handleLogin = (t: string, u: { email: string; name: string }) => {
    setToken(t);
    setUser(u);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("tradepilot_token");
  };

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <>
    {showProfile && (
      <ProfileModal
        user={user}
        onClose={() => setShowProfile(false)}
        onProfileUpdate={(u) => setUser(u)}
      />
    )}
    <Routes>
      <Route element={<Layout onLogout={handleLogout} user={user} />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/scanner" element={<Scanner />} />
        <Route path="/analyse" element={<Analyse />} />
        <Route path="/correlation" element={<Correlation />} />
        <Route path="/theses" element={<Theses />} />
        <Route path="/asset/:symbol" element={<AssetDetail />} />
        <Route path="/analyser" element={<Analyser />} />
        <Route path="/scoring" element={<Scoring />} />
        <Route path="/execution" element={<Execution />} />
        <Route path="/backtest" element={<Backtest />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/performance" element={<Performance />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/guide" element={<Guide />} />
        <Route path="/livres" element={<Livres />} />
        <Route path="/admin" element={<Admin />} />
      </Route>
    </Routes>
    </>
  );
}

export default App;
