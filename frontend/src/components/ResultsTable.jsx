import './ResultsTable.css'

export default function ResultsTable({ results, loading, screened, onSelectStock }) {
  if (loading) {
    return (
      <div className="results-panel">
        <div className="results-header">
          <div className="section-label">篩選結果</div>
        </div>
        <div className="loading-state">
          <div className="scan-animation">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="scan-row" style={{ animationDelay: `${i * 0.1}s` }}></div>
            ))}
          </div>
          <div className="loading-text">正在掃描 {screened || 0}+ 支個股...</div>
        </div>
      </div>
    )
  }

  if (screened === null) {
    return (
      <div className="results-panel empty-state">
        <div className="empty-icon">⌖</div>
        <div className="empty-title">設定均線條件，開始篩選</div>
        <div className="empty-desc">
          支援日K、週K、月K線<br />
          可設定多個篩選條件同時過濾
        </div>
      </div>
    )
  }

  return (
    <div className="results-panel">
      <div className="results-header">
        <div className="section-label">篩選結果</div>
        <div className="results-meta">
          <span className="result-count">
            <span className="count-num">{results.length}</span> 支符合
          </span>
          <span className="divider">／</span>
          <span className="total-count">共掃描 {screened} 支</span>
        </div>
      </div>

      {results.length === 0 ? (
        <div className="no-results">
          <span>⊘</span> 無符合條件的個股
        </div>
      ) : (
        <div className="table-wrap">
          <table className="results-table">
            <thead>
              <tr>
                <th>代號</th>
                <th>名稱</th>
                <th className="right">現價</th>
                <th className="right">漲跌</th>
                <th className="right">漲跌幅</th>
                <th className="right">成交量</th>
                <th className="center">圖表</th>
              </tr>
            </thead>
            <tbody>
              {results.map((stock, idx) => (
                <tr
                  key={stock.symbol}
                  className="fade-in"
                  style={{ animationDelay: `${Math.min(idx * 0.03, 0.5)}s` }}
                  onClick={() => onSelectStock(stock)}
                >
                  <td>
                    <div className="symbol-badge">{stock.symbol}</div>
                  </td>
                  <td className="name-cell">{stock.name}</td>
                  <td className="right price-cell">
                    {stock.price.toFixed(2)}
                  </td>
                  <td className={`right ${stock.change >= 0 ? 'up' : 'down'}`}>
                    {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}
                  </td>
                  <td className={`right ${stock.change_pct >= 0 ? 'up' : 'down'}`}>
                    <span className="pct-badge" data-dir={stock.change_pct >= 0 ? 'up' : 'down'}>
                      {stock.change_pct >= 0 ? '▲' : '▼'} {Math.abs(stock.change_pct).toFixed(2)}%
                    </span>
                  </td>
                  <td className="right volume-cell">
                    {(stock.volume / 1000).toFixed(0)}K
                  </td>
                  <td className="center">
                    <a
                      href={`https://tw.tradingview.com/chart/?symbol=TWSE:${stock.symbol}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="chart-link"
                      title="在 TradingView 查看"
                    >TV</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
