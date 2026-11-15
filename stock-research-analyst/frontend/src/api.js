// Thin fetch wrapper. Auth lives in an HTTP-only cookie set by the backend, so JS never
// touches the JWT. For state-changing requests we echo the (non-secret) CSRF cookie value
// in the X-CSRF-Token header, which the backend checks against the signed token.
const BASE = "/api";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

let onUnauthorized = null;
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn;
};

function getCookie(name) {
  const hit = document.cookie.split("; ").find((c) => c.startsWith(name + "="));
  return hit ? decodeURIComponent(hit.split("=")[1]) : null;
}

function errorMessage(data, status) {
  if (data && typeof data.detail === "string") return data.detail;
  if (data && Array.isArray(data.detail)) {
    return data.detail
      .map((d) => String(d.msg || "Invalid input").replace(/^Value error, /, ""))
      .join(". ");
  }
  return `Request failed (${status})`;
}

async function request(path, { method = "GET", body, silent401 = false } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET") {
    const csrf = getCookie("csrf_token");
    if (csrf) headers["X-CSRF-Token"] = csrf;
  }
  let res;
  try {
    res = await fetch(BASE + path, {
      method,
      headers,
      credentials: "include",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Cannot reach the server. Is the backend running?", 0);
  }
  let data = null;
  if (res.status !== 204) {
    try {
      data = await res.json();
    } catch {
      /* non-JSON body */
    }
  }
  if (!res.ok) {
    if (res.status === 401 && !silent401 && onUnauthorized) onUnauthorized();
    throw new ApiError(errorMessage(data, res.status), res.status);
  }
  return data;
}

export const api = {
  register: (b) => request("/auth/register", { method: "POST", body: b }),
  login: (b) => request("/auth/login", { method: "POST", body: b, silent401: true }),
  logout: () => request("/auth/logout", { method: "POST", silent401: true }),
  me: () => request("/auth/me", { silent401: true }),

  getPreferences: () => request("/preferences"),
  savePreferences: (b) => request("/preferences", { method: "PUT", body: b }),

  searchStocks: (q, market) =>
    request(`/stocks/search?q=${encodeURIComponent(q)}${market ? `&market=${market}` : ""}`),

  getWatchlist: () => request("/watchlist"),
  addToWatchlist: (b) => request("/watchlist", { method: "POST", body: b }),
  removeFromWatchlist: (id) => request(`/watchlist/${id}`, { method: "DELETE" }),

  startResearch: (b) => request("/research", { method: "POST", body: b }),
  getResearchHistory: () => request("/research"),
  getResearch: (id) => request(`/research/${id}`),
};

export const MARKETS = [
  { value: "NSE", label: "NSE – National Stock Exchange of India" },
  { value: "BSE", label: "BSE – BSE Ltd., India" },
  { value: "NASDAQ", label: "NASDAQ – US stock exchange" },
  { value: "NYSE", label: "NYSE – New York Stock Exchange" },
];

export const PERIODS = [
  { value: "1M", label: "1 Month" },
  { value: "3M", label: "3 Months" },
  { value: "6M", label: "6 Months" },
  { value: "1Y", label: "1 Year" },
  { value: "5Y", label: "5 Years" },
];

export const periodLabel = (v) => PERIODS.find((p) => p.value === v)?.label ?? v;
