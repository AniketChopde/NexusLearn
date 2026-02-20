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
import { EngagementButtons } from '../components/EngagementButtons';

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
    const [elapsedSeconds, setElapsedSeconds] = React.useState(0);

    // Initialization: If we come back and there's no active quiz, reset
    React.useEffect(() => {
        // Only reset if we are not in progress
        if (!activeQuiz && !results) {
            resetQuiz();
        }
    }, []);

    // Timer Logic: countdown when time_limit_minutes set, else just track elapsed
    React.useEffect(() => {
        if (!activeQuiz || !timeStarted || results) return;

        const totalMinutes = activeQuiz.time_limit_minutes ?? 180; // fallback 3h for test center
        const totalSeconds = totalMinutes * 60;

        const tick = () => {
            const elapsed = Math.floor((Date.now() - timeStarted) / 1000);
            setElapsedSeconds(elapsed);
            const remaining = totalSeconds - elapsed;

            if (remaining <= 0) {
                setTimeLeft(0);
                handleAutoSubmit();
                return true;
            }
            setTimeLeft(remaining);
            return false;
        };

        if (tick()) return; // time already up on mount
        const intervalId = setInterval(() => {
            if (tick()) clearInterval(intervalId);
        }, 1000);

        return () => clearInterval(intervalId);
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
            <div className="max-w-3xl mx-auto py-10 px-4 animate-in fade-in duration-700">
                <div className="text-center mb-8 space-y-4">
                    <div className="h-16 w-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-4 transform rotate-3 shadow-inner">
                        <ShieldCheck className="h-8 w-8 text-primary" />
                    </div>
                    <h1 className="text-4xl font-black tracking-tighter uppercase mb-2">Exam Test Center</h1>
                    <p className="text-muted-foreground font-medium max-w-lg mx-auto text-base">
                        Execute full-scale exam simulations with real rules, timers, and high-weightage topics.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <div className="p-5 bg-blue-500/5 border border-blue-500/10 rounded-2xl space-y-3 hover:bg-blue-500/10 transition-colors">
                        <div className="h-10 w-10 bg-blue-500/20 rounded-xl flex items-center justify-center">
                            <Clock className="text-blue-600 h-5 w-5" />
                        </div>
                        <div>
                            <h3 className="text-lg font-black">Simulation Engine</h3>
                            <p className="text-xs font-medium text-muted-foreground mt-1">
                                We search for official exam rules and set a precise timer. The test auto-closes when time is up.
                            </p>
                        </div>
                    </div>
                    <div className="p-5 bg-purple-500/5 border border-purple-500/10 rounded-2xl space-y-3 hover:bg-purple-500/10 transition-colors">
                        <div className="h-10 w-10 bg-purple-500/20 rounded-xl flex items-center justify-center">
                            <Target className="text-purple-600 h-5 w-5" />
                        </div>
                        <div>
                            <h3 className="text-lg font-black">Weightage Focused</h3>
                            <p className="text-xs font-medium text-muted-foreground mt-1">
                                AI analyzes the syllabus to prioritize hard-level questions from high-weightage chapters.
                            </p>
                        </div>
                    </div>
                </div>

                <Card className="border-none shadow-xl bg-card rounded-3xl overflow-hidden">
                    <CardContent className="p-8 space-y-6">
                        <div className="space-y-3 text-center">
                            <p className="font-black text-[10px] uppercase tracking-[0.2em] text-primary">Enter Target Examination</p>
                            <Input
                                placeholder="e.g. UPSC, GATE 2024, JEE Main, NEET"
                                value={examName}
                                onChange={(e) => setExamName(e.target.value)}
                                className="h-14 text-lg font-bold text-center rounded-xl border-2 focus:ring-4 transition-all"
                            />
                        </div>
                        <Button
                            onClick={handleStartTest}
                            className="w-full h-14 rounded-xl text-lg font-black uppercase tracking-widest shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all"
                            isLoading={isLoading}
                        >
                            <Play size={20} className="mr-2 fill-current" />
                            Initialize Simulation
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // 2. Results View
    const handleDownloadReview = () => {
        if (!results) return;
        
        const content = [
            `Test Center Result: ${results.topic}`,
            `Score: ${Math.round(results.score)}%`,
            `Status: ${results.score >= 50 ? 'PASSED' : 'FAILED'}`,
            `Date: ${new Date().toLocaleString()}`,
            `----------------------------------------`,
            `DETAILS`,
            ...results.detailed_results.map((r, i) => `
Item ${i + 1}: ${r.explanation}
Your Answer: ${r.user_answer}
Correct Answer: ${r.correct_answer}
Result: ${r.is_correct ? 'CORRECT' : 'INCORRECT'}
----------------------------------------`)
        ].join('\n');

        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${results.topic.replace(/\s+/g, '_')}_Result.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    if (results) {
        const isSuccess = results.score >= 50;
        return (
            <div className="max-w-4xl mx-auto py-8 px-4">
                <div className="text-center mb-6">
                    <h1 className="text-2xl font-black tracking-tight">{results.topic} Result</h1>
                    <div className="flex justify-center mt-2">
                        <EngagementButtons 
                            contentType="simulation" 
                            contentId={results.id || 'simulation'} 
                        />
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-8">
                    <Card className={`lg:col-span-2 rounded-2xl shadow-sm border-2 overflow-hidden ${isSuccess ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                        <CardContent className="p-6 h-full flex flex-col justify-center">
                            <div className="flex items-start justify-between">
                                <div className="space-y-2">
                                    <h2 className="text-6xl font-black leading-none tracking-tighter tabular-nums">
                                        {Math.round(results.score)}<span className="text-3xl opacity-50">%</span>
                                    </h2>
                                    <div className="space-y-1">
                                        <p className="text-lg font-black uppercase">Simulation {isSuccess ? 'Passed' : 'Failed'}</p>
                                        <p className="font-medium text-sm max-w-sm opacity-80">
                                            {isSuccess
                                                ? "You have demonstrated professional competency in this exam simulation."
                                                : "This was a high-difficulty simulation. Review the analysis below."}
                                        </p>
                                    </div>
                                </div>
                                <div className="h-16 w-16 bg-white/50 rounded-xl flex items-center justify-center backdrop-blur-sm">
                                    {isSuccess ? <Award size={32} /> : <AlertTriangle size={32} />}
                                </div>
                            </div>
                            <div className="mt-6 flex gap-3">
                                <Button onClick={resetQuiz} className="bg-foreground text-background hover:bg-foreground/90 rounded-lg h-10 px-5 font-bold uppercase text-[10px] tracking-widest shadow-sm">
                                    New Simulation
                                </Button>
                                <Button onClick={handleDownloadReview} variant="outline" className="bg-transparent border-current hover:bg-black/5 rounded-lg h-10 px-5 font-bold uppercase text-[10px] tracking-widest">
                                    Download Review
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    <div className="grid grid-cols-2 lg:grid-cols-1 gap-4">
                        <div className="p-4 bg-card rounded-2xl shadow-sm border text-center flex flex-col items-center justify-center">
                            <CheckCircle className="h-6 w-6 text-green-500 mb-2" />
                            <p className="text-[10px] font-bold uppercase tracking-widest opacity-40">Accuracy</p>
                            <p className="text-2xl font-black">{results.correct_answers}/{results.total_questions}</p>
                        </div>
                        <div className="p-4 bg-card rounded-2xl shadow-sm border text-center flex flex-col items-center justify-center">
                            <Timer className="h-6 w-6 text-blue-500 mb-2" />
                            <p className="text-[10px] font-bold uppercase tracking-widest opacity-40">Time Taken</p>
                            <p className="text-2xl font-black">{formatTime(results.time_taken_seconds)}</p>
                        </div>
                    </div>
                </div>

                <div className="space-y-4">
                    <h2 className="text-lg font-black uppercase tracking-tight px-2 flex items-center gap-2">
                        <Brain className="text-primary h-4 w-4" />
                        Detailed Analysis
                    </h2>
                    {results.detailed_results.map((result, idx) => (
                        <Card key={idx} className="border-none shadow-sm rounded-xl overflow-hidden hover:shadow-md transition-shadow bg-card/50">
                            <CardContent className="p-4 flex items-start gap-4">
                                <div className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 shadow-sm ${result.is_correct ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}`}>
                                    {result.is_correct ? <CheckCircle size={16} /> : <XCircle size={16} />}
                                </div>
                                <div className="space-y-2 flex-1">
                                    <div className="flex items-center gap-2">
                                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${result.is_correct ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                            {result.is_correct ? 'Verified' : 'Incorrect'}
                                        </span>
                                        <span className="text-[10px] font-bold text-muted-foreground uppercase">Item {idx + 1}</span>
                                    </div>
                                    <p className="text-sm font-bold leading-relaxed">{result.explanation}</p>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1">
                                        <div className={`p-2 rounded-lg border ${result.is_correct ? 'bg-green-50/50 border-green-100' : 'bg-red-50/50 border-red-100'}`}>
                                            <p className="text-[10px] uppercase font-black opacity-40 mb-1">Your Submission</p>
                                            <p className={`font-bold text-xs ${result.is_correct ? 'text-green-600' : 'text-red-500'}`}>{result.user_answer}</p>
                                        </div>
                                        {!result.is_correct && (
                                            <div className="p-2 bg-green-50/50 rounded-lg border border-green-100">
                                                <p className="text-[10px] uppercase font-black opacity-40 mb-1">Official Solution</p>
                                                <p className="font-bold text-xs text-green-600">{result.correct_answer}</p>
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
        const showCountdown = activeQuiz.time_limit_minutes != null;
        const timerValue = showCountdown && timeLeft !== null ? formatTime(timeLeft) : formatTime(elapsedSeconds);
        const timerLabel = showCountdown ? 'Time left' : 'Elapsed';

        return (
            <div className="max-w-5xl mx-auto py-6 px-4 animate-in fade-in duration-700">
                {/* Fixed Timer Header - always visible below app top bar */}
                <div className="fixed left-0 right-0 top-16 z-50 px-4 lg:px-8">
                    <div className="mx-auto max-w-5xl p-4 bg-card/95 backdrop-blur-md border border-primary/10 rounded-2xl shadow-lg flex flex-wrap items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                            <div className="text-center bg-primary text-primary-foreground p-2 rounded-lg h-10 w-10 flex items-center justify-center text-lg font-bold shrink-0">
                                {currentQuestion + 1}
                            </div>
                            <div className="min-w-0">
                                <h3 className="font-bold uppercase tracking-tight text-xs">Question {currentQuestion + 1} of {activeQuiz.questions.length}</h3>
                                <p className="text-[10px] font-medium text-muted-foreground uppercase truncate">{activeQuiz.topic}</p>
                            </div>
                        </div>

                        <div className={`flex items-center gap-3 px-5 py-2.5 rounded-xl border transition-colors shrink-0 ${showCountdown && timeLeft !== null && timeLeft < 300 ? 'bg-red-500/10 border-red-500 text-red-600 animate-pulse' : 'bg-muted/30 border-border/50'}`}>
                            <Timer className="h-5 w-5 text-primary" aria-hidden />
                            <div className="text-right">
                                <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">{timerLabel}</p>
                                <span className="text-xl font-bold tabular-nums">{timerValue}</span>
                            </div>
                        </div>

                        <Button onClick={handleManualSubmit} variant="ghost" size="sm" className="rounded-lg font-bold uppercase text-[10px] hover:bg-destructive/10 hover:text-destructive shrink-0">
                            Early Exit
                        </Button>
                    </div>
                </div>

                {/* Spacer so content starts below the fixed timer bar */}
                <div className="h-20 shrink-0" aria-hidden />

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    {/* Progress Sidebar */}
                    <div className="hidden lg:block lg:col-span-3 space-y-4">
                        <Card className="rounded-2xl border-none shadow-sm bg-card/50 p-4">
                            <h4 className="font-bold uppercase text-[10px] mb-3 text-center text-muted-foreground">Navigator</h4>
                            <div className="grid grid-cols-5 gap-2">
                                {activeQuiz.questions.map((q, idx) => (
                                    <button
                                        key={q.question_id}
                                        onClick={() => useQuizStore.getState().goToQuestion(idx)}
                                        className={`h-8 w-8 rounded-lg font-bold text-xs flex items-center justify-center transition-all ${idx === currentQuestion
                                            ? 'bg-primary text-primary-foreground shadow-md scale-110'
                                            : answers[q.question_id]
                                                ? 'bg-green-500/10 text-green-700 border border-green-500/20'
                                                : 'bg-muted/50 text-muted-foreground hover:bg-muted'
                                            }`}
                                    >
                                        {idx + 1}
                                    </button>
                                ))}
                            </div>
                        </Card>
                    </div>

                    {/* Main Question Card */}
                    <div className="lg:col-span-9 space-y-6">
                        <Card className="border-none shadow-xl bg-card rounded-[2rem] overflow-hidden min-h-[400px] flex flex-col">
                            <CardContent className="p-6 md:p-10 flex-1 space-y-6">
                                <p className="text-xl md:text-2xl font-bold leading-snug tracking-tight text-foreground/90">
                                    {currentQ.question_text || currentQ.question}
                                </p>

                                <div className="space-y-3">
                                    {currentQ.options.map((option, index) => {
                                        const hasPrefix = option.length > 3 && option.charAt(1) === ')';
                                        const optionLetter = hasPrefix ? option.charAt(0) : String.fromCharCode(65 + index);
                                        const optionText = hasPrefix ? option.substring(3) : option;
                                        const isSelected = selectedAnswer === optionLetter;

                                        return (
                                            <button
                                                key={index}
                                                onClick={() => submitAnswer(currentQ.question_id, optionLetter)}
                                                className={`w-full group relative text-left p-4 rounded-xl border transition-all duration-200 ${isSelected
                                                    ? 'border-primary bg-primary/5 shadow-inner'
                                                    : 'border-transparent bg-muted/30 hover:bg-muted/60'
                                                    }`}
                                            >
                                                <div className="flex items-center gap-4">
                                                    <div className={`h-8 w-8 rounded-lg flex items-center justify-center font-bold text-sm transition-colors ${isSelected
                                                        ? 'bg-primary text-primary-foreground'
                                                        : 'bg-background text-muted-foreground border shadow-sm'
                                                        }`}>
                                                        {optionLetter}
                                                    </div>
                                                    <span className={`text-base font-medium leading-normal flex-1 ${isSelected ? 'text-primary font-bold' : 'text-foreground/80'}`}>
                                                        {optionText}
                                                    </span>
                                                </div>
                                            </button>
                                        );
                                    })}
                                </div>
                            </CardContent>

                            <div className="p-6 border-t bg-muted/10 flex items-center justify-between">
                                <Button
                                    variant="ghost"
                                    onClick={previousQuestion}
                                    disabled={currentQuestion === 0}
                                    className="rounded-xl h-10 font-bold px-6 text-xs"
                                >
                                    Previous
                                </Button>

                                {currentQuestion < activeQuiz.questions.length - 1 ? (
                                    <Button
                                        onClick={nextQuestion}
                                        className="rounded-xl h-10 px-8 font-bold uppercase text-xs tracking-wide shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all"
                                    >
                                        Next <ArrowRight size={16} className="ml-2" />
                                    </Button>
                                ) : (
                                    <Button
                                        onClick={handleManualSubmit}
                                        isLoading={isLoading}
                                        className="rounded-xl h-10 px-8 font-bold uppercase text-xs tracking-wide bg-green-600 hover:bg-green-700 shadow-lg shadow-green-500/20 hover:shadow-green-500/30 transition-all"
                                    >
                                        Submit <Award size={16} className="ml-2" />
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
