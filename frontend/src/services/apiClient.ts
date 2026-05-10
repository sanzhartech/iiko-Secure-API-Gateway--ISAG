import axios from 'axios';

export const apiClient = axios.create({
  baseURL: '',
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
      // Only redirect to login if it was a main info request or if we are not already on login page
      // and if the request was to /auth/me or it's a persistent failure.
      const requestUrl = String(error.config?.url ?? '');
      const isMeRequest = requestUrl.includes('/auth/me');
      
      if (isMeRequest || window.location.pathname !== '/login') {
         // Optionally try to refresh token here if implemented
         // For now, only redirect if it's the 'me' request that failed
         if (isMeRequest) {
           localStorage.removeItem('admin_access_token');
           window.location.href = '/login';
         }
      }
    }
    return Promise.reject(error);
  }
);
