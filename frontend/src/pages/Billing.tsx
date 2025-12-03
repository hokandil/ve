import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, Badge } from '../components/ui';
import { PageLayout } from '../components/layout';
import { DollarSign, TrendingUp, Download } from 'lucide-react';
import { billingAPI, BillingUsage, SubscriptionDetails } from '../services/billingAPI';
import { useToast } from '../components/ui/Toast';

const Billing: React.FC = () => {
    const { addToast } = useToast();
    const [loading, setLoading] = useState(true);
    const [usage, setUsage] = useState<BillingUsage | null>(null);
    const [subscription, setSubscription] = useState<SubscriptionDetails | null>(null);

    useEffect(() => {
        loadBillingData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const loadBillingData = async () => {
        setLoading(true);
        try {
            const [usageData, subscriptionData] = await Promise.all([
                billingAPI.getUsage(),
                billingAPI.getSubscription(),
            ]);
            setUsage(usageData);
            setSubscription(subscriptionData);
        } catch (error) {
            console.error('Failed to load billing data:', error);
            addToast('error', 'Failed to load billing data');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <PageLayout title="Billing & Usage">
                <div className="flex items-center justify-center h-64">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
                </div>
            </PageLayout>
        );
    }

    const totalCost = (subscription?.monthly_ve_cost || 0) + (usage?.total_cost || 0);

    return (
        <PageLayout title="Billing & Usage">
            {/* Current Bill */}
            <div className="mb-8 grid gap-4 md:grid-cols-3">
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-slate-600">Current Plan</p>
                                <p className="text-2xl font-bold text-slate-900">{subscription?.subscription_tier || 'Free'}</p>
                            </div>
                            <Badge variant={subscription?.subscription_status === 'active' ? 'success' : 'default'}>
                                {subscription?.subscription_status || 'Active'}
                            </Badge>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-slate-600">VE Subscriptions</p>
                                <p className="text-2xl font-bold text-slate-900">${subscription?.monthly_ve_cost.toFixed(2) || '0.00'}</p>
                                <p className="text-xs text-slate-500 mt-1">{subscription?.hired_ves_count || 0} VEs hired</p>
                            </div>
                            <div className="rounded-full bg-indigo-100 p-3">
                                <DollarSign className="h-6 w-6 text-indigo-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-slate-600">Token Usage</p>
                                <p className="text-2xl font-bold text-slate-900">${usage?.total_cost.toFixed(2) || '0.00'}</p>
                                <p className="text-xs text-slate-500 mt-1">{usage?.total_tokens.toLocaleString() || 0} tokens</p>
                            </div>
                            <div className="rounded-full bg-green-100 p-3">
                                <TrendingUp className="h-6 w-6 text-green-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Total This Month */}
            <Card className="mb-8">
                <CardHeader>
                    <CardTitle>Total This Month</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-4xl font-bold text-slate-900">${totalCost.toFixed(2)}</p>
                            <p className="text-sm text-slate-600 mt-1">
                                Billing cycle: {usage?.period_start ? new Date(usage.period_start).toLocaleDateString() : 'N/A'} - {usage?.period_end ? new Date(usage.period_end).toLocaleDateString() : 'N/A'}
                            </p>
                        </div>
                        <Badge variant="info">Next billing</Badge>
                    </div>
                </CardContent>
            </Card>

            {/* Usage by VE */}
            {usage && usage.usage_by_ve && usage.usage_by_ve.length > 0 && (
                <Card className="mb-8">
                    <CardHeader>
                        <CardTitle>Usage by Virtual Employee</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {usage.usage_by_ve.map((ve, index) => (
                                <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                                    <div>
                                        <h4 className="font-medium text-slate-900">
                                            {/* In a real app, we'd map ID to name from a context or separate fetch */}
                                            {ve.ve_id === 'orchestrator' ? 'System Orchestrator' : `VE (${ve.ve_id.substring(0, 8)})`}
                                        </h4>
                                        <p className="text-sm text-slate-600">{ve.tokens?.toLocaleString() || 0} tokens</p>
                                    </div>
                                    <p className="text-lg font-semibold text-slate-900">${ve.cost?.toFixed(2) || '0.00'}</p>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Usage by Operation */}
            {usage && usage.usage_by_operation && usage.usage_by_operation.length > 0 && (
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <CardTitle>Usage by Operation</CardTitle>
                            <button className="flex items-center gap-2 text-sm text-indigo-600 hover:text-indigo-700">
                                <Download className="h-4 w-4" />
                                Export CSV
                            </button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-slate-200">
                                        <th className="pb-3 text-left text-sm font-medium text-slate-600">Operation</th>
                                        <th className="pb-3 text-right text-sm font-medium text-slate-600">Tokens</th>
                                        <th className="pb-3 text-right text-sm font-medium text-slate-600">Cost</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {usage.usage_by_operation.map((item, index) => (
                                        <tr key={index} className="border-b border-slate-100">
                                            <td className="py-3 text-sm text-slate-900">{item.operation}</td>
                                            <td className="py-3 text-right text-sm text-slate-900">{item.tokens?.toLocaleString() || 0}</td>
                                            <td className="py-3 text-right text-sm font-medium text-slate-900">${item.cost?.toFixed(2) || '0.00'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>
            )}

            {(!usage || (usage.usage_by_operation?.length === 0 && usage.usage_by_ve?.length === 0)) && (
                <Card>
                    <CardContent className="py-12 text-center">
                        <p className="text-slate-500">No usage data available for this period.</p>
                    </CardContent>
                </Card>
            )}
        </PageLayout>
    );
};

export default Billing;
