import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from './api';

// Message API
export const messageAPI = {
    inbox: async (folder: string = 'inbox') => {
        const { data } = await api.get('/messages/inbox', { params: { folder } });
        return data;
    },

    thread: async (threadId: string) => {
        const { data } = await api.get(`/messages/thread/${threadId}`);
        return data;
    },

    send: async (message: {
        to_ve_id: string;
        subject: string;
        content: string;
        thread_id?: string;
        replied_to_id?: string;
    }) => {
        const { data } = await api.post('/messages/send', message);
        return data;
    },

    markAsRead: async (messageId: string) => {
        const { data } = await api.patch(`/messages/${messageId}/read`);
        return data;
    },
};

// React Query hooks
export const useMessages = (folder: string = 'inbox') => {
    return useQuery({
        queryKey: ['messages', folder],
        queryFn: () => messageAPI.inbox(folder),
    });
};

export const useThread = (threadId: string | null) => {
    return useQuery({
        queryKey: ['thread', threadId],
        queryFn: () => messageAPI.thread(threadId!),
        enabled: !!threadId,
    });
};

export const useSendMessage = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: messageAPI.send,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['messages'] });
        },
    });
};
