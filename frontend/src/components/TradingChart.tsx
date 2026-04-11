import { useEffect, useRef } from "react";
import { createChart, type IChartApi, type ISeriesApi, ColorType } from "lightweight-charts";

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

export default function TradingChart({
  data,
  height = 400,
  showVolume = true,
  showSMA = true,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    // Nettoyer le chart précédent
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
        scaleMargins: { top: 0.1, bottom: showVolume ? 0.25 : 0.05 },
      },
      timeScale: {
        borderColor: "#1F1F1F",
        timeVisible: false,
      },
    });

    chartRef.current = chart;

    // Données formatées
    const candleData = data.map((d) => ({
      time: d.date as any,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));

    // Chandeliers
    const candleSeries = chart.addCandlestickSeries({
      upColor: "#D4AF37",
      downColor: "#FFFFFF22",
      borderUpColor: "#D4AF37",
      borderDownColor: "#555555",
      wickUpColor: "#D4AF37",
      wickDownColor: "#555555",
    });
    candleSeries.setData(candleData);

    // SMA 20
    if (showSMA && data.length >= 20) {
      const sma20 = computeSMA(data.map((d) => d.close), 20);
      const smaData = data
        .map((d, i) => ({
          time: d.date as any,
          value: sma20[i],
        }))
        .filter((d) => d.value !== null) as { time: any; value: number }[];

      const smaSeries = chart.addLineSeries({
        color: "#D4AF3788",
        lineWidth: 1,
        crosshairMarkerVisible: false,
      });
      smaSeries.setData(smaData);
    }

    // SMA 50
    if (showSMA && data.length >= 50) {
      const sma50 = computeSMA(data.map((d) => d.close), 50);
      const smaData = data
        .map((d, i) => ({
          time: d.date as any,
          value: sma50[i],
        }))
        .filter((d) => d.value !== null) as { time: any; value: number }[];

      const smaSeries = chart.addLineSeries({
        color: "#F5D06066",
        lineWidth: 1,
        crosshairMarkerVisible: false,
      });
      smaSeries.setData(smaData);
    }

    // Volume
    if (showVolume) {
      const volumeSeries = chart.addHistogramSeries({
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

    // Resize
    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    const observer = new ResizeObserver(handleResize);
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [data, height, showVolume, showSMA]);

  return <div ref={containerRef} className="w-full rounded-lg overflow-hidden" />;
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
