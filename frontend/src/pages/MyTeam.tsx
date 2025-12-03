import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { customerAPI } from '../services/api';
import api from '../services/api';
import { Plus, MoreVertical, Activity, MessageSquare, CheckSquare, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { ChatInterface } from '../components/ChatInterface';
import { Card, CardContent, Button, Badge, Avatar } from '../components/ui';
import { PageLayout } from '../components/layout';
import { useAuth } from '../contexts/AuthContext';

interface VEDetails {
    id: string;
    name: string;
    role: string;
    department: string;
    seniority_level: string;
    pricing_monthly: number;
    icon_url?: string;
}

interface CustomerVE {
    id: string;
    customer_id: string;
    marketplace_agent_id: string;
    persona_name: string;
    persona_email: string;
    hired_at: string;
    status: string;
    agent_type: string;
    agent_gateway_route: string;
    ve_details: VEDetails;
}

const MyTeam: React.FC = () => {
    const { user } = useAuth();
    const [agents, setAgents] = useState<CustomerVE[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [testingCollaboration, setTestingCollaboration] = useState(false);
    const [collaborationResult, setCollaborationResult] = useState<string | null>(null);
    const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
    const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());

    const navigate = useNavigate();

    const fetchAgents = useCallback(async () => {
        try {
            setLoading(true);
            const data = await customerAPI.listVEs();
            setAgents(data || []);
            setError(null);
        } catch (err: any) {
            console.error('Error fetching agents:', err);
            setError(err.response?.data?.detail || 'Failed to load agents');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAgents();
    }, []); // fetch once on mount


    const handleUnhire = async (veId: string) => {
        if (!window.confirm('Are you sure you want to unhire this agent? This action cannot be undone.')) {
            return;
        }

        try {
            await customerAPI.unhireVE(veId);
            fetchAgents();
            setActiveMenuId(null);
        } catch (error) {
            console.error('Error unhiring VE:', error);
            alert('Failed to unhire agent');
        }
    };

    const toggleCardExpansion = (agentId: string) => {
        setExpandedCards(prev => {
            const newSet = new Set(prev);
            if (newSet.has(agentId)) {
                newSet.delete(agentId);
            } else {
                newSet.add(agentId);
            }
            return newSet;
        });
    };

    const testMultiAgentCollaboration = async () => {
        setTestingCollaboration(true);
        setCollaborationResult(null);

        try {
            if (agents.length === 0) {
                setCollaborationResult('❌ No agents hired yet. Please hire at least one agent to test collaboration.');
                return;
            }

            const testTask = {
                title: 'Multi-Agent Collaboration Test',
                description: `This is a test to verify the orchestrator and multi-agent collaboration system.

The orchestrator should:
1. Analyze this request
2. Route to the most appropriate agent(s) in my team
3. Coordinate responses if multiple agents are involved

Available agents in my team:
${agents.map(a => `- ${a.persona_name} (${a.ve_details?.role})`).join('\n')}

This is just a test - no actual work needs to be done.`,
                assigned_to_ve: null,
                priority: 'medium'
            };

            const response = await api.post('/tasks', testTask);

            setCollaborationResult(`✅ Test task created successfully! 
      
Task ID: ${response.data.id}
Routing: Orchestrator will analyze and route to best agent(s)

The orchestrator should now:
1. Analyze the task requirements
2. Route to the most suitable agent from your team
3. Coordinate multi-agent collaboration if needed

Your team (${agents.length} agent${agents.length > 1 ? 's' : ''}):
${agents.map(a => `• ${a.persona_name} - ${a.ve_details?.role} (${a.ve_details?.seniority_level})`).join('\n')}

Check the Tasks page to see the orchestrator's routing decision.`);

        } catch (err: any) {
            console.error('Error testing collaboration:', err);
            setCollaborationResult(`❌ Test failed: ${err.response?.data?.detail || err.message}`);
        } finally {
            setTestingCollaboration(false);
        }
    };

    const getSeniorityBadgeColor = (level: string) => {
        switch (level) {
            case 'manager': return 'bg-purple-100 text-purple-800 border-purple-300';
            case 'senior': return 'bg-blue-100 text-blue-800 border-blue-300';
            case 'junior': return 'bg-green-100 text-green-800 border-green-300';
            default: return 'bg-gray-100 text-gray-800 border-gray-300';
        }
    };

    const [editingAgent, setEditingAgent] = useState<CustomerVE | null>(null);
    const [activeChatAgent, setActiveChatAgent] = useState<CustomerVE | null>(null);
    const [editName, setEditName] = useState('');
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);

    const openEditModal = (agent: CustomerVE) => {
        setEditingAgent(agent);
        setEditName(agent.persona_name);
        setIsEditModalOpen(true);
        setActiveMenuId(null);
    };

    const handleUpdateVE = async () => {
        if (!editingAgent) return;

        try {
            await customerAPI.updateVE(editingAgent.id, { persona_name: editName });
            setIsEditModalOpen(false);
            setEditingAgent(null);
            fetchAgents();
        } catch (error) {
            console.error('Error updating VE:', error);
            alert('Failed to update agent details');
        }
    };

    if (loading) {
        return (
            <PageLayout title="My Team">
                <div className="flex items-center justify-center h-64">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
                </div>
            </PageLayout>
        );
    }

    return (
        <PageLayout title="My Team">
            <div className="mb-6 flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900">Your Virtual Team</h2>
                    <p className="text-slate-600">Manage your hired virtual employees and their performance.</p>
                </div>
                <Button onClick={() => navigate('/marketplace')}>
                    <Plus className="mr-2 h-4 w-4" />
                    Hire VE
                </Button>
            </div>

            {error && (
                <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
                    <p className="text-red-800">{error}</p>
                </div>
            )}

            {/* Orchestrator Test Section */}
            <div className="mb-8 bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-3">
                    🤝 Orchestrator & Multi-Agent Test
                </h2>
                <p className="text-gray-700 mb-4">
                    Test the orchestrator's ability to route tasks to the right agents. The shared orchestrator
                    will analyze the task and decide which agent(s) should handle it.
                </p>

                <button
                    onClick={testMultiAgentCollaboration}
                    disabled={testingCollaboration || agents.length === 0}
                    className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
                >
                    {testingCollaboration ? 'Testing...' : 'Run Orchestrator Test'}
                </button>

                {collaborationResult && (
                    <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4">
                        <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">
                            {collaborationResult}
                        </pre>
                    </div>
                )}
            </div>

            {agents.length === 0 ? (
                <Card>
                    <CardContent className="py-12 text-center">
                        <Activity className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                        <h3 className="text-lg font-semibold text-slate-900 mb-2">No team members yet</h3>
                        <p className="text-slate-600 mb-6">
                            Start building your virtual team by hiring your first VE from the marketplace.
                        </p>
                        <Button onClick={() => navigate('/marketplace')}>
                            Browse Marketplace
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {agents.map((agent) => {
                        const isExpanded = expandedCards.has(agent.id);

                        return (
                            <div
                                key={agent.id}
                                className="bg-white rounded-lg shadow-md border border-gray-200 p-6 hover:shadow-lg transition-shadow relative"
                            >
                                {/* Unhire Menu - Top Right */}
                                <div className="absolute top-4 right-4">
                                    <button
                                        className="text-slate-400 hover:text-slate-600 p-1 rounded-full hover:bg-slate-100"
                                        onClick={() => setActiveMenuId(activeMenuId === agent.id ? null : agent.id)}
                                    >
                                        <MoreVertical className="h-5 w-5" />
                                    </button>

                                    {activeMenuId === agent.id && (
                                        <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-50 border border-slate-200">
                                            <div className="py-1">
                                                <button
                                                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center"
                                                    onClick={() => openEditModal(agent)}
                                                >
                                                    <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                    </svg>
                                                    Settings
                                                </button>
                                                <button
                                                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center"
                                                    onClick={() => handleUnhire(agent.id)}
                                                >
                                                    <Trash2 className="h-4 w-4 mr-2" />
                                                    Unhire Agent
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Agent Header - Always Visible */}
                                <div className="flex items-start justify-between mb-4 pr-8">
                                    <div className="flex-1">
                                        <h3 className="text-lg font-semibold text-gray-900">
                                            {agent.persona_name}
                                        </h3>
                                        <p className="text-sm text-gray-600">{agent.ve_details?.role}</p>
                                    </div>
                                </div>

                                {/* Seniority Badge - Always Visible */}
                                <div className="mb-4 flex items-center justify-between">
                                    <span
                                        className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getSeniorityBadgeColor(
                                            agent.ve_details?.seniority_level
                                        )}`}
                                    >
                                        {agent.ve_details?.seniority_level?.toUpperCase()}
                                    </span>

                                    {/* Expand/Collapse Button */}
                                    <button
                                        onClick={() => toggleCardExpansion(agent.id)}
                                        className="text-slate-500 hover:text-slate-700 p-1 rounded-full hover:bg-slate-100 transition-colors"
                                        title={isExpanded ? "Show less" : "Show more"}
                                    >
                                        {isExpanded ? (
                                            <ChevronUp className="h-5 w-5" />
                                        ) : (
                                            <ChevronDown className="h-5 w-5" />
                                        )}
                                    </button>
                                </div>

                                {/* Collapsible Details */}
                                {isExpanded && (
                                    <>
                                        {/* Agent Details */}
                                        <div className="space-y-2 text-sm mb-4">
                                            <div className="flex items-center text-gray-600">
                                                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                                </svg>
                                                {agent.persona_email}
                                            </div>

                                            <div className="flex items-center text-gray-600">
                                                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                                </svg>
                                                {agent.ve_details?.department}
                                            </div>

                                            <div className="flex items-center text-gray-600">
                                                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                </svg>
                                                ${agent.ve_details?.pricing_monthly}/month
                                            </div>

                                            <div className="flex items-center text-gray-600">
                                                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                </svg>
                                                Hired {new Date(agent.hired_at).toLocaleDateString()}
                                            </div>
                                        </div>

                                        {/* Status Badge */}
                                        <div className="mb-4">
                                            <Badge variant={agent.status === 'active' ? 'success' : 'default'}>
                                                {agent.status}
                                            </Badge>
                                        </div>

                                        {/* Agent Type */}
                                        <div className="mb-4 pt-4 border-t border-gray-200">
                                            <p className="text-xs text-gray-500">
                                                Agent Type: <span className="font-mono text-gray-700">{agent.agent_type}</span>
                                            </p>
                                        </div>
                                    </>
                                )}

                                {/* Action Buttons - Always Visible */}
                                <div className="flex gap-2">
                                    <Button size="sm" variant="outline" className="flex-1 gap-2">
                                        <CheckSquare className="h-4 w-4" />
                                        Tasks
                                    </Button>
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        className="flex-1 gap-2"
                                        onClick={() => setActiveChatAgent(agent)}
                                    >
                                        <MessageSquare className="h-4 w-4" />
                                        Chat
                                    </Button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Chat Interface */}
            {activeChatAgent && (
                <ChatInterface
                    veId={activeChatAgent.id}
                    agentName={activeChatAgent.persona_name}
                    agentRole={activeChatAgent.ve_details?.role || 'Virtual Employee'}
                    onClose={() => setActiveChatAgent(null)}
                />
            )}

            {/* Hierarchical Department View */}
            <div className="mt-8">
                <h2 className="text-2xl font-bold text-slate-900 mb-4">Team by Department</h2>
                {Object.entries(
                    agents.reduce((acc, agent) => {
                        const dept = agent.ve_details?.department || 'Unassigned';
                        if (!acc[dept]) acc[dept] = [];
                        acc[dept].push(agent);
                        return acc;
                    }, {} as Record<string, typeof agents>)
                ).map(([dept, deptAgents]) => (
                    <div key={dept} className="mb-6 border border-gray-200 rounded-lg">
                        <button
                            className="w-full text-left px-4 py-2 bg-gray-50 hover:bg-gray-100 flex justify-between items-center rounded-t-lg"
                            onClick={() => setExpandedCards(prev => {
                                const newSet = new Set(prev);
                                if (newSet.has(dept)) newSet.delete(dept); else newSet.add(dept);
                                return newSet;
                            })}
                        >
                            <span className="font-semibold text-slate-800">{dept}</span>
                            {expandedCards.has(dept) ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        </button>
                        {expandedCards.has(dept) && (
                            <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 bg-white rounded-b-lg">
                                {deptAgents.map(agent => (
                                    <div key={agent.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 relative">
                                        <div className="flex justify-between items-start mb-2">
                                            <div>
                                                <h4 className="font-semibold text-slate-900">{agent.persona_name}</h4>
                                                <p className="text-xs text-slate-500">{agent.ve_details?.role}</p>
                                            </div>
                                            <Badge variant={agent.status === 'active' ? 'success' : 'default'} className="text-xs">
                                                {agent.status}
                                            </Badge>
                                        </div>
                                        <div className="flex justify-between items-center mt-4">
                                            <span className={`text-xs px-2 py-1 rounded-full border ${getSeniorityBadgeColor(agent.ve_details?.seniority_level)}`}>
                                                {agent.ve_details?.seniority_level?.toUpperCase()}
                                            </span>
                                            <Button size="sm" variant="ghost" onClick={() => openEditModal(agent)}>
                                                Settings
                                            </Button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Team Composition Summary */}
            {agents.length > 0 && (
                <div className="mt-8 bg-white rounded-lg shadow-md border border-gray-200 p-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Team Composition</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center p-4 bg-purple-50 rounded-lg">
                            <div className="text-3xl font-bold text-purple-600">
                                {agents.filter(a => a.ve_details?.seniority_level === 'manager').length}
                            </div>
                            <div className="text-sm text-gray-600 mt-1">Managers</div>
                        </div>
                        <div className="text-center p-4 bg-blue-50 rounded-lg">
                            <div className="text-3xl font-bold text-blue-600">
                                {agents.filter(a => a.ve_details?.seniority_level === 'senior').length}
                            </div>
                            <div className="text-sm text-gray-600 mt-1">Senior</div>
                        </div>
                        <div className="text-center p-4 bg-green-50 rounded-lg">
                            <div className="text-3xl font-bold text-green-600">
                                {agents.filter(a => a.ve_details?.seniority_level === 'junior').length}
                            </div>
                            <div className="text-sm text-gray-600 mt-1">Junior</div>
                        </div>
                    </div>
                </div>
            )}

            {/* Edit Modal */}
            {isEditModalOpen && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h3 className="text-lg font-semibold mb-4">Edit Agent Details</h3>
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Persona Name
                            </label>
                            <input
                                type="text"
                                value={editName}
                                onChange={(e) => setEditName(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                        </div>
                        <div className="flex justify-end gap-2">
                            <Button variant="outline" onClick={() => setIsEditModalOpen(false)}>
                                Cancel
                            </Button>
                            <Button onClick={handleUpdateVE}>
                                Save Changes
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </PageLayout>
    );
};

export default MyTeam;
