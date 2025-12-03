import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, RefreshCw, Settings } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Select, Textarea, Badge } from '../components/ui';

interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
}

const Playground: React.FC = () => {
    const [selectedVE, setSelectedVE] = useState('1');
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Mock VEs
    const veOptions = [
        { value: '1', label: 'Marketing Manager' },
        { value: '2', label: 'Content Writer' },
        { value: '3', label: 'Sales Representative' },
    ];

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim()) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsTyping(true);

        // Simulate AI response
        setTimeout(() => {
            const aiMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: `This is a simulated response from the ${veOptions.find(v => v.value === selectedVE)?.label}. In the real implementation, this would call the backend agent runtime.`,
                timestamp: new Date(),
            };
            setMessages(prev => [...prev, aiMsg]);
            setIsTyping(false);
        }, 1500);
    };

    const clearChat = () => {
        setMessages([]);
    };

    return (
        <div className="flex h-[calc(100vh-80px)] p-6 gap-6">
            {/* Sidebar Configuration */}
            <div className="w-80 flex-shrink-0">
                <Card className="h-full">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Settings className="h-5 w-5" />
                            Configuration
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div>
                            <label className="text-sm font-medium text-slate-700 mb-2 block">
                                Select VE Template
                            </label>
                            <Select
                                value={selectedVE}
                                onChange={(val) => setSelectedVE(val as string)}
                                options={veOptions}
                            />
                        </div>

                        <div>
                            <label className="text-sm font-medium text-slate-700 mb-2 block">
                                System Prompt Override
                            </label>
                            <Textarea
                                placeholder="Override the default system prompt for this session..."
                                className="h-40 text-xs font-mono"
                            />
                        </div>

                        <div>
                            <label className="text-sm font-medium text-slate-700 mb-2 block">
                                Model Settings
                            </label>
                            <div className="space-y-4">
                                <div>
                                    <div className="flex justify-between text-xs mb-1">
                                        <span>Temperature</span>
                                        <span>0.7</span>
                                    </div>
                                    <input type="range" min="0" max="1" step="0.1" defaultValue="0.7" className="w-full" />
                                </div>
                            </div>
                        </div>

                        <Button variant="outline" className="w-full" onClick={clearChat}>
                            <RefreshCw className="mr-2 h-4 w-4" />
                            Reset Session
                        </Button>
                    </CardContent>
                </Card>
            </div>

            {/* Chat Area */}
            <div className="flex-1 flex flex-col bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
                    <h3 className="font-semibold text-slate-800">
                        Testing: {veOptions.find(v => v.value === selectedVE)?.label}
                    </h3>
                    <Badge variant="success">Online</Badge>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.length === 0 && (
                        <div className="h-full flex flex-col items-center justify-center text-slate-400">
                            <Bot className="h-12 w-12 mb-4 opacity-50" />
                            <p>Start a conversation to test the VE's responses.</p>
                        </div>
                    )}

                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                        >
                            <div className={`
                w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                ${msg.role === 'user' ? 'bg-indigo-100 text-indigo-600' : 'bg-green-100 text-green-600'}
              `}>
                                {msg.role === 'user' ? <User className="h-5 w-5" /> : <Bot className="h-5 w-5" />}
                            </div>

                            <div className={`
                max-w-[80%] rounded-lg p-3 text-sm
                ${msg.role === 'user'
                                    ? 'bg-indigo-600 text-white rounded-tr-none'
                                    : 'bg-slate-100 text-slate-800 rounded-tl-none'}
              `}>
                                {msg.content}
                                <div className={`text-[10px] mt-1 opacity-70 ${msg.role === 'user' ? 'text-indigo-100' : 'text-slate-500'}`}>
                                    {msg.timestamp.toLocaleTimeString()}
                                </div>
                            </div>
                        </div>
                    ))}

                    {isTyping && (
                        <div className="flex gap-3">
                            <div className="w-8 h-8 rounded-full bg-green-100 text-green-600 flex items-center justify-center flex-shrink-0">
                                <Bot className="h-5 w-5" />
                            </div>
                            <div className="bg-slate-100 rounded-lg rounded-tl-none p-4 flex items-center gap-1">
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <div className="p-4 border-t border-slate-200 bg-white">
                    <form onSubmit={handleSendMessage} className="flex gap-2">
                        <Input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type a message to test..."
                            className="flex-1"
                            autoFocus
                        />
                        <Button type="submit" disabled={!input.trim() || isTyping}>
                            <Send className="h-4 w-4" />
                        </Button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default Playground;
