import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Save, X, Globe, EyeOff } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Badge } from '../components/ui';
import { api } from '../services/api';

interface MetadataForm {
    pricing_monthly: number;
    token_billing: 'customer_pays' | 'included';
    estimated_usage: string;
    tags: string[];
    category: string;
    featured: boolean;
    icon_url: string;
    screenshots: string[];
    marketing_description: string;
    status: string;
    seniority_level: string;
}

const MetadataEditor: React.FC = () => {
    const { veId } = useParams<{ veId: string }>();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [agentName, setAgentName] = useState('');
    const [tagInput, setTagInput] = useState('');

    const [formData, setFormData] = useState<MetadataForm>({
        pricing_monthly: 99,
        token_billing: 'customer_pays',
        estimated_usage: 'medium',
        tags: [],
        category: 'general',
        featured: false,
        icon_url: '',
        screenshots: [],
        marketing_description: '',
        status: 'draft',
        seniority_level: 'junior'
    });

    const loadAgent = React.useCallback(async () => {
        try {
            const response = await api.get(`/marketplace/ves/${veId}`);
            const agent = response.data;
            setAgentName(agent.name);

            // Load existing metadata if available
            setFormData({
                pricing_monthly: agent.pricing_monthly || 99,
                token_billing: agent.token_billing || 'customer_pays',
                estimated_usage: agent.estimated_usage || 'medium',
                tags: agent.tags || [],
                category: agent.category || 'general',
                featured: agent.featured || false,
                icon_url: agent.icon_url || '',
                screenshots: agent.screenshots || [],
                marketing_description: agent.marketing_description || agent.description || '',
                status: agent.status || 'draft',
                seniority_level: agent.seniority_level || 'junior'
            });
        } catch (error) {
            console.error('Failed to load agent:', error);
            alert('Failed to load agent details');
        } finally {
            setLoading(false);
        }
    }, [veId]);

    useEffect(() => {
        loadAgent();
    }, [loadAgent]);

    const handleSave = async () => {
        setSaving(true);
        try {
            await api.put(`/marketplace/admin/agents/${veId}`, formData);
            alert('✅ Metadata saved successfully!');
            navigate('/catalog');
        } catch (error: any) {
            console.error('Failed to save metadata:', error);
            alert(`❌ Failed to save: ${error.response?.data?.detail || error.message}`);
        } finally {
            setSaving(false);
        }
    };

    const handleAddTag = () => {
        if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
            setFormData({
                ...formData,
                tags: [...formData.tags, tagInput.trim()]
            });
            setTagInput('');
        }
    };

    const handleRemoveTag = (tag: string) => {
        setFormData({
            ...formData,
            tags: formData.tags.filter(t => t !== tag)
        });
    };

    const handlePublish = async () => {
        if (!window.confirm('Are you sure you want to publish this agent to the marketplace?')) return;
        setSaving(true);
        try {
            await api.post(`/marketplace/admin/agents/${veId}/publish`);
            alert('✅ Agent published successfully!');
            loadAgent(); // Reload to get updated status
        } catch (error: any) {
            console.error('Failed to publish agent:', error);
            alert(`❌ Failed to publish: ${error.response?.data?.detail || error.message}`);
        } finally {
            setSaving(false);
        }
    };

    const handleUnpublish = async () => {
        if (!window.confirm('Are you sure you want to unpublish this agent? It will be hidden from customers.')) return;
        setSaving(true);
        try {
            await api.post(`/marketplace/admin/agents/${veId}/unpublish`);
            alert('✅ Agent unpublished successfully!');
            loadAgent(); // Reload to get updated status
        } catch (error: any) {
            console.error('Failed to unpublish agent:', error);
            alert(`❌ Failed to unpublish: ${error.response?.data?.detail || error.message}`);
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-3">
                            <h1 className="text-3xl font-bold text-slate-900">Edit Marketplace Metadata</h1>
                            <Badge variant={formData.status === 'stable' ? 'default' : 'secondary'}>
                                {formData.status === 'stable' ? 'Published' : 'Draft'}
                            </Badge>
                        </div>
                        <p className="text-slate-600 mt-2">Agent: {agentName}</p>
                    </div>
                    <div className="flex gap-2">
                        {formData.status === 'stable' ? (
                            <Button variant="outline" onClick={handleUnpublish} isLoading={saving} className="text-red-600 border-red-200 hover:bg-red-50">
                                <EyeOff className="mr-2 h-4 w-4" />
                                Unpublish
                            </Button>
                        ) : (
                            <Button variant="outline" onClick={handlePublish} isLoading={saving} className="text-green-600 border-green-200 hover:bg-green-50">
                                <Globe className="mr-2 h-4 w-4" />
                                Publish
                            </Button>
                        )}
                        <Button variant="outline" onClick={() => navigate('/catalog')}>
                            <X className="mr-2 h-4 w-4" />
                            Cancel
                        </Button>
                    </div>
                </div>

                {/* Pricing Section */}
                <Card className="mb-6">
                    <CardHeader>
                        <CardTitle>Pricing</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Monthly Fee ($)
                                </label>
                                <Input
                                    type="number"
                                    value={formData.pricing_monthly}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        pricing_monthly: parseFloat(e.target.value)
                                    })}
                                    min="0"
                                    step="1"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Token Billing
                                </label>
                                <select
                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    value={formData.token_billing}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        token_billing: e.target.value as 'customer_pays' | 'included'
                                    })}
                                >
                                    <option value="customer_pays">Customer Pays</option>
                                    <option value="included">Included</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Estimated Usage
                                </label>
                                <select
                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    value={formData.estimated_usage}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        estimated_usage: e.target.value
                                    })}
                                >
                                    <option value="low">Low ($10-20/mo)</option>
                                    <option value="medium">Medium ($20-50/mo)</option>
                                    <option value="high">High ($50-100/mo)</option>
                                </select>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Categorization Section */}
                <Card className="mb-6">
                    <CardHeader>
                        <CardTitle>Categorization</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Category
                                </label>
                                <select
                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    value={formData.category}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        category: e.target.value
                                    })}
                                >
                                    <option value="general">General</option>
                                    <option value="marketing">Marketing</option>
                                    <option value="sales">Sales</option>
                                    <option value="hr">HR</option>
                                    <option value="engineering">Engineering</option>
                                    <option value="customer-success">Customer Success</option>
                                    <option value="operations">Operations</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Seniority Level
                                </label>
                                <select
                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    value={formData.seniority_level}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        seniority_level: e.target.value
                                    })}
                                >
                                    <option value="junior">Junior</option>
                                    <option value="senior">Senior</option>
                                    <option value="manager">Manager</option>
                                </select>
                            </div>
                            <div className="flex items-center">
                                <label className="flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={formData.featured}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            featured: e.target.checked
                                        })}
                                        className="mr-2 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-slate-300 rounded"
                                    />
                                    <span className="text-sm font-medium text-slate-700">
                                        Featured Agent
                                    </span>
                                </label>
                            </div>
                        </div>

                        {/* Tags */}
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">
                                Tags
                            </label>
                            <div className="flex gap-2 mb-2">
                                <Input
                                    placeholder="Add tag..."
                                    value={tagInput}
                                    onChange={(e) => setTagInput(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                                />
                                <Button onClick={handleAddTag}>Add</Button>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {formData.tags.map((tag) => (
                                    <Badge key={tag} variant="default" className="flex items-center gap-1">
                                        {tag}
                                        <button
                                            onClick={() => handleRemoveTag(tag)}
                                            className="ml-1 hover:text-red-600"
                                        >
                                            <X className="h-3 w-3" />
                                        </button>
                                    </Badge>
                                ))}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Marketing Section */}
                <Card className="mb-6">
                    <CardHeader>
                        <CardTitle>Marketing Content</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-slate-700 mb-2">
                                Icon URL
                            </label>
                            <Input
                                placeholder="https://example.com/icon.png"
                                value={formData.icon_url}
                                onChange={(e) => setFormData({
                                    ...formData,
                                    icon_url: e.target.value
                                })}
                            />
                            <p className="text-xs text-slate-500 mt-1">
                                Recommended: 256x256px PNG or SVG
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">
                                Marketing Description
                            </label>
                            <textarea
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                rows={6}
                                placeholder="Describe what makes this agent valuable to customers..."
                                value={formData.marketing_description}
                                onChange={(e) => setFormData({
                                    ...formData,
                                    marketing_description: e.target.value
                                })}
                            />
                            <p className="text-xs text-slate-500 mt-1">
                                This will be shown to customers in the marketplace
                            </p>
                        </div>
                    </CardContent>
                </Card>

                {/* Actions */}
                <div className="flex justify-end gap-4">
                    <Button variant="outline" onClick={() => navigate('/catalog')}>
                        Cancel
                    </Button>
                    <Button onClick={handleSave} isLoading={saving}>
                        <Save className="mr-2 h-4 w-4" />
                        Save Metadata
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default MetadataEditor;
