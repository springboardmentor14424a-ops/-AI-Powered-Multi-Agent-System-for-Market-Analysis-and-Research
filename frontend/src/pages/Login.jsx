import { useState } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../api";
import { useAuth } from "../auth";
import AuthLayout from "../components/AuthLayout";
import Field from "../components/Field";

export default function Login() {
  const { login, expired } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
    setError("");
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!form.email.trim() || !form.password) {
      setError("Enter your email address and password.");
      return;
    }
    setSubmitting(true);
    try {
      // On success the auth context updates and <GuestRoute> redirects to the dashboard.
      await login(form.email.trim(), form.password);
    } catch (err) {
      if (!(err instanceof ApiError)) throw err;
      setError(err.status === 422 ? "Enter a valid email address." : err.message);
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to your research workspace."
      footer={
        <>
          New here? <Link to="/register">Create an account</Link>
        </>
      }
    >
      <form onSubmit={onSubmit} noValidate>
        {expired && !error && (
          <div className="alert alert-info" role="status">
            Your session has expired. Please sign in again.
          </div>
        )}
        {error && (
          <div className="alert alert-error" role="alert">
            {error}
          </div>
        )}
        <Field id="email" label="Email address" type="email" autoComplete="email" value={form.email} onChange={onChange} />
        <Field id="password" label="Password" type="password" autoComplete="current-password" value={form.password} onChange={onChange} />
        <button className="btn btn-primary btn-block" type="submit" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </AuthLayout>
  );
}
