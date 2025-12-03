import React, { useState, useEffect, useCallback } from 'react';
import { customerAPI } from '../services/api';
import api from '../services/api';

interface VEDetails {
    id: string;
    name: string;
    role: string;
    department: string;
    seniority_level: string;
    pricing_monthly: number;
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

const MyAgents: React.FC = () => {
    const [agents, setAgents] = useState<CustomerVE[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [testingCollaboration, setTestingCollaboration] = useState(false);
    const [collaborationResult, setCollaborationResult] = useState<string | null>(null);

    const fetchAgents = useCallback(async () => {
        try {
            setLoading(true);
            const data = await customerAPI.listVEs();
            setAgents(data);
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
    }, [fetchAgents]);

    const testMultiAgentCollaboration = async () => {
        setTestingCollaboration(true);
        setCollaborationResult(null);

        try {
            if (agents.length === 0) {
                setCollaborationResult('❌ No agents hired yet. Please hire at least one agent to test collaboration.');
                return;
            }

            // Create a test task WITHOUT assigning to specific agent
            // The orchestrator will route it to the appropriate agent(s)
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
                // Don't assign to specific agent - let orchestrator decide
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
            case 'manager':
                return 'bg-purple-100 text-purple-800 border-purple-300';
            case 'senior':
                return 'bg-blue-100 text-blue-800 border-blue-300';
            case 'junior':
                return 'bg-green-100 text-green-800 border-green-300';
            default:
                return 'bg-gray-100 text-gray-800 border-gray-300';
        }
    };

    const getStatusIndicator = (status: string) => {
        switch (status) {
            case 'active':
                return <span className="flex items-center text-green-600">
                    <span className="w-2 h-2 bg-green-600 rounded-full mr-2 animate-pulse"></span>
                    Active
                </span>;
            case 'idle':
                return <span className="flex items-center text-gray-600">
                    <span className="w-2 h-2 bg-gray-400 rounded-full mr-2"></span>
                    Idle
                </span>;
            case 'working':
                return <span className="flex items-center text-blue-600">
                    <span className="w-2 h-2 bg-blue-600 rounded-full mr-2 animate-pulse"></span>
                    Working
                </span>;
            default:
                return <span className="flex items-center text-gray-600">
                    <span className="w-2 h-2 bg-gray-400 rounded-full mr-2"></span>
                    {status}
                </span>;
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading your agents...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">My Virtual Employees</h1>
                <p className="mt-2 text-gray-600">
                    Manage your hired agents and test orchestrator-based collaboration
                </p>
            </div>

            {error && (
                <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
                    <p className="text-red-800">{error}</p>
                </div>
            )}

            {/* Multi-Agent Collaboration Test Section */}
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

            {/* Agents List */}
            {agents.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                    <svg
                        className="mx-auto h-12 w-12 text-gray-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                        />
                    </svg>
                    <h3 className="mt-4 text-lg font-medium text-gray-900">No agents hired yet</h3>
                    <p className="mt-2 text-gray-600">
                        Visit the Marketplace to hire your first Virtual Employee
                    </p>
                    <a
                        href="/marketplace"
                        className="mt-4 inline-block px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                    >
                        Browse Marketplace
                    </a>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {agents.map((agent) => (
                        <div
                            key={agent.id}
                            className="bg-white rounded-lg shadow-md border border-gray-200 p-6 hover:shadow-lg transition-shadow"
                        >
                            {/* Agent Header */}
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex-1">
                                    <h3 className="text-lg font-semibold text-gray-900">
                                        {agent.persona_name}
                                    </h3>
                                    <p className="text-sm text-gray-600">{agent.ve_details?.role}</p>
                                </div>
                                <div className="ml-4">
                                    {getStatusIndicator(agent.status)}
                                </div>
                            </div>

                            {/* Seniority Badge */}
                            <div className="mb-4">
                                <span
                                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getSeniorityBadgeColor(
                                        agent.ve_details?.seniority_level
                                    )}`}
                                >
                                    {agent.ve_details?.seniority_level?.toUpperCase()}
                                </span>
                            </div>

                            {/* Agent Details */}
                            <div className="space-y-2 text-sm">
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

                            {/* Agent Type */}
                            <div className="mt-4 pt-4 border-t border-gray-200">
                                <p className="text-xs text-gray-500">
                                    Agent Type: <span className="font-mono text-gray-700">{agent.agent_type}</span>
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            )}

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

                    <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-sm text-blue-900 font-semibold mb-2">
                            💡 How Task Routing Works:
                        </p>
                        <div className="text-sm text-blue-800 space-y-2">
                            <p>
                                The <strong>Shared Orchestrator</strong> analyzes every task first. It understands your team's structure and the task's domain (e.g., Marketing, IT).
                            </p>
                            <ul className="list-disc list-inside ml-2 space-y-1">
                                <li><strong>Domain Matching:</strong> Marketing tasks go to Marketing Managers; IT tasks go to IT Managers.</li>
                                <li><strong>Cross-Functional:</strong> The Orchestrator identifies the primary department for complex tasks.</li>
                                <li><strong>Specialist Fallback:</strong> If no manager exists for a domain, it routes to the best specialist.</li>
                            </ul>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MyAgents;
