import React, { useState, useEffect, useRef } from 'react';
import { Send, X, Minimize2, Maximize2, Loader2 } from 'lucide-react';
import { chatAPI } from '../services/api';
import { Button } from './ui/button';
import { Card } from './ui/card';

interface ChatInterfaceProps {
    veId: string;
    agentName: string;
    agentRole: string;
    onClose: () => void;
}

interface Message {
    id: string;
    content: string;
    from_type: 'customer' | 've' | 'system';
    created_at: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ veId, agentName, agentRole, onClose }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isStreaming, setIsStreaming] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Fetch history on mount
    useEffect(() => {
        const loadHistory = async () => {
            try {
                const history = await chatAPI.getHistory(veId);
                setMessages(history.reverse()); // Assuming API returns newest first
            } catch (error) {
                console.error('Failed to load chat history:', error);
            }
        };
        loadHistory();
    }, [veId]);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isStreaming]);

    const handleSend = async () => {
        if (!input.trim() || isStreaming) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            content: input,
            from_type: 'customer',
            created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsStreaming(true);

        // Placeholder for agent response
        const agentMessageId = (Date.now() + 1).toString();
        setMessages(prev => [...prev, {
            id: agentMessageId,
            content: '',
            from_type: 've',
            created_at: new Date().toISOString()
        }]);

        try {
            await chatAPI.streamMessage(
                veId,
                userMessage.content,
                (event) => {
                    if (event.type === 'message') {
                        setMessages(prev => prev.map(msg =>
                            msg.id === agentMessageId
                                ? { ...msg, content: msg.content + event.content }
                                : msg
                        ));
                    } else if (event.type === 'thought') {
                        // Optionally show thoughts
                        console.log('Agent thought:', event.content);
                    } else if (event.type === 'error') {
                        console.error('Agent error:', event.content);
                    }
                },
                (error) => {
                    console.error('Stream error:', error);
                    setIsStreaming(false);
                },
                () => {
                    setIsStreaming(false);
                }
            );
        } catch (error) {
            console.error('Failed to send message:', error);
            setIsStreaming(false);
        }
    };

    return (
        <div className="fixed bottom-4 right-4 w-96 h-[600px] bg-white rounded-lg shadow-2xl border border-gray-200 flex flex-col z-50 overflow-hidden">
            {/* Header */}
            <div className="bg-indigo-600 p-4 flex justify-between items-center text-white">
                <div>
                    <h3 className="font-semibold">{agentName}</h3>
                    <p className="text-xs text-indigo-100">{agentRole}</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={onClose} className="hover:bg-indigo-700 p-1 rounded">
                        <X className="h-4 w-4" />
                    </button>
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 bg-gray-50 space-y-4">
                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`flex ${msg.from_type === 'customer' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-[80%] rounded-lg p-3 ${msg.from_type === 'customer'
                                    ? 'bg-indigo-600 text-white'
                                    : 'bg-white border border-gray-200 text-gray-800 shadow-sm'
                                }`}
                        >
                            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                            <span className="text-xs opacity-70 mt-1 block">
                                {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                        </div>
                    </div>
                ))}
                {isStreaming && messages[messages.length - 1]?.from_type === 've' && messages[messages.length - 1].content === '' && (
                    <div className="flex justify-start">
                        <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-sm">
                            <Loader2 className="h-4 w-4 animate-spin text-indigo-600" />
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-white border-t border-gray-200">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Type a message..."
                        className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        disabled={isStreaming}
                    />
                    <Button
                        onClick={handleSend}
                        disabled={!input.trim() || isStreaming}
                        className="bg-indigo-600 hover:bg-indigo-700"
                    >
                        <Send className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    );
};
