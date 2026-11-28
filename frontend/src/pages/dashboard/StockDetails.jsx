
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import {
  Activity,
  ArrowLeft,
  RefreshCw,
  BarChart3,
} from 'lucide-react'

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  ReferenceLine,
} from 'recharts'

import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  ColorType,
} from 'lightweight-charts'

import { useAuth } from '../../context/AuthContext'
import api from '../../services/api'

// ======================================================
// INTERACTIVE CANDLESTICK CHART
// ======================================================

function CandlestickChart({ data }) {
  const chartContainerRef = useRef(null)

  useEffect(() => {
    const container = chartContainerRef.current

    if (!container || !data.length) return

    const chart = createChart(container, {
      width: container.clientWidth,
      height: 430,

      layout: {
        background: {
          type: ColorType.Solid,
          color: '#0f172a',
        },
        textColor: '#94a3b8',
      },

      grid: {
        vertLines: {
          color: '#1e293b',
        },
        horzLines: {
          color: '#1e293b',
        },
      },

      crosshair: {
        mode: 0,
      },

      rightPriceScale: {
        borderColor: '#334155',
      },

      timeScale: {
        borderColor: '#334155',
        timeVisible: false,
        secondsVisible: false,
      },

      handleScroll: true,
      handleScale: true,
    })

    // Candlestick series
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    })

    const candleData = data
      .filter(
        (item) =>
          item.Open != null &&
          item.High != null &&
          item.Low != null &&
          item.Close != null
      )
      .map((item) => ({
        time: item.date,
        open: Number(item.Open),
        high: Number(item.High),
        low: Number(item.Low),
        close: Number(item.Close),
      }))
      .filter(
        (item) =>
          Number.isFinite(item.open) &&
          Number.isFinite(item.high) &&
          Number.isFinite(item.low) &&
          Number.isFinite(item.close)
      )
      .sort((a, b) => a.time.localeCompare(b.time))

    candleSeries.setData(candleData)

    // Volume histogram
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
      lastValueVisible: false,
      priceLineVisible: false,
    })

    volumeSeries.setData(
      data
        .filter(
          (item) =>
            item.Volume != null &&
            item.Open != null &&
            item.Close != null
        )
        .map((item) => ({
          time: item.date,
          value: Number(item.Volume),
          color:
            Number(item.Close) >= Number(item.Open)
              ? 'rgba(34, 197, 94, 0.45)'
              : 'rgba(239, 68, 68, 0.45)',
        }))
        .filter(
          (item) =>
            Number.isFinite(item.value) && item.value >= 0
        )
        .sort((a, b) => a.time.localeCompare(b.time))
    )

    // Keep volume in the lower part of the chart
    chart.priceScale('').applyOptions({
      scaleMargins: {
        top: 0.82,
        bottom: 0,
      },
    })

    chart.timeScale().fitContent()

    // Responsive chart
    const resizeObserver = new ResizeObserver((entries) => {
      if (!entries.length) return

      const { width } = entries[0].contentRect

      if (width > 0) {
        chart.applyOptions({
          width,
        })
      }
    })

    resizeObserver.observe(container)

    return () => {
      resizeObserver.disconnect()
      chart.remove()
    }
  }, [data])

  return (
    <div
      ref={chartContainerRef}
      className="w-full"
      style={{ minHeight: '430px' }}
    />
  )
}

// ======================================================
// STOCK DETAILS PAGE
// ======================================================

function StockDetails() {
  const { symbol } = useParams()
  const { token } = useAuth()

  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [period, setPeriod] = useState('1y')
  const [preferencesLoaded, setPreferencesLoaded] = useState(false)
  const [fundamentalAnalysis, setFundamentalAnalysis] = useState(null)
  const [fundamentalLoading, setFundamentalLoading] = useState(false)
  const [fundamentalError, setFundamentalError] = useState('')

  // Fetch stock analysis
  const fetchAnalysis = async () => {
    try {
      setLoading(true)
      setError('')

      const response = await api.get(
        `/stocks/${encodeURIComponent(symbol)}/analysis`,
        {
          params: {
            period,
            interval: '1d',
          },
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      setAnalysis(response.data)
    } catch (err) {
      console.error('Stock analysis error:', err)

      setError(
        err.response?.data?.detail ||
        'Unable to load stock analysis.'
      )
    } finally {
      setLoading(false)
    }
  }


  // Fetch Fundamental Analysis independently so a failure here
  // does not prevent the historical stock page from loading.
  const fetchFundamentalAnalysis = async () => {
    if (!symbol || !token) return

    try {
      setFundamentalLoading(true)
      setFundamentalError('')

      const response = await api.get(
        `/stocks/${encodeURIComponent(symbol)}/fundamental-analysis`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      setFundamentalAnalysis(response.data)
    } catch (err) {
      console.error('Fundamental analysis error:', err)
      setFundamentalError(
        err.response?.data?.detail ||
        'Unable to load fundamental analysis.'
      )
    } finally {
      setFundamentalLoading(false)
    }
  }

  // Load the user's saved preferences before fetching stock analysis
  useEffect(() => {
    const loadPreferences = async () => {
      setPreferencesLoaded(false)

      try {
        if (!token) return

        const response = await api.get('/preferences/', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        const savedPeriod = response.data?.default_analysis_period
        const allowedPeriods = ['1mo', '3mo', '6mo', '1y', '5y']

        if (allowedPeriods.includes(savedPeriod)) {
          setPeriod(savedPeriod)
        }
      } catch (err) {
        // A 404 means the user has not saved preferences yet.
        // Keep the default period of 1y in that case.
        if (err.response?.status !== 404) {
          console.error('Unable to load user preferences:', err)
        }
      } finally {
        setPreferencesLoaded(true)
      }
    }

    loadPreferences()
  }, [token])

  // Fetch stock analysis only after preferences have been loaded
  useEffect(() => {
    if (!preferencesLoaded) return

    if (symbol && token) {
      fetchAnalysis()
    } else {
      setLoading(false)
    }
  }, [symbol, period, token, preferencesLoaded])


  // Load fundamental analysis when the selected stock changes.
  useEffect(() => {
    setFundamentalAnalysis(null)
    setFundamentalError('')

    if (symbol && token) {
      fetchFundamentalAnalysis()
    }
  }, [symbol, token])

  const summary = analysis?.summary
  const historicalData = analysis?.historical_data || []

  const formatPrice = (value) => {
    if (value === null || value === undefined) return 'N/A'

    return Number(value).toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  }

  const formatNumber = (value) => {
    if (value === null || value === undefined) return 'N/A'

    return Number(value).toLocaleString('en-IN')
  }


  const formatFinancialValue = (value) => {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) {
      return 'N/A'
    }

    return Number(value).toLocaleString('en-IN', {
      notation: 'compact',
      maximumFractionDigits: 2,
    })
  }

  const formatPercent = (value) => {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) {
      return 'N/A'
    }

    return `${Number(value).toFixed(2)}%`
  }

  const chartData = useMemo(
    () =>
      historicalData.map((item) => ({
        ...item,
        date: String(item.Date || item.index || '').slice(0, 10),
      })),
    [historicalData]
  )

  const performancePositive = Number(summary?.daily_change) >= 0

  const metricCards = [
    {
      title: 'Closing Price',
      value:
        summary?.close !== null && summary?.close !== undefined
          ? `₹ ${formatPrice(summary.close)}`
          : 'N/A',
    },
    {
      title: 'Daily Change',
      value:
        summary?.daily_change_percent !== null &&
        summary?.daily_change_percent !== undefined
          ? `${summary.daily_change_percent}%`
          : 'N/A',
      color: performancePositive
        ? 'text-emerald-400'
        : 'text-red-400',
    },
    {
      title: 'Trading Volume',
      value: formatNumber(summary?.volume),
    },
    {
      title: 'RSI (14)',
      value: formatPrice(summary?.rsi),
    },
  ]

  // Loading
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center">
        <div className="text-center">
          <RefreshCw
            className="animate-spin text-cyan-400 mx-auto mb-4"
            size={32}
          />
          <p className="text-slate-400">
            Loading stock analysis...
          </p>
        </div>
      </div>
    )
  }

  // Error
  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 text-white p-8">
        <div className="max-w-3xl mx-auto bg-slate-900 border border-red-500/30 rounded-xl p-8">

          <h2 className="text-xl font-bold text-red-400">
            Stock Analysis Failed
          </h2>

          <p className="text-slate-400 mt-3">
            {error}
          </p>

          <div className="flex gap-3 mt-6">
            <button
              onClick={fetchAnalysis}
              className="px-4 py-2 bg-cyan-500 text-slate-950 rounded-lg font-semibold"
            >
              Try Again
            </button>

            <Link
              to="/dashboard"
              className="px-4 py-2 bg-slate-800 rounded-lg"
            >
              Dashboard
            </Link>
          </div>

        </div>
      </div>
    )
  }

  // Main page
  return (
    <div className="min-h-screen bg-slate-950 text-white">

      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-800 px-5 md:px-8 py-5">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">

          <div className="flex items-center gap-3">
            <Activity className="text-cyan-400" size={28} />

            <div>
              <h1 className="font-bold">
                Multi-Agent Stock Research
              </h1>
              <p className="text-xs text-slate-400">
                Stock Analysis
              </p>
            </div>
          </div>

          <Link
            to="/dashboard"
            className="flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300"
          >
            <ArrowLeft size={18} />
            Dashboard
          </Link>

        </div>
      </header>

      <main className="max-w-7xl mx-auto p-5 md:p-8">

        {/* Stock Title */}
        <section className="flex flex-col md:flex-row md:items-center justify-between gap-5 mb-8">

          <div>
            <p className="text-sm text-slate-400">
              Stock Symbol
            </p>

            <h1 className="text-3xl md:text-4xl font-bold mt-1">
              {analysis?.symbol || symbol}
            </h1>

            <p className="text-sm text-slate-400 mt-2">
              Historical Stock Analysis · {analysis?.period}
            </p>
          </div>

          <div className="flex flex-wrap gap-3">

            <select
              value={period}
              onChange={(event) => setPeriod(event.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white"
            >
              <option value="1mo">1 Month</option>
              <option value="3mo">3 Months</option>
              <option value="6mo">6 Months</option>
              <option value="1y">1 Year</option>
              <option value="5y">5 Years</option>
            </select>

            <button
              onClick={fetchAnalysis}
              className="flex items-center gap-2 bg-cyan-500 text-slate-950 px-4 py-3 rounded-lg font-semibold hover:bg-cyan-400"
            >
              <RefreshCw size={17} />
              Refresh
            </button>

          </div>
        </section>

        {/* Summary Cards */}
        <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5 mb-8">

          {metricCards.map((metric) => (
            <div
              key={metric.title}
              className="bg-slate-900 border border-slate-800 rounded-xl p-6"
            >
              <p className="text-sm text-slate-400">
                {metric.title}
              </p>

              <h2 className={`text-2xl font-bold mt-4 ${metric.color || 'text-white'}`}>
                {metric.value}
              </h2>
            </div>
          ))}

        </section>

        {/* NEW: Candlestick Chart */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-5 md:p-7 mb-8">

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">

            <div className="flex items-center gap-3">
              <BarChart3 className="text-cyan-400" size={23} />

              <div>
                <h2 className="text-xl font-semibold">
                  Candlestick Chart
                </h2>

                <p className="text-sm text-slate-400">
                  Open, High, Low, Close and Trading Volume
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-4 text-xs">
              <span className="flex items-center gap-2 text-emerald-400">
                <span className="w-3 h-3 rounded-sm bg-emerald-500" />
                Bullish
              </span>

              <span className="flex items-center gap-2 text-red-400">
                <span className="w-3 h-3 rounded-sm bg-red-500" />
                Bearish
              </span>
            </div>

          </div>

          {chartData.length === 0 ? (
            <p className="text-slate-400 py-10 text-center">
              No candlestick data available.
            </p>
          ) : (
            <CandlestickChart data={chartData} />
          )}

          <p className="text-xs text-slate-500 mt-3">
            Use your mouse wheel to zoom and drag to move through historical prices.
          </p>

        </section>

        {/* Historical Price Chart */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-5 md:p-7 mb-8">

          <div className="flex items-center gap-3 mb-6">
            <BarChart3 className="text-cyan-400" size={23} />

            <div>
              <h2 className="text-xl font-semibold">
                Historical Price Chart
              </h2>

              <p className="text-sm text-slate-400">
                Closing price and moving averages
              </p>
            </div>
          </div>

          {chartData.length === 0 ? (
            <p className="text-slate-400 py-10 text-center">
              No historical price data available.
            </p>
          ) : (
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid
                    stroke="#334155"
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="date"
                    stroke="#94a3b8"
                    minTickGap={35}
                    tick={{ fontSize: 11 }}
                  />

                  <YAxis
                    stroke="#94a3b8"
                    domain={['auto', 'auto']}
                    tick={{ fontSize: 11 }}
                  />

                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#fff',
                    }}
                  />

                  <Legend />

                  <Line
                    type="monotone"
                    dataKey="Close"
                    name="Closing Price"
                    stroke="#22d3ee"
                    strokeWidth={2}
                    dot={false}
                    connectNulls
                  />

                  <Line
                    type="monotone"
                    dataKey="MA20"
                    name="MA20"
                    stroke="#facc15"
                    strokeWidth={1.5}
                    dot={false}
                    connectNulls
                  />

                  <Line
                    type="monotone"
                    dataKey="MA50"
                    name="MA50"
                    stroke="#a78bfa"
                    strokeWidth={1.5}
                    dot={false}
                    connectNulls
                  />

                  <Line
                    type="monotone"
                    dataKey="MA200"
                    name="MA200"
                    stroke="#fb923c"
                    strokeWidth={1.5}
                    dot={false}
                    connectNulls
                  />

                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

        </section>

        {/* Volume Chart */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-5 md:p-7 mb-8">

          <h2 className="text-xl font-semibold mb-6">
            Trading Volume
          </h2>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid
                  stroke="#334155"
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="date"
                  stroke="#94a3b8"
                  minTickGap={35}
                  tick={{ fontSize: 11 }}
                />

                <YAxis
                  stroke="#94a3b8"
                  tick={{ fontSize: 11 }}
                />

                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                />

                <Bar dataKey="Volume" fill="#0891b2" />
              </BarChart>
            </ResponsiveContainer>
          </div>

        </section>

        {/* RSI Chart */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-5 md:p-7 mb-8">

          <h2 className="text-xl font-semibold mb-2">
            Relative Strength Index (RSI)
          </h2>

          <p className="text-sm text-slate-400 mb-6">
            RSI values between 0 and 100
          </p>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid
                  stroke="#334155"
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="date"
                  stroke="#94a3b8"
                  minTickGap={35}
                  tick={{ fontSize: 11 }}
                />

                <YAxis
                  domain={[0, 100]}
                  stroke="#94a3b8"
                />

                <Tooltip />

                <ReferenceLine
                  y={70}
                  stroke="#f87171"
                  strokeDasharray="5 5"
                />

                <ReferenceLine
                  y={30}
                  stroke="#34d399"
                  strokeDasharray="5 5"
                />

                <Line
                  type="monotone"
                  dataKey="RSI"
                  name="RSI"
                  stroke="#c084fc"
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                />

              </LineChart>
            </ResponsiveContainer>
          </div>

        </section>

        {/* MACD Chart */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-5 md:p-7 mb-8">

          <h2 className="text-xl font-semibold mb-6">
            MACD Analysis
          </h2>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid
                  stroke="#334155"
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="date"
                  stroke="#94a3b8"
                  minTickGap={35}
                  tick={{ fontSize: 11 }}
                />

                <YAxis stroke="#94a3b8" />

                <Tooltip />

                <ReferenceLine
                  y={0}
                  stroke="#64748b"
                />

                <Legend />

                <Line
                  type="monotone"
                  dataKey="MACD"
                  stroke="#22d3ee"
                  name="MACD"
                  dot={false}
                  connectNulls
                />

                <Line
                  type="monotone"
                  dataKey="MACD_Signal"
                  stroke="#facc15"
                  name="Signal"
                  dot={false}
                  connectNulls
                />

                <Line
                  type="monotone"
                  dataKey="MACD_Histogram"
                  stroke="#a78bfa"
                  name="Histogram"
                  dot={false}
                  connectNulls
                />

              </LineChart>
            </ResponsiveContainer>
          </div>

        </section>

        {/* Technical Summary */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8">

          <h2 className="text-xl font-semibold mb-5">
            Technical Analysis Summary
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">

            {[
              ['MA5', summary?.ma5],
              ['MA20', summary?.ma20],
              ['MA50', summary?.ma50],
              ['MA200', summary?.ma200],
              ['RSI', summary?.rsi],
              ['MACD', summary?.macd],
              ['MACD Signal', summary?.macd_signal],
              ['MACD Histogram', summary?.macd_histogram],
            ].map(([label, value]) => (
              <div
                key={label}
                className="bg-slate-950 rounded-lg p-4"
              >
                <p className="text-xs text-slate-400">
                  {label}
                </p>

                <p className="text-lg font-semibold mt-2">
                  {formatPrice(value)}
                </p>
              </div>
            ))}

          </div>

          <div className="mt-6 p-4 bg-cyan-500/10 border border-cyan-500/20 rounded-lg">

            <p className="text-sm text-slate-400">
              Moving Average Crossover
            </p>

            <p className="text-cyan-400 font-semibold mt-2">
              {summary?.ma_crossover || 'Not available'}
            </p>

          </div>

        </section>

        {/* Latest OHLC Information */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8">

          <h2 className="text-xl font-semibold mb-5">
            Latest Trading Information
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-5">

            {[
              ['Open', historicalData.at(-1)?.Open],
              ['High', historicalData.at(-1)?.High],
              ['Low', historicalData.at(-1)?.Low],
              ['Close', historicalData.at(-1)?.Close],
            ].map(([label, value]) => (
              <div key={label}>
                <p className="text-sm text-slate-400">
                  {label}
                </p>

                <p className="text-lg font-semibold mt-2">
                  {value == null ? 'N/A' : formatPrice(value)}
                </p>
              </div>
            ))}

          </div>

        </section>

        {/* Fundamental Analysis */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-5 md:p-7 mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-xl font-semibold">Fundamental Analysis</h2>
              <p className="text-sm text-slate-400 mt-1">
                Financial performance, profitability, stability, valuation and peer comparison
              </p>
            </div>

            <button
              onClick={fetchFundamentalAnalysis}
              disabled={fundamentalLoading}
              className="flex items-center justify-center gap-2 bg-cyan-500 text-slate-950 px-4 py-2.5 rounded-lg font-semibold hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw size={16} className={fundamentalLoading ? 'animate-spin' : ''} />
              {fundamentalLoading ? 'Loading...' : 'Refresh Fundamentals'}
            </button>
          </div>

          {fundamentalLoading && !fundamentalAnalysis ? (
            <div className="py-10 text-center text-slate-400">
              <RefreshCw className="animate-spin text-cyan-400 mx-auto mb-3" size={26} />
              Loading fundamental analysis...
            </div>
          ) : fundamentalError ? (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
              <p className="font-semibold text-red-400">Fundamental analysis unavailable</p>
              <p className="text-sm text-slate-300 mt-2">{fundamentalError}</p>
              <button
                onClick={fetchFundamentalAnalysis}
                className="mt-3 text-sm font-semibold text-cyan-400 hover:text-cyan-300"
              >
                Try again
              </button>
            </div>
          ) : !fundamentalAnalysis ? (
            <p className="text-slate-400 py-6 text-center">
              Fundamental analysis has not been loaded yet.
            </p>
          ) : (
            <>
              <div className="mb-6">
                <h3 className="text-lg font-semibold">
                  {fundamentalAnalysis.company_name || fundamentalAnalysis.symbol}
                </h3>
                <p className="text-sm text-slate-400 mt-1">
                  {fundamentalAnalysis.sector || 'Sector unavailable'}
                  {fundamentalAnalysis.industry ? ` · ${fundamentalAnalysis.industry}` : ''}
                </p>
              </div>

              {/* Growth, profitability, stability and valuation metrics */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                {[
                  {
                    label: 'Revenue Growth',
                    value: formatPercent(fundamentalAnalysis.revenue_earnings?.revenue_growth_percent),
                  },
                  {
                    label: 'Earnings Growth',
                    value: formatPercent(fundamentalAnalysis.revenue_earnings?.earnings_growth_percent),
                  },
                  {
                    label: 'Profit Margin',
                    value: formatPercent(fundamentalAnalysis.profitability?.profit_margin_percent),
                  },
                  {
                    label: 'Return on Equity (ROE)',
                    value: formatPercent(fundamentalAnalysis.profitability?.return_on_equity_percent),
                  },
                  {
                    label: 'Debt-to-Equity',
                    value: formatPercent(fundamentalAnalysis.financial_stability?.debt_to_equity_percent),
                  },
                  {
                    label: 'P/E Ratio',
                    value: fundamentalAnalysis.valuation?.pe_ratio ?? 'N/A',
                  },
                  {
                    label: 'P/B Ratio',
                    value: fundamentalAnalysis.valuation?.pb_ratio ?? 'N/A',
                  },
                  {
                    label: 'Net Income',
                    value: formatFinancialValue(fundamentalAnalysis.profitability?.net_income),
                  },
                ].map((metric) => (
                  <div
                    key={metric.label}
                    className="bg-slate-950 border border-slate-800 rounded-lg p-4"
                  >
                    <p className="text-xs text-slate-400">{metric.label}</p>
                    <p className="text-xl font-bold text-white mt-2">{metric.value}</p>
                  </div>
                ))}
              </div>

              {/* Revenue and earnings history */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-8">
                <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
                  <h3 className="font-semibold mb-3">Revenue History</h3>
                  {(fundamentalAnalysis.revenue_earnings?.revenue_history || []).length === 0 ? (
                    <p className="text-sm text-slate-500">Revenue history unavailable.</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm text-left">
                        <thead className="text-slate-400 border-b border-slate-800">
                          <tr>
                            <th className="py-2 pr-3">Financial period</th>
                            <th className="py-2 text-right">Reported value</th>
                          </tr>
                        </thead>
                        <tbody>
                          {fundamentalAnalysis.revenue_earnings.revenue_history.map((item, index) => (
                            <tr key={`${item.period}-${index}`} className="border-b border-slate-800/70">
                              <td className="py-2 pr-3 text-slate-300">
                                {String(item.period).slice(0, 10)}
                              </td>
                              <td className="py-2 text-right text-white">
                                {formatFinancialValue(item.value)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
                  <h3 className="font-semibold mb-3">Earnings History</h3>
                  {(fundamentalAnalysis.revenue_earnings?.earnings_history || []).length === 0 ? (
                    <p className="text-sm text-slate-500">Earnings history unavailable.</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm text-left">
                        <thead className="text-slate-400 border-b border-slate-800">
                          <tr>
                            <th className="py-2 pr-3">Financial period</th>
                            <th className="py-2 text-right">Reported value</th>
                          </tr>
                        </thead>
                        <tbody>
                          {fundamentalAnalysis.revenue_earnings.earnings_history.map((item, index) => (
                            <tr key={`${item.period}-${index}`} className="border-b border-slate-800/70">
                              <td className="py-2 pr-3 text-slate-300">
                                {String(item.period).slice(0, 10)}
                              </td>
                              <td className="py-2 text-right text-white">
                                {formatFinancialValue(item.value)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>

              {/* Financial stability details */}
              <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 mb-8">
                <h3 className="font-semibold mb-4">Financial Stability</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-slate-400">Total Debt</p>
                    <p className="text-lg font-semibold mt-1">
                      {formatFinancialValue(fundamentalAnalysis.financial_stability?.total_debt)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400">Shareholders' Equity</p>
                    <p className="text-lg font-semibold mt-1">
                      {formatFinancialValue(fundamentalAnalysis.financial_stability?.shareholders_equity)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Peer comparison */}
              <div className="mb-8">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">Industry Peer Comparison</h3>
                    <p className="text-sm text-slate-400 mt-1">
                      Comparison with companies in the same industry
                    </p>
                  </div>
                  <span className={`text-xs px-3 py-1 rounded-full ${
                    fundamentalAnalysis.peer_comparison?.status === 'available'
                      ? 'bg-emerald-500/10 text-emerald-400'
                      : 'bg-amber-500/10 text-amber-400'
                  }`}>
                    {fundamentalAnalysis.peer_comparison?.status === 'available'
                      ? `${fundamentalAnalysis.peer_comparison.peer_count} peers found`
                      : 'Peer data unavailable'}
                  </span>
                </div>

                {fundamentalAnalysis.peer_comparison?.status === 'available' ? (
                  <div className="overflow-x-auto border border-slate-800 rounded-lg">
                    <table className="w-full min-w-[760px] text-sm text-left">
                      <thead className="bg-slate-950 text-slate-400">
                        <tr>
                          <th className="p-3">Company</th>
                          <th className="p-3 text-right">Revenue Growth</th>
                          <th className="p-3 text-right">Profit Margin</th>
                          <th className="p-3 text-right">ROE</th>
                          <th className="p-3 text-right">Debt/Equity</th>
                          <th className="p-3 text-right">P/E</th>
                          <th className="p-3 text-right">P/B</th>
                        </tr>
                      </thead>
                      <tbody>
                        {[
                          {
                            symbol: fundamentalAnalysis.symbol,
                            company_name: `${fundamentalAnalysis.company_name || fundamentalAnalysis.symbol} (Selected)`,
                            metrics: fundamentalAnalysis.peer_comparison.company_metrics,
                            isCurrent: true,
                          },
                          ...(fundamentalAnalysis.peer_comparison.peers || []).map((peer) => ({
                            ...peer,
                            isCurrent: false,
                          })),
                        ].map((company) => (
                          <tr
                            key={company.symbol}
                            className={`border-t border-slate-800 ${
                              company.isCurrent ? 'bg-cyan-500/10' : 'bg-slate-900'
                            }`}
                          >
                            <td className="p-3">
                              <p className="font-semibold text-white">{company.company_name}</p>
                              <p className="text-xs text-slate-500">{company.symbol}</p>
                            </td>
                            <td className="p-3 text-right">{formatPercent(company.metrics?.revenue_growth_percent)}</td>
                            <td className="p-3 text-right">{formatPercent(company.metrics?.profit_margin_percent)}</td>
                            <td className="p-3 text-right">{formatPercent(company.metrics?.return_on_equity_percent)}</td>
                            <td className="p-3 text-right">{formatPercent(company.metrics?.debt_to_equity_percent)}</td>
                            <td className="p-3 text-right">{company.metrics?.pe_ratio ?? 'N/A'}</td>
                            <td className="p-3 text-right">{company.metrics?.pb_ratio ?? 'N/A'}</td>
                          </tr>
                        ))}
                        {fundamentalAnalysis.peer_comparison.peer_average_metrics && (
                          <tr className="border-t border-slate-700 bg-slate-950 font-semibold">
                            <td className="p-3 text-cyan-400">Peer Average</td>
                            <td className="p-3 text-right">{formatPercent(fundamentalAnalysis.peer_comparison.peer_average_metrics.revenue_growth_percent)}</td>
                            <td className="p-3 text-right">{formatPercent(fundamentalAnalysis.peer_comparison.peer_average_metrics.profit_margin_percent)}</td>
                            <td className="p-3 text-right">{formatPercent(fundamentalAnalysis.peer_comparison.peer_average_metrics.return_on_equity_percent)}</td>
                            <td className="p-3 text-right">{formatPercent(fundamentalAnalysis.peer_comparison.peer_average_metrics.debt_to_equity_percent)}</td>
                            <td className="p-3 text-right">{fundamentalAnalysis.peer_comparison.peer_average_metrics.pe_ratio ?? 'N/A'}</td>
                            <td className="p-3 text-right">{fundamentalAnalysis.peer_comparison.peer_average_metrics.pb_ratio ?? 'N/A'}</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4 text-sm text-slate-300">
                    {fundamentalAnalysis.peer_comparison?.message ||
                      'Comparable company data is currently unavailable.'}
                  </div>
                )}
              </div>

              {/* Data quality and source */}
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-t border-slate-800 pt-5">
                <div>
                  <h3 className="font-semibold">Data Quality</h3>
                  {(fundamentalAnalysis.data_quality?.missing_information || []).length === 0 ? (
                    <p className="text-sm text-emerald-400 mt-2">
                      No missing fundamental metrics were detected.
                    </p>
                  ) : (
                    <ul className="text-sm text-amber-400 mt-2 list-disc list-inside">
                      {fundamentalAnalysis.data_quality.missing_information.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  )}
                </div>
                <p className="text-xs text-slate-500">
                  Source: {fundamentalAnalysis.metadata?.source || 'Yahoo Finance'}
                  {fundamentalAnalysis.metadata?.retrieved_at
                    ? ` · Retrieved ${new Date(fundamentalAnalysis.metadata.retrieved_at).toLocaleString()}`
                    : ''}
                </p>
              </div>
            </>
          )}
        </section>

        {/* Footer */}
        <footer className="border-t border-slate-800 pt-6 text-sm text-slate-500 flex flex-col sm:flex-row justify-between gap-3">

          <span>
            Multi-Agent Stock Research Analyst
          </span>

          <span>
            Data provided by Yahoo Finance through your backend
          </span>

        </footer>

      </main>
    </div>
  )
}

export default StockDetails
