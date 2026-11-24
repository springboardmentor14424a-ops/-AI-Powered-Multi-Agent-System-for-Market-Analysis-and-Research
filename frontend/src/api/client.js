import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  withCredentials: true, // Sends secure, HTTP-only session cookies automatically
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor: automatically redirect to login when session expires or is unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const url = error.config?.url || '';
      const isAuthForm = url.includes('/auth/login') || url.includes('/auth/register');
      
      if (!isAuthForm) {
        // Clear any residual items
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        sessionStorage.clear();

        // Redirect to login page without showing technical errors
        if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
