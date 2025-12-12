import React, { useState } from 'react';
import { Card, Badge, Avatar } from '../ui';
import { Calendar, AlertCircle, MoreVertical, Edit, Trash2 } from 'lucide-react';

interface TaskCardProps {
    task: {
        id: string;
        title: string;
        description: string;
        priority: string;
        due_date?: string;
        assigned_to_ve?: string;
        status?: string;
        metadata?: {
            last_progress_message?: string;
            last_progress_timestamp?: string;
        };
    };
    isDragging?: boolean;
    onEdit?: (task: any) => void;
    onDelete?: (taskId: string) => void;
}

const priorityColors = {
    low: 'default',
    medium: 'info',
    high: 'warning',
    urgent: 'error',
} as const;

export const TaskCard: React.FC<TaskCardProps> = ({ task, isDragging, onEdit, onDelete }) => {
    const isOverdue = task.due_date && new Date(task.due_date) < new Date();
    const [showMenu, setShowMenu] = useState(false);

    return (
        <Card
            className={`cursor-grab active:cursor-grabbing transition-shadow relative group ${isDragging ? 'shadow-lg' : 'hover:shadow-md'
                }`}
        >
            <div className="p-4">
                <div className="mb-2 flex items-start justify-between">
                    <h4 className="font-medium text-slate-900 line-clamp-2 pr-6">{task.title}</h4>
                    <div className="flex flex-col items-end gap-1">
                        <Badge variant={priorityColors[task.priority as keyof typeof priorityColors]}>
                            {task.priority}
                        </Badge>
                    </div>
                </div>

                {/* Progress Indicator */}
                {task.status === 'in_progress' && task.metadata?.last_progress_message && (
                    <div className="mb-2 text-xs bg-blue-50 text-blue-700 p-1.5 rounded border border-blue-100 flex items-center gap-1">
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></div>
                        <span className="truncate">{task.metadata.last_progress_message}</span>
                    </div>
                )}

                {/* Action Menu */}
                <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                        className="p-1 hover:bg-slate-100 rounded-full text-slate-400 hover:text-slate-600"
                        onClick={(e) => {
                            e.stopPropagation();
                            setShowMenu(!showMenu);
                        }}
                    >
                        <MoreVertical className="h-4 w-4" />
                    </button>

                    {showMenu && (
                        <div className="absolute right-0 mt-1 w-32 bg-white rounded-md shadow-lg border border-slate-200 z-50 py-1">
                            <button
                                className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setShowMenu(false);
                                    onEdit?.(task);
                                }}
                            >
                                <Edit className="h-3 w-3" /> Edit
                            </button>
                            <button
                                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setShowMenu(false);
                                    if (window.confirm('Are you sure you want to delete this task?')) {
                                        onDelete?.(task.id);
                                    }
                                }}
                            >
                                <Trash2 className="h-3 w-3" /> Delete
                            </button>
                        </div>
                    )}
                </div>

                {task.description && (
                    <p className="mb-3 text-sm text-slate-600 line-clamp-2">{task.description}</p>
                )}

                <div className="flex items-center justify-between">
                    {task.due_date && (
                        <div className={`flex items-center gap-1 text-xs ${isOverdue ? 'text-red-600' : 'text-slate-500'}`}>
                            {isOverdue && <AlertCircle className="h-3 w-3" />}
                            <Calendar className="h-3 w-3" />
                            <span>{new Date(task.due_date).toLocaleDateString()}</span>
                        </div>
                    )}

                    {task.assigned_to_ve && (
                        <Avatar
                            fallback="VE"
                            size="sm"
                        />
                    )}
                </div>
            </div>

            {/* Overlay to close menu when clicking outside */}
            {showMenu && (
                <div
                    className="fixed inset-0 z-40"
                    onClick={(e) => {
                        e.stopPropagation();
                        setShowMenu(false);
                    }}
                />
            )}
        </Card>
    );
};
