
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Activity, User, Mail, Lock, ArrowRight } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

function Register() {
  const navigate = useNavigate()
  const { register } = useAuth()

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    if (password.length < 8) {
      setError('Password must contain at least 8 characters.')
      return
    }

    try {
      setLoading(true)

      await register(fullName.trim(), email.trim(), password)

      navigate('/login', {
        state: { message: 'Account created successfully. Please sign in.' },
      })
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Registration failed. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">

        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 mb-4">
            <Activity size={30} className="text-cyan-400" />
          </div>

          <h1 className="text-3xl font-bold text-white">
            Multi-Agent Stock Research
          </h1>

          <p className="text-slate-400 mt-2">
            Start your intelligent investment research
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl">

          <h2 className="text-2xl font-semibold text-white">
            Create account
          </h2>

          <p className="text-slate-400 text-sm mt-2 mb-7">
            Register to access your research workspace.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">

            <div>
              <label className="block text-sm text-slate-300 mb-2">
                Full name
              </label>

              <div className="flex items-center gap-3 bg-slate-950 border border-slate-700 rounded-lg px-4 focus-within:border-cyan-400">
                <User size={18} className="text-slate-500" />

                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Enter your full name"
                  className="w-full bg-transparent py-3 text-white outline-none placeholder:text-slate-600"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-slate-300 mb-2">
                Email address
              </label>

              <div className="flex items-center gap-3 bg-slate-950 border border-slate-700 rounded-lg px-4 focus-within:border-cyan-400">
                <Mail size={18} className="text-slate-500" />

                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full bg-transparent py-3 text-white outline-none placeholder:text-slate-600"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-slate-300 mb-2">
                Password
              </label>

              <div className="flex items-center gap-3 bg-slate-950 border border-slate-700 rounded-lg px-4 focus-within:border-cyan-400">
                <Lock size={18} className="text-slate-500" />

                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Create a password"
                  className="w-full bg-transparent py-3 text-white outline-none placeholder:text-slate-600"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-slate-300 mb-2">
                Confirm password
              </label>

              <div className="flex items-center gap-3 bg-slate-950 border border-slate-700 rounded-lg px-4 focus-within:border-cyan-400">
                <Lock size={18} className="text-slate-500" />

                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                  className="w-full bg-transparent py-3 text-white outline-none placeholder:text-slate-600"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-3 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold py-3 rounded-lg transition"
            >
              {loading ? 'Creating account...' : 'Create account'}
              {!loading && <ArrowRight size={18} />}
            </button>

          </form>

          <p className="text-center text-slate-400 text-sm mt-7">
            Already have an account?{' '}
            <Link
              to="/login"
              className="text-cyan-400 hover:text-cyan-300 font-medium"
            >
              Sign in
            </Link>
          </p>

        </div>

        <p className="text-center text-xs text-slate-600 mt-6">
          Secure access to your stock research workspace
        </p>

      </div>
    </div>
  )
}

export default Register
