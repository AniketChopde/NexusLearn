import React from 'react';
import { useChatStore } from '../stores/chatStore';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Loading } from '../components/ui/Loading';
import { Send, Bot, User, ArrowLeft } from 'lucide-react';
import { formatDate } from '../lib/utils';
import { useNavigate, useSearchParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';

export const ChatPage: React.FC = () => {
    const { messages, isTyping, sendMessage, createSession, activeSession, setChatContext } = useChatStore();
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [input, setInput] = React.useState('');
    const planId = searchParams.get('planId');
    const messagesEndRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
        if (!activeSession) {
            createSession();
        }
    }, []);

    React.useEffect(() => {
        const moduleId = searchParams.get('moduleId');
        const examType = searchParams.get('examType');
        const chapter = searchParams.get('chapter');
        const topic = searchParams.get('topic');

        const ctx: Record<string, any> = {};
        if (moduleId) ctx.module_id = moduleId;
        if (examType) ctx.exam_type = examType;
        if (chapter) ctx.chapter = chapter;
        if (topic) ctx.topic = topic;

        if (Object.keys(ctx).length > 0) {
            setChatContext(ctx);
        }
    }, [searchParams, setChatContext]);

    React.useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const message = input;
        setInput('');
        await sendMessage(message);
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const quickPrompts = [
        'Explain in simple terms',
        'Give me examples',
        'Create a quiz',
        'Show mindmap',
    ];

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col">
            <div className="mb-4 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Learning Chat</h1>
                    <p className="text-muted-foreground mt-2">
                        Ask me anything about your study topics
                    </p>
                </div>
                {planId && (
                    <Button
                        variant="ghost"
                        className="gap-2 text-primary font-bold"
                        onClick={() => navigate(`/study-plans/${planId}`)}
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Back to Learning
                    </Button>
                )}
            </div>

            <Card className="flex-1 flex flex-col overflow-hidden">
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {messages.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-full text-center">
                            <Bot className="h-16 w-16 text-muted-foreground mb-4" />
                            <h3 className="text-xl font-semibold mb-2">Start a Conversation</h3>
                            <p className="text-muted-foreground max-w-md">
                                Ask me to explain concepts, generate quizzes, create mindmaps, or find resources
                            </p>
                        </div>
                    )}

                    {messages.map((message, index) => (
                        <div
                            key={index}
                            className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            {message.role === 'assistant' && (
                                <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                                    <Bot className="h-5 w-5 text-primary-foreground" />
                                </div>
                            )}

                            <div
                                className={`max-w-[70%] rounded-lg p-4 ${message.role === 'user'
                                    ? 'bg-primary text-primary-foreground'
                                    : 'bg-accent'
                                    }`}
                            >
                                <div className={`prose ${message.role === 'user' ? 'prose-invert' : 'prose-zinc dark:prose-invert'} max-w-none prose-sm`}>
                                    <ReactMarkdown>{message.content}</ReactMarkdown>
                                </div>
                                <p className="text-xs opacity-70 mt-2">
                                    {formatDate(message.timestamp)}
                                </p>
                            </div>

                            {message.role === 'user' && (
                                <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
                                    <User className="h-5 w-5" />
                                </div>
                            )}
                        </div>
                    ))}

                    {isTyping && (
                        <div className="flex gap-3">
                            <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                                <Bot className="h-5 w-5 text-primary-foreground" />
                            </div>
                            <div className="bg-accent rounded-lg p-4">
                                <Loading size="sm" text="AI is thinking..." />
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Quick Prompts */}
                {messages.length === 0 && (
                    <div className="px-6 pb-4">
                        <p className="text-sm text-muted-foreground mb-2">Quick prompts:</p>
                        <div className="flex flex-wrap gap-2">
                            {quickPrompts.map((prompt) => (
                                <Button
                                    key={prompt}
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setInput(prompt)}
                                >
                                    {prompt}
                                </Button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Input */}
                <div className="border-t p-4">
                    <div className="flex gap-2">
                        <Input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask me anything..."
                            className="flex-1"
                        />
                        <Button onClick={handleSend} disabled={!input.trim() || isTyping}>
                            <Send className="h-5 w-5" />
                        </Button>
                    </div>
                </div>
            </Card>
        </div>
    );
};
