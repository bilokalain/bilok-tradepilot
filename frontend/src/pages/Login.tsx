import { useState } from "react";
import axios from "axios";

interface Props {
  onLogin: (token: string, user: { email: string; name: string }) => void;
}

export default function Login({ onLogin }: Props) {
  const [email, setEmail] = useState("admin@tradepilot.local");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await axios.post("/api/auth/login", { email, password });
      const { access_token, user } = res.data;
      localStorage.setItem("tradepilot_token", access_token);
      onLogin(access_token, user);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erreur de connexion");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gold mb-2">TradePilot</h1>
          <p className="text-text-secondary text-sm">Système de trading automatisé</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-card border border-border rounded-2xl p-8 space-y-5">
          <h2 className="text-lg font-semibold text-center">Connexion</h2>

          {error && (
            <div className="p-3 bg-red-400/10 border border-red-400/20 rounded-lg text-sm text-red-400 text-center">
              {error}
            </div>
          )}

          <div>
            <label className="text-xs text-text-secondary mb-1.5 block">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-surface border border-border rounded-lg px-4 py-2.5 text-sm font-mono focus:outline-none focus:border-gold/50 transition-colors"
              required
            />
          </div>

          <div>
            <label className="text-xs text-text-secondary mb-1.5 block">Mot de passe</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-surface border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-gold/50 transition-colors"
              placeholder="Entrez votre mot de passe"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm font-semibold hover:bg-gold/20 transition-colors disabled:opacity-50"
          >
            {loading ? "Connexion..." : "Se connecter"}
          </button>

          <p className="text-[10px] text-text-secondary text-center">
            Compte par défaut : admin@tradepilot.local / tradepilot2024
          </p>
        </form>
      </div>
    </div>
  );
}
