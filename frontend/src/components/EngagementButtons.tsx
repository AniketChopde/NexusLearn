
import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { submitEngagement, getEngagement } from '../api/engagement';
import type { ContentType, EngagementAction } from '../api/engagement';
import { cn } from '../utils/cn'; // Assuming utility exists, otherwise inline

interface EngagementButtonsProps {
    contentType: ContentType;
    contentId: string;
    initialAction?: EngagementAction | null; // 'like', 'dislike' or null
    className?: string;
}

export const EngagementButtons: React.FC<EngagementButtonsProps> = ({
    contentType,
    contentId,
    initialAction = null,
    className
}) => {
    const [action, setAction] = useState<EngagementAction | null>(initialAction);
    const [loading, setLoading] = useState(false);

    // Fetch existing engagement status on mount
    React.useEffect(() => {
        let isMounted = true;
        
        const fetchStatus = async () => {
            try {
                // Check both like and dislike status
                const [likeData, dislikeData] = await Promise.all([
                    getEngagement(contentType, contentId, 'like'),
                    getEngagement(contentType, contentId, 'dislike')
                ]);

                if (!isMounted) return;

                // Determine effective action
                // Priority to whichever exists. If both (edge case), default to like or most recent? 
                // Since we can't easily check timestamps without more logic, we'll straightforwardly check presence.
                // ideally backend ensures mutual exclusivity, but for now:
                if (likeData) {
                    setAction('like');
                    // If dislike also exists, we have a data consistency issue, but let's trust UI flow mostly prevents it.
                } else if (dislikeData) {
                    setAction('dislike');
                }
            } catch (error) {
                console.error("Failed to fetch engagement status:", error);
            }
        };

        fetchStatus();

        return () => { isMounted = false; };
    }, [contentType, contentId]);

    const handleAction = async (newAction: EngagementAction) => {
        if (loading) return;
        
        // Optimistic update (toggle off if same action clicked)
        // For distinct like/dislike actions, toggling off is tricky without a 'delete' endpoint.
        // For now, we'll just switch. If clicking same, maybe valid to keep it or do nothing.
        // Let's allow switching.
        if (action === newAction) return; 

        const prevAction = action;
        setAction(newAction);

        try {
            setLoading(true);
            await submitEngagement({
                content_type: contentType,
                content_id: contentId,
                action: newAction,
                value: newAction === 'like' ? 1 : -1,
            });
            toast.success(newAction === 'like' ? 'Liked!' : 'Disliked');
        } catch (error) {
            console.error('Failed to update engagement:', error);
            toast.error('Failed to submit feedback');
            setAction(prevAction); // Revert
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={cn("flex items-center gap-2", className)}>
            <button
                onClick={() => handleAction('like')}
                disabled={loading}
                className={cn(
                    "p-1.5 rounded-full transition-colors",
                    action === 'like' 
                        ? "text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400" 
                        : "text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20"
                )}
                title="Like"
            >
                <ThumbsUp className={cn("w-4 h-4", action === 'like' && "fill-current")} />
            </button>
            <button
                onClick={() => handleAction('dislike')}
                disabled={loading}
                className={cn(
                    "p-1.5 rounded-full transition-colors",
                    action === 'dislike' 
                        ? "text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-400" 
                        : "text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                )}
                title="Dislike"
            >
                <ThumbsDown className={cn("w-4 h-4", action === 'dislike' && "fill-current")} />
            </button>
        </div>
    );
};
