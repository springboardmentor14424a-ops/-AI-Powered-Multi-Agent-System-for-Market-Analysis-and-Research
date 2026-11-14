
import React from 'react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import Workspace from './components/Workspace';

function App() {
  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
      <div className="w-full h-full min-h-screen bg-slate-950">
        <Workspace />
      </div>
    </GoogleOAuthProvider>
  );
}

export default App;
