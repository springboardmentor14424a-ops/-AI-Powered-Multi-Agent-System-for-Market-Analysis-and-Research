import Navbar from '../components/Navbar'
import Watchlist from '../components/Watchlist'
import { useAuth } from '../context/AuthContext'

function PlaceholderCard({ title, text }) {
  return (
    <div className="rounded-xl bg-slate-800 p-6">
      <h2 className="text-lg font-semibold text-emerald-400">{title}</h2>
      <p className="mt-2 text-slate-400">{text}</p>
      <p className="mt-4 text-sm text-slate-500">Coming soon</p>
    </div>
  )
}

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

        <section className="mt-10 grid gap-6 md:grid-cols-3 items-start">
          <PlaceholderCard
            title="Research History"
            text="Your past stock research reports will appear here."
          />
          <Watchlist />
          <PlaceholderCard
            title="Preferences"
            text="Choose your market (NSE, BSE, NASDAQ, NYSE) and default analysis period."
          />
        </section>
      </main>
    </div>
  )
}