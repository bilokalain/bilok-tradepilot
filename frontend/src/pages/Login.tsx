import { useState } from "react";
import api from "../services/api";

interface Props {
  onLogin: (token: string, user: { email: string; name: string }) => void;
}

export default function Login({ onLogin }: Props) {
  const [mode, setMode] = useState<"login" | "register" | "forgot">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  // Forgot password state
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [resetStep, setResetStep] = useState<"email" | "reset">("email");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      if (mode === "forgot") {
        if (resetStep === "email") {
          const res = await api.post("/auth/forgot-password", { email });
          if (res.data.reset_token) {
            setResetToken(res.data.reset_token);
            setResetStep("reset");
            setSuccess("Token de réinitialisation généré. Entrez votre nouveau mot de passe.");
          } else {
            setSuccess("Si cet email existe, un lien de réinitialisation a été envoyé.");
          }
        } else {
          if (newPassword !== confirmPassword) {
            setError("Les mots de passe ne correspondent pas");
            setLoading(false);
            return;
          }
          await api.post("/auth/reset-password", {
            token: resetToken,
            new_password: newPassword,
          });
          setSuccess("Mot de passe réinitialisé ! Vous pouvez vous connecter.");
          setMode("login");
          setResetStep("email");
          setResetToken("");
          setNewPassword("");
          setConfirmPassword("");
        }
      } else {
        const endpoint = mode === "login" ? "/auth/login" : "/auth/register";
        const payload = mode === "login"
          ? { email, password }
          : { email, password, name };

        const res = await api.post(endpoint, payload);
        const { access_token, user } = res.data;
        localStorage.setItem("tradepilot_token", access_token);
        onLogin(access_token, user);
      }
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
          <h1 className="text-3xl font-bold text-gold mb-2">Bilok-TradePilot</h1>
          <p className="text-text-secondary text-sm">Système de trading automatisé</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-card border border-border rounded-2xl p-8 space-y-5">
          {/* Onglets */}
          {mode !== "forgot" ? (
            <div className="flex border border-border rounded-lg overflow-hidden">
              <button
                type="button"
                onClick={() => { setMode("login"); setError(""); setSuccess(""); }}
                className={`flex-1 py-2 text-sm font-semibold transition-colors ${
                  mode === "login"
                    ? "bg-gold/10 text-gold"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                Connexion
              </button>
              <button
                type="button"
                onClick={() => { setMode("register"); setError(""); setSuccess(""); }}
                className={`flex-1 py-2 text-sm font-semibold transition-colors ${
                  mode === "register"
                    ? "bg-gold/10 text-gold"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                Créer un compte
              </button>
            </div>
          ) : (
            <div className="text-center">
              <h2 className="text-lg font-semibold text-text-primary">Mot de passe oublié</h2>
              <p className="text-xs text-text-secondary mt-1">
                {resetStep === "email"
                  ? "Entrez votre email pour réinitialiser"
                  : "Choisissez un nouveau mot de passe"}
              </p>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-400/10 border border-red-400/20 rounded-lg text-sm text-red-400 text-center">
              {error}
            </div>
          )}

          {success && (
            <div className="p-3 bg-emerald-400/10 border border-emerald-400/20 rounded-lg text-sm text-emerald-400 text-center">
              {success}
            </div>
          )}

          {/* Register: nom */}
          {mode === "register" && (
            <div>
              <label className="text-xs text-text-secondary mb-1.5 block">Nom</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-surface border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-gold/50 transition-colors"
                placeholder="Votre nom"
                required
              />
            </div>
          )}

          {/* Email (login, register, forgot step 1) */}
          {(mode !== "forgot" || resetStep === "email") && (
            <div>
              <label className="text-xs text-text-secondary mb-1.5 block">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-surface border border-border rounded-lg px-4 py-2.5 text-sm font-mono focus:outline-none focus:border-gold/50 transition-colors"
                placeholder="email@exemple.com"
                required
              />
            </div>
          )}

          {/* Password (login, register) */}
          {mode !== "forgot" && (
            <div>
              <label className="text-xs text-text-secondary mb-1.5 block">Mot de passe</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-surface border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-gold/50 transition-colors"
                placeholder={mode === "register" ? "Minimum 6 caractères" : "Votre mot de passe"}
                minLength={mode === "register" ? 6 : undefined}
                required
              />
            </div>
          )}

          {/* Forgot: new password fields */}
          {mode === "forgot" && resetStep === "reset" && (
            <>
              <div>
                <label className="text-xs text-text-secondary mb-1.5 block">Nouveau mot de passe</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-gold/50 transition-colors"
                  placeholder="Minimum 6 caractères"
                  minLength={6}
                  required
                />
              </div>
              <div>
                <label className="text-xs text-text-secondary mb-1.5 block">Confirmer le mot de passe</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-gold/50 transition-colors"
                  placeholder="Retapez le mot de passe"
                  minLength={6}
                  required
                />
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm font-semibold hover:bg-gold/20 transition-colors disabled:opacity-50"
          >
            {loading
              ? "Chargement..."
              : mode === "login"
                ? "Se connecter"
                : mode === "register"
                  ? "Créer mon compte"
                  : resetStep === "email"
                    ? "Envoyer"
                    : "Réinitialiser"}
          </button>

          {/* Lien mot de passe oublié */}
          {mode === "login" && (
            <button
              type="button"
              onClick={() => { setMode("forgot"); setResetStep("email"); setError(""); setSuccess(""); }}
              className="w-full text-center text-xs text-text-secondary hover:text-gold transition-colors"
            >
              Mot de passe oublié ?
            </button>
          )}

          {/* Retour à la connexion */}
          {mode === "forgot" && (
            <button
              type="button"
              onClick={() => { setMode("login"); setResetStep("email"); setError(""); setSuccess(""); setResetToken(""); }}
              className="w-full text-center text-xs text-text-secondary hover:text-gold transition-colors"
            >
              Retour à la connexion
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
