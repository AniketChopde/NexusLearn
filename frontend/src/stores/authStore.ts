import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authService } from '../api/services';
import type { User, LoginCredentials, RegisterData } from '../types';
import toast from 'react-hot-toast';

interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;

    // Actions
    login: (credentials: LoginCredentials) => Promise<void>;
    register: (data: RegisterData) => Promise<void>;
    logout: () => void;
    fetchProfile: () => Promise<void>;
    setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,

            login: async (credentials) => {
                try {
                    set({ isLoading: true });
                    const response = await authService.login(credentials);
                    const { access_token, refresh_token } = response.data;

                    localStorage.setItem('access_token', access_token);
                    localStorage.setItem('refresh_token', refresh_token);

                    // Fetch user profile
                    const profileResponse = await authService.getProfile();
                    const user = profileResponse.data;

                    set({
                        user,
                        token: access_token,
                        isAuthenticated: true,
                        isLoading: false,
                    });

                    toast.success('Login successful!');
                } catch (error: any) {
                    set({ isLoading: false });
                    toast.error(error.response?.data?.detail || 'Login failed');
                    throw error;
                }
            },

            register: async (data) => {
                try {
                    set({ isLoading: true });
                    await authService.register(data);

                    // Auto-login after registration
                    await useAuthStore.getState().login({
                        email: data.email,
                        password: data.password,
                    });

                    toast.success('Registration successful!');
                } catch (error: any) {
                    set({ isLoading: false });
                    toast.error(error.response?.data?.detail || 'Registration failed');
                    throw error;
                }
            },

            logout: () => {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');

                set({
                    user: null,
                    token: null,
                    isAuthenticated: false,
                });

                toast.success('Logged out successfully');
            },

            fetchProfile: async () => {
                try {
                    const response = await authService.getProfile();
                    set({ user: response.data, isAuthenticated: true });
                } catch (error) {
                    console.error('Failed to fetch profile:', error);
                }
            },

            setUser: (user) => set({ user }),
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({
                user: state.user,
                token: state.token,
                isAuthenticated: state.isAuthenticated,
            }),
        }
    )
);
