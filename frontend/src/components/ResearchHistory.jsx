import { useEffect, useState } from 'react'
import api, { getErrorMessage } from '../api'

const STATUS_STYLES = {
  Pending: 'bg-slate-700 text-slate-300',
  Processing: 'bg-amber-500/20 text-amber-300',
  Completed: 'bg-emerald-500/20 text-emerald-300',
  Failed: 'bg-red-500/20 text-red-300',
}

export default function ResearchHistory({ refreshKey }) {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get('/research')
      .then((res) => {
        setTasks(res.data)
        setError('')
      })
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [refreshKey])

  return (
    <div className="rounded-xl bg-slate-800 p-6">
      <h2 className="text-lg font-semibold text-emerald-400">Research History</h2>

      {error && (
        <p className="mt-3 rounded-lg bg-red-500/10 border border-red-500/40 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      <ul className="mt-4 space-y-2">
        {loading && <li className="text-slate-500 text-sm">Loading...</li>}
        {!loading && tasks.length === 0 && (
          <li className="text-slate-500 text-sm">
            No research yet. Click Research on a saved stock.
          </li>
        )}
        {tasks.map((t) => (
          <li key={t.task_id} className="rounded-lg bg-slate-900 px-3 py-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold">{t.ticker}</span>
              <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS_STYLES[t.status] || STATUS_STYLES.Pending}`}>
                {t.status}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              {t.market} · {t.requested_period} · {new Date(t.created_at).toLocaleString()}
            </p>
            <button
              disabled={t.status !== 'Completed'}
              className="mt-2 rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-500 cursor-not-allowed"
            >
              Open report
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}