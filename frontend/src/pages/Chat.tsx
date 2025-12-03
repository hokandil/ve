import React, { useState, useEffect, useRef } from 'react';
import { Send, User, Bot, MoreVertical } from 'lucide-react';
import { PageLayout } from '../components/layout';
import { customerAPI, chatAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Avatar, Button, Input, Card } from '../components/ui';

interface Message {
    id: string;
    content: string;
    from_type: 'customer' | 've';
    created_at: string;
}

interface ChatVE {
    id: string;
    persona_name: string;
    ve_details?: {
        role: string;
        icon_url?: string;
    };
}

const Chat: React.FC = () => {
    const { user } = useAuth();
    const [ves, setVes] = useState<ChatVE[]>([]);
    const [selectedVE, setSelectedVE] = useState<ChatVE | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const [sending, setSending] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        loadVEs();
    }, [user]);

    useEffect(() => {
        if (selectedVE) {
            loadHistory(selectedVE.id);
        }
    }, [selectedVE]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    const loadVEs = async () => {
        if (!user) return;
        try {
            const data: ChatVE[] = await customerAPI.listVEs();
            setVes(data || []);
            if (data && data.length > 0) {
                setSelectedVE(data[0]);
            }
        } catch (error) {
            console.error('Error loading VEs:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadHistory = async (veId: string) => {
        try {
            const history = await chatAPI.getHistory(veId);
            setMessages(history || []);
        } catch (error) {
            console.error('Error loading history:', error);
        }
    };

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newMessage.trim() || !selectedVE) return;

        const tempId = Date.now().toString();
        const userMessageContent = newMessage;

        // Add user message immediately
        const tempUserMessage: Message = {
            id: tempId,
            content: userMessageContent,
            from_type: 'customer',
            created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, tempUserMessage]);
        setNewMessage('');
        setSending(true);

        // Add placeholder for agent response
        const agentTempId = `agent-${Date.now()}`;
        const tempAgentMessage: Message = {
            id: agentTempId,
            content: '',
            from_type: 've',
            created_at: new Date().toISOString()
        };
        setMessages(prev => [...prev, tempAgentMessage]);

        try {
            let userMessageSaved: any = null;
            let agentMessageContent = '';

            await chatAPI.streamMessage(
                selectedVE.id,
                userMessageContent,
                (event) => {
                    console.log('Stream event:', event);

                    if (event.type === 'user_message') {
                        // Replace temp user message with saved one
                        userMessageSaved = event.data;
                        setMessages(prev => prev.map(m =>
                            m.id === tempId ? { ...event.data, from_type: 'customer' } : m
                        ));
                    } else if (event.type === 'message' || event.type === 'artifact') {
                        // Append to agent message
                        agentMessageContent += event.content;
                        setMessages(prev => prev.map(m =>
                            m.id === agentTempId ? { ...m, content: agentMessageContent } : m
                        ));
                    } else if (event.type === 'agent_message_saved') {
                        // Replace temp agent message with saved one
                        setMessages(prev => prev.map(m =>
                            m.id === agentTempId ? { ...event.data, from_type: 've' } : m
                        ));
                    } else if (event.type === 'error') {
                        console.error('Agent error:', event.content);
                        setMessages(prev => prev.map(m =>
                            m.id === agentTempId ? { ...m, content: `Error: ${event.content}` } : m
                        ));
                    }
                },
                (error) => {
                    console.error('Stream error:', error);
                    setMessages(prev => prev.map(m =>
                        m.id === agentTempId ? { ...m, content: `Error: ${error.message}` } : m
                    ));
                },
                () => {
                    console.log('Stream complete');
                }
            );
        } catch (error) {
            console.error('Error sending message:', error);
            setMessages(prev => prev.map(m =>
                m.id === agentTempId ? { ...m, content: `Error: ${error}` } : m
            ));
        } finally {
            setSending(false);
        }
    };

    if (loading) {
        return (
            <PageLayout title="Chat">
                <div className="flex items-center justify-center h-64">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
                </div>
            </PageLayout>
        );
    }

    return (
        <PageLayout title="Chat">
            <div className="flex h-[calc(100vh-200px)] bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
                {/* Sidebar - VE List */}
                <div className="w-1/4 border-r border-slate-200 bg-slate-50 flex flex-col">
                    <div className="p-4 border-b border-slate-200">
                        <h3 className="font-semibold text-slate-700">Team Members</h3>
                    </div>
                    <div className="flex-1 overflow-y-auto">
                        {ves.map(ve => (
                            <div
                                key={ve.id}
                                onClick={() => setSelectedVE(ve)}
                                className={`p-4 flex items-center gap-3 cursor-pointer hover:bg-slate-100 transition-colors ${selectedVE?.id === ve.id ? 'bg-white border-l-4 border-indigo-600 shadow-sm' : ''
                                    }`}
                            >
                                {ve.ve_details?.icon_url ? (
                                    <img src={ve.ve_details.icon_url} alt={ve.persona_name} className="h-10 w-10 rounded-full object-cover" />
                                ) : (
                                    <Avatar fallback={ve.persona_name.substring(0, 2)} />
                                )}
                                <div className="overflow-hidden">
                                    <p className="font-medium text-slate-900 truncate">{ve.persona_name}</p>
                                    <p className="text-xs text-slate-500 truncate">{ve.ve_details?.role}</p>
                                </div>
                            </div>
                        ))}
                        {ves.length === 0 && (
                            <div className="p-4 text-center text-slate-500 text-sm">
                                No team members hired yet.
                            </div>
                        )}
                    </div>
                </div>

                {/* Chat Area */}
                <div className="flex-1 flex flex-col">
                    {selectedVE ? (
                        <>
                            {/* Header */}
                            <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-white">
                                <div className="flex items-center gap-3">
                                    {selectedVE.ve_details?.icon_url ? (
                                        <img src={selectedVE.ve_details.icon_url} alt={selectedVE.persona_name} className="h-10 w-10 rounded-full object-cover" />
                                    ) : (
                                        <Avatar fallback={selectedVE.persona_name.substring(0, 2)} />
                                    )}
                                    <div>
                                        <h3 className="font-bold text-slate-900">{selectedVE.persona_name}</h3>
                                        <p className="text-xs text-slate-500">{selectedVE.ve_details?.role}</p>
                                    </div>
                                </div>
                                <Button variant="ghost" size="sm">
                                    <MoreVertical className="h-5 w-5 text-slate-400" />
                                </Button>
                            </div>

                            {/* Messages */}
                            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
                                {messages.map((msg) => (
                                    <div
                                        key={msg.id}
                                        className={`flex ${msg.from_type === 'customer' ? 'justify-end' : 'justify-start'}`}
                                    >
                                        <div
                                            className={`max-w-[70%] rounded-2xl p-4 shadow-sm ${msg.from_type === 'customer'
                                                ? 'bg-indigo-600 text-white rounded-br-none'
                                                : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none'
                                                }`}
                                        >
                                            <p className="text-sm">{msg.content}</p>
                                            <p className={`text-[10px] mt-1 ${msg.from_type === 'customer' ? 'text-indigo-200' : 'text-slate-400'}`}>
                                                {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                                <div ref={messagesEndRef} />
                            </div>

                            {/* Input */}
                            <div className="p-4 bg-white border-t border-slate-200">
                                <form onSubmit={handleSendMessage} className="flex gap-2">
                                    <Input
                                        value={newMessage}
                                        onChange={(e) => setNewMessage(e.target.value)}
                                        placeholder={`Message ${selectedVE.persona_name}...`}
                                        className="flex-1"
                                        disabled={sending}
                                    />
                                    <Button type="submit" disabled={!newMessage.trim() || sending}>
                                        <Send className="h-4 w-4" />
                                    </Button>
                                </form>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-slate-400">
                            Select a team member to start chatting
                        </div>
                    )}
                </div>
            </div>
        </PageLayout>
    );
};

export default Chat;
