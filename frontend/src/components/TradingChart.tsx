import { useEffect, useRef, useState, useCallback } from "react";
import { createChart, type IChartApi, ColorType, CandlestickSeries, LineSeries, HistogramSeries, AreaSeries } from "lightweight-charts";

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
  showVolume?: boolean;
  showSMA?: boolean;
  symbol?: string;
  onPeriodChange?: (period: string) => void;
}

type ChartType = "candles" | "line" | "area";
type Indicator = "sma20" | "sma50" | "sma200" | "ema9" | "ema21" | "bb" | "volume";

const PERIODS = [
  { label: "1S", days: 5 },
  { label: "1M", days: 21 },
  { label: "3M", days: 63 },
  { label: "6M", days: 126 },
  { label: "1A", days: 252 },
  { label: "2A", days: 504 },
  { label: "5A", days: 1260 },
  { label: "MAX", days: 99999 },
];

export default function TradingChart({
  data: fullData,
  height = 450,
  showVolume = true,
  showSMA = true,
  symbol = "",
  onPeriodChange,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [chartType, setChartType] = useState<ChartType>("candles");
  const [period, setPeriod] = useState("1A");
  const [indicators, setIndicators] = useState<Set<Indicator>>(new Set(showSMA ? ["sma20", "sma50", "volume"] : ["volume"]));
  const [showIndicatorPanel, setShowIndicatorPanel] = useState(false);
  const [crosshairData, setCrosshairData] = useState<any>(null);

  const toggleIndicator = (ind: Indicator) => {
    setIndicators((prev) => {
      const next = new Set(prev);
      if (next.has(ind)) next.delete(ind); else next.add(ind);
      return next;
    });
  };

  // Filtrer par période
  const selectedPeriod = PERIODS.find((p) => p.label === period);
  const data = selectedPeriod
    ? fullData.slice(Math.max(0, fullData.length - selectedPeriod.days))
    : fullData;

  // Stats rapides
  const lastBar = data.length > 0 ? data[data.length - 1] : null;
  const firstBar = data.length > 0 ? data[0] : null;
  const periodChange = lastBar && firstBar ? ((lastBar.close / firstBar.open - 1) * 100) : 0;
  const periodHigh = data.length > 0 ? Math.max(...data.map((d) => d.high)) : 0;
  const periodLow = data.length > 0 ? Math.min(...data.map((d) => d.low)) : 0;
  const avgVolume = data.length > 0 ? data.reduce((s, d) => s + d.volume, 0) / data.length : 0;

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "#0A0A0A" },
        textColor: "#A0A0A0",
        fontFamily: "JetBrains Mono, monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "#141414" },
        horzLines: { color: "#141414" },
      },
      crosshair: {
        vertLine: { color: "#D4AF3744", width: 1, style: 2, labelBackgroundColor: "#D4AF37" },
        horzLine: { color: "#D4AF3744", width: 1, style: 2, labelBackgroundColor: "#D4AF37" },
      },
      rightPriceScale: {
        borderColor: "#1F1F1F",
        scaleMargins: { top: 0.05, bottom: indicators.has("volume") ? 0.25 : 0.05 },
      },
      timeScale: {
        borderColor: "#1F1F1F",
        timeVisible: false,
      },
    });

    chartRef.current = chart;

    const candleData = data.map((d) => ({ time: d.date as any, open: d.open, high: d.high, low: d.low, close: d.close }));
    const lineData = data.map((d) => ({ time: d.date as any, value: d.close }));

    // === Type de graphique ===
    if (chartType === "candles") {
      const series = chart.addSeries(CandlestickSeries, {
        upColor: "#D4AF37", downColor: "#FFFFFF15",
        borderUpColor: "#D4AF37", borderDownColor: "#555555",
        wickUpColor: "#D4AF3799", wickDownColor: "#55555599",
      });
      series.setData(candleData);
    } else if (chartType === "line") {
      const series = chart.addSeries(LineSeries, { color: "#D4AF37", lineWidth: 2, crosshairMarkerVisible: true, crosshairMarkerRadius: 3 });
      series.setData(lineData);
    } else {
      const series = chart.addSeries(AreaSeries, { topColor: "rgba(212,175,55,0.25)", bottomColor: "rgba(212,175,55,0.01)", lineColor: "#D4AF37", lineWidth: 2 });
      series.setData(lineData);
    }

    // === Indicateurs ===
    const closes = data.map((d) => d.close);

    if (indicators.has("sma20") && data.length >= 20) {
      addSMALine(chart, data, closes, 20, "#D4AF3777");
    }
    if (indicators.has("sma50") && data.length >= 50) {
      addSMALine(chart, data, closes, 50, "#F5D06055");
    }
    if (indicators.has("sma200") && data.length >= 200) {
      addSMALine(chart, data, closes, 200, "#60A5FA44");
    }
    if (indicators.has("ema9") && data.length >= 9) {
      addEMALine(chart, data, closes, 9, "#A78BFA77");
    }
    if (indicators.has("ema21") && data.length >= 21) {
      addEMALine(chart, data, closes, 21, "#F472B677");
    }
    if (indicators.has("bb") && data.length >= 20) {
      addBollingerBands(chart, data, closes, 20, 2);
    }

    // === Volume ===
    if (indicators.has("volume")) {
      const volumeSeries = chart.addSeries(HistogramSeries, { priceFormat: { type: "volume" }, priceScaleId: "volume" });
      chart.priceScale("volume").applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
      volumeSeries.setData(data.map((d) => ({
        time: d.date as any, value: d.volume,
        color: d.close >= d.open ? "#D4AF3725" : "#FFFFFF10",
      })));
    }

    chart.timeScale().fitContent();

    // Crosshair data
    chart.subscribeCrosshairMove((param) => {
      if (param.time && param.point) {
        const bar = data.find((d) => d.date === param.time);
        if (bar) setCrosshairData(bar);
      }
    });

    const observer = new ResizeObserver(() => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth });
    });
    observer.observe(containerRef.current);

    return () => { observer.disconnect(); chart.remove(); chartRef.current = null; };
  }, [data, height, chartType, indicators]);

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      {/* Top bar — Stats */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border/50">
        <div className="flex items-center gap-4">
          {symbol && <span className="font-mono font-bold text-gold text-sm">{symbol}</span>}
          {lastBar && (
            <>
              <span className="font-mono text-sm">${lastBar.close.toFixed(lastBar.close < 5 ? 4 : 2)}</span>
              <span className={`text-xs font-mono ${periodChange >= 0 ? "text-gold" : "text-red-400"}`}>
                {periodChange >= 0 ? "+" : ""}{periodChange.toFixed(2)}%
              </span>
            </>
          )}
        </div>
        {/* Crosshair OHLCV */}
        {crosshairData && (
          <div className="flex gap-3 text-[10px] text-text-secondary font-mono">
            <span>O <span className="text-text-primary">{crosshairData.open.toFixed(2)}</span></span>
            <span>H <span className="text-text-primary">{crosshairData.high.toFixed(2)}</span></span>
            <span>L <span className="text-text-primary">{crosshairData.low.toFixed(2)}</span></span>
            <span>C <span className="text-text-primary">{crosshairData.close.toFixed(2)}</span></span>
            <span>V <span className="text-text-primary">{formatVolume(crosshairData.volume)}</span></span>
          </div>
        )}
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-1.5 border-b border-border/30 bg-surface/30">
        {/* Périodes */}
        <div className="flex gap-0.5">
          {PERIODS.map((p) => (
            <button
              key={p.label}
              onClick={() => setPeriod(p.label)}
              className={`px-2.5 py-1 text-[10px] rounded transition-colors ${
                period === p.label ? "bg-gold/15 text-gold font-semibold" : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Type + Indicateurs */}
        <div className="flex items-center gap-2">
          {/* Type graphique */}
          <div className="flex gap-0.5 border-r border-border/50 pr-2">
            {(["candles", "line", "area"] as const).map((type) => (
              <button
                key={type}
                onClick={() => setChartType(type)}
                className={`px-2 py-1 text-[10px] rounded transition-colors ${
                  chartType === type ? "bg-gold/15 text-gold" : "text-text-secondary hover:text-text-primary"
                }`}
                title={type === "candles" ? "Chandeliers" : type === "line" ? "Ligne" : "Zone"}
              >
                {type === "candles" ? "◩" : type === "line" ? "╱" : "▧"}
              </button>
            ))}
          </div>

          {/* Indicateurs toggle */}
          <div className="relative">
            <button
              onClick={() => setShowIndicatorPanel(!showIndicatorPanel)}
              className={`px-2.5 py-1 text-[10px] rounded transition-colors ${
                showIndicatorPanel ? "bg-gold/15 text-gold" : "text-text-secondary hover:text-text-primary"
              }`}
            >
              Indicateurs ({indicators.size})
            </button>

            {showIndicatorPanel && (
              <div className="absolute right-0 top-8 bg-card border border-border rounded-xl shadow-2xl z-50 p-3 w-52">
                <p className="text-[10px] text-text-secondary mb-2 font-semibold uppercase tracking-wider">Superposer</p>
                {([
                  { id: "sma20" as Indicator, label: "SMA 20", color: "#D4AF37" },
                  { id: "sma50" as Indicator, label: "SMA 50", color: "#F5D060" },
                  { id: "sma200" as Indicator, label: "SMA 200", color: "#60A5FA" },
                  { id: "ema9" as Indicator, label: "EMA 9", color: "#A78BFA" },
                  { id: "ema21" as Indicator, label: "EMA 21", color: "#F472B6" },
                  { id: "bb" as Indicator, label: "Bollinger Bands", color: "#34D399" },
                  { id: "volume" as Indicator, label: "Volume", color: "#D4AF37" },
                ]).map((ind) => (
                  <button
                    key={ind.id}
                    onClick={() => toggleIndicator(ind.id)}
                    className={`w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs transition-colors ${
                      indicators.has(ind.id) ? "bg-surface text-text-primary" : "text-text-secondary hover:bg-surface/50"
                    }`}
                  >
                    <span className="w-3 h-0.5 rounded-full" style={{ backgroundColor: indicators.has(ind.id) ? ind.color : "#333" }} />
                    {ind.label}
                    {indicators.has(ind.id) && <span className="ml-auto text-gold text-[10px]">✓</span>}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div ref={containerRef} className="w-full" />

      {/* Bottom stats */}
      <div className="flex items-center justify-between px-4 py-1.5 border-t border-border/30 text-[10px] text-text-secondary">
        <div className="flex gap-4">
          <span>Période : <span className="text-text-primary">{data.length} barres</span></span>
          <span>Haut : <span className="text-text-primary">${periodHigh.toFixed(2)}</span></span>
          <span>Bas : <span className="text-text-primary">${periodLow.toFixed(2)}</span></span>
          <span>Amplitude : <span className="text-text-primary">{((periodHigh / periodLow - 1) * 100).toFixed(1)}%</span></span>
        </div>
        <span>Vol. moy : <span className="text-text-primary">{formatVolume(avgVolume)}</span></span>
      </div>
    </div>
  );
}


// ============================================================
// Helpers
// ============================================================

function computeSMA(values: number[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) result.push(null);
    else {
      let sum = 0;
      for (let j = i - period + 1; j <= i; j++) sum += values[j];
      result.push(sum / period);
    }
  }
  return result;
}

function computeEMA(values: number[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  const mult = 2 / (period + 1);
  let ema: number | null = null;
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else if (ema === null) {
      let sum = 0;
      for (let j = i - period + 1; j <= i; j++) sum += values[j];
      ema = sum / period;
      result.push(ema);
    } else {
      ema = (values[i] - ema) * mult + ema;
      result.push(ema);
    }
  }
  return result;
}

function addSMALine(chart: IChartApi, data: OHLCVBar[], closes: number[], period: number, color: string) {
  const smaValues = computeSMA(closes, period);
  const smaData = data.map((d, i) => ({ time: d.date as any, value: smaValues[i] })).filter((d) => d.value !== null) as any[];
  const series = chart.addSeries(LineSeries, { color, lineWidth: 1, crosshairMarkerVisible: false, lastValueVisible: false, priceLineVisible: false });
  series.setData(smaData);
}

function addEMALine(chart: IChartApi, data: OHLCVBar[], closes: number[], period: number, color: string) {
  const emaValues = computeEMA(closes, period);
  const emaData = data.map((d, i) => ({ time: d.date as any, value: emaValues[i] })).filter((d) => d.value !== null) as any[];
  const series = chart.addSeries(LineSeries, { color, lineWidth: 1, crosshairMarkerVisible: false, lastValueVisible: false, priceLineVisible: false });
  series.setData(emaData);
}

function addBollingerBands(chart: IChartApi, data: OHLCVBar[], closes: number[], period: number, stdDev: number) {
  const smaValues = computeSMA(closes, period);
  const upper: (number | null)[] = [];
  const lower: (number | null)[] = [];

  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1 || smaValues[i] === null) {
      upper.push(null);
      lower.push(null);
    } else {
      let sumSq = 0;
      for (let j = i - period + 1; j <= i; j++) sumSq += (closes[j] - smaValues[i]!) ** 2;
      const std = Math.sqrt(sumSq / period);
      upper.push(smaValues[i]! + stdDev * std);
      lower.push(smaValues[i]! - stdDev * std);
    }
  }

  const upperData = data.map((d, i) => ({ time: d.date as any, value: upper[i] })).filter((d) => d.value !== null) as any[];
  const lowerData = data.map((d, i) => ({ time: d.date as any, value: lower[i] })).filter((d) => d.value !== null) as any[];

  chart.addSeries(LineSeries, { color: "#34D39944", lineWidth: 1, crosshairMarkerVisible: false, lastValueVisible: false, priceLineVisible: false }).setData(upperData);
  chart.addSeries(LineSeries, { color: "#34D39944", lineWidth: 1, crosshairMarkerVisible: false, lastValueVisible: false, priceLineVisible: false }).setData(lowerData);
}

function formatVolume(vol: number): string {
  if (vol >= 1e9) return (vol / 1e9).toFixed(1) + "B";
  if (vol >= 1e6) return (vol / 1e6).toFixed(1) + "M";
  if (vol >= 1e3) return (vol / 1e3).toFixed(0) + "K";
  return vol.toFixed(0);
}

