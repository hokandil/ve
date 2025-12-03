import api from './api';

export interface BillingUsage {
    total_tokens: number;
    total_cost: number;
    period_start: string;
    period_end: string;
    usage_by_ve: Array<{
        ve_id: string;
        ve_name: string;
        tokens: number;
        cost: number;
    }>;
    usage_by_operation: Array<{
        operation: string;
        tokens: number;
        cost: number;
    }>;
}

export interface SubscriptionDetails {
    customer_id: string;
    subscription_tier: string;
    subscription_status: string;
    monthly_ve_cost: number;
    estimated_token_cost: number;
    total_estimated_cost: number;
    hired_ves_count: number;
}

export const billingAPI = {
    getUsage: async (startDate?: string, endDate?: string): Promise<BillingUsage> => {
        const params = { start_date: startDate, end_date: endDate };
        const { data } = await api.get('/billing/usage', { params });
        return data;
    },

    getSubscription: async (): Promise<SubscriptionDetails> => {
        const { data } = await api.get('/billing/subscription');
        return data;
    },
};
