import { create } from 'zustand';
import { studyPlanService } from '../api/services';
import type { StudyPlan, CreatePlanData } from '../types';
import toast from 'react-hot-toast';

interface StudyPlanState {
    plans: StudyPlan[];
    activePlan: StudyPlan | null;
    isLoading: boolean;
    isCreating: boolean;
    isTeaching: boolean;
    isSearchingCourses: boolean;

    // Actions
    fetchPlans: () => Promise<void>;
    createPlan: (data: CreatePlanData) => Promise<any>;
    getPlan: (id: string) => Promise<void>;
    deletePlan: (id: string) => Promise<void>;
    updateChapterStatus: (chapterId: string, status: 'pending' | 'in_progress' | 'completed') => Promise<void>;
    teachChapter: (chapterId: string) => Promise<any>;
    getCourses: (planId: string) => Promise<void>;
    setActivePlan: (plan: StudyPlan | null) => void;
}

export const useStudyPlanStore = create<StudyPlanState>((set, get) => ({
    plans: [],
    activePlan: null,
    isLoading: false,
    isCreating: false,
    isTeaching: false,
    isSearchingCourses: false,

    fetchPlans: async () => {
        try {
            set({ isLoading: true });
            const response = await studyPlanService.list();
            set({ plans: response.data, isLoading: false });
        } catch (error) {
            set({ isLoading: false });
            toast.error('Failed to fetch study plans');
            throw error;
        }
    },

    createPlan: async (data) => {
        try {
            set({ isCreating: true });
            const response = await studyPlanService.create(data);

            // Refresh plans list to ensure dashboard is up to date
            await get().fetchPlans();

            // Set the active plan if we have a detailed object back
            if (response.data.study_plan) {
                set({ activePlan: response.data.study_plan });
            }

            set({ isCreating: false });
            toast.success('Study plan created successfully!');

            return response.data;
        } catch (error: any) {
            set({ isCreating: false });
            toast.error(error.response?.data?.detail || 'Failed to create study plan');
            throw error;
        }
    },

    getPlan: async (id: string) => {
        try {
            set({ isLoading: true });
            const response = await studyPlanService.get(id);
            set({ activePlan: response.data, isLoading: false });
        } catch (error) {
            set({ isLoading: false });
            toast.error('Failed to fetch study plan');
            throw error;
        }
    },

    getCourses: async (planId: string) => {
        try {
            set({ isSearchingCourses: true });
            // Don't set global isLoading to avoid full page spinner
            const response = await studyPlanService.getCourses(planId);

            set((state) => {
                if (!state.activePlan || state.activePlan.id !== planId) return state;
                return {
                    activePlan: {
                        ...state.activePlan,
                        recommended_courses: response.data
                    },
                    isSearchingCourses: false
                };
            });
        } catch (error) {
            console.error('Failed to fetch courses:', error);
            set({ isSearchingCourses: false });
        }
    },

    deletePlan: async (id: string) => {
        try {
            await studyPlanService.delete(id);

            // Remove from plans list
            set((state) => ({
                plans: state.plans.filter((plan) => plan.id !== id),
                activePlan: state.activePlan?.id === id ? null : state.activePlan,
            }));

            toast.success('Study plan deleted');
        } catch (error) {
            toast.error('Failed to delete study plan');
            throw error;
        }
    },

    updateChapterStatus: async (chapterId, status) => {
        try {
            await studyPlanService.updateChapterStatus(chapterId, status);

            // Update in local state
            set((state) => {
                if (!state.activePlan) return state;

                const updatedChapters = state.activePlan.chapters.map((chapter) =>
                    chapter.id.toString() === chapterId ? { ...chapter, status } : chapter
                );

                return {
                    activePlan: {
                        ...state.activePlan,
                        chapters: updatedChapters,
                    },
                };
            });

            toast.success(`Chapter marked as ${status}`);
        } catch (error) {
            toast.error('Failed to update chapter status');
            throw error;
        }
    },

    teachChapter: async (chapterId) => {
        try {
            set({ isTeaching: true });
            const response = await studyPlanService.teachChapter(chapterId);

            // Update the chapter content in local state
            set((state) => {
                if (!state.activePlan) return state;
                const updatedChapters = state.activePlan.chapters.map((chapter) =>
                    chapter.id.toString() === chapterId
                        ? { ...chapter, content: response.data }
                        : chapter
                );
                return {
                    activePlan: { ...state.activePlan, chapters: updatedChapters },
                    isTeaching: false
                };
            });

            return response.data;
        } catch (error) {
            set({ isTeaching: false });
            toast.error('Failed to generate teaching content');
            throw error;
        }
    },

    setActivePlan: (plan) => set({ activePlan: plan }),
}));
