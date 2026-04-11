export default function Settings() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Paramètres</h2>

      <div className="space-y-6">
        <section className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">APIs Marché</h3>
          <div className="space-y-3">
            {["Alpha Vantage", "Binance", "Polygon.io"].map((api) => (
              <div key={api} className="flex items-center justify-between">
                <span className="text-sm">{api}</span>
                <span className="text-xs text-text-secondary px-2 py-1 bg-surface rounded">
                  Non configuré
                </span>
              </div>
            ))}
          </div>
        </section>

        <section className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Broker</h3>
          <div className="space-y-3">
            {["Alpaca (Paper Trading)", "Binance", "Interactive Brokers"].map((broker) => (
              <div key={broker} className="flex items-center justify-between">
                <span className="text-sm">{broker}</span>
                <span className="text-xs text-text-secondary px-2 py-1 bg-surface rounded">
                  Non configuré
                </span>
              </div>
            ))}
          </div>
        </section>

        <section className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Pipeline</h3>
          <div className="flex items-center justify-between">
            <span className="text-sm">Mode</span>
            <span className="text-xs text-gold px-2 py-1 bg-gold/10 border border-gold/20 rounded">
              Paper Trading
            </span>
          </div>
        </section>
      </div>
    </div>
  );
}
