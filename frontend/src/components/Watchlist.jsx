import { useEffect, useState } from 'react'
import api, { getErrorMessage } from '../api'

export default function Watchlist() {
  const [items, setItems] = useState([])
  const [ticker, setTicker] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [adding, setAdding] = useState(false)

  async function loadItems() {
    try {
      const res = await api.get('/watchlist')
      setItems(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadItems()
  }, [])

  async function handleAdd(e) {
    e.preventDefault()
    setError('')
    if (!ticker.trim()) return
    setAdding(true)
    try {
      const res = await api.post('/watchlist', { ticker })
      setItems([res.data, ...items])
      setTicker('')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setAdding(false)
    }
  }

  async function handleRemove(id) {
    setError('')
    try {
      await api.delete(`/watchlist/${id}`)
      setItems(items.filter((item) => item.saved_stock_id !== id))
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="rounded-xl bg-slate-800 p-6">
      <h2 className="text-lg font-semibold text-emerald-400">Watchlist</h2>

      <form onSubmit={handleAdd} className="mt-4 flex gap-2">
        <input
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="Ticker, e.g. AAPL"
          className="flex-1 min-w-0 rounded-lg bg-slate-900 border border-slate-600 px-3 py-2 text-slate-100 focus:outline-none focus:border-emerald-400"
        />
        <button
          type="submit"
          disabled={adding}
          className="rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-slate-900 hover:bg-emerald-400 disabled:opacity-60"
        >
          Add
        </button>
      </form>

      {error && (
        <p className="mt-3 rounded-lg bg-red-500/10 border border-red-500/40 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      <ul className="mt-4 space-y-2">
        {loading && <li className="text-slate-500 text-sm">Loading...</li>}
        {!loading && items.length === 0 && (
          <li className="text-slate-500 text-sm">No saved stocks yet. Add one above.</li>
        )}
        {items.map((item) => (
          <li
            key={item.saved_stock_id}
            className="flex items-center justify-between rounded-lg bg-slate-900 px-3 py-2"
          >
            <span className="font-semibold">{item.ticker}</span>
            <div className="flex gap-2">
              <button
                disabled
                title="Research opens in a later module"
                className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-500 cursor-not-allowed"
              >
                Research
              </button>
              <button
                onClick={() => handleRemove(item.saved_stock_id)}
                className="rounded-md border border-slate-600 px-2 py-1 text-xs hover:bg-slate-800"
              >
                Remove
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}