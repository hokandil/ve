import { api } from './api';

export interface Agent {
    id: string;
    name: string;
    namespace: string;
    description: string;
    version: string;
    type: string;
    tools: string[];
    labels: Record<string, string>;
    annotations: Record<string, string>;
    created_at: string;
}

export interface MCPServer {
    id: string;
    name: string;
    namespace: string;
    description: string;
    url: string;
    tools: string[];
    created_at: string;
}

export interface Tool {
    name: string;
    description: string;
    mcp_server: string;
    type: string;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export const discoveryAPI = {
    // List agents from KAgent
    listAgents: async (params?: {
        namespace?: string;
        search?: string;
        department?: string;
        page?: number;
        page_size?: number;
    }): Promise<PaginatedResponse<Agent>> => {
        const response = await api.get('/discovery/agents', { params });
        return response.data;
    },

    // Get agent details
    getAgent: async (agentId: string, namespace: string = 'default'): Promise<Agent> => {
        const response = await api.get(`/discovery/agents/${agentId}`, {
            params: { namespace }
        });
        return response.data;
    },

    // List MCP servers
    listMCPs: async (params?: {
        namespace?: string;
        search?: string;
        page?: number;
        page_size?: number;
    }): Promise<PaginatedResponse<MCPServer>> => {
        const response = await api.get('/discovery/mcps', { params });
        return response.data;
    },

    // List tools
    listTools: async (params?: {
        search?: string;
        mcp_server?: string;
        page?: number;
        page_size?: number;
    }): Promise<PaginatedResponse<Tool>> => {
        const response = await api.get('/discovery/tools', { params });
        return response.data;
    },

    // Import agent from KAgent
    importAgent: async (
        agentId: string,
        params: {
            namespace?: string;
            pricing_monthly?: number;
            token_billing?: string;
            estimated_usage?: string;
        }
    ): Promise<{
        success: boolean;
        ve_id: string;
        agent_id: string;
        message: string;
    }> => {
        const response = await api.post(`/discovery/import/agent/${agentId}`, null, {
            params
        });
        return response.data;
    },
};
