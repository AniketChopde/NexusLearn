// User Types
export interface User {
    id: string;
    email: string;
    full_name?: string;
    is_active: boolean;
    is_verified: boolean;
    created_at: string;
}

export interface LoginCredentials {
    email: string;
    password: string;
}

export interface RegisterData {
    email: string;
    password: string;
    full_name?: string;
}

export interface TokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

// Study Plan Types
export interface StudyPlan {
    id: string;
    exam_type: string;
    target_date: string;
    daily_hours: number;
    status: string;
    current_knowledge: Record<string, any>;
    recommended_courses?: Resource[]; // New field
    chapters: Chapter[];
    plan_metadata?: Record<string, any>;
    created_at: string;
}

export interface Chapter {
    id: string;
    chapter_name: string;
    subject: string;
    topics: string[];
    estimated_hours: number;
    order_index: number;
    status: string;
    resources: Resource[];
    content?: ChapterContent;
}

export interface ChapterContent {
    chapter_name: string;
    overview: string;
    learning_path: any[];
    topic_lessons: Explanation[];
    exercises: any[];
    key_takeaways: string[];
}

export interface CreatePlanData {
    exam_type: string;
    target_date: string;
    daily_hours: number;
    current_knowledge: Record<string, any>;
    fast_learn: boolean;
}

// Quiz Types
export interface Quiz {
    id: string;
    topic: string;
    subject: string;
    difficulty: string;
    questions: Question[];
    status: string;
    time_limit_minutes?: number;
    created_at: string;
}

/** Quiz history entry (from GET /quiz/history) – stored attempts, no questions. */
export interface QuizHistoryItem {
    id: string;
    topic: string;
    subject: string;
    difficulty: string;
    status: string;
    score?: number | null;
    completed_at?: string | null;
    created_at: string;
}

export interface Question {
    question_id: string;
    question_text?: string; // Make optional to allow fallback
    question?: string; // Backwards compatibility for API mismatch
    options: string[];
    correct_answer: string;
    explanation: string;
    difficulty: string;
    topic: string;
    marks: number;
    metadata?: {
        is_pyq?: boolean;
        year?: string | null;
        exam?: string | null;
        [key: string]: any;
    };
}

export interface QuizSubmission {
    quiz_id: string;
    answers: Record<string, string>;
    time_taken_seconds: number;
}

export interface QuizResult {
    id: string;
    topic: string;
    subject: string;
    score: number;
    total_questions: number;
    correct_answers: number;
    time_taken_seconds: number;
    answers: Record<string, string>;
    detailed_results: DetailedResult[];
    completed_at: string;
}

export interface DetailedResult {
    question_id: string;
    user_answer: string;
    correct_answer: string;
    is_correct: boolean;
    explanation: string;
    marks_obtained: number;
    total_marks: number;
}

// Chat Types
export interface ChatSession {
    id: string;
    title?: string;
    messages: ChatMessage[];
    created_at: string;
}

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
}

export interface ChatRequest {
    session_id?: string;
    message: string;
    context?: Record<string, any>;
}

export interface ChatResponse {
    session_id: string;
    message: string;
    sources: any[];
}

// Progress Types
export interface UserStats {
    study_streak: number;
    total_hours: number;
    completed_topics: number;
    quiz_average: number;
}

/** Dashboard stats from /api/analytics/stats */
export interface DashboardStats {
    study_streak_days: number;
    hours_studied: number;
    topics_completed: number;
    topics_total: number;
    quiz_average_percent: number | null;
}

export interface Progress {
    id: string;
    topic: string;
    subject: string;
    completion_percentage: number;
    quiz_scores: number[];
    time_spent_minutes: number;
    last_accessed: string;
}

export interface Gap {
    topic: string;
    subject: string;
    priority: 'high' | 'medium' | 'low';
    reason: string;
    recommended_action: string;
}

export interface Recommendation {
    priority: string;
    title: string;
    description: string;
    resources: Resource[];
    estimated_time: string;
}

// Resource Types
export interface Resource {
    title: string;
    type: 'video' | 'article' | 'book' | 'practice' | 'tutorial';
    url: string;
    source: string;
    snippet?: string;
    rating?: number;
    duration?: string;
    thumbnail?: string;
    description?: string;
}

// Content Types
export interface Explanation {
    topic: string;
    introduction: string;
    main_explanation: string;
    key_points: string[];
    visuals?: { type: string; description: string }[];
    visual_description?: string; // New: grounded visual description
    mermaid_diagram?: string;
    examples?: Example[];
    common_mistakes?: string[]; // New: added for deep lesson
    exam_tips?: string[]; // New: added for deep lesson
    common_misconceptions?: string[];
    related_topics?: string[];
    difficulty_level?: string;
    citation?: string; // New: source citation
    is_blocked?: boolean; // New: for grounding filter
}

export interface Example {
    title: string;
    description: string;
    code?: string;
}

export interface Mindmap {
    central_topic: string;
    main_branches: MindmapBranch[];
    connections: MindmapConnection[];
}

export interface MindmapBranch {
    branch_name: string;
    sub_branches: SubBranch[];
}

export interface SubBranch {
    name: string;
    concepts: string[];
}

export interface MindmapConnection {
    from: string;
    to: string;
    relationship: string;
}

export interface TopicMindmapNode {
    id: string;
    label: string;
    type: string;
}

export interface TopicMindmapEdge {
    source: string;
    target: string;
}

export interface TopicMindmap {
    topic: string;
    nodes: TopicMindmapNode[];
    edges: TopicMindmapEdge[];
    metadata: {
        exam?: string | null;
        chapter?: string | null;
        topic?: string | null;
        [key: string]: any;
    };
}

// API Response Types
export interface ApiResponse<T> {
    success: boolean;
    message: string;
    data?: T;
    timestamp: string;
}

export interface ApiError {
    error: boolean;
    message: string;
    detail?: any;
    status_code: number;
    timestamp: string;
}
