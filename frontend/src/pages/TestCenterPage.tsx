import React from 'react';
import { useQuizStore } from '../stores/quizStore';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Loading } from '../components/ui/Loading';
import {
    Brain, Clock, CheckCircle, XCircle,
    ArrowRight,
    Target, Award, AlertTriangle, Play, ShieldCheck, Timer
} from 'lucide-react';
import { formatTime } from '../lib/utils';
import toast from 'react-hot-toast';

export const TestCenterPage: React.FC = () => {
    const {
        activeQuiz,
        currentQuestion,
        answers,
        results,
        timeStarted,
        startTestCenter,
        submitAnswer,
        submitQuiz,
        nextQuestion,
        previousQuestion,
        resetQuiz,
        isLoading,
    } = useQuizStore();

    const [examName, setExamName] = React.useState('');
    const [timeLeft, setTimeLeft] = React.useState<number | null>(null);

    // Initialization: If we come back and there's no active quiz, reset
    React.useEffect(() => {
        // Only reset if we are not in progress
        if (!activeQuiz && !results) {
            resetQuiz();
        }
    }, []);

    // Timer Logic
    React.useEffect(() => {
        if (activeQuiz && activeQuiz.time_limit_minutes && timeStarted && !results) {
            const totalSeconds = activeQuiz.time_limit_minutes * 60;

            const interval = setInterval(() => {
                const elapsed = Math.floor((Date.now() - timeStarted) / 1000);
                const remaining = totalSeconds - elapsed;

                if (remaining <= 0) {
                    setTimeLeft(0);
                    clearInterval(interval);
                    handleAutoSubmit();
                } else {
                    setTimeLeft(remaining);
                }
            }, 1000);

            return () => clearInterval(interval);
        }
    }, [activeQuiz, timeStarted, results]);

    const handleStartTest = async () => {
        if (!examName.trim()) {
            toast.error('Please enter an exam name');
            return;
        }
        await startTestCenter(examName);
    };

    const handleAutoSubmit = async () => {
        toast.error("Time's up! Submitting your exam automatically.");
        await submitQuiz();
    };

    const handleManualSubmit = async () => {
        if (window.confirm("Are you sure you want to submit your exam now?")) {
            await submitQuiz();
        }
    };

    const currentQ = activeQuiz?.questions[currentQuestion];
    const selectedAnswer = currentQ ? answers[currentQ.question_id] : undefined;

    // 1. Landing / Entry View
    if (!activeQuiz && !results) {
        return (
            <div className="max-w-4xl mx-auto py-12 px-4 animate-in fade-in duration-700">
                <div className="text-center mb-12 space-y-6">
                    <div className="h-24 w-24 bg-primary/10 rounded-3xl flex items-center justify-center mx-auto mb-6 transform rotate-3 shadow-inner">
                        < ShieldCheck className="h-12 w-12 text-primary" />
                    </div>
                    <h1 className="text-5xl font-black tracking-tighter uppercase mb-2">Exam Test Center</h1>
                    <p className="text-muted-foreground font-semibold max-w-lg mx-auto text-lg">
                        Execute full-scale exam simulations with real rules, timers, and high-weightage topics.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
                    <div className="p-8 bg-blue-500/5 border-2 border-blue-500/10 rounded-[2.5rem] space-y-4">
                        <div className="h-12 w-12 bg-blue-500/20 rounded-2xl flex items-center justify-center">
                            <Clock className="text-blue-600" />
                        </div>
                        <h3 className="text-xl font-black">Simulation Engine</h3>
                        <p className="text-sm font-medium text-muted-foreground">
                            We search for official exam rules and set a precise timer. The test auto-closes when time is up.
                        </p>
                    </div>
                    <div className="p-8 bg-purple-500/5 border-2 border-purple-500/10 rounded-[2.5rem] space-y-4">
                        <div className="h-12 w-12 bg-purple-500/20 rounded-2xl flex items-center justify-center">
                            <Target className="text-purple-600" />
                        </div>
                        <h3 className="text-xl font-black">Weightage Focused</h3>
                        <p className="text-sm font-medium text-muted-foreground">
                            AI analyzes the syllabus to prioritize hard-level questions from high-weightage chapters.
                        </p>
                    </div>
                </div>

                <Card className="border-none shadow-2xl bg-card rounded-[3rem] overflow-hidden p-2">
                    <CardContent className="p-10 space-y-8">
                        <div className="space-y-4 text-center">
                            <p className="font-black text-xs uppercase tracking-[0.2em] text-primary">Enter Target Examination</p>
                            <Input
                                placeholder="e.g. UPSC, GATE 2024, JEE Main, NEET"
                                value={examName}
                                onChange={(e) => setExamName(e.target.value)}
                                className="h-20 text-2xl font-black text-center rounded-[2rem] border-4 focus:ring-8 transition-all"
                            />
                        </div>
                        <Button
                            onClick={handleStartTest}
                            className="w-full h-20 rounded-[2rem] text-xl font-black uppercase tracking-widest shadow-2xl shadow-primary/30"
                            isLoading={isLoading}
                        >
                            <Play size={24} className="mr-3 fill-current" />
                            Initialize Simulation
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // 2. Results View
    if (results) {
        const isSuccess = results.score >= 50; // Exams are harder
        return (
            <div className="max-w-5xl mx-auto py-12 px-4">
                <div className="text-center mb-10">
                    <div className="inline-flex items-center gap-2 px-6 py-2 rounded-full bg-muted font-black text-xs uppercase tracking-widest mb-4">
                        <ShieldCheck size={16} className="text-primary" />
                        Test Center Transcript
                    </div>
                    <h1 className="text-5xl font-black tracking-tight">{results.topic} Result</h1>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
                    <Card className={`lg:col-span-2 rounded-[3.5rem] border-none shadow-2xl overflow-hidden ${isSuccess ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
                        <CardContent className="p-12 h-full flex flex-col justify-center">
                            <div className="flex items-start justify-between">
                                <div className="space-y-4">
                                    <h2 className="text-[120px] font-black leading-none tracking-tighter tabular-nums">
                                        {Math.round(results.score)}<span className="text-4xl opacity-50">%</span>
                                    </h2>
                                    <div className="space-y-1">
                                        <p className="text-2xl font-black uppercase">Simulation {isSuccess ? 'Passed' : 'Failed'}</p>
                                        <p className="text-white/70 font-bold max-w-md">
                                            {isSuccess
                                                ? "You have demonstrated professional competency in this exam simulation. Keep up the momentum!"
                                                : "This was a high-difficulty simulation. Use the insights below to bridge your knowledge gaps."}
                                        </p>
                                    </div>
                                </div>
                                <div className="h-32 w-32 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-md">
                                    {isSuccess ? <Award size={64} /> : <AlertTriangle size={64} />}
                                </div>
                            </div>
                            <div className="mt-12 flex gap-4">
                                <Button onClick={resetQuiz} className="bg-white text-black hover:bg-zinc-200 rounded-2xl h-14 px-10 font-black uppercase tracking-widest border-none">
                                    New Simulation
                                </Button>
                                <Button variant="outline" className="text-white border-white/30 hover:bg-white/10 rounded-2xl h-14 px-10 font-black uppercase tracking-widest">
                                    Download Review
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    <div className="space-y-6">
                        <div className="p-8 bg-card rounded-[2.5rem] shadow-xl border-2 border-border/50 text-center">
                            <CheckCircle className="h-10 w-10 text-green-500 mx-auto mb-3" />
                            <p className="text-[10px] font-black uppercase tracking-widest opacity-40">Accuracy</p>
                            <p className="text-4xl font-black">{results.correct_answers}/{results.total_questions}</p>
                        </div>
                        <div className="p-8 bg-card rounded-[2.5rem] shadow-xl border-2 border-border/50 text-center">
                            <Timer className="h-10 w-10 text-blue-500 mx-auto mb-3" />
                            <p className="text-[10px] font-black uppercase tracking-widest opacity-40">Time Taken</p>
                            <p className="text-4xl font-black">{formatTime(results.time_taken_seconds)}</p>
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    <h2 className="text-2xl font-black uppercase tracking-tight px-4 flex items-center gap-3">
                        <Brain className="text-primary" />
                        Detailed Analysis
                    </h2>
                    {results.detailed_results.map((result, idx) => (
                        <Card key={idx} className="border-none shadow-lg rounded-[2.5rem] overflow-hidden hover:shadow-2xl transition-shadow">
                            <CardContent className="p-8 flex items-start gap-8">
                                <div className={`h-14 w-14 rounded-2xl flex items-center justify-center shrink-0 shadow-lg ${result.is_correct ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}`}>
                                    {result.is_correct ? <CheckCircle size={28} /> : <XCircle size={28} />}
                                </div>
                                <div className="space-y-4">
                                    <div className="flex items-center gap-2">
                                        <span className={`text-[10px] font-black px-3 py-1 rounded-full uppercase ${result.is_correct ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                            {result.is_correct ? 'Verified' : 'Incorrect'}
                                        </span>
                                        <span className="text-[10px] font-black text-muted-foreground uppercase">Item {idx + 1}</span>
                                    </div>
                                    <p className="text-lg font-bold leading-tight">{result.explanation}</p>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                                        <div className={`p-4 rounded-2xl border-2 ${result.is_correct ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
                                            <p className="text-[10px] uppercase font-black opacity-40 mb-1">Your Submission</p>
                                            <p className={`font-black ${result.is_correct ? 'text-green-600' : 'text-red-500'}`}>{result.user_answer}</p>
                                        </div>
                                        {!result.is_correct && (
                                            <div className="p-4 bg-green-500/5 rounded-2xl border-2 border-green-500/10">
                                                <p className="text-[10px] uppercase font-black opacity-40 mb-1">Official Solution</p>
                                                <p className="font-black text-green-600">{result.correct_answer}</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        );
    }

    // 3. Active Test View
    if (activeQuiz && currentQ) {
        return (
            <div className="max-w-6xl mx-auto py-8 px-4 animate-in fade-in duration-700">
                {/* Fixed Timer Header */}
                <div className="sticky top-4 z-50 mb-8 p-6 bg-card/80 backdrop-blur-2xl border-2 border-primary/20 rounded-[2.5rem] shadow-2xl flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="text-center bg-primary text-primary-foreground p-2 rounded-xl h-12 w-12 flex items-center justify-center text-xl font-black">
                            {currentQuestion + 1}
                        </div>
                        <div>
                            <h3 className="font-black uppercase tracking-tight text-sm">Question {currentQuestion + 1} of {activeQuiz.questions.length}</h3>
                            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{activeQuiz.topic} Simulation</p>
                        </div>
                    </div>

                    <div className={`flex items-center gap-4 px-8 py-3 rounded-2xl border-2 transition-colors ${timeLeft !== null && timeLeft < 300 ? 'bg-red-500/10 border-red-500 text-red-600 animate-pulse' : 'bg-muted/50 border-border/50'}`}>
                        <Timer className="h-6 w-6" />
                        <span className="text-3xl font-black tabular-nums">{timeLeft !== null ? formatTime(timeLeft) : '--:--'}</span>
                    </div>

                    <Button onClick={handleManualSubmit} variant="outline" className="rounded-xl border-2 font-black uppercase text-xs">
                        Early Exit
                    </Button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                    {/* Progress Sidebar */}
                    <div className="hidden lg:block space-y-4">
                        <Card className="rounded-[2rem] border-none shadow-xl bg-card p-6">
                            <h4 className="font-black uppercase text-xs mb-4 text-center">Navigator</h4>
                            <div className="grid grid-cols-4 gap-2">
                                {activeQuiz.questions.map((q, idx) => (
                                    <button
                                        key={q.question_id}
                                        onClick={() => useQuizStore.getState().goToQuestion(idx)}
                                        className={`h-10 rounded-xl font-black text-xs transition-all ${idx === currentQuestion
                                            ? 'bg-primary text-primary-foreground ring-4 ring-primary/20'
                                            : answers[q.question_id]
                                                ? 'bg-green-500/20 text-green-600 border border-green-500/20'
                                                : 'bg-muted text-muted-foreground hover:bg-muted/80'
                                            }`}
                                    >
                                        {idx + 1}
                                    </button>
                                ))}
                            </div>
                        </Card>
                    </div>

                    {/* Main Question Card */}
                    <div className="lg:col-span-3 space-y-8">
                        <Card className="border-none shadow-2xl bg-card rounded-[3.5rem] overflow-hidden min-h-[500px] flex flex-col">
                            <CardContent className="p-10 md:p-16 flex-1 space-y-10">
                                <p className="text-2xl md:text-3xl font-black leading-tight tracking-tight">
                                    {currentQ.question_text || currentQ.question}
                                </p>

                                <div className="grid grid-cols-1 gap-4">
                                    {currentQ.options.map((option, index) => {
                                        const hasPrefix = option.length > 3 && option.charAt(1) === ')';
                                        const optionLetter = hasPrefix ? option.charAt(0) : String.fromCharCode(65 + index);
                                        const optionText = hasPrefix ? option.substring(3) : option;

                                        return (
                                            <button
                                                key={index}
                                                onClick={() => submitAnswer(currentQ.question_id, optionLetter)}
                                                className={`group relative text-left p-8 rounded-[2rem] border-2 transition-all duration-300 ${selectedAnswer === optionLetter
                                                    ? 'border-primary bg-primary/5 ring-1 ring-primary/20 translate-x-1'
                                                    : 'border-muted/50 bg-card hover:bg-muted/10 hover:border-muted-foreground/30'
                                                    }`}
                                            >
                                                <div className="flex items-center gap-6">
                                                    <div className={`h-12 w-12 rounded-xl flex items-center justify-center font-black text-lg transition-colors ${selectedAnswer === optionLetter
                                                        ? 'bg-primary text-primary-foreground'
                                                        : 'bg-muted group-hover:bg-muted-foreground/10 text-muted-foreground'
                                                        }`}>
                                                        {optionLetter}
                                                    </div>
                                                    <span className="text-xl font-bold leading-tight flex-1">
                                                        {optionText}
                                                    </span>
                                                </div>
                                            </button>
                                        );
                                    })}
                                </div>
                            </CardContent>

                            <div className="p-8 border-t bg-muted/20 flex items-center justify-between">
                                <Button
                                    variant="ghost"
                                    onClick={previousQuestion}
                                    disabled={currentQuestion === 0}
                                    className="rounded-xl h-12 font-black px-8 uppercase text-xs"
                                >
                                    Previous
                                </Button>

                                {currentQuestion < activeQuiz.questions.length - 1 ? (
                                    <Button
                                        onClick={nextQuestion}
                                        className="rounded-2xl h-14 px-12 font-black uppercase tracking-widest shadow-xl shadow-primary/20"
                                    >
                                        Next Item <ArrowRight size={18} className="ml-2" />
                                    </Button>
                                ) : (
                                    <Button
                                        onClick={handleManualSubmit}
                                        isLoading={isLoading}
                                        className="rounded-2xl h-14 px-12 font-black uppercase tracking-widest bg-green-600 hover:bg-green-700 shadow-xl shadow-green-500/20"
                                    >
                                        Submit Final Result <Award size={18} className="ml-2" />
                                    </Button>
                                )}
                            </div>
                        </Card>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="h-screen flex items-center justify-center">
            <Loading text="Initializing Proctored Simulation Engine..." />
        </div>
    );
};
