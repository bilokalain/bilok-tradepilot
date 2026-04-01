// ─── APIs MARCHÉ ───────────────────────────────────────────

export type MarketQuote = {
  symbol: string
  nom: string
  prix: number
  change: number
  changePct: number
  volume: number
  high: number
  low: number
  open: number
  previousClose: number
  marketCap?: number
  timestamp: number
}

export type HistoricalCandle = {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

/**
 * Yahoo Finance — Données temps réel (via proxy gratuit)
 */
export async function getQuote(symbol: string): Promise<MarketQuote | null> {
  try {
    const res = await fetch(
      `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=1d`,
      { next: { revalidate: 60 } }
    )
    if (!res.ok) return null
    const data = await res.json()

    const meta = data.chart?.result?.[0]?.meta
    if (!meta) return null

    return {
      symbol: meta.symbol,
      nom: meta.shortName || meta.longName || symbol,
      prix: meta.regularMarketPrice,
      change: meta.regularMarketPrice - meta.previousClose,
      changePct: ((meta.regularMarketPrice - meta.previousClose) / meta.previousClose) * 100,
      volume: meta.regularMarketVolume || 0,
      high: meta.regularMarketDayHigh || meta.regularMarketPrice,
      low: meta.regularMarketDayLow || meta.regularMarketPrice,
      open: meta.regularMarketOpen || meta.regularMarketPrice,
      previousClose: meta.previousClose,
      timestamp: Date.now(),
    }
  } catch {
    return null
  }
}

/**
 * Yahoo Finance — Données historiques
 */
export async function getHistorical(
  symbol: string,
  range: "1mo" | "3mo" | "6mo" | "1y" | "2y" | "5y" = "1y",
  interval: "1d" | "1wk" | "1mo" = "1d"
): Promise<HistoricalCandle[]> {
  try {
    const res = await fetch(
      `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=${interval}&range=${range}`,
      { next: { revalidate: 300 } }
    )
    if (!res.ok) return []
    const data = await res.json()

    const result = data.chart?.result?.[0]
    if (!result) return []

    const timestamps = result.timestamp || []
    const quotes = result.indicators?.quote?.[0] || {}

    return timestamps.map((ts: number, i: number) => ({
      date: new Date(ts * 1000).toISOString().split("T")[0],
      open: quotes.open?.[i] ?? 0,
      high: quotes.high?.[i] ?? 0,
      low: quotes.low?.[i] ?? 0,
      close: quotes.close?.[i] ?? 0,
      volume: quotes.volume?.[i] ?? 0,
    })).filter((c: HistoricalCandle) => c.close > 0)
  } catch {
    return []
  }
}

/**
 * Recherche de symboles
 */
export async function searchSymbols(query: string): Promise<{ symbol: string; nom: string; type: string }[]> {
  try {
    const res = await fetch(
      `https://query1.finance.yahoo.com/v1/finance/search?q=${encodeURIComponent(query)}&quotesCount=10`,
      { next: { revalidate: 3600 } }
    )
    if (!res.ok) return []
    const data = await res.json()

    return (data.quotes || []).map((q: any) => ({
      symbol: q.symbol,
      nom: q.shortname || q.longname || q.symbol,
      type: q.quoteType || "EQUITY",
    }))
  } catch {
    return []
  }
}
