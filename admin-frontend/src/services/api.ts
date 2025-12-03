import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

// Create axios instance
const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const api = apiClient;

export const legacyAPI = {
    kagent: {
        listAgents: async () => {
            const res = await fetch(`${API_URL}/marketplace/kagent/agents`);
            if (!res.ok) throw new Error('Failed to fetch kagent agents');
            return res.json();
        },
        listRegistryAgents: async () => {
            const res = await fetch(`${API_URL}/marketplace/registry/agents`);
            if (!res.ok) throw new Error('Failed to fetch registry agents');
            return res.json();
        }
    },
    templates: {
        list: async () => {
            const res = await fetch(`${API_URL}/marketplace/ves`);
            if (!res.ok) throw new Error('Failed to fetch templates');
            const data = await res.json();
            return data.items || [];
        },

        create: async (data: any) => {
            const res = await fetch(`${API_URL}/marketplace/ves`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!res.ok) throw new Error('Failed to create template');
            return res.json();
        },

        update: async (id: string, data: any) => {
            // TODO: Implement update endpoint in backend
            console.log('Update not implemented yet');
        },

        delete: async (id: string) => {
            // TODO: Implement delete endpoint in backend
            console.log('Delete not implemented yet');
        }
    }
};
