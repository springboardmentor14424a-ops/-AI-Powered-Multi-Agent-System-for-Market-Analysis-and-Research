// Tiny fetch wrapper for the FastAPI backend.
//  - credentials: "include" -> the browser sends the HTTP-only auth cookie.
//  - The JWT itself is never readable from JavaScript (that's the point of HTTP-only).
//  - The CSRF token (returned by login and /auth/me) is kept in memory and sent
//    as X-CSRF-Token on state-changing requests.

const BASE = import.meta.env.VITE_API_URL ?? "";

let csrfToken = null;
let onUnauthorized = null;

export const setCsrfToken = (token) => {
  csrfToken = token ?? null;
};
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn;
};

export class ApiError extends Error {
  constructor(message, status, fieldErrors = {}) {
    super(message);
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

export async function api(path, { method = "GET", body } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET" && csrfToken) headers["X-CSRF-Token"] = csrfToken;

  let res;
  try {
    res = await fetch(`${BASE}/api${path}`, {
      method,
      headers,
      credentials: "include",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check your connection and try again.", 0);
  }

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const message =
      typeof data?.detail === "string" ? data.detail : "Something went wrong. Please try again.";
    // A 401 on a protected endpoint means the session is gone/expired.
    if (res.status === 401 && !path.startsWith("/auth/") && onUnauthorized) onUnauthorized();
    throw new ApiError(message, res.status, data?.errors ?? {});
  }
  return data;
}
