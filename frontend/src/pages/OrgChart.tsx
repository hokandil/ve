import React, { useCallback } from 'react';
import ReactFlow, {
    Node,
    Edge,
    Controls,
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Connection,
    BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { PageLayout } from '../components/layout';
import { Card } from '../components/ui';

const initialNodes: Node[] = [
    {
        id: '1',
        type: 'default',
        data: { label: 'CEO (You)' },
        position: { x: 250, y: 0 },
        style: { background: '#6366f1', color: 'white', border: '1px solid #4f46e5', borderRadius: '8px', padding: '10px' },
    },
    {
        id: '2',
        data: { label: 'Marketing Manager' },
        position: { x: 100, y: 100 },
        style: { background: '#10b981', color: 'white', border: '1px solid #059669', borderRadius: '8px', padding: '10px' },
    },
    {
        id: '3',
        data: { label: 'Sales Manager' },
        position: { x: 400, y: 100 },
        style: { background: '#10b981', color: 'white', border: '1px solid #059669', borderRadius: '8px', padding: '10px' },
    },
    {
        id: '4',
        data: { label: 'Content Writer' },
        position: { x: 50, y: 200 },
        style: { background: '#3b82f6', color: 'white', border: '1px solid #2563eb', borderRadius: '8px', padding: '10px' },
    },
    {
        id: '5',
        data: { label: 'Social Media Manager' },
        position: { x: 150, y: 200 },
        style: { background: '#3b82f6', color: 'white', border: '1px solid #2563eb', borderRadius: '8px', padding: '10px' },
    },
    {
        id: '6',
        data: { label: 'Sales Rep' },
        position: { x: 400, y: 200 },
        style: { background: '#3b82f6', color: 'white', border: '1px solid #2563eb', borderRadius: '8px', padding: '10px' },
    },
];

const initialEdges: Edge[] = [
    { id: 'e1-2', source: '1', target: '2', animated: true },
    { id: 'e1-3', source: '1', target: '3', animated: true },
    { id: 'e2-4', source: '2', target: '4' },
    { id: 'e2-5', source: '2', target: '5' },
    { id: 'e3-6', source: '3', target: '6' },
];

const OrgChart: React.FC = () => {
    const [nodes, , onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge(params, eds)),
        [setEdges]
    );

    return (
        <PageLayout title="Organization Chart">
            <Card className="p-0" style={{ height: '600px' }}>
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    fitView
                >
                    <Controls />
                    <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
                </ReactFlow>
            </Card>

            <div className="mt-6 grid gap-4 md:grid-cols-3">
                <Card className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="h-4 w-4 rounded bg-indigo-600"></div>
                        <span className="text-sm font-medium">You</span>
                    </div>
                    <p className="text-xs text-slate-600">Your position in the organization</p>
                </Card>
                <Card className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="h-4 w-4 rounded bg-green-600"></div>
                        <span className="text-sm font-medium">Managers</span>
                    </div>
                    <p className="text-xs text-slate-600">Team leads and managers</p>
                </Card>
                <Card className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="h-4 w-4 rounded bg-blue-600"></div>
                        <span className="text-sm font-medium">Team Members</span>
                    </div>
                    <p className="text-xs text-slate-600">Individual contributors</p>
                </Card>
            </div>
        </PageLayout>
    );
};

export default OrgChart;
