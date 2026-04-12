import { useEffect, useRef, useState } from "react";
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
}

type ChartType = "candles" | "line" | "area";

export default function TradingChart({
  data,
  height = 400,
  showVolume = true,
  showSMA = true,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [chartType, setChartType] = useState<ChartType>("candles");
  const [smaVisible, setSmaVisible] = useState(showSMA);
  const [volumeVisible, setVolumeVisible] = useState(showVolume);

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
        vertLines: { color: "#1F1F1F" },
        horzLines: { color: "#1F1F1F" },
      },
      crosshair: {
        vertLine: { color: "#D4AF3766", width: 1, style: 2 },
        horzLine: { color: "#D4AF3766", width: 1, style: 2 },
      },
      rightPriceScale: {
        borderColor: "#1F1F1F",
        scaleMargins: { top: 0.1, bottom: volumeVisible ? 0.25 : 0.05 },
      },
      timeScale: {
        borderColor: "#1F1F1F",
        timeVisible: false,
      },
    });

    chartRef.current = chart;

    const candleData = data.map((d) => ({
      time: d.date as any,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));

    const lineData = data.map((d) => ({
      time: d.date as any,
      value: d.close,
    }));

    // === Type de graphique ===
    if (chartType === "candles") {
      const series = chart.addSeries(CandlestickSeries, {
        upColor: "#D4AF37",
        downColor: "#FFFFFF22",
        borderUpColor: "#D4AF37",
        borderDownColor: "#555555",
        wickUpColor: "#D4AF37",
        wickDownColor: "#555555",
      });
      series.setData(candleData);
    } else if (chartType === "line") {
      const series = chart.addSeries(LineSeries, {
        color: "#D4AF37",
        lineWidth: 2,
        crosshairMarkerVisible: true,
        crosshairMarkerRadius: 4,
      });
      series.setData(lineData);
    } else if (chartType === "area") {
      const series = chart.addSeries(AreaSeries, {
        topColor: "rgba(212, 175, 55, 0.3)",
        bottomColor: "rgba(212, 175, 55, 0.02)",
        lineColor: "#D4AF37",
        lineWidth: 2,
        crosshairMarkerVisible: true,
      });
      series.setData(lineData);
    }

    // === SMA ===
    if (smaVisible) {
      if (data.length >= 20) {
        const sma20 = computeSMA(data.map((d) => d.close), 20);
        const smaData = data
          .map((d, i) => ({ time: d.date as any, value: sma20[i] }))
          .filter((d) => d.value !== null) as { time: any; value: number }[];

        const sma20Series = chart.addSeries(LineSeries, {
          color: "#D4AF3788",
          lineWidth: 1,
          crosshairMarkerVisible: false,
        });
        sma20Series.setData(smaData);
      }

      if (data.length >= 50) {
        const sma50 = computeSMA(data.map((d) => d.close), 50);
        const smaData = data
          .map((d, i) => ({ time: d.date as any, value: sma50[i] }))
          .filter((d) => d.value !== null) as { time: any; value: number }[];

        const sma50Series = chart.addSeries(LineSeries, {
          color: "#F5D06066",
          lineWidth: 1,
          crosshairMarkerVisible: false,
        });
        sma50Series.setData(smaData);
      }
    }

    // === Volume ===
    if (volumeVisible) {
      const volumeSeries = chart.addSeries(HistogramSeries, {
        priceFormat: { type: "volume" },
        priceScaleId: "volume",
      });

      chart.priceScale("volume").applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
      });

      volumeSeries.setData(
        data.map((d) => ({
          time: d.date as any,
          value: d.volume,
          color: d.close >= d.open ? "#D4AF3733" : "#FFFFFF1A",
        }))
      );
    }

    chart.timeScale().fitContent();

    const observer = new ResizeObserver(() => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    });
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [data, height, chartType, smaVisible, volumeVisible]);

  return (
    <div>
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex gap-1">
          {(["candles", "line", "area"] as const).map((type) => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              className={`px-3 py-1 text-[10px] rounded-lg transition-colors ${
                chartType === type
                  ? "bg-gold/10 text-gold border border-gold/20"
                  : "text-text-secondary hover:text-text-primary bg-surface"
              }`}
            >
              {type === "candles" ? "Bougies" : type === "line" ? "Ligne" : "Zone"}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setSmaVisible(!smaVisible)}
            className={`px-2 py-1 text-[10px] rounded-lg transition-colors ${
              smaVisible ? "bg-gold/10 text-gold border border-gold/20" : "text-text-secondary bg-surface"
            }`}
          >
            SMA
          </button>
          <button
            onClick={() => setVolumeVisible(!volumeVisible)}
            className={`px-2 py-1 text-[10px] rounded-lg transition-colors ${
              volumeVisible ? "bg-gold/10 text-gold border border-gold/20" : "text-text-secondary bg-surface"
            }`}
          >
            Volume
          </button>
        </div>
      </div>

      {/* Chart */}
      <div ref={containerRef} className="w-full rounded-lg overflow-hidden" />
    </div>
  );
}

function computeSMA(values: number[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else {
      let sum = 0;
      for (let j = i - period + 1; j <= i; j++) sum += values[j];
      result.push(sum / period);
    }
  }
  return result;
}
