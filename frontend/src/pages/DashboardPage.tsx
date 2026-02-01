import React from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useStudyPlanStore } from '../stores/studyPlanStore';
import { Loading } from '../components/ui/Loading';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { BookOpen, Brain, MessageSquare, TrendingUp, Clock, Target, Award, Flame } from 'lucide-react';

export const DashboardPage: React.FC = () => {
    const { user } = useAuthStore();
    const { plans, isLoading, fetchPlans } = useStudyPlanStore();

    React.useEffect(() => {
        fetchPlans();
    }, []);

    if (isLoading && plans.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px]">
                <Loading size="lg" text="Loading dashboard..." />
            </div>
        );
    }

    const activePlan = plans.find((p) => p.status === 'active');

    const stats = [
        { name: 'Study Streak', value: '7 days', icon: Flame, color: 'text-orange-500' },
        { name: 'Hours Studied', value: '24.5h', icon: Clock, color: 'text-blue-500' },
        { name: 'Topics Completed', value: '12/45', icon: Target, color: 'text-green-500' },
        { name: 'Quiz Average', value: '78%', icon: Award, color: 'text-purple-500' },
    ];

    const quickActions = [
        { name: 'Start Learning', href: '/chat', icon: MessageSquare, color: 'bg-blue-500' },
        { name: 'Take Quiz', href: '/quiz', icon: Brain, color: 'bg-purple-500' },
        { name: 'Create Plan', href: '/study-plans/create', icon: BookOpen, color: 'bg-green-500' },
        { name: 'View Analytics', href: '/analytics', icon: TrendingUp, color: 'bg-orange-500' },
    ];

    return (
        <div className="space-y-8">
            {/* Welcome Section */}
            <div>
                <h1 className="text-3xl font-bold">Welcome back, {user?.full_name || 'Student'}! 👋</h1>
                <p className="text-muted-foreground mt-2">
                    Here's your learning progress and what's next
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.map((stat) => (
                    <Card key={stat.name}>
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">{stat.name}</p>
                                    <p className="text-2xl font-bold mt-1">{stat.value}</p>
                                </div>
                                <stat.icon className={`h-8 w-8 ${stat.color}`} />
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Active Study Plan */}
            {activePlan ? (
                <Card>
                    <CardHeader>
                        <CardTitle>Active Study Plan</CardTitle>
                        <CardDescription>{activePlan.exam_type}</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">Target Date</span>
                                <span className="font-medium">{new Date(activePlan.target_date).toLocaleDateString()}</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">Daily Hours</span>
                                <span className="font-medium">{activePlan.daily_hours}h</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">Chapters</span>
                                <span className="font-medium">{activePlan.chapters?.length || 0}</span>
                            </div>
                            <Link to={`/study-plans/${activePlan.id}`}>
                                <Button className="w-full mt-4">View Full Plan</Button>
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            ) : (
                <Card>
                    <CardHeader>
                        <CardTitle>No Active Study Plan</CardTitle>
                        <CardDescription>Create a study plan to get started</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Link to="/study-plans/create">
                            <Button className="w-full">Create Study Plan</Button>
                        </Link>
                    </CardContent>
                </Card>
            )}

            {/* Quick Actions */}
            <div>
                <h2 className="text-2xl font-bold mb-4">Quick Actions</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {quickActions.map((action) => (
                        <Link key={action.name} to={action.href}>
                            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                                <CardContent className="p-6">
                                    <div className="flex flex-col items-center text-center space-y-3">
                                        <div className={`${action.color} p-3 rounded-lg`}>
                                            <action.icon className="h-6 w-6 text-white" />
                                        </div>
                                        <p className="font-medium">{action.name}</p>
                                    </div>
                                </CardContent>
                            </Card>
                        </Link>
                    ))}
                </div>
            </div>

            {/* Today's Schedule */}
            <Card>
                <CardHeader>
                    <CardTitle>Today's Schedule</CardTitle>
                    <CardDescription>Your planned activities for today</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-3">
                        {[
                            { time: '09:00 AM', task: 'Operating Systems - Process Synchronization', duration: '2h' },
                            { time: '02:00 PM', task: 'Database Management - SQL Queries', duration: '1.5h' },
                            { time: '05:00 PM', task: 'Quiz - Computer Networks', duration: '30m' },
                        ].map((item, index) => (
                            <div key={index} className="flex items-center justify-between p-3 bg-accent rounded-lg">
                                <div className="flex items-center gap-3">
                                    <Clock className="h-4 w-4 text-muted-foreground" />
                                    <div>
                                        <p className="font-medium">{item.task}</p>
                                        <p className="text-sm text-muted-foreground">{item.time}</p>
                                    </div>
                                </div>
                                <span className="text-sm text-muted-foreground">{item.duration}</span>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};
