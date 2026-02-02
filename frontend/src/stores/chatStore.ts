import { create } from 'zustand';
import { chatService } from '../api/services';
import type { ChatMessage, ChatSession } from '../types';
import toast from 'react-hot-toast';

// UUID generator that works in all contexts (including HTTP)
const generateUUID = (): string => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    // Fallback for browsers without crypto.randomUUID
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
};

interface ChatState {
    sessions: ChatSession[];
    activeSession: ChatSession | null;
    messages: ChatMessage[];
    isTyping: boolean;
    activeAgent: string;
    chatContext: Record<string, any>;

    // Actions
    sendMessage: (message: string, context?: Record<string, any>) => Promise<void>;
    createSession: () => void;
    loadHistory: (sessionId: string) => Promise<void>;
    deleteSession: (sessionId: string) => Promise<void>;
    setActiveSession: (session: ChatSession | null) => void;
    setChatContext: (context: Record<string, any>) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
    sessions: [],
    activeSession: null,
    messages: [],
    isTyping: false,
    activeAgent: '',
    chatContext: {},

    sendMessage: async (message, context = {}) => {
        try {
            const { activeSession } = get();
            const mergedContext = { ...(get().chatContext || {}), ...(context || {}) };

            if (Object.keys(mergedContext).length > 0) {
                set({ chatContext: mergedContext });
            }

            // Add user message immediately
            const userMessage: ChatMessage = {
                role: 'user',
                content: message,
                timestamp: new Date().toISOString(),
            };

            set((state) => ({
                messages: [...state.messages, userMessage],
                isTyping: true,
                activeAgent: 'AI Tutor',
            }));

            // Send to API
            const response = await chatService.sendMessage({
                session_id: activeSession?.id,
                message,
                context: mergedContext,
            });

            // Add AI response
            const aiMessage: ChatMessage = {
                role: 'assistant',
                content: response.data.message,
                timestamp: new Date().toISOString(),
            };

            set((state) => ({
                messages: [...state.messages, aiMessage],
                isTyping: false,
                activeSession: activeSession || {
                    id: response.data.session_id,
                    title: message.substring(0, 50),
                    messages: [userMessage, aiMessage],
                    created_at: new Date().toISOString(),
                },
            }));
        } catch (error) {
            set({ isTyping: false });
            toast.error('Failed to send message');
            throw error;
        }
    },

    createSession: () => {
        const newSession: ChatSession = {
            id: generateUUID(),
            title: 'New Chat',
            messages: [],
            created_at: new Date().toISOString(),
        };

        set({
            activeSession: newSession,
            messages: [],
            chatContext: {},
        });
    },

    setChatContext: (context) => {
        set({ chatContext: context || {} });
    },

    loadHistory: async (sessionId) => {
        try {
            const response = await chatService.getHistory(sessionId);
            const session = response.data;

            set({
                activeSession: session,
                messages: session.messages,
            });
        } catch (error) {
            toast.error('Failed to load chat history');
            throw error;
        }
    },

    deleteSession: async (sessionId) => {
        try {
            await chatService.deleteSession(sessionId);

            set((state) => ({
                sessions: state.sessions.filter((s) => s.id !== sessionId),
                activeSession: state.activeSession?.id === sessionId ? null : state.activeSession,
                messages: state.activeSession?.id === sessionId ? [] : state.messages,
            }));

            toast.success('Chat session deleted');
        } catch (error) {
            toast.error('Failed to delete session');
            throw error;
        }
    },

    setActiveSession: (session) => {
        set({
            activeSession: session,
            messages: session?.messages || [],
        });
    },
}));
