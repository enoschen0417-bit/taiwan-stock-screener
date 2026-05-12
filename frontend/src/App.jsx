import { useState } from 'react'
import Header from './components/Header.jsx'
import Screener from './components/Screener.jsx'
import ResultsTable from './components/ResultsTable.jsx'
import StockModal from './components/StockModal.jsx'
import './App.css'

export default function App() {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [screened, setScreened] = useState(null)
  const [selectedStock, setSelectedStock] = useState(null)

  return (
    <div className="app">
      <Header />
      <main className="main">
        <Screener
          onResults={(data) => {
            setResults(data.results)
            setScreened(data.total_screened)
          }}
          onLoading={setLoading}
        />
        <ResultsTable
          results={results}
          loading={loading}
          screened={screened}
          onSelectStock={setSelectedStock}
        />
      </main>
      {selectedStock && (
        <StockModal
          stock={selectedStock}
          onClose={() => setSelectedStock(null)}
        />
      )}
    </div>
  )
}
