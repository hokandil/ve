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

    getComments: async (taskId: string) => {
        const { data } = await api.get(`/tasks/${taskId}/comments`);
        return data;
    },

    provideFeedback: async (taskId: string, feedback: string) => {
        const { data } = await api.post(`/tasks/${taskId}/feedback`, { content: feedback });
        return data;
    },

    getTaskPlan: async (taskId: string) => {
        const { data } = await api.get(`/tasks/${taskId}/plan`);
        return data as TaskPlan;
    },

    approveTaskPlan: async (taskId: string) => {
        const { data } = await api.post(`/tasks/${taskId}/plan/approve`, {});
        return data;
    },
};

export interface TaskStep {
    output_type: string;
    description: string;
}

export interface TaskPlan {
    id: string;
    steps: TaskStep[];
    timeline: string;
    resources: string[];
    initial_thought: string;
    status: 'draft' | 'approved';
    created_at: string;
}

// React Query hooks
export const useTasks = (filters?: { status?: string; assigned_to_ve?: string }) => {
    return useQuery({
        queryKey: ['tasks', filters],
        queryFn: () => taskAPI.list(filters),
    });
};

export const useTaskComments = (taskId: string) => {
    return useQuery({
        queryKey: ['task-comments', taskId],
        queryFn: () => taskAPI.getComments(taskId),
        enabled: !!taskId,
    });
};

export const useTaskPlan = (taskId: string) => {
    return useQuery({
        queryKey: ['task-plan', taskId],
        queryFn: () => taskAPI.getTaskPlan(taskId),
        enabled: !!taskId,
        retry: 1, // Don't retry too much if 404
    });
};

export const useProvideFeedback = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ taskId, feedback }: { taskId: string, feedback: string }) =>
            taskAPI.provideFeedback(taskId, feedback),
        onSuccess: (_, { taskId }) => {
            queryClient.invalidateQueries({ queryKey: ['task-comments', taskId] });
        }
    });
};

export const useApproveTaskPlan = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ taskId }: { taskId: string }) => taskAPI.approveTaskPlan(taskId),
        onSuccess: (_, { taskId }) => {
            queryClient.invalidateQueries({ queryKey: ['task-plan', taskId] });
            queryClient.invalidateQueries({ queryKey: ['tasks'] }); // Refresh task status
        }
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
