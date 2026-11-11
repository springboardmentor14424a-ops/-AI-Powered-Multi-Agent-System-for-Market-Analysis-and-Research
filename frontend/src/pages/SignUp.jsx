import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api.js";

export default function SignUp() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", confirm_password: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);

  const change = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm_password) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      const res = await api("/auth/register", { method: "POST", body: form });
      setSuccess(res.message);
      setTimeout(() => navigate("/signin"), 1500);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <form className="auth-card" onSubmit={submit}>
        <h2>Create your account</h2>
        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-ok">{success}</div>}

        <label>Full Name
          <input name="full_name" value={form.full_name} onChange={change} required />
        </label>
        <label>Email Address
          <input name="email" type="email" value={form.email} onChange={change} required />
        </label>
        <label>Password
          <input name="password" type="password" value={form.password} onChange={change}
                 minLength={8} maxLength={72} required />
          <small>At least 8 characters.</small>
        </label>
        <label>Confirm Password
          <input name="confirm_password" type="password" value={form.confirm_password}
                 onChange={change} required />
        </label>

        <button className="btn btn-big" disabled={busy || !!success}>
          {busy ? "Creating account..." : "Sign Up"}
        </button>
        <p className="muted">Already registered? <Link to="/signin">Sign in</Link></p>
        <p className="muted"><Link to="/">Back to home</Link></p>
      </form>
    </div>
  );
}
