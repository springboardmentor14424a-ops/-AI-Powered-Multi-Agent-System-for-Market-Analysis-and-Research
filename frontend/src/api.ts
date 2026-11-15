
const API_URL = "http://localhost:8000";

function getCookie(name: string): string | null {
  const cookie = document.cookie
    .split("; ")
    .find(row => row.startsWith(name + "="));

  return cookie
    ? decodeURIComponent(cookie.split("=")[1])
    : null;
}

export async function api(
  endpoint: string,
  options: RequestInit = {}
) {
  const method = (options.method || "GET").toUpperCase();

  const headers = new Headers(options.headers);

  if (options.body) {
    headers.set("Content-Type", "application/json");
  }

  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const csrf = getCookie("csrf_token");

    if (csrf) {
      headers.set("X-CSRF-Token", csrf);
    }
  }

  let response: Response;

  try {
    response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      method,
      headers,
      credentials: "include"
    });
  } catch (error) {
    console.error("StockPilot API connection error:", error);

    throw new Error(
      "Cannot connect to StockPilot backend. Check whether FastAPI is running on port 8000."
    );
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      data.detail || `API error: ${response.status}`
    );
  }

  return data;
}
