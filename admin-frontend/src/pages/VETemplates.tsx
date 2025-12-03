import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, Button, Badge } from '../components/ui';
import { Edit, Trash2, Plus, Copy } from 'lucide-react';

interface VETemplate {
    id: string;
    name: string;
    department: string;
    role: string;
    pricingMonthly: number;
    status: 'draft' | 'beta' | 'stable';
    published: boolean;
    description: string;
    updatedAt: string;
}

const VETemplates: React.FC = () => {
    const navigate = useNavigate();

    // Mock data - eventually fetch from backend
    const [templates] = useState<VETemplate[]>([
        {
            id: '1',
            name: 'Customer Success Manager',
            department: 'Customer Success',
            role: 'Manager',
            pricingMonthly: 99,
            status: 'stable',
            published: true,
            description: 'Strategic marketing leadership and campaign management.',
            updatedAt: '2025-11-20T10:00:00Z',
        },
        {
            id: '2',
            name: 'Junior Content Creator',
            department: 'Marketing',
            role: 'Junior',
            pricingMonthly: 29,
            status: 'beta',
            published: false,
            description: 'Creates social media posts and blog content.',
            updatedAt: '2025-11-25T14:30:00Z',
        }
    ]);

    const handleCreate = () => {
        navigate('/create-template');
    };

    const handleEdit = (id: string) => {
        navigate(`/create-template?id=${id}`);
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'stable': return <Badge variant="success">Stable</Badge>;
            case 'beta': return <Badge variant="warning">Beta</Badge>;
            case 'draft': return <Badge variant="default">Draft</Badge>;
            default: return <Badge variant="default">{status}</Badge>;
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 mb-2">VE Templates</h1>
                        <p className="text-slate-600">
                            Create and manage Virtual Employee templates for the marketplace.
                        </p>
                    </div>
                    <Button onClick={handleCreate}>
                        <Plus className="h-4 w-4 mr-2" />
                        Create New Template
                    </Button>
                </div>

                {/* Templates List */}
                <div className="grid gap-4">
                    {templates.map((template) => (
                        <Card key={template.id} className="hover:shadow-md transition-shadow">
                            <CardContent className="p-6">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h3 className="text-xl font-semibold text-slate-900">
                                                {template.name}
                                            </h3>
                                            {getStatusBadge(template.status)}
                                            {template.published ? (
                                                <Badge variant="info" className="bg-indigo-100 text-indigo-800">Published</Badge>
                                            ) : (
                                                <Badge variant="default" className="bg-slate-100 text-slate-600">Unpublished</Badge>
                                            )}
                                        </div>

                                        <div className="flex items-center gap-2 text-sm text-slate-500 mb-3">
                                            <span>{template.department}</span>
                                            <span>•</span>
                                            <span>{template.role}</span>
                                            <span>•</span>
                                            <span>${template.pricingMonthly}/mo</span>
                                        </div>

                                        <p className="text-slate-600 mb-4 max-w-3xl">
                                            {template.description}
                                        </p>

                                        <div className="text-xs text-slate-400">
                                            Last updated: {new Date(template.updatedAt).toLocaleDateString()}
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex gap-2 ml-4">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleEdit(template.id)}
                                            title="Edit Template"
                                        >
                                            <Edit className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            title="Duplicate"
                                        >
                                            <Copy className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                            title="Delete"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default VETemplates;
