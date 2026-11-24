import { useEffect, useState } from 'react'
import api, { getErrorMessage } from '../api'

const MARKETS = [
  { value: 'NSE', label: 'NSE – National Stock Exchange of India' },
  { value: 'BSE', label: 'BSE – BSE Ltd., India' },
  { value: 'NASDAQ', label: 'NASDAQ – US exchange' },
  { value: 'NYSE', label: 'NYSE – New York Stock Exchange' },
]

const PERIODS = [
  { value: '1M', label: '1 Month' },
  { value: '3M', label: '3 Months' },
  { value: '6M', label: '6 Months' },
  { value: '1Y', label: '1 Year' },
  { value: '5Y', label: '5 Years' },
]

export default function Preferences() {
  const [prefs, setPrefs] = useState({ market: 'NSE', default_period: '1Y' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    api
      .get('/preferences')
      .then((res) => setPrefs(res.data))
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [])

  function handleChange(e) {
    setPrefs({ ...prefs, [e.target.name]: e.target.value })
    setMessage('')
  }

  async function handleSave(e) {
    e.preventDefault()
    setError('')
    setMessage('')
    setSaving(true)
    try {
      const res = await api.put('/preferences', prefs)
      setPrefs(res.data)
      setMessage('Preferences saved')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const selectClass =
    'w-full rounded-lg bg-slate-900 border border-slate-600 px-3 py-2 text-slate-100 focus:outline-none focus:border-emerald-400'

  return (
    <div className="rounded-xl bg-slate-800 p-6">
      <h2 className="text-lg font-semibold text-emerald-400">Preferences</h2>

      {loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading...</p>
      ) : (
        <form onSubmit={handleSave} className="mt-4 space-y-4">
          <div>
            <label className="block mb-1 text-sm text-slate-400">Market</label>
            <select name="market" value={prefs.market} onChange={handleChange} className={selectClass}>
              {MARKETS.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block mb-1 text-sm text-slate-400">Default analysis period</label>
            <select name="default_period" value={prefs.default_period} onChange={handleChange} className={selectClass}>
              {PERIODS.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>

          {error && (
            <p className="rounded-lg bg-red-500/10 border border-red-500/40 px-3 py-2 text-sm text-red-300">
              {error}
            </p>
          )}
          {message && (
            <p className="rounded-lg bg-emerald-500/10 border border-emerald-500/40 px-3 py-2 text-sm text-emerald-300">
              {message}
            </p>
          )}

          <button
            type="submit"
            disabled={saving}
            className="w-full rounded-lg bg-emerald-500 py-2 font-semibold text-slate-900 hover:bg-emerald-400 disabled:opacity-60"
          >
            {saving ? 'Saving...' : 'Save preferences'}
          </button>
        </form>
      )}
    </div>
  )
}