import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 120_000, // 2 minutes max
});

// --- Types Scanner ---

export interface Asset {
  id: number;
  symbol: string;
  name: string;
  asset_class: string;
}

export interface ScanResult {
  symbol: string;
  name: string;
  asset_class: string;
  scores: {
    technical: number;
    correlation: number;
    final: number;
  };
  last_close: number;
  data_points: number;
}

export interface OHLCVData {
  symbol: string;
  name: string;
  data: Array<{
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
}

// --- Types Analyseur ---

export interface RegimeSummary {
  dominant_regime: string;
  distribution: Record<string, number>;
  total_assets: number;
}

export interface StrategySignal {
  strategy: string;
  direction: string;
  conviction: number;
  weight: number;
  weighted_score: number;
  entry?: number;
  stop_loss?: number;
  take_profit?: number;
  status?: string;
  volume_ratio?: number;
}

export interface AnalysisResult {
  symbol: string;
  name: string;
  asset_class: string;
  regime: {
    regime: string;
    probabilities: Record<string, number>;
    confidence: number;
  };
  best_strategy: {
    name: string | null;
    direction: string;
    conviction: number;
    entry?: number;
    stop_loss?: number;
    take_profit?: number;
  };
  all_strategies: StrategySignal[];
  last_close: number;
}

// --- API Scanner ---

export const scannerApi = {
  scan: () => api.get<ScanResult[]>("/scanner/scan"),
  getResult: (symbol: string) => api.get<ScanResult>(`/scanner/results/${symbol}`),
  getAssets: () => api.get<Asset[]>("/scanner/assets"),
  getOhlcv: (symbol: string, limit = 100) =>
    api.get<OHLCVData>(`/scanner/ohlcv/${symbol}?limit=${limit}`),
};

// --- API Analyseur ---

export const analyserApi = {
  analyseAll: () => api.get<AnalysisResult[]>("/analyser/analyse"),
  analyse: (symbol: string) => api.get<AnalysisResult>(`/analyser/analyse/${symbol}`),
  getRegime: () => api.get<RegimeSummary>("/analyser/regime"),
};

// --- Types Scoring ---

export interface TradeThesis {
  symbol: string;
  name: string;
  asset_class: string;
  action: "GO" | "WAIT" | "NO_TRADE";
  thesis_score: number;
  direction: string;
  strategy: string;
  regime: {
    regime: string;
    probabilities: Record<string, number>;
    confidence: number;
  };
  entry: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  last_close: number;
  bayesian: {
    prior: number;
    likelihood: number;
    posterior: number;
    prior_weight: number;
    observation_weight: number;
  };
  scanner_score: number;
  conviction: number;
  sqc: {
    sqc: number;
    components: {
      liquidity: number;
      time: number;
      volatility_context: number;
    };
  };
  shelf_life: {
    shelf_life_hours: number;
    shelf_life_label: string;
    order_type: string;
    order_reason: string;
  };
  sizing: {
    kelly_fraction: number;
    position_size_usd: number;
    quantity: number;
    risk_per_trade_usd: number;
    risk_pct_of_capital: number;
    risk_reward_ratio: number;
    win_rate_estimate: number;
    expected_value: number;
    reject_reason: string | null;
  };
  reason?: string;
}

// --- API Scoring ---

export const scoringApi = {
  getThesis: (symbol: string, capital = 100000) =>
    api.get<TradeThesis>(`/scoring/thesis/${symbol}?capital=${capital}`),
  getAllTheses: (capital = 100000) =>
    api.get<TradeThesis[]>(`/scoring/theses?capital=${capital}`),
  getSignals: (capital = 100000) =>
    api.get<TradeThesis[]>(`/scoring/signals?capital=${capital}`),
};

// --- Types Execution ---

export interface ExecutionResult {
  symbol: string;
  executed: boolean;
  thesis_score?: number;
  direction?: string;
  strategy?: string;
  reason?: string;
  orders?: Array<{
    symbol: string;
    side: string;
    order_type: string;
    quantity: number;
    price: number | null;
    stop_price: number | null;
    tranche: number;
    status: string;
    filled_price: number | null;
    slippage: number;
  }>;
  bias_check?: {
    overall_level: string;
    overall_score: number;
    message: string;
    can_execute: boolean;
    biases: Array<{
      bias: string;
      score: number;
      level: string;
      detail: string;
    }>;
  };
  position?: {
    symbol: string;
    direction: string;
    entry_price: number;
    quantity: number;
    stop_loss: number;
    take_profit: number;
    pnl: number;
    pnl_pct: number;
  };
  sizing?: {
    position_size_usd: number;
    kelly_fraction: number;
  };
}

export interface OpenPosition {
  id: number;
  symbol: string;
  name: string;
  direction: string;
  entry_price: number;
  current_price: number;
  quantity: number;
  stop_loss: number;
  take_profit: number;
  pnl: number;
  pnl_pct: number;
  status: string;
  opened_at: string;
}

export interface ExecuteAllResult {
  total_signals: number;
  executed: number;
  skipped: number;
  capital_deployed: number;
  capital_remaining: number;
  results: ExecutionResult[];
}

// --- API Execution ---

export const executionApi = {
  execute: (symbol: string, capital = 100000) =>
    api.post<ExecutionResult>(`/execution/execute/${symbol}?capital=${capital}`),
  executeAll: (capital = 100000) =>
    api.post<ExecuteAllResult>(`/execution/execute-all?capital=${capital}`),
  getPositions: () => api.get<OpenPosition[]>("/execution/positions"),
  getOrders: () => api.get("/execution/orders"),
  biasCheck: () => api.get("/execution/bias-check"),
};

export default api;
