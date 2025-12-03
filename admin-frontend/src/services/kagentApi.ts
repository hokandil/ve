import axios, { AxiosInstance } from 'axios';

// KAgent API types
export interface KAgentAgent {
    apiVersion: string;
    kind: string;
    metadata: {
        name: string;
        namespace: string;
        labels?: Record<string, string>;
        annotations?: Record<string, string>;
        creationTimestamp?: string;
    };
    spec: {
        description: string;
        type: 'Declarative' | 'BYO';
        declarative?: {
            modelConfig: string;
            systemMessage: string;
        };
        tools?: Array<{
            type: string;
            mcpServer?: {
                apiGroup: string;
                kind: string;
                name: string;
            };
            toolNames?: string[];
        }>;
    };
    status?: {
        conditions?: Array<{
            type: string;
            status: string;
            message?: string;
            reason?: string;
            lastTransitionTime?: string;
        }>;
        configHash?: string;
        observedGeneration?: number;
    };
}

export interface KAgentAgentList {
    apiVersion: string;
    kind: string;
    items: KAgentAgent[];
    metadata?: {
        continue?: string;
        resourceVersion?: string;
    };
}

class KAgentAPIClient {
    private client: AxiosInstance;

    constructor(baseURL: string = process.env.REACT_APP_KAGENT_API_URL || 'http://localhost:8080') {
        this.client = axios.create({
            baseURL,
            headers: {
                'Content-Type': 'application/json',
            },
        });
    }

    /**
     * List all agents from KAgent
     */
    async listAgents(namespace: string = 'default'): Promise<KAgentAgent[]> {
        try {
            const response = await this.client.get<KAgentAgentList>(
                `/apis/kagent.dev/v1alpha2/namespaces/${namespace}/agents`
            );
            return response.data.items || [];
        } catch (error) {
            console.error('Error listing agents from KAgent:', error);
            throw error;
        }
    }

    /**
     * Get a specific agent by name
     */
    async getAgent(name: string, namespace: string = 'default'): Promise<KAgentAgent> {
        try {
            const response = await this.client.get<KAgentAgent>(
                `/apis/kagent.dev/v1alpha2/namespaces/${namespace}/agents/${name}`
            );
            return response.data;
        } catch (error) {
            console.error(`Error getting agent ${name} from KAgent:`, error);
            throw error;
        }
    }

    /**
     * Get agent status
     */
    async getAgentStatus(name: string, namespace: string = 'default'): Promise<KAgentAgent['status']> {
        try {
            const agent = await this.getAgent(name, namespace);
            return agent.status;
        } catch (error) {
            console.error(`Error getting agent status for ${name}:`, error);
            throw error;
        }
    }

    /**
     * Check if agent is ready
     */
    isAgentReady(agent: KAgentAgent): boolean {
        if (!agent.status?.conditions) return false;

        const readyCondition = agent.status.conditions.find(c => c.type === 'Ready');
        return readyCondition?.status === 'True';
    }

    /**
     * Extract tools from agent
     */
    getAgentTools(agent: KAgentAgent): string[] {
        if (!agent.spec.tools) return [];

        const tools: string[] = [];
        agent.spec.tools.forEach(tool => {
            if (tool.toolNames) {
                tools.push(...tool.toolNames);
            }
        });

        return tools;
    }

    /**
     * Get agent description
     */
    getAgentDescription(agent: KAgentAgent): string {
        return agent.spec.description || 'No description available';
    }

    /**
     * Get agent system message (for Declarative agents)
     */
    getAgentSystemMessage(agent: KAgentAgent): string | null {
        if (agent.spec.type === 'Declarative' && agent.spec.declarative) {
            return agent.spec.declarative.systemMessage;
        }
        return null;
    }
}

// Export singleton instance
export const kagentApi = new KAgentAPIClient();

// Export class for testing
export default KAgentAPIClient;
