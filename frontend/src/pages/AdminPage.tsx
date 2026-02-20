
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { Trash2, User as UserIcon, ShieldAlert, Activity, MessageSquare, Users, ThumbsUp, ThumbsDown, Star } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { fetchUsers, deleteUser, fetchEngagements } from '../api/admin';
import type { User, Engagement } from '../types';

type Tab = 'users' | 'activity' | 'feedback';

const AdminPage: React.FC = () => {
    const { user: currentUser } = useAuthStore();
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState<Tab>('users');
    
    const [users, setUsers] = useState<User[]>([]);
    const [engagements, setEngagements] = useState<Engagement[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (currentUser && !currentUser.is_superuser) {
            toast.error("Access Denied: Admin privileges required.");
            navigate('/dashboard');
            return;
        }
        loadData();
    }, [currentUser, navigate, activeTab]);

    const loadData = async () => {
        setLoading(true);
        try {
            if (activeTab === 'users') {
                const data = await fetchUsers();
                setUsers(data.filter(u => !u.is_superuser));
            } else {
                const data = await fetchEngagements();
                setEngagements(data);
            }
        } catch (error) {
            console.error("Failed to fetch data:", error);
            toast.error("Failed to load data.");
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteUser = async (userId: string) => {
        if (!window.confirm("Are you sure you want to delete this user? This action cannot be undone.")) {
            return;
        }
        try {
            await deleteUser(userId);
            toast.success("User deleted successfully");
            setUsers(users.filter(u => u.id !== userId));
        } catch (error) {
            console.error("Failed to delete user:", error);
            toast.error("Failed to delete user.");
        }
    };

    const LoadingSpinner = () => (
        <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
        </div>
    );

    const UsersTable = () => (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Email</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Role</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Joined</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {users.map((user) => (
                            <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                                <td className="px-6 py-4 whitespace-nowrap flex items-center">
                                    <div className="flex-shrink-0 h-8 w-8 bg-primary/10 rounded-full flex items-center justify-center mr-3">
                                        <UserIcon className="h-4 w-4 text-primary" />
                                    </div>
                                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{user.full_name || 'Guest'}</span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{user.email}</td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${user.is_superuser ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'}`}>
                                        {user.is_superuser ? 'Admin' : 'User'}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                    {new Date(user.created_at).toLocaleDateString()}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <button onClick={() => handleDeleteUser(user.id)} className="text-red-600 hover:text-red-900 p-2 rounded-full hover:bg-red-50">
                                        <Trash2 className="w-5 h-5" />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );

    const ActivityTable = () => {
        // Filter out items with comments (feedback) if desired, or show all actions
        // User asked for "Activity" and "Feedback" separately.
        // Activity = Likes/Dislikes/Ratings (maybe without text?)
        // Feedback = Items with comments.
        // Let's simpler: Activity shows EVERYTHING chronologically.
        
        const activityLog = engagements; 

        return (
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-900">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">User</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Action</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Content</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Date</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                            {activityLog.map((log) => (
                                <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                                        {log.user?.email || 'Unknown User'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center gap-2">
                                            {log.action === 'like' && <ThumbsUp className="w-4 h-4 text-green-500" />}
                                            {log.action === 'dislike' && <ThumbsDown className="w-4 h-4 text-red-500" />}
                                            {log.action === 'rate' && <Star className="w-4 h-4 text-yellow-500" />}
                                            <span className="text-sm capitalize">{log.action} {log.action === 'rate' && `(${log.value})`}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                        <span className="capitalize">{log.content_type}</span>: {log.content_id.substring(0, 8)}...
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                        {new Date(log.created_at).toLocaleString()}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    const FeedbackTable = () => {
        const feedbacks = engagements.filter(e => e.comment && e.comment.trim().length > 0);

        if (feedbacks.length === 0) {
            return <div className="p-8 text-center text-gray-500">No feedback entries found.</div>;
        }

        return (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {feedbacks.map((item) => (
                    <div key={item.id} className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 relative">
                        <div className="flex justify-between items-start mb-4">
                            <div className="flex items-center gap-2">
                                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">
                                    {item.user?.full_name?.[0] || item.user?.email?.[0]?.toUpperCase() || 'U'}
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{item.user?.full_name || 'User'}</p>
                                    <p className="text-xs text-gray-500">{item.user?.email}</p>
                                </div>
                            </div>
                            <span className="text-xs text-gray-400">{new Date(item.created_at).toLocaleDateString()}</span>
                        </div>
                        
                        <div className="mb-4">
                            <p className="text-gray-700 dark:text-gray-300 italic">"{item.comment}"</p>
                        </div>

                        <div className="flex items-center justify-between text-xs text-gray-500 pt-4 border-t dark:border-gray-700">
                            <span className="capitalize bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">{item.content_type}</span>
                            <div className="flex items-center gap-1">
                                {item.action === 'rate' && <Star className="w-3 h-3 text-yellow-500 fill-yellow-500" />}
                                <span>{item.action === 'rate' ? `${item.value}/5` : item.action}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-3">
                    <ShieldAlert className="w-8 h-8 text-primary" />
                    Admin Dashboard
                </h1>
                <div className="flex space-x-2 bg-white dark:bg-gray-800 p-1 rounded-lg shadow-sm border dark:border-gray-700">
                    <button
                        onClick={() => setActiveTab('users')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                            activeTab === 'users' 
                            ? 'bg-primary text-primary-foreground' 
                            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                    >
                        <Users className="w-4 h-4" /> Users
                    </button>
                    <button
                        onClick={() => setActiveTab('activity')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                            activeTab === 'activity' 
                            ? 'bg-primary text-primary-foreground' 
                            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                    >
                        <Activity className="w-4 h-4" /> Activity
                    </button>
                    <button
                        onClick={() => setActiveTab('feedback')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                            activeTab === 'feedback' 
                            ? 'bg-primary text-primary-foreground' 
                            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                    >
                        <MessageSquare className="w-4 h-4" /> Feedback
                    </button>
                </div>
            </div>

            {loading ? (
                <LoadingSpinner />
            ) : (
                <>
                    {activeTab === 'users' && <UsersTable />}
                    {activeTab === 'activity' && <ActivityTable />}
                    {activeTab === 'feedback' && <FeedbackTable />}
                </>
            )}
        </div>
    );
};

export default AdminPage;
