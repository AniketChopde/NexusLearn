import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useStudyPlanStore } from '../stores/studyPlanStore';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Loading } from '../components/ui/Loading';
import {
    Calendar, Clock, BookOpen, CheckCircle2,
    Layout, Sparkles,
    BookMarked, Video, FileText,
    ArrowLeft, GraduationCap, ChevronRight,
    PlayCircle,
    Download, ListChecks, Target as GoalIcon,
    AlertTriangle, Lightbulb
} from 'lucide-react';
import { format } from 'date-fns';
import { Mermaid } from '../components/ui/Mermaid';
import { TopicMindmap } from '../components/TopicMindmap';

export const StudyPlanDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { activePlan, isLoading, isTeaching, getPlan, updateChapterStatus, teachChapter } = useStudyPlanStore();
    const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<'overview' | 'lesson' | 'syllabus'>('overview');
    const [expandedMindmaps, setExpandedMindmaps] = useState<Record<string, boolean>>({});

    useEffect(() => {
        if (id) {
            getPlan(id);
        }
    }, [id, getPlan]);

    useEffect(() => {
        if (activePlan?.chapters && activePlan.chapters.length > 0 && !selectedChapterId) {
            setSelectedChapterId(activePlan.chapters[0].id.toString());
        }
    }, [activePlan, selectedChapterId]);

    const selectedChapter = activePlan?.chapters.find(
        (c) => c.id.toString() === selectedChapterId
    );

    const handleStartLesson = async () => {
        if (!selectedChapter) return;

        if (!selectedChapter.content || !selectedChapter.content.topic_lessons) {
            await teachChapter(selectedChapter.id.toString());
        }
        setViewMode('lesson');
    };

    const handleDownload = () => {
        if (!activePlan) return;
        const planData = JSON.stringify(activePlan, null, 2);
        const blob = new Blob([planData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${activePlan.exam_type}_study_plan.json`;
        a.click();
        URL.revokeObjectURL(url);
    };

    if (isLoading && !activePlan) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px]">
                <Loading size="lg" text="Loading study plan details..." />
            </div>
        );
    }

    if (!activePlan) {
        return (
            <div className="text-center py-12">
                <h2 className="text-2xl font-bold mb-4">Study Plan Not Found</h2>
                <Button onClick={() => navigate('/study-plans')}>Back to All Plans</Button>
            </div>
        );
    }

    const completedChapters = activePlan.chapters.filter((c) => c.status === 'completed').length;
    const progress = Math.round((completedChapters / activePlan.chapters.length) * 100) || 0;

    return (
        <div className="space-y-8 animate-in fade-in duration-700 pb-20">
            {/* Header section */}
            <div className="relative overflow-hidden rounded-3xl bg-primary/5 border border-primary/10 p-8 md:p-12">
                <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
                    <Sparkles className="h-32 w-32 text-primary" />
                </div>

                <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                    <div className="space-y-2">
                        <div className="flex items-center gap-2">
                            <span className="bg-primary/20 text-primary text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-widest">
                                {activePlan.exam_type}
                            </span>
                        </div>
                        <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                            {activePlan.exam_type} Preparation
                        </h1>
                        <div className="flex flex-wrap items-center gap-6 text-muted-foreground font-medium">
                            <div className="flex items-center gap-2">
                                <Calendar className="h-4 w-4" />
                                <span className="text-sm">Target: {format(new Date(activePlan.target_date), 'MMM d, yyyy')}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Clock className="h-4 w-4" />
                                <span className="text-sm">{activePlan.daily_hours}h daily focus</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-col items-end gap-4 w-full md:w-auto">
                        <Button
                            variant="outline"
                            size="sm"
                            className="rounded-full border-primary/20 hover:bg-primary/5 h-10 px-6 font-bold flex items-center gap-2"
                            onClick={handleDownload}
                        >
                            <Download size={16} />
                            Download Plan
                        </Button>
                        <div className="w-full md:w-64 space-y-2">
                            <div className="flex justify-between mb-1">
                                <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Growth Progress</span>
                                <span className="text-xs font-black text-primary">{progress}%</span>
                            </div>
                            <div className="w-full h-2 bg-primary/10 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-primary transition-all duration-1000 ease-out"
                                    style={{ width: `${progress}%` }}
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Chapter List (Sidebar) */}
                <div className="lg:col-span-4 space-y-4">
                    <div className="flex flex-col space-y-4">
                        <div className="flex p-1.5 bg-muted/50 rounded-2xl border border-border/50">
                            <button
                                onClick={() => setViewMode('overview')}
                                className={`flex-1 flex items-center justify-center py-2.5 rounded-xl text-xs font-bold transition-all ${viewMode === 'overview' || viewMode === 'lesson' ? 'bg-background shadow-sm text-primary' : 'text-muted-foreground hover:bg-muted'}`}
                            >
                                <Layout className="h-3.5 w-3.5 mr-2" />
                                Planning
                            </button>
                            <button
                                onClick={() => setViewMode('syllabus')}
                                className={`flex-1 flex items-center justify-center py-2.5 rounded-xl text-xs font-bold transition-all ${viewMode === 'syllabus' ? 'bg-background shadow-sm text-primary' : 'text-muted-foreground hover:bg-muted'}`}
                            >
                                <ListChecks className="h-3.5 w-3.5 mr-2" />
                                Syllabus
                            </button>
                        </div>
                    </div>

                    <div className="space-y-3 max-h-[700px] overflow-y-auto pr-2 custom-scrollbar">
                        {activePlan.chapters.map((chapter, index) => (
                            <button
                                key={chapter.id.toString()}
                                onClick={() => {
                                    setSelectedChapterId(chapter.id.toString());
                                    setViewMode('overview');
                                }}
                                className={`w-full text-left p-4 rounded-2xl border transition-all duration-300 group relative ${selectedChapterId === chapter.id.toString()
                                    ? 'border-primary bg-primary/5 shadow-lg shadow-primary/5 ring-1 ring-primary/20'
                                    : 'border-transparent bg-muted/30 hover:bg-muted/50'
                                    }`}
                            >
                                <div className="flex items-start gap-3">
                                    <div className={`mt-1 h-5 w-5 rounded-full flex items-center justify-center ${chapter.status === 'completed'
                                        ? 'bg-green-500/20 text-green-500'
                                        : 'bg-muted text-muted-foreground/30'
                                        }`}>
                                        {chapter.status === 'completed' ? <CheckCircle2 className="h-3.5 w-3.5" /> : <div className="h-1.5 w-1.5 rounded-full bg-current" />}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between mb-0.5">
                                            <span className="text-[9px] font-black uppercase text-muted-foreground/60 tracking-tighter">
                                                Week {index + 1}
                                            </span>
                                            {selectedChapterId === chapter.id.toString() && (
                                                <div className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
                                            )}
                                        </div>
                                        <h4 className={`font-bold text-sm truncate leading-tight ${selectedChapterId === chapter.id.toString() ? 'text-primary' : ''}`}>
                                            {chapter.chapter_name}
                                        </h4>
                                        <p className="text-[10px] text-muted-foreground font-semibold uppercase mt-1">
                                            {chapter.subject} • {chapter.estimated_hours} Hours
                                        </p>
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Main Content Area */}
                <div className="lg:col-span-8">
                    {viewMode === 'syllabus' ? (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500 space-y-6">
                            <Card className="rounded-[2.5rem] border-none shadow-xl overflow-hidden bg-card">
                                <CardHeader className="p-8 pb-4">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="p-2.5 bg-primary/10 rounded-xl text-primary">
                                            <ListChecks size={24} />
                                        </div>
                                        <div>
                                            <CardTitle className="text-2xl font-black">Official Syllabus Overview</CardTitle>
                                            <CardDescription>Comprehensive curriculum breakdown for {activePlan.exam_type}</CardDescription>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent className="p-8 pt-4 space-y-8">
                                    {activePlan.plan_metadata?.goal_analysis && (
                                        <div className="p-6 bg-primary/5 rounded-3xl border border-primary/10">
                                            <h4 className="flex items-center gap-2 text-sm font-black uppercase tracking-wider text-primary mb-3">
                                                <GoalIcon size={16} />
                                                Goal Analysis
                                            </h4>
                                            <div className="space-y-4">
                                                {typeof activePlan.plan_metadata.goal_analysis === 'string' ? (
                                                    <p className="text-sm leading-relaxed text-muted-foreground/80 font-medium">
                                                        {activePlan.plan_metadata.goal_analysis}
                                                    </p>
                                                ) : (
                                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                        <div className="p-4 bg-background/50 rounded-2xl border border-border/50 shadow-sm">
                                                            <p className="text-[10px] font-black text-primary/60 uppercase tracking-widest mb-1">Feasibility</p>
                                                            <div className="flex items-center gap-2">
                                                                <div className={`h-2 w-2 rounded-full ${activePlan.plan_metadata.goal_analysis.feasibility === 'high' ? 'bg-green-500' :
                                                                    activePlan.plan_metadata.goal_analysis.feasibility === 'medium' ? 'bg-yellow-500' : 'bg-red-500'
                                                                    }`} />
                                                                <p className="text-sm font-black capitalize">{activePlan.plan_metadata.goal_analysis.feasibility}</p>
                                                            </div>
                                                        </div>
                                                        <div className="p-4 bg-background/50 rounded-2xl border border-border/50 shadow-sm">
                                                            <p className="text-[10px] font-black text-primary/60 uppercase tracking-widest mb-1">Approach</p>
                                                            <p className="text-sm font-black capitalize">{activePlan.plan_metadata.goal_analysis.recommended_approach}</p>
                                                        </div>
                                                        <div className="p-4 bg-background/50 rounded-2xl border border-border/50 shadow-sm">
                                                            <p className="text-[10px] font-black text-primary/60 uppercase tracking-widest mb-1">Est. Coverage</p>
                                                            <p className="text-sm font-black">{activePlan.plan_metadata.goal_analysis.estimated_coverage}</p>
                                                        </div>

                                                        {activePlan.plan_metadata.goal_analysis.key_focus_areas && (
                                                            <div className="col-span-1 md:col-span-3 p-5 bg-background/50 rounded-2xl border border-border/50 shadow-sm">
                                                                <p className="text-[10px] font-black text-primary/60 uppercase tracking-widest mb-3">Key Focus Areas</p>
                                                                <div className="flex flex-wrap gap-2">
                                                                    {activePlan.plan_metadata.goal_analysis.key_focus_areas.map((area: string, i: number) => (
                                                                        <span key={i} className="px-3 py-1 bg-primary/10 text-primary text-[10px] font-black rounded-lg uppercase border border-primary/20">
                                                                            {area}
                                                                        </span>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        )}

                                                        {activePlan.plan_metadata.goal_analysis.recommendations && (
                                                            <div className="col-span-1 md:col-span-3 p-5 bg-background/50 rounded-2xl border border-border/50 shadow-sm">
                                                                <p className="text-[10px] font-black text-primary/60 uppercase tracking-widest mb-2">Key Recommendations</p>
                                                                <ul className="space-y-1.5">
                                                                    {activePlan.plan_metadata.goal_analysis.recommendations.map((rec: string, i: number) => (
                                                                        <li key={i} className="text-xs font-bold text-muted-foreground flex items-start gap-2">
                                                                            <span className="mt-1.5 h-1 w-1 rounded-full bg-primary/40 shrink-0" />
                                                                            {rec}
                                                                        </li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    <div className="space-y-6">
                                        {(activePlan.plan_metadata?.official_syllabus?.exam_pattern || activePlan.plan_metadata?.official_syllabus?.pattern) && (
                                            <div className="space-y-4">
                                                <h4 className="text-sm font-black uppercase tracking-widest text-muted-foreground px-2">Exam Pattern</h4>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    {Object.entries(activePlan.plan_metadata.official_syllabus.exam_pattern || activePlan.plan_metadata.official_syllabus.pattern).map(([key, val]: any, i) => (
                                                        <div key={i} className="p-4 bg-muted/30 rounded-2xl border border-border/50">
                                                            <p className="text-[10px] font-bold text-muted-foreground uppercase mb-1">{key.replace(/_/g, ' ')}</p>
                                                            <p className="text-sm font-black">{Array.isArray(val) ? val.join(', ') : String(val)}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {(activePlan.plan_metadata?.official_syllabus?.syllabus_overview || activePlan.plan_metadata?.official_syllabus?.syllabus) && (
                                            <div className="space-y-4 pt-4">
                                                <h4 className="text-sm font-black uppercase tracking-widest text-muted-foreground px-2">Curriculum Topics</h4>
                                                <div className="space-y-3">
                                                    {/* Handle syllabus_overview.topics_per_subject structure */}
                                                    {activePlan.plan_metadata.official_syllabus.syllabus_overview?.topics_per_subject ? (
                                                        Object.entries(activePlan.plan_metadata.official_syllabus.syllabus_overview.topics_per_subject).map(([subject, topics]: any, i: number) => (
                                                            <div key={i} className="p-5 bg-muted/20 rounded-2xl border border-border/40 hover:bg-muted/30 transition-colors">
                                                                <h5 className="font-bold text-base mb-3 flex items-center gap-2">
                                                                    <span className="h-6 w-6 bg-primary/10 text-primary text-[10px] rounded-lg flex items-center justify-center">{i + 1}</span>
                                                                    {subject}
                                                                </h5>
                                                                <ul className="grid grid-cols-1 md:grid-cols-2 gap-y-2 gap-x-6">
                                                                    {(Array.isArray(topics) ? topics : []).map((topic: string, j: number) => (
                                                                        <li key={j} className="text-sm text-muted-foreground flex items-center gap-2">
                                                                            <div className="h-1 w-1 rounded-full bg-primary/40" />
                                                                            {topic}
                                                                        </li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        ))
                                                    ) : (
                                                        /* Fallback for simple syllabus array */
                                                        (activePlan.plan_metadata.official_syllabus.syllabus || []).map((section: any, i: number) => (
                                                            <div key={i} className="p-5 bg-muted/20 rounded-2xl border border-border/40 hover:bg-muted/30 transition-colors">
                                                                <h5 className="font-bold text-base mb-3 flex items-center gap-2">
                                                                    <span className="h-6 w-6 bg-primary/10 text-primary text-[10px] rounded-lg flex items-center justify-center">{i + 1}</span>
                                                                    {section.category || section.name || "Topic"}
                                                                </h5>
                                                                <ul className="grid grid-cols-1 md:grid-cols-2 gap-y-2 gap-x-6">
                                                                    {(section.topics || []).map((topic: string, j: number) => (
                                                                        <li key={j} className="text-sm text-muted-foreground flex items-center gap-2">
                                                                            <div className="h-1 w-1 rounded-full bg-primary/40" />
                                                                            {topic}
                                                                        </li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        ))
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    ) : selectedChapter ? (
                        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
                            {viewMode === 'overview' ? (
                                <Card className="border-none shadow-2xl bg-card rounded-[2rem] overflow-hidden">
                                    <div className="p-8 pb-0">
                                        <div className="flex flex-col md:flex-row justify-between items-start gap-4">
                                            <div>
                                                <h2 className="text-3xl font-black">{selectedChapter.chapter_name}</h2>
                                                <p className="text-primary font-bold uppercase text-xs tracking-widest mt-1">
                                                    Focus: {selectedChapter.subject}
                                                </p>
                                            </div>
                                            <Button
                                                onClick={handleStartLesson}
                                                isLoading={isTeaching}
                                                className="rounded-full px-8 bg-primary hover:bg-primary/90 text-primary-foreground font-bold shadow-lg shadow-primary/20 h-12"
                                            >
                                                <GraduationCap className="mr-2 h-5 w-5" />
                                                Start Deep Lesson
                                            </Button>
                                        </div>
                                    </div>

                                    <CardContent className="p-8 pt-6 space-y-10">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                            <div className="space-y-4">
                                                <h4 className="text-xs font-black uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                                                    <BookMarked className="h-4 w-4 text-primary" />
                                                    Exam Topics
                                                </h4>
                                                <div className="space-y-2">
                                                    {selectedChapter.topics.map((topic, i) => (
                                                        <div key={i} className="flex items-center gap-3 p-3.5 bg-muted/30 rounded-2xl border border-transparent hover:border-primary/20 transition-all">
                                                            <span className="text-xs font-bold text-primary/40">0{i + 1}</span>
                                                            <span className="text-sm font-semibold">{topic}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>

                                            <div className="space-y-4">
                                                <h4 className="text-xs font-black uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                                                    <PlayCircle className="h-4 w-4 text-primary" />
                                                    Hand-picked Resources
                                                </h4>
                                                <div className="space-y-3">
                                                    {selectedChapter.resources?.map((res, i) => (
                                                        <a key={i} href={res.url} target="_blank" rel="noopener noreferrer" className="flex items-center justify-between p-3.5 bg-muted/50 rounded-2xl hover:bg-primary/5 border border-transparent hover:border-primary/10 transition-all group">
                                                            <div className="flex items-center gap-3">
                                                                <div className="h-8 w-8 bg-background rounded-xl flex items-center justify-center text-primary shadow-sm">
                                                                    {res.type === 'video' ? <Video size={16} /> : <FileText size={16} />}
                                                                </div>
                                                                <span className="text-xs font-bold line-clamp-1 group-hover:text-primary transition-colors">{res.title}</span>
                                                            </div>
                                                            <ChevronRight size={14} className="text-muted-foreground" />
                                                        </a>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="pt-6 border-t border-border flex flex-col md:flex-row gap-4">
                                            <Button
                                                variant={selectedChapter.status === 'completed' ? 'outline' : 'default'}
                                                className="flex-1 rounded-2xl h-14 text-sm font-black uppercase tracking-widest"
                                                onClick={() => updateChapterStatus(selectedChapter.id.toString(), selectedChapter.status === 'completed' ? 'pending' : 'completed')}
                                            >
                                                {selectedChapter.status === 'completed' ? 'Completed 🎉' : 'Mark as Complete'}
                                            </Button>
                                            <Button
                                                variant="secondary"
                                                className="px-8 rounded-2xl h-14 text-sm font-black uppercase tracking-widest"
                                                onClick={() => navigate(`/quiz?topic=${encodeURIComponent(selectedChapter.chapter_name)}&subject=${encodeURIComponent(selectedChapter.subject)}&chapterId=${selectedChapter.id.toString()}&examType=${encodeURIComponent(activePlan.exam_type)}`)}
                                            >
                                                Knowledge Check
                                            </Button>
                                        </div>
                                    </CardContent>
                                </Card>
                            ) : (
                                <div className="space-y-6">
                                    <div className="flex items-center justify-between">
                                        <button
                                            onClick={() => setViewMode('overview')}
                                            className="flex items-center gap-2 text-sm font-bold text-muted-foreground hover:text-primary"
                                        >
                                            <ArrowLeft size={16} />
                                            Back to Focus Areas
                                        </button>
                                        <div className="flex items-center gap-2 text-xs font-bold text-primary bg-primary/10 px-3 py-1 rounded-full border border-primary/20">
                                            <Sparkles size={12} />
                                            Deep Teaching Mode
                                        </div>
                                    </div>

                                    {selectedChapter.content ? (
                                        <Card className="border-none shadow-2xl bg-card rounded-[2.5rem] overflow-hidden">
                                            <div className="p-8 md:p-12 space-y-12">
                                                <div className="space-y-4">
                                                    <h2 className="text-4xl font-black tracking-tight">{selectedChapter.chapter_name}</h2>
                                                    <p className="text-lg text-muted-foreground font-medium leading-relaxed italic border-l-4 border-primary/20 pl-6">
                                                        {selectedChapter.content.overview}
                                                    </p>
                                                </div>

                                                <div className="space-y-16">
                                                    {selectedChapter.content.topic_lessons.map((lesson: any, i: number) => (
                                                        <div key={i} className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500" style={{ animationDelay: `${i * 100}ms` }}>
                                                            <div className="flex items-center justify-between">
                                                                <div className="flex items-center gap-3">
                                                                    <span className="px-3 py-1 bg-primary/10 text-primary text-[10px] font-black rounded-lg uppercase">Concept 0{i + 1}</span>
                                                                    <h3 className="text-3xl font-black tracking-tight">{lesson.topic}</h3>
                                                                </div>
                                                                <Button
                                                                    variant="outline"
                                                                    size="sm"
                                                                    className="rounded-full"
                                                                    onClick={() => {
                                                                        const moduleId = `${selectedChapter.id.toString()}_${String(lesson.topic || '').replace(/ /g, '_')}`;
                                                                        navigate(
                                                                            `/chat?moduleId=${encodeURIComponent(moduleId)}&planId=${encodeURIComponent(id || '')}` +
                                                                            `&examType=${encodeURIComponent(activePlan.exam_type)}` +
                                                                            `&chapter=${encodeURIComponent(selectedChapter.chapter_name)}` +
                                                                            `&topic=${encodeURIComponent(String(lesson.topic || ''))}`
                                                                        );
                                                                    }}
                                                                >
                                                                    Ask in Chat
                                                                </Button>
                                                                {lesson.citation && (
                                                                    <div className="flex items-center gap-1.5 px-3 py-1 bg-muted rounded-full border border-border">
                                                                        <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Source: {lesson.citation}</span>
                                                                    </div>
                                                                )}
                                                            </div>

                                                            <div className="prose prose-slate dark:prose-invert max-w-none">
                                                                <p className="text-lg leading-relaxed text-foreground font-medium opacity-90">{lesson.introduction}</p>
                                                                <div className="my-6 p-8 bg-muted/30 rounded-[2rem] border border-border/50">
                                                                    <h4 className="text-[10px] font-black uppercase text-primary mb-4 tracking-widest">Grounded Explanation</h4>
                                                                    <div className="text-base leading-loose whitespace-pre-wrap">{lesson.main_explanation}</div>
                                                                </div>
                                                            </div>

                                                            {(lesson.mermaid_diagram || lesson.visual_description || lesson.visuals) && (
                                                                <div className="space-y-4">
                                                                    <div className="flex items-center gap-2 mb-2">
                                                                        <div className="p-1.5 bg-primary/10 rounded-lg text-primary">
                                                                            <GoalIcon size={14} />
                                                                        </div>
                                                                        <h4 className="text-[10px] font-black uppercase text-primary tracking-widest">Visual Study Guide</h4>
                                                                    </div>

                                                                    {lesson.mermaid_diagram && (
                                                                        <div className="bg-muted/10 rounded-[2rem] border border-border/50 p-6 shadow-inner">
                                                                            <Mermaid chart={lesson.mermaid_diagram} />
                                                                        </div>
                                                                    )}

                                                                    {(lesson.visual_description || (lesson.visuals && lesson.visuals[0]?.description)) && (
                                                                        <div className="p-6 bg-primary/5 rounded-2xl border border-primary/10 flex items-start gap-4 transition-all hover:bg-primary/[0.07]">
                                                                            <div className="flex-1">
                                                                                <p className="text-sm font-medium text-muted-foreground leading-relaxed italic">
                                                                                    {lesson.visual_description || (lesson.visuals && lesson.visuals[0]?.description)}
                                                                                </p>
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            )}

                                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                                {lesson.key_points?.map((point: string, k: number) => (
                                                                    <div key={k} className="p-5 bg-card rounded-2xl border border-border flex items-start gap-3">
                                                                        <CheckCircle2 size={16} className="text-green-500 mt-0.5 shrink-0" />
                                                                        <span className="text-sm font-bold text-foreground/80 leading-snug">{point}</span>
                                                                    </div>
                                                                ))}
                                                            </div>

                                                            {/* Common Mistakes & Exam Tips */}
                                                            {(lesson.common_mistakes?.length > 0 || lesson.exam_tips?.length > 0) && (
                                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                                    {lesson.common_mistakes?.length > 0 && (
                                                                        <div className="p-6 bg-red-500/5 rounded-[2rem] border border-red-500/10 space-y-4">
                                                                            <div className="flex items-center gap-2 text-red-600">
                                                                                <AlertTriangle size={18} />
                                                                                <h4 className="text-[10px] font-black uppercase tracking-widest">Common Pitfalls</h4>
                                                                            </div>
                                                                            <ul className="space-y-3">
                                                                                {lesson.common_mistakes.map((mistake: string, mI: number) => (
                                                                                    <li key={mI} className="text-xs font-bold text-muted-foreground flex items-start gap-2">
                                                                                        <span className="mt-1.5 h-1 w-1 rounded-full bg-red-400 shrink-0" />
                                                                                        {mistake}
                                                                                    </li>
                                                                                ))}
                                                                            </ul>
                                                                        </div>
                                                                    )}
                                                                    {lesson.exam_tips?.length > 0 && (
                                                                        <div className="p-6 bg-amber-500/5 rounded-[2rem] border border-amber-500/10 space-y-4">
                                                                            <div className="flex items-center gap-2 text-amber-600">
                                                                                <Lightbulb size={18} />
                                                                                <h4 className="text-[10px] font-black uppercase tracking-widest">Exam Strategies</h4>
                                                                            </div>
                                                                            <ul className="space-y-3">
                                                                                {lesson.exam_tips.map((tip: string, tI: number) => (
                                                                                    <li key={tI} className="text-xs font-bold text-muted-foreground flex items-start gap-2">
                                                                                        <span className="mt-1.5 h-1 w-1 rounded-full bg-amber-400 shrink-0" />
                                                                                        {tip}
                                                                                    </li>
                                                                                ))}
                                                                            </ul>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            )}

                                                            {lesson.examples?.map((ex: any, exI: number) => (
                                                                <div key={exI} className="bg-slate-900 rounded-[2rem] overflow-hidden shadow-xl border border-white/5">
                                                                    <div className="px-6 py-4 bg-slate-800/50 flex items-center justify-between border-b border-white/5">
                                                                        <span className="text-[10px] font-bold text-slate-300 uppercase tracking-widest">{ex.title}</span>
                                                                    </div>
                                                                    <div className="p-8 space-y-4">
                                                                        <p className="text-slate-400 text-sm leading-relaxed">{ex.description}</p>
                                                                        {ex.code && (
                                                                            <pre className="p-6 bg-black/40 rounded-2xl border border-white/5 overflow-x-auto">
                                                                                <code className="text-green-400 text-xs font-mono">{ex.code}</code>
                                                                            </pre>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            ))}

                                                            {/* Mindmap (collapsed by default) */}
                                                            <div className="pt-2">
                                                                <div className="flex items-center justify-between">
                                                                    <h4 className="text-[10px] font-black uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                                                                        Mindmap
                                                                        <span className="text-[8px] bg-primary/10 text-primary px-1.5 py-0.5 rounded uppercase">RAG-Powered</span>
                                                                    </h4>
                                                                    <Button
                                                                        variant="outline"
                                                                        size="sm"
                                                                        className="rounded-full"
                                                                        onClick={() => {
                                                                            const key = String(lesson.topic || i);
                                                                            setExpandedMindmaps((prev) => ({
                                                                                ...prev,
                                                                                [key]: !prev[key],
                                                                            }));
                                                                        }}
                                                                    >
                                                                        {expandedMindmaps[String(lesson.topic || i)] ? 'Collapse' : 'Expand'}
                                                                    </Button>
                                                                </div>

                                                                {expandedMindmaps[String(lesson.topic || i)] && (
                                                                    <div className="mt-4 h-[420px] bg-muted/20 rounded-[2rem] border border-border/50 overflow-hidden">
                                                                        <TopicMindmap
                                                                            topicId={`${selectedChapter.id.toString()}_${String(lesson.topic || '').replace(/ /g, '_')}`}
                                                                        />
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>

                                                <div className="pt-12 border-t flex flex-col items-center gap-6">
                                                    <div className="text-center space-y-2">
                                                        <h4 className="text-xl font-black italic">Ready to verify?</h4>
                                                        <p className="text-sm text-muted-foreground font-medium">Take a quick quiz to cement these concepts.</p>
                                                    </div>
                                                    <Button
                                                        onClick={() => navigate(`/quiz?topic=${encodeURIComponent(selectedChapter.chapter_name)}&subject=${encodeURIComponent(selectedChapter.subject)}&chapterId=${selectedChapter.id.toString()}&examType=${encodeURIComponent(activePlan.exam_type)}&autoStart=true`)}
                                                        className="h-16 px-12 rounded-full text-lg font-black uppercase tracking-widest shadow-2xl shadow-primary/20"
                                                    >
                                                        Take Knowledge Check 🚀
                                                    </Button>
                                                </div>
                                            </div>
                                        </Card>
                                    ) : (
                                        <div className="h-96 flex flex-col items-center justify-center space-y-4">
                                            <Loading size="lg" text="Synthesizing deep knowledge..." />
                                            <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest animate-pulse">Generating diagrams • Building examples • Mapping path</p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="h-full min-h-[500px] flex flex-col items-center justify-center border-4 border-dashed border-muted rounded-[3rem] p-12 text-center bg-muted/5 transition-all hover:bg-muted/10">
                            <div className="max-w-xs space-y-4">
                                <div className="h-20 w-20 bg-muted/20 rounded-full flex items-center justify-center mx-auto mb-2">
                                    <BookOpen className="h-10 w-10 text-muted-foreground opacity-30" />
                                </div>
                                <h3 className="text-2xl font-black opacity-40 uppercase tracking-tighter">Your Journey Starts Here</h3>
                                <p className="text-sm font-bold text-muted-foreground/40 leading-relaxed uppercase tracking-tighter">
                                    Select a chapter from the left to unlock deep AI teaching and adaptive quizzes.
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
