import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from './api';

// Task API
export const taskAPI = {
    list: async (filters?: { status?: string; assigned_to_ve?: string }) => {
        const { data } = await api.get('/tasks', { params: filters });
        return data;
    },

    create: async (task: {
        title: string;
        description: string;
        assigned_to_ve?: string;
        priority?: string;
        due_date?: string;
    }) => {
        const { data } = await api.post('/tasks', task);
        return data;
    },

    update: async (id: string, updates: any) => {
        const { data } = await api.patch(`/tasks/${id}`, updates);
        return data;
    },

    addComment: async (taskId: string, content: string) => {
        const { data } = await api.post(`/tasks/${taskId}/comments`, { content });
        return data;
    },

    delete: async (id: string) => {
        await api.delete(`/tasks/${id}`);
    },
};

// React Query hooks
export const useTasks = (filters?: { status?: string; assigned_to_ve?: string }) => {
    return useQuery({
        queryKey: ['tasks', filters],
        queryFn: () => taskAPI.list(filters),
    });
};

export const useCreateTask = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: taskAPI.create,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
        },
    });
};

export const useUpdateTask = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, updates }: { id: string; updates: any }) =>
            taskAPI.update(id, updates),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
        },
    });
};

export const useDeleteTask = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: taskAPI.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
        },
    });
};
