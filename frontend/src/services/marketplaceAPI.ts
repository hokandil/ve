import api from './api';

export interface VETemplate {
    id: string;
    name: string;
    role: string;
    department: string;
    seniority_level: string;
    description: string;
    capabilities: Record<string, any>;
    tools: Record<string, any>;
    pricing_monthly: number;
    status: string;
    created_at: string;
    updated_at: string;
}

export interface MarketplaceListResponse {
    items: VETemplate[];
    total: number;
    page: number;
    page_size: number;
}

export interface HireVERequest {
    ve_id: string;
    persona_name?: string;
    persona_email?: string;
    position_x?: number;
    position_y?: number;
}

export const marketplaceAPI = {
    list: async (params?: {
        department?: string;
        seniority_level?: string;
        status?: string;
        page?: number;
        page_size?: number;
    }): Promise<MarketplaceListResponse> => {
        const { data } = await api.get('/marketplace/ves', { params });
        return data;
    },

    getVE: async (veId: string): Promise<VETemplate> => {
        const { data } = await api.get(`/marketplace/ves/${veId}`);
        return data;
    },

    hireVE: async (veId: string, request: Omit<HireVERequest, 've_id'>) => {
        const { data } = await api.post(`/marketplace/ves/${veId}/hire`, request);
        return data;
    },
};
