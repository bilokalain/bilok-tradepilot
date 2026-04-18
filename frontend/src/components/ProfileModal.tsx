import { useState, useEffect } from "react";
import { X, User, Lock, Check } from "lucide-react";
import api from "../services/api";

interface Props {
  user: { email: string; name: string } | null;
  onClose: () => void;
  onProfileUpdate: (user: { email: string; name: string }) => void;
}

export default function ProfileModal({ user, onClose, onProfileUpdate }: Props) {
  const [tab, setTab] = useState<"profile" | "password">("profile");
  const [name, setName] = useState(user?.name || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setName(user?.name || "");
  }, [user]);

  const handleProfileSave = async () => {
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      const res = await api.put("/auth/me", { name });
      onProfileUpdate({ email: user?.email || "", name: res.data.name });
      setSuccess("Profil mis à jour");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erreur");
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async () => {
    setError("");
    setSuccess("");
    if (newPassword !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas");
      return;
    }
    if (newPassword.length < 6) {
      setError("Le mot de passe doit faire au moins 6 caractères");
      return;
    }
    setLoading(true);
    try {
      await api.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSuccess("Mot de passe modifié avec succès");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erreur");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-card border border-border rounded-2xl w-full max-w-md mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <h2 className="text-lg font-semibold text-text-primary">Mon Profil</h2>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary">
            <X size={18} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border">
          <button
            onClick={() => { setTab("profile"); setError(""); setSuccess(""); }}
            className={`flex-1 py-3 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${
              tab === "profile" ? "text-gold border-b-2 border-gold" : "text-text-secondary"
            }`}
          >
            <User size={14} /> Profil
          </button>
          <button
            onClick={() => { setTab("password"); setError(""); setSuccess(""); }}
            className={`flex-1 py-3 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${
              tab === "password" ? "text-gold border-b-2 border-gold" : "text-text-secondary"
            }`}
          >
            <Lock size={14} /> Mot de passe
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4">
          {error && (
            <div className="p-3 bg-red-400/10 border border-red-400/20 rounded-lg text-sm text-red-400 text-center">
              {error}
            </div>
          )}
          {success && (
            <div className="p-3 bg-emerald-400/10 border border-emerald-400/20 rounded-lg text-sm text-emerald-400 text-center flex items-center justify-center gap-2">
              <Check size={14} /> {success}
            </div>
          )}

          {tab === "profile" ? (
            <>
              <div>
                <label className="text-xs text-text-secondary mb-1.5 block">Email</label>
                <input
                  type="email"
                  value={user?.email || ""}
                  disabled
                  className="w-full bg-surface/50 border border-border rounded-lg px-4 py-2.5 text-sm font-mono text-text-secondary cursor-not-allowed"
                />
              </div>
              <div>
                <label className="text-xs text-text-secondary mb-1.5 block">Nom</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-gold/50 transition-colors"
                  placeholder="Votre nom"
                />
              </div>
              <button
                onClick={handleProfileSave}
                disabled={loading}
                className="w-full py-2.5 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm font-semibold hover:bg-gold/20 transition-colors disabled:opacity-50"
              >
                {loading ? "Enregistrement..." : "Enregistrer"}
              </button>
            </>
          ) : (
            <>
              <div>
                <label className="text-xs text-text-secondary mb-1.5 block">Mot de passe actuel</label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-gold/50 transition-colors"
                  placeholder="Votre mot de passe actuel"
                />
              </div>
              <div>
                <label className="text-xs text-text-secondary mb-1.5 block">Nouveau mot de passe</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-gold/50 transition-colors"
                  placeholder="Minimum 6 caractères"
                />
              </div>
              <div>
                <label className="text-xs text-text-secondary mb-1.5 block">Confirmer</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-gold/50 transition-colors"
                  placeholder="Retapez le nouveau mot de passe"
                />
              </div>
              <button
                onClick={handlePasswordChange}
                disabled={loading || !currentPassword || !newPassword}
                className="w-full py-2.5 bg-gold/10 text-gold border border-gold/20 rounded-lg text-sm font-semibold hover:bg-gold/20 transition-colors disabled:opacity-50"
              >
                {loading ? "Modification..." : "Changer le mot de passe"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
