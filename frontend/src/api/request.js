import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('smart-agriculture-token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('smart-agriculture-token')
      localStorage.removeItem('smart-agriculture-user')
      if (window.location.pathname !== '/login') window.location.assign('/login')
    }
    const message = error.response?.data?.message || error.response?.data?.detail || (error.code === 'ECONNABORTED' ? '请求超时，请检查网络后重试' : '请求失败，请稍后重试')
    error.message = message
    return Promise.reject(error)
  },
)

export default request
