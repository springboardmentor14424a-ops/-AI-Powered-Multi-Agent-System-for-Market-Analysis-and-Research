import { useEffect, useState } from 'react'
import api, { getErrorMessage } from '../api'

const compact = new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 2 })

const fmt = (v) => (v === null || v === undefined ? '—' : compact.format(v))
const num = (v) => (v === null || v === undefined ? '—' : Number(v).toFixed(2))
const pct = (v) => (v === null || v === undefined ? '—' : `${(v * 100).toFixed(2)}%`)

const STATEMENTS = [
  { key: 'income_statement', label: 'Income statement' },
  { key: 'balance_sheet', label: 'Balance sheet' },
  { key: 'cash_flow', label: 'Cash flow' },
]

export default function CompanyInfo({ symbol, market }) {
  const [profile, setProfile] = useState(null)
  const [fin, setFin] = useState(null)
  const [sources, setSources] = useState([])
  const [tab, setTab] = useState('income_statement')
  const [loading, setLoading] = useState(true)
  const [profileError, setProfileError] = useState('')
  const [finError, setFinError] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setProfile(null)
    setFin(null)
    setProfileError('')
    setFinError('')

    const path = `/stocks/${encodeURIComponent(symbol)}`
    const params = { market }

    Promise.allSettled([
      api.get(`${path}/profile`, { params }),
      api.get(`${path}/financials`, { params }),
    ]).then(async ([p, f]) => {
      if (cancelled) return
      if (p.status === 'fulfilled') setProfile(p.value.data)
      else setProfileError(getErrorMessage(p.reason))
      if (f.status === 'fulfilled') setFin(f.value.data)
      else setFinError(getErrorMessage(f.reason))
      try {
        const s = await api.get('/stocks/sources/log')
        if (!cancelled) setSources(s.data)
      } catch {
        /* the log is optional */
      }
      if (!cancelled) setLoading(false)
    })

    return () => {
      cancelled = true
    }
  }, [symbol, market])

  if (loading) {
    return <p className="mt-8 text-slate-500">Loading company details...</p>
  }

  const p = profile?.profile
  const table = fin?.[tab]

  return (
    <div className="mt-8 space-y-6">
      <div className="rounded-xl bg-slate-800 p-6">
        <h3 className="text-lg font-semibold text-emerald-400">Company profile</h3>
        {profileError && <p className="mt-3 text-sm text-red-300">{profileError}</p>}
        {p && (
          <>
            <p className="mt-2 text-xl font-semibold">{p.name}</p>
            <p className="text-sm text-slate-400">
              {[p.sector, p.industry, p.country].filter(Boolean).join(' · ') || '—'}
            </p>

            <div className="mt-4 grid gap-4 sm:grid-cols-3 lg:grid-cols-6">
              {[
                ['Market cap', fmt(p.market_cap)],
                ['P/E (trailing)', num(p.trailing_pe)],
                ['P/B', num(p.price_to_book)],
                ['ROE', pct(p.return_on_equity)],
                ['52-week high', num(p.week_52_high)],
                ['52-week low', num(p.week_52_low)],
              ].map(([label, value]) => (
                <div key={label} className="rounded-lg bg-slate-900 p-3">
                  <p className="text-xs text-slate-500">{label}</p>
                  <p className="text-lg font-semibold">{value}</p>
                </div>
              ))}
            </div>

            {p.summary && (
              <p className="mt-4 text-sm text-slate-400 leading-relaxed">{p.summary}</p>
            )}
            <p className="mt-3 text-xs text-slate-500">
              {p.exchange && <span>{p.exchange} · </span>}
              {p.currency && <span>{p.currency} · </span>}
              {p.employees && <span>{p.employees.toLocaleString()} employees · </span>}
              {p.website && (
                <a href={p.website} target="_blank" rel="noreferrer" className="text-emerald-400 hover:underline">
                  {p.website}
                </a>
              )}
            </p>
            <p className="mt-2 text-xs text-slate-500">
              Ratios are as reported by {profile.source}, retrieved{' '}
              {new Date(profile.retrieved_at).toLocaleString()}.
            </p>
          </>
        )}
      </div>

      <div className="rounded-xl bg-slate-800 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-lg font-semibold text-emerald-400">Financial statements (annual)</h3>
          <div className="flex gap-2">
            {STATEMENTS.map((s) => (
              <button
                key={s.key}
                onClick={() => setTab(s.key)}
                className={`rounded-md px-3 py-1 text-sm ${
                  tab === s.key
                    ? 'bg-emerald-500 text-slate-900 font-semibold'
                    : 'border border-slate-600 hover:bg-slate-700'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {finError && <p className="mt-3 text-sm text-red-300">{finError}</p>}

        {table && table.rows.length > 0 && (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-slate-500">
                <tr>
                  <th className="py-1 pr-4">Item</th>
                  {table.periods.map((d) => (
                    <th key={d} className="pr-4">{d}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.map((r) => (
                  <tr key={r.item} className="border-t border-slate-700">
                    <td className="py-1 pr-4 text-slate-300">{r.item}</td>
                    {r.values.map((v, i) => (
                      <td key={i} className="pr-4">{fmt(v)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {table && table.rows.length === 0 && (
          <p className="mt-4 text-sm text-slate-500">
            This statement is not available from the provider for this company.
          </p>
        )}

        {fin && (
          <p className="mt-3 text-xs text-slate-500">
            {fin.currency && <span>Currency: {fin.currency}. </span>}
            Source: {fin.source}, retrieved {new Date(fin.retrieved_at).toLocaleString()}.
            {fin.notes.map((n) => (
              <span key={n}> {n}</span>
            ))}
          </p>
        )}
      </div>

      {sources.length > 0 && (
        <div className="rounded-xl bg-slate-800 p-6">
          <h3 className="text-lg font-semibold text-emerald-400">Data source log</h3>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-slate-500">
                <tr>
                  <th className="py-1 pr-4">Type</th>
                  <th className="pr-4">Source</th>
                  <th className="pr-4">Retrieved</th>
                  <th>Hash</th>
                </tr>
              </thead>
              <tbody>
                {sources.slice(0, 8).map((s) => (
                  <tr key={s.source_id} className="border-t border-slate-700">
                    <td className="py-1 pr-4 text-slate-300">{s.source_type}</td>
                    <td className="pr-4">
                      {s.source_url ? (
                        <a href={s.source_url} target="_blank" rel="noreferrer" className="text-emerald-400 hover:underline">
                          {s.title}
                        </a>
                      ) : (
                        s.title
                      )}
                    </td>
                    <td className="pr-4">{new Date(s.retrieved_at).toLocaleString()}</td>
                    <td className="font-mono text-xs text-slate-500">{s.content_hash.slice(0, 10)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}