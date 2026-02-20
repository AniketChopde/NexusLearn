import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuthStore } from '../stores/authStore';
import { Button } from '../components/ui/Button';
import { ShieldAlert, AlertCircle } from 'lucide-react';
import { Input } from '../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card';

const loginSchema = z.object({
    email: z.string().email('Invalid email address'),
    password: z.string().min(1, 'Password is required'),
    rememberMe: z.boolean().optional(),
});

type LoginFormData = z.infer<typeof loginSchema>;

export const LoginPage: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { login, isLoading } = useAuthStore();

    // Field-level API errors (shown inline under each input)
    const [apiEmailError, setApiEmailError] = useState<string | null>(null);
    const [apiPasswordError, setApiPasswordError] = useState<string | null>(null);
    // Account-level errors shown as a banner
    const [apiError, setApiError] = useState<string | null>(null);

    const rememberedEmail = localStorage.getItem('remembered_email');
    const rememberedPassword = localStorage.getItem('remembered_password');

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginFormData>({
        resolver: zodResolver(loginSchema),
        defaultValues: {
            email: rememberedEmail || '',
            password: rememberedPassword || '',
            rememberMe: !!rememberedEmail,
        }
    });

    const onSubmit = async (data: LoginFormData) => {
        // Clear previous API errors on new submit
        setApiEmailError(null);
        setApiPasswordError(null);
        setApiError(null);

        try {
            if (data.rememberMe) {
                localStorage.setItem('remembered_email', data.email);
                localStorage.setItem('remembered_password', data.password);
            } else {
                localStorage.removeItem('remembered_email');
                localStorage.removeItem('remembered_password');
            }
            await login(data);

            // Superusers always go to admin panel
            const loggedInUser = useAuthStore.getState().user;
            if (loggedInUser?.is_superuser) {
                navigate('/admin', { replace: true });
            } else {
                const from = location.state?.from?.pathname || '/dashboard';
                navigate(from, { replace: true });
            }
        } catch (error: any) {
            const httpStatus = error?.response?.status;
            const detail = error?.response?.data?.detail;

            if (httpStatus === 404) {
                // Email not found — highlight email field
                setApiEmailError(detail || 'No account found with this email address.');
            } else if (httpStatus === 401) {
                // Wrong password — highlight password field
                setApiPasswordError(detail || 'Incorrect password. Please try again.');
            } else if (httpStatus === 403) {
                // Account deactivated — show as banner
                setApiError(detail || 'Your account has been deactivated. Please contact support.');
            } else if (!error?.response) {
                setApiError('Cannot reach the server. Please check your connection.');
            } else {
                setApiError(detail || 'Login failed. Please try again.');
            }
        }
    };

    const from = location.state?.from?.pathname || '/dashboard';
    const isAdminLogin = from.includes('/admin');

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 to-secondary/10 p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="space-y-1">
                    <div className="flex flex-col items-center justify-center gap-2 mb-2">
                        {isAdminLogin ? (
                             <ShieldAlert className="h-12 w-12 text-purple-600" />
                        ) : (
                            <img src="/logo.png" alt="StudyItUp" className="h-12 w-12" />
                        )}
                        <span className="text-2xl font-bold text-primary">StudyItUp</span>
                    </div>
                    <CardTitle className="text-3xl font-bold text-center">
                        {isAdminLogin ? 'Admin Login' : 'Welcome Back'}
                    </CardTitle>
                    <CardDescription className="text-center">
                        {isAdminLogin
                            ? 'Secure access for administrators only'
                            : 'Sign in to your StudyItUp account'}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        <Input
                            label="Email"
                            type="email"
                            placeholder="you@example.com"
                            error={errors.email?.message || apiEmailError || undefined}
                            {...register('email')}
                        />
                        <Input
                            label="Password"
                            type="password"
                            placeholder="••••••••"
                            error={errors.password?.message || apiPasswordError || undefined}
                            {...register('password')}
                        />

                        {apiError && (
                            <div className="flex items-start gap-2 p-3 rounded-md bg-destructive/10 border border-destructive/30 text-destructive text-sm">
                                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                                <span>{apiError}</span>
                            </div>
                        )}

                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                                <input
                                    type="checkbox"
                                    id="rememberMe"
                                    className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                                    {...register('rememberMe')}
                                />
                                <label htmlFor="rememberMe" className="text-sm text-gray-500 font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                    Remember me
                                </label>
                            </div>
                            {!isAdminLogin && (
                                <Link
                                    to="/forgot-password"
                                    className="text-sm font-medium text-primary hover:underline"
                                >
                                    Forgot password?
                                </Link>
                            )}
                        </div>
                        <Button type="submit" className="w-full" isLoading={isLoading}>
                            Sign In
                        </Button>
                    </form>
                </CardContent>
                <CardFooter className="flex flex-col space-y-2">
                    {!isAdminLogin && (
                        <p className="text-sm text-center text-muted-foreground">
                            Don't have an account?{' '}
                            <Link to="/register" className="text-primary hover:underline">
                                Sign up
                            </Link>
                        </p>
                    )}
                    {isAdminLogin && (
                        <p className="text-sm text-center text-muted-foreground">
                            Forgot your admin password?{' '}
                            <Link to="/admin/forgot-password" className="text-purple-600 hover:underline font-medium">
                                Reset it here
                            </Link>
                        </p>
                    )}
                </CardFooter>
            </Card>
        </div>
    );
};
