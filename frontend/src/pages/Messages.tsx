import React, { useState } from 'react';
import { Mail, Send } from 'lucide-react';
import { useMessages } from '../services/messageAPI';
import { Card, Button, Badge } from '../components/ui';
import { PageLayout } from '../components/layout';
import { ComposeModal } from '../components/messages/ComposeModal';

const Messages: React.FC = () => {
    const [selectedFolder, setSelectedFolder] = useState('inbox');
    const [isComposeOpen, setIsComposeOpen] = useState(false);
    const { data: messages = [], isLoading } = useMessages(selectedFolder);

    const folders = [
        { id: 'inbox', label: 'Inbox', count: messages.filter((m: any) => !m.read).length },
        { id: 'sent', label: 'Sent', count: 0 },
    ];

    if (isLoading) {
        return (
            <PageLayout title="Messages">
                <div className="flex items-center justify-center h-64">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
                </div>
            </PageLayout>
        );
    }

    return (
        <PageLayout title="Messages">
            <div className="mb-6 flex items-center justify-between">
                <div className="flex gap-2">
                    {folders.map((folder) => (
                        <Button
                            key={folder.id}
                            variant={selectedFolder === folder.id ? 'primary' : 'outline'}
                            onClick={() => setSelectedFolder(folder.id)}
                        >
                            {folder.label}
                            {folder.count > 0 && (
                                <Badge variant="error" className="ml-2">
                                    {folder.count}
                                </Badge>
                            )}
                        </Button>
                    ))}
                </div>
                <Button onClick={() => setIsComposeOpen(true)}>
                    <Send className="mr-2 h-4 w-4" />
                    Compose
                </Button>
            </div>

            <Card>
                {messages.length === 0 ? (
                    <div className="p-12 text-center text-slate-500">
                        <Mail className="mx-auto h-12 w-12 mb-4 text-slate-300" />
                        <p>No messages in {selectedFolder}</p>
                    </div>
                ) : (
                    <div className="divide-y divide-slate-200">
                        {messages.map((message: any) => (
                            <div
                                key={message.id}
                                className={`p-4 hover:bg-slate-50 cursor-pointer ${!message.read ? 'bg-blue-50' : ''
                                    }`}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <h4 className={`font-medium ${!message.read ? 'font-bold' : ''}`}>
                                                {message.subject}
                                            </h4>
                                            {!message.read && <Badge variant="info">New</Badge>}
                                        </div>
                                        <p className="text-sm text-slate-600 line-clamp-2">{message.content}</p>
                                    </div>
                                    <span className="text-xs text-slate-500 ml-4">
                                        {new Date(message.created_at).toLocaleDateString()}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </Card>

            <ComposeModal
                isOpen={isComposeOpen}
                onClose={() => setIsComposeOpen(false)}
            />
        </PageLayout>
    );
};

export default Messages;
