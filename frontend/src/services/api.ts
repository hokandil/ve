import axios from 'axios';
import { supabase } from './supabase';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token to requests
api.interceptors.request.use(async (config) => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
});

// Marketplace API
export const marketplaceAPI = {
    list: async (params?: any) => {
        const response = await api.get('/marketplace/ves', { params });
        return response.data;
    },
    get: async (id: string) => {
        const response = await api.get(`/marketplace/ves/${id}`);
        return response.data;
    }
};

// Customer API
export const customerAPI = {
    hire: async (marketplaceAgentId: string, personaName?: string, personaEmail?: string, positionX?: number, positionY?: number) => {
        const response = await api.post('/customer/ves', {
            marketplace_agent_id: marketplaceAgentId,
            persona_name: personaName,
            persona_email: personaEmail,
            position_x: positionX,
            position_y: positionY
        });
        return response.data;
    },

    unhireVE: async (veId: string) => {
        await api.delete(`/customer/ves/${veId}`);
    },

    listVEs: async () => {
        const response = await api.get('/customer/ves');
        return response.data;
    },

    updateVE: async (veId: string, data: { persona_name?: string }) => {
        const response = await api.patch(`/customer/ves/${veId}`, data);
        return response.data;
    }
};

// Chat API
export const chatAPI = {
    streamMessage: async (
        veId: string,
        content: string,
        onEvent: (event: any) => void,
        onError?: (error: Error) => void,
        onComplete?: () => void
    ) => {
        try {
            const { data: { session } } = await supabase.auth.getSession();
            const token = session?.access_token;

            const response = await fetch(`${API_URL}/messages/ves/${veId}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': token ? `Bearer ${token}` : '',
                },
                body: JSON.stringify({
                    content,
                    subject: 'Chat'
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (!reader) {
                throw new Error('No response body');
            }

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            onEvent(data);
                        } catch (e) {
                            console.error('Failed to parse SSE data:', e);
                        }
                    }
                }
            }

            if (onComplete) {
                onComplete();
            }
        } catch (error) {
            console.error('Stream error:', error);
            if (onError) {
                onError(error as Error);
            }
        }
    },

    sendMessage: async (veId: string, content: string) => {
        const response = await api.post(`/messages/ves/${veId}/chat`, {
            content,
            subject: "Chat"
        });
        return response.data;
    },

    getHistory: async (veId: string) => {
        const response = await api.get(`/messages/ves/${veId}/history`);
        return response.data;
    }
};

// Auth API
export const authAPI = {
    login: async (email: string, password: string) => {
        const response = await api.post('/auth/login', {
            email,
            password,
        });
        return response.data;
    },

    signup: async (email: string, password: string, companyName: string, industry?: string, companySize?: string) => {
        const response = await api.post('/auth/signup', {
            email,
            password,
            company_name: companyName,
            industry,
            company_size: companySize,
        });
        return response.data;
    }
};

export default api;
