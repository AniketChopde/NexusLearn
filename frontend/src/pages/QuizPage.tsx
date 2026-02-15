import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useQuizStore } from '../stores/quizStore';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Loading } from '../components/ui/Loading';
import {
    Brain, Clock, CheckCircle, XCircle,
    ArrowRight, RefreshCcw, GraduationCap,
    Target, Award, AlertTriangle, Lightbulb, History
} from 'lucide-react';
import { formatTime } from '../lib/utils';

export const QuizPage: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const {
        activeQuiz,
        currentQuestion,
        answers,
        results,
        timeStarted,
        quizHistory,
        generateQuiz,
        generateChapterQuiz,
        submitAnswer,
        submitQuiz,
        nextQuestion,
        previousQuestion,
        resetQuiz,

        fetchHistory,
        loadQuizResult,
        isLoading,
    } = useQuizStore();


    const [topic, setTopic] = React.useState('');
    const [subject, setSubject] = React.useState('');
    const [elapsedTime, setElapsedTime] = React.useState(0);
    // Parse URL params
    const queryParams = new URLSearchParams(location.search);
    const urlTopic = queryParams.get('topic');
    const urlSubject = queryParams.get('subject');
    const urlChapterId = queryParams.get('chapterId');
    const urlExamType = queryParams.get('examType');
    const autoStart = queryParams.get('autoStart') === 'true';

    const hasStartedRef = React.useRef(false);

    // Reset quiz on mount if we're not waiting for results or mid-quiz
    // This fixes the issue where old results persist when coming back to "Take Quiz"
    React.useEffect(() => {
        // Only reset if we don't have URL params that imply continuation or specific start
        // And if we are not already in a fresh state
        if (!urlChapterId && !urlTopic && (activeQuiz || results)) {
            resetQuiz();
        }
    }, [location.pathname, location.key]); // Run on mount/navigation

    // When coming from Study Plan "Knowledge Check" with chapterId, only clear *completed* quiz (results) so we can start a new one.
    React.useEffect(() => {
        if (urlChapterId && results) {
            resetQuiz();
            hasStartedRef.current = false;
        }
    }, [urlChapterId, results, resetQuiz]);

    React.useEffect(() => {
        if (urlTopic && urlTopic !== topic) setTopic(urlTopic);
        if (urlSubject && urlSubject !== subject) setSubject(urlSubject);

        const hasChapterContext = urlChapterId || (urlTopic && urlSubject);
        const canAutoStart = autoStart && hasChapterContext && !activeQuiz && !results && !isLoading && !hasStartedRef.current;
        if (canAutoStart) {
            hasStartedRef.current = true; // set immediately so we never fire twice (e.g. Strict Mode)
            handleGenerateQuiz();
        }
    }, [urlTopic, urlSubject, urlChapterId, autoStart, activeQuiz, results, isLoading]);

    React.useEffect(() => {
        if (timeStarted) {
            const interval = setInterval(() => {
                setElapsedTime(Math.floor((Date.now() - timeStarted) / 1000));
            }, 1000);
            return () => clearInterval(interval);
        }
    }, [timeStarted]);

    const handleGenerateQuiz = async () => {
        if (urlChapterId) {
            await generateChapterQuiz(urlChapterId);
        } else {
            const finalTopic = urlTopic || topic;
            const finalSubject = urlSubject || subject;
            if (!finalTopic || !finalSubject) return;
            await generateQuiz(finalTopic, finalSubject, 10, 'medium', urlExamType);
        }
    };

    const handleSubmitQuiz = async () => {
        await submitQuiz();
    };

    const currentQ = activeQuiz?.questions[currentQuestion];
    const selectedAnswer = currentQ ? answers[currentQ.question_id] : undefined;

    // Fetch quiz history when on config view so user can see their previous attempts
    React.useEffect(() => {
        if (!activeQuiz && !results) {
            fetchHistory();
        }
    }, [activeQuiz, results, fetchHistory]);

    // Quiz Generation Form
    if (!activeQuiz && !results) {
        return (
            <div className="max-w-2xl mx-auto py-12 px-4 animate-in fade-in duration-700 space-y-10">
                <div className="text-center mb-10 space-y-4">
                    <div className="h-20 w-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Brain className="h-10 w-10 text-primary" />
                    </div>
                    <h1 className="text-4xl font-black tracking-tight uppercase">Knowledge Validator</h1>
                    <p className="text-muted-foreground font-medium max-w-sm mx-auto">
                        Ready to prove your mastery? Generate an AI-powered quiz tailored to your current study topic.
                    </p>
                </div>

                <Card className="border-none shadow-2xl bg-card rounded-[2.5rem] overflow-hidden">
                    <CardHeader className="p-8 pb-0">
                        <CardTitle className="text-lg font-black uppercase tracking-widest text-primary flex items-center gap-2">
                            <Target size={20} />
                            Quiz Configuration
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="p-8 space-y-6">
                        <Input
                            label="Topic of Interest"
                            placeholder="e.g., Quantum Mechanics"
                            value={topic}
                            onChange={(e) => setTopic(e.target.value)}
                            className="h-14 rounded-2xl"
                        />
                        <Input
                            label="Broad Subject Area"
                            placeholder="e.g., Physics"
                            value={subject}
                            onChange={(e) => setSubject(e.target.value)}
                            className="h-14 rounded-2xl"
                        />
                        <Button
                            onClick={handleGenerateQuiz}
                            className="w-full h-16 rounded-[1.5rem] text-sm font-black uppercase tracking-widest shadow-xl shadow-primary/20 mt-4"
                            isLoading={isLoading}
                            disabled={!topic || !subject}
                        >
                            Start Assessment 🚀
                        </Button>
                    </CardContent>
                </Card>

                {/* Your Quiz History – stored attempts, always visible */}
                <Card className="border-none shadow-xl bg-card rounded-[2.5rem] overflow-hidden">
                    <CardHeader className="p-6 pb-0">
                        <CardTitle className="text-base font-black uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                            <History size={18} />
                            Your Quiz History
                        </CardTitle>
                        <CardDescription className="text-sm text-muted-foreground/80">
                            Previous attempts are stored here. Starting a new quiz does not remove them.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="p-6 pt-4">
                        {quizHistory.length === 0 ? (
                            <p className="text-sm text-muted-foreground py-6 text-center">
                                No quizzes yet. Complete a quiz to see it here.
                            </p>
                        ) : (
                            <ul className="space-y-3 max-h-64 overflow-y-auto">
                                {quizHistory.map((entry) => (
                                    <li
                                        key={entry.id}
                                        onClick={() => loadQuizResult(entry.id)}
                                        className="flex items-center justify-between p-4 rounded-2xl bg-muted/30 border border-border/50 hover:bg-muted/50 transition-colors cursor-pointer"
                                    >
                                        <div className="min-w-0">
                                            <p className="font-bold text-foreground truncate">{entry.topic}</p>
                                            <p className="text-xs text-muted-foreground mt-0.5">{entry.subject} · {entry.difficulty}</p>
                                        </div>
                                        <div className="flex items-center gap-4 shrink-0 ml-4">
                                            {entry.status === 'completed' && entry.score != null && (
                                                <span className={`text-sm font-black px-2.5 py-1 rounded-lg ${entry.score >= 70 ? 'bg-green-500/20 text-green-600' : 'bg-amber-500/20 text-amber-600'}`}>
                                                    {Math.round(entry.score)}%
                                                </span>
                                            )}
                                            <span className="text-xs text-muted-foreground whitespace-nowrap">
                                                {entry.completed_at
                                                    ? new Date(entry.completed_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
                                                    : new Date(entry.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                            </span>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Quiz Results
    if (results) {
        const isSuccess = results.score >= 70;
        return (
            <div className="max-w-4xl mx-auto py-12 px-4 animate-in fade-in slide-in-from-bottom-8 duration-700">
                <div className="mb-10 text-center space-y-2 relative">
                    {/* <Button
                        variant="ghost" 
                        onClick={() => {
                            resetQuiz();
                            navigate('/quiz');
                        }}
                        className="absolute left-0 top-0 hidden md:flex"
                    >
                        <ArrowRight className="h-4 w-4 mr-2 rotate-180" /> Back
                    </Button> */}
                    <span className="text-xs font-black uppercase tracking-widest text-muted-foreground opacity-60">Performance Report</span>
                    <h1 className="text-4xl font-black">{results.topic}</h1>
                </div>

                <Card className={`mb-8 border-none shadow-2xl rounded-[3rem] overflow-hidden ${isSuccess ? 'bg-green-500/5' : 'bg-orange-500/5'}`}>
                    <CardContent className="p-10 md:p-14">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                            <div className="text-center lg:text-left space-y-6">
                                <div className="space-y-2">
                                    <div className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full font-black text-[10px] uppercase tracking-widest ${isSuccess ? 'bg-green-500/20 text-green-600' : 'bg-orange-500/20 text-orange-600'}`}>
                                        {isSuccess ? <Award size={14} /> : <AlertTriangle size={14} />}
                                        {isSuccess ? 'Goal Achieved' : 'Learning Gap Detected'}
                                    </div>
                                    <h2 className="text-7xl font-black tracking-tighter tabular-nums">
                                        {Math.round(results.score)}<span className="text-3xl opacity-30">%</span>
                                    </h2>
                                </div>
                                <p className="text-lg font-medium text-muted-foreground leading-relaxed">
                                    {isSuccess
                                        ? "Outstanding! You've successfully demonstrated your understanding of this topic. You're ready to proceed."
                                        : "Don't worry! This is part of the process. We've identified some areas that need another look before you move forward."}
                                </p>
                                <div className="flex flex-wrap gap-4 pt-4">
                                    {isSuccess ? (
                                        <Button onClick={() => navigate('/study-plans')} className="rounded-2xl h-14 px-8 font-black uppercase tracking-widest shadow-lg shadow-primary/20">
                                            Continue Journey <ArrowRight size={18} className="ml-2" />
                                        </Button>
                                    ) : (
                                        <Button onClick={resetQuiz} className="rounded-2xl h-14 px-8 font-black uppercase tracking-widest bg-orange-600 hover:bg-orange-700">
                                            Try Again <RefreshCcw size={18} className="ml-2" />
                                        </Button>
                                    )}
                                    <Button variant="outline" onClick={() => navigate('/analytics')} className="rounded-2xl h-14 px-8 font-black uppercase tracking-widest border-2">
                                        View Breakdown
                                    </Button>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-8 bg-background rounded-[2rem] border border-border/50 text-center space-y-2">
                                    <CheckCircle className="h-8 w-8 text-green-500 mx-auto" />
                                    <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Correct</p>
                                    <p className="text-3xl font-black">{results.correct_answers}</p>
                                </div>
                                <div className="p-8 bg-background rounded-[2rem] border border-border/50 text-center space-y-2">
                                    <XCircle className="h-8 w-8 text-red-500 mx-auto" />
                                    <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Wrong</p>
                                    <p className="text-3xl font-black">{results.total_questions - results.correct_answers}</p>
                                </div>
                                <div className="p-8 bg-background rounded-[2rem] border border-border/50 text-center col-span-2 space-y-2">
                                    <Clock className="h-8 w-8 text-blue-500 mx-auto" />
                                    <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Total Time Invested</p>
                                    <p className="text-2xl font-black">{formatTime(results.time_taken_seconds)}</p>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* AI Insights */}
                {!isSuccess && (
                    <div className="mb-8 p-8 rounded-[2.5rem] bg-primary/5 border border-primary/10 space-y-4">
                        <div className="flex items-center gap-3">
                            <Lightbulb className="text-primary h-6 w-6" />
                            <h3 className="text-xl font-black uppercase tracking-tighter">AI Learning Recommendation</h3>
                        </div>
                        <p className="text-sm font-medium text-muted-foreground leading-relaxed">
                            Based on your performance, we suggest focusing on the concepts where you missed questions.
                            If you used the <b>AI Teaching Mode</b>, try reviewing the <b>Common Pitfalls</b> and <b>Real-World Illustrations</b> again.
                            A score below 70% suggests the foundation is still forming—take your time!
                        </p>
                    </div>
                )}

                {/* Detailed Results */}
                <div className="space-y-6">
                    <h2 className="text-xl font-black uppercase tracking-widest px-2">Knowledge Gap Analysis</h2>
                    {results.detailed_results.map((result, index) => (
                        <Card key={index} className="border-none shadow-lg rounded-3xl overflow-hidden">
                            <CardContent className="p-8">
                                <div className="flex items-start gap-6">
                                    <div className={`h-12 w-12 rounded-2xl flex items-center justify-center shrink-0 shadow-sm ${result.is_correct ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}`}>
                                        {result.is_correct ? <CheckCircle size={24} /> : <XCircle size={24} />}
                                    </div>
                                    <div className="flex-1 space-y-4">
                                        <div className="flex items-center justify-between">
                                            <p className="text-xs font-black uppercase tracking-widest opacity-40">Observation {index + 1}</p>
                                            <span className={`text-[10px] font-black px-3 py-1 rounded-full uppercase ${result.is_correct ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                                {result.is_correct ? 'Accurate' : 'Misconception'}
                                            </span>
                                        </div>
                                        <p className="text-sm font-bold text-muted-foreground leading-relaxed">{result.explanation}</p>
                                        <div className="flex flex-col md:flex-row gap-4 pt-2">
                                            <div className="flex-1 p-4 bg-muted/30 rounded-2xl border border-transparent">
                                                <p className="text-[10px] uppercase font-black opacity-40 mb-1">Proposed Choice</p>
                                                <p className={`text-sm font-bold ${result.is_correct ? 'text-green-600' : 'text-red-500'}`}>{result.user_answer}</p>
                                            </div>
                                            {!result.is_correct && (
                                                <div className="flex-1 p-4 bg-green-500/5 rounded-2xl border border-green-500/10">
                                                    <p className="text-[10px] uppercase font-black opacity-40 mb-1">Correct Reality</p>
                                                    <p className="text-sm font-bold text-green-600">{result.correct_answer}</p>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        );
    }

    // Active Quiz
    if (activeQuiz && currentQ) {
        const progress = ((currentQuestion + 1) / activeQuiz.questions.length) * 100;

        return (
            <div className="max-w-4xl mx-auto py-12 px-4 animate-in fade-in duration-700">
                {/* Header */}
                <div className="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="space-y-1">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary mb-2">
                            <GraduationCap size={14} />
                            <span className="text-[10px] font-black uppercase tracking-widest">{activeQuiz.subject}</span>
                        </div>
                        <h1 className="text-3xl font-black leading-tight tracking-tight">{activeQuiz.topic}</h1>
                    </div>
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-3 p-4 bg-muted/40 rounded-2xl border border-border/50 shadow-sm min-w-32">
                            <Clock className="h-5 w-5 text-primary" />
                            <span className="font-black text-lg tabular-nums">{formatTime(elapsedTime)}</span>
                        </div>
                        <div className="text-right">
                            <p className="text-[10px] font-black uppercase tracking-widest opacity-40">Progression</p>
                            <p className="text-lg font-black">{currentQuestion + 1} / {activeQuiz.questions.length}</p>
                        </div>
                    </div>
                </div>

                {/* Question Card */}
                <Card className="mb-8 border-none shadow-2xl bg-card rounded-[3rem] overflow-hidden">
                    <div className="h-2 bg-muted">
                        <div
                            className="h-full bg-primary transition-all duration-1000 ease-out"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                    <CardContent className="p-10 md:p-14 space-y-10">
                        {currentQ.question_text || currentQ.question || "Question text unavailable"}

                        {/* PYQ Indicator */}
                        {currentQ.metadata?.is_pyq && (
                            <div className="absolute top-8 right-8 animate-in fade-in slide-in-from-top-4 duration-500">
                                <div className="bg-yellow-100 text-yellow-800 border-yellow-200 border px-4 py-2 rounded-xl shadow-sm transform rotate-2 hover:rotate-0 transition-transform cursor-help">
                                    <div className="flex items-center gap-2">
                                        <Award size={16} className="text-yellow-600" />
                                        <div className="flex flex-col leading-none">
                                            <span className="text-[10px] font-black uppercase tracking-widest text-yellow-600/60">Previous Year Q</span>
                                            <span className="text-xs font-black">
                                                {currentQ.metadata.exam} {currentQ.metadata.year ? "'" + currentQ.metadata.year.slice(-2) : ''}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}


                        <div className="grid grid-cols-1 gap-4">
                            {currentQ.options.map((option, index) => {
                                const hasPrefix = option.length > 3 && option.charAt(1) === ')';
                                const optionLetter = hasPrefix ? option.charAt(0) : String.fromCharCode(65 + index);
                                const optionText = hasPrefix ? option.substring(3) : option;

                                return (
                                    <button
                                        key={index}
                                        onClick={() => submitAnswer(currentQ.question_id, optionLetter)}
                                        className={`group text-left p-6 rounded-[2rem] border-2 transition-all duration-300 relative overflow-hidden ${selectedAnswer === optionLetter
                                            ? 'border-primary bg-primary/5 ring-1 ring-primary/20'
                                            : 'border-muted/50 bg-card hover:bg-muted/10 hover:border-muted-foreground/30'
                                            }`}
                                    >
                                        <div className="flex items-center gap-5 relative z-10">
                                            <div className={`h-10 w-10 rounded-xl flex items-center justify-center font-black transition-colors ${selectedAnswer === optionLetter ? 'bg-primary text-primary-foreground' : 'bg-muted group-hover:bg-muted-foreground/10 text-muted-foreground'}`}>
                                                {optionLetter}
                                            </div>
                                            <span className="text-lg font-bold leading-tight">
                                                {optionText}
                                            </span>
                                        </div>
                                        {selectedAnswer === optionLetter && (
                                            <div className="absolute top-0 right-0 p-4 opacity-10">
                                                <CheckCircle size={48} className="text-primary" />
                                            </div>
                                        )}
                                    </button>
                                )
                            })}
                        </div>
                    </CardContent>
                </Card>

                {/* Navigation */}
                <div className="flex items-center justify-between px-4">
                    <Button
                        variant="ghost"
                        onClick={previousQuestion}
                        disabled={currentQuestion === 0}
                        className="rounded-xl h-12 font-bold px-6"
                    >
                        Previous
                    </Button>
                    {currentQuestion < activeQuiz.questions.length - 1 ? (
                        <Button
                            onClick={nextQuestion}
                            disabled={!selectedAnswer}
                            className="rounded-2xl h-14 px-10 font-black uppercase tracking-widest shadow-xl shadow-primary/20"
                        >
                            Next Question <ArrowRight size={18} className="ml-2" />
                        </Button>
                    ) : (
                        <Button
                            onClick={handleSubmitQuiz}
                            isLoading={isLoading}
                            disabled={!selectedAnswer}
                            className="rounded-2xl h-14 px-10 font-black uppercase tracking-widest bg-green-600 hover:bg-green-700 shadow-xl shadow-green-500/20"
                        >
                            Submit Validation <Award size={18} className="ml-2" />
                        </Button>
                    )}
                </div>
            </div >
        );
    }

    return (
        <div className="h-screen flex items-center justify-center">
            <Loading text="Initializing Adaptive Quiz Engine..." />
        </div>
    );
};
