import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { Button } from '../ui/Button';
import {
    Home,
    BookOpen,
    MessageSquare,
    LogOut,
    Menu,
    X,
    ShieldCheck,
    Brain,
    BarChart,
} from 'lucide-react';

const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Study Plans', href: '/study-plans', icon: BookOpen },
    { name: 'Learning Chat', href: '/chat', icon: MessageSquare },
    { name: 'Take Quiz', href: '/quiz', icon: Brain },
    { name: 'View Analytics', href: '/analytics', icon: BarChart },
    { name: 'Test Center', href: '/test-center', icon: ShieldCheck },
];

interface LayoutProps {
    children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
    const [sidebarOpen, setSidebarOpen] = React.useState(false);
    const { user, logout } = useAuthStore();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="min-h-screen bg-background">
            {/* Mobile sidebar */}
            {sidebarOpen && (
                <div className="fixed inset-0 z-50 lg:hidden">
                    <div className="fixed inset-0 bg-black/50" onClick={() => setSidebarOpen(false)} />
                    <div className="fixed inset-y-0 left-0 w-64 bg-card border-r flex flex-col">
                        <div className="flex items-center justify-between p-4 border-b">
                            <div className="flex items-center gap-2">
                                <img src="/logo.png" alt="StudyItUp" className="h-12 w-12 mix-blend-multiply" />
                                <h1 className="text-xl font-bold">StudyItUp</h1>
                            </div>
                            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(false)}>
                                <X className="h-5 w-5" />
                            </Button>
                        </div>
                        <nav className="flex-1 p-4 space-y-2">
                            {navigation.map((item) => (
                                <Link
                                    key={item.name}
                                    to={item.href}
                                    className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent transition-colors"
                                    onClick={() => setSidebarOpen(false)}
                                >
                                    <item.icon className="h-5 w-5" />
                                    <span>{item.name}</span>
                                </Link>
                            ))}
                        </nav>
                        <div className="p-4 border-t">
                            <Button
                                variant="ghost"
                                className="w-full justify-start"
                                onClick={handleLogout}
                            >
                                <LogOut className="h-5 w-5 mr-3" />
                                Logout
                            </Button>
                        </div>
                    </div>
                </div>
            )}

            {/* Desktop sidebar */}
            <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
                <div className="flex flex-col flex-1 border-r bg-card">
                    <div className="flex items-center h-16 px-6 border-b">
                        <div className="flex items-center gap-2">
                            <img src="/logo.png" alt="StudyItUp" className="h-12 w-12 mix-blend-multiply" />
                            <h1 className="text-xl font-bold">StudyItUp</h1>
                        </div>
                    </div>
                    <nav className="flex-1 p-4 space-y-2">
                        {navigation.map((item) => (
                            <Link
                                key={item.name}
                                to={item.href}
                                className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent transition-colors"
                            >
                                <item.icon className="h-5 w-5" />
                                <span>{item.name}</span>
                            </Link>
                        ))}
                    </nav>
                    <div className="p-4 border-t">
                        <Button
                            variant="ghost"
                            className="w-full justify-start"
                            onClick={handleLogout}
                        >
                            <LogOut className="h-5 w-5 mr-3" />
                            Logout
                        </Button>
                    </div>
                </div>
            </div>

            {/* Main content */}
            <div className="lg:pl-64">
                {/* Top bar */}
                <div className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b bg-card px-4 lg:px-8">
                    <Button
                        variant="ghost"
                        size="icon"
                        className="lg:hidden"
                        onClick={() => setSidebarOpen(true)}
                    >
                        <Menu className="h-5 w-5" />
                    </Button>
                    <div className="flex-1" />
                    <div className="flex items-center gap-4">
                        <div className="text-sm">
                            <p className="font-medium">{user?.full_name || user?.email}</p>
                            <p className="text-xs text-muted-foreground">{user?.email}</p>
                        </div>
                        <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-semibold">
                            {user?.full_name?.[0] || user?.email?.[0] || 'U'}
                        </div>
                    </div>
                </div>

                {/* Page content */}
                <main className="p-4 lg:p-8">
                    {children}
                </main>
            </div>
        </div>
    );
};
