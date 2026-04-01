// ─── INDICATEURS TECHNIQUES ────────────────────────────────

type Candle = { open: number; high: number; low: number; close: number; volume: number }

/**
 * Simple Moving Average (SMA)
 */
export function sma(closes: number[], period: number): (number | null)[] {
  return closes.map((_, i) => {
    if (i < period - 1) return null
    const slice = closes.slice(i - period + 1, i + 1)
    return slice.reduce((a, b) => a + b, 0) / period
  })
}

/**
 * Exponential Moving Average (EMA)
 */
export function ema(closes: number[], period: number): (number | null)[] {
  const result: (number | null)[] = []
  const multiplier = 2 / (period + 1)

  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) {
      result.push(null)
    } else if (i === period - 1) {
      const sum = closes.slice(0, period).reduce((a, b) => a + b, 0)
      result.push(sum / period)
    } else {
      const prev = result[i - 1] as number
      result.push((closes[i] - prev) * multiplier + prev)
    }
  }
  return result
}

/**
 * Relative Strength Index (RSI)
 */
export function rsi(closes: number[], period: number = 14): (number | null)[] {
  const result: (number | null)[] = []
  const gains: number[] = []
  const losses: number[] = []

  for (let i = 0; i < closes.length; i++) {
    if (i === 0) {
      result.push(null)
      continue
    }

    const change = closes[i] - closes[i - 1]
    gains.push(change > 0 ? change : 0)
    losses.push(change < 0 ? -change : 0)

    if (i < period) {
      result.push(null)
      continue
    }

    let avgGain: number, avgLoss: number

    if (i === period) {
      avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period
      avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period
    } else {
      const prevRsi = result[i - 1]
      if (prevRsi === null) { result.push(null); continue }
      // Approximation avec lissage
      const prevGains = gains.slice(Math.max(0, gains.length - period), gains.length)
      const prevLosses = losses.slice(Math.max(0, losses.length - period), losses.length)
      avgGain = prevGains.reduce((a, b) => a + b, 0) / period
      avgLoss = prevLosses.reduce((a, b) => a + b, 0) / period
    }

    if (avgLoss === 0) {
      result.push(100)
    } else {
      const rs = avgGain / avgLoss
      result.push(100 - 100 / (1 + rs))
    }
  }

  return result
}

/**
 * MACD (Moving Average Convergence Divergence)
 */
export function macd(closes: number[], fast = 12, slow = 26, signal = 9) {
  const emaFast = ema(closes, fast)
  const emaSlow = ema(closes, slow)

  const macdLine = emaFast.map((f, i) => {
    const s = emaSlow[i]
    if (f === null || s === null) return null
    return f - s
  })

  const macdValues = macdLine.filter((v): v is number => v !== null)
  const signalLine = ema(macdValues, signal)

  // Aligner la signal line avec l'index original
  const signalFull: (number | null)[] = new Array(macdLine.length).fill(null)
  let j = 0
  for (let i = 0; i < macdLine.length; i++) {
    if (macdLine[i] !== null) {
      signalFull[i] = signalLine[j] ?? null
      j++
    }
  }

  const histogram = macdLine.map((m, i) => {
    const s = signalFull[i]
    if (m === null || s === null) return null
    return m - s
  })

  return { macd: macdLine, signal: signalFull, histogram }
}

/**
 * Bollinger Bands
 */
export function bollingerBands(closes: number[], period = 20, stdDev = 2) {
  const middle = sma(closes, period)

  return middle.map((mid, i) => {
    if (mid === null) return { upper: null, middle: null, lower: null }
    const slice = closes.slice(i - period + 1, i + 1)
    const variance = slice.reduce((sum, val) => sum + Math.pow(val - mid, 2), 0) / period
    const std = Math.sqrt(variance)
    return {
      upper: mid + stdDev * std,
      middle: mid,
      lower: mid - stdDev * std,
    }
  })
}

/**
 * Average True Range (ATR)
 */
export function atr(candles: Candle[], period = 14): (number | null)[] {
  const trueRanges: number[] = []

  for (let i = 0; i < candles.length; i++) {
    if (i === 0) {
      trueRanges.push(candles[i].high - candles[i].low)
    } else {
      const tr = Math.max(
        candles[i].high - candles[i].low,
        Math.abs(candles[i].high - candles[i - 1].close),
        Math.abs(candles[i].low - candles[i - 1].close)
      )
      trueRanges.push(tr)
    }
  }

  return sma(trueRanges, period)
}

/**
 * Stochastique %K et %D
 */
export function stochastic(candles: Candle[], kPeriod = 14, dPeriod = 3) {
  const kValues: (number | null)[] = []

  for (let i = 0; i < candles.length; i++) {
    if (i < kPeriod - 1) {
      kValues.push(null)
      continue
    }
    const slice = candles.slice(i - kPeriod + 1, i + 1)
    const highestHigh = Math.max(...slice.map((c) => c.high))
    const lowestLow = Math.min(...slice.map((c) => c.low))
    const k = highestHigh === lowestLow ? 50 : ((candles[i].close - lowestLow) / (highestHigh - lowestLow)) * 100
    kValues.push(k)
  }

  const kFiltered = kValues.filter((v): v is number => v !== null)
  const dValues = sma(kFiltered, dPeriod)

  return { k: kValues, d: dValues }
}
