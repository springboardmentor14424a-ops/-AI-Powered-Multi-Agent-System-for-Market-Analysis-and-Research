import Navbar from '../components/Navbar'
import { useAuth } from '../context/AuthContext'

const cards = [
  {
    title: 'Research History',
    text: 'Your past stock research reports will appear here.',
  },
  {
    title: 'Watchlist',
    text: 'Stocks you save to monitor will appear here.',
  },
  {
    title: 'Preferences',
    text: 'Choose your market (NSE, BSE, NASDAQ, NYSE) and default analysis period.',
  },
]

export default function Dashboard() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <Navbar />

      <main className="max-w-6xl mx-auto px-6 py-10">
        <h1 className="text-3xl font-bold">Welcome, {user.full_name}</h1>
        <p className="mt-2 text-slate-400">
          Search a stock, save it to your watchlist, and revisit your past research.
        </p>

        <section className="mt-10 grid gap-6 md:grid-cols-3">
          {cards.map((c) => (
            <div key={c.title} className="rounded-xl bg-slate-800 p-6">
              <h2 className="text-lg font-semibold text-emerald-400">{c.title}</h2>
              <p className="mt-2 text-slate-400">{c.text}</p>
              <p className="mt-4 text-sm text-slate-500">Coming soon</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  )
}