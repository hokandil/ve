import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter, Button, Badge } from '../components/ui';
import { DeleteAgentDialog } from '../components/DeleteAgentDialog';
import { Edit, Trash2, Plus } from 'lucide-react';

interface MarketplaceVE {
    id: string;
    name: string;
    role: string;
    status: string;
    pricing_monthly: number;
    kagent_id?: string;
    description?: string;
    category?: string;
    source?: string;
}

const CatalogManager: React.FC = () => {
    const navigate = useNavigate();
    const [marketplaceVEs, setMarketplaceVEs] = useState<MarketplaceVE[]>([]);
    const [loading, setLoading] = useState(true);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [agentToDelete, setAgentToDelete] = useState<{ id: string, name: string } | null>(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const response = await api.get('/marketplace/ves');
            setMarketplaceVEs(response.data.items || []);
        } catch (error) {
            console.error("Failed to fetch catalog data", error);
            // alert("Failed to load catalog data. Is the backend running?");
        } finally {
            setLoading(false);
        }
    };

    const openDeleteDialog = (ve: MarketplaceVE) => {
        setAgentToDelete({ id: ve.id, name: ve.name });
        setDeleteDialogOpen(true);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
            </div>
        );
    }

    return (
        <div className="container mx-auto p-8 space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Catalog Manager</h1>
                    <p className="text-slate-600 mt-2">Manage your marketplace offerings and metadata.</p>
                </div>
                <Button onClick={() => navigate('/browse-agents')}>
                    <Plus className="mr-2 h-4 w-4" />
                    Import New Agent
                </Button>
            </div>

            <div className="grid grid-cols-1 gap-6">
                {marketplaceVEs.length === 0 ? (
                    <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
                        <p className="text-slate-500 mb-4">No agents in marketplace yet.</p>
                        <Button onClick={() => navigate('/browse-agents')}>
                            Browse KAgent Registry
                        </Button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {marketplaceVEs.map(ve => (
                            <Card key={ve.id} className="flex flex-col hover:shadow-md transition-shadow">
                                <CardHeader>
                                    <div className="flex justify-between items-start">
                                        <CardTitle className="text-xl truncate pr-2">{ve.name}</CardTitle>
                                        <Badge variant={ve.status === 'stable' ? 'default' : 'secondary'}>
                                            {ve.status === 'stable' ? 'Published' : 'Draft'}
                                        </Badge>
                                    </div>
                                    <CardDescription className="line-clamp-2 h-10">
                                        {ve.description || "No description provided"}
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="flex-1">
                                    <div className="flex flex-wrap gap-2 mb-4">
                                        {ve.category && (
                                            <Badge variant="outline" className="text-xs">
                                                {ve.category}
                                            </Badge>
                                        )}
                                        {ve.source === 'kagent' && (
                                            <Badge variant="secondary" className="text-xs bg-blue-50 text-blue-700 border-blue-100">
                                                KAgent
                                            </Badge>
                                        )}
                                    </div>
                                    <div className="text-sm font-medium text-slate-900">
                                        ${ve.pricing_monthly}/mo
                                    </div>
                                </CardContent>
                                <CardFooter className="pt-4 border-t bg-slate-50 flex justify-between gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="flex-1"
                                        onClick={() => navigate(`/metadata-editor/${ve.id}`)}
                                    >
                                        <Edit className="mr-2 h-4 w-4" /> Edit
                                    </Button>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                        onClick={() => openDeleteDialog(ve)}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </CardFooter>
                            </Card>
                        ))}
                    </div>
                )}
            </div>

            <DeleteAgentDialog
                isOpen={deleteDialogOpen}
                onClose={() => setDeleteDialogOpen(false)}
                onSuccess={() => {
                    fetchData();
                    setDeleteDialogOpen(false);
                }}
                agentId={agentToDelete?.id || ''}
                agentName={agentToDelete?.name || ''}
            />
        </div>
    );
};

export default CatalogManager;
