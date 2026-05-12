import { useState } from 'react'
import axios from 'axios'
import './Screener.css'

const API_BASE = import.meta.env.VITE_API_URL || ''

const MA_OPTIONS = [3, 5, 7, 10, 20, 25, 30, 60, 99, 120, 200]
const PERIOD_OPTIONS = [
  { value: '1d', label: '日K' },
  { value: '1wk', label: '週K' },
  { value: '1mo', label: '月K' },
]
const OP_OPTIONS = [
  { value: 'gt', label: '大於 >' },
  { value: 'lt', label: '小於 <' },
  { value: 'gte', label: '大於等於 ≥' },
  { value: 'lte', label: '小於等於 ≤' },
]

const DEFAULT_CONDITION = { ma1: 5, operator: 'gt', ma2: 20, period: '1d' }

// Preset strategies
const PRESETS = [
  {
    name: '多頭排列（日線）',
    desc: 'MA5 > MA20 > MA60',
    conditions: [
      { ma1: 5, operator: 'gt', ma2: 20, period: '1d' },
      { ma1: 20, operator: 'gt', ma2: 60, period: '1d' },
    ],
  },
  {
    name: '黃金交叉準備',
    desc: 'MA5 > MA20，日線',
    conditions: [
      { ma1: 5, operator: 'gt', ma2: 20, period: '1d' },
    ],
  },
  {
    name: '多週期多頭',
    desc: '日線+週線均多頭',
    conditions: [
      { ma1: 5, operator: 'gt', ma2: 20, period: '1d' },
      { ma1: 5, operator: 'gt', ma2: 20, period: '1wk' },
    ],
  },
  {
    name: '空頭排列（日線）',
    desc: 'MA5 < MA20 < MA60',
    conditions: [
      { ma1: 5, operator: 'lt', ma2: 20, period: '1d' },
      { ma1: 20, operator: 'lt', ma2: 60, period: '1d' },
    ],
  },
]

export default function Screener({ onResults, onLoading }) {
  const [conditions, setConditions] = useState([{ ...DEFAULT_CONDITION }])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [progress, setProgress] = useState(0)

  const addCondition = () => {
    setConditions([...conditions, { ...DEFAULT_CONDITION }])
  }

  const removeCondition = (idx) => {
    setConditions(conditions.filter((_, i) => i !== idx))
  }

  const updateCondition = (idx, field, value) => {
    const updated = [...conditions]
    updated[idx] = { ...updated[idx], [field]: field === 'ma1' || field === 'ma2' ? parseInt(value) : value }
    setConditions(updated)
  }

  const loadPreset = (preset) => {
    setConditions(preset.conditions.map(c => ({ ...c })))
  }

  const handleScreen = async () => {
    setLoading(true)
    setError('')
    onLoading(true)

    // Simulate progress while waiting
    let prog = 0
    const interval = setInterval(() => {
      prog = Math.min(prog + Math.random() * 8, 90)
      setProgress(Math.round(prog))
    }, 600)

    try {
      const res = await axios.post(`${API_BASE}/api/screen`, { conditions })
      setProgress(100)
      setTimeout(() => setProgress(0), 800)
      onResults(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || '篩選失敗，請確認後端服務是否正常運行')
    } finally {
      clearInterval(interval)
      setLoading(false)
      onLoading(false)
    }
  }

  return (
    <div className="screener">
      {/* Presets */}
      <div className="presets-section">
        <div className="section-label">快速策略</div>
        <div className="presets">
          {PRESETS.map((p) => (
            <button key={p.name} className="preset-btn" onClick={() => loadPreset(p)}>
              <span className="preset-name">{p.name}</span>
              <span className="preset-desc">{p.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Conditions */}
      <div className="conditions-section">
        <div className="section-header">
          <div className="section-label">篩選條件</div>
          <button className="add-btn" onClick={addCondition}>
            <span>＋</span> 新增條件
          </button>
        </div>

        <div className="conditions-list">
          {conditions.map((cond, idx) => (
            <div key={idx} className="condition-row fade-in">
              <div className="condition-num">{idx + 1}</div>

              <div className="condition-fields">
                <select
                  className="select period-select"
                  value={cond.period}
                  onChange={(e) => updateCondition(idx, 'period', e.target.value)}
                >
                  {PERIOD_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>

                <div className="ma-label">MA</div>
                <select
                  className="select ma-select"
                  value={cond.ma1}
                  onChange={(e) => updateCondition(idx, 'ma1', e.target.value)}
                >
                  {MA_OPTIONS.map(n => <option key={n} value={n}>{n}</option>)}
                </select>

                <select
                  className="select op-select"
                  value={cond.operator}
                  onChange={(e) => updateCondition(idx, 'operator', e.target.value)}
                >
                  {OP_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>

                <div className="ma-label">MA</div>
                <select
                  className="select ma-select"
                  value={cond.ma2}
                  onChange={(e) => updateCondition(idx, 'ma2', e.target.value)}
                >
                  {MA_OPTIONS.map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>

              {conditions.length > 1 && (
                <button
                  className="remove-btn"
                  onClick={() => removeCondition(idx)}
                  title="移除此條件"
                >✕</button>
              )}
            </div>
          ))}
        </div>

        {error && <div className="error-msg">⚠ {error}</div>}

        {/* Progress bar */}
        {loading && (
          <div className="progress-wrap">
            <div className="progress-bar" style={{ width: `${progress}%` }}></div>
            <div className="progress-text">掃描中... {progress}%</div>
          </div>
        )}

        <button
          className={`screen-btn ${loading ? 'loading' : ''}`}
          onClick={handleScreen}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              篩選中，請稍候...
            </>
          ) : (
            <>
              <span>⌖</span> 開始篩選
            </>
          )}
        </button>
      </div>
    </div>
  )
}
