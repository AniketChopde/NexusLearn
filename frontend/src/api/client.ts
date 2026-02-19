import axios from 'axios';
import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import toast from 'react-hot-toast';

// Production best practice: explicit /api path
// This is cleaner, more maintainable, and easier to refactor later
// Using import.meta.env (Vite-specific, NOT process.env)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// Create axios instance with professional configuration
const apiClient: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 300000, // 5 minutes to accommodate slow AI generations or searches
    withCredentials: false, // Set to true if using auth cookies
});

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        // Skip adding access token for refresh requests as they use the refresh token
        if (config.url?.includes('/auth/refresh')) {
            return config;
        }

        const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Single in-flight refresh: avoid multiple 401s all triggering refresh at once
let refreshPromise: Promise<string | null> | null = null;

function clearAuthAndRedirect(reason?: string) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
<<<<<<< HEAD
    localStorage.removeItem('auth-storage'); // clear persisted auth state so reload shows login
    if (reason) toast.error(reason);
=======
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
>>>>>>> origin/updatestudyitup
    window.location.href = '/login';
}

function isRefreshRequest(config: InternalAxiosRequestConfig): boolean {
    const url = config.url ?? '';
    const baseURL = config.baseURL ?? '';
    const full = url.startsWith('http') ? url : `${baseURL.replace(/\/$/, '')}/${url.replace(/^\//, '')}`;
    return full.includes('/auth/refresh');
}

// Response interceptor - Handle errors and token refresh
apiClient.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
        const status = error.response?.status;
        const url = originalRequest?.url;

        console.debug(`[API Error] Status: ${status} | URL: ${url}`, error.response?.data);

        // If this 401 is FROM the refresh call itself, do not try to refresh again (prevents loop)
<<<<<<< HEAD
        if (error.response?.status === 401 && isRefreshRequest(originalRequest)) {
            clearAuthAndRedirect('Session expired. Please sign in again.');
=======
        if (status === 401 && isRefreshRequest(originalRequest)) {
            console.error('[API] Refresh token expired or invalid. Redirecting to login.');
            clearAuthAndRedirect();
>>>>>>> origin/updatestudyitup
            return Promise.reject(error);
        }

        // Handle 401 Unauthorized - Token expired (for normal API calls)
        if (status === 401 && !originalRequest._retry) {
            console.debug('[API] Access token expired. Attempting refresh...');
            originalRequest._retry = true;

            const localRefresh = localStorage.getItem('refresh_token');
            const sessionRefresh = sessionStorage.getItem('refresh_token');
            const refreshToken = localRefresh || sessionRefresh;

            if (!refreshToken) {
<<<<<<< HEAD
                clearAuthAndRedirect('Session expired. Please sign in again.');
=======
                console.warn('[API] No refresh token available. Redirecting.');
                clearAuthAndRedirect();
>>>>>>> origin/updatestudyitup
                return Promise.reject(error);
            }

            try {
                // Only one refresh at a time; other 401s wait for this
                if (!refreshPromise) {
                    refreshPromise = (async () => {
                        try {
                            const response = await apiClient.post(
                                '/auth/refresh',
                                {},
                                {
                                    headers: { Authorization: `Bearer ${refreshToken}` },
                                    // Mark so the interceptor won't try to refresh again if this 401s
                                } as InternalAxiosRequestConfig
                            );
                            const { access_token, refresh_token: newRefresh } = response.data;

                            if (localRefresh) {
                                localStorage.setItem('access_token', access_token);
                                localStorage.setItem('refresh_token', newRefresh);
                            } else {
                                sessionStorage.setItem('access_token', access_token);
                                sessionStorage.setItem('refresh_token', newRefresh);
                            }

                            console.debug('[API] Token refresh successful.');
                            return access_token;
                        } finally {
                            refreshPromise = null;
                        }
                    })();
                }

                const newAccessToken = await refreshPromise;
                if (newAccessToken && originalRequest.headers) {
                    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                    return apiClient(originalRequest);
                }
            } catch (refreshError) {
                console.error('[API] Token refresh failed:', refreshError);
                refreshPromise = null;
                clearAuthAndRedirect('Session expired. Please sign in again.');
                return Promise.reject(refreshError);
            }
        }

        // Server unreachable or 5xx: logout so user isn't stuck with a broken UI
        const status = error.response?.status;
        const isServerError = status != null && status >= 500;
        const isNetworkError = !error.response || error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED';
        if (isServerError || isNetworkError) {
            clearAuthAndRedirect('Server unavailable. Please sign in again.');
            return Promise.reject(error);
        }

        // Handle other errors (4xx etc.) – show toast only, stay logged in
        const errorData = error.response?.data as any;
        const errorMessage = errorData?.detail || errorData?.message || error.message || 'An error occurred';
<<<<<<< HEAD
        toast.error(errorMessage);
=======

        // Filter out 401s from toasting (handled above or ignored during refresh flow)
        // Also handling 403 explicitly if that's what user sees as "Not authenticated"
        if (status !== 401) {
            // For 404s on API endpoints, it might mean Nginx misconfig or wrong URL.
            // We should still toast but maybe clarify?
            if (status === 404 && url?.includes('/api/')) {
                console.error('[API] 404 Not Found. Potential Nginx/URL issue.');
            }
            toast.error(errorMessage);
        }
>>>>>>> origin/updatestudyitup

        return Promise.reject(error);
    }
);

// Content Upload API
export const uploadContent = async (planId: string, file: File | null, url: string | null) => {
    const formData = new FormData();
    formData.append('plan_id', planId);
    if (file) {
        formData.append('file', file);
    }
    if (url) {
        formData.append('url', url);
    }

    const response = await apiClient.post('/content/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export default apiClient;
