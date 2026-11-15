import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import LandingPage from './components/LandingPage';
import Dashboard from './components/Dashboard';
import AuthModal from './components/AuthModal';

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();
  const [authModal, setAuthModal] = useState({ isOpen: false, tab: 'login' });

  const handleOpenAuth = (tab = 'login') => {
    setAuthModal({ isOpen: true, tab });
  };

  const handleCloseAuth = () => {
    setAuthModal({ isOpen: false, tab: 'login' });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#E9E8F8] via-[#f5f6fc] to-[#e8f0fb] flex flex-col items-center justify-center space-y-3 font-sans text-xs text-slate-600">
        <div className="w-9 h-9 border-3 border-[#8DB9F0] border-t-[#F5B69E] rounded-full animate-spin"></div>
        <p className="font-medium tracking-wide">Connecting to Multi-Agent Workspace...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#E9E8F8] via-[#f7f8fd] to-[#edf3fb] flex flex-col selection:bg-[#8DB9F0]/40 selection:text-[#1e3a8a] text-slate-800">
      <Navbar onOpenAuth={handleOpenAuth} />

      <main className="flex-1">
        {isAuthenticated ? (
          <Dashboard />
        ) : (
          <LandingPage onOpenAuth={handleOpenAuth} />
        )}
      </main>

      {/* Persistent Footer */}
      <footer className="border-t border-[#8DB9F0]/25 bg-white/80 backdrop-blur-md py-6 text-center text-xs text-slate-500 font-sans shadow-sm">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="font-medium text-slate-600">© 2026 Multi-Agent Stock Research Analyst Platform. Module 1: Auth & Workspace.</p>
          <div className="flex items-center space-x-3 text-[11px] text-slate-500 font-medium">
            <span className="px-2 py-0.5 rounded-full bg-[#8DB9F0]/15 text-[#2c5282]">FastAPI REST</span>
            <span>•</span>
            <span className="px-2 py-0.5 rounded-full bg-[#E9E8F8] text-[#4b4870]">PostgreSQL SQLAlchemy</span>
            <span>•</span>
            <span className="px-2 py-0.5 rounded-full bg-[#F5B69E]/20 text-[#9c4221]">JWT Bearer</span>
            <span>•</span>
            <span className="px-2 py-0.5 rounded-full bg-[#8DB9F0]/15 text-[#2c5282]">React + Tailwind</span>
          </div>
        </div>
      </footer>

      {/* Global Auth Modal */}
      <AuthModal
        isOpen={authModal.isOpen}
        onClose={handleCloseAuth}
        initialTab={authModal.tab}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

