import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
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

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/scanner" element={<Scanner />} />
        <Route path="/asset/:symbol" element={<AssetDetail />} />
        <Route path="/analyser" element={<Analyser />} />
        <Route path="/scoring" element={<Scoring />} />
        <Route path="/execution" element={<Execution />} />
        <Route path="/backtest" element={<Backtest />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/performance" element={<Performance />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

export default App;
