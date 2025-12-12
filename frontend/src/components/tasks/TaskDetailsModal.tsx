import React, { useEffect, useRef } from 'react';
import { Modal } from '../ui/Modal';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { useTaskComments, useProvideFeedback } from '../../services/taskAPI';
import { supabase } from '../../services/supabase';
import { useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { User, Bot, CheckCircle, AlertCircle } from 'lucide-react';

interface TaskDetailsModalProps {
    isOpen: boolean;
    onClose: () => void;
    task: any;
}

export const TaskDetailsModal: React.FC<TaskDetailsModalProps> = ({ isOpen, onClose, task }) => {
    const { data: comments = [], isLoading } = useTaskComments(task?.id || '');
    const queryClient = useQueryClient();
    const commentsEndRef = useRef<HTMLDivElement>(null);

    // Scroll to bottom of comments on new messages
    useEffect(() => {
        if (commentsEndRef.current) {
            commentsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [comments]);

    const isWaitingForInput = task?.status === 'waiting_for_input';
    const { mutate: provideFeedback, isPending: isProvidingFeedback } = useProvideFeedback();

    const handleFeedbackSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const form = e.target as HTMLFormElement;
        const input = form.elements.namedItem('feedback') as HTMLInputElement;
        const feedback = input.value;

        if (feedback.trim() && task) {
            provideFeedback({ taskId: task.id, feedback });
            input.value = '';
        }
    };

    // Real-time subscription for comments
    useEffect(() => {
        if (!isOpen || !task) return;

        const channel = supabase
            .channel(`comments:${task.id}`)
            .on(
                'postgres_changes',
                {
                    event: 'INSERT',
                    schema: 'public',
                    table: 'task_comments',
                    filter: `task_id=eq.${task.id}`,
                },
                (payload) => {
                    console.log('New comment received:', payload);
                    queryClient.invalidateQueries({ queryKey: ['task-comments', task.id] });
                }
            )
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, [isOpen, task, queryClient]);

    if (!task) return null;

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'success';
            case 'in_progress': return 'primary'; // Use 'primary' or 'info' depending on Badge variants
            case 'waiting_for_input': return 'warning';
            case 'failed': return 'error';
            default: return 'default';
        }
    };

    // Check for progress message in metadata
    const progressMessage = task.metadata?.last_progress_message;
    const progressTimestamp = task.metadata?.last_progress_timestamp;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Task Details"
            description={task.id} // Show ID for reference
            size="lg"
        >
            <div className="space-y-6">
                {/* Header Info */}
                <div className="flex justify-between items-start border-b pb-4">
                    <div>
                        <h3 className="text-xl font-bold text-slate-900">{task.title}</h3>
                        <div className="flex gap-2 mt-2">
                            <Badge variant={getStatusColor(task.status) as any}>
                                {task.status.replace('_', ' ').toUpperCase()}
                            </Badge>
                            <Badge variant="outline">{task.priority.toUpperCase()}</Badge>
                        </div>
                    </div>
                </div>

                {/* Progress Alert */}
                {task.status === 'in_progress' && progressMessage && (
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-3 flex items-start gap-3">
                        <div className="animate-pulse bg-blue-500 w-2 h-2 rounded-full mt-2"></div>
                        <div>
                            <p className="text-sm font-medium text-blue-800">Current Activity</p>
                            <p className="text-sm text-blue-600">{progressMessage}</p>
                            {progressTimestamp && (
                                <p className="text-xs text-blue-400 mt-1">
                                    Last update: {new Date(progressTimestamp).toLocaleTimeString()}
                                </p>
                            )}
                        </div>
                    </div>
                )}

                {/* Waiting For Input Alert */}
                {isWaitingForInput && (
                    <div className="bg-amber-50 border border-amber-200 rounded-md p-4 space-y-3">
                        <div className="flex items-center gap-2 text-amber-800 font-medium">
                            <span className="relative flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
                            </span>
                            Agent needs your input
                        </div>
                        <p className="text-sm text-amber-700">
                            {progressMessage || "The agent has paused and needs your feedback to continue."}
                        </p>
                        <form onSubmit={handleFeedbackSubmit} className="flex gap-2">
                            <input
                                name="feedback"
                                type="text"
                                className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm p-2 bg-white"
                                placeholder="Type your reply here..."
                                autoFocus
                            />
                            <Button type="submit" variant="primary" isLoading={isProvidingFeedback}>
                                Reply
                            </Button>
                        </form>
                    </div>
                )}

                {/* Description */}
                <div>
                    <h4 className="font-semibold text-slate-700 mb-2">Description</h4>
                    <div className="bg-slate-50 p-3 rounded-md text-slate-600 text-sm whitespace-pre-wrap">
                        {task.description}
                    </div>
                </div>

                {/* Results / Comments Section */}
                <div>
                    <h4 className="font-semibold text-slate-700 mb-2">Activity Log & Results</h4>
                    <div className="bg-white border rounded-lg h-64 overflow-y-auto p-4 space-y-4">
                        {isLoading ? (
                            <div className="flex justify-center py-4">
                                <div className="animate-spin h-5 w-5 border-2 border-indigo-500 rounded-full border-t-transparent"></div>
                            </div>
                        ) : comments.length === 0 ? (
                            <p className="text-center text-slate-400 text-sm py-4">No activity yet.</p>
                        ) : (
                            comments.map((comment: any) => (
                                <div key={comment.id} className={`flex gap-3 ${comment.author_type === 'user' ? 'flex-row-reverse' : ''}`}>
                                    <div className={`mt-1 h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${comment.author_type === 'user' ? 'bg-indigo-100 text-indigo-600' :
                                        comment.author_type === 'system' ? 'bg-slate-100 text-slate-600' : 'bg-green-100 text-green-600'
                                        }`}>
                                        {comment.author_type === 'user' ? <User size={16} /> :
                                            comment.author_type === 'system' ? <AlertCircle size={16} /> : <Bot size={16} />}
                                    </div>
                                    <div className={`flex flex-col max-w-[80%] ${comment.author_type === 'user' ? 'items-end' : 'items-start'}`}>
                                        <span className="text-xs text-slate-400 mb-1">
                                            {comment.author_type === 've' ? 'Virtual Employee' :
                                                comment.author_type === 'system' ? 'System' : 'You'} • {format(new Date(comment.created_at), 'MMM d, h:mm a')}
                                        </span>
                                        <div className={`p-3 rounded-lg text-sm ${comment.author_type === 'user' ? 'bg-indigo-600 text-white' :
                                            comment.author_type === 'system' ? 'bg-slate-100 text-slate-700 border-l-4 border-slate-300' : 'bg-green-50 text-slate-800 border border-green-100'
                                            }`}>
                                            {comment.content}
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                        <div ref={commentsEndRef} />
                    </div>
                </div>

                <div className="flex justify-end pt-4">
                    <Button variant="outline" onClick={onClose}>Close</Button>
                </div>
            </div>
        </Modal>
    );
};
