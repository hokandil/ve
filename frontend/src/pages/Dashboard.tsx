import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Users, CheckSquare, Mail } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Button } from '../components/ui';
import { PageLayout } from '../components/layout';
import { useTasks } from '../services/taskAPI';
import { customerAPI } from '../services/api';
import { messageAPI } from '../services/messageAPI';

const Dashboard: React.FC = () => {
    const navigate = useNavigate();
    const { data: tasks = [] } = useTasks();
    const [totalVEs, setTotalVEs] = useState(0);
    const [pendingMessages, setPendingMessages] = useState(0);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            // Fetch VE count
            const ves = await customerAPI.listVEs();
            setTotalVEs(ves?.length || 0);

            // Fetch unread messages count
            const inbox = await messageAPI.inbox('inbox');
            const unreadCount = inbox?.filter((msg: any) => !msg.read).length || 0;
            setPendingMessages(unreadCount);
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
        }
    };

    const stats = {
        totalVEs,
        activeTasks: tasks.filter((t: any) => t.status !== 'completed').length,
        completedTasks: tasks.filter((t: any) => t.status === 'completed').length,
        pendingMessages,
    };

    const recentTasks = tasks.slice(0, 5);

    return (
        <PageLayout title="Dashboard">
            {/* Stats Grid */}
            <div className="mb-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-slate-600">Total VEs</p>
                                <p className="text-2xl font-bold text-slate-900">{stats.totalVEs}</p>
                            </div>
                            <div className="rounded-full bg-indigo-100 p-3">
                                <Users className="h-6 w-6 text-indigo-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-slate-600">Active Tasks</p>
                                <p className="text-2xl font-bold text-slate-900">{stats.activeTasks}</p>
                            </div>
                            <div className="rounded-full bg-blue-100 p-3">
                                <CheckSquare className="h-6 w-6 text-blue-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-slate-600">Completed</p>
                                <p className="text-2xl font-bold text-slate-900">{stats.completedTasks}</p>
                            </div>
                            <div className="rounded-full bg-green-100 p-3">
                                <CheckSquare className="h-6 w-6 text-green-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-slate-600">Messages</p>
                                <p className="text-2xl font-bold text-slate-900">{stats.pendingMessages}</p>
                            </div>
                            <div className="rounded-full bg-amber-100 p-3">
                                <Mail className="h-6 w-6 text-amber-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Quick Actions */}
            <div className="mb-8">
                <h2 className="mb-4 text-lg font-semibold text-slate-900">Quick Actions</h2>
                <div className="flex gap-4">
                    <Button onClick={() => navigate('/marketplace')}>
                        <Plus className="mr-2 h-4 w-4" />
                        Hire VE
                    </Button>
                    <Button variant="outline" onClick={() => navigate('/tasks')}>
                        <Plus className="mr-2 h-4 w-4" />
                        Create Task
                    </Button>
                </div>
            </div>

            {/* Recent Tasks */}
            <Card>
                <CardHeader>
                    <CardTitle>Recent Tasks</CardTitle>
                </CardHeader>
                <CardContent>
                    {recentTasks.length === 0 ? (
                        <div className="py-8 text-center text-slate-500">
                            <p>No tasks yet. Create your first task to get started!</p>
                            <Button className="mt-4" onClick={() => navigate('/tasks')}>
                                Create Task
                            </Button>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {recentTasks.map((task: any) => (
                                <div
                                    key={task.id}
                                    className="flex items-center justify-between rounded-lg border border-slate-200 p-4 hover:bg-slate-50"
                                >
                                    <div className="flex-1">
                                        <h4 className="font-medium text-slate-900">{task.title}</h4>
                                        <p className="text-sm text-slate-600">{task.description}</p>
                                    </div>
                                    <div className="ml-4">
                                        <span
                                            className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${task.status === 'completed'
                                                ? 'bg-green-100 text-green-800'
                                                : task.status === 'in_progress'
                                                    ? 'bg-blue-100 text-blue-800'
                                                    : 'bg-slate-100 text-slate-800'
                                                }`}
                                        >
                                            {task.status.replace('_', ' ')}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </PageLayout>
    );
};

export default Dashboard;
