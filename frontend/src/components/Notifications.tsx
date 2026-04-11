import { useEffect, useState, useCallback } from "react";
import { Bell, X, TrendingUp, AlertTriangle, Zap } from "lucide-react";
import { scoringApi, type TradeThesis } from "../services/api";

interface Notification {
  id: string;
  type: "signal" | "warning" | "info";
  title: string;
  message: string;
  symbol?: string;
  timestamp: Date;
  read: boolean;
}

export default function Notifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [open, setOpen] = useState(false);
  const [lastCheck, setLastCheck] = useState<string[]>([]);

  const checkSignals = useCallback(async () => {
    try {
      const res = await scoringApi.getSignals();
      const signals = res.data;
      const currentSymbols = signals.map((s) => s.symbol);

      // Nouveaux signaux GO par rapport au dernier check
      const newSignals = signals.filter((s) => !lastCheck.includes(s.symbol));

      if (newSignals.length > 0) {
        const newNotifs: Notification[] = newSignals.map((s) => ({
          id: `signal-${s.symbol}-${Date.now()}`,
          type: "signal" as const,
          title: `Signal GO — ${s.symbol}`,
          message: `${s.direction} via ${s.strategy} | Score ${s.thesis_score.toFixed(1)} | Entry $${s.entry.toFixed(2)}`,
          symbol: s.symbol,
          timestamp: new Date(),
          read: false,
        }));

        setNotifications((prev) => [...newNotifs, ...prev].slice(0, 50));
      }

      setLastCheck(currentSymbols);
    } catch {
      // Silently fail
    }
  }, [lastCheck]);

  // Check toutes les 60 secondes
  useEffect(() => {
    checkSignals();
    const interval = setInterval(checkSignals, 60_000);
    return () => clearInterval(interval);
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const removeNotif = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  const iconMap = {
    signal: TrendingUp,
    warning: AlertTriangle,
    info: Zap,
  };

  const colorMap = {
    signal: "text-gold",
    warning: "text-yellow-400",
    info: "text-blue-400",
  };

  return (
    <div className="relative">
      {/* Bell icon */}
      <button
        onClick={() => { setOpen(!open); if (!open) markAllRead(); }}
        className="relative p-2 text-text-secondary hover:text-text-primary transition-colors"
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-gold text-black text-[10px] font-bold rounded-full flex items-center justify-center">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-10 w-96 bg-card border border-border rounded-xl shadow-2xl z-50 max-h-[500px] overflow-hidden flex flex-col">
          <div className="flex items-center justify-between p-4 border-b border-border">
            <h3 className="text-sm font-semibold">Notifications</h3>
            {notifications.length > 0 && (
              <button
                onClick={() => setNotifications([])}
                className="text-xs text-text-secondary hover:text-text-primary"
              >
                Tout effacer
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-text-secondary text-sm">
                Aucune notification
              </div>
            ) : (
              notifications.map((n) => {
                const Icon = iconMap[n.type];
                return (
                  <div
                    key={n.id}
                    className={`flex items-start gap-3 p-3 border-b border-border/50 hover:bg-surface transition-colors ${
                      !n.read ? "bg-gold/5" : ""
                    }`}
                  >
                    <Icon size={16} className={`mt-0.5 flex-shrink-0 ${colorMap[n.type]}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium">{n.title}</p>
                      <p className="text-xs text-text-secondary mt-0.5 truncate">{n.message}</p>
                      <p className="text-[10px] text-text-secondary mt-1">
                        {formatTime(n.timestamp)}
                      </p>
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); removeNotif(n.id); }}
                      className="text-text-secondary hover:text-text-primary p-0.5"
                    >
                      <X size={12} />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function formatTime(date: Date): string {
  const now = new Date();
  const diff = (now.getTime() - date.getTime()) / 1000;
  if (diff < 60) return "À l'instant";
  if (diff < 3600) return `Il y a ${Math.floor(diff / 60)}min`;
  if (diff < 86400) return `Il y a ${Math.floor(diff / 3600)}h`;
  return date.toLocaleDateString("fr-FR");
}
