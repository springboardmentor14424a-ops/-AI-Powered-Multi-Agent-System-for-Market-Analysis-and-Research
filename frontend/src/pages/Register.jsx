import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function Register() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Registration failed.");
        return;
      }
      const jwt = data.access_token || data.token;
      if (jwt) {
        localStorage.setItem("token", jwt);
        localStorage.setItem("access_token", jwt);
        navigate("/dashboard", { replace: true });
      } else {
        navigate("/login", { replace: true });
      }
    } catch {
      setError("Network error while registering.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#06071A] text-[#E0E1EE] flex items-center justify-center px-4">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#0D0F2B] p-8 shadow-2xl">
        <h1 className="text-2xl font-bold text-white">Create Your Account</h1>
        <p className="mt-1 text-sm text-[#9496B8]">
          Start analyzing NSE, BSE, NASDAQ & NYSE stocks.
        </p>

        {error && (
          <div className="mt-4 rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-[#C5C7E0]">Full Name</label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="mt-1 w-full rounded-lg border border-white/15 bg-[#06071A] px-3.5 py-2.5 text-sm text-white focus:border-[#E6C27A] focus:outline-none"
            />
          </div>
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
            className="w-full rounded-xl bg-gradient-to-r from-[#682EC7] to-[#8347E5] py-2.5 text-sm font-bold text-white hover:brightness-110 disabled:opacity-60"
          >
            {loading ? "Creating account..." : "Sign Up"}
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
          Already have an account?{" "}
          <Link to="/login" className="text-[#E6C27A] hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}