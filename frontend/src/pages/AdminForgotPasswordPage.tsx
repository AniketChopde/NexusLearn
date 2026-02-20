import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card';
import apiClient from '../api/client';
import { ShieldAlert, Mail, AlertCircle, CheckCircle } from 'lucide-react';

const schema = z.object({
    email: z
        .string()
        .min(1, 'Email is required')
        .email('Please enter a valid email address'),
});

type FormData = z.infer<typeof schema>;

// Navigate to admin login (LoginPage detects admin mode via from state)
const ADMIN_LOGIN_STATE = { state: { from: { pathname: '/admin' } } };

export const AdminForgotPasswordPage: React.FC = () => {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);
    const [isSubmitted, setIsSubmitted] = useState(false);
    const [apiError, setApiError] = useState<string | null>(null);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<FormData>({ resolver: zodResolver(schema) });

    const onSubmit = async (data: FormData) => {
        setIsLoading(true);
        setApiError(null);
        try {
            await apiClient.post('/admin/forgot-password', data);
            setIsSubmitted(true);
        } catch (error: any) {
            const detail = error?.response?.data?.detail;
            const httpStatus = error?.response?.status;

            if (httpStatus === 404) {
                setApiError(detail || 'No admin account found with this email address.');
            } else if (httpStatus === 403) {
                setApiError(detail || 'This email does not belong to an admin account.');
            } else {
                setApiError(detail || 'Something went wrong. Please try again later.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    if (isSubmitted) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 p-4">
                <Card className="w-full max-w-md">
                    <CardHeader className="space-y-1">
                        <div className="flex justify-center mb-2">
                            <div className="bg-green-100 dark:bg-green-900/30 p-4 rounded-full">
                                <CheckCircle className="h-10 w-10 text-green-600" />
                            </div>
                        </div>
                        <CardTitle className="text-2xl font-bold text-center">Check your email</CardTitle>
                        <CardDescription className="text-center">
                            An admin password reset link has been sent to your email. It expires in 30 minutes.
                        </CardDescription>
                    </CardHeader>
                    <CardFooter className="flex justify-center">
                        <Button variant="outline" onClick={() => navigate('/login', ADMIN_LOGIN_STATE)}>
                            Back to Admin Login
                        </Button>
                    </CardFooter>
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
                    <CardTitle className="text-2xl font-bold text-center">Admin Password Reset</CardTitle>
                    <CardDescription className="text-center">
                        Enter your admin email address. Only registered admin accounts can reset their password here.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        <Input
                            label="Admin Email Address"
                            type="email"
                            placeholder="admin@example.com"
                            error={errors.email?.message}
                            icon={<Mail className="h-4 w-4" />}
                            {...register('email')}
                        />

                        {apiError && (
                            <div className="flex items-start gap-2 p-3 rounded-md bg-destructive/10 border border-destructive/30 text-destructive text-sm">
                                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                                <span>{apiError}</span>
                            </div>
                        )}

                        <Button type="submit" className="w-full" isLoading={isLoading}>
                            Send Admin Reset Link
                        </Button>
                    </form>
                </CardContent>
                <CardFooter className="flex justify-center">
                    <button
                        onClick={() => navigate('/login', ADMIN_LOGIN_STATE)}
                        className="text-sm text-primary hover:underline"
                    >
                        Back to Admin Login
                    </button>
                </CardFooter>
            </Card>
        </div>
    );
};
