// Small helper that talks to the FastAPI backend.
const TOKEN_KEY = "access_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const saveToken = (t) => localStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

function messageFrom(data) {
  if (!data) return "Something went wrong. Please try again.";
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail) && data.detail[0]) {
    const first = data.detail[0];
    const field = first.loc ? first.loc[first.loc.length - 1] : "";
    return `${field ? field + ": " : ""}${String(first.msg).replace("Value error, ", "")}`;
  }
  return "Something went wrong. Please try again.";
}

export async function api(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`/api${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Cannot reach the server. Is the backend running?");
  }

  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error(messageFrom(data));
    err.status = res.status;
    throw err;
  }
  return data;
}
