import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Save, Plus, Trash2, Code, Edit } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Textarea, Badge } from '../components/ui';

const toolSchema = z.object({
    name: z.string().min(1, 'Name is required'),
    pythonPackage: z.string().min(1, 'Python package is required'),
    functionName: z.string().min(1, 'Function name is required'),
    description: z.string().min(10, 'Description must be at least 10 characters'),
});

type ToolFormData = z.infer<typeof toolSchema>;

interface ParameterData {
    name: string;
    type: 'string' | 'number' | 'boolean' | 'array' | 'object';
    description: string;
    required: boolean;
}

const ToolManager: React.FC = () => {
    const [isCreating, setIsCreating] = useState(false);
    const [parameters, setParameters] = useState<ParameterData[]>([]);
    const [newParameter, setNewParameter] = useState<ParameterData>({
        name: '',
        type: 'string',
        description: '',
        required: true,
    });

    // Mock tools list
    const [tools, setTools] = useState([
        {
            id: '1',
            name: 'web_search',
            description: 'Search the internet for information using Google Search.',
            pythonPackage: 'langchain_community.tools',
            functionName: 'GoogleSearchRun',
            parameters: [{ name: 'query', type: 'string', description: 'The search query', required: true }]
        },
        {
            id: '2',
            name: 'send_email',
            description: 'Send an email to a recipient.',
            pythonPackage: 'app.tools.email',
            functionName: 'send_email',
            parameters: [
                { name: 'to', type: 'string', description: 'Recipient email', required: true },
                { name: 'subject', type: 'string', description: 'Email subject', required: true },
                { name: 'body', type: 'string', description: 'Email body content', required: true }
            ]
        }
    ]);

    const {
        register,
        handleSubmit,
        formState: { errors },
        reset,
    } = useForm<ToolFormData>({
        resolver: zodResolver(toolSchema),
    });

    const addParameter = () => {
        if (newParameter.name && newParameter.description) {
            setParameters([...parameters, newParameter]);
            setNewParameter({
                name: '',
                type: 'string',
                description: '',
                required: true,
            });
        }
    };

    const removeParameter = (index: number) => {
        setParameters(parameters.filter((_, i) => i !== index));
    };

    const onSubmit = (data: ToolFormData) => {
        const newTool = {
            id: Date.now().toString(),
            ...data,
            parameters,
        };

        setTools([...tools, newTool]);
        setIsCreating(false);
        reset();
        setParameters([]);
    };

    if (isCreating) {
        return (
            <div className="p-8">
                <div className="mb-6 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">Create New Tool</h1>
                        <p className="text-slate-600">Define a tool capability for Virtual Employees</p>
                    </div>
                    <Button variant="outline" onClick={() => setIsCreating(false)}>
                        Cancel
                    </Button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-4xl">
                    <Card>
                        <CardHeader>
                            <CardTitle>Tool Definition</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid gap-4 md:grid-cols-2">
                                <Input
                                    label="Tool Name"
                                    placeholder="e.g., web_search"
                                    error={errors.name?.message}
                                    {...register('name')}
                                />
                                <Input
                                    label="Python Package/Module"
                                    placeholder="e.g., app.tools.search"
                                    error={errors.pythonPackage?.message}
                                    {...register('pythonPackage')}
                                />
                            </div>

                            <div className="grid gap-4 md:grid-cols-2">
                                <Input
                                    label="Function Name"
                                    placeholder="e.g., search_google"
                                    error={errors.functionName?.message}
                                    {...register('functionName')}
                                />
                            </div>

                            <Textarea
                                label="Description"
                                placeholder="Describe what this tool does and when the AI should use it..."
                                rows={3}
                                error={errors.description?.message}
                                {...register('description')}
                            />
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Parameters</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="mb-6 p-4 bg-slate-50 rounded-lg border border-slate-200">
                                <h4 className="text-sm font-medium text-slate-900 mb-3">Add Parameter</h4>
                                <div className="grid gap-4 md:grid-cols-4 mb-3">
                                    <Input
                                        placeholder="Name (e.g., query)"
                                        value={newParameter.name}
                                        onChange={(e) => setNewParameter({ ...newParameter, name: e.target.value })}
                                    />
                                    <select
                                        className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                                        value={newParameter.type}
                                        onChange={(e) => setNewParameter({ ...newParameter, type: e.target.value as any })}
                                    >
                                        <option value="string">String</option>
                                        <option value="number">Number</option>
                                        <option value="boolean">Boolean</option>
                                        <option value="array">Array</option>
                                        <option value="object">Object</option>
                                    </select>
                                    <div className="md:col-span-2 flex gap-2">
                                        <Input
                                            placeholder="Description"
                                            className="flex-1"
                                            value={newParameter.description}
                                            onChange={(e) => setNewParameter({ ...newParameter, description: e.target.value })}
                                        />
                                        <Button type="button" onClick={addParameter}>
                                            <Plus className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        id="required"
                                        checked={newParameter.required}
                                        onChange={(e) => setNewParameter({ ...newParameter, required: e.target.checked })}
                                        className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                                    />
                                    <label htmlFor="required" className="text-sm text-slate-600">Required parameter</label>
                                </div>
                            </div>

                            <div className="space-y-2">
                                {parameters.map((param, index) => (
                                    <div key={index} className="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-md">
                                        <div className="flex items-center gap-3">
                                            <Badge variant="info">{param.type}</Badge>
                                            <div>
                                                <p className="font-medium text-slate-900">
                                                    {param.name}
                                                    {param.required && <span className="text-red-500 ml-1">*</span>}
                                                </p>
                                                <p className="text-sm text-slate-500">{param.description}</p>
                                            </div>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => removeParameter(index)}
                                            className="text-slate-400 hover:text-red-600"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                ))}
                                {parameters.length === 0 && (
                                    <p className="text-center text-slate-500 py-4">No parameters defined yet.</p>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    <div className="flex justify-end gap-3">
                        <Button type="button" variant="outline" onClick={() => setIsCreating(false)}>
                            Cancel
                        </Button>
                        <Button type="submit">
                            <Save className="mr-2 h-4 w-4" />
                            Save Tool
                        </Button>
                    </div>
                </form>
            </div>
        );
    }

    return (
        <div className="p-8">
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Tool Manager</h1>
                    <p className="text-slate-600">Manage AI tools and capabilities</p>
                </div>
                <Button onClick={() => setIsCreating(true)}>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Tool
                </Button>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {tools.map((tool) => (
                    <Card key={tool.id} className="hover:shadow-md transition-shadow">
                        <CardHeader>
                            <div className="flex items-start justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-indigo-100 rounded-lg">
                                        <Code className="h-5 w-5 text-indigo-600" />
                                    </div>
                                    <div>
                                        <CardTitle className="text-base">{tool.name}</CardTitle>
                                        <p className="text-xs text-slate-500 font-mono">{tool.functionName}</p>
                                    </div>
                                </div>
                                <Button size="sm" variant="ghost">
                                    <Edit className="h-4 w-4 text-slate-400" />
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm text-slate-600 mb-4 min-h-[40px]">{tool.description}</p>

                            <div>
                                <p className="text-xs font-medium text-slate-700 mb-2">Parameters:</p>
                                <div className="flex flex-wrap gap-1">
                                    {tool.parameters.map((param, idx) => (
                                        <Badge key={idx} variant="default" className="text-xs">
                                            {param.name}
                                        </Badge>
                                    ))}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    );
};

export default ToolManager;
