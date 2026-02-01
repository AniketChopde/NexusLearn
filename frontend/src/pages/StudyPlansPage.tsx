import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStudyPlanStore } from '../stores/studyPlanStore';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Loading } from '../components/ui/Loading';
import { Plus, Calendar, Clock, BookOpen, ChevronRight, Trash2 } from 'lucide-react';
import { format } from 'date-fns';

export const StudyPlansPage: React.FC = () => {
    const navigate = useNavigate();
    const { plans, isLoading, fetchPlans, deletePlan } = useStudyPlanStore();

    useEffect(() => {
        fetchPlans();
    }, [fetchPlans]);

    const handleDelete = async (e: React.MouseEvent, id: string) => {
        e.stopPropagation();
        if (window.confirm('Are you sure you want to delete this study plan?')) {
            await deletePlan(id);
        }
    };

    if (isLoading && plans.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px]">
                <Loading size="lg" text="Fetching your study plans..." />
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Your Study Plans</h1>
                    <p className="text-muted-foreground mt-1">
                        Manage and track your preparation for various exams
                    </p>
                </div>
                <Button
                    onClick={() => navigate('/study-plans/create')}
                    className="group transition-all duration-300 hover:shadow-lg active:scale-95"
                >
                    <Plus className="h-5 w-5 mr-2 group-hover:rotate-90 transition-transform duration-300" />
                    New Study Plan
                </Button>
            </div>

            {plans.length === 0 ? (
                <Card className="border-dashed border-2 bg-muted/30 py-12">
                    <CardContent className="flex flex-col items-center text-center">
                        <div className="p-4 bg-primary/10 rounded-full mb-4">
                            <BookOpen className="h-10 w-10 text-primary" />
                        </div>
                        <h3 className="text-xl font-semibold mb-2">No active plans yet</h3>
                        <p className="text-muted-foreground max-w-sm mb-8">
                            Create your first AI-powered study plan to start your learning journey with personalized topic breakdowns.
                        </p>
                        <Button variant="outline" onClick={() => navigate('/study-plans/create')}>
                            Get Started
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {plans.map((plan) => (
                        <Card
                            key={plan.id}
                            className="group relative cursor-pointer hover:border-primary/40 hover:shadow-xl transition-all duration-300 overflow-hidden"
                            onClick={() => navigate(`/study-plans/${plan.id}`)}
                        >
                            <div className="absolute top-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 text-destructive hover:bg-destructive/10"
                                    onClick={(e) => handleDelete(e, plan.id.toString())}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>

                            <CardHeader>
                                <div className="flex justify-between items-start mb-2">
                                    <div className="bg-primary/10 text-primary px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider">
                                        {plan.exam_type}
                                    </div>
                                    <div className={`px-2 py-1 rounded text-[10px] font-bold uppercase transition-colors ${plan.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                                        }`}>
                                        {plan.status}
                                    </div>
                                </div>
                                <CardTitle className="line-clamp-1 group-hover:text-primary transition-colors">
                                    {plan.exam_type} Preparation
                                </CardTitle>
                                <CardDescription className="flex items-center gap-2 mt-1">
                                    <Calendar className="h-3 w-3" />
                                    Target: {format(new Date(plan.target_date), 'PPP')}
                                </CardDescription>
                            </CardHeader>

                            <CardContent>
                                <div className="grid grid-cols-2 gap-4 mb-6">
                                    <div className="flex flex-col bg-muted/50 p-3 rounded-lg border border-border/50">
                                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
                                            <Clock className="h-3 w-3" />
                                            Daily Effort
                                        </div>
                                        <div className="text-lg font-bold">{plan.daily_hours}h</div>
                                    </div>
                                    <div className="flex flex-col bg-muted/50 p-3 rounded-lg border border-border/50">
                                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
                                            <BookOpen className="h-3 w-3" />
                                            Chapters
                                        </div>
                                        <div className="text-lg font-bold">{plan.chapters?.length || 0}</div>
                                    </div>
                                </div>

                                <div className="flex items-center justify-between text-sm group-hover:translate-x-1 transition-transform">
                                    <span className="text-primary font-medium">Continue Planning</span>
                                    <ChevronRight className="h-4 w-4 text-primary" />
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
};
