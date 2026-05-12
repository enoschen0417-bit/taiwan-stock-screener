import './Header.css'

export default function Header() {
  return (
    <header className="header">
      <div className="header-inner">
        <div className="logo">
          <span className="logo-icon">⌖</span>
          <div className="logo-text">
            <span className="logo-title">台股狙擊手</span>
            <span className="logo-sub">Taiwan Stock Screener</span>
          </div>
        </div>
        <div className="header-info">
          <div className="info-chip">
            <span className="dot green"></span>
            <span>資料來源：Yahoo Finance</span>
          </div>
          <div className="info-chip">
            <span className="dot yellow"></span>
            <span>延遲約 15 分鐘</span>
          </div>
        </div>
      </div>
      <div className="header-line"></div>
    </header>
  )
}
