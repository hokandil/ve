import React, { useState } from 'react';
import { Button, Input, Card } from './ui';
import { customerAPI } from '../services/api';
import { useToast } from '../components/ui/Toast';

interface HireAgentModalProps {
    isOpen: boolean;
    onClose: () => void;
    agent: {
        id: string;
        name: string;
        role: string;
        pricing_monthly: number;
    } | null;
}

const HireAgentModal: React.FC<HireAgentModalProps> = ({ isOpen, onClose, agent }) => {
    const [personaName, setPersonaName] = useState('');
    const [personaEmail, setPersonaEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const { addToast } = useToast();

    if (!agent || !isOpen) return null;

    const handleHire = async () => {
        setLoading(true);
        try {
            await customerAPI.hire(
                agent.id,
                personaName || agent.name,
                personaEmail || undefined
            );
            addToast("success", `You have successfully hired ${personaName || agent.name}.`);
            onClose();
            // Redirect to my-team page
            window.location.href = '/my-team';
        } catch (error: any) {
            console.error("Failed to hire agent:", error);

            // Handle Pydantic validation errors (422)
            let errorMessage = "Could not hire agent. Please try again.";
            if (error.response?.data?.detail) {
                const detail = error.response.data.detail;
                // If detail is an array of Pydantic validation errors
                if (Array.isArray(detail)) {
                    errorMessage = detail.map((err: any) => `${err.loc.join('.')}: ${err.msg}`).join(', ');
                } else if (typeof detail === 'string') {
                    errorMessage = detail;
                }
            }

            addToast("error", errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
            <Card className="w-full max-w-md p-6 bg-white" onClick={(e) => e.stopPropagation()}>
                <div className="space-y-4">
                    <div>
                        <h2 className="text-2xl font-bold text-slate-900">Hire {agent.name}</h2>
                        <p className="text-sm text-slate-500 mt-1">Customize your new virtual employee's persona.</p>
                    </div>

                    <div className="space-y-4">
                        <div>
                            <label htmlFor="name" className="block text-sm font-medium text-slate-700 mb-1">
                                Name
                            </label>
                            <Input
                                id="name"
                                defaultValue={agent.name}
                                onChange={(e) => setPersonaName(e.target.value)}
                                placeholder="e.g. Sarah"
                            />
                        </div>

                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1">
                                Email (Optional)
                            </label>
                            <Input
                                id="email"
                                onChange={(e) => setPersonaEmail(e.target.value)}
                                placeholder="Custom email address"
                            />
                        </div>

                        <div className="text-sm text-slate-500 bg-slate-50 p-3 rounded">
                            <p>Monthly Cost: <span className="font-semibold text-slate-900">${agent.pricing_monthly}/mo</span></p>
                        </div>
                    </div>

                    <div className="flex gap-3 justify-end pt-4">
                        <Button variant="outline" onClick={onClose}>Cancel</Button>
                        <Button onClick={handleHire} disabled={loading}>
                            {loading ? "Hiring..." : "Confirm Hire"}
                        </Button>
                    </div>
                </div>
            </Card>
        </div>
    );
};

export default HireAgentModal;
