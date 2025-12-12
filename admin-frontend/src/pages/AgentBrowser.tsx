import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Download, RefreshCw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Badge } from '../components/ui';
import { discoveryAPI, Agent } from '../services/discoveryAPI';

const AgentBrowser: React.FC = () => {
    const navigate = useNavigate();
    const [agents, setAgents] = useState<Agent[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [department, setDepartment] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [importing, setImporting] = useState<string | null>(null);

    useEffect(() => {
        loadAgents();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [page, department]);

    const loadAgents = async () => {
        setLoading(true);
        try {
            const response = await discoveryAPI.listAgents({
                search: search || undefined,
                department: department || undefined,
                page,
                page_size: 12
            });
            setAgents(response.items);
            setTotalPages(response.total_pages);
        } catch (error) {
            console.error('Failed to load agents:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = () => {
        setPage(1);
        loadAgents();
    };

    const handleImport = async (agent: Agent) => {
        setImporting(agent.id);
        try {
            const result = await discoveryAPI.importAgent(agent.id, {
                namespace: agent.namespace,
                pricing_monthly: 99,
                token_billing: 'customer_pays',
                estimated_usage: 'medium'
            });

            alert(`✅ ${result.message}\n\nYou can now add pricing and metadata.`);

            // Navigate to metadata editor
            navigate(`/metadata-editor/${result.ve_id}`);
        } catch (error: any) {
            console.error('Failed to import agent:', error);
            alert(`❌ Failed to import agent: ${error.response?.data?.detail || error.message}`);
        } finally {
            setImporting(null);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-slate-900">Browse KAgent Agents</h1>
                    <p className="text-slate-600 mt-2">
                        Import agents from KAgent Dashboard and add them to your marketplace
                    </p>
                </div>

                {/* Filters */}
                <Card className="mb-6">
                    <CardContent className="p-6">
                        <div className="flex gap-4">
                            <div className="flex-1">
                                <Input
                                    placeholder="Search agents..."
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                                />
                            </div>
                            <div className="w-48">
                                <select
                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    value={department}
                                    onChange={(e) => setDepartment(e.target.value)}
                                >
                                    <option value="">All Departments</option>
                                    <option value="hr">HR</option>
                                    <option value="sales">Sales</option>
                                    <option value="engineering">Engineering</option>
                                    <option value="marketing">Marketing</option>
                                </select>
                            </div>
                            <Button onClick={handleSearch}>
                                <Search className="mr-2 h-4 w-4" />
                                Search
                            </Button>
                            <Button variant="outline" onClick={loadAgents}>
                                <RefreshCw className="h-4 w-4" />
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Loading State */}
                {loading && (
                    <div className="flex items-center justify-center h-64">
                        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
                    </div>
                )}

                {/* Agents Grid */}
                {!loading && (
                    <>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
                            {agents.map((agent) => (
                                <Card key={agent.id} className="hover:shadow-lg transition-shadow">
                                    <CardHeader>
                                        <div className="flex items-start justify-between">
                                            <div>
                                                <CardTitle className="text-lg">{agent.name}</CardTitle>
                                                <p className="text-sm text-slate-500 mt-1">
                                                    {agent.namespace} • v{agent.version}
                                                </p>
                                            </div>
                                            <Badge variant="info">KAgent</Badge>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        <p className="text-sm text-slate-600 mb-4 line-clamp-2">
                                            {agent.description || 'No description available'}
                                        </p>

                                        {/* Labels */}
                                        <div className="flex flex-wrap gap-2 mb-4">
                                            {Object.entries(agent.labels).map(([key, value]) => (
                                                <Badge key={key} variant="default" className="text-xs">
                                                    {key}: {value}
                                                </Badge>
                                            ))}
                                        </div>

                                        {/* Tools */}
                                        {agent.tools.length > 0 && (
                                            <div className="mb-4">
                                                <p className="text-xs font-medium text-slate-700 mb-2">
                                                    Tools ({agent.tools.length})
                                                </p>
                                                <div className="flex flex-wrap gap-1">
                                                    {agent.tools.slice(0, 3).map((tool) => (
                                                        <span
                                                            key={tool}
                                                            className="text-xs px-2 py-1 bg-slate-100 text-slate-600 rounded"
                                                        >
                                                            {tool}
                                                        </span>
                                                    ))}
                                                    {agent.tools.length > 3 && (
                                                        <span className="text-xs px-2 py-1 bg-slate-100 text-slate-600 rounded">
                                                            +{agent.tools.length - 3} more
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        )}

                                        {/* Actions */}
                                        <Button
                                            className="w-full"
                                            onClick={() => handleImport(agent)}
                                            isLoading={importing === agent.id}
                                            disabled={importing !== null}
                                        >
                                            <Download className="mr-2 h-4 w-4" />
                                            Import to Marketplace
                                        </Button>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>

                        {/* Empty State */}
                        {agents.length === 0 && (
                            <Card>
                                <CardContent className="py-12 text-center">
                                    <p className="text-slate-500">No agents found</p>
                                    <p className="text-sm text-slate-400 mt-2">
                                        Try adjusting your search filters
                                    </p>
                                </CardContent>
                            </Card>
                        )}

                        {/* Pagination */}
                        {totalPages > 1 && (
                            <div className="flex items-center justify-center gap-2 mt-6">
                                <Button
                                    variant="outline"
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                >
                                    Previous
                                </Button>
                                <span className="text-sm text-slate-600">
                                    Page {page} of {totalPages}
                                </span>
                                <Button
                                    variant="outline"
                                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                    disabled={page === totalPages}
                                >
                                    Next
                                </Button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default AgentBrowser;
