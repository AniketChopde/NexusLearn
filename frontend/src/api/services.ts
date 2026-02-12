import apiClient from './client';
import type {
    LoginCredentials,
    RegisterData,
    TokenResponse,
    User,
    CreatePlanData,
    StudyPlan,
    Quiz,
    QuizHistoryItem,
    QuizSubmission,
    QuizResult,
    ChatRequest,
    ChatResponse,
    Resource,
    Explanation,
    Mindmap,
    TopicMindmap,
    DashboardStats,
} from '../types';

// Auth Service
export const authService = {
    register: (data: RegisterData) =>
        apiClient.post<User>('/auth/register', data),

    login: (credentials: LoginCredentials) =>
        apiClient.post<TokenResponse>('/auth/login', credentials),

    getProfile: () =>
        apiClient.get<User>('/auth/profile'),

    refreshToken: () =>
        apiClient.post<TokenResponse>('/auth/refresh'),
};

// Study Plan Service
export const studyPlanService = {
    create: (data: CreatePlanData) =>
        apiClient.post('/study-plan/create', data),

    get: (id: string) =>
        apiClient.get<StudyPlan>(`/study-plan/${id}`),

    list: () =>
        apiClient.get<StudyPlan[]>('/study-plan'),

    delete: (id: string) =>
        apiClient.delete(`/study-plan/${id}`),

    updateChapterStatus: (chapterId: string, status: 'pending' | 'in_progress' | 'completed') =>
        apiClient.patch(`/study-plan/chapter/${chapterId}`, { status }),

    teachChapter: (chapterId: string) =>
        apiClient.post(`/study-plan/chapter/${chapterId}/teach`),
};

// Content Service
export const contentService = {
    explain: (topic: string, detailLevel: string = 'detailed', includeExamples: boolean = true) =>
        apiClient.post<Explanation>('/content/explain', {
            topic,
            detail_level: detailLevel,
            include_examples: includeExamples,
        }),

    createMindmap: (subject: string) =>
        apiClient.post<Mindmap>('/content/mindmap', { subject }),
};

// Topic Mindmap Service
export const mindmapService = {
    getTopicMindmap: (topicId: string) =>
        apiClient.get<TopicMindmap>(`/mindmap/topic/${encodeURIComponent(topicId)}`),
};

// Quiz Service
export const quizService = {
    generate: (topic: string, subject: string, questionCount: number = 10, difficulty: string = 'medium', examType?: string | null) =>
        apiClient.post<Quiz>('/quiz/generate', {
            topic,
            subject,
            question_count: questionCount,
            difficulty,
            exam_type: examType || undefined,
        }),

    submit: (submission: QuizSubmission) =>
        apiClient.post<QuizResult>('/quiz/submit', submission),

    getHistory: () =>
        apiClient.get<QuizHistoryItem[]>('/quiz/history'),

    startTestCenter: (examName: string) =>
        apiClient.post<Quiz>('/quiz/test-center', { exam_name: examName }),

    generateChapterQuiz: (chapterId: string) =>
        apiClient.post<Quiz>(`/quiz/chapter/${chapterId}/generate`),
};

// Chat Service
export const chatService = {
    sendMessage: (request: ChatRequest) =>
        apiClient.post<ChatResponse>('/chat/message', request),

    getHistory: (sessionId: string) =>
        apiClient.get(`/chat/history/${sessionId}`),

    deleteSession: (sessionId: string) =>
        apiClient.delete(`/chat/session/${sessionId}`),
};

// Search Service
export const searchService = {
    deepSearch: (query: string, searchDepth: string = 'comprehensive') =>
        apiClient.post('/search/deep', { query, search_depth: searchDepth }),

    searchResources: (topic: string, resourceType: string = 'all') =>
        apiClient.post<{ topic: string; resources: Resource[] }>('/search/resources', {
            topic,
            resource_type: resourceType,
        }),
};

// Analytics / Dashboard Service
export const analyticsService = {
    getStats: () =>
        apiClient.get<DashboardStats>('/analytics/stats'),

    getProgress: () =>
        apiClient.get('/analytics/progress'),

    getGaps: () =>
        apiClient.get('/analytics/gaps'),
};
