import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal, Input, Textarea, Select, Button } from '../ui';
import { useUpdateTask } from '../../services/taskAPI';
import { customerAPI } from '../../services/api';
import { useToast } from '../ui/Toast';

const taskSchema = z.object({
    title: z.string().min(1, 'Title is required').max(200),
    description: z.string().min(1, 'Description is required'),
    priority: z.string(),
    due_date: z.string().optional(),
    assigned_to_ve: z.string().optional(),
});

type TaskFormData = z.infer<typeof taskSchema>;

interface TaskEditModalProps {
    isOpen: boolean;
    onClose: () => void;
    task: any;
}

export const TaskEditModal: React.FC<TaskEditModalProps> = ({ isOpen, onClose, task }) => {
    const { addToast } = useToast();
    const updateTask = useUpdateTask();
    const [ves, setVes] = useState<{ value: string; label: string }[]>([]);

    const {
        register,
        handleSubmit,
        formState: { errors },
        reset,
        setValue,
        watch,
    } = useForm<TaskFormData>({
        resolver: zodResolver(taskSchema),
        defaultValues: {
            title: '',
            description: '',
            priority: 'medium',
            due_date: '',
            assigned_to_ve: '',
        },
    });

    const priority = watch('priority');
    const assignedToVe = watch('assigned_to_ve');

    useEffect(() => {
        if (isOpen && task) {
            loadVEs();
            // Populate form with task data
            setValue('title', task.title);
            setValue('description', task.description);
            setValue('priority', task.priority);
            setValue('due_date', task.due_date ? task.due_date.split('T')[0] : '');
            setValue('assigned_to_ve', task.assigned_to_ve || '');
        }
    }, [isOpen, task, setValue]);

    const loadVEs = async () => {
        try {
            const data = await customerAPI.listVEs();
            if (data) {
                setVes(data.map((ve: any) => ({
                    value: ve.id,
                    label: ve.persona_name
                })));
            }
        } catch (error) {
            console.error('Failed to load VEs', error);
        }
    };

    const onSubmit = async (data: TaskFormData) => {
        try {
            await updateTask.mutateAsync({
                id: task.id,
                updates: data
            });
            addToast('success', 'Task updated successfully!');
            onClose();
        } catch (error) {
            addToast('error', 'Failed to update task');
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Edit Task"
            description="Update task details"
            size="lg"
        >
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <Input
                    label="Title"
                    placeholder="Enter task title"
                    error={errors.title?.message}
                    {...register('title')}
                />

                <Textarea
                    label="Description"
                    placeholder="Describe the task in detail"
                    rows={4}
                    error={errors.description?.message}
                    {...register('description')}
                />

                <div className="grid grid-cols-2 gap-4">
                    <Select
                        label="Priority"
                        value={priority}
                        onChange={(value) => setValue('priority', value as any)}
                        options={[
                            { value: 'low', label: 'Low' },
                            { value: 'medium', label: 'Medium' },
                            { value: 'high', label: 'High' },
                            { value: 'urgent', label: 'Urgent' },
                        ]}
                        error={errors.priority?.message as string | undefined}
                    />

                    <Select
                        label="Assign to VE"
                        value={assignedToVe || ''}
                        onChange={(value) => setValue('assigned_to_ve', value)}
                        options={[
                            { value: '', label: 'Unassigned' },
                            ...ves
                        ]}
                        error={errors.assigned_to_ve?.message as string | undefined}
                    />
                </div>

                <Input
                    label="Due Date"
                    type="date"
                    error={errors.due_date?.message}
                    {...register('due_date')}
                />

                <div className="flex justify-end gap-3 pt-4">
                    <Button type="button" variant="outline" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button type="submit" isLoading={updateTask.isPending}>
                        Save Changes
                    </Button>
                </div>
            </form>
        </Modal>
    );
};
