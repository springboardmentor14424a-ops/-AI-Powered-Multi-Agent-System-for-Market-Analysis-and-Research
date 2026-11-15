import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  X, 
  Lock, 
  Mail, 
  User, 
  ShieldCheck, 
  ArrowRight, 
  AlertCircle, 
  CheckCircle2, 
  KeyRound
} from 'lucide-react';

export default function AuthModal({ isOpen, onClose, initialTab = 'login' }) {
  const [tab, setTab] = useState(initialTab); // 'login' | 'register'
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login, register } = useAuth();

  if (!isOpen) return null;

  const resetForm = () => {
    setError('');
    setSuccess('');
    setPassword('');
    setConfirmPassword('');
  };

  const handleTabSwitch = (newTab) => {
    setTab(newTab);
    resetForm();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (tab === 'register') {
      if (!fullName.trim() || fullName.trim().length < 2) {
        setError('Please provide your full name (minimum 2 characters).');
        return;
      }
      if (password.length < 6) {
        setError('Password must be at least 6 characters in length.');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match. Please re-enter identical passwords.');
        return;
      }
    }

    setIsSubmitting(true);

    try {
      if (tab === 'register') {
        await register(fullName.trim(), email.trim(), password);
        setSuccess('Account created and authenticated successfully! Redirecting...');
      } else {
        await login(email.trim(), password);
        setSuccess('Signed in successfully! Redirecting to your workspace...');
      }

      setTimeout(() => {
        onClose();
      }, 700);
    } catch (err) {
      setError(err.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-md animate-in fade-in duration-200">
      <div 
        className="relative w-full max-w-md bg-white/95 border border-[#E9E8F8] rounded-3xl p-6 sm:p-8 shadow-2xl shadow-[#8DB9F0]/20 text-slate-800"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-slate-800 p-1.5 rounded-full hover:bg-[#E9E8F8] transition-colors"
          aria-label="Close dialog"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header Branding */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-[#E9E8F8] border border-[#d7d4f2] text-[#524398] mb-3">
            <KeyRound className="w-6 h-6 stroke-[2.2]" />
          </div>
          <h2 className="text-xl sm:text-2xl font-extrabold tracking-tight text-slate-900">
            {tab === 'login' ? 'Sign In to Workspace' : 'Create Analyst Account'}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {tab === 'login' 
              ? 'Enter your credentials to access real-time multi-agent research.' 
              : 'Join the automated institutional-grade research platform.'}
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="grid grid-cols-2 p-1 bg-[#f4f3fb] border border-[#E9E8F8] rounded-2xl mb-6">
          <button
            type="button"
            onClick={() => handleTabSwitch('login')}
            className={`py-2 text-xs font-bold rounded-xl transition-all ${
              tab === 'login'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => handleTabSwitch('register')}
            className={`py-2 text-xs font-bold rounded-xl transition-all ${
              tab === 'register'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Sign Up
          </button>
        </div>

        {/* Error / Success Feedback */}
        {error && (
          <div className="mb-4 p-3 rounded-2xl bg-rose-50 border border-rose-200 flex items-start space-x-2.5 text-xs text-rose-700 font-medium">
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
            <div className="flex-1">{error}</div>
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-start space-x-2.5 text-xs text-emerald-700 font-medium">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
            <div className="flex-1">{success}</div>
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {tab === 'register' && (
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Full Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Arjun Sharma"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-white border border-[#E9E8F8] rounded-2xl text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-[#8DB9F0] focus:ring-2 focus:ring-[#8DB9F0]/30 transition-all font-medium shadow-sm"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                placeholder="analyst@domain.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-white border border-[#E9E8F8] rounded-2xl text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-[#8DB9F0] focus:ring-2 focus:ring-[#8DB9F0]/30 transition-all font-medium shadow-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-white border border-[#E9E8F8] rounded-2xl text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-[#8DB9F0] focus:ring-2 focus:ring-[#8DB9F0]/30 transition-all font-medium shadow-sm"
              />
            </div>
          </div>

          {tab === 'register' && (
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-white border border-[#E9E8F8] rounded-2xl text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-[#8DB9F0] focus:ring-2 focus:ring-[#8DB9F0]/30 transition-all font-medium shadow-sm"
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-2 py-3 px-4 bg-gradient-to-r from-[#F5B69E] to-[#ea9e80] hover:from-[#f0a68d] hover:to-[#df8b6b] disabled:opacity-50 text-slate-900 font-extrabold text-xs rounded-2xl shadow-lg shadow-[#F5B69E]/35 transition-all flex items-center justify-center space-x-2 glow-peach"
          >
            {isSubmitting ? (
              <span className="flex items-center space-x-2">
                <span className="w-3.5 h-3.5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin"></span>
                <span>Authenticating with FastAPI...</span>
              </span>
            ) : (
              <>
                <span>{tab === 'login' ? 'Sign In' : 'Create Free Account'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Security Footer Info */}
        <div className="mt-6 pt-5 border-t border-[#E9E8F8] text-center">
          <div className="flex items-center justify-center space-x-2 text-[11px] text-slate-500 font-mono">
            <ShieldCheck className="w-3.5 h-3.5 text-[#3575cb]" />
            <span>FastAPI JWT Token Auth & Bcrypt Hashed Credentials</span>
          </div>
        </div>
      </div>
    </div>
  );
}
