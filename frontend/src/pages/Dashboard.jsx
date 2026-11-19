import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Dashboard() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-10">
      <h1 className="text-3xl font-bold">Welcome, {user.full_name}</h1>
      <button
        onClick={handleLogout}
        className="mt-6 px-4 py-2 rounded-lg border border-slate-600 hover:bg-slate-800"
      >
        Log out
      </button>
    </div>
  )
}