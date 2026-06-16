import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const http: AxiosInstance = axios.create({
  baseURL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

http.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

http.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default http
