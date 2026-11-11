import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, saveToken } from "../api.js";

export default function SignIn() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const change = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const res = await api("/auth/login", { method: "POST", body: form });
      saveToken(res.access_token);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <form className="auth-card" onSubmit={submit}>
        <h2>Welcome back</h2>
        {error && <div className="alert alert-error">{error}</div>}

        <label>Email Address
          <input name="email" type="email" value={form.email} onChange={change} required />
        </label>
        <label>Password
          <input name="password" type="password" value={form.password} onChange={change} required />
        </label>

        <button className="btn btn-big" disabled={busy}>
          {busy ? "Signing in..." : "Sign In"}
        </button>
        <p className="muted">New here? <Link to="/signup">Create an account</Link></p>
        <p className="muted"><Link to="/">Back to home</Link></p>
      </form>
    </div>
  );
}
