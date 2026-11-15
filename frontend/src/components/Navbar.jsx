import React from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  TrendingUp, 
  LogOut, 
  Sparkles,
  Database
} from 'lucide-react';

export default function Navbar({ onOpenAuth, preferredMarket }) {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="sticky top-0 z-40 border-b border-[#E9E8F8] bg-white/75 backdrop-blur-md shadow-sm shadow-[#8DB9F0]/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <div className="flex items-center space-x-3 cursor-pointer">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#8DB9F0] via-[#c5dcf7] to-[#F5B69E] flex items-center justify-center shadow-md shadow-[#8DB9F0]/30">
              <TrendingUp className="w-5 h-5 text-slate-800 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight text-slate-800">
                  StockPulse
                </span>
                <span className="text-[11px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-full bg-[#E9E8F8] text-[#524398] border border-[#d7d4f2]">
                  Multi-Agent AI
                </span>
              </div>
              <p className="text-[10px] text-slate-500 font-mono tracking-wide hidden sm:block">
                Autonomous Financial Research System
              </p>
            </div>
          </div>

          {/* Center Status Pill */}
          <div className="hidden md:flex items-center space-x-3 text-xs font-mono text-slate-600 bg-white/90 border border-[#E9E8F8] rounded-full px-4 py-1.5 shadow-sm">
            <span className="flex items-center space-x-1.5 text-slate-700">
              <span className="w-2 h-2 rounded-full bg-[#8DB9F0] animate-pulse"></span>
              <span className="font-semibold text-slate-700">FastAPI Active</span>
            </span>
            <span className="text-slate-300">|</span>
            <span className="flex items-center space-x-1 text-slate-600">
              <Database className="w-3.5 h-3.5 text-[#8DB9F0]" />
              <span>PostgreSQL Engine</span>
            </span>
          </div>

          {/* Right Action buttons */}
          <div className="flex items-center space-x-3">
            {isAuthenticated ? (
              <div className="flex items-center space-x-3">
                {/* Market Indicator */}
                {preferredMarket && (
                  <div className="hidden sm:flex items-center space-x-1.5 bg-[#E9E8F8]/60 border border-[#d7d4f2] rounded-xl px-3 py-1.5 text-xs font-mono">
                    <span className="text-slate-500">Market:</span>
                    <span className="font-bold text-[#3575cb]">{preferredMarket}</span>
                  </div>
                )}

                {/* User Info */}
                <div className="flex items-center space-x-2.5 bg-white/90 border border-[#E9E8F8] rounded-2xl px-3.5 py-1.5 shadow-sm">
                  <div className="w-7 h-7 rounded-xl bg-[#E9E8F8] text-[#524398] flex items-center justify-center font-bold text-xs uppercase border border-[#d7d4f2]">
                    {user?.full_name ? user.full_name.charAt(0) : 'U'}
                  </div>
                  <div className="hidden sm:block text-left">
                    <p className="text-xs font-bold text-slate-800 leading-none">
                      {user?.full_name || 'Stock Analyst'}
                    </p>
                    <p className="text-[10px] text-slate-500 font-mono leading-none mt-1">
                      {user?.email}
                    </p>
                  </div>
                </div>

                {/* Logout Button */}
                <button
                  onClick={logout}
                  className="flex items-center space-x-1.5 text-xs text-rose-600 hover:text-rose-700 bg-rose-50 hover:bg-rose-100/80 border border-rose-200 rounded-xl px-3 py-2 transition-all font-semibold"
                  title="Sign out of your account"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2.5">
                <button
                  onClick={() => onOpenAuth('login')}
                  className="text-xs font-bold text-slate-700 hover:text-slate-900 bg-white/80 hover:bg-white border border-[#E9E8F8] rounded-xl px-4 py-2 shadow-sm transition-all"
                >
                  Sign In
                </button>
                <button
                  onClick={() => onOpenAuth('register')}
                  className="text-xs font-bold text-slate-900 bg-gradient-to-r from-[#F5B69E] to-[#ea9e80] hover:from-[#f0a68d] hover:to-[#df8b6b] rounded-xl px-4 py-2 shadow-md shadow-[#F5B69E]/30 transition-all flex items-center space-x-1.5 glow-peach"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Get Started</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
