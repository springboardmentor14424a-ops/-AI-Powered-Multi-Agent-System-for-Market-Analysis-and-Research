const API_BASE = '/api/v1';

export const getStoredToken = () => {
  return localStorage.getItem('stock_analyst_token');
};

export const setStoredToken = (token) => {
  if (token) {
    localStorage.setItem('stock_analyst_token', token);
  } else {
    localStorage.removeItem('stock_analyst_token');
  }
};

export const clearStoredToken = () => {
  localStorage.removeItem('stock_analyst_token');
};

async function request(endpoint, options = {}) {
  const token = getStoredToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, config);

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorMsg = data?.detail || data?.message || `Request failed with status ${response.status}`;
    const error = new Error(errorMsg);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

export const authApi = {
  login: (email, password) => 
    request('/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  register: (fullName, email, password) =>
    request('/register', {
      method: 'POST',
      body: JSON.stringify({ full_name: fullName, email, password }),
    }),
  getMe: () => request('/me'),
};

export const watchlistApi = {
  getAll: () => request('/watchlist'),
  add: (ticker) =>
    request('/watchlist', {
      method: 'POST',
      body: JSON.stringify({ ticker }),
    }),
  remove: (ticker) =>
    request(`/watchlist/${encodeURIComponent(ticker)}`, {
      method: 'DELETE',
    }),
};

export const historyApi = {
  getAll: () => request('/history'),
  createTask: (ticker, market, requestedPeriod) =>
    request('/tasks', {
      method: 'POST',
      body: JSON.stringify({
        ticker,
        market: market || 'NSE',
        requested_period: requestedPeriod || '6 Months',
      }),
    }),
  getTask: (taskId) => request(`/tasks/${taskId}`),
};

export const preferencesApi = {
  get: () => request('/preferences'),
  update: (preferredMarket, preferredAnalysisPeriod) =>
    request('/preferences', {
      method: 'PUT',
      body: JSON.stringify({
        preferred_market: preferredMarket,
        preferred_analysis_period: preferredAnalysisPeriod,
      }),
    }),
};

export const stocksApi = {
  search: (query) => request(`/stocks/search?query=${encodeURIComponent(query || '')}`),
  getQuote: (ticker, market) =>
    request(`/stocks/quote/${encodeURIComponent(ticker)}?market=${encodeURIComponent(market || 'NSE')}`),
  getIndices: () => request('/stocks/indices'),
  getChart: (ticker, period, market) =>
    request(`/stocks/chart/${encodeURIComponent(ticker)}?period=${encodeURIComponent(period || '6 Months')}&market=${encodeURIComponent(market || 'NSE')}`),
};

export const marketApi = {
  search: (query, market) => {
    let url = `/market/search?query=${encodeURIComponent(query || '')}`;
    if (market && market !== 'ALL') {
      url += `&market=${encodeURIComponent(market)}`;
    }
    return request(url);
  },
  getHistoricalOHLCV: (ticker, market, period = '6 Months', interval = '1d') =>
    request(`/market/historical/${encodeURIComponent(ticker)}?market=${encodeURIComponent(market || 'NSE')}&period=${encodeURIComponent(period)}&interval=${encodeURIComponent(interval)}`),
  getProfile: (ticker, market) =>
    request(`/market/profile/${encodeURIComponent(ticker)}?market=${encodeURIComponent(market || 'NSE')}`),
  getFinancials: (ticker, market, periodType = 'annual') =>
    request(`/market/financials/${encodeURIComponent(ticker)}?market=${encodeURIComponent(market || 'NSE')}&period_type=${encodeURIComponent(periodType)}`),
  validateData: (ticker, market, records) =>
    request('/market/validate', {
      method: 'POST',
      body: JSON.stringify({ ticker, market: market || 'NSE', records }),
    }),
  getQuote: (ticker, market) =>
    request(`/market/quote/${encodeURIComponent(ticker)}?market=${encodeURIComponent(market || 'NSE')}`),
  getStatus: () => request('/market/status'),
  updateKeys: (alphaVantageKey, twelveDataKey) =>
    request('/market/config', {
      method: 'POST',
      body: JSON.stringify({
        alpha_vantage_key: alphaVantageKey,
        twelve_data_key: twelveDataKey,
      }),
    }),
};


