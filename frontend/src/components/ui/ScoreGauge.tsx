/**
 * Jauge circulaire animée pour les scores 0-100.
 * Couleur adaptative : rouge < 40, neutre 40-65, doré > 65
 */

interface Props {
  score: number;
  size?: number;
  label?: string;
  sublabel?: string;
}

export default function ScoreGauge({ score, size = 120, label, sublabel }: Props) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.max(0, Math.min(100, score)) / 100;
  const offset = circumference * (1 - progress);

  const color =
    score >= 70 ? "#D4AF37" :
    score >= 50 ? "#A0A0A0" :
    score >= 35 ? "#F59E0B" :
    "#EF4444";

  const bgColor =
    score >= 70 ? "rgba(212,175,55,0.1)" :
    score >= 50 ? "rgba(160,160,160,0.1)" :
    "rgba(239,68,68,0.1)";

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#1F1F1F"
            strokeWidth={6}
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={6}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 1s ease-out" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-mono font-bold" style={{ color }}>
            {score.toFixed(0)}
          </span>
          {sublabel && (
            <span className="text-[10px] text-text-secondary">{sublabel}</span>
          )}
        </div>
      </div>
      {label && (
        <span className="text-xs text-text-secondary mt-2 text-center">{label}</span>
      )}
    </div>
  );
}
