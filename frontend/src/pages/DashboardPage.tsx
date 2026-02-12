import React from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useStudyPlanStore } from '../stores/studyPlanStore';
import { Loading } from '../components/ui/Loading';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { BookOpen, Brain, MessageSquare, TrendingUp, Clock, Target, Award, Flame } from 'lucide-react';
import { analyticsService } from '../api/services';
import type { DashboardStats } from '../types';

export const DashboardPage: React.FC = () => {
    const { user } = useAuthStore();
    const { plans, isLoading, fetchPlans } = useStudyPlanStore();
    const [stats, setStats] = React.useState<DashboardStats | null>(null);
    const [statsLoading, setStatsLoading] = React.useState(true);

    React.useEffect(() => {
        fetchPlans();
    }, []);

    React.useEffect(() => {
        let cancelled = false;
        setStatsLoading(true);
        analyticsService
            .getStats()
            .then((res) => {
                if (!cancelled) setStats(res.data);
            })
            .catch(() => {
                if (!cancelled) setStats(null);
            })
            .finally(() => {
                if (!cancelled) setStatsLoading(false);
            });
        return () => {
            cancelled = true;
        };
    }, []);

    if (isLoading && plans.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px]">
                <Loading size="lg" text="Loading dashboard..." />
            </div>
        );
    }

    const activePlan = plans.find((p) => p.status === 'active');

    const statRows = [
        {
            name: 'Study Streak',
            value: statsLoading ? '…' : `${stats?.study_streak_days ?? 0} days`,
            icon: Flame,
            color: 'text-orange-500',
        },
        {
            name: 'Hours Studied',
            value: statsLoading ? '…' : `${stats?.hours_studied ?? 0}h`,
            icon: Clock,
            color: 'text-blue-500',
        },
        {
            name: 'Topics Completed',
            value: statsLoading ? '…' : `${stats?.topics_completed ?? 0}/${stats?.topics_total ?? 0}`,
            icon: Target,
            color: 'text-green-500',
        },
        {
            name: 'Quiz Average',
            value:
                statsLoading
                    ? '…'
                    : stats?.quiz_average_percent != null
                      ? `${Math.round(stats.quiz_average_percent)}%`
                      : '—',
            icon: Award,
            color: 'text-purple-500',
        },
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
                <h1 className="text-3xl font-bold">
                    {!statsLoading && stats && (stats.study_streak_days > 0 || stats.hours_studied > 0 || stats.topics_completed > 0 || (stats.quiz_average_percent != null))
                        ? `Welcome back, ${user?.full_name || 'Student'}! 👋`
                        : `Welcome, ${user?.full_name || 'Student'}! 👋`}
                </h1>
                <p className="text-muted-foreground mt-2">
                    {!statsLoading && stats && (stats.study_streak_days > 0 || stats.hours_studied > 0 || stats.topics_completed > 0 || (stats.quiz_average_percent != null))
                        ? "Here's your learning progress and what's next"
                        : "Create a study plan, start learning in Chat, or take a quiz to see your stats here."}
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {statRows.map((stat) => (
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

            {/* Today's Schedule / Next up */}
            <Card>
                <CardHeader>
                    <CardTitle>Today's Schedule</CardTitle>
                    <CardDescription>Your planned activities and what's next</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-3">
                        {activePlan?.chapters?.length ? (
                            (() => {
                                const next = activePlan.chapters.find(
                                    (ch) => ch.status === 'in_progress' || ch.status === 'pending'
                                );
                                if (next) {
                                    return (
                                        <div className="flex items-center justify-between p-3 bg-accent rounded-lg">
                                            <div className="flex items-center gap-3">
                                                <Clock className="h-4 w-4 text-muted-foreground" />
                                                <div>
                                                    <p className="font-medium">
                                                        Next: {next.chapter_name}
                                                        {next.subject ? ` (${next.subject})` : ''}
                                                    </p>
                                                    <p className="text-sm text-muted-foreground">
                                                        {next.status === 'in_progress' ? 'In progress' : 'Pending'} • ~{next.estimated_hours}h
                                                    </p>
                                                </div>
                                            </div>
                                            <Link to={`/study-plans/${activePlan.id}`}>
                                                <Button variant="outline" size="sm">Open plan</Button>
                                            </Link>
                                        </div>
                                    );
                                }
                                return (
                                    <p className="text-muted-foreground py-2">
                                        All chapters in your active plan are completed. Great job! Create a new plan or take a quiz.
                                    </p>
                                );
                            })()
                        ) : (
                            <p className="text-muted-foreground py-2">
                                No scheduled activities yet. Create a study plan or start learning from Chat.
                            </p>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};
