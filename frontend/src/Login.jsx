import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

const MARKET_TICKERS = [
  { symbol: 'NIFTY 50', price: '24,812.40', change: '+1.18%', up: true },
  { symbol: 'SENSEX', price: '81,523.15', change: '+0.94%', up: true },
  { symbol: 'NASDAQ', price: '19,245.80', change: '+1.42%', up: true },
  { symbol: 'AAPL', price: '$232.60', change: '+0.85%', up: true },
  { symbol: 'RELIANCE.NS', price: '₹2,948.10', change: '-0.32%', up: false },
  { symbol: 'NVDA', price: '$146.30', change: '+2.64%', up: true },
  { symbol: 'TCS.NS', price: '₹4,112.50', change: '+0.51%', up: true },
];

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');

    try {
      const response = await fetch('http://127.0.0.1:8000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('token', data.access_token);
        setMessage('Login successful! Redirecting to terminal...');
        setTimeout(() => {
          navigate('/dashboard');
        }, 900);
      } else {
        setMessage(data.detail || 'Invalid credentials');
        setIsLoading(false);
      }
    } catch (error) {
      setMessage('Error connecting to the server.');
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0b1120',
      color: '#f8fafc',
      fontFamily: '"Inter", "Segoe UI", sans-serif',
      display: 'flex',
      flexDirection: 'column',
      backgroundImage: 'radial-gradient(circle at 15% 20%, rgba(16, 185, 129, 0.12), transparent 35%), radial-gradient(circle at 85% 80%, rgba(37, 99, 235, 0.15), transparent 40%)'
    }}>
      {/* Top Market Ticker Strip */}
      <div style={{
        backgroundColor: '#0f172a',
        borderBottom: '1px solid #1e293b',
        padding: '10px 24px',
        display: 'flex',
        gap: '28px',
        overflowX: 'auto',
        whiteSpace: 'nowrap',
        alignItems: 'center',
        fontSize: '12px'
      }}>
        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          color: '#10b981',
          fontWeight: '700',
          letterSpacing: '0.5px'
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: '#10b981',
            boxShadow: '0 0 8px #10b981'
          }} />
          MARKETS LIVE
        </span>

        {MARKET_TICKERS.map((item) => (
          <div key={item.symbol} style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: '#94a3b8', fontWeight: '600' }}>{item.symbol}</span>
            <span style={{ color: '#f1f5f9', fontWeight: '500' }}>{item.price}</span>
            <span style={{
              color: item.up ? '#10b981' : '#f43f5e',
              backgroundColor: item.up ? 'rgba(16, 185, 129, 0.12)' : 'rgba(244, 63, 94, 0.12)',
              padding: '2px 6px',
              borderRadius: '4px',
              fontWeight: '600',
              fontSize: '11px'
            }}>
              {item.change}
            </span>
          </div>
        ))}
      </div>

      {/* Main Split Container */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '60px',
        padding: '40px 24px',
        maxWidth: '1200px',
        width: '100%',
        margin: '0 auto',
        boxSizing: 'border-box'
      }}>

        {/* Left Side: Stock Market Visual & Brand Pitch */}
        <div style={{ flex: '1.2', minWidth: '320px', maxWidth: '540px' }}>
          <div style={{
            display: 'inline-block',
            padding: '5px 12px',
            borderRadius: '9999px',
            backgroundColor: 'rgba(37, 99, 235, 0.15)',
            border: '1px solid rgba(59, 130, 246, 0.35)',
            color: '#60a5fa',
            fontSize: '12px',
            fontWeight: '600',
            marginBottom: '18px'
          }}>
            AI-Powered Multi-Agent Research Platform
          </div>

          <h1 style={{
            margin: '0 0 14px 0',
            fontSize: '38px',
            lineHeight: '1.15',
            fontWeight: '700',
            letterSpacing: '-0.5px',
            color: '#ffffff'
          }}>
            Trade Smarter with <span style={{ color: '#10b981' }}>Autonomous</span> Market Intelligence
          </h1>

          <p style={{
            margin: '0 0 28px 0',
            color: '#94a3b8',
            fontSize: '15px',
            lineHeight: '1.6'
          }}>
            Analyze NSE, BSE, NASDAQ, and NYSE equities with real-time OHLCV pipelines, automated data validation, financial statements, and multi-agent research workflows.
          </p>

          {/* Stylized Stock Chart Preview Card */}
          <div style={{
            backgroundColor: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid #1e293b',
            borderRadius: '14px',
            padding: '20px',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.35)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div>
                <div style={{ fontSize: '14px', fontWeight: '700', color: '#f8fafc' }}>
                  AAPL • NASDAQ
                </div>
                <div style={{ fontSize: '11px', color: '#64748b' }}>
                  Multi-Agent Technical & Fundamental Signal
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '18px', fontWeight: '700', color: '#10b981' }}>$232.60</div>
                <div style={{ fontSize: '11px', color: '#10b981', fontWeight: '600' }}>+4.82% (1M)</div>
              </div>
            </div>

            {/* Clean SVG Area + Candlestick Preview */}
            <svg viewBox="0 0 420 130" style={{ width: '100%', height: '130px', display: 'block' }}>
              <defs>
                <linearGradient id="chartGlow" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
                  <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
                </linearGradient>
              </defs>
              {/* Subtle Grid Lines */}
              <line x1="0" y1="30" x2="420" y2="30" stroke="#1e293b" strokeDasharray="4 4" />
              <line x1="0" y1="70" x2="420" y2="70" stroke="#1e293b" strokeDasharray="4 4" />
              <line x1="0" y1="110" x2="420" y2="110" stroke="#1e293b" strokeDasharray="4 4" />

              {/* Area Fill */}
              <path
                d="M0 105 L45 96 L90 102 L135 80 L180 86 L225 60 L270 68 L315 42 L365 48 L420 20 L420 130 L0 130 Z"
                fill="url(#chartGlow)"
              />
              {/* Trend Line */}
              <path
                d="M0 105 L45 96 L90 102 L135 80 L180 86 L225 60 L270 68 L315 42 L365 48 L420 20"
                fill="none"
                stroke="#10b981"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {/* Pulsing End Dot */}
              <circle cx="420" cy="20" r="4" fill="#10b981" />
            </svg>

            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginTop: '12px',
              paddingTop: '12px',
              borderTop: '1px solid #1e293b',
              fontSize: '12px',
              color: '#94a3b8'
            }}>
              <span>OHLCV Validated</span>
              <span>4 Global Exchanges</span>
              <span style={{ color: '#38bdf8', fontWeight: '600' }}>JWT Secured</span>
            </div>
          </div>
        </div>

        {/* Right Side: Glassmorphism Login Card */}
        <div style={{
          flex: '1',
          minWidth: '320px',
          maxWidth: '410px',
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          border: '1px solid #1e293b',
          padding: '36px',
          borderRadius: '16px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          boxSizing: 'border-box'
        }}>
          <div style={{ marginBottom: '28px' }}>
            <h2 style={{ margin: '0 0 6px 0', color: '#ffffff', fontSize: '24px', fontWeight: '700' }}>
              Analyst Portal
            </h2>
            <p style={{ margin: 0, color: '#94a3b8', fontSize: '14px' }}>
              Sign in to access your market workspace
            </p>
          </div>

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: '#cbd5e1', fontWeight: '500' }}>
                Email Address
              </label>
              <input
                type="email"
                placeholder="analyst@firm.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  fontSize: '14px',
                  color: '#f8fafc',
                  backgroundColor: '#0b1120',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  boxSizing: 'border-box',
                  outline: 'none'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: '#cbd5e1', fontWeight: '500' }}>
                Password
              </label>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  fontSize: '14px',
                  color: '#f8fafc',
                  backgroundColor: '#0b1120',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  boxSizing: 'border-box',
                  outline: 'none'
                }}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              style={{
                marginTop: '6px',
                padding: '12px',
                fontSize: '15px',
                fontWeight: '600',
                color: '#ffffff',
                background: isLoading ? '#475569' : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                border: 'none',
                borderRadius: '8px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                boxShadow: isLoading ? 'none' : '0 8px 20px rgba(16, 185, 129, 0.25)'
              }}
            >
              {isLoading ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>

          {message && (
            <div style={{
              marginTop: '18px',
              padding: '12px',
              borderRadius: '8px',
              backgroundColor: message.includes('successful') ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
              border: message.includes('successful') ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(244, 63, 94, 0.4)',
              color: message.includes('successful') ? '#34d399' : '#fb7185',
              fontSize: '13px',
              textAlign: 'center',
              fontWeight: '500'
            }}>
              {message}
            </div>
          )}

          <p style={{ marginTop: '24px', textAlign: 'center', fontSize: '13px', color: '#94a3b8' }}>
            New to the platform?{' '}
            <Link to="/register" style={{ color: '#10b981', fontWeight: '600', textDecoration: 'none' }}>
              Create an account
            </Link>
          </p>
        </div>

      </div>
    </div>
  );
}

export default Login;