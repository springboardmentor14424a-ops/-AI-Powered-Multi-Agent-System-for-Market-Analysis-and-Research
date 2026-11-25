import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Sign in failed.");
        return;
      }
      const jwt = data.access_token || data.token;
      if (!jwt) {
        setError("No token returned by server.");
        return;
      }
      localStorage.setItem("token", jwt);
      localStorage.setItem("access_token", jwt);
      navigate("/dashboard", { replace: true });
    } catch {
      setError("Network error while signing in.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#06071A] text-[#E0E1EE] flex items-center justify-center px-4">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#0D0F2B] p-8 shadow-2xl">
        <h1 className="text-2xl font-bold text-white">Sign In to R-AIstock</h1>
        <p className="mt-1 text-sm text-[#9496B8]">Access your multi-agent research workspace.</p>

        {error && (
          <div className="mt-4 rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-[#C5C7E0]">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg border border-white/15 bg-[#06071A] px-3.5 py-2.5 text-sm text-white focus:border-[#E6C27A] focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[#C5C7E0]">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border border-white/15 bg-[#06071A] px-3.5 py-2.5 text-sm text-white focus:border-[#E6C27A] focus:outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-gradient-to-r from-[#E6C27A] to-[#F5D793] py-2.5 text-sm font-bold text-[#06071A] hover:brightness-105 disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <button
          type="button"
          onClick={() => {
            window.location.href = `${API_BASE}/api/auth/oauth/google`;
          }}
          className="mt-4 w-full rounded-xl border border-white/15 bg-[#121432] py-2.5 text-sm font-medium text-white hover:border-[#E6C27A]/50"
        >
          Continue with Google
        </button>

        <p className="mt-6 text-center text-xs text-[#9496B8]">
          Don't have an account?{" "}
          <Link to="/register" className="text-[#E6C27A] hover:underline">
            Sign Up
          </Link>
        </p>
      </div>
    </div>
  );
}