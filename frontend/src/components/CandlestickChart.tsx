import { useMemo } from "react";
import {
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
  Cell,
} from "recharts";

interface OHLCVBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface Props {
  data: OHLCVBar[];
  height?: number;
}

export default function CandlestickChart({ data, height = 400 }: Props) {
  const chartData = useMemo(() => {
    return data.map((d) => ({
      date: d.date.slice(5),  // MM-DD
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
      volume: d.volume,
      // Pour les barres du "corps" de la bougie
      bodyLow: Math.min(d.open, d.close),
      bodyHigh: Math.max(d.open, d.close),
      body: [Math.min(d.open, d.close), Math.max(d.open, d.close)],
      isUp: d.close >= d.open,
    }));
  }, [data]);

  if (chartData.length === 0) return null;

  return (
    <div>
      {/* Prix */}
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1F1F1F" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#A0A0A0", fontSize: 10 }}
            tickLine={false}
            interval={Math.floor(chartData.length / 8)}
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
            labelStyle={{ color: "#A0A0A0" }}
            formatter={(value: number, name: string) => {
              const label = name === "close" ? "Close" : name === "high" ? "High" : name === "low" ? "Low" : name;
              return [`$${value.toFixed(2)}`, label];
            }}
          />
          <Line type="monotone" dataKey="close" stroke="#D4AF37" dot={false} strokeWidth={1.5} />
          <Line type="monotone" dataKey="high" stroke="#555" dot={false} strokeWidth={0.5} />
          <Line type="monotone" dataKey="low" stroke="#555" dot={false} strokeWidth={0.5} />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Volume */}
      <ResponsiveContainer width="100%" height={80}>
        <ComposedChart data={chartData} margin={{ top: 0, right: 10, left: 10, bottom: 5 }}>
          <XAxis dataKey="date" hide />
          <YAxis hide />
          <Bar dataKey="volume" maxBarSize={3}>
            {chartData.map((entry, i) => (
              <Cell key={i} fill={entry.isUp ? "#D4AF3755" : "#FFFFFF33"} />
            ))}
          </Bar>
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
