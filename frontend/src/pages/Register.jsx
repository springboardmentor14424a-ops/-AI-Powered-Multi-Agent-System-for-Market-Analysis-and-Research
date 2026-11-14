import { useState } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../api";
import { useAuth } from "../auth";
import AuthLayout from "../components/AuthLayout";
import Field from "../components/Field";

const RULES = [
  ["At least 8 characters", (p) => p.length >= 8],
  ["A lowercase letter", (p) => /[a-z]/.test(p)],
  ["An uppercase letter", (p) => /[A-Z]/.test(p)],
  ["A number", (p) => /\d/.test(p)],
];
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Mirrors the backend rules for instant feedback; the backend is still the authority.
function validate(f) {
  const e = {};
  if (f.full_name.trim().length < 2) e.full_name = "Enter your full name.";
  if (!EMAIL_RE.test(f.email.trim())) e.email = "Enter a valid email address.";
  if (!RULES.every(([, ok]) => ok(f.password))) {
    e.password = "Password doesn't meet the requirements below.";
  } else if (new TextEncoder().encode(f.password).length > 72) {
    e.password = "Password must be at most 72 bytes long.";
  }
  if (f.confirm_password !== f.password) e.confirm_password = "Passwords do not match.";
  return e;
}

export default function Register() {
  const { register } = useAuth();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", confirm_password: "" });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [registeredName, setRegisteredName] = useState(null);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
    if (errors[name]) setErrors((er) => ({ ...er, [name]: undefined }));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setFormError("");
    const clientErrors = validate(form);
    if (Object.keys(clientErrors).length) {
      setErrors(clientErrors);
      return;
    }
    setSubmitting(true);
    try {
      const res = await register({ ...form, full_name: form.full_name.trim(), email: form.email.trim() });
      setRegisteredName(res.user.full_name);
    } catch (err) {
      if (!(err instanceof ApiError)) throw err;
      if (err.status === 409) setErrors({ email: err.message });
      else if (err.status === 422) setErrors(err.fieldErrors);
      else setFormError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (registeredName) {
    return (
      <AuthLayout title="You're all set!">
        <div className="alert alert-success" role="status">
          Registration successful, {registeredName.split(" ")[0]}! Your account has been created.
        </div>
        <Link className="btn btn-primary btn-block" to="/login">
          Continue to sign in
        </Link>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Start researching stocks with a team of AI agents."
      footer={
        <>
          Already have an account? <Link to="/login">Sign in</Link>
        </>
      }
    >
      <form onSubmit={onSubmit} noValidate>
        {formError && (
          <div className="alert alert-error" role="alert">
            {formError}
          </div>
        )}
        <Field id="full_name" label="Full name" autoComplete="name" value={form.full_name} onChange={onChange} error={errors.full_name} />
        <Field id="email" label="Email address" type="email" autoComplete="email" value={form.email} onChange={onChange} error={errors.email} />
        <Field id="password" label="Password" type="password" autoComplete="new-password" value={form.password} onChange={onChange} error={errors.password} />
        <ul className="rules" aria-label="Password requirements">
          {RULES.map(([label, ok]) => (
            <li key={label} className={ok(form.password) ? "ok" : ""}>
              {label}
            </li>
          ))}
        </ul>
        <Field id="confirm_password" label="Confirm password" type="password" autoComplete="new-password" value={form.confirm_password} onChange={onChange} error={errors.confirm_password} />
        <button className="btn btn-primary btn-block" type="submit" disabled={submitting}>
          {submitting ? "Creating account…" : "Sign up"}
        </button>
      </form>
    </AuthLayout>
  );
}
