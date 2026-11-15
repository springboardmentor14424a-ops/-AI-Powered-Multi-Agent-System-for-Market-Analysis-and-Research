import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api.js";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", confirm_password: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm_password) return setError("Passwords do not match.");
    setBusy(true);
    try {
      await api.register(form);
      setSuccess("Registration successful! Redirecting to sign in…");
      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <form onSubmit={onSubmit} className="card w-full max-w-md space-y-4">
        <div>
          <h1 className="text-2xl font-semibold">Create your account</h1>
          <p className="text-sm text-slate-500">Multi-Agent Stock Research Analyst</p>
        </div>

        {error && <p role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        {success && <p role="status" className="rounded-md bg-green-50 p-3 text-sm text-green-700">{success}</p>}

        <div>
          <label className="label" htmlFor="full_name">Full Name</label>
          <input id="full_name" className="input" value={form.full_name} onChange={set("full_name")} required minLength={2} autoComplete="name" />
        </div>
        <div>
          <label className="label" htmlFor="email">Email Address</label>
          <input id="email" type="email" className="input" value={form.email} onChange={set("email")} required autoComplete="email" />
        </div>
        <div>
          <label className="label" htmlFor="password">Password</label>
          <input id="password" type="password" className="input" value={form.password} onChange={set("password")} required minLength={8} autoComplete="new-password" />
          <p className="mt-1 text-xs text-slate-500">At least 8 characters, with a letter and a number.</p>
        </div>
        <div>
          <label className="label" htmlFor="confirm_password">Confirm Password</label>
          <input id="confirm_password" type="password" className="input" value={form.confirm_password} onChange={set("confirm_password")} required autoComplete="new-password" />
        </div>

        <button className="btn w-full" disabled={busy || !!success}>{busy ? "Creating account…" : "Register"}</button>
        <p className="text-center text-sm text-slate-600">
          Already have an account? <Link to="/login" className="text-indigo-600 hover:underline">Sign in</Link>
        </p>
      </form>
    </div>
  );
}
