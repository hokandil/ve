import React, { useState, useEffect, useRef } from 'react';
import { useTaskComments, useProvideFeedback, useTaskPlan, useApproveTaskPlan } from '../../services/taskAPI';
import { supabase } from '../../services/supabase';
import { useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { User, Bot, CheckCircle, AlertCircle, FileText, Layout, MessageSquare, Clock, Send, PlayCircle, ShieldCheck, Maximize2, X } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface TaskWorkspaceProps {
    task: any;
    onClose: () => void;
}

export const TaskWorkspace: React.FC<TaskWorkspaceProps> = ({ task, onClose }) => {
    const [activeTab, setActiveTab] = useState<'plan' | 'deliverables' | 'context'>('plan');
    const { data: comments = [], isLoading: isLoadingComments } = useTaskComments(task?.id || '');
    const { data: plan, isLoading: isLoadingPlan } = useTaskPlan(task?.id || '');
    const { mutate: approvePlan, isPending: isApproving } = useApproveTaskPlan();
    const queryClient = useQueryClient();
    const commentsEndRef = useRef<HTMLDivElement>(null);

    // Scroll chat to bottom
    useEffect(() => {
        if (commentsEndRef.current) {
            commentsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [comments]);

    // Real-time comments subscription
    useEffect(() => {
        if (!task) return;
        const channel = supabase
            .channel(`comments:${task.id}`)
            .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'task_comments', filter: `task_id=eq.${task.id}` },
                () => queryClient.invalidateQueries({ queryKey: ['task-comments', task.id] }))
            .subscribe();
        return () => { supabase.removeChannel(channel); };
    }, [task, queryClient]);

    // Real-time task update subscription (for status/phase changes)
    useEffect(() => {
        if (!task) return;
        const channel = supabase
            .channel(`task-updates:${task.id}`)
            .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'tasks', filter: `id=eq.${task.id}` },
                () => {
                    queryClient.invalidateQueries({ queryKey: ['tasks'] });
                    // Also refetch plan if it might have changed
                    queryClient.invalidateQueries({ queryKey: ['task-plan', task.id] });
                })
            .subscribe();
        return () => { supabase.removeChannel(channel); };
    }, [task, queryClient]);


    const isWaitingForInput = task?.status === 'waiting_for_input';
    const isPlanning = task?.current_phase === 'planning';
    const progressMessage = task?.metadata?.last_progress_message;

    // Feedback Logic
    const { mutate: provideFeedback, isPending: isProvidingFeedback } = useProvideFeedback();
    const [feedbackInput, setFeedbackInput] = useState('');
    const handleFeedbackSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (feedbackInput.trim() && task) {
            provideFeedback({ taskId: task.id, feedback: feedbackInput });
            setFeedbackInput('');
        }
    };

    if (!task) return null;

    return (
        <div className="fixed inset-0 z-50 bg-white flex flex-col">
            {/* Header */}
            <header className="h-16 border-b flex items-center justify-between px-6 bg-slate-50">
                <div className="flex items-center gap-4">
                    <div className="bg-indigo-600 p-2 rounded-lg text-white">
                        <Bot size={20} />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold text-slate-800 line-clamp-1">{task.title}</h1>
                        <div className="flex items-center gap-2 text-xs text-slate-500">
                            <span className="flex items-center gap-1">
                                <Clock size={12} /> {format(new Date(task.created_at), 'MMM d')}
                            </span>
                            <span>•</span>
                            <Badge variant={task.status === 'completed' ? 'success' : task.status === 'waiting_for_input' ? 'warning' : 'default'}>
                                {task.status.toUpperCase()}
                            </Badge>
                            {isPlanning && <Badge variant="warning">PLANNING PHASE</Badge>}
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <Button variant="outline" onClick={onClose}><X size={16} className="mr-2" />Close</Button>
                </div>
            </header>

            {/* Main Content (Split View) */}
            <div className="flex-1 flex overflow-hidden">

                {/* Left Panel: Activity Feed / Chat (35%) */}
                <div className="w-[400px] border-r flex flex-col bg-slate-50">
                    <div className="p-4 border-b bg-white">
                        <h3 className="font-semibold text-slate-700 flex items-center gap-2">
                            <MessageSquare size={16} /> Activity & Chat
                        </h3>
                    </div>

                    {/* Chat Area */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {isLoadingComments ? (
                            <div className="text-center py-4 text-slate-400">Loading history...</div>
                        ) : comments.map((comment: any) => (
                            <div key={comment.id} className={`flex gap-3 ${comment.author_type === 'user' ? 'flex-row-reverse' : ''}`}>
                                <div className={`mt-1 h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${comment.author_type === 'user' ? 'bg-indigo-100 text-indigo-600' :
                                    comment.author_type === 'system' ? 'bg-slate-200 text-slate-600' : 'bg-green-100 text-green-600'
                                    }`}>
                                    {comment.author_type === 'user' ? <User size={14} /> :
                                        comment.author_type === 'system' ? <AlertCircle size={14} /> : <Bot size={14} />}
                                </div>
                                <div className={`flex flex-col max-w-[85%] ${comment.author_type === 'user' ? 'items-end' : 'items-start'}`}>
                                    <div className={`p-3 rounded-2xl text-sm shadow-sm ${comment.author_type === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' :
                                        comment.author_type === 'system' ? 'bg-slate-200 text-slate-700 text-xs italic' : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none'
                                        }`}>
                                        {comment.content}
                                    </div>
                                    <span className="text-[10px] text-slate-400 mt-1 px-1">
                                        {format(new Date(comment.created_at), 'h:mm a')}
                                    </span>
                                </div>
                            </div>
                        ))}
                        <div ref={commentsEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-4 bg-white border-t">
                        {isWaitingForInput && (
                            <div className="mb-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 flex items-center gap-2 animate-pulse">
                                <AlertCircle size={16} /> Agent needs your input!
                            </div>
                        )}
                        <form onSubmit={handleFeedbackSubmit} className="flex gap-2">
                            <input
                                value={feedbackInput}
                                onChange={(e) => setFeedbackInput(e.target.value)}
                                className="flex-1 border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                                placeholder={isWaitingForInput ? "Type your reply..." : "Send a message..."}
                            />
                            <Button type="submit" variant="primary" disabled={!feedbackInput.trim() || isProvidingFeedback}>
                                <Send size={16} />
                            </Button>
                        </form>
                    </div>
                </div>

                {/* Right Panel: Workspace (65%) */}
                <div className="flex-1 flex flex-col bg-slate-100 h-full overflow-hidden">
                    {/* Tabs */}
                    <div className="bg-white border-b px-6 flex gap-6">
                        <button
                            onClick={() => setActiveTab('plan')}
                            className={`py-4 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'plan' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700'
                                }`}
                        >
                            <Layout size={16} /> Execution Plan
                        </button>
                        <button
                            onClick={() => setActiveTab('deliverables')}
                            className={`py-4 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'deliverables' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700'
                                }`}
                        >
                            <FileText size={16} /> Deliverables
                        </button>
                        <button
                            onClick={() => setActiveTab('context')}
                            className={`py-4 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'context' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700'
                                }`}
                        >
                            <ShieldCheck size={16} /> Context & Files
                        </button>
                    </div>

                    {/* Content */}
                    <div className="flex-1 overflow-y-auto p-8">
                        {activeTab === 'plan' && (
                            <div className="max-w-3xl mx-auto space-y-6">
                                {isPlanning && !plan ? (
                                    <div className="bg-white p-12 rounded-xl shadow-sm border border-slate-200 text-center">
                                        <div className="animate-spin h-8 w-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                                        <h3 className="text-lg font-semibold text-slate-800">Drafting Plan...</h3>
                                        <p className="text-slate-500 mt-2">The agent is analyzing your request and generating a strategy.</p>
                                    </div>
                                ) : plan ? (
                                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                                        <div className="p-6 border-b bg-indigo-50/50 flex justify-between items-center">
                                            <div>
                                                <h2 className="text-lg font-bold text-slate-800">Proposed Strategy</h2>
                                                <p className="text-sm text-slate-500">{plan.initial_thought}</p>
                                            </div>
                                            {plan.status === 'draft' && isPlanning ? (
                                                <Button
                                                    variant="primary"
                                                    className="bg-green-600 hover:bg-green-700 focus-visible:ring-green-500"
                                                    onClick={() => approvePlan({ taskId: task.id })}
                                                    isLoading={isApproving}
                                                >
                                                    <CheckCircle size={16} className="mr-2" />
                                                    Approve Plan
                                                </Button>
                                            ) : (
                                                <Badge variant="success">APPROVED</Badge>
                                            )}
                                        </div>
                                        <div className="p-6 space-y-8">
                                            {/* Steps */}
                                            <div>
                                                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4">Execution Steps</h3>
                                                <div className="space-y-4">
                                                    {plan.steps.map((step: any, idx: number) => (
                                                        <div key={idx} className="flex gap-4">
                                                            <div className="flex flex-col items-center">
                                                                <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center font-bold text-slate-600 text-sm">
                                                                    {idx + 1}
                                                                </div>
                                                                {idx < plan.steps.length - 1 && <div className="w-0.5 h-full bg-slate-200 my-1"></div>}
                                                            </div>
                                                            <div className="flex-1 pb-4">
                                                                <div className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow">
                                                                    <div className="flex justify-between items-start mb-2">
                                                                        <p className="font-medium text-slate-800">{step.description}</p>
                                                                        <Badge variant="outline">{step.output_type}</Badge>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Details Grid */}
                                            <div className="grid grid-cols-2 gap-6 pt-6 border-t">
                                                <div>
                                                    <h4 className="text-sm font-semibold text-slate-700 mb-2">Timeline</h4>
                                                    <div className="bg-slate-50 p-3 rounded-lg border text-sm text-slate-600 flex items-center gap-2">
                                                        <Clock size={16} /> {plan.timeline}
                                                    </div>
                                                </div>
                                                <div>
                                                    <h4 className="text-sm font-semibold text-slate-700 mb-2">Resources</h4>
                                                    <div className="flex flex-wrap gap-2">
                                                        {plan.resources.map((res: string, i: number) => (
                                                            <span key={i} className="bg-slate-100 text-slate-600 px-2 py-1 rounded text-xs border">
                                                                {res}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="text-center py-20">
                                        <div className="mx-auto w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                                            <Layout size={32} className="text-slate-400" />
                                        </div>
                                        <h3 className="text-lg font-medium text-slate-900">No Plan Yet</h3>
                                        <p className="text-slate-500 mt-2">The plan will appear here once the agent starts working.</p>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeTab === 'deliverables' && (
                            <div className="text-center py-20">
                                <div className="mx-auto w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                                    <FileText size={32} className="text-slate-400" />
                                </div>
                                <h3 className="text-lg font-medium text-slate-900">No Deliverables Yet</h3>
                                <p className="text-slate-500 mt-2">Outputs generated by the agent will be listed here.</p>
                            </div>
                        )}

                        {activeTab === 'context' && (
                            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                                <h3 className="font-bold text-slate-800 mb-4">Task Description</h3>
                                <div className="text-slate-600 whitespace-pre-wrap">{task.description}</div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
