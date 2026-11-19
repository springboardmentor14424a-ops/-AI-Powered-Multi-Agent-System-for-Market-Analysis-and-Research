import { Link } from 'react-router-dom'

const APP_NAME = 'Multi-Agent Stock Analyst'

const features = [
  {
    title: 'Specialized AI agents',
    text: 'Fundamental, technical, news and risk agents each research a stock from their own angle.',
  },
  {
    title: 'One clear report',
    text: 'A supervisor combines every finding into a single report with sources and timestamps.',
  },
  {
    title: 'Your research workspace',
    text: 'Save stocks to a watchlist, set your market and period, and revisit past research.',
  },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <nav className="flex items-center justify-between px-6 py-4 max-w-6xl mx-auto">
        <span className="text-lg font-bold text-emerald-400">{APP_NAME}</span>
        <div className="flex gap-3">
          <Link to="/login" className="px-4 py-2 rounded-lg border border-slate-600 hover:bg-slate-800">
            Sign In
          </Link>
          <Link to="/register" className="px-4 py-2 rounded-lg bg-emerald-500 text-slate-900 font-semibold hover:bg-emerald-400">
            Sign Up
          </Link>
        </div>
      </nav>

      <header className="max-w-3xl mx-auto text-center px-6 py-24">
        <h1 className="text-4xl sm:text-5xl font-bold leading-tight">
          Research any stock with a team of AI agents
        </h1>
        <p className="mt-6 text-lg text-slate-400">
          Fundamentals, price trends, news sentiment and risk, combined into one
          report you can trust and trace back to its sources.
        </p>
        <Link to="/register" className="inline-block mt-10 px-8 py-3 rounded-lg bg-emerald-500 text-slate-900 font-semibold hover:bg-emerald-400">
          Get Started
        </Link>
      </header>

      <section className="max-w-6xl mx-auto px-6 pb-24 grid gap-6 sm:grid-cols-3">
        {features.map((f) => (
          <div key={f.title} className="rounded-xl bg-slate-800 p-6">
            <h3 className="text-lg font-semibold text-emerald-400">{f.title}</h3>
            <p className="mt-2 text-slate-400">{f.text}</p>
          </div>
        ))}
      </section>
    </div>
  )
}