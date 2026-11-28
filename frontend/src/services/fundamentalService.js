/**
 * fundamentalService.js
 * =======================
 * Dedicated frontend service for Fundamental Agent API interactions.
 * Reuses the pre-configured Axios instance with JWT interceptor from authService.
 */

import API from "./authService";

/**
 * Execute real-time fundamental analysis for a company.
 * 
 * @param {string} ticker - Stock ticker symbol (e.g. TCS, AAPL)
 * @param {string} market - Exchange/market (NSE, BSE, NASDAQ, NYSE), default NSE
 * @returns {Promise<object>} Fundamental Agent analysis response envelope
 */
export const analyzeFundamentals = async (ticker, market = "NSE") => {
  const payload = {
    ticker: ticker.trim().toUpperCase(),
    market: market.trim().toUpperCase(),
  };

  const response = await API.post("/api/fundamental/analyze", payload);
  return response.data;
};

export default {
  analyzeFundamentals,
};
