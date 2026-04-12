import { useState } from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
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
import Guide from "./pages/Guide";

function App() {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("tradepilot_token")
  );
  const [user, setUser] = useState<{ email: string; name: string } | null>(null);

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
    <Routes>
      <Route element={<Layout onLogout={handleLogout} user={user} />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/scanner" element={<Scanner />} />
        <Route path="/analyse" element={<Analyse />} />
        <Route path="/asset/:symbol" element={<AssetDetail />} />
        <Route path="/analyser" element={<Analyser />} />
        <Route path="/scoring" element={<Scoring />} />
        <Route path="/execution" element={<Execution />} />
        <Route path="/backtest" element={<Backtest />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/performance" element={<Performance />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/guide" element={<Guide />} />
      </Route>
    </Routes>
  );
}

export default App;
