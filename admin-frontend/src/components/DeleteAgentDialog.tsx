import React, { useState } from 'react';
import { Modal, Button } from './ui';
import { AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

interface DeleteAgentDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    agentId: string;
    agentName: string;
}

export const DeleteAgentDialog: React.FC<DeleteAgentDialogProps> = ({
    isOpen,
    onClose,
    onSuccess,
    agentId,
    agentName
}) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleDelete = async () => {
        setLoading(true);
        setError(null);
        try {
            // Call the correct discovery endpoint
            await api.delete(`/discovery/agents/${agentId}`);
            onSuccess();
            onClose();
        } catch (err: any) {
            console.error("Failed to delete agent:", err);
            // Extract error message from response
            const errorMessage = err.response?.data?.detail || "Failed to delete agent. Please try again.";
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Delete Agent"
            size="sm"
        >
            <div className="flex flex-col gap-4">
                <div className="flex items-start gap-3 text-slate-600">
                    <div className="p-2 bg-red-100 rounded-full text-red-600 shrink-0">
                        <AlertTriangle className="h-6 w-6" />
                    </div>
                    <div>
                        <p className="mb-2">
                            Are you sure you want to delete <strong>{agentName}</strong>?
                        </p>
                        <p className="text-sm text-slate-500">
                            This action cannot be undone. It will remove the agent from the marketplace and delete all associated routing configuration.
                        </p>
                    </div>
                </div>

                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                        {error}
                    </div>
                )}

                <div className="flex justify-end gap-3 mt-4">
                    <Button variant="outline" onClick={onClose} disabled={loading}>
                        Cancel
                    </Button>
                    <Button
                        variant="destructive"
                        onClick={handleDelete}
                        isLoading={loading}
                        disabled={loading}
                    >
                        Delete Agent
                    </Button>
                </div>
            </div>
        </Modal>
    );
};
