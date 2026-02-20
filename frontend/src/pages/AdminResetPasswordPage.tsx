import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card';
import apiClient from '../api/client';
import toast from 'react-hot-toast';
import { ShieldAlert, Lock, AlertCircle, CheckCircle } from 'lucide-react';

const schema = z.object({
    password: z
        .string()
        .min(8, 'Password must be at least 8 characters')
        .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
        .regex(/[0-9]/, 'Must contain at least one number'),
    confirmPassword: z.string().min(1, 'Please confirm your password'),
}).refine((d) => d.password === d.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
});

type FormData = z.infer<typeof schema>;

export const AdminResetPasswordPage: React.FC = () => {
    const [searchParams] = useSearchParams();
    const token = searchParams.get('token');
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);
    const [apiError, setApiError] = useState<string | null>(null);
    const [isSuccess, setIsSuccess] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<FormData>({ resolver: zodResolver(schema) });

    const onSubmit = async (data: FormData) => {
        if (!token) {
            toast.error('Invalid token. Please request a new admin reset link.');
            return;
        }
        setIsLoading(true);
        setApiError(null);
        try {
            await apiClient.post('/admin/reset-password', {
                token,
                new_password: data.password,
            });
            setIsSuccess(true);
            toast.success('Admin password reset successfully!');
            setTimeout(() => navigate('/login'), 2000);
        } catch (error: any) {
            const detail = error?.response?.data?.detail;
            const httpStatus = error?.response?.status;

            if (httpStatus === 400 || httpStatus === 403) {
                setApiError(detail || 'This reset link is invalid or expired.');
            } else {
                setApiError(detail || 'Something went wrong. Please try again later.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    if (!token) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 p-4">
                <Card className="w-full max-w-md">
                    <CardHeader>
                        <div className="flex justify-center mb-2">
                            <div className="bg-destructive/10 p-4 rounded-full">
                                <AlertCircle className="h-10 w-10 text-destructive" />
                            </div>
                        </div>
                        <CardTitle className="text-xl font-bold text-center text-destructive">Invalid Link</CardTitle>
                        <CardDescription className="text-center">
                            This admin password reset link is missing or invalid. Please request a new one.
                        </CardDescription>
                    </CardHeader>
                    <CardFooter className="flex justify-center">
                        <Link to="/admin/forgot-password">
                            <Button>Request New Admin Reset Link</Button>
                        </Link>
                    </CardFooter>
                </Card>
            </div>
        );
    }

    if (isSuccess) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 p-4">
                <Card className="w-full max-w-md">
                    <CardHeader>
                        <div className="flex justify-center mb-2">
                            <div className="bg-green-100 dark:bg-green-900/30 p-4 rounded-full">
                                <CheckCircle className="h-10 w-10 text-green-600" />
                            </div>
                        </div>
                        <CardTitle className="text-xl font-bold text-center">Admin Password Updated!</CardTitle>
                        <CardDescription className="text-center">
                            Password reset successful. Redirecting to login...
                        </CardDescription>
                    </CardHeader>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="space-y-1">
                    <div className="flex flex-col items-center gap-2 mb-2">
                        <ShieldAlert className="h-10 w-10 text-purple-600" />
                    </div>
                    <CardTitle className="text-2xl font-bold text-center">Reset Admin Password</CardTitle>
                    <CardDescription className="text-center">
                        Enter your new admin password. Must be 8+ characters with an uppercase letter and number.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        <Input
                            label="New Password"
                            type="password"
                            placeholder="••••••••"
                            error={errors.password?.message}
                            icon={<Lock className="h-4 w-4" />}
                            {...register('password')}
                        />
                        <Input
                            label="Confirm Password"
                            type="password"
                            placeholder="••••••••"
                            error={errors.confirmPassword?.message}
                            icon={<Lock className="h-4 w-4" />}
                            {...register('confirmPassword')}
                        />

                        {apiError && (
                            <div className="flex items-start gap-2 p-3 rounded-md bg-destructive/10 border border-destructive/30 text-destructive text-sm">
                                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                                <div>
                                    <span>{apiError}</span>
                                    {apiError.toLowerCase().includes('expired') || apiError.toLowerCase().includes('invalid') ? (
                                        <div className="mt-1">
                                            <Link to="/admin/forgot-password" className="font-semibold underline">
                                                Request a new admin reset link →
                                            </Link>
                                        </div>
                                    ) : null}
                                </div>
                            </div>
                        )}

                        <Button type="submit" className="w-full" isLoading={isLoading}>
                            Reset Admin Password
                        </Button>
                    </form>
                </CardContent>
                <CardFooter className="flex justify-center">
                    <Link to="/login" className="text-sm text-primary hover:underline">
                        Back to Login
                    </Link>
                </CardFooter>
            </Card>
        </div>
    );
};
