import React, { useState, useEffect } from 'react';
import {
  Search,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  ShieldCheck,
  Database,
  Calendar,
  DollarSign,
  BarChart2,
  Building,
  Key,
  Sparkles,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  Info,
  Table,
  Plus,
  Compass,
  ChevronDown
} from 'lucide-react';
import { marketApi, watchlistApi } from '../services/api';

const POPULAR_EQUITIES = {
  NSE: [
    { ticker: 'RELIANCE', name: 'Reliance Industries', price: '₹2,985.50' },
    { ticker: 'TCS', name: 'Tata Consultancy Services', price: '₹4,120.25' },
    { ticker: 'INFY', name: 'Infosys Ltd', price: '₹1,892.40' },
    { ticker: 'HDFCBANK', name: 'HDFC Bank', price: '₹1,640.80' },
    { ticker: 'ICICIBANK', name: 'ICICI Bank', price: '₹1,265.10' },
    { ticker: 'TATAMOTORS', name: 'Tata Motors', price: '₹980.60' },
    { ticker: 'SBIN', name: 'State Bank of India', price: '₹845.30' },
    { ticker: 'BHARTIARTL', name: 'Bharti Airtel', price: '₹1,580.00' },
    { ticker: 'ITC', name: 'ITC Ltd', price: '₹502.75' },
    { ticker: 'WIPRO', name: 'Wipro Ltd', price: '₹560.40' },
    { ticker: 'LT', name: 'Larsen & Toubro', price: '₹3,620.00' },
  ],
  BSE: [
    { ticker: 'BSE', name: 'BSE Limited', price: '₹4,650.00' },
    { ticker: 'RELIANCE', name: 'Reliance Industries', price: '₹2,985.50' },
    { ticker: 'TCS', name: 'Tata Consultancy', price: '₹4,120.25' },
    { ticker: 'INFY', name: 'Infosys Ltd', price: '₹1,892.40' },
  ],
  NASDAQ: [
    { ticker: 'AAPL', name: 'Apple Inc.', price: '$228.50' },
    { ticker: 'MSFT', name: 'Microsoft Corporation', price: '$435.20' },
    { ticker: 'NVDA', name: 'NVIDIA Corporation', price: '$142.30' },
    { ticker: 'GOOGL', name: 'Alphabet Google', price: '$178.60' },
    { ticker: 'TSLA', name: 'Tesla Inc.', price: '$260.40' },
    { ticker: 'AMZN', name: 'Amazon.com Inc.', price: '$195.10' },
    { ticker: 'META', name: 'Meta Platforms', price: '$585.00' },
  ],
  NYSE: [
    { ticker: 'JPM', name: 'JPMorgan Chase', price: '$222.80' },
    { ticker: 'DIS', name: 'The Walt Disney Company', price: '$115.50' },
  ],
  ALL: [
    { ticker: 'RELIANCE', market: 'NSE', name: 'Reliance Industries', price: '₹2,985.50' },
    { ticker: 'AAPL', market: 'NASDAQ', name: 'Apple Inc.', price: '$228.50' },
    { ticker: 'TCS', market: 'NSE', name: 'Tata Consultancy', price: '₹4,120.25' },
    { ticker: 'NVDA', market: 'NASDAQ', name: 'NVIDIA Corp', price: '$142.30' },
    { ticker: 'INFY', market: 'NSE', name: 'Infosys Ltd', price: '₹1,892.40' },
    { ticker: 'MSFT', market: 'NASDAQ', name: 'Microsoft Corp', price: '$435.20' },
    { ticker: 'TATAMOTORS', market: 'NSE', name: 'Tata Motors', price: '₹980.60' },
    { ticker: 'TSLA', market: 'NASDAQ', name: 'Tesla Inc.', price: '$260.40' },
    { ticker: 'BSE', market: 'BSE', name: 'BSE Limited', price: '₹4,650.00' },
    { ticker: 'JPM', market: 'NYSE', name: 'JPMorgan Chase', price: '$222.80' },
  ]
};

export default function MarketDataWorkspace({ onLaunchTask }) {
  const [selectedMarket, setSelectedMarket] = useState('NSE');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedStock, setSelectedStock] = useState('RELIANCE');
  const [selectedStockInfo, setSelectedStockInfo] = useState({
    ticker: 'RELIANCE',
    name: 'Reliance Industries Limited',
    market: 'NSE',
    sector: 'Energy & Retail',
    currency: 'INR'
  });

  // Data states
  const [ohlcvData, setOhlcvData] = useState(null);
  const [companyProfile, setCompanyProfile] = useState(null);
  const [financials, setFinancials] = useState(null);
  const [fundamentalAnalysis, setFundamentalAnalysis] = useState(null);
  const [financialPeriod, setFinancialPeriod] = useState('annual'); // annual | quarterly
  const [financialTab, setFinancialTab] = useState('income'); // income | balance | cashflow | ratios
  const [chartPeriod, setChartPeriod] = useState('6 Months');
  const [isLoading, setIsLoading] = useState(true);
  const [activeSubTab, setActiveSubTab] = useState('chart'); // chart | fundamental | profile | financials | validation

  // Modals & Messages
  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false);
  const [isBrowseModalOpen, setIsBrowseModalOpen] = useState(false);
  const [allCompaniesList, setAllCompaniesList] = useState([]);
  const [providerStatus, setProviderStatus] = useState(null);
  const [alphaKeyInput, setAlphaKeyInput] = useState('');
  const [twelveKeyInput, setTwelveKeyInput] = useState('');
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const [notification, setNotification] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Load all market data for selected stock
  const loadStockData = async (ticker, market) => {
    setIsLoading(true);
    setErrorMsg('');
    try {
      // 1. Load OHLCV & Validation Report
      const ohlcv = await marketApi.getHistoricalOHLCV(ticker, market, chartPeriod);
      setOhlcvData(ohlcv);

      // 2. Load Company Profile
      const profile = await marketApi.getProfile(ticker, market);
      setCompanyProfile(profile);

      // 3. Load Financial Statements
      const fin = await marketApi.getFinancials(ticker, market, financialPeriod);
      setFinancials(fin);

      // 4. Load Fundamental Analysis Agent Report
      const fund = await marketApi.getFundamentalAnalysis(ticker, market, financialPeriod);
      setFundamentalAnalysis(fund);
    } catch (err) {
      setErrorMsg(err.message || 'Error retrieving market data.');
    } finally {
      setIsLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadStockData(selectedStock, selectedMarket);
    loadProviderStatus();
    loadAllCompanies();
  }, [selectedStock, selectedMarket, chartPeriod, financialPeriod]);

  const loadAllCompanies = async () => {
    try {
      const list = await marketApi.search('', 'ALL');
      if (list && list.length > 0) {
        setAllCompaniesList(list);
      }
    } catch {
      // Fallback
    }
  };

  const loadProviderStatus = async () => {
    try {
      const status = await marketApi.getStatus();
      setProviderStatus(status);
    } catch {
      // Keep silent fallback
    }
  };

  // Search handler
  const handleSearchChange = async (e) => {
    const val = e.target.value;
    setSearchQuery(val);
    if (val.trim().length > 0) {
      setIsSearching(true);
      try {
        const res = await marketApi.search(val, selectedMarket === 'ALL' ? null : selectedMarket);
        setSearchResults(res);
      } catch {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    } else {
      setSearchResults([]);
    }
  };

  const handleSelectSearchResult = (stock) => {
    setSelectedStock(stock.ticker);
    setSelectedMarket(stock.market);
    setSelectedStockInfo(stock);
    setSearchQuery('');
    setSearchResults([]);
  };

  const handleMarketChange = (mkt) => {
    setSelectedMarket(mkt);
    setSearchQuery('');
    setSearchResults([]);
    // Default to prominent equity in that market
    const defaultTicker = {
      NSE: 'RELIANCE',
      BSE: 'BSE',
      NASDAQ: 'AAPL',
      NYSE: 'JPM',
      ALL: 'RELIANCE'
    }[mkt] || 'RELIANCE';
    setSelectedStock(defaultTicker);
  };

  const handleAddToWatchlist = async () => {
    try {
      await watchlistApi.add(selectedStock);
      setNotification(`Added ${selectedStock} to your watchlist!`);
      setTimeout(() => setNotification(''), 3000);
    } catch (err) {
      setNotification(err.message || 'Already in watchlist or could not add.');
      setTimeout(() => setNotification(''), 3500);
    }
  };

  const handleSaveApiKeys = async (e) => {
    e.preventDefault();
    try {
      const updated = await marketApi.updateKeys(alphaKeyInput, twelveKeyInput);
      setProviderStatus(updated);
      setIsKeyModalOpen(false);
      setNotification('API keys successfully updated and tested!');
      setTimeout(() => setNotification(''), 3000);
      loadStockData(selectedStock, selectedMarket);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to update keys');
    }
  };

  // Price calculations
  const points = ohlcvData?.points || [];
  const latestCandle = points.length > 0 ? points[points.length - 1] : null;
  const prevCandle = points.length > 1 ? points[points.length - 2] : latestCandle;
  const currentPrice = latestCandle?.close || ohlcvData?.current_price || 0;
  const priceChange = prevCandle ? roundNum(currentPrice - prevCandle.close) : 0;
  const priceChangePct = prevCandle && prevCandle.close ? roundNum((priceChange / prevCandle.close) * 100) : 0;
  const isPositive = priceChange >= 0;

  function roundNum(num) {
    return Math.round((num + Number.EPSILON) * 100) / 100;
  }

  // SVG Chart rendering helper
  const renderInteractiveChart = () => {
    if (!points || points.length === 0) return null;

    const width = 800;
    const height = 280;
    const padding = { top: 20, right: 30, bottom: 40, left: 60 };

    const minPrice = Math.min(...points.map((p) => p.low)) * 0.985;
    const maxPrice = Math.max(...points.map((p) => p.high)) * 1.015;
    const priceRange = maxPrice - minPrice || 1;

    const maxVolume = Math.max(...points.map((p) => p.volume || 1));

    const getX = (idx) => padding.left + (idx / (points.length - 1)) * (width - padding.left - padding.right);
    const getY = (val) => height - padding.bottom - ((val - minPrice) / priceRange) * (height - padding.top - padding.bottom);

    // Build line path
    const pathD = points.reduce((acc, pt, idx) => {
      const x = getX(idx);
      const y = getY(pt.close);
      return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, '');

    // Build area fill
    const areaD = `${pathD} L ${getX(points.length - 1)} ${height - padding.bottom} L ${getX(0)} ${height - padding.bottom} Z`;

    return (
      <div className="relative w-full overflow-hidden">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-72 select-none"
          onMouseLeave={() => setHoveredPoint(null)}
        >
          <defs>
            <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={isPositive ? '#10B981' : '#EF4444'} stopOpacity="0.35" />
              <stop offset="100%" stopColor={isPositive ? '#10B981' : '#EF4444'} stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
            const yVal = minPrice + priceRange * pct;
            const yPos = getY(yVal);
            return (
              <g key={i}>
                <line
                  x1={padding.left}
                  y1={yPos}
                  x2={width - padding.right}
                  y2={yPos}
                  stroke="#E2E8F0"
                  strokeDasharray="4 4"
                  strokeWidth="1"
                />
                <text
                  x={padding.left - 8}
                  y={yPos + 4}
                  textAnchor="end"
                  className="text-[10px] fill-slate-400 font-mono"
                >
                  {ohlcvData?.currency === 'INR' ? '₹' : '$'}
                  {roundNum(yVal).toLocaleString()}
                </text>
              </g>
            );
          })}

          {/* Volume bars at bottom */}
          {points.map((pt, idx) => {
            const x = getX(idx);
            const barW = Math.max(2, (width - padding.left - padding.right) / points.length - 2);
            const vHeight = (pt.volume / maxVolume) * 45;
            const isUp = pt.close >= pt.open;
            return (
              <rect
                key={`vol-${idx}`}
                x={x - barW / 2}
                y={height - padding.bottom - vHeight}
                width={barW}
                height={vHeight}
                fill={isUp ? '#10B981' : '#EF4444'}
                opacity="0.25"
              />
            );
          })}

          {/* Area fill */}
          <path d={areaD} fill="url(#chartGrad)" />

          {/* Price Line */}
          <path
            d={pathD}
            fill="none"
            stroke={isPositive ? '#10B981' : '#EF4444'}
            strokeWidth="2.5"
            strokeLinecap="round"
          />

          {/* Interactive hover points */}
          {points.map((pt, idx) => {
            const x = getX(idx);
            const y = getY(pt.close);
            return (
              <circle
                key={`pt-${idx}`}
                cx={x}
                cy={y}
                r={hoveredPoint?.date === pt.date ? 5 : 3}
                fill={hoveredPoint?.date === pt.date ? (isPositive ? '#10B981' : '#EF4444') : 'white'}
                stroke={isPositive ? '#10B981' : '#EF4444'}
                strokeWidth="2"
                className="cursor-pointer transition-all"
                onMouseEnter={() => setHoveredPoint(pt)}
              />
            );
          })}

          {/* Date labels */}
          {points.filter((_, i) => i % Math.ceil(points.length / 6) === 0 || i === points.length - 1).map((pt, i) => (
            <text
              key={`date-${i}`}
              x={getX(points.indexOf(pt))}
              y={height - padding.bottom + 18}
              textAnchor="middle"
              className="text-[10px] fill-slate-500 font-mono"
            >
              {pt.display_date || pt.date}
            </text>
          ))}
        </svg>

        {/* Floating Tooltip */}
        {hoveredPoint && (
          <div className="absolute top-3 left-16 bg-slate-900/90 backdrop-blur-md text-white text-xs px-3.5 py-2 rounded-xl shadow-xl border border-slate-700 font-mono flex items-center space-x-4 pointer-events-none z-10">
            <span className="font-bold text-[#8DB9F0]">{hoveredPoint.date}</span>
            <span>O: <strong className="text-white">{hoveredPoint.open}</strong></span>
            <span>H: <strong className="text-emerald-400">{hoveredPoint.high}</strong></span>
            <span>L: <strong className="text-rose-400">{hoveredPoint.low}</strong></span>
            <span>C: <strong className="text-amber-300">{hoveredPoint.close}</strong></span>
            <span>Vol: <strong className="text-slate-300">{hoveredPoint.volume.toLocaleString()}</strong></span>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Controls: Market Selector & Search Bar */}
      <div className="glass-panel rounded-3xl p-6 bg-white/95 border border-[#8DB9F0]/25 shadow-lg shadow-[#8DB9F0]/10">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          {/* Market Selector Tabs */}
          <div className="flex items-center space-x-1.5 p-1 bg-slate-100 rounded-2xl w-fit">
            {['NSE', 'BSE', 'NASDAQ', 'NYSE', 'ALL'].map((mkt) => (
              <button
                key={mkt}
                onClick={() => handleMarketChange(mkt)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  selectedMarket === mkt
                    ? 'bg-white text-slate-900 shadow-sm shadow-slate-200 font-extrabold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {mkt === 'NSE' && '🇮🇳 NSE'}
                {mkt === 'BSE' && '🇮🇳 BSE'}
                {mkt === 'NASDAQ' && '🇺🇸 NASDAQ'}
                {mkt === 'NYSE' && '🇺🇸 NYSE'}
                {mkt === 'ALL' && '🌐 All Markets'}
              </button>
            ))}
          </div>

          {/* Search Bar with Autocomplete Dropdown */}
          <div className="relative flex-1 max-w-lg">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={handleSearchChange}
                placeholder={`Search company or ticker in ${selectedMarket} (e.g. AAPL, Reliance, TCS, Nvidia)...`}
                className="w-full pl-10 pr-10 py-2.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-[#8DB9F0] focus:bg-white transition-all"
              />
              {isSearching && (
                <RefreshCw className="w-4 h-4 text-[#8DB9F0] absolute right-3.5 top-1/2 -translate-y-1/2 animate-spin" />
              )}
            </div>

            {/* Autocomplete Dropdown */}
            {searchResults.length > 0 && (
              <div className="absolute left-0 right-0 top-full mt-2 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden z-30 max-h-72 overflow-y-auto">
                <div className="p-2 border-b border-slate-100 text-[11px] font-mono font-semibold text-slate-400 uppercase tracking-wider">
                  Discovered Equities ({searchResults.length})
                </div>
                {searchResults.map((item) => (
                  <button
                    key={`${item.market}-${item.ticker}`}
                    onClick={() => handleSelectSearchResult(item)}
                    className="w-full text-left px-4 py-2.5 hover:bg-[#8DB9F0]/10 flex items-center justify-between transition-colors border-b border-slate-50 last:border-b-0"
                  >
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-extrabold text-slate-900 text-xs font-mono">{item.ticker}</span>
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-slate-100 text-slate-600">
                          {item.market}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 truncate max-w-xs">{item.name}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-mono font-bold text-slate-800">
                        {item.currency === 'INR' ? '₹' : '$'}
                        {item.base_price?.toFixed(2)}
                      </span>
                      <p className="text-[10px] text-slate-400">{item.sector || 'Equities'}</p>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Action Buttons: Browse All & API Keys */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsBrowseModalOpen(true)}
              className="flex items-center space-x-1.5 px-3.5 py-2.5 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 text-blue-900 rounded-2xl text-xs font-bold hover:bg-blue-100 transition-all shadow-xs"
              title="Browse entire directory of supported companies"
            >
              <Compass className="w-3.5 h-3.5 text-blue-600" />
              <span>Browse All Stocks ({allCompaniesList.length || 18})</span>
            </button>

            <button
              onClick={() => setIsKeyModalOpen(true)}
              className="flex items-center space-x-1.5 px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-2xl text-xs font-bold transition-all"
              title="Configure Free Alpha Vantage & Twelve Data API Keys"
            >
              <Key className="w-3.5 h-3.5 text-[#e67e22]" />
              <span>Free API Keys</span>
            </button>
          </div>
        </div>

        {/* Quick Select Clickable Stock Pills Bar */}
        <div className="mt-4 pt-3.5 border-t border-slate-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#F5B69E]" />
              <span>Quick Select {selectedMarket} Equities (Click to View):</span>
            </span>
            <span className="text-[10px] text-slate-400 font-mono">
              Current: <strong className="text-slate-800">{selectedStock}</strong>
            </span>
          </div>
          <div className="flex items-center space-x-2 overflow-x-auto pb-1 scrollbar-none">
            {(POPULAR_EQUITIES[selectedMarket] || POPULAR_EQUITIES.NSE).map((item) => {
              const isCurrent = selectedStock === item.ticker;
              return (
                <button
                  key={`${item.ticker}-${item.market || selectedMarket}`}
                  onClick={() => {
                    setSelectedStock(item.ticker);
                    if (item.market && item.market !== selectedMarket) {
                      setSelectedMarket(item.market);
                    }
                    setSelectedStockInfo({
                      ticker: item.ticker,
                      name: item.name,
                      market: item.market || selectedMarket,
                      currency: (item.market || selectedMarket) in ['NASDAQ', 'NYSE'] ? 'USD' : 'INR'
                    });
                  }}
                  className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all flex items-center space-x-1.5 flex-shrink-0 cursor-pointer ${
                    isCurrent
                      ? 'bg-gradient-to-r from-[#1e3a8a] to-[#2563eb] text-white shadow-md shadow-blue-500/25 ring-2 ring-blue-400 scale-105'
                      : 'bg-slate-100 hover:bg-slate-200 text-slate-700 hover:text-slate-900 border border-slate-200'
                  }`}
                >
                  <span>{item.ticker}</span>
                  <span className={`text-[10px] font-normal ${isCurrent ? 'text-blue-100' : 'text-slate-500'}`}>
                    ({item.price || item.name.split(' ')[0]})
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Notification Banner */}
      {notification && (
        <div className="flex items-center space-x-2 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-2xl text-xs font-medium animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{notification}</span>
        </div>
      )}

      {errorMsg && (
        <div className="flex items-center space-x-2 p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-xs font-medium">
          <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Stock Header Card */}
      <div className="glass-panel rounded-3xl p-6 sm:p-8 bg-white border border-[#8DB9F0]/30 shadow-xl shadow-[#8DB9F0]/10">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-slate-100">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono tracking-tight">
                {selectedStock}
              </span>

              {/* In-Card Quick Switcher Dropdown */}
              <select
                value={selectedStock}
                onChange={(e) => {
                  const t = e.target.value;
                  const found = (allCompaniesList.length > 0 ? allCompaniesList : (POPULAR_EQUITIES[selectedMarket] || POPULAR_EQUITIES.ALL)).find(c => c.ticker === t);
                  if (found) {
                    handleSelectSearchResult(found);
                  } else {
                    setSelectedStock(t);
                  }
                }}
                className="text-xs font-mono font-bold bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded-xl px-2.5 py-1 text-slate-700 cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#8DB9F0]"
                title="Quick switch to another company"
              >
                <option value="" disabled>Switch Company...</option>
                {(allCompaniesList.length > 0 ? allCompaniesList : (POPULAR_EQUITIES[selectedMarket] || POPULAR_EQUITIES.ALL)).map((c) => (
                  <option key={`opt-${c.market}-${c.ticker}`} value={c.ticker}>
                    {c.ticker} - {c.name} ({c.market})
                  </option>
                ))}
              </select>

              <span className="px-2.5 py-1 rounded-xl text-xs font-extrabold bg-[#8DB9F0]/15 text-[#1e3a8a] border border-[#8DB9F0]/30 font-mono">
                {ohlcvData?.market || selectedMarket}
              </span>
              <span className="text-xs px-2.5 py-1 rounded-xl bg-slate-100 text-slate-600 font-medium">
                {companyProfile?.sector || selectedStockInfo.sector || 'Equities'}
              </span>
            </div>
            <h2 className="text-sm sm:text-base font-semibold text-slate-600">
              {companyProfile?.name || selectedStockInfo.name}
            </h2>

            {/* Source & Retrieval Timestamp Badges */}
            <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] font-mono">
              <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 font-medium">
                <Database className="w-3 h-3 text-emerald-500" />
                <span>Source: {ohlcvData?.data_source || 'Market Data Engine'}</span>
              </span>
              <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-600">
                <Calendar className="w-3 h-3 text-slate-400" />
                <span>Retrieved: {ohlcvData?.retrieval_timestamp || new Date().toISOString()}</span>
              </span>
            </div>
          </div>

          {/* Live Price & Change */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="text-left sm:text-right">
              <div className="text-3xl sm:text-4xl font-extrabold font-mono text-slate-900 tracking-tight">
                {ohlcvData?.currency === 'INR' ? '₹' : '$'}
                {currentPrice.toLocaleString()}
              </div>
              <div className={`flex items-center sm:justify-end space-x-1 text-xs font-bold font-mono mt-1 ${isPositive ? 'text-emerald-600' : 'text-rose-600'}`}>
                {isPositive ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                <span>{isPositive ? '+' : ''}{priceChange} ({isPositive ? '+' : ''}{priceChangePct}%)</span>
                <span className="text-slate-400 font-normal">24h</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-2">
              <button
                onClick={handleAddToWatchlist}
                className="px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-2xl flex items-center space-x-1.5 transition-all"
                title="Save to your institutional watchlist"
              >
                <Plus className="w-4 h-4" />
                <span>Watchlist</span>
              </button>
              {onLaunchTask && (
                <button
                  onClick={() => onLaunchTask(selectedStock)}
                  className="px-4 py-2.5 bg-gradient-to-r from-[#F5B69E] to-[#ea9e80] hover:from-[#f0a68d] hover:to-[#df8b6b] text-slate-900 text-xs font-bold rounded-2xl flex items-center space-x-1.5 shadow-md shadow-[#F5B69E]/25 transition-all"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Research Task</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* OHLCV Summary Bar */}
        {latestCandle && (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-4 mt-2">
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
              <p className="text-[10px] uppercase font-mono text-slate-400 font-semibold">Open</p>
              <p className="text-xs font-mono font-bold text-slate-800">
                {ohlcvData?.currency === 'INR' ? '₹' : '$'}{latestCandle.open}
              </p>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
              <p className="text-[10px] uppercase font-mono text-slate-400 font-semibold">Day High</p>
              <p className="text-xs font-mono font-bold text-emerald-600">
                {ohlcvData?.currency === 'INR' ? '₹' : '$'}{latestCandle.high}
              </p>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
              <p className="text-[10px] uppercase font-mono text-slate-400 font-semibold">Day Low</p>
              <p className="text-xs font-mono font-bold text-rose-600">
                {ohlcvData?.currency === 'INR' ? '₹' : '$'}{latestCandle.low}
              </p>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
              <p className="text-[10px] uppercase font-mono text-slate-400 font-semibold">Prev Close</p>
              <p className="text-xs font-mono font-bold text-slate-800">
                {ohlcvData?.currency === 'INR' ? '₹' : '$'}{prevCandle ? prevCandle.close : latestCandle.close}
              </p>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 col-span-2 sm:col-span-1">
              <p className="text-[10px] uppercase font-mono text-slate-400 font-semibold">Day Volume</p>
              <p className="text-xs font-mono font-bold text-slate-800">
                {latestCandle.volume.toLocaleString()}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Sub-Tabs: Interactive Chart | Company Profile | Financial Statements | Data Validation */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-200 pb-3 gap-3">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveSubTab('chart')}
            className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-extrabold transition-all ${
              activeSubTab === 'chart'
                ? 'bg-white text-slate-900 shadow-md border border-slate-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5 text-[#3575cb]" />
            <span>Interactive OHLCV Chart</span>
          </button>

          <button
            onClick={() => setActiveSubTab('fundamental')}
            className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-extrabold transition-all ${
              activeSubTab === 'fundamental'
                ? 'bg-white text-slate-900 shadow-md border border-slate-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5 text-indigo-600" />
            <span>Fundamental Agent</span>
            {fundamentalAnalysis?.valuation_status && (
              <span className="ml-1 text-[10px] font-mono font-bold px-1.5 py-0.2 rounded-full bg-indigo-100 text-indigo-800">
                {fundamentalAnalysis.valuation_status}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveSubTab('profile')}
            className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-extrabold transition-all ${
              activeSubTab === 'profile'
                ? 'bg-white text-slate-900 shadow-md border border-slate-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Building className="w-3.5 h-3.5 text-[#8e44ad]" />
            <span>Company Profile</span>
          </button>

          <button
            onClick={() => setActiveSubTab('financials')}
            className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-extrabold transition-all ${
              activeSubTab === 'financials'
                ? 'bg-white text-slate-900 shadow-md border border-slate-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Table className="w-3.5 h-3.5 text-[#e67e22]" />
            <span>Financial Statements</span>
          </button>

          <button
            onClick={() => setActiveSubTab('validation')}
            className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-extrabold transition-all ${
              activeSubTab === 'validation'
                ? 'bg-white text-slate-900 shadow-md border border-slate-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span>Data Validation Engine</span>
            {ohlcvData?.validation && (
              <span className="ml-1 text-[10px] font-mono font-bold px-1.5 py-0.2 rounded-full bg-emerald-100 text-emerald-800">
                {ohlcvData.validation.quality_score}%
              </span>
            )}
          </button>
        </div>

        {/* Timeframe selector when Chart is active */}
        {activeSubTab === 'chart' && (
          <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl">
            {['1 Month', '3 Months', '6 Months', '1 Year', '5 Years'].map((p) => (
              <button
                key={p}
                onClick={() => setChartPeriod(p)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-mono font-bold transition-all ${
                  chartPeriod === p
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Content for Active Sub-Tab */}
      {isLoading ? (
        <div className="glass-panel rounded-3xl p-16 flex flex-col items-center justify-center space-y-3 bg-white">
          <RefreshCw className="w-8 h-8 text-[#8DB9F0] animate-spin" />
          <p className="text-xs text-slate-500 font-mono">Retrieving market data & running integrity validation...</p>
        </div>
      ) : (
        <>
          {/* TAB 1: INTERACTIVE OHLCV CHART */}
          {activeSubTab === 'chart' && (
            <div className="glass-panel rounded-3xl p-6 bg-white border border-slate-200 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xs font-mono font-extrabold text-slate-800 uppercase tracking-wider">
                    Candlestick & Volume Timeline ({chartPeriod})
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    Hover over data points to inspect detailed Open, High, Low, Close, and Volume indicators.
                  </p>
                </div>
                <div className="flex items-center space-x-2 text-[11px] font-mono">
                  <span className="flex items-center space-x-1 text-emerald-600">
                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span>Bullish Candle</span>
                  </span>
                  <span className="flex items-center space-x-1 text-rose-600">
                    <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                    <span>Bearish Candle</span>
                  </span>
                </div>
              </div>

              {renderInteractiveChart()}
            </div>
          )}

          {/* TAB 1B: MODULE 3 - FUNDAMENTAL ANALYSIS AGENT */}
          {activeSubTab === 'fundamental' && fundamentalAnalysis && (
            <div className="space-y-6">
              {/* Executive Summary & Valuation Banner */}
              <div className="glass-panel rounded-3xl p-6 bg-gradient-to-r from-indigo-50/90 via-white to-blue-50/90 border border-indigo-200 shadow-md">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-indigo-100">
                  <div>
                    <div className="flex items-center space-x-2 text-xs font-mono font-bold text-indigo-700 mb-1">
                      <TrendingUp className="w-4 h-4 text-indigo-600" />
                      <span>Autonomous Fundamental Analysis Agent</span>
                    </div>
                    <h3 className="text-lg font-extrabold text-slate-900">
                      {fundamentalAnalysis.company_name} ({fundamentalAnalysis.ticker}) — Financial Health & Valuation
                    </h3>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="px-3 py-1.5 rounded-xl text-xs font-mono font-bold bg-white border border-indigo-200 text-indigo-900">
                      Health: {fundamentalAnalysis.health}
                    </span>
                    <span className={`px-3 py-1.5 rounded-xl text-xs font-mono font-extrabold ${
                      fundamentalAnalysis.valuation_status === 'Undervalued'
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        : fundamentalAnalysis.valuation_status === 'Fairly Valued'
                        ? 'bg-blue-100 text-blue-800 border border-blue-200'
                        : 'bg-amber-100 text-amber-800 border border-amber-200'
                    }`}>
                      {fundamentalAnalysis.valuation_status} ({fundamentalAnalysis.margin_of_safety})
                    </span>
                  </div>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed pt-3">
                  {fundamentalAnalysis.summary}
                </p>
              </div>

              {/* Key Valuation Ratios Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">P/E Ratio</span>
                  <p className="text-lg font-extrabold text-slate-900 font-mono mt-1">{fundamentalAnalysis.pe_ratio}</p>
                </div>
                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">P/B Ratio</span>
                  <p className="text-lg font-extrabold text-slate-900 font-mono mt-1">{fundamentalAnalysis.pb_ratio}</p>
                </div>
                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Return on Equity (ROE)</span>
                  <p className="text-lg font-extrabold text-emerald-700 font-mono mt-1">{fundamentalAnalysis.roe}</p>
                </div>
                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Return on Assets (ROA)</span>
                  <p className="text-lg font-extrabold text-slate-900 font-mono mt-1">{fundamentalAnalysis.valuation_ratios?.roa || 'N/A'}</p>
                </div>
                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Debt / Equity</span>
                  <p className="text-lg font-extrabold text-slate-900 font-mono mt-1">{fundamentalAnalysis.debt_to_equity}</p>
                </div>
                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">DCF Fair Value</span>
                  <p className="text-lg font-extrabold text-indigo-700 font-mono mt-1">
                    {fundamentalAnalysis.currency === 'INR' ? '₹' : '$'}{fundamentalAnalysis.dcf_fair_value}
                  </p>
                </div>
              </div>

              {/* 3-Column Deep Analysis Cards: Revenue & Earnings | Profitability | Debt & Stability */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div className="p-5 rounded-3xl bg-white border border-slate-200 shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-mono font-extrabold uppercase text-slate-800">1. Revenue & Earnings</h4>
                    <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded-lg bg-emerald-50 text-emerald-700">
                      {fundamentalAnalysis.revenue_and_earnings?.trend}
                    </span>
                  </div>
                  <div className="text-xs font-mono text-slate-600 space-y-1 pt-1">
                    <p>YoY Revenue Growth: <strong className="text-slate-900">{fundamentalAnalysis.revenue_and_earnings?.latest_yoy_revenue_growth_display}</strong></p>
                    <p>3Y Revenue CAGR: <strong className="text-slate-900">{fundamentalAnalysis.revenue_and_earnings?.revenue_cagr_pct ?? 'N/A'}%</strong></p>
                    <p>YoY Earnings Growth: <strong className="text-slate-900">{fundamentalAnalysis.revenue_and_earnings?.latest_yoy_earnings_growth_pct ?? 'N/A'}%</strong></p>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-relaxed pt-2 border-t border-slate-100">
                    {fundamentalAnalysis.revenue_and_earnings?.narrative}
                  </p>
                </div>

                <div className="p-5 rounded-3xl bg-white border border-slate-200 shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-mono font-extrabold uppercase text-slate-800">2. Profitability</h4>
                    <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded-lg bg-blue-50 text-blue-700">
                      {fundamentalAnalysis.profitability?.margin_trend}
                    </span>
                  </div>
                  <div className="text-xs font-mono text-slate-600 space-y-1 pt-1">
                    <p>Gross Margin: <strong className="text-slate-900">{fundamentalAnalysis.profitability?.gross_margin_pct ?? 'N/A'}%</strong></p>
                    <p>Operating Margin: <strong className="text-slate-900">{fundamentalAnalysis.profitability?.operating_margin_pct ?? 'N/A'}%</strong></p>
                    <p>Net Margin: <strong className="text-slate-900">{fundamentalAnalysis.profitability?.net_margin_display}</strong></p>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-relaxed pt-2 border-t border-slate-100">
                    {fundamentalAnalysis.profitability?.narrative}
                  </p>
                </div>

                <div className="p-5 rounded-3xl bg-white border border-slate-200 shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-mono font-extrabold uppercase text-slate-800">3. Debt & Stability</h4>
                    <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded-lg bg-indigo-50 text-indigo-700">
                      {fundamentalAnalysis.debt_and_stability?.stability_rating}
                    </span>
                  </div>
                  <div className="text-xs font-mono text-slate-600 space-y-1 pt-1">
                    <p>Debt-to-Equity: <strong className="text-slate-900">{fundamentalAnalysis.debt_and_stability?.debt_to_equity}</strong></p>
                    <p>Current Ratio: <strong className="text-slate-900">{fundamentalAnalysis.debt_and_stability?.current_ratio ?? 'N/A'}x</strong></p>
                    <p>Position: <strong className="text-slate-900">{fundamentalAnalysis.debt_and_stability?.net_position}</strong></p>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-relaxed pt-2 border-t border-slate-100">
                    {fundamentalAnalysis.debt_and_stability?.narrative}
                  </p>
                </div>
              </div>

              {/* Historical Financial Performance Comparison */}
              {fundamentalAnalysis.historical_comparison?.length > 0 && (
                <div className="glass-panel rounded-3xl p-6 bg-white border border-slate-200 shadow-sm">
                  <h4 className="text-xs font-mono font-extrabold uppercase text-slate-800 mb-3">
                    4. Historical Financial Performance Comparison ({fundamentalAnalysis.currency})
                  </h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs font-mono">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-400 text-left">
                          <th className="py-2 font-bold">Period</th>
                          <th className="py-2 text-right font-bold">Revenue</th>
                          <th className="py-2 text-right font-bold">YoY Growth</th>
                          <th className="py-2 text-right font-bold">Net Income</th>
                          <th className="py-2 text-right font-bold">Net Margin</th>
                          <th className="py-2 text-right font-bold">EPS</th>
                          <th className="py-2 text-right font-bold">ROE</th>
                          <th className="py-2 text-right font-bold">Debt/Eq</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {fundamentalAnalysis.historical_comparison.map((row, i) => (
                          <tr key={i} className="hover:bg-slate-50">
                            <td className="py-2 font-bold text-slate-800">{row.period}</td>
                            <td className="py-2 text-right text-slate-800">{row.revenue?.toLocaleString() ?? 'N/A'}</td>
                            <td className="py-2 text-right text-emerald-600 font-bold">
                              {row.yoy_revenue_growth_pct !== null ? `${row.yoy_revenue_growth_pct > 0 ? '+' : ''}${row.yoy_revenue_growth_pct}%` : '—'}
                            </td>
                            <td className="py-2 text-right text-slate-800">{row.net_income?.toLocaleString() ?? 'N/A'}</td>
                            <td className="py-2 text-right text-slate-700">{row.net_margin_pct ?? 'N/A'}%</td>
                            <td className="py-2 text-right text-slate-700">{row.eps ?? 'N/A'}</td>
                            <td className="py-2 text-right text-indigo-700 font-bold">{row.roe_pct ?? 'N/A'}%</td>
                            <td className="py-2 text-right text-slate-700">{row.debt_to_equity ?? 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Peer Comparison */}
              {fundamentalAnalysis.peer_comparison?.peers?.length > 0 && (
                <div className="glass-panel rounded-3xl p-6 bg-white border border-slate-200 shadow-sm space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <h4 className="text-xs font-mono font-extrabold uppercase text-slate-800">
                      5. Sector & Market Peer Comparison
                    </h4>
                    <span className="text-xs font-mono font-bold text-indigo-700 bg-indigo-50 px-3 py-1 rounded-xl">
                      {fundamentalAnalysis.peer_comparison.relative_valuation_verdict}
                    </span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs font-mono">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-400 text-left">
                          <th className="py-2 font-bold">Company</th>
                          <th className="py-2 font-bold">Market</th>
                          <th className="py-2 text-right font-bold">Market Cap</th>
                          <th className="py-2 text-right font-bold">P/E</th>
                          <th className="py-2 text-right font-bold">ROE</th>
                          <th className="py-2 text-right font-bold">Net Margin</th>
                          <th className="py-2 text-right font-bold">Debt/Eq</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        <tr className="bg-blue-50/60 font-bold">
                          <td className="py-2 text-blue-900">{fundamentalAnalysis.ticker} (Target)</td>
                          <td className="py-2 text-blue-800">{fundamentalAnalysis.market}</td>
                          <td className="py-2 text-right text-blue-900">{companyProfile?.market_cap || '—'}</td>
                          <td className="py-2 text-right text-blue-900">{fundamentalAnalysis.pe_ratio}</td>
                          <td className="py-2 text-right text-blue-900">{fundamentalAnalysis.roe}</td>
                          <td className="py-2 text-right text-blue-900">{fundamentalAnalysis.profitability?.net_margin_display}</td>
                          <td className="py-2 text-right text-blue-900">{fundamentalAnalysis.debt_to_equity}</td>
                        </tr>
                        {fundamentalAnalysis.peer_comparison.peers.map((p, i) => (
                          <tr key={i} className="hover:bg-slate-50">
                            <td className="py-2 font-bold text-slate-800">{p.ticker} <span className="font-normal text-slate-500">({p.name})</span></td>
                            <td className="py-2 text-slate-600">{p.market}</td>
                            <td className="py-2 text-right text-slate-700">{p.market_cap || '—'}</td>
                            <td className="py-2 text-right text-slate-800">{p.pe_ratio ? `${p.pe_ratio}x` : 'N/A'}</td>
                            <td className="py-2 text-right text-slate-800">{p.roe_pct ? `${p.roe_pct}%` : 'N/A'}</td>
                            <td className="py-2 text-right text-slate-800">{p.net_margin_pct ? `${p.net_margin_pct}%` : 'N/A'}</td>
                            <td className="py-2 text-right text-slate-800">{p.debt_to_equity ?? 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Missing or Inconsistent Financial Information Audit */}
              {fundamentalAnalysis.data_quality_audit && (
                <div className="glass-panel rounded-3xl p-6 bg-white border border-slate-200 shadow-sm space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-mono font-extrabold uppercase text-slate-800">
                      6. Financial Data Completeness & Consistency Audit
                    </h4>
                    <span className={`text-xs font-mono font-bold px-3 py-1 rounded-xl ${
                      fundamentalAnalysis.data_quality_audit.is_consistent && !fundamentalAnalysis.data_quality_audit.has_missing_data
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-amber-50 text-amber-800 border border-amber-200'
                    }`}>
                      Completeness: {fundamentalAnalysis.data_quality_audit.completeness_score_pct}%
                    </span>
                  </div>
                  <p className="text-xs text-slate-600">{fundamentalAnalysis.data_quality_audit.audit_summary}</p>
                  {(fundamentalAnalysis.data_quality_audit.missing_fields?.length > 0 || fundamentalAnalysis.data_quality_audit.inconsistencies_found?.length > 0) && (
                    <div className="space-y-1.5 pt-2 text-xs font-mono">
                      {fundamentalAnalysis.data_quality_audit.missing_fields?.map((m, i) => (
                        <div key={`miss-${i}`} className="p-2 rounded-xl bg-amber-50 text-amber-800 border border-amber-200">
                          Missing: {m}
                        </div>
                      ))}
                      {fundamentalAnalysis.data_quality_audit.inconsistencies_found?.map((inc, i) => (
                        <div key={`inc-${i}`} className="p-2 rounded-xl bg-rose-50 text-rose-800 border border-rose-200">
                          Inconsistency: {inc}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: COMPANY PROFILE */}
          {activeSubTab === 'profile' && companyProfile && (
            <div className="space-y-6">
              {/* Profile Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Market Capitalization</span>
                  <p className="text-base font-extrabold text-slate-900 font-mono mt-1">{companyProfile.market_cap}</p>
                </div>
                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">P/E Ratio (TTM)</span>
                  <p className="text-base font-extrabold text-slate-900 font-mono mt-1">{companyProfile.pe_ratio}</p>
                </div>
                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">52-Week Range</span>
                  <p className="text-base font-extrabold text-slate-900 font-mono mt-1">
                    {companyProfile.currency === 'INR' ? '₹' : '$'}{companyProfile.week_52_low} - {companyProfile.currency === 'INR' ? '₹' : '$'}{companyProfile.week_52_high}
                  </p>
                </div>
                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Dividend Yield</span>
                  <p className="text-base font-extrabold text-slate-900 font-mono mt-1">{companyProfile.dividend_yield}%</p>
                </div>
              </div>

              {/* Company Info & Description */}
              <div className="glass-panel rounded-3xl p-6 bg-white border border-slate-200 shadow-md space-y-4">
                <h3 className="text-sm font-extrabold text-slate-900">Business Overview & Regulatory Profile</h3>
                <p className="text-xs text-slate-600 leading-relaxed">{companyProfile.description}</p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-slate-100 text-xs">
                  <div>
                    <span className="text-slate-400 font-mono">Chief Executive Officer:</span>
                    <p className="font-bold text-slate-800 mt-0.5">{companyProfile.ceo || 'Executive Leadership'}</p>
                  </div>
                  <div>
                    <span className="text-slate-400 font-mono">Headquarters:</span>
                    <p className="font-bold text-slate-800 mt-0.5">{companyProfile.headquarters || 'Corporate Office'}</p>
                  </div>
                  <div>
                    <span className="text-slate-400 font-mono">Full-Time Employees:</span>
                    <p className="font-bold text-slate-800 mt-0.5">{companyProfile.employees ? companyProfile.employees.toLocaleString() : 'N/A'}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: FINANCIAL STATEMENTS */}
          {activeSubTab === 'financials' && financials && (
            <div className="glass-panel rounded-3xl p-6 bg-white border border-slate-200 shadow-md space-y-6">
              {/* Financial Sub-Navigation */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
                <div className="flex items-center space-x-1.5">
                  <button
                    onClick={() => setFinancialTab('income')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                      financialTab === 'income' ? 'bg-[#8DB9F0]/20 text-[#1e3a8a]' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Income Statement
                  </button>
                  <button
                    onClick={() => setFinancialTab('balance')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                      financialTab === 'balance' ? 'bg-[#8DB9F0]/20 text-[#1e3a8a]' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Balance Sheet
                  </button>
                  <button
                    onClick={() => setFinancialTab('cashflow')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                      financialTab === 'cashflow' ? 'bg-[#8DB9F0]/20 text-[#1e3a8a]' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Cash Flow
                  </button>
                  <button
                    onClick={() => setFinancialTab('ratios')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                      financialTab === 'ratios' ? 'bg-[#8DB9F0]/20 text-[#1e3a8a]' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Key Ratios
                  </button>
                </div>

                {/* Annual vs Quarterly Toggle */}
                <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl w-fit">
                  <button
                    onClick={() => setFinancialPeriod('annual')}
                    className={`px-2.5 py-1 rounded-lg text-xs font-bold ${
                      financialPeriod === 'annual' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
                    }`}
                  >
                    Annual (FY)
                  </button>
                  <button
                    onClick={() => setFinancialPeriod('quarterly')}
                    className={`px-2.5 py-1 rounded-lg text-xs font-bold ${
                      financialPeriod === 'quarterly' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
                    }`}
                  >
                    Quarterly
                  </button>
                </div>
              </div>

              {/* Statement Tables */}
              <div className="overflow-x-auto">
                {financialTab === 'income' && (
                  <table className="w-full text-xs font-mono">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-400 text-left">
                        <th className="py-2.5 font-bold">Line Item ({financials.currency})</th>
                        {financials.income_statement.map((item, idx) => (
                          <th key={idx} className="py-2.5 text-right font-bold text-slate-700">{item.period}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">Total Revenue</td>
                        {financials.income_statement.map((item, idx) => (
                          <td key={idx} className="py-2 text-right font-bold text-slate-900">{item.total_revenue?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">Cost of Revenue (COGS)</td>
                        {financials.income_statement.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-slate-700">{item.cost_of_revenue?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr className="bg-slate-50 font-bold">
                        <td className="py-2 text-slate-800">Gross Profit</td>
                        {financials.income_statement.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-emerald-700">{item.gross_profit?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">Operating Expenses (SG&A, R&D)</td>
                        {financials.income_statement.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-slate-700">{item.operating_expenses?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">EBITDA</td>
                        {financials.income_statement.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-slate-800">{item.ebitda?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">Operating Income (EBIT)</td>
                        {financials.income_statement.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-slate-800">{item.operating_income?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr className="bg-emerald-50/60 font-extrabold">
                        <td className="py-2.5 text-emerald-900">Net Income</td>
                        {financials.income_statement.map((item, idx) => (
                          <td key={idx} className="py-2.5 text-right text-emerald-700">{item.net_income?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">Net Profit Margin</td>
                        {financials.income_statement.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-slate-700 font-bold">{item.profit_margin_pct}%</td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                )}

                {financialTab === 'balance' && (
                  <table className="w-full text-xs font-mono">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-400 text-left">
                        <th className="py-2.5 font-bold">Balance Sheet Item ({financials.currency})</th>
                        {financials.balance_sheet.map((item, idx) => (
                          <th key={idx} className="py-2.5 text-right font-bold text-slate-700">{item.period}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">Cash & Cash Equivalents</td>
                        {financials.balance_sheet.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-slate-700">{item.cash_and_equivalents?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">Total Current Assets</td>
                        {financials.balance_sheet.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-slate-800 font-bold">{item.current_assets?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr className="bg-slate-50 font-bold">
                        <td className="py-2 text-slate-800">Total Assets</td>
                        {financials.balance_sheet.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-blue-700">{item.total_assets?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">Current Liabilities</td>
                        {financials.balance_sheet.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-slate-700">{item.current_liabilities?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">Long-Term Debt</td>
                        {financials.balance_sheet.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-slate-700">{item.long_term_debt?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">Total Liabilities</td>
                        {financials.balance_sheet.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-slate-800 font-bold">{item.total_liabilities?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr className="bg-emerald-50/60 font-extrabold">
                        <td className="py-2.5 text-emerald-900">Total Stockholders' Equity</td>
                        {financials.balance_sheet.map((item, idx) => (
                          <td key={idx} className="py-2.5 text-right text-emerald-700">{item.stockholders_equity?.toLocaleString()}</td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                )}

                {financialTab === 'cashflow' && (
                  <table className="w-full text-xs font-mono">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-400 text-left">
                        <th className="py-2.5 font-bold">Cash Flow Activities ({financials.currency})</th>
                        {financials.cash_flow.map((item, idx) => (
                          <th key={idx} className="py-2.5 text-right font-bold text-slate-700">{item.period}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">Cash Flow from Operations (CFO)</td>
                        {financials.cash_flow.map((item, idx) => (
                          <td key={idx} className="py-2 text-right font-bold text-emerald-600">{item.operating_cash_flow?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">Capital Expenditures (CapEx)</td>
                        {financials.cash_flow.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-rose-600">-{item.capital_expenditures?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr className="bg-slate-50 font-bold">
                        <td className="py-2 text-slate-800">Free Cash Flow (FCF)</td>
                        {financials.cash_flow.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-emerald-700">{item.free_cash_flow?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">Cash Flow from Investing</td>
                        {financials.cash_flow.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-slate-700">{item.investing_cash_flow?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 text-slate-600 font-medium">Cash Flow from Financing</td>
                        {financials.cash_flow.map((item, idx) => (
                          <td key={idx} className="py-2 text-right text-slate-700">{item.financing_cash_flow?.toLocaleString()}</td>
                        ))}
                      </tr>
                      <tr className="bg-emerald-50/60 font-extrabold">
                        <td className="py-2.5 text-emerald-900">Net Change in Cash</td>
                        {financials.cash_flow.map((item, idx) => (
                          <td key={idx} className="py-2.5 text-right text-emerald-700">{item.net_change_in_cash?.toLocaleString()}</td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                )}

                {financialTab === 'ratios' && (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-2">
                    {Object.entries(financials.ratios).map(([key, val]) => (
                      <div key={key} className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                        <p className="text-[10px] font-mono text-slate-400 uppercase font-semibold">
                          {key.replace(/_/g, ' ')}
                        </p>
                        <p className="text-base font-extrabold text-slate-900 font-mono mt-1">{val}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: DATA VALIDATION & QUALITY REPORT */}
          {activeSubTab === 'validation' && ohlcvData?.validation && (
            <div className="space-y-6">
              {/* Quality Score Header */}
              <div className="glass-panel rounded-3xl p-6 bg-white border border-slate-200 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                <div>
                  <div className="flex items-center space-x-2 text-xs font-mono font-bold text-emerald-700 mb-1">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>Automated Data Integrity Audit Passed</span>
                  </div>
                  <h3 className="text-lg font-extrabold text-slate-900">
                    Mathematical Validation & Quality Diagnostic Report
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Checked {ohlcvData.validation.total_records} candle records for missing values, duplicate dates, and price bounds.
                  </p>
                </div>

                <div className="flex items-center space-x-3 bg-emerald-50 border border-emerald-200 px-5 py-3 rounded-2xl">
                  <span className="text-xs font-mono font-bold text-emerald-800">Quality Score:</span>
                  <span className="text-2xl font-black font-mono text-emerald-700">
                    {ohlcvData.validation.quality_score}%
                  </span>
                </div>
              </div>

              {/* Validation Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Total Input Records</span>
                  <p className="text-xl font-extrabold text-slate-900 font-mono mt-1">
                    {ohlcvData.validation.total_records}
                  </p>
                </div>
                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Missing Values Handled</span>
                  <p className="text-xl font-extrabold text-slate-900 font-mono mt-1">
                    {ohlcvData.validation.missing_values_handled}
                  </p>
                </div>
                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Duplicate Dates Removed</span>
                  <p className="text-xl font-extrabold text-slate-900 font-mono mt-1">
                    {ohlcvData.validation.duplicate_dates_removed}
                  </p>
                </div>
                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Inconsistencies Corrected</span>
                  <p className="text-xl font-extrabold text-slate-900 font-mono mt-1">
                    {ohlcvData.validation.inconsistencies_corrected}
                  </p>
                </div>
              </div>

              {/* Audit Log Table */}
              <div className="glass-panel rounded-3xl p-6 bg-white border border-slate-200 shadow-md">
                <h4 className="text-xs font-mono font-extrabold uppercase text-slate-700 tracking-wider mb-3">
                  Audit Verification Event Log
                </h4>
                <div className="space-y-2 max-h-60 overflow-y-auto font-mono text-xs">
                  {ohlcvData.validation.issues_log.map((logMsg, i) => (
                    <div key={i} className="flex items-start space-x-2 p-2 rounded-xl bg-slate-50 border border-slate-100">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mt-0.5 flex-shrink-0" />
                      <span className="text-slate-700">{logMsg}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Free API Keys Modal */}
      {isKeyModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-slate-200 space-y-6">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center space-x-2 text-xs font-mono text-[#e67e22] font-bold mb-1">
                  <Key className="w-4 h-4 text-[#e67e22]" />
                  <span>Free NYSE & NASDAQ API Integration</span>
                </div>
                <h3 className="text-lg font-extrabold text-slate-900">Market Provider API Keys</h3>
              </div>
              <button
                onClick={() => setIsKeyModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed">
              Configure free API keys for live NYSE and NASDAQ stock quotes, technicals, and fundamental statements. If left unconfigured or rate-limited, the system automatically uses the calibrated institutional engine.
            </p>

            <form onSubmit={handleSaveApiKeys} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-800 mb-1">
                  Alpha Vantage API Key (Free tier: stocks, indices, fundamentals)
                </label>
                <input
                  type="text"
                  value={alphaKeyInput}
                  onChange={(e) => setAlphaKeyInput(e.target.value)}
                  placeholder={providerStatus?.alpha_vantage_masked_key || 'Enter Alpha Vantage API Key'}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-[#8DB9F0] focus:outline-none font-mono"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-800 mb-1">
                  Twelve Data API Key (Free tier: 800 requests/day real-time & historical)
                </label>
                <input
                  type="text"
                  value={twelveKeyInput}
                  onChange={(e) => setTwelveKeyInput(e.target.value)}
                  placeholder={providerStatus?.twelve_data_masked_key || 'Enter Twelve Data API Key'}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-[#8DB9F0] focus:outline-none font-mono"
                />
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-[11px] text-slate-600 space-y-1">
                <p className="font-bold text-slate-700">Supported Markets:</p>
                <p>• <strong>NSE / BSE</strong>: Direct Indian Market Exchange Feed & Regulatory Engine</p>
                <p>• <strong>NYSE / NASDAQ</strong>: Alpha Vantage REST API & Twelve Data Free Tier</p>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsKeyModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-600 font-bold hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-[#8DB9F0] hover:bg-[#72a4e2] text-slate-900 font-extrabold shadow-md transition-all"
                >
                  Save & Test Providers
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* Browse All Companies Modal */}
      {isBrowseModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-3xl max-w-3xl w-full p-6 sm:p-8 shadow-2xl border border-slate-200 space-y-5 max-h-[85vh] flex flex-col">
            <div className="flex items-start justify-between pb-3 border-b border-slate-100">
              <div>
                <div className="flex items-center space-x-2 text-xs font-mono text-blue-600 font-bold mb-1">
                  <Compass className="w-4 h-4 text-blue-600" />
                  <span>Universal Equity Directory</span>
                </div>
                <h3 className="text-xl font-extrabold text-slate-900">
                  Browse All Supported Companies ({allCompaniesList.length || 18})
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Click any stock to immediately load its interactive OHLCV candlestick chart, audited financial statements, and company profile.
                </p>
              </div>
              <button
                onClick={() => setIsBrowseModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 text-lg font-bold p-1 rounded-lg"
              >
                ✕
              </button>
            </div>

            {/* Quick Search inside Modal */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Filter by ticker, name, or sector..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#8DB9F0]"
              />
            </div>

            {/* Companies Grid */}
            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {(allCompaniesList.length > 0 ? allCompaniesList : POPULAR_EQUITIES.ALL)
                  .filter((c) => {
                    if (!searchQuery) return true;
                    const q = searchQuery.toUpperCase();
                    return c.ticker.includes(q) || c.name.toUpperCase().includes(q) || (c.sector && c.sector.toUpperCase().includes(q));
                  })
                  .map((item) => {
                    const isSelected = selectedStock === item.ticker;
                    return (
                      <button
                        key={`modal-${item.market}-${item.ticker}`}
                        onClick={() => {
                          handleSelectSearchResult(item);
                          setIsBrowseModalOpen(false);
                        }}
                        className={`text-left p-3.5 rounded-2xl border transition-all flex flex-col justify-between cursor-pointer ${
                          isSelected
                            ? 'bg-blue-50/80 border-blue-400 ring-2 ring-blue-300 shadow-md'
                            : 'bg-white hover:bg-slate-50 border-slate-200 hover:border-slate-300 shadow-xs'
                        }`}
                      >
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-extrabold text-sm font-mono text-slate-900">{item.ticker}</span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">
                              {item.market}
                            </span>
                          </div>
                          <p className="text-xs text-slate-600 font-semibold truncate">{item.name}</p>
                          <p className="text-[11px] text-slate-400 truncate mt-0.5">{item.sector || 'Equities'}</p>
                        </div>
                        <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between">
                          <span className="text-xs font-mono font-bold text-slate-800">
                            {item.currency === 'INR' ? '₹' : '$'}{item.base_price?.toFixed(2)}
                          </span>
                          <span className="text-[11px] font-bold text-blue-600 flex items-center space-x-1">
                            <span>Inspect</span>
                            <ArrowUpRight className="w-3 h-3" />
                          </span>
                        </div>
                      </button>
                    );
                  })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
