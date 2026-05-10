import axios from 'axios';

export const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // If unauthorized, clear token and redirect to login
    if (error.response?.status === 401) {
      if (window.location.pathname !== '/login') {
        localStorage.removeItem('admin_access_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
