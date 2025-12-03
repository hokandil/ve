import React, { useState } from 'react';
import { Edit, Trash2, Plus, Search } from 'lucide-react';
import { Card, CardContent, Button, Input, Badge } from '../components/ui';

interface VETemplate {
    id: string;
    name: string;
    role: string;
    department: string;
    seniority: string;
    status: string;
    pricing: number;
    created_at: string;
}

const VEList: React.FC = () => {
    const [searchQuery, setSearchQuery] = useState('');

    // Mock data
    const veTemplates: VETemplate[] = [
        {
            id: '1',
            name: 'Marketing Manager',
            role: 'Marketing Manager',
            department: 'Marketing',
            seniority: 'Manager',
            status: 'stable',
            pricing: 299,
            created_at: '2025-11-20',
        },
        {
            id: '2',
            name: 'Content Writer',
            role: 'Content Writer',
            department: 'Marketing',
            seniority: 'Senior',
            status: 'stable',
            pricing: 199,
            created_at: '2025-11-18',
        },
        {
            id: '3',
            name: 'Sales Representative',
            role: 'Sales Rep',
            department: 'Sales',
            seniority: 'Junior',
            status: 'beta',
            pricing: 149,
            created_at: '2025-11-15',
        },
    ];

    const filteredVEs = veTemplates.filter(ve =>
        ve.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        ve.department.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="p-8">
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">VE Templates</h1>
                    <p className="text-slate-600">Manage virtual employee templates</p>
                </div>
                <Button onClick={() => window.location.href = '/ve-creator'}>
                    <Plus className="mr-2 h-4 w-4" />
                    Create VE
                </Button>
            </div>

            <Card className="mb-6">
                <CardContent className="p-4">
                    <Input
                        placeholder="Search templates..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        icon={<Search className="h-4 w-4" />}
                    />
                </CardContent>
            </Card>

            <Card>
                <CardContent className="p-0">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-slate-200 bg-slate-50">
                                    <th className="p-4 text-left text-sm font-medium text-slate-600">Name</th>
                                    <th className="p-4 text-left text-sm font-medium text-slate-600">Department</th>
                                    <th className="p-4 text-left text-sm font-medium text-slate-600">Seniority</th>
                                    <th className="p-4 text-left text-sm font-medium text-slate-600">Status</th>
                                    <th className="p-4 text-left text-sm font-medium text-slate-600">Pricing</th>
                                    <th className="p-4 text-left text-sm font-medium text-slate-600">Created</th>
                                    <th className="p-4 text-right text-sm font-medium text-slate-600">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredVEs.map((ve) => (
                                    <tr key={ve.id} className="border-b border-slate-100 hover:bg-slate-50">
                                        <td className="p-4">
                                            <div>
                                                <p className="font-medium text-slate-900">{ve.name}</p>
                                                <p className="text-sm text-slate-600">{ve.role}</p>
                                            </div>
                                        </td>
                                        <td className="p-4 text-sm text-slate-900">{ve.department}</td>
                                        <td className="p-4 text-sm text-slate-900">{ve.seniority}</td>
                                        <td className="p-4">
                                            <Badge variant={ve.status === 'stable' ? 'success' : 'warning'}>
                                                {ve.status}
                                            </Badge>
                                        </td>
                                        <td className="p-4 text-sm font-medium text-slate-900">${ve.pricing}/mo</td>
                                        <td className="p-4 text-sm text-slate-600">
                                            {new Date(ve.created_at).toLocaleDateString()}
                                        </td>
                                        <td className="p-4">
                                            <div className="flex justify-end gap-2">
                                                <Button size="sm" variant="outline">
                                                    <Edit className="h-4 w-4" />
                                                </Button>
                                                <Button size="sm" variant="destructive">
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default VEList;
