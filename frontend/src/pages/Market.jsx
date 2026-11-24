import { useEffect, useRef, useState } from 'react'
import Plotly from 'plotly.js-dist-min'
import Navbar from '../components/Navbar'
import api, { getErrorMessage } from '../api'
import CompanyInfo from '../components/CompanyInfo'

const PERIODS = ['1M', '3M', '6M', '1Y', '5Y']

function marketFrom(symbol, exchange = '') {
  if (symbol.endsWith('.NS')) return 'NSE'
  if (symbol.endsWith('.BO')) return 'BSE'
  if (/nyse/i.test(exchange)) return 'NYSE'
  return 'NASDAQ'
}

export default function Market() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [selected, setSelected] = useState(null)
  const [period, setPeriod] = useState('1Y')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const priceRef = useRef(null)
  const volumeRef = useRef(null)
  const [chartType, setChartType] = useState('candlestick')

  useEffect(() => {
    api
      .get('/preferences')
      .then((res) => setPeriod(res.data.default_period))
      .catch(() => {})
  }, [])

  async function handleSearch(e) {
    e.preventDefault()
    if (!query.trim()) return
    setError('')
    setSearching(true)
    try {
      const res = await api.get('/stocks/search', { params: { q: query } })
      setResults(res.data)
      if (res.data.length === 0) setError('No matching stocks found.')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSearching(false)
    }
  }

  function selectStock(r) {
    setSelected({ symbol: r.symbol, name: r.name, market: marketFrom(r.symbol, r.exchange) })
    setResults([])
  }

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    setLoading(true)
    setError('')
    api
      .get(`/stocks/${encodeURIComponent(selected.symbol)}/history`, {
        params: { market: selected.market, period },
      })
      .then((res) => {
        if (!cancelled) setData(res.data)
      })
      .catch((err) => {
        if (!cancelled) {
          setData(null)
          setError(getErrorMessage(err))
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [selected, period])

  useEffect(() => {
    const priceEl = priceRef.current
    const volumeEl = volumeRef.current
    if (!data || !priceEl || !volumeEl) return

    const p = data.prices
    const dates = p.map((x) => x.date)
    const base = {
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: { color: '#cbd5e1' },
      margin: { l: 55, r: 20, t: 40, b: 30 },
      xaxis: { rangeslider: { visible: false }, gridcolor: '#1e293b' },
      yaxis: { gridcolor: '#1e293b' },
    }
    const config = { responsive: true, displaylogo: false }

    Plotly.newPlot(
      priceEl,
      [
        {
          type: 'candlestick',
          x: dates,
          open: p.map((x) => x.open),
          high: p.map((x) => x.high),
          low: p.map((x) => x.low),
          close: p.map((x) => x.close),
          increasing: { line: { color: '#34d399' } },
          decreasing: { line: { color: '#f87171' } },
        },
      ],
      { ...base, title: { text: `${data.symbol} price (${data.period})` }, height: 380 },
      config,
    )
    Plotly.newPlot(
      volumeEl,
      [{ type: 'bar', x: dates, y: p.map((x) => x.volume), marker: { color: '#475569' } }],
      { ...base, title: { text: 'Volume' }, height: 200 },
      config,
    )

    return () => {
      Plotly.purge(priceEl)
      Plotly.purge(volumeEl)
    }
  }, [data])

  let stats = null
  if (data && data.prices.length > 0) {
    const p = data.prices
    const first = p[0].close
    const last = p[p.length - 1].close
    const change = ((last - first) / first) * 100
    stats = {
      last,
      change,
      high: Math.max(...p.map((x) => x.high)),
      low: Math.min(...p.map((x) => x.low)),
    }
  }

  const inputClass =
    'flex-1 min-w-0 rounded-lg bg-slate-900 border border-slate-600 px-3 py-2 text-slate-100 focus:outline-none focus:border-emerald-400'

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <Navbar />
      <main className="max-w-6xl mx-auto px-6 py-10">
        <h1 className="text-3xl font-bold">Market Data</h1>
        <p className="mt-2 text-slate-400">
          Search a company by name or ticker. Data comes from Yahoo Finance.
        </p>

        <form onSubmit={handleSearch} className="mt-6 flex gap-2 max-w-xl">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Apple, TCS, Reliance"
            className={inputClass}
          />
          <button
            type="submit"
            disabled={searching}
            className="rounded-lg bg-emerald-500 px-5 py-2 font-semibold text-slate-900 hover:bg-emerald-400 disabled:opacity-60"
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </form>

        {results.length > 0 && (
          <ul className="mt-3 max-w-xl rounded-xl bg-slate-800 divide-y divide-slate-700">
            {results.map((r) => (
              <li key={r.symbol}>
                <button
                  onClick={() => selectStock(r)}
                  className="w-full text-left px-4 py-3 hover:bg-slate-700 flex justify-between"
                >
                  <span>
                    <span className="font-semibold">{r.symbol}</span>
                    <span className="ml-2 text-slate-400">{r.name}</span>
                  </span>
                  <span className="text-xs text-slate-500">{r.exchange}</span>
                </button>
              </li>
            ))}
          </ul>
        )}

        {error && (
          <p className="mt-4 max-w-xl rounded-lg bg-red-500/10 border border-red-500/40 px-4 py-2 text-sm text-red-300">
            {error}
          </p>
        )}

        {selected && (
          <section className="mt-8">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-xl font-semibold">
                <span className="text-emerald-400">{selected.symbol}</span>
                <span className="ml-2 text-slate-400">{selected.name}</span>
                <span className="ml-2 text-xs text-slate-500">{selected.market}</span>
              </h2>
              <div className="flex gap-2">
                {PERIODS.map((p) => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={`rounded-md px-3 py-1 text-sm ${
                      period === p
                        ? 'bg-emerald-500 text-slate-900 font-semibold'
                        : 'border border-slate-600 hover:bg-slate-800'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>

            {loading && <p className="mt-6 text-slate-500">Loading data...</p>}
            
            {data && !loading && (
              <>
                {stats && (
                  <div className="mt-6 grid gap-4 sm:grid-cols-4">
                    <div className="rounded-xl bg-slate-800 p-4">
                      <p className="text-xs text-slate-500">Latest close</p>
                      <p className="text-xl font-semibold">{stats.last.toFixed(2)}</p>
                    </div>
                    <div className="rounded-xl bg-slate-800 p-4">
                      <p className="text-xs text-slate-500">Change over period</p>
                      <p className={`text-xl font-semibold ${stats.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {stats.change >= 0 ? '+' : ''}{stats.change.toFixed(2)}%
                      </p>
                    </div>
                    <div className="rounded-xl bg-slate-800 p-4">
                      <p className="text-xs text-slate-500">Period high</p>
                      <p className="text-xl font-semibold">{stats.high.toFixed(2)}</p>
                    </div>
                    <div className="rounded-xl bg-slate-800 p-4">
                      <p className="text-xs text-slate-500">Period low</p>
                      <p className="text-xl font-semibold">{stats.low.toFixed(2)}</p>
                    </div>
                  </div>
                )}

                <div className="mt-6 rounded-xl bg-slate-800 p-4">
                  <div ref={priceRef} />
                  <div ref={volumeRef} />
                </div>

                <div className="mt-6 rounded-xl bg-slate-800 p-4 text-sm text-slate-400 space-y-1">
                  <p>
                    <span className="text-slate-300">Source:</span> {data.source}
                  </p>
                  <p>
                    <span className="text-slate-300">Retrieved:</span>{' '}
                    {new Date(data.retrieved_at).toLocaleString()}
                  </p>
                  <p>
                    <span className="text-slate-300">Data validation:</span>{' '}
                    {data.validation.rows_received} rows received, {data.validation.rows_returned} kept
                    ({data.validation.duplicates_removed} duplicate dates,{' '}
                    {data.validation.missing_removed} missing values,{' '}
                    {data.validation.inconsistent_removed} inconsistent rows removed)
                  </p>
                </div>

                <div className="mt-6 overflow-x-auto rounded-xl bg-slate-800 p-4">
                  <h3 className="mb-2 font-semibold text-emerald-400">Latest prices (OHLCV)</h3>
                  <table className="w-full text-sm">
                    <thead className="text-left text-slate-500">
                      <tr>
                        <th className="py-1">Date</th>
                        <th>Open</th>
                        <th>High</th>
                        <th>Low</th>
                        <th>Close</th>
                        <th>Volume</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.prices.slice(-10).reverse().map((r) => (
                        <tr key={r.date} className="border-t border-slate-700">
                          <td className="py-1">{r.date}</td>
                          <td>{r.open}</td>
                          <td>{r.high}</td>
                          <td>{r.low}</td>
                          <td>{r.close}</td>
                          <td>{r.volume.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}

            <CompanyInfo symbol={selected.symbol} market={selected.market} />
          </section>
        )}
      </main>
    </div>
  )
}