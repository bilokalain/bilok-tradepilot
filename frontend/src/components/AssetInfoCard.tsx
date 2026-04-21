import { useEffect, useState } from "react";
import { Building2, Globe, Users, DollarSign, TrendingUp, Activity, Info, ExternalLink } from "lucide-react";
import api from "../services/api";

interface AssetInfo {
  symbol: string;
  name: string;
  asset_class: string | null;
  description: string | null;
  key_info: Record<string, any>;
  valuation: Record<string, any>;
  holdings: { symbol: string; name: string; weight: number }[];
  crypto: Record<string, any>;
  error: string | null;
}

interface Props {
  symbol: string;
  compact?: boolean;
}

export default function AssetInfoCard({ symbol, compact = false }: Props) {
  const [info, setInfo] = useState<AssetInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [showFullDesc, setShowFullDesc] = useState(false);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    api.get(`/scanner/asset-info/${encodeURIComponent(symbol)}`)
      .then((res) => setInfo(res.data))
      .catch(() => setInfo(null))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) {
    return (
      <div className="bg-card border border-border rounded-xl p-5 mb-6 animate-pulse">
        <div className="h-4 bg-surface rounded w-1/3 mb-3"></div>
        <div className="h-3 bg-surface rounded w-full mb-2"></div>
        <div className="h-3 bg-surface rounded w-3/4"></div>
      </div>
    );
  }

  if (!info || info.error) return null;

  const hasContent = info.description || Object.keys(info.key_info).length > 0 || Object.keys(info.valuation).length > 0;
  if (!hasContent) return null;

  const ki = info.key_info;
  const val = info.valuation;
  const cr = info.crypto;
  const desc = info.description || "";
  const descShort = desc.length > 280 ? desc.slice(0, 280) + "..." : desc;

  return (
    <div className="bg-card border border-border rounded-xl p-5 mb-6">
      <div className="flex items-center gap-2 mb-3">
        <Info size={16} className="text-gold" />
        <h3 className="text-sm font-semibold">Carte d'identité — {info.name}</h3>
        {info.asset_class && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface border border-border text-text-secondary">
            {info.asset_class}
          </span>
        )}
      </div>

      {/* Description */}
      {desc && (
        <div className="mb-4">
          <p className="text-xs text-text-secondary leading-relaxed">
            {showFullDesc ? desc : descShort}
          </p>
          {desc.length > 280 && (
            <button
              onClick={() => setShowFullDesc(!showFullDesc)}
              className="text-[10px] text-gold hover:underline mt-1"
            >
              {showFullDesc ? "Réduire" : "Lire la suite"}
            </button>
          )}
        </div>
      )}

      {/* Infos clés — grille */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
        {ki.sector && (
          <InfoCell icon={<Building2 size={12} />} label="Secteur" value={ki.sector} sublabel={ki.industry} />
        )}
        {ki.country && (
          <InfoCell icon={<Globe size={12} />} label="Pays" value={ki.country} />
        )}
        {ki.employees && (
          <InfoCell icon={<Users size={12} />} label="Employés" value={ki.employees.toLocaleString("fr-FR")} />
        )}
        {ki.market_cap_formatted && (
          <InfoCell icon={<DollarSign size={12} />} label="Market Cap" value={`$${ki.market_cap_formatted}`} />
        )}
        {ki.beta !== undefined && (
          <InfoCell icon={<Activity size={12} />} label="Beta" value={ki.beta.toFixed(2)} sublabel={ki.beta > 1.3 ? "Très volatile" : ki.beta > 0.8 ? "Volatilité marché" : "Peu volatile"} />
        )}
        {ki.website && (
          <a href={ki.website} target="_blank" rel="noopener noreferrer" className="bg-surface rounded-lg p-2 text-xs hover:border-gold/30 border border-transparent flex items-center gap-1.5 transition-colors">
            <ExternalLink size={12} className="text-gold shrink-0" />
            <span className="truncate text-gold">{ki.website.replace(/^https?:\/\//, "").replace(/\/$/, "")}</span>
          </a>
        )}
        {ki.aum_formatted && (
          <InfoCell icon={<DollarSign size={12} />} label="AUM" value={`$${ki.aum_formatted}`} />
        )}
        {ki.expense_ratio !== undefined && (
          <InfoCell icon={<DollarSign size={12} />} label="Frais" value={`${ki.expense_ratio}%`} sublabel="Expense ratio" />
        )}
        {ki.fund_family && (
          <InfoCell icon={<Building2 size={12} />} label="Émetteur" value={ki.fund_family} />
        )}
        {ki.high_52w && ki.low_52w && (
          <InfoCell icon={<TrendingUp size={12} />} label="52w range" value={`$${ki.low_52w.toFixed(2)} - $${ki.high_52w.toFixed(2)}`} />
        )}
      </div>

      {/* Valorisation (actions) */}
      {!compact && Object.keys(val).length > 0 && (
        <div>
          <p className="text-[10px] text-text-secondary uppercase tracking-wider font-semibold mb-2">Valorisation & fondamentaux</p>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
            {val.pe !== undefined && <MetricCell label="P/E" value={val.pe.toFixed(1)} help="Price/Earnings" />}
            {val.forward_pe !== undefined && <MetricCell label="Fwd P/E" value={val.forward_pe.toFixed(1)} help="Forward P/E" />}
            {val.eps !== undefined && <MetricCell label="EPS" value={`$${val.eps}`} help="Earnings/share" />}
            {val.dividend_yield !== undefined && <MetricCell label="Div Yield" value={`${val.dividend_yield}%`} help="Rendement" />}
            {val.profit_margin !== undefined && <MetricCell label="Marge" value={`${val.profit_margin}%`} help="Marge nette" />}
            {val.gross_margin !== undefined && <MetricCell label="Marge brute" value={`${val.gross_margin}%`} help="Gross margin" />}
            {val.revenue_formatted && <MetricCell label="CA" value={`$${val.revenue_formatted}`} help="Revenue TTM" />}
            {val.roe !== undefined && <MetricCell label="ROE" value={`${val.roe}%`} help="Return on Equity" />}
            {val.price_to_book !== undefined && <MetricCell label="P/B" value={val.price_to_book.toFixed(2)} help="Price/Book" />}
            {val.debt_to_equity !== undefined && <MetricCell label="D/E" value={val.debt_to_equity.toFixed(2)} help="Debt/Equity" />}
          </div>
        </div>
      )}

      {/* Spécifique Crypto */}
      {info.asset_class === "CRYPTO" && Object.keys(cr).length > 0 && (
        <div className="mt-3">
          <p className="text-[10px] text-text-secondary uppercase tracking-wider font-semibold mb-2">Supply & activité</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {cr.circulating_supply_formatted && <MetricCell label="Supply circulante" value={cr.circulating_supply_formatted} help="" />}
            {cr.total_supply_formatted && <MetricCell label="Supply totale" value={cr.total_supply_formatted} help="" />}
            {cr.max_supply_formatted && <MetricCell label="Supply max" value={cr.max_supply_formatted} help="Limite" />}
            {cr.volume_24h_formatted && <MetricCell label="Volume 24h" value={`$${cr.volume_24h_formatted}`} help="" />}
          </div>
        </div>
      )}

      {/* Top holdings (ETF) */}
      {info.holdings.length > 0 && (
        <div className="mt-3">
          <p className="text-[10px] text-text-secondary uppercase tracking-wider font-semibold mb-2">Top {info.holdings.length} holdings</p>
          <div className="space-y-1">
            {info.holdings.slice(0, 10).map((h, i) => (
              <div key={i} className="flex items-center justify-between text-xs bg-surface rounded-lg px-3 py-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-gold w-4">{i + 1}</span>
                  <span className="font-semibold">{h.symbol}</span>
                  {h.name && <span className="text-text-secondary text-[10px] truncate max-w-[200px]">{h.name}</span>}
                </div>
                <span className="font-mono text-gold font-semibold">{h.weight.toFixed(2)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function InfoCell({ icon, label, value, sublabel }: { icon: React.ReactNode; label: string; value: string | number; sublabel?: string }) {
  return (
    <div className="bg-surface rounded-lg p-2 border border-border/30">
      <div className="flex items-center gap-1.5 text-text-secondary text-[9px] uppercase tracking-wider mb-0.5">
        {icon}
        <span>{label}</span>
      </div>
      <p className="text-xs font-semibold truncate">{value}</p>
      {sublabel && <p className="text-[9px] text-text-secondary truncate">{sublabel}</p>}
    </div>
  );
}

function MetricCell({ label, value, help }: { label: string; value: string; help: string }) {
  return (
    <div className="bg-surface rounded-lg p-2 text-center border border-border/30" title={help}>
      <p className="text-[9px] text-text-secondary uppercase">{label}</p>
      <p className="text-sm font-mono font-bold">{value}</p>
      {help && <p className="text-[8px] text-text-secondary italic truncate">{help}</p>}
    </div>
  );
}
