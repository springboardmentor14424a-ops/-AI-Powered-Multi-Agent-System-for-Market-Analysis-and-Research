import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import {
  Activity,
  LayoutDashboard,
  Search,
  Bookmark,
  History,
  Settings,
  LogOut,
  Bell,
  TrendingUp,
  BarChart3,
  UserCircle,
  ArrowUpRight,
} from 'lucide-react'

import { useAuth } from '../../context/AuthContext'
import api from '../../services/api'
import PreferencesSection from './PreferencesSection'

function Dashboard() {
  const { user, token, logout } = useAuth()
  const navigate = useNavigate()

  const [watchlist, setWatchlist] = useState([])
  const [watchlistLoading, setWatchlistLoading] = useState(true)
  const [watchlistError, setWatchlistError] = useState('')

  const [stockTicker, setStockTicker] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchMarket, setSearchMarket] = useState('NSE')
  const [companyResults, setCompanyResults] = useState([])
  const [searchingCompanies, setSearchingCompanies] = useState(false)
  const [companySearchError, setCompanySearchError] = useState('')
  const [addingStock, setAddingStock] = useState(false)
  const [stockActionMessage, setStockActionMessage] = useState('')
  const [stockActionError, setStockActionError] = useState('')
  const [removingStockId, setRemovingStockId] = useState(null)

  const [startingResearch, setStartingResearch] = useState(false)
  const [researchActionMessage, setResearchActionMessage] = useState('')
  const [researchActionError, setResearchActionError] = useState('')

  const [researchHistory, setResearchHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const [historyError, setHistoryError] = useState('')

  // Fetch Watchlist
  useEffect(() => {
    const fetchWatchlist = async () => {
      try {
        setWatchlistLoading(true)
        setWatchlistError('')

        const response = await api.get('/watchlist/', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        setWatchlist(
          Array.isArray(response.data) ? response.data : []
        )
      } catch (error) {
        console.error('Watchlist error:', error)
        setWatchlistError(
          error.response?.data?.detail || 'Unable to load watchlist.'
        )
      } finally {
        setWatchlistLoading(false)
      }
    }

    if (token) {
      fetchWatchlist()
    } else {
      setWatchlistLoading(false)
    }
  }, [token])

  // Fetch Research History
  useEffect(() => {
    const fetchResearchHistory = async () => {
      try {
        setHistoryLoading(true)
        setHistoryError('')

        const response = await api.get('/research/history', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        setResearchHistory(
          Array.isArray(response.data) ? response.data : []
        )
      } catch (error) {
        console.error('Research history error:', error)
        setHistoryError(
          error.response?.data?.detail || 'Unable to load research history.'
        )
      } finally {
        setHistoryLoading(false)
      }
    }

    if (token) {
      fetchResearchHistory()
    } else {
      setHistoryLoading(false)
    }
  }, [token])

  // Search companies by name or ticker using the Stock Search API
  const handleCompanySearch = async (event) => {
    event.preventDefault()

    const query = searchQuery.trim()
    if (!query) {
      setCompanySearchError('Enter a company name or ticker to search.')
      setCompanyResults([])
      return
    }

    try {
      setSearchingCompanies(true)
      setCompanySearchError('')
      setCompanyResults([])

      const response = await api.get('/stocks/search', {
        params: {
          query,
          market: searchMarket,
          max_results: 10,
        },
      })

      const results = response.data?.results
      setCompanyResults(Array.isArray(results) ? results : [])

      if (!Array.isArray(results) || results.length === 0) {
        setCompanySearchError('No companies found. Try another company name or market.')
      }
    } catch (error) {
      console.error('Company search error:', error)
      setCompanySearchError(
        error.response?.data?.detail || 'Unable to search companies. Please try again.'
      )
    } finally {
      setSearchingCompanies(false)
    }
  }

  // Select a search result for watchlist or research actions
  const handleSelectCompany = (company) => {
    setStockTicker(company.symbol)
    setStockActionError('')
    setStockActionMessage('')
    setResearchActionError('')
    setResearchActionMessage('')
    setCompanySearchError('')
  }

  // Add stock to watchlist
  const handleAddStock = async (event) => {
    event.preventDefault()

    const ticker = stockTicker.trim().toUpperCase()

    if (!ticker) {
      setStockActionError('Please enter a stock ticker.')
      setStockActionMessage('')
      return
    }

    if (!/^[A-Z0-9.^=_-]{1,20}$/.test(ticker)) {
      setStockActionError(
        'Enter a valid ticker, for example TCS.NS or AAPL.'
      )
      setStockActionMessage('')
      return
    }

    try {
      setAddingStock(true)
      setStockActionError('')
      setStockActionMessage('')

      await api.post('/watchlist/add', null, {
        params: { ticker },
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      const response = await api.get('/watchlist/', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      setWatchlist(
        Array.isArray(response.data) ? response.data : []
      )

      setStockTicker('')
      setStockActionMessage(`${ticker} added to your watchlist.`)
    } catch (error) {
      console.error('Add stock error:', error)

      setStockActionError(
        error.response?.data?.detail || 'Unable to add this stock.'
      )
    } finally {
      setAddingStock(false)
    }
  }

  // Start stock research using the user's saved preferences
  const handleStartResearch = async () => {
    const ticker = stockTicker.trim().toUpperCase()

    if (!ticker) {
      setResearchActionError('Please enter a stock ticker before starting research.')
      setResearchActionMessage('')
      return
    }

    if (!/^[A-Z0-9.^=_-]{1,20}$/.test(ticker)) {
      setResearchActionError(
        'Enter a valid ticker, for example TCS.NS or AAPL.'
      )
      setResearchActionMessage('')
      return
    }

    try {
      setStartingResearch(true)
      setResearchActionError('')
      setResearchActionMessage('')

      const headers = {
        Authorization: `Bearer ${token}`,
      }

      // Read the user's saved market and analysis period.
      // Use the application defaults if no preferences have been saved.
      let preferredMarket = 'NSE'
      let preferredPeriod = '1y'

      try {
        const preferencesResponse = await api.get('/preferences/', { headers })
        preferredMarket =
          preferencesResponse.data?.preferred_market || preferredMarket
        preferredPeriod =
          preferencesResponse.data?.default_analysis_period || preferredPeriod
      } catch (preferenceError) {
        if (preferenceError.response?.status !== 404) {
          throw preferenceError
        }
      }

      // Create the research task in the database.
      const createResponse = await api.post(
        '/research/',
        {
          ticker,
          market: preferredMarket,
          requested_period: preferredPeriod,
        },
        { headers }
      )

      const taskId = createResponse.data?.task_id

      if (!taskId) {
        throw new Error('The research task was created, but no task ID was returned.')
      }

      // Execute the newly created research task.
      await api.post(`/research/${taskId}/execute`, {}, { headers })

      // Reload research history so the new task appears immediately.
      const historyResponse = await api.get('/research/history', { headers })
      setResearchHistory(
        Array.isArray(historyResponse.data) ? historyResponse.data : []
      )

      setResearchActionMessage(
        `Research for ${ticker} finished. Your task is now in Research History.`
      )
      setStockTicker('')
    } catch (error) {
      console.error('Start research error:', error)

      // Refresh history even if execution fails, because the task may
      // already have been created and marked as Failed by the backend.
      try {
        const historyResponse = await api.get('/research/history', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        setResearchHistory(
          Array.isArray(historyResponse.data) ? historyResponse.data : []
        )
      } catch (historyRefreshError) {
        console.error('Research history refresh error:', historyRefreshError)
      }

      setResearchActionError(
        error.response?.data?.detail ||
        error.message ||
        'Unable to start stock research.'
      )
    } finally {
      setStartingResearch(false)
    }
  }

  // Remove stock from watchlist
  const handleRemoveStock = async (savedStockId, ticker) => {
    try {
      setRemovingStockId(savedStockId)
      setStockActionError('')
      setStockActionMessage('')

      await api.delete(`/watchlist/${savedStockId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      setWatchlist((currentStocks) =>
        currentStocks.filter(
          (stock) => stock.saved_stock_id !== savedStockId
        )
      )

      setStockActionMessage(`${ticker} removed from your watchlist.`)
    } catch (error) {
      console.error('Remove stock error:', error)

      setStockActionError(
        error.response?.data?.detail || 'Unable to remove this stock.'
      )
    } finally {
      setRemovingStockId(null)
    }
  }

  // Logout
  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  // Stock details route for watchlist entries
  const getStockDetailsPath = (ticker) =>
    `/stock/${encodeURIComponent(ticker)}`

  // Build the correct Yahoo Finance symbol for a research-history task.
  // NSE tickers need .NS and BSE tickers need .BO.
  const getResearchStockDetailsPath = (task) => {
    let ticker = (task.ticker || '').trim().toUpperCase()

    if (!ticker || ticker.includes('.') || ticker.startsWith('^')) {
      return getStockDetailsPath(ticker)
    }

    if (task.market === 'NSE') {
      ticker = `${ticker}.NS`
    } else if (task.market === 'BSE') {
      ticker = `${ticker}.BO`
    }

    return getStockDetailsPath(ticker)
  }

  // Sidebar menu
  const menuItems = [
    {
      name: 'Dashboard',
      icon: LayoutDashboard,
      active: true,
      href: '#overview',
    },
    {
      name: 'Stock Search',
      icon: Search,
      href: '#stock-search',
    },
    {
      name: 'My Watchlist',
      icon: Bookmark,
      href: '#watchlist',
    },
    {
      name: 'Research History',
      icon: History,
      href: '#history',
    },
    {
      name: 'Preferences',
      icon: Settings,
      href: '#preferences',
    },
  ]

  // Dashboard statistics
  const stats = [
    {
      title: 'Research Tasks',
      value: historyLoading
        ? '...'
        : historyError
          ? '—'
          : researchHistory.length,
      description: 'Your research tasks',
      icon: BarChart3,
    },
    {
      title: 'Saved Stocks',
      value: watchlistLoading
        ? '...'
        : watchlistError
          ? '—'
          : watchlist.length,
      description: 'Stocks in your watchlist',
      icon: Bookmark,
    },
    {
      title: 'Market Coverage',
      value: '4',
      description: 'NSE · BSE · NASDAQ · NYSE',
      icon: TrendingUp,
    },
  ]

  return (
    <div className="min-h-screen bg-slate-950 text-white flex">

      {/* Sidebar */}
      <aside className="hidden md:flex w-64 flex-col bg-slate-900 border-r border-slate-800 fixed inset-y-0 left-0">

        <div className="h-20 flex items-center gap-3 px-6 border-b border-slate-800">
          <div className="bg-cyan-500/10 p-2 rounded-lg">
            <Activity className="text-cyan-400" size={25} />
          </div>

          <div>
            <h1 className="font-bold text-white">Multi-Agent</h1>
            <p className="text-xs text-cyan-400">Stock Research</p>
          </div>
        </div>

        {/* Navigation */}
        <div className="px-4 py-6">
          <p className="text-xs uppercase tracking-wider text-slate-500 mb-4 px-3">
            Workspace
          </p>

          <nav className="space-y-2">
            {menuItems.map((item) => {
              const Icon = item.icon

              return (
                <a
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition ${
                    item.active
                      ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon size={19} />
                  {item.name}
                </a>
              )
            })}
          </nav>
        </div>

        {/* User Profile */}
        <div className="mt-auto p-4 border-t border-slate-800">
          <div className="flex items-center gap-3 px-2 py-3">
            <div className="w-10 h-10 rounded-full bg-cyan-500/10 flex items-center justify-center">
              <UserCircle className="text-cyan-400" size={25} />
            </div>

            <div className="min-w-0">
              <p className="text-sm font-semibold truncate">
                {user?.full_name || 'User'}
              </p>

              <p className="text-xs text-slate-500 truncate">
                {user?.email || ''}
              </p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-3 text-sm text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 md:ml-64 min-w-0">

        {/* Top Navigation */}
        <header className="h-20 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between px-5 md:px-8 sticky top-0 z-10 backdrop-blur">
          <div>
            <p className="text-sm text-slate-400">Workspace</p>
            <h2 className="text-lg font-semibold">Dashboard</h2>
          </div>

          <div className="flex items-center gap-4">
            <button
              type="button"
              aria-label="Notifications"
              className="p-2 text-slate-400 hover:text-cyan-400"
            >
              <Bell size={21} />
            </button>

            <div className="hidden sm:block text-right">
              <p className="text-sm font-medium">
                {user?.full_name || 'User'}
              </p>
              <p className="text-xs text-slate-500">
                Research workspace
              </p>
            </div>
          </div>
        </header>

        <div className="p-5 md:p-8 max-w-7xl mx-auto">

          {/* Welcome Section */}
          <section id="overview" className="mb-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold">
                  Welcome back, {user?.full_name?.split(' ')[0] || 'User'}!
                </h1>

                <p className="text-slate-400 mt-2">
                  Your intelligent stock research workspace is ready.
                </p>
              </div>

              <div className="flex items-center gap-2 text-sm bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-4 py-2 rounded-lg w-fit">
                <Activity size={17} />
                Workspace active
              </div>
            </div>
          </section>

          {/* Summary Cards */}
          <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5 mb-8">
            {stats.map((stat) => {
              const Icon = stat.icon

              return (
                <div
                  key={stat.title}
                  className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-cyan-500/40 transition"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-slate-400">
                      {stat.title}
                    </p>

                    <div className="p-3 bg-cyan-500/10 rounded-lg">
                      <Icon className="text-cyan-400" size={21} />
                    </div>
                  </div>

                  <h3 className="text-3xl font-bold mt-5">
                    {stat.value}
                  </h3>

                  <p className="text-xs text-slate-500 mt-2">
                    {stat.description}
                  </p>
                </div>
              )
            })}
          </section>

          {/* Stock Search and Add to Watchlist */}
          <section
            id="stock-search"
            className="bg-slate-900 border border-slate-800 rounded-xl p-6 md:p-8 mb-8"
          >
            <div className="flex items-center gap-3 mb-5">
              <div className="p-3 rounded-lg bg-cyan-500/10">
                <Search className="text-cyan-400" size={23} />
              </div>

              <div>
                <h2 className="text-xl font-semibold">
                  Start Stock Research
                </h2>

                <p className="text-sm text-slate-400">
                  Add a supported stock ticker to your watchlist.
                </p>
              </div>
            </div>

            {/* Search companies by name or ticker */}
            <form onSubmit={handleCompanySearch} className="mb-6 space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_180px_auto] gap-3">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Search company name or ticker (e.g. Infosys, Reliance, TCS)"
                  className="min-w-0 rounded-lg bg-slate-950 border border-slate-700 px-4 py-3 text-white placeholder:text-slate-500 outline-none focus:border-cyan-500"
                />

                <select
                  value={searchMarket}
                  onChange={(event) => setSearchMarket(event.target.value)}
                  className="rounded-lg bg-slate-950 border border-slate-700 px-4 py-3 text-white outline-none focus:border-cyan-500"
                >
                  <option value="NSE">NSE</option>
                  <option value="BSE">BSE</option>
                  <option value="NASDAQ">NASDAQ</option>
                  <option value="NYSE">NYSE</option>
                </select>

                <button
                  type="submit"
                  disabled={searchingCompanies || !searchQuery.trim()}
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-cyan-500 px-5 py-3 font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  <Search size={18} />
                  {searchingCompanies ? 'Searching...' : 'Search'}
                </button>
              </div>

              <p className="text-xs text-slate-500">
                Search supported companies across NSE, BSE, NASDAQ, and NYSE.
              </p>

              {companySearchError && (
                <p role="alert" className="text-sm text-amber-400">
                  {companySearchError}
                </p>
              )}

              {companyResults.length > 0 && (
                <div className="rounded-lg border border-slate-700 divide-y divide-slate-800 overflow-hidden">
                  {companyResults.map((company) => (
                    <div
                      key={`${company.symbol}-${company.exchange || company.market}`}
                      className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-950/70 px-4 py-3"
                    >
                      <div className="min-w-0">
                        <p className="font-medium text-white">{company.name || company.symbol}</p>
                        <p className="text-xs text-slate-400 mt-1">
                          {company.symbol} · {company.exchange || company.market}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleSelectCompany(company)}
                        className="shrink-0 rounded-lg border border-cyan-500 px-4 py-2 text-sm font-medium text-cyan-400 hover:bg-cyan-500/10 transition"
                      >
                        Select Stock
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </form>

            <div className="border-t border-slate-800 pt-5 mb-4">
              <h3 className="text-sm font-semibold text-white mb-1">Selected Stock</h3>
              <p className="text-xs text-slate-400">
                Select a company above, or enter a ticker manually below.
              </p>
            </div>

            <form onSubmit={handleAddStock} className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  value={stockTicker}
                  onChange={(event) => setStockTicker(event.target.value)}
                  placeholder="Enter ticker (e.g. TCS.NS, RELIANCE.NS, AAPL)"
                  maxLength={20}
                  className="flex-1 min-w-0 rounded-lg bg-slate-950 border border-slate-700 px-4 py-3 text-white placeholder:text-slate-500 outline-none focus:border-cyan-500"
                />

                <div className="flex flex-col sm:flex-row gap-3">
                  <button
                    type="submit"
                    disabled={addingStock || startingResearch || !stockTicker.trim()}
                    className="inline-flex items-center justify-center gap-2 rounded-lg bg-cyan-500 px-5 py-3 font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed transition"
                  >
                    <Bookmark size={18} />
                    {addingStock ? 'Adding...' : 'Add to Watchlist'}
                  </button>

                  <button
                    type="button"
                    onClick={handleStartResearch}
                    disabled={addingStock || startingResearch || !stockTicker.trim()}
                    className="inline-flex items-center justify-center gap-2 rounded-lg border border-cyan-500 px-5 py-3 font-semibold text-cyan-400 hover:bg-cyan-500/10 disabled:opacity-50 disabled:cursor-not-allowed transition"
                  >
                    <TrendingUp size={18} />
                    {startingResearch ? 'Researching...' : 'Start Research'}
                  </button>
                </div>
              </div>

              <p className="text-xs text-slate-500">
                Examples: TCS.NS, RELIANCE.NS, INFY.NS, AAPL.
              </p>

              {stockActionMessage && (
                <p role="status" className="text-sm text-emerald-400">
                  {stockActionMessage}
                </p>
              )}

              {stockActionError && (
                <p role="alert" className="text-sm text-red-400">
                  {stockActionError}
                </p>
              )}

              {researchActionMessage && (
                <p role="status" className="text-sm text-emerald-400">
                  {researchActionMessage}
                </p>
              )}

              {researchActionError && (
                <p role="alert" className="text-sm text-red-400">
                  {researchActionError}
                </p>
              )}
            </form>
          </section>

          {/* Watchlist and Research History */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-5">

            {/* Watchlist */}
            <div
              id="watchlist"
              className="bg-slate-900 border border-slate-800 rounded-xl p-6"
            >
              <div className="flex justify-between items-center mb-5">
                <h2 className="font-semibold text-lg">
                  My Watchlist
                </h2>

                <Bookmark className="text-cyan-400" size={20} />
              </div>

              {watchlistLoading ? (
                <p className="text-slate-400 text-sm">
                  Loading watchlist...
                </p>
              ) : watchlistError ? (
                <p className="text-red-400 text-sm">
                  {watchlistError}
                </p>
              ) : watchlist.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No saved stocks yet. Add stocks to your watchlist.
                </p>
              ) : (
                <div className="space-y-3">
                  {watchlist.map((stock) => (
                    <div
                      key={stock.saved_stock_id}
                      className="flex justify-between items-center gap-3 border-b border-slate-800 px-3 py-3 rounded-lg hover:bg-slate-800/70 transition"
                    >
                      <Link
                        to={getStockDetailsPath(stock.ticker)}
                        className="group min-w-0 flex-1"
                        title={`View complete ${stock.ticker} stock analysis`}
                      >
                        <p className="font-medium text-white group-hover:text-cyan-400 transition">
                          {stock.ticker}
                        </p>

                        <p className="text-xs text-slate-500 mt-1">
                          View complete stock analysis
                        </p>

                        <span className="inline-flex items-center gap-1 text-xs text-cyan-400 mt-2">
                          View Details
                          <ArrowUpRight size={15} />
                        </span>
                      </Link>

                      <button
                        type="button"
                        onClick={() =>
                          handleRemoveStock(
                            stock.saved_stock_id,
                            stock.ticker
                          )
                        }
                        disabled={
                          removingStockId === stock.saved_stock_id
                        }
                        className="shrink-0 rounded-lg border border-red-500/20 px-3 py-2 text-xs text-red-400 hover:bg-red-500/10 disabled:opacity-50 transition"
                      >
                        {removingStockId === stock.saved_stock_id
                          ? 'Removing...'
                          : 'Remove'}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Research History */}
            <div
              id="history"
              className="bg-slate-900 border border-slate-800 rounded-xl p-6"
            >
              <div className="flex justify-between items-center mb-5">
                <h2 className="font-semibold text-lg">
                  Research History
                </h2>

                <History className="text-cyan-400" size={20} />
              </div>

              {historyLoading ? (
                <p className="text-slate-400 text-sm">
                  Loading research history...
                </p>
              ) : historyError ? (
                <p className="text-red-400 text-sm">
                  {historyError}
                </p>
              ) : researchHistory.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No research tasks found. Start your first stock research.
                </p>
              ) : (
                <div className="space-y-3">
                  {researchHistory.map((task) => (
                    <Link
                      key={task.task_id}
                      to={getResearchStockDetailsPath(task)}
                      className="group flex justify-between items-center gap-3 border-b border-slate-800 px-3 py-4 rounded-lg hover:bg-slate-800/70 hover:border-cyan-500/40 transition"
                      title={`Open complete ${task.ticker} stock analysis`}
                    >
                      <div>
                        <p className="font-medium text-white group-hover:text-cyan-400 transition">
                          {task.ticker}
                        </p>

                        <p className="text-xs text-slate-500 mt-1">
                          {task.market} · {task.requested_period}
                        </p>

                        <p className="text-xs text-slate-500 mt-1">
                          {task.created_at
                            ? new Date(task.created_at).toLocaleString()
                            : 'Research record'}
                        </p>
                      </div>

                      <div className="flex flex-col items-end gap-2">
                        <span
                          className={`text-xs ${
                            task.status?.toLowerCase() === 'completed'
                              ? 'text-emerald-400'
                              : task.status?.toLowerCase() === 'failed'
                                ? 'text-red-400'
                                : 'text-amber-400'
                          }`}
                        >
                          {task.status}
                        </span>

                        <span className="flex items-center gap-1 text-xs text-cyan-400">
                          View Details
                          <ArrowUpRight size={15} />
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* User Preferences */}
          <PreferencesSection />

          {/* Footer */}
          <footer className="mt-10 pt-6 border-t border-slate-800 flex flex-col sm:flex-row justify-between gap-3 text-xs text-slate-500">
            <p>Multi-Agent Stock Research Analyst</p>
            <p>AI-powered stock market research platform</p>
          </footer>

        </div>
      </main>
    </div>
  )
}

export default Dashboard