import React, { useState, useEffect } from 'react';
import { Search, Filter, Star, Users, TrendingUp, Zap, Tag } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Badge, Avatar } from '../components/ui';
import { PageLayout } from '../components/layout';
import { marketplaceAPI } from '../services/api';
import HireAgentModal from '../components/HireAgentModal';

interface VETemplate {
    id: string;
    name: string;
    role: string;
    description: string;
    pricing_monthly: number;
    status: string;
    tags: string[];
    category: string;
    featured: boolean;
    icon_url?: string;
    marketing_description?: string;
    token_billing: string;
    estimated_usage: string;
}

const Marketplace: React.FC = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [veTemplates, setVeTemplates] = useState<VETemplate[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedAgent, setSelectedAgent] = useState<VETemplate | null>(null);
    // Toast context available if needed

    const categories = ['all', 'marketing', 'sales', 'hr', 'engineering', 'operations', 'general'];

    useEffect(() => {
        loadVEs();
    }, [selectedCategory]);

    const loadVEs = async () => {
        setLoading(true);
        try {
            const params = selectedCategory !== 'all' ? { category: selectedCategory } : {};
            const response = await marketplaceAPI.list(params);
            console.log('Marketplace VEs:', response.items);
            setVeTemplates(response.items || []);
        } catch (error) {
            console.error('Error loading VEs:', error);
            // Error loading - could show toast here if needed
            console.error('Failed to load marketplace agents');
        } finally {
            setLoading(false);
        }
    };

    const filteredVEs = veTemplates.filter(ve => {
        const matchesSearch = ve.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            ve.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            ve.marketing_description?.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesSearch;
    });

    if (loading) {
        return (
            <PageLayout title="VE Marketplace">
                <div className="flex items-center justify-center h-64">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
                </div>
            </PageLayout>
        );
    }

    return (
        <PageLayout title="VE Marketplace">
            {/* Search and Filters */}
            <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div className="flex-1 max-w-md">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 h-4 w-4" />
                        <Input
                            placeholder="Search agents..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10"
                        />
                    </div>
                </div>
                <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0">
                    {categories.map((cat) => (
                        <Button
                            key={cat}
                            variant={selectedCategory === cat ? 'primary' : 'outline'}
                            size="sm"
                            onClick={() => setSelectedCategory(cat)}
                            className="capitalize whitespace-nowrap"
                        >
                            {cat}
                        </Button>
                    ))}
                </div>
            </div>

            {/* VE Grid */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {filteredVEs.map((ve) => (
                    <Card key={ve.id} className="hover:shadow-lg transition-all duration-200 border-slate-200 flex flex-col h-full">
                        <CardHeader className="pb-3">
                            <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-3">
                                    {ve.icon_url ? (
                                        <img src={ve.icon_url} alt={ve.name} className="h-12 w-12 rounded-lg object-cover bg-slate-100" />
                                    ) : (
                                        <Avatar fallback={typeof ve.name === 'string' ? ve.name.substring(0, 2) : '??'} className="h-12 w-12 text-lg" />
                                    )}
                                    <div>
                                        <CardTitle className="text-lg">{typeof ve.name === 'string' ? ve.name : 'Unknown Agent'}</CardTitle>
                                        <p className="text-sm text-slate-500 font-medium">{typeof ve.role === 'string' ? ve.role : 'Unknown Role'}</p>
                                    </div>
                                </div>
                                {ve.featured && (
                                    <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-200 border-amber-200">
                                        Featured
                                    </Badge>
                                )}
                            </div>
                        </CardHeader>
                        <CardContent className="flex-1 flex flex-col">
                            <p className="text-sm text-slate-600 mb-4 line-clamp-3 flex-1">
                                {typeof ve.marketing_description === 'string' ? ve.marketing_description :
                                    typeof ve.description === 'string' ? ve.description : 'No description available'}
                            </p>

                            <div className="space-y-3 mb-4">
                                <div className="flex flex-wrap gap-2">
                                    {Array.isArray(ve.tags) && ve.tags.map((tag) => {
                                        if (typeof tag !== 'string' && typeof tag !== 'number') return null;
                                        return (
                                            <Badge key={String(tag)} variant="default" className="text-xs">
                                                {String(tag)}
                                            </Badge>
                                        );
                                    })}
                                </div>

                                <div className="flex items-center gap-4 text-xs text-slate-500">
                                    <div className="flex items-center gap-1">
                                        <Zap className="h-3 w-3" />
                                        <span className="capitalize">{typeof ve.estimated_usage === 'string' ? ve.estimated_usage : 'Unknown'} Usage</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <Tag className="h-3 w-3" />
                                        <span className="capitalize">{ve.token_billing === 'included' ? 'Tokens Included' : 'Pay-as-you-go'}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center justify-between border-t border-slate-100 pt-4 mt-auto">
                                <div>
                                    <p className="text-xs text-slate-500">Starting at</p>
                                    <div className="flex items-baseline gap-1">
                                        <span className="text-xl font-bold text-slate-900">${typeof ve.pricing_monthly === 'number' ? ve.pricing_monthly : '0'}</span>
                                        <span className="text-xs text-slate-500">/mo</span>
                                    </div>
                                </div>
                                <Button
                                    onClick={() => setSelectedAgent(ve)}
                                    className="bg-indigo-600 hover:bg-indigo-700"
                                >
                                    Hire Agent
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {filteredVEs.length === 0 && (
                <div className="py-16 text-center bg-slate-50 rounded-lg border border-dashed border-slate-300">
                    <Users className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                    <h3 className="text-lg font-medium text-slate-900">No agents found</h3>
                    <p className="text-slate-500">Try adjusting your search or category filters.</p>
                </div>
            )}

            <HireAgentModal
                isOpen={!!selectedAgent}
                onClose={() => setSelectedAgent(null)}
                agent={selectedAgent}
            />
        </PageLayout>
    );
};

export default Marketplace;
