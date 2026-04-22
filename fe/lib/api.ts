
import axios from "axios";

// Update API_BASE_URL to localhost for development
const API_BASE_URL = "http://localhost:3000";

console.log("🔗 API Base URL:", API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    // Bypass ngrok browser warning for free accounts (kept for compatibility if switched back)
    "ngrok-skip-browser-warning": "true",
    "Bypass-Tunnel-Reminder": "true",
    "Content-Type": "application/json",
    "Accept": "application/json",
  },
});

// Attach Bearer token
api.interceptors.request.use((config) => {
  const token =
    sessionStorage.getItem("accessToken") ||
    localStorage.getItem("accessToken");

  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor for better debugging
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === "ERR_NETWORK") {
      console.error("Network Error detected. This might be due to CORS or the server being unreachable.");
    }
    return Promise.reject(error);
  }
);

export default api;
