import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Mail, Lock, Eye, EyeOff, TrendingUp, LogIn } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../context/AuthContext';

const schema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
});

export default function LoginPage() {
  const { login, googleLogin } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(schema) });

  const onSubmit = async (data) => {
    try {
      await login(data.email, data.password);
      toast.success('Welcome back!');
      navigate('/dashboard');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login failed. Check your credentials.';
      toast.error(msg);
    }
  };

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  const handleGoogleLogin = async (credential) => {
    try {
      await googleLogin(credential);
      toast.success('Signed in with Google!');
      navigate('/dashboard');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Google sign-in failed.';
      toast.error(msg);
    }
  };

  const handleDirectGoogleLogin = async () => {
    try {
      await googleLogin('demo_google_analyst_session');
      toast.success('Signed in with Google!');
      navigate('/dashboard');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Google sign-in failed.';
      toast.error(msg);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-emerald-950 to-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="p-2 bg-emerald-600 rounded-xl">
            <TrendingUp className="w-7 h-7 text-white" />
          </div>
          <span className="text-2xl font-bold text-white">Stock Research</span>
        </div>

        {/* Card */}
        <div className="bg-gray-900/80 border border-emerald-900/50 rounded-2xl p-8 backdrop-blur-sm shadow-2xl">
          <div className="flex items-center gap-3 mb-6">
            <LogIn className="w-6 h-6 text-emerald-400" />
            <h1 className="text-2xl font-bold text-white">Sign In</h1>
          </div>
          <p className="text-gray-400 mb-6 text-sm">Access your personalized stock research dashboard.</p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  {...register('email')}
                  type="email"
                  placeholder="you@example.com"
                  className="w-full bg-gray-800/60 border border-gray-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-gray-500 outline-none transition-all"
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-xs text-red-400">{errors.email.message}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Your password"
                  className="w-full bg-gray-800/60 border border-gray-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-lg pl-10 pr-10 py-2.5 text-white placeholder-gray-500 outline-none transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-emerald-400 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-xs text-red-400">{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-lg transition-colors mt-2 flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  Sign In
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-6">
            <div className="flex-1 h-px bg-gray-700" />
            <span className="text-xs text-gray-500">or continue with</span>
            <div className="flex-1 h-px bg-gray-700" />
          </div>

          {/* Google Sign-In */}
          <div className="flex justify-center">
            {googleClientId ? (
              <GoogleLogin
                onSuccess={(response) => handleGoogleLogin(response.credential)}
                onError={() => {
                  toast.error('Google sign-in failed. Please try email/password login.', { duration: 4000 });
                }}
                theme="filled_black"
                shape="rectangular"
                text="continue_with"
                width="100%"
              />
            ) : (
              <button
                type="button"
                onClick={handleDirectGoogleLogin}
                className="w-full bg-white hover:bg-gray-100 text-gray-800 font-medium py-2.5 px-4 rounded-lg transition-all flex items-center justify-center gap-3 text-sm shadow-md"
              >
                <svg className="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                </svg>
                <span>Sign in with Google</span>
              </button>
            )}
          </div>

          <p className="mt-6 text-center text-sm text-gray-400">
            Don't have an account?{' '}
            <Link to="/register" className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
