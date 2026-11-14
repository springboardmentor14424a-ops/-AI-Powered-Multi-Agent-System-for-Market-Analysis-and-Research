import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ApiError } from "../api";
import { useAuth } from "../auth";
import AuthLayout from "../components/AuthLayout";
import Field from "../components/Field";
import SocialButtons from "../components/SocialButtons";

const SOCIAL_ERRORS = {
  signin_failed: "Sign-in with that provider didn't complete. Please try again.",
  provider_not_configured: "That sign-in method isn't set up on this server yet.",
  email_exists: "An account with that email already exists. Sign in with your email and password instead.",
};

export default function Login() {
  const { login, expired } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [params] = useSearchParams();
  const [error, setError] = useState(SOCIAL_ERRORS[params.get("error")] || "");
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
      <SocialButtons onNotice={setError} />
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
