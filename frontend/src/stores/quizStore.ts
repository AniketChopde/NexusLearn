import { create } from 'zustand';
import { quizService } from '../api/services';
import type { Quiz, QuizResult, QuizHistoryItem } from '../types';
import toast from 'react-hot-toast';

interface QuizState {
    activeQuiz: Quiz | null;
    currentQuestion: number;
    answers: Record<string, string>;
    results: QuizResult | null;
    quizHistory: QuizHistoryItem[];
    isLoading: boolean;
    timeStarted: number | null;

    // Actions
    generateQuiz: (topic: string, subject: string, count?: number, difficulty?: string, examType?: string | null) => Promise<void>;
    submitAnswer: (questionId: string, answer: string) => void;
    submitQuiz: () => Promise<void>;
    nextQuestion: () => void;
    previousQuestion: () => void;
    goToQuestion: (index: number) => void;
    fetchHistory: () => Promise<void>;
    resetQuiz: () => void;
    startTestCenter: (examName: string) => Promise<void>;
    generateChapterQuiz: (chapterId: string) => Promise<void>;
    loadQuizResult: (id: string) => Promise<void>;
}

export const useQuizStore = create<QuizState>((set, get) => ({
    activeQuiz: null,
    currentQuestion: 0,
    answers: {},
    results: null,
    quizHistory: [],
    isLoading: false,
    timeStarted: null,

    generateChapterQuiz: async (chapterId) => {
        try {
            set({ isLoading: true });
            const response = await quizService.generateChapterQuiz(chapterId);

            set({
                activeQuiz: response.data,
                currentQuestion: 0,
                answers: {},
                results: null,
                timeStarted: Date.now(),
                isLoading: false,
            });

            toast.success('Chapter quiz generated with PYQs!');
        } catch (error) {
            set({ isLoading: false });
            toast.error('Failed to generate chapter quiz');
            throw error;
        }
    },

    loadQuizResult: async (id) => {
        try {
            set({ isLoading: true });
            const response = await quizService.getResult(id);
            set({
                results: response.data,
                activeQuiz: null, // Ensure we are not in "taking quiz" mode
                isLoading: false,
            });
        } catch (error) {
            set({ isLoading: false });
            toast.error('Failed to load quiz result');
            throw error;
        }
    },
    startTestCenter: async (examName) => {
        try {
            set({ isLoading: true });
            const response = await quizService.startTestCenter(examName);

            set({
                activeQuiz: response.data,
                currentQuestion: 0,
                answers: {},
                results: null,
                timeStarted: Date.now(),
                isLoading: false,
            });

            toast.success(`Exam simulation for ${examName} started!`);
        } catch (error) {
            set({ isLoading: false });
            toast.error('Failed to start test center');
            throw error;
        }
    },

    generateQuiz: async (topic, subject, count = 10, difficulty = 'medium', examType = null) => {
        try {
            set({ isLoading: true });
            const response = await quizService.generate(topic, subject, count, difficulty, examType);

            set({
                activeQuiz: response.data,
                currentQuestion: 0,
                answers: {},
                results: null,
                timeStarted: Date.now(),
                isLoading: false,
            });

            toast.success('Quiz generated successfully!');
        } catch (error) {
            set({ isLoading: false });
            toast.error('Failed to generate quiz');
            throw error;
        }
    },

    submitAnswer: (questionId, answer) => {
        set((state) => ({
            answers: {
                ...state.answers,
                [questionId]: answer,
            },
        }));
    },

    submitQuiz: async () => {
        try {
            const { activeQuiz, answers, timeStarted } = get();

            if (!activeQuiz || !timeStarted) {
                toast.error('No active quiz');
                return;
            }

            const timeTaken = (Date.now() - timeStarted) / 1000; // in seconds

            set({ isLoading: true });

            const response = await quizService.submit({
                quiz_id: activeQuiz.id,
                answers,
                time_taken_seconds: timeTaken,
            });

            set({
                results: response.data,
                isLoading: false,
            });

            toast.success('Quiz submitted successfully!');
        } catch (error) {
            set({ isLoading: false });
            toast.error('Failed to submit quiz');
            throw error;
        }
    },

    nextQuestion: () => {
        set((state) => {
            const maxQuestion = (state.activeQuiz?.questions.length || 1) - 1;
            return {
                currentQuestion: Math.min(state.currentQuestion + 1, maxQuestion),
            };
        });
    },

    previousQuestion: () => {
        set((state) => ({
            currentQuestion: Math.max(state.currentQuestion - 1, 0),
        }));
    },

    goToQuestion: (index) => {
        set({ currentQuestion: index });
    },

    fetchHistory: async () => {
        try {
            const response = await quizService.getHistory();
            set({ quizHistory: response.data });
        } catch (error) {
            toast.error('Failed to fetch quiz history');
            throw error;
        }
    },

    // Clears only the current in-progress quiz so a new one can be started. Does NOT remove or clear
    // quiz history: completed quizzes remain stored on the backend and in quizHistory when fetched.
    resetQuiz: () => {
        set({
            activeQuiz: null,
            currentQuestion: 0,
            answers: {},
            results: null,
            timeStarted: null,
        });
    },
}));
