import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { Plus } from 'lucide-react';
import { useTasks, useUpdateTask, useDeleteTask } from '../services/taskAPI';
import { Button, Badge } from '../components/ui';
import { PageLayout } from '../components/layout';
import { TaskCreateModal } from '../components/tasks/TaskCreateModal';
import { TaskEditModal } from '../components/tasks/TaskEditModal';
import { TaskWorkspace } from '../components/workspace/TaskWorkspace';
import { TaskCard } from '../components/tasks/TaskCard';
import { useToast } from '../components/ui/Toast';
import { supabase } from '../services/supabase';
import { useQueryClient } from '@tanstack/react-query';

const columns = [
    { id: 'pending', title: 'To Do' },
    { id: 'in_progress', title: 'In Progress' },
    { id: 'review', title: 'Review' },
    { id: 'completed', title: 'Completed' },
];

const Tasks: React.FC = () => {
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [editingTask, setEditingTask] = useState<any>(null);
    const [viewingTask, setViewingTask] = useState<any>(null);
    const { data: tasks = [], isLoading } = useTasks();
    const updateTask = useUpdateTask();
    const deleteTask = useDeleteTask();
    const { addToast } = useToast();
    const queryClient = useQueryClient();

    // Real-time task updates
    useEffect(() => {
        const channel = supabase
            .channel('public:tasks')
            .on(
                'postgres_changes',
                {
                    event: '*',
                    schema: 'public',
                    table: 'tasks',
                },
                (payload) => {
                    console.log('Task update received:', payload);
                    queryClient.invalidateQueries({ queryKey: ['tasks'] });
                }
            )
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, [queryClient]);

    const tasksByStatus = columns.reduce((acc, column) => {
        if (column.id === 'in_progress') {
            // Group 'planning' and 'waiting_for_input' into 'in_progress' column for now
            acc[column.id] = tasks.filter((task: any) =>
                task.status === 'in_progress' ||
                task.status === 'planning' ||
                task.status === 'waiting_for_input'
            );
        } else {
            acc[column.id] = tasks.filter((task: any) => task.status === column.id);
        }
        return acc;
    }, {} as Record<string, any[]>);

    const handleDragEnd = (result: DropResult) => {
        const { destination, source, draggableId } = result;

        if (!destination) return;
        if (destination.droppableId === source.droppableId && destination.index === source.index) return;

        const newStatus = destination.droppableId;
        updateTask.mutate({
            id: draggableId,
            updates: { status: newStatus },
        });
    };

    const handleEdit = (task: any) => {
        setEditingTask(task);
    };

    const handleView = (task: any) => {
        setViewingTask(task);
    };

    const handleDelete = async (taskId: string) => {
        try {
            await deleteTask.mutateAsync(taskId);
            addToast('success', 'Task deleted successfully');
        } catch (error) {
            addToast('error', 'Failed to delete task');
        }
    };

    if (isLoading) {
        return (
            <PageLayout title="Tasks">
                <div className="flex items-center justify-center h-64">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
                </div>
            </PageLayout>
        );
    }

    return (
        <PageLayout title="Tasks">
            <div className="mb-6">
                <Button onClick={() => setIsCreateModalOpen(true)}>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Task
                </Button>
            </div>

            <DragDropContext onDragEnd={handleDragEnd}>
                <div className="grid grid-cols-4 gap-4">
                    {columns.map((column) => (
                        <div key={column.id} className="flex flex-col">
                            <div className="mb-4 flex items-center justify-between">
                                <h3 className="font-semibold text-slate-900">{column.title}</h3>
                                <Badge variant="default">{tasksByStatus[column.id]?.length || 0}</Badge>
                            </div>

                            <Droppable droppableId={column.id}>
                                {(provided, snapshot) => (
                                    <div
                                        ref={provided.innerRef}
                                        {...provided.droppableProps}
                                        className={`flex-1 rounded-lg p-2 transition-colors ${snapshot.isDraggingOver ? 'bg-indigo-50' : 'bg-slate-50'
                                            }`}
                                        style={{ minHeight: '500px' }}
                                    >
                                        <div className="space-y-2">
                                            {tasksByStatus[column.id]?.map((task: any, index: number) => (
                                                <Draggable key={task.id} draggableId={task.id} index={index}>
                                                    {(provided, snapshot) => (
                                                        <div
                                                            ref={provided.innerRef}
                                                            {...provided.draggableProps}
                                                            {...provided.dragHandleProps}
                                                            onClick={() => handleView(task)}
                                                        >
                                                            <TaskCard
                                                                task={task}
                                                                isDragging={snapshot.isDragging}
                                                                onEdit={handleEdit}
                                                                onDelete={handleDelete}
                                                            />
                                                        </div>
                                                    )}
                                                </Draggable>
                                            ))}
                                            {provided.placeholder}
                                        </div>
                                    </div>
                                )}
                            </Droppable>
                        </div>
                    ))}
                </div>
            </DragDropContext>

            <TaskCreateModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
            />

            {editingTask && (
                <TaskEditModal
                    isOpen={!!editingTask}
                    onClose={() => setEditingTask(null)}
                    task={editingTask}
                />
            )}

            {viewingTask && (
                <TaskWorkspace
                    task={viewingTask}
                    onClose={() => setViewingTask(null)}
                />
            )}
        </PageLayout>
    );
};

export default Tasks;
