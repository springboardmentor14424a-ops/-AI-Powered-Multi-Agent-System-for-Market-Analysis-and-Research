import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getErrorMessage } from '../api'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const inputClass =
    'w-full rounded-lg bg-slate-900 border border-slate-600 px-4 py-2 text-slate-100 focus:outline-none focus:border-emerald-400'

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex items-center justify-center px-4">
      <form onSubmit={handleSubmit} className="w-full max-w-md rounded-xl bg-slate-800 p-8 space-y-4">
        <h1 className="text-2xl font-bold text-emerald-400">Sign in</h1>

        {location.state?.registered && (
          <p className="rounded-lg bg-emerald-500/10 border border-emerald-500/40 px-4 py-2 text-emerald-300 text-sm">
            Account created! Please sign in.
          </p>
        )}
        {error && (
          <p className="rounded-lg bg-red-500/10 border border-red-500/40 px-4 py-2 text-red-300 text-sm">
            {error}
          </p>
        )}

        <div>
          <label className="block mb-1 text-sm text-slate-400">Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className={inputClass} />
        </div>
        <div>
          <label className="block mb-1 text-sm text-slate-400">Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className={inputClass} />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-emerald-500 py-2 font-semibold text-slate-900 hover:bg-emerald-400 disabled:opacity-60"
        >
          {submitting ? 'Signing in...' : 'Sign In'}
        </button>

        <p className="text-sm text-slate-400 text-center">
          New here?{' '}
          <Link to="/register" className="text-emerald-400 hover:underline">Create an account</Link>
        </p>
      </form>
    </div>
  )
}