import { useState, useRef, useEffect } from 'react';
import { Send, Mic, Sparkles, Code2, Image as ImageIcon, Search, Settings, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

const ChatMessage = ({ msg }) => {
    const isAi = msg.role === 'assistant';
    
    return (
        <div className={`flex gap-4 p-6 ${isAi ? 'bg-void' : ''}`}>
            <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${isAi ? 'bg-plasma/20 text-plasma' : 'bg-graphite text-ghost/60'}`}>
                {isAi ? <Sparkles className="w-5 h-5" /> : <div className="w-3 h-3 bg-ghost/40 rounded-full" />}
            </div>
            <div className="flex-1 space-y-4">
                <div className="font-sans font-semibold text-ghost/80">
                    {isAi ? 'AI Gateway' : 'You'}
                </div>
                <div className="font-sans text-ghost/90 leading-relaxed whitespace-pre-wrap">
                    {msg.content}
                </div>
                {msg.latency && (
                    <div className="flex items-center gap-2 mt-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-plasma"></div>
                        <span className="font-mono text-xs text-plasma/70">{msg.provider} • {msg.latency}ms</span>
                    </div>
                )}
            </div>
        </div>
    );
};

const Chat = () => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Xin chào. Hệ thống định tuyến đã sẵn sàng. Bạn muốn thực hiện tác vụ nào hôm nay?', provider: 'Groq (Llama 3)', latency: 120 }
    ]);
    const [input, setInput] = useState('');
    const [mode, setMode] = useState('chat');
    const [isRecording, setIsRecording] = useState(false);
    
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;
        
        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        
        try {
            const res = await fetch('/v1/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: [...messages, userMsg],
                    mode: 'chat'
                })
            });
            
            if (res.ok) {
                const data = await res.json();
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: data.reply,
                    provider: data.router?.provider || 'Unknown',
                    latency: data.router?.latency_ms ? Math.round(data.router.latency_ms) : 0
                }]);
            } else {
                const err = await res.json();
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: `Error: ${err.detail || res.statusText}`,
                    provider: 'System',
                    latency: 0
                }]);
            }
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: `Error: ${error.message}`,
                provider: 'System',
                latency: 0
            }]);
        }
    };

    const toggleRecording = () => {
        setIsRecording(!isRecording);
    };

    const modes = [
        { id: 'chat', icon: Sparkles, label: 'Chat' },
        { id: 'research', icon: Search, label: 'Research' },
        { id: 'code', icon: Code2, label: 'Code' },
        { id: 'image', icon: ImageIcon, label: 'Image' },
    ];

    return (
        <div className="flex h-screen bg-[#05050A]">
            {/* Sidebar */}
            <div className="w-64 border-r border-graphite bg-void flex flex-col">
                <div className="p-6 border-b border-graphite flex items-center gap-3">
                    <Link to="/" className="text-ghost/60 hover:text-ghost transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div className="font-sans font-bold text-ghost tracking-tight">Gateway<span className="text-plasma">.</span></div>
                </div>
                <div className="p-4 flex-1 overflow-y-auto">
                    <div className="text-xs font-mono text-ghost/40 mb-4 px-2">HISTORY</div>
                    {/* Mock history items */}
                    <div className="flex flex-col gap-1">
                        <button className="text-left px-3 py-2 rounded-lg bg-graphite/40 text-ghost/80 text-sm font-sans truncate hover:bg-graphite transition-colors">
                            Thiết lập AI Gateway
                        </button>
                        <button className="text-left px-3 py-2 rounded-lg text-ghost/60 text-sm font-sans truncate hover:bg-graphite/40 transition-colors">
                            Phân tích chi phí Cloud
                        </button>
                    </div>
                </div>
                <div className="p-4 border-t border-graphite">
                    <button className="flex items-center gap-2 text-ghost/60 hover:text-ghost transition-colors w-full px-2 py-2">
                        <Settings className="w-4 h-4" />
                        <span className="text-sm font-sans">Settings</span>
                    </button>
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col relative overflow-hidden bg-[url('https://images.unsplash.com/photo-1518423238622-0e363674dcfc?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center">
                <div className="absolute inset-0 bg-void/95 backdrop-blur-3xl z-0"></div>
                
                {/* Header */}
                <div className="relative z-10 h-16 border-b border-graphite flex items-center justify-between px-6 bg-void/50 backdrop-blur-md">
                    <div className="flex items-center gap-2 bg-graphite/40 p-1 rounded-lg">
                        {modes.map(m => (
                            <button 
                                key={m.id}
                                onClick={() => setMode(m.id)}
                                className={`flex items-center gap-2 px-3 py-[6px] rounded-md text-sm transition-all ${mode === m.id ? 'bg-plasma/20 text-plasma shadow-sm' : 'text-ghost/60 hover:text-ghost hover:bg-graphite/60'}`}
                            >
                                <m.icon className="w-4 h-4" />
                                <span className="font-sans font-medium">{m.label}</span>
                            </button>
                        ))}
                    </div>
                    <div className="flex items-center gap-2 px-3 py-1 bg-green-500/10 rounded-full border border-green-500/20">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                        <span className="text-xs font-mono text-green-500">System Healthy</span>
                    </div>
                </div>

                {/* Messages */}
                <div className="relative z-10 flex-1 overflow-y-auto">
                    <div className="max-w-3xl mx-auto py-8">
                        {messages.map((msg, i) => (
                            <ChatMessage key={i} msg={msg} />
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {/* Input Area */}
                <div className="relative z-10 p-6 bg-gradient-to-t from-void to-transparent">
                    <div className="max-w-3xl mx-auto">
                        <form onSubmit={handleSubmit} className="relative bg-graphite/60 backdrop-blur-xl border border-ghost/10 rounded-2xl p-2 focus-within:border-plasma/50 transition-colors shadow-2xl">
                            <textarea 
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Message Gateway..."
                                className="w-full bg-transparent text-ghost placeholder-ghost/30 resize-none outline-none py-3 px-4 font-sans max-h-32 min-h-[60px]"
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        handleSubmit(e);
                                    }
                                }}
                            />
                            <div className="flex justify-between items-center px-2 pb-1">
                                <button 
                                    type="button" 
                                    onClick={toggleRecording}
                                    className={`p-2 rounded-lg transition-colors ${isRecording ? 'text-red-500 bg-red-500/10' : 'text-ghost/40 hover:text-ghost hover:bg-graphite'}`}
                                >
                                    <Mic className="w-5 h-5" />
                                </button>
                                <button 
                                    type="submit"
                                    disabled={!input.trim()}
                                    className="p-2 rounded-lg bg-plasma text-ghost disabled:opacity-50 disabled:cursor-not-allowed hover:bg-plasma/80 transition-colors"
                                >
                                    <Send className="w-5 h-5" />
                                </button>
                            </div>
                        </form>
                        <div className="text-center mt-3 text-xs font-mono text-ghost/30">
                            AI Gateway routes to the optimal model based on your task.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Chat;
