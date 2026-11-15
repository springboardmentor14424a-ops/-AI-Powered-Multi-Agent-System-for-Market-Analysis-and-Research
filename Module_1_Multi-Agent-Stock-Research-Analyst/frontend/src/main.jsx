import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { GoogleOAuthProvider } from '@react-oauth/google';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || ''}>
      <BrowserRouter>
        <App />
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#111827',
              color: '#f9fafb',
              border: '1px solid #064e3b',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#030712',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#030712',
              },
            },
          }}
        />
      </BrowserRouter>
    </GoogleOAuthProvider>
  </React.StrictMode>
);
