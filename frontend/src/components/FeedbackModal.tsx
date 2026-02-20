
import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { Star, X } from 'lucide-react';
import { Button } from './ui/Button'; // Assuming we have these
import { submitEngagement, getEngagement } from '../api/engagement';
import type { ContentType, EngagementAction } from '../api/engagement';

interface FeedbackModalProps {
    isOpen: boolean;
    onClose: () => void;
    contentType: ContentType;
    contentId: string;
    title?: string;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
    isOpen,
    onClose,
    contentType,
    contentId,
    title = "Rate your experience"
}) => {
    const [rating, setRating] = useState(0);
    const [hoverRating, setHoverRating] = useState(0);
    const [comment, setComment] = useState('');
    const [loading, setLoading] = useState(false);
    const [fetching, setFetching] = useState(false);

    useEffect(() => {
        if (isOpen) {
            const fetchFeedback = async () => {
                setFetching(true);
                try {
                    const data = await getEngagement(contentType, contentId, 'rate');
                    if (data) {
                        setRating(data.value);
                        setComment(data.comment || '');
                    } else {
                        // Reset if no existing feedback
                        setRating(0);
                        setComment('');
                    }
                } catch (error) {
                    console.error("Failed to fetch feedback:", error);
                } finally {
                    setFetching(false);
                }
            };
            fetchFeedback();
        }
    }, [isOpen, contentType, contentId]);

    if (!isOpen) return null;

    const handleSubmit = async () => {
        if (rating === 0) {
            toast.error("Please select a rating");
            return;
        }

        try {
            setLoading(true);
            await submitEngagement({
                content_type: contentType,
                content_id: contentId,
                action: 'rate' as EngagementAction, // Explicit cast if string literal types
                value: rating,
                comment: comment
            });
            toast.success("Thank you for your feedback!");
            onClose();
        } catch (error) {
            console.error("Failed to submit feedback:", error);
            toast.error("Something went wrong. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6 relative animate-in fade-in zoom-in duration-200">
                <button 
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                >
                    <X className="w-5 h-5" />
                </button>

                <h3 className="text-xl font-semibold mb-2">{title}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                    {fetching ? "Loading your feedback..." : "Your feedback helps us improve the learning experience."}
                </p>

                <div className="flex justify-center gap-2 mb-6">
                    {[1, 2, 3, 4, 5].map((star) => (
                        <button
                            key={star}
                            className="transition-transform hover:scale-110 focus:outline-none"
                            onMouseEnter={() => setHoverRating(star)}
                            onMouseLeave={() => setHoverRating(0)}
                            onClick={() => setRating(star)}
                            disabled={fetching}
                        >
                            <Star 
                                className={`w-8 h-8 ${
                                    star <= (hoverRating || rating) 
                                        ? "fill-yellow-400 text-yellow-400" 
                                        : "text-gray-300 dark:text-gray-600"
                                }`} 
                            />
                        </button>
                    ))}
                </div>

                <textarea
                    className="w-full p-3 border rounded-md mb-4 bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-primary/20 outline-none resize-none text-sm"
                    rows={4}
                    placeholder="Tell us more about your experience (optional)..."
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    disabled={fetching}
                />

                <div className="flex justify-end gap-3">
                    <Button variant="ghost" onClick={onClose} disabled={loading}>
                        Cancel
                    </Button>
                    <Button onClick={handleSubmit} disabled={loading || rating === 0 || fetching}>
                        {loading ? 'Submitting...' : 'Submit Feedback'}
                    </Button>
                </div>
            </div>
        </div>
    );
};
