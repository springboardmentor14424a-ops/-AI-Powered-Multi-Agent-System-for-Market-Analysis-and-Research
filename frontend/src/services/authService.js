
import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Automatically attach the logged-in user's JWT
API.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("access_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// Signup
export const signupUser = async (userData) => {
  const response = await API.post("/auth/signup", userData);
  return response.data;
};

// Login
export const loginUser = async (credentials) => {
  const response = await API.post("/auth/login", credentials);
  return response.data;
};

// Retrieve the logged-in user's research history
export const getResearchHistory = async () => {
  const response = await API.get("/research/history");
  return response.data;
};

// Retrieve a completed research report
export const getResearchReport = async (taskId) => {
  const response = await API.get(`/research/${taskId}/report`);
  return response.data;
};

// Create a new research task
export const createResearchTask = async (taskData) => {
  const response = await API.post("/research/", taskData);
  return response.data;
};

// Retrieve real historical stock data
export const getStockHistory = async (ticker, market, period) => {
  const response = await API.get("/stocks/history", {
    params: {
      ticker,
      market,
      period,
    },
  });

  return response.data;
};
// Search for stocks by company name or ticker
export const searchStocks = async (query) => {
  const response = await API.get("/stocks/search", {
    params: { query },
  });

  return response.data;
};


// Add a stock to the logged-in user's watchlist
export const addToWatchlist = async (stockData) => {
  const response = await API.post("/watchlist/", null, {
    params: stockData,
  });
  return response.data;
};

// Retrieve the logged-in user's watchlist
export const getWatchlist = async () => {
  const response = await API.get("/watchlist/");
  return response.data;
};

// Remove a stock from the watchlist
export const removeFromWatchlist = async (watchlistId) => {
  const response = await API.delete(`/watchlist/${watchlistId}`);
  return response.data;
};


export const getPreferences = async () => {
  return (await API.get("/preferences/")).data;
};

export const updatePreferences = async (preferences) => {
  return (await API.put("/preferences/", preferences)).data;
};

export default API;