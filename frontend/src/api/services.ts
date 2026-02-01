import apiClient from './client';
import type {
    LoginCredentials,
    RegisterData,
    TokenResponse,
    User,
    CreatePlanData,
    StudyPlan,
    Quiz,
    QuizSubmission,
    QuizResult,
    ChatRequest,
    ChatResponse,
    Resource,
    Explanation,
    Mindmap,
    TopicMindmap,
} from '../types';

// Auth Service
export const authService = {
    register: (data: RegisterData) =>
        apiClient.post<User>('/api/auth/register', data),

    login: (credentials: LoginCredentials) =>
        apiClient.post<TokenResponse>('/api/auth/login', credentials),

    getProfile: () =>
        apiClient.get<User>('/api/auth/profile'),

    refreshToken: () =>
        apiClient.post<TokenResponse>('/api/auth/refresh'),
};

// Study Plan Service
export const studyPlanService = {
    create: (data: CreatePlanData) =>
        apiClient.post('/api/study-plan/create', data),

    get: (id: string) =>
        apiClient.get<StudyPlan>(`/api/study-plan/${id}`),

    list: () =>
        apiClient.get<StudyPlan[]>('/api/study-plan'),

    delete: (id: string) =>
        apiClient.delete(`/api/study-plan/${id}`),

    updateChapterStatus: (chapterId: string, status: 'pending' | 'in_progress' | 'completed') =>
        apiClient.patch(`/api/study-plan/chapter/${chapterId}`, { status }),

    teachChapter: (chapterId: string) =>
        apiClient.post(`/api/study-plan/chapter/${chapterId}/teach`),
};

// Content Service
export const contentService = {
    explain: (topic: string, detailLevel: string = 'detailed', includeExamples: boolean = true) =>
        apiClient.post<Explanation>('/api/content/explain', {
            topic,
            detail_level: detailLevel,
            include_examples: includeExamples,
        }),

    createMindmap: (subject: string) =>
        apiClient.post<Mindmap>('/api/content/mindmap', { subject }),
};

// Topic Mindmap Service
export const mindmapService = {
    getTopicMindmap: (topicId: string) =>
        apiClient.get<TopicMindmap>(`/api/mindmap/topic/${encodeURIComponent(topicId)}`),
};

// Quiz Service
export const quizService = {
    generate: (topic: string, subject: string, questionCount: number = 10, difficulty: string = 'medium', examType?: string | null) =>
        apiClient.post<Quiz>('/api/quiz/generate', {
            topic,
            subject,
            question_count: questionCount,
            difficulty,
            exam_type: examType || undefined,
        }),

    submit: (submission: QuizSubmission) =>
        apiClient.post<QuizResult>('/api/quiz/submit', submission),

    getHistory: () =>
        apiClient.get<Quiz[]>('/api/quiz/history'),

    startTestCenter: (examName: string) =>
        apiClient.post<Quiz>('/api/quiz/test-center', { exam_name: examName }),

    generateChapterQuiz: (chapterId: string) =>
        apiClient.post<Quiz>(`/api/quiz/chapter/${chapterId}/generate`),
};

// Chat Service
export const chatService = {
    sendMessage: (request: ChatRequest) =>
        apiClient.post<ChatResponse>('/api/chat/message', request),

    getHistory: (sessionId: string) =>
        apiClient.get(`/api/chat/history/${sessionId}`),

    deleteSession: (sessionId: string) =>
        apiClient.delete(`/api/chat/session/${sessionId}`),
};

// Search Service
export const searchService = {
    deepSearch: (query: string, searchDepth: string = 'comprehensive') =>
        apiClient.post('/api/search/deep', { query, search_depth: searchDepth }),

    searchResources: (topic: string, resourceType: string = 'all') =>
        apiClient.post<{ topic: string; resources: Resource[] }>('/api/search/resources', {
            topic,
            resource_type: resourceType,
        }),
};

// Analytics Service (if you add analytics endpoints later)
export const analyticsService = {
    getStats: () =>
        apiClient.get('/api/analytics/stats'),

    getProgress: () =>
        apiClient.get('/api/analytics/progress'),

    getGaps: () =>
        apiClient.get('/api/analytics/gaps'),
};
