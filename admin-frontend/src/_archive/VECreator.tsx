import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Save, Plus, Trash2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Textarea, Select, Badge } from '../components/ui';

const veSchema = z.object({
    name: z.string().min(1, 'Name is required'),
    role: z.string().min(1, 'Role is required'),
    department: z.string().min(1, 'Department is required'),
    seniority: z.enum(['Junior', 'Mid', 'Senior', 'Manager', 'Director']),
    description: z.string().min(10, 'Description must be at least 10 characters'),
    systemPrompt: z.string().min(20, 'System prompt must be at least 20 characters'),
    pricing: z.number().min(0, 'Pricing must be positive'),
});

type VEFormData = z.infer<typeof veSchema>;

const VECreator: React.FC = () => {
    const [capabilities, setCapabilities] = useState<string[]>([]);
    const [newCapability, setNewCapability] = useState('');
    const [tools] = useState<string[]>([]);

    const {
        register,
        handleSubmit,
        formState: { errors },
        setValue,
        watch,
    } = useForm<VEFormData>({
        resolver: zodResolver(veSchema),
        defaultValues: {
            seniority: 'Mid',
            pricing: 199,
        },
    });

    const seniority = watch('seniority');

    const addCapability = () => {
        if (newCapability.trim()) {
            setCapabilities([...capabilities, newCapability.trim()]);
            setNewCapability('');
        }
    };

    const removeCapability = (index: number) => {
        setCapabilities(capabilities.filter((_, i) => i !== index));
    };

    const onSubmit = async (data: VEFormData) => {
        const veData = {
            ...data,
            capabilities,
            tools,
            status: 'beta',
        };

        console.log('Creating VE:', veData);
        // TODO: Call API to create VE
        alert('VE template created successfully!');
    };

    return (
        <div className="p-8">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-slate-900">VE Creator</h1>
                <p className="text-slate-600">Create a new virtual employee template</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <Card>
                    <CardHeader>
                        <CardTitle>Basic Information</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-4 md:grid-cols-2">
                            <Input
                                label="VE Name"
                                placeholder="e.g., Marketing Manager"
                                error={errors.name?.message}
                                {...register('name')}
                            />
                            <Input
                                label="Role"
                                placeholder="e.g., Marketing Manager"
                                error={errors.role?.message}
                                {...register('role')}
                            />
                        </div>

                        <div className="grid gap-4 md:grid-cols-3">
                            <Input
                                label="Department"
                                placeholder="e.g., Marketing"
                                error={errors.department?.message}
                                {...register('department')}
                            />
                            <Select
                                label="Seniority"
                                value={seniority}
                                onChange={(value) => setValue('seniority', value as any)}
                                options={[
                                    { value: 'Junior', label: 'Junior' },
                                    { value: 'Mid', label: 'Mid-Level' },
                                    { value: 'Senior', label: 'Senior' },
                                    { value: 'Manager', label: 'Manager' },
                                    { value: 'Director', label: 'Director' },
                                ]}
                                error={errors.seniority?.message}
                            />
                            <Input
                                label="Monthly Pricing ($)"
                                type="number"
                                placeholder="199"
                                error={errors.pricing?.message}
                                {...register('pricing', { valueAsNumber: true })}
                            />
                        </div>

                        <Textarea
                            label="Description"
                            placeholder="Describe what this VE does..."
                            rows={3}
                            error={errors.description?.message}
                            {...register('description')}
                        />
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>AI Configuration</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Textarea
                            label="System Prompt"
                            placeholder="You are a professional marketing manager with expertise in..."
                            rows={6}
                            error={errors.systemPrompt?.message}
                            {...register('systemPrompt')}
                        />
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Capabilities</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="mb-4 flex gap-2">
                            <Input
                                placeholder="Add a capability..."
                                value={newCapability}
                                onChange={(e) => setNewCapability(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCapability())}
                            />
                            <Button type="button" onClick={addCapability}>
                                <Plus className="h-4 w-4" />
                            </Button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {capabilities.map((cap, index) => (
                                <Badge key={index} variant="info" className="flex items-center gap-2">
                                    {cap}
                                    <button
                                        type="button"
                                        onClick={() => removeCapability(index)}
                                        className="hover:text-red-600"
                                    >
                                        <Trash2 className="h-3 w-3" />
                                    </button>
                                </Badge>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                <div className="flex justify-end gap-3">
                    <Button type="button" variant="outline">
                        Cancel
                    </Button>
                    <Button type="submit">
                        <Save className="mr-2 h-4 w-4" />
                        Create VE Template
                    </Button>
                </div>
            </form>
        </div>
    );
};

export default VECreator;
