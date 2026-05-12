import { useEffect, useState } from 'react'
import axios from 'axios'
import './StockModal.css'

const API_BASE = import.meta.env.VITE_API_URL || ''

export default function StockModal({ stock, onClose }) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const handleKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose])

  useEffect(() => {
    setLoading(true)
    axios.get(`${API_BASE}/api/stock/${stock.symbol}`)
      .then(res => setDetail(res.data))
      .catch(() => setDetail(null))
      .finally(() => setLoading(false))
  }, [stock.symbol])

  const isUp = stock.change_pct >= 0

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <div className="modal-symbol">{stock.symbol}</div>
            <div className="modal-name">{stock.name}</div>
          </div>
          <div className="modal-price-block">
            <div className="modal-price">{stock.price.toFixed(2)}</div>
            <div className={`modal-change ${isUp ? 'up' : 'down'}`}>
              {isUp ? '▲' : '▼'} {Math.abs(stock.change_pct).toFixed(2)}%
              ({isUp ? '+' : ''}{stock.change.toFixed(2)})
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="modal-loading">
              <div className="spinner-lg"></div>
              <span>載入中...</span>
            </div>
          ) : detail ? (
            <>
              {/* Mini price chart using canvas */}
              {detail.chart_data && detail.chart_data.length > 0 && (
                <MiniChart data={detail.chart_data} />
              )}

              {/* MA Values */}
              {stock.ma_values && Object.keys(stock.ma_values).length > 0 && (
                <div className="ma-section">
                  <div className="ma-section-title">均線數值</div>
                  {Object.entries(stock.ma_values).map(([period, mas]) => (
                    <div key={period} className="ma-period-group">
                      <div className="ma-period-label">
                        {period === '1d' ? '日K' : period === '1wk' ? '週K' : '月K'}
                      </div>
                      <div className="ma-chips">
                        {Object.entries(mas).map(([name, val]) => (
                          <div key={name} className="ma-chip">
                            <span className="ma-chip-name">{name}</span>
                            <span className="ma-chip-val">{val.toFixed(2)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="modal-links">
                <a
                  href={`https://tw.tradingview.com/chart/?symbol=TWSE:${stock.symbol}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="modal-link-btn"
                >
                  📈 TradingView 圖表
                </a>
                <a
                  href={`https://www.twse.com.tw/zh/stock/search?stockNo=${stock.symbol}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="modal-link-btn secondary"
                >
                  🏛 證交所資料
                </a>
              </div>
            </>
          ) : (
            <div className="modal-error">無法載入詳細資料</div>
          )}
        </div>
      </div>
    </div>
  )
}

function MiniChart({ data }) {
  const closes = data.map(d => d.close)
  const min = Math.min(...closes)
  const max = Math.max(...closes)
  const range = max - min || 1
  const W = 600
  const H = 120
  const pad = { l: 40, r: 10, t: 10, b: 20 }
  const chartW = W - pad.l - pad.r
  const chartH = H - pad.t - pad.b
  const last = closes.length - 1
  const isUp = closes[last] >= closes[0]
  const color = isUp ? '#ff4757' : '#00d68f'

  const pts = closes.map((c, i) => {
    const x = pad.l + (i / (last || 1)) * chartW
    const y = pad.t + (1 - (c - min) / range) * chartH
    return `${x},${y}`
  })

  const pathD = `M ${pts.join(' L ')}`
  const fillD = `${pathD} L ${pad.l + chartW},${pad.t + chartH} L ${pad.l},${pad.t + chartH} Z`

  // Last few labels
  const firstClose = closes[0]
  const lastClose = closes[last]

  return (
    <div className="mini-chart">
      <div className="chart-label">近 120 日走勢</div>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg">
        <defs>
          <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map(t => (
          <line key={t}
            x1={pad.l} y1={pad.t + t * chartH}
            x2={pad.l + chartW} y2={pad.t + t * chartH}
            stroke="#1e2a38" strokeWidth="1"
          />
        ))}
        {/* Fill */}
        <path d={fillD} fill="url(#chartGrad)" />
        {/* Line */}
        <path d={pathD} fill="none" stroke={color} strokeWidth="1.5" />
        {/* Labels */}
        <text x={pad.l - 4} y={pad.t + 4} textAnchor="end" fontSize="9" fill="#4a5568">{max.toFixed(0)}</text>
        <text x={pad.l - 4} y={pad.t + chartH} textAnchor="end" fontSize="9" fill="#4a5568">{min.toFixed(0)}</text>
        {/* Current price dot */}
        <circle
          cx={pad.l + chartW}
          cy={pad.t + (1 - (lastClose - min) / range) * chartH}
          r="3" fill={color}
        />
      </svg>
    </div>
  )
}
