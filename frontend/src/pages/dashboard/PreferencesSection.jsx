
import { useEffect, useState } from 'react'
import { Settings, Save } from 'lucide-react'
import api from '../../services/api'
import { useAuth } from '../../context/AuthContext'

const markets = ['NSE', 'BSE', 'NASDAQ', 'NYSE']

const periods = [
  { value: '1mo', label: '1 Month' },
  { value: '3mo', label: '3 Months' },
  { value: '6mo', label: '6 Months' },
  { value: '1y', label: '1 Year' },
  { value: '5y', label: '5 Years' },
]

function PreferencesSection() {
  const { token } = useAuth()

  const [market, setMarket] = useState('NSE')
  const [period, setPeriod] = useState('1y')
  const [preferenceExists, setPreferenceExists] = useState(false)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const headers = {
    Authorization: `Bearer ${token}`,
  }

  useEffect(() => {
    const loadPreferences = async () => {
      try {
        setLoading(true)
        setError('')

        const response = await api.get('/preferences/', { headers })

        setMarket(response.data.preferred_market)
        setPeriod(response.data.default_analysis_period)
        setPreferenceExists(true)
      } catch (err) {
        if (err.response?.status === 404) {
          // No saved preferences: use the schema defaults.
          setMarket('NSE')
          setPeriod('1y')
          setPreferenceExists(false)
        } else {
          setError(
            err.response?.data?.detail ||
            'Unable to load preferences.'
          )
        }
      } finally {
        setLoading(false)
      }
    }

    if (token) {
      loadPreferences()
    } else {
      setLoading(false)
    }
  }, [token])

  const handleSave = async (event) => {
    event.preventDefault()

    try {
      setSaving(true)
      setMessage('')
      setError('')

      const payload = {
        preferred_market: market,
        default_analysis_period: period,
      }

      if (preferenceExists) {
        await api.put('/preferences/', payload, { headers })
      } else {
        await api.post('/preferences/', payload, { headers })
      }

      setPreferenceExists(true)
      setMessage('Your preferences have been saved successfully.')
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to save preferences.'
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <section
      id="preferences"
      className="bg-slate-900 border border-slate-800 rounded-xl p-6 md:p-8 mt-8"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 rounded-lg bg-cyan-500/10">
          <Settings className="text-cyan-400" size={23} />
        </div>

        <div>
          <h2 className="text-xl font-semibold">
            User Preferences
          </h2>
          <p className="text-sm text-slate-400">
            Customize your preferred stock market and analysis period.
          </p>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-slate-400">
          Loading your preferences...
        </p>
      ) : (
        <form onSubmit={handleSave} className="space-y-6">
          <div>
            <label
              htmlFor="preferred-market"
              className="block text-sm font-medium text-slate-300 mb-2"
            >
              Preferred Market
            </label>

            <select
              id="preferred-market"
              value={market}
              onChange={(event) => setMarket(event.target.value)}
              className="w-full rounded-lg bg-slate-950 border border-slate-700 px-4 py-3 text-white outline-none focus:border-cyan-500"
            >
              {markets.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="analysis-period"
              className="block text-sm font-medium text-slate-300 mb-2"
            >
              Default Analysis Period
            </label>

            <select
              id="analysis-period"
              value={period}
              onChange={(event) => setPeriod(event.target.value)}
              className="w-full rounded-lg bg-slate-950 border border-slate-700 px-4 py-3 text-white outline-none focus:border-cyan-500"
            >
              {periods.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          {message && (
            <p role="status" className="text-sm text-emerald-400">
              {message}
            </p>
          )}

          {error && (
            <p role="alert" className="text-sm text-red-400">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-cyan-500 px-5 py-3 font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50 transition"
          >
            <Save size={18} />
            {saving ? 'Saving...' : 'Save Preferences'}
          </button>
        </form>
      )}
    </section>
  )
}

export default PreferencesSection
