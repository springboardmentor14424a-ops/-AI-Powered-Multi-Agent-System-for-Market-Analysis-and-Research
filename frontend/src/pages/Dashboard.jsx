import { useState } from 'react'
import Navbar from '../components/Navbar'
import ResearchHistory from '../components/ResearchHistory'
import Watchlist from '../components/Watchlist'
import Preferences from '../components/Preferences'
import { useAuth } from '../context/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <Navbar />

      <main className="max-w-6xl mx-auto px-6 py-10">
        <h1 className="text-3xl font-bold">Welcome, {user.full_name}</h1>
        <p className="mt-2 text-slate-400">
          Search a stock, save it to your watchlist, and revisit your past research.
        </p>

        <section className="mt-10 grid gap-6 md:grid-cols-3 items-start">
          <ResearchHistory refreshKey={refreshKey} />
          <Watchlist onResearchStarted={() => setRefreshKey((k) => k + 1)} />
          <Preferences />
        </section>
      </main>
    </div>
  )
}