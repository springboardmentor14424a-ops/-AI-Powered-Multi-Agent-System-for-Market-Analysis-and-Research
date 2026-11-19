import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api, { getErrorMessage } from '../api'

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    confirm_password: '',
  })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm_password) {
      setError('Passwords do not match')
      return
    }
    setSubmitting(true)
    try {
      await api.post('/auth/register', form)
      navigate('/login', { state: { registered: true } })
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
        <h1 className="text-2xl font-bold text-emerald-400">Create your account</h1>

        {error && (
          <p className="rounded-lg bg-red-500/10 border border-red-500/40 px-4 py-2 text-red-300 text-sm">
            {error}
          </p>
        )}

        <div>
          <label className="block mb-1 text-sm text-slate-400">Full name</label>
          <input name="full_name" value={form.full_name} onChange={handleChange} required className={inputClass} />
        </div>
        <div>
          <label className="block mb-1 text-sm text-slate-400">Email</label>
          <input type="email" name="email" value={form.email} onChange={handleChange} required className={inputClass} />
        </div>
        <div>
          <label className="block mb-1 text-sm text-slate-400">Password (min 8 characters)</label>
          <input type="password" name="password" value={form.password} onChange={handleChange} required className={inputClass} />
        </div>
        <div>
          <label className="block mb-1 text-sm text-slate-400">Confirm password</label>
          <input type="password" name="confirm_password" value={form.confirm_password} onChange={handleChange} required className={inputClass} />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-emerald-500 py-2 font-semibold text-slate-900 hover:bg-emerald-400 disabled:opacity-60"
        >
          {submitting ? 'Creating account...' : 'Sign Up'}
        </button>

        <p className="text-sm text-slate-400 text-center">
          Already have an account?{' '}
          <Link to="/login" className="text-emerald-400 hover:underline">Sign In</Link>
        </p>
      </form>
    </div>
  )
}