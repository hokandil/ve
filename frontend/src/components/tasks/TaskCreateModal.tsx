import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal, Input, Textarea, Select, Button } from '../ui';
import { useCreateTask } from '../../services/taskAPI';
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

interface TaskCreateModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const TaskCreateModal: React.FC<TaskCreateModalProps> = ({ isOpen, onClose }) => {
    const { addToast } = useToast();
    const createTask = useCreateTask();
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
            priority: 'medium',
        },
    });

    const priority = watch('priority');
    const assignedToVe = watch('assigned_to_ve');

    useEffect(() => {
        if (isOpen) {
            loadVEs();
        }
    }, [isOpen]);

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
            await createTask.mutateAsync(data);
            addToast('success', 'Task created successfully!');
            reset();
            onClose();
        } catch (error) {
            addToast('error', 'Failed to create task');
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Create New Task"
            description="Add a new task to your workflow"
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
                    <Button type="submit" isLoading={createTask.isPending}>
                        Create Task
                    </Button>
                </div>
            </form>
        </Modal>
    );
};
