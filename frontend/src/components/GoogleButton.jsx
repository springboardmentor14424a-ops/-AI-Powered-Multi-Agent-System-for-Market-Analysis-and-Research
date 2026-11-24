import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Key, ExternalLink } from 'lucide-react';

export default function GoogleButton() {
  const { continueWithGoogle } = useAuth();
  const navigate = useNavigate();
  const googleBtnRef = useRef(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Read Google Client ID from environment variables
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  useEffect(() => {
    if (!clientId) return;

    const initializeGoogleGSI = () => {
      if (window.google && googleBtnRef.current) {
        try {
          /* global google */
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: async (response) => {
              setLoading(true);
              setError('');
              try {
                // Send Google-signed ID token to backend for cryptographic verification
                await continueWithGoogle({ credential: response.credential });
                navigate('/');
              } catch (err) {
                setError(err.response?.data?.detail || 'Google cryptographic verification failed.');
              } finally {
                setLoading(false);
              }
            },
          });

          // Render official Google button directly from accounts.google.com
          window.google.accounts.id.renderButton(googleBtnRef.current, {
            type: 'standard',
            theme: 'outline',
            size: 'large',
            text: 'continue_with',
            shape: 'rectangular',
            width: 380,
            logo_alignment: 'left',
          });
        } catch (e) {
          console.error('Failed to initialize Google Identity Services:', e);
        }
      }
    };

    // If script is already loaded
    if (window.google) {
      initializeGoogleGSI();
    } else {
      // Check every 100ms until Google script loads
      const interval = setInterval(() => {
        if (window.google) {
          initializeGoogleGSI();
          clearInterval(interval);
        }
      }, 100);
      return () => clearInterval(interval);
    }
  }, [clientId]);

  return (
    <div className="w-full flex flex-col items-center">
      {error && (
        <div className="w-full mb-3 p-2.5 bg-red-950/70 border border-red-800 rounded-lg text-red-300 text-xs flex items-center gap-2">
          <AlertCircle size={15} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <p className="text-xs text-blue-400 mb-2 animate-pulse">
          Verifying with Google servers...
        </p>
      )}

      {clientId ? (
        // Official Google Identity Services container
        <div ref={googleBtnRef} className="w-full flex justify-center min-h-[44px]"></div>
      ) : (
        // Guidance card if Client ID is not yet entered in frontend/.env
        <div className="w-full bg-slate-800/80 border border-amber-800/60 rounded-xl p-4 text-xs text-slate-300 space-y-2.5">
          <div className="flex items-center gap-2 text-amber-400 font-semibold">
            <Key size={15} />
            <span>Real Google OAuth Setup (2 Minutes)</span>
          </div>
          <p className="text-slate-400 leading-relaxed text-[11px]">
            To allow Google to securely open its official login popup and verify your Gmail password, you need a free Google Client ID.
          </p>
          <ol className="list-decimal pl-4 space-y-1 text-slate-300 text-[11px]">
            <li>Open <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noreferrer" className="text-blue-400 underline font-medium">Google Cloud Console Credentials <ExternalLink size={11} className="inline" /></a></li>
            <li>Click <strong>Create Credentials ➔ OAuth client ID</strong> (Web application).</li>
            <li>Add Authorized JavaScript Origin: <code className="bg-slate-900 px-1 py-0.5 rounded text-blue-300">http://localhost:5173</code></li>
            <li>Copy your Client ID and paste it into <code className="bg-slate-900 px-1 py-0.5 rounded text-blue-300">frontend/.env</code></li>
          </ol>
        </div>
      )}
    </div>
  );
}
