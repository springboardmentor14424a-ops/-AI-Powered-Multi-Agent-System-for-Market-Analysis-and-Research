import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';
import api from './api/axios';

vi.mock('./api/axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    interceptors: { request: { use: vi.fn() } },
  },
}));

describe('StockMind AI Frontend', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    window.history.pushState({}, '', '/');
  });

  it('renders the landing page with hero heading, features, and how it works', () => {
    render(<App />);
    expect(
      screen.getByText(/Intelligent Stock Research\./i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Powered by Multi-Agent AI\./i)
    ).toBeInTheDocument();
    expect(screen.getByText('Fundamental Analysis')).toBeInTheDocument();
    expect(screen.getByText('Technical Analysis')).toBeInTheDocument();
    expect(screen.getByText('News & Sentiment Intelligence')).toBeInTheDocument();
    expect(screen.getByText('Risk Assessment')).toBeInTheDocument();
    expect(screen.getByText('AI-Powered Reports')).toBeInTheDocument();
    expect(screen.getByText('Smart Watchlists')).toBeInTheDocument();
    expect(screen.getByText('Search Stock')).toBeInTheDocument();
    expect(screen.getByText('Collect Market Data')).toBeInTheDocument();
  });

  it('redirects unauthenticated /dashboard access to /login', async () => {
    window.history.pushState({}, '', '/dashboard');
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText(/Welcome Back/i)).toBeInTheDocument();
    });
  });

  it('submits registration form and redirects to /login on success', async () => {
    api.post.mockResolvedValueOnce({
      data: {
        message: 'User registered successfully',
        user: { id: 1, full_name: 'Jane Doe', email: 'jane@example.com' },
      },
    });

    window.history.pushState({}, '', '/register');
    render(<App />);

    fireEvent.change(screen.getByPlaceholderText(/John Doe/i), {
      target: { value: 'Jane Doe' },
    });
    fireEvent.change(screen.getByPlaceholderText(/you@example.com/i), {
      target: { value: 'jane@example.com' },
    });

    const passwordInputs = screen.getAllByPlaceholderText('••••••••');
    fireEvent.change(passwordInputs[0], {
      target: { value: 'StrongPass123!' },
    });
    fireEvent.change(passwordInputs[1], {
      target: { value: 'StrongPass123!' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/auth/register', {
        full_name: 'Jane Doe',
        email: 'jane@example.com',
        password: 'StrongPass123!',
      });
    });
  });
});

