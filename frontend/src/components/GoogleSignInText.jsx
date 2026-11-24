import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { X, UserPlus, ArrowLeft } from 'lucide-react';

const INITIAL_ACCOUNTS = [
  {
    name: 'Sahithi Redrouthu',
    email: 'sahithiredrouthu01@gmail.com',
  },
];

export default function GoogleSignInText() {
  const [showModal, setShowModal] = useState(false);
  const [mode, setMode] = useState('choose_account'); // 'choose_account' | 'enter_email'
  const [accounts, setAccounts] = useState(INITIAL_ACCOUNTS);
  
  const [inputEmail, setInputEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { continueWithGoogle } = useAuth();
  const navigate = useNavigate();

  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

  // Load saved accounts from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem('google_saved_accounts');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          const emailMap = new Map();
          INITIAL_ACCOUNTS.forEach((acc) => emailMap.set(acc.email.toLowerCase(), acc));
          parsed.forEach((acc) => {
            if (acc.email) {
              emailMap.set(acc.email.toLowerCase(), acc);
            }
          });
          setAccounts(Array.from(emailMap.values()));
        }
      }
    } catch {
      // Ignore storage read issues
    }
  }, []);

  const saveAccountToList = (newAcc) => {
    const updated = [
      ...accounts.filter((a) => a.email.toLowerCase() !== newAcc.email.toLowerCase()),
      newAcc,
    ];
    setAccounts(updated);
    try {
      localStorage.setItem('google_saved_accounts', JSON.stringify(updated));
    } catch {
      // Ignore storage write issues
    }
  };

  // 1. Primary Action: Launch official Google OAuth popup (accounts.google.com)
  const handleMainClick = () => {
    setError('');

    // If client ID is present and Google SDK is loaded, open genuine Google popup
    if (clientId && clientId.trim() && window.google?.accounts?.oauth2) {
      try {
        setLoading(true);
        const tokenClient = window.google.accounts.oauth2.initTokenClient({
          client_id: clientId.trim(),
          scope: 'openid email profile',
          prompt: 'select_account',
          callback: async (response) => {
            if (response.error) {
              setError(`Google sign-in error: ${response.error_description || response.error}`);
              setLoading(false);
              return;
            }

            if (response.access_token) {
              try {
                // Send genuine Google OAuth access token to FastAPI backend
                await continueWithGoogle({
                  credential: response.access_token,
                });
                navigate('/');
              } catch (err) {
                setError(err.response?.data?.detail || 'Backend failed to verify Google credentials.');
              } finally {
                setLoading(false);
              }
            }
          },
        });

        // Opens official Google popup window (accounts.google.com)
        tokenClient.requestAccessToken({ prompt: 'select_account' });
        return;
      } catch (err) {
        console.warn('OAuth popup launch failed, falling back to account chooser:', err);
      }
    }

    // Fallback to local account chooser
    setMode('choose_account');
    setShowModal(true);
  };

  // 2. Select account from local chooser
  const handleSelectAccount = async (account) => {
    setLoading(true);
    setError('');
    try {
      await continueWithGoogle({
        email: account.email,
        full_name: account.name,
      });
      setShowModal(false);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // 3. Add account manually
  const handleAddAccountSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const email = inputEmail.trim().toLowerCase();
    if (!email || !email.includes('@')) {
      setError('Enter a valid Google email address');
      return;
    }

    setLoading(true);
    const inferredName = email.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

    try {
      await continueWithGoogle({
        email: email,
        full_name: inferredName,
      });

      saveAccountToList({
        name: inferredName,
        email: email,
      });

      setShowModal(false);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to authenticate account. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full my-3">
      {/* Button labeled "Sign in with Google" */}
      <button
        type="button"
        disabled={loading}
        onClick={handleMainClick}
        className="w-full flex items-center justify-center gap-3 py-2.5 px-4 bg-white hover:bg-slate-100 text-slate-800 font-medium text-sm rounded-xl border border-slate-300 shadow-sm transition active:scale-[0.99] disabled:opacity-60"
      >
        {/* Google G Logo */}
        <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
          <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
          />
          <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
          />
        </svg>
        <span className="font-semibold text-slate-800">
          {loading ? 'Opening Google...' : 'Sign in with Google'}
        </span>
      </button>

      {error && !showModal && (
        <div className="mt-2 text-center text-xs text-red-400">
          {error}
        </div>
      )}

      {/* Fallback Google Authentication Dialog */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#1e1f20] text-[#e8eaed] border border-[#3c4043] rounded-2xl max-w-sm w-full p-6 shadow-2xl relative text-left font-sans">
            {/* Close Button */}
            <button
              type="button"
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 p-1.5 text-[#9aa0a6] hover:text-white rounded-full hover:bg-[#282a2d] transition"
            >
              <X size={18} />
            </button>

            {/* Google Logo Header */}
            <div className="flex items-center gap-2 mb-1">
              <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <h2 className="text-base font-semibold text-white">
                {mode === 'choose_account' ? 'Choose an account' : 'Sign in'}
              </h2>
            </div>

            <p className="text-xs text-[#9aa0a6] mb-4">
              to continue to <span className="text-[#8ab4f8] font-medium">Stock Research Analyst</span>
            </p>

            {error && (
              <div className="mb-3 p-2.5 bg-red-950/70 border border-red-800 rounded-lg text-red-300 text-xs">
                {error}
              </div>
            )}

            {/* Account Chooser View */}
            {mode === 'choose_account' && (
              <div>
                <div className="divide-y divide-[#3c4043] border-y border-[#3c4043] my-2">
                  {accounts.map((acc) => (
                    <button
                      key={acc.email}
                      type="button"
                      disabled={loading}
                      onClick={() => handleSelectAccount(acc)}
                      className="w-full text-left py-2.5 px-2 flex items-center gap-3 hover:bg-[#282a2d] rounded-lg transition group disabled:opacity-50"
                    >
                      <div className="w-9 h-9 rounded-full bg-[#5c4033] flex items-center justify-center font-normal text-white text-sm shrink-0">
                        {acc.name ? acc.name.charAt(0).toUpperCase() : acc.email.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-white group-hover:text-white truncate">
                          {acc.name}
                        </div>
                        <div className="text-xs text-[#9aa0a6] truncate">
                          {acc.email}
                        </div>
                      </div>
                    </button>
                  ))}

                  <button
                    type="button"
                    disabled={loading}
                    onClick={() => {
                      setMode('enter_email');
                      setError('');
                    }}
                    className="w-full text-left py-2.5 px-2 flex items-center gap-3 hover:bg-[#282a2d] rounded-lg transition text-white group disabled:opacity-50"
                  >
                    <div className="w-9 h-9 flex items-center justify-center shrink-0 text-[#9aa0a6] group-hover:text-white">
                      <UserPlus size={20} />
                    </div>
                    <span className="text-sm font-medium text-white">
                      Add Google Account
                    </span>
                  </button>
                </div>

                <div className="mt-4 flex items-center justify-between text-xs text-[#9aa0a6]">
                  <a href="#" onClick={(e) => e.preventDefault()} className="hover:text-white">
                    Privacy Policy
                  </a>
                  <a href="#" onClick={(e) => e.preventDefault()} className="hover:text-white">
                    Terms of Service
                  </a>
                </div>
              </div>
            )}

            {/* Add Google Account - Enter Email */}
            {mode === 'enter_email' && (
              <form onSubmit={handleAddAccountSubmit} className="space-y-4 pt-1">
                <div>
                  <label className="block text-xs text-[#9aa0a6] mb-1">
                    Google Email address
                  </label>
                  <input
                    type="email"
                    required
                    autoFocus
                    placeholder="Enter your Gmail address"
                    value={inputEmail}
                    onChange={(e) => setInputEmail(e.target.value)}
                    className="w-full bg-transparent border border-[#3c4043] focus:border-[#8ab4f8] focus:ring-1 focus:ring-[#8ab4f8] rounded-md px-3.5 py-2.5 text-sm text-white placeholder-[#5f6368] outline-none transition"
                  />
                </div>

                <div className="pt-2 flex items-center justify-between">
                  <button
                    type="button"
                    onClick={() => {
                      setMode('choose_account');
                      setError('');
                    }}
                    className="inline-flex items-center gap-1 text-xs text-[#8ab4f8] hover:underline"
                  >
                    <ArrowLeft size={14} /> Back
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="bg-[#8ab4f8] hover:bg-[#a8c7fa] text-[#041e49] text-xs font-semibold px-5 py-2 rounded-full transition disabled:opacity-50"
                  >
                    {loading ? 'Adding...' : 'Continue'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
