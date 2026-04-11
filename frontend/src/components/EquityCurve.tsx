import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Props {
  data: number[];
  height?: number;
  label?: string;
}

export default function EquityCurve({ data, height = 250, label = "Equity" }: Props) {
  if (data.length === 0) return null;

  const chartData = data.map((value, i) => ({
    index: i,
    value: value,
  }));

  const startValue = data[0];
  const endValue = data[data.length - 1];
  const isPositive = endValue >= startValue;
  const color = isPositive ? "#D4AF37" : "#EF4444";

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-text-secondary">{label}</span>
        <span className={`text-sm font-mono font-semibold ${isPositive ? "text-gold" : "text-red-400"}`}>
          ${endValue.toFixed(0)} ({((endValue / startValue - 1) * 100).toFixed(2)}%)
        </span>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
          <defs>
            <linearGradient id={`gradient-${label}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1F1F1F" />
          <XAxis
            dataKey="index"
            tick={{ fill: "#A0A0A0", fontSize: 10 }}
            tickLine={false}
            interval={Math.floor(chartData.length / 6)}
          />
          <YAxis
            domain={["auto", "auto"]}
            tick={{ fill: "#A0A0A0", fontSize: 10 }}
            tickLine={false}
            orientation="right"
          />
          <Tooltip
            contentStyle={{
              background: "#0A0A0A",
              border: "1px solid #1F1F1F",
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(value: number) => [`$${value.toFixed(2)}`, label]}
            labelFormatter={(i: number) => `Jour ${i}`}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            fill={`url(#gradient-${label})`}
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
