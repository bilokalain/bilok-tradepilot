/**
 * Badge de signal avec explication contextuelle.
 */

interface Props {
  action: "GO" | "WAIT" | "NO_TRADE";
  direction?: string;
  size?: "sm" | "md" | "lg";
  showExplanation?: boolean;
}

const CONFIG = {
  GO: {
    bg: "bg-gold/15",
    border: "border-gold/30",
    text: "text-gold",
    label: "GO",
    explanation: "Signal validé — les critères sont alignés pour entrer en position.",
    dot: "bg-gold",
  },
  WAIT: {
    bg: "bg-yellow-400/10",
    border: "border-yellow-400/20",
    text: "text-yellow-400",
    label: "ATTENTE",
    explanation: "Les conditions ne sont pas encore optimales. Surveiller l'actif.",
    dot: "bg-yellow-400",
  },
  NO_TRADE: {
    bg: "bg-surface",
    border: "border-border",
    text: "text-text-secondary",
    label: "PAS DE TRADE",
    explanation: "Aucun signal directionnel clair. Rester à l'écart.",
    dot: "bg-text-secondary",
  },
};

const DIRECTION_TEXT: Record<string, string> = {
  LONG: "Achat (position haussière)",
  SHORT: "Vente (position baissière)",
};

export default function SignalBadge({ action, direction, size = "md", showExplanation = false }: Props) {
  const config = CONFIG[action];
  const sizeClasses = {
    sm: "text-[10px] px-2 py-0.5",
    md: "text-xs px-3 py-1",
    lg: "text-sm px-4 py-2",
  };

  return (
    <div>
      <div className="flex items-center gap-2">
        <span className={`inline-flex items-center gap-1.5 border rounded-lg font-bold ${config.bg} ${config.border} ${config.text} ${sizeClasses[size]}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${config.dot} ${action === "GO" ? "animate-pulse" : ""}`} />
          {config.label}
        </span>
        {direction && direction !== "NEUTRAL" && (
          <span className={`${sizeClasses[size]} border rounded-lg font-semibold ${
            direction === "LONG" ? "text-gold bg-gold/10 border-gold/20" : "text-red-400 bg-red-400/10 border-red-400/20"
          }`}>
            {direction}
          </span>
        )}
      </div>
      {showExplanation && (
        <p className="text-[11px] text-text-secondary mt-1.5">
          {config.explanation}
          {direction && DIRECTION_TEXT[direction] && (
            <span className="ml-1">Direction : {DIRECTION_TEXT[direction]}.</span>
          )}
        </p>
      )}
    </div>
  );
}
