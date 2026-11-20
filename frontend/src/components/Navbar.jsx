import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const APP_NAME = 'Multi-Agent Stock Analyst'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <nav className="border-b border-slate-800">
      <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
        <Link to="/dashboard" className="text-lg font-bold text-emerald-400">
          {APP_NAME}
        </Link>
        <div className="flex items-center gap-4">
          <span className="text-slate-400 hidden sm:inline">{user?.full_name}</span>
          <button
            onClick={handleLogout}
            className="px-4 py-2 rounded-lg border border-slate-600 hover:bg-slate-800"
          >
            Log out
          </button>
        </div>
      </div>
    </nav>
  )
}