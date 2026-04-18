/**
 * Radar chart SVG pour visualiser les 10 critères du scanner.
 * Pas de dépendance externe — SVG pur.
 */

interface DataPoint {
  label: string;
  value: number; // 0-100
  icon?: string;
}

interface Props {
  data: DataPoint[];
  size?: number;
}

export default function RadarChart({ data, size = 300 }: Props) {
  const cx = size / 2;
  const cy = size / 2;
  const maxR = size * 0.38;
  const levels = [20, 40, 60, 80, 100];
  const n = data.length;
  const angleStep = (2 * Math.PI) / n;

  const getPoint = (index: number, value: number) => {
    const angle = angleStep * index - Math.PI / 2;
    const r = (value / 100) * maxR;
    return {
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
    };
  };

  // Polygone des valeurs
  const dataPoints = data.map((d, i) => getPoint(i, d.value));
  const dataPath = dataPoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";

  return (
    <div className="flex justify-center">
      <svg width={size} height={size} className="overflow-visible">
        {/* Grille de fond */}
        {levels.map((level) => {
          const points = Array.from({ length: n }, (_, i) => getPoint(i, level));
          const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";
          return (
            <polygon
              key={level}
              points={points.map((p) => `${p.x},${p.y}`).join(" ")}
              fill="none"
              stroke="#1F1F1F"
              strokeWidth={1}
            />
          );
        })}

        {/* Axes */}
        {data.map((_, i) => {
          const end = getPoint(i, 100);
          return (
            <line
              key={`axis-${i}`}
              x1={cx}
              y1={cy}
              x2={end.x}
              y2={end.y}
              stroke="#1F1F1F"
              strokeWidth={1}
            />
          );
        })}

        {/* Zone de données */}
        <polygon
          points={dataPoints.map((p) => `${p.x},${p.y}`).join(" ")}
          fill="rgba(212,175,55,0.15)"
          stroke="#D4AF37"
          strokeWidth={2}
        />

        {/* Points */}
        {dataPoints.map((p, i) => (
          <circle
            key={`dot-${i}`}
            cx={p.x}
            cy={p.y}
            r={4}
            fill={data[i].value >= 65 ? "#D4AF37" : data[i].value >= 45 ? "#A0A0A0" : "#EF4444"}
            stroke="#0A0A0A"
            strokeWidth={2}
          />
        ))}

        {/* Labels */}
        {data.map((d, i) => {
          const labelPoint = getPoint(i, 125);
          const align = labelPoint.x > cx + 5 ? "start" : labelPoint.x < cx - 5 ? "end" : "middle";
          return (
            <g key={`label-${i}`}>
              <text
                x={labelPoint.x}
                y={labelPoint.y - 6}
                textAnchor={align}
                className="fill-text-secondary"
                fontSize={10}
                fontFamily="Inter, sans-serif"
              >
                {d.icon} {d.label}
              </text>
              <text
                x={labelPoint.x}
                y={labelPoint.y + 8}
                textAnchor={align}
                className="fill-text-primary"
                fontSize={11}
                fontWeight={600}
                fontFamily="JetBrains Mono, monospace"
              >
                {d.value.toFixed(0)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
