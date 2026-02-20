import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { Button } from '../ui/Button';
import { LogOut, ShieldAlert } from 'lucide-react';

interface AdminLayoutProps {
    children: React.ReactNode;
}

export const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
    const { logout } = useAuthStore();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login', { state: { from: { pathname: '/admin' } } });
    };

    return (
        <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
            {/* Admin Top Bar */}
            <header className="bg-white dark:bg-gray-800 shadow">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <ShieldAlert className="h-8 w-8 text-purple-600" />
                        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">StudyItUp Admin Panel</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <Button
                            variant="destructive"
                            onClick={handleLogout}
                            className="flex items-center gap-2"
                        >
                            <LogOut className="h-4 w-4" />
                            Logout
                        </Button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {children}
            </main>
        </div>
    );
};
