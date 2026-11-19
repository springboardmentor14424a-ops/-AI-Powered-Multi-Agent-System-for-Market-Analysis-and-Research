import axios from 'axios'

const api = axios.create({ baseURL: 'http://127.0.0.1:8000' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url || ''
    if (
      error.response?.status === 401 &&
      !url.includes('/auth/login') &&
      localStorage.getItem('token')
    ) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export function getErrorMessage(error) {
  if (!error.response) return 'Cannot reach the server. Is the backend running?'
  const detail = error.response.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    return detail.map((d) => d.msg.replace(/^Value error, /, '')).join('. ')
  }
  return 'Something went wrong. Please try again.'
}

export default api