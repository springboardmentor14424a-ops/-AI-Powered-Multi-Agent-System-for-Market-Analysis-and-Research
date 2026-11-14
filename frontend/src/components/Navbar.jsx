import React from 'react';
import { useAuth } from '../context/AuthContext';
import { TrendingUp, LogOut, User, ShieldCheck } from 'lucide-react';

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <nav className="bg-slate-900/90 backdrop-blur border-b border-slate-800 sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-600/20 border border-blue-500/40 rounded-lg text-blue-400">
          <TrendingUp size={20} />
        </div>
        <div>
          <span className="font-bold text-white text-lg tracking-tight">Multi-Agent Stock Analyst</span>
        </div>
      </div>

      {isAuthenticated && (
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/80 rounded-lg border border-slate-700 text-sm text-slate-200">
            <User size={15} className="text-blue-400" />
            <span className="font-medium">{user?.full_name}</span>
            <span className="text-xs text-slate-500">({user?.email})</span>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-red-950/40 hover:bg-red-900/50 text-red-300 border border-red-800/60 rounded-lg transition"
          >
            <LogOut size={14} /> Logout
          </button>
        </div>
      )}
    </nav>
  );
}
