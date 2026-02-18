import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useStudyPlanStore } from '../stores/studyPlanStore';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Target, Calendar, Clock, Sparkles } from 'lucide-react';

const createPlanSchema = z.object({
    exam_type: z.string().min(2, 'Learning goal or topic is required'),
    target_date: z.string().min(1, 'Target completion date is required'),
    daily_hours: z.number().min(1).max(24),
    fast_learn: z.boolean().default(false),
});

type CreatePlanFormData = z.infer<typeof createPlanSchema>;

export const CreateStudyPlanPage: React.FC = () => {
    const navigate = useNavigate();
    const { createPlan } = useStudyPlanStore();

    const {
        register,
        handleSubmit,
        watch,
        formState: { errors },
    } = useForm<CreatePlanFormData>({
        resolver: zodResolver(createPlanSchema),
        defaultValues: {
            daily_hours: 4,
            fast_learn: false,
        }
    });

    const isFastLearn = watch('fast_learn');

    // Use isCreating for the local state of this operation
    const isCreatingLocal = useStudyPlanStore(state => state.isCreating);

    const onSubmit = async (data: CreatePlanFormData) => {
        try {
            const response = await createPlan({
                ...data,
                current_knowledge: {},
            });
            // response.study_plan is the new plan object
            if (response.study_plan?.id) {
                navigate(`/study-plans/${response.study_plan.id}`);
            } else {
                navigate('/dashboard');
            }
        } catch (error) {
            // Error handled by store
        }
    };

    return (
        <div className="max-w-2xl mx-auto py-8 px-4">
            <div className="flex items-center gap-3 mb-8">
                <div className="p-3 bg-primary/10 rounded-xl">
                    <Sparkles className="h-8 w-8 text-primary" />
                </div>
                <div>
                    <h1 className="text-3xl font-bold">Create Study Plan</h1>
                    <p className="text-muted-foreground">Our AI will generate a personalized learning path for you</p>
                </div>
            </div>

            <Card className="border-2 border-primary/20 shadow-xl">
                <CardHeader>
                    <CardTitle>Plan Details</CardTitle>
                    <CardDescription>Tell us about your goal and schedule</CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                        <div className="space-y-4">
                            <Input
                                label="What do you want to learn?"
                                placeholder="e.g. Machine Learning, LangChain, UPSC, GATE CS, React"
                                icon={<Target className="h-4 w-4" />}
                                error={errors.exam_type?.message}
                                {...register('exam_type')}
                            />

                            <Input
                                label="Target completion date"
                                type="date"
                                icon={<Calendar className="h-4 w-4" />}
                                error={errors.target_date?.message}
                                {...register('target_date')}
                            />

                            <Input
                                label="How many hours can you study daily?"
                                type="number"
                                min="1"
                                max="24"
                                icon={<Clock className="h-4 w-4" />}
                                error={errors.daily_hours?.message}
                                {...register('daily_hours', { valueAsNumber: true })}
                            />

                            <div className={`p-4 rounded-xl border-2 transition-all cursor-pointer ${isFastLearn ? 'border-primary bg-primary/5 shadow-md ring-1 ring-primary/20' : 'border-border bg-card hover:bg-muted/50'}`}>
                                <label className="flex items-start gap-3 cursor-pointer">
                                    <div className="flex items-center h-5 mt-1">
                                        <input
                                            type="checkbox"
                                            className="h-5 w-5 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer"
                                            {...register('fast_learn')}
                                        />
                                    </div>
                                    <div className="flex flex-col">
                                        <div className="flex items-center gap-2">
                                            <span className="font-black text-sm uppercase tracking-tight">Fast Learn Mode 🚀</span>
                                            {isFastLearn && <span className="text-[10px] font-bold bg-primary text-primary-foreground px-2 py-0.5 rounded-full uppercase">Enabled</span>}
                                        </div>
                                        <p className="text-xs text-muted-foreground font-medium mt-1">
                                            Focus on core and foundational topics first. Skip optional or advanced content to cover essentials in less time. Ideal when you have a deadline or want a quick overview.
                                        </p>
                                    </div>
                                </label>
                            </div>
                        </div>

                        <div className="p-4 bg-muted/50 rounded-lg border border-border">
                            <h4 className="font-semibold flex items-center gap-2 mb-2">
                                <Sparkles className="h-4 w-4 text-primary" />
                                {isFastLearn ? 'Fast Learn Optimization' : 'AI Engine Features'}
                            </h4>
                            <ul className="text-sm space-y-2 text-muted-foreground">
                                {isFastLearn ? (
                                    <>
                                        <li>• Core-first topic prioritization</li>
                                        <li>• Compressed timeline for quick coverage</li>
                                        <li>• Focus on must-know concepts before advanced topics</li>
                                        <li>• Smart resource discovery for essential topics</li>
                                    </>
                                ) : (
                                    <>
                                        <li>• Personalized topic breakdown and learning path</li>
                                        <li>• Smart resource discovery (videos, notes, articles)</li>
                                        <li>• Adaptive scheduling based on your daily hours</li>
                                        <li>• Integrated progress tracking and gap analysis</li>
                                    </>
                                )}
                            </ul>
                        </div>

                        <Button type="submit" className="w-full h-12 text-lg" isLoading={isCreatingLocal}>
                            {isFastLearn ? 'Generate Fast Plan ⚡' : 'Generate My Plan 🚀'}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
};
