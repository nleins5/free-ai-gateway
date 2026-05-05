import { useState, useRef, useEffect } from 'react';
import { Send, Mic, Sparkles, Code2, Image as ImageIcon, Search, Settings, ArrowLeft, Zap, X } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

const API_BASE = import.meta.env.VITE_API_BASE || '';

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
                {msg.isImage ? (
                    <img src={msg.content} alt="Generated" className="rounded-xl shadow-2xl max-w-full h-auto mt-2" />
                ) : (
                    <div className="font-sans text-ghost/90 leading-relaxed whitespace-pre-wrap">
                        {msg.content}
                    </div>
                )}
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
    const [mediaRecorder, setMediaRecorder] = useState(null);
    const audioChunksRef = useRef([]);
    const audioContextRef = useRef(null);
    const animationFrameRef = useRef(null);
    const wsRef = useRef(null);
    const recordingIntervalRef = useRef(null);
    const [liveTranscript, setLiveTranscript] = useState('');
    const [audioLevel, setAudioLevel] = useState(0);
    
    const [userId, setUserId] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [toast, setToast] = useState(null);
    const [currentTier, setCurrentTier] = useState('vip');
    const [promptCount, setPromptCount] = useState(0);
    
    const messagesEndRef = useRef(null);
    const navigate = useNavigate();

    useEffect(() => {
        let id = localStorage.getItem('user_id');
        if (!id) {
            id = crypto.randomUUID();
            localStorage.setItem('user_id', id);
        }
        setUserId(id);
        
        const count = parseInt(localStorage.getItem('prompt_count') || '0', 10);
        setPromptCount(count);
        if (count >= 10) {
            setCurrentTier('general');
        }
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        if (toast) {
            const timer = setTimeout(() => setToast(null), 5000);
            return () => clearTimeout(timer);
        }
    }, [toast]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || !userId) return;
        
        // Limits disabled
        // if (promptCount >= 100) {
        //     setShowModal(true);
        //     return;
        // }

        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        
        try {
            let res;
            if (mode === 'image') {
                res = await fetch(`${API_BASE}/v1/images/generations`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: input })
                });
            } else {
                res = await fetch(`${API_BASE}/v1/chat/unified`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query: input,
                        user_id: userId,
                        task: mode,
                        use_rag: mode === 'research'
                    })
                });
            }
            
            if (res.status === 402) {
                setShowModal(true);
                setMessages(prev => prev.slice(0, -1)); // Remove user message if not sent
                return;
            }

            if (res.ok) {
                const data = await res.json();
                
                const newCount = promptCount + 1;
                setPromptCount(newCount);
                localStorage.setItem('prompt_count', newCount.toString());

                if (newCount === 10 && currentTier === 'vip') {
                    setToast('VIP Credits exhausted. Transitioning to Free AI tier for the next 90 prompts.');
                    setCurrentTier('general');
                }
                
                if (mode === 'image') {
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: data.data[0].url,
                        isImage: true,
                        provider: data.provider || 'AI Image Generator',
                        latency: 1500
                    }]);
                } else {
                    const isVip = newCount <= 10;
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: data.answer,
                        provider: isVip ? (data.metadata?.provider || 'GPT-4o (VIP)') : 'Llama 3 (General)',
                        latency: data.metadata?.latency_ms ? Math.round(data.metadata.latency_ms) : (isVip ? 450 : 85)
                    }]);
                }
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

    const startRecording = async () => {
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                setToast('Trình duyệt của bạn không hỗ trợ ghi âm hoặc cần HTTPS.');
                return;
            }
            
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true // Simplified constraints for maximum compatibility on Safari
            });
            
            // Detect supported mime type for Safari/Mac compatibility
            let options = undefined;
            if (MediaRecorder.isTypeSupported('audio/webm')) {
                options = { mimeType: 'audio/webm' };
            } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
                options = { mimeType: 'audio/mp4' };
            }
                
            let recorder;
            try {
                recorder = new MediaRecorder(stream, options);
            } catch (e) {
                console.warn('Failed to initialize MediaRecorder with options, falling back to default', e);
                recorder = new MediaRecorder(stream);
            }
            
            // Set up AudioContext for Voice Activity Detection (VAD) / Silence detection
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            audioContextRef.current = audioContext;
            const source = audioContext.createMediaStreamSource(stream);
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 512;
            source.connect(analyser);
            
            const dataArray = new Uint8Array(analyser.frequencyBinCount);
            let silenceStart = Date.now();
            const SILENCE_THRESHOLD = 15; // Noise threshold (0-255)
            const SILENCE_DURATION = 2500; // 2.5 seconds of silence auto-stop

            const checkSilence = () => {
                if (recorder.state === 'inactive') return;

                analyser.getByteFrequencyData(dataArray);
                const sum = dataArray.reduce((a, b) => a + b, 0);
                const average = sum / dataArray.length;
                
                // Update visualizer state
                setAudioLevel(Math.min(100, Math.round((average / 255) * 100 * 2.5)));

                if (average > SILENCE_THRESHOLD) {
                    silenceStart = Date.now(); // Reset timer when sound is detected
                } else {
                    if (Date.now() - silenceStart > SILENCE_DURATION) {
                        // Silence detected, stop recording automatically
                        if (recorder.state !== 'inactive') {
                            recorder.stop();
                        }
                        setIsRecording(false);
                        return;
                    }
                }
                animationFrameRef.current = requestAnimationFrame(checkSilence);
            };

            recorder.onstart = () => {
                silenceStart = Date.now();
                audioChunksRef.current = [];
                setLiveTranscript('');
                console.log('Recording started, mimeType:', recorder.mimeType);
                checkSilence();
            };
            
            recorder.ondataavailable = (e) => {
                console.log('Data available:', e.data.size, 'bytes');
                if (e.data.size > 0) {
                    audioChunksRef.current.push(e.data);
                }
            };

            recorder.onstop = async () => {
                console.log('Recorder stopped. Chunks:', audioChunksRef.current.length);
                if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
                if (recordingIntervalRef.current) clearInterval(recordingIntervalRef.current);
                if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
                    audioContextRef.current.close();
                }

                setIsRecording(false);
                setAudioLevel(0);

                // Stop all tracks to release microphone
                stream.getTracks().forEach(track => track.stop());

                // Create a single blob from all chunks
                const finalMimeType = recorder.mimeType || (options ? options.mimeType : 'audio/mp4');
                console.log('Creating blob with type:', finalMimeType, 'chunks:', audioChunksRef.current.length);
                const audioBlob = new Blob(audioChunksRef.current, { type: finalMimeType });
                console.log('Blob created:', audioBlob.size, 'bytes');
                audioChunksRef.current = [];
                
                if (audioBlob.size > 0) {
                    setLiveTranscript('Đang xử lý giọng nói...');
                    try {
                        const formData = new FormData();
                        const extension = finalMimeType.includes('webm') ? 'webm' : 'mp4';
                        formData.append('file', audioBlob, `audio.${extension}`);
                        
                        const res = await fetch(`${API_BASE}/v1/audio/transcriptions`, {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (res.ok) {
                            const data = await res.json();
                            const text = data.text?.trim() || '';
                            console.log('Transcription result:', text);
                            if (text && text !== "1" && text !== "1." && text !== "Đây là câu nói tiếng Việt.") {
                                const newInput = (input ? input + ' ' : '') + text;
                                setInput(newInput);
                                setLiveTranscript('');
                                // Auto-submit after state updates
                                setTimeout(() => {
                                    handleSubmit({ preventDefault: () => {} });
                                }, 300);
                            } else {
                                setLiveTranscript('Không nghe rõ, vui lòng thử lại.');
                                setTimeout(() => setLiveTranscript(''), 2000);
                            }
                        } else {
                            const err = await res.json();
                            setToast(`Lỗi xử lý giọng nói: ${err.detail || err.error || res.statusText}`);
                            setLiveTranscript('');
                        }
                    } catch (error) {
                        console.error('Audio upload error:', error);
                        setToast(`Lỗi upload: ${error.message}`);
                        setLiveTranscript('');
                    }
                }
            };

            recorder.start(100); // Collect data every 100ms for debugging
            setMediaRecorder(recorder);
            setIsRecording(true);
        } catch (err) {
            console.error('Mic error:', err);
            let errMsg = 'Không thể truy cập Microphone. Vui lòng cấp quyền.';
            if (err.name === 'NotAllowedError' || err.message.includes('Permission denied')) {
                errMsg = 'Quyền bị từ chối. Vui lòng kiểm tra cài đặt Microphone trong System Settings > Privacy & Security > Microphone của Mac và cho phép trình duyệt của bạn.';
            } else {
                errMsg = `Lỗi: ${err.message}`;
            }
            setToast(errMsg);
            setIsRecording(false);
        }
    };

    const stopRecording = () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
        setIsRecording(false);
    };

    const toggleRecording = () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    };

    const modes = [
        { id: 'chat', icon: Sparkles, label: 'Chat' },
        { id: 'research', icon: Search, label: 'Research' },
        { id: 'code', icon: Code2, label: 'Code' },
        { id: 'image', icon: ImageIcon, label: 'Image' },
    ];

    return (
        <div className="flex h-screen bg-[#05050A] font-sans">
            {/* Sidebar */}
            <div className="w-64 border-r border-graphite bg-void hidden md:flex flex-col">
                <div className="p-6 border-b border-graphite flex items-center gap-3">
                    <Link to="/" className="text-ghost/60 hover:text-ghost transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div className="font-bold text-ghost tracking-tight">Gateway<span className="text-plasma">.</span></div>
                </div>
                <div className="p-4 flex-1 overflow-y-auto">
                    <div className="text-xs font-mono text-ghost/40 mb-4 px-2">HISTORY</div>
                    <div className="flex flex-col gap-1">
                        <button className="text-left px-3 py-2 rounded-lg bg-graphite/40 text-ghost/80 text-sm truncate hover:bg-graphite transition-colors">
                            Thiết lập AI Gateway
                        </button>
                        <button className="text-left px-3 py-2 rounded-lg text-ghost/60 text-sm truncate hover:bg-graphite/40 transition-colors">
                            Phân tích chi phí Cloud
                        </button>
                    </div>
                </div>
                <div className="p-4 border-t border-graphite">
                    <button className="flex items-center gap-2 text-ghost/60 hover:text-ghost transition-colors w-full px-2 py-2">
                        <Settings className="w-4 h-4" />
                        <span className="text-sm">Settings</span>
                    </button>
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col relative overflow-hidden bg-[url('https://images.unsplash.com/photo-1518423238622-0e363674dcfc?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center">
                <div className="absolute inset-0 bg-void/95 backdrop-blur-3xl z-0"></div>
                
                {/* Header */}
                <div className="relative z-10 h-16 border-b border-graphite flex items-center justify-between px-4 md:px-6 bg-void/50 backdrop-blur-md">
                    <div className="flex items-center gap-1 md:gap-2 bg-graphite/40 p-1 rounded-lg overflow-x-auto no-scrollbar">
                        {modes.map(m => (
                            <button 
                                key={m.id}
                                onClick={() => setMode(m.id)}
                                className={`flex items-center gap-2 px-3 py-[6px] rounded-md text-sm transition-all ${mode === m.id ? 'bg-plasma/20 text-plasma shadow-sm' : 'text-ghost/60 hover:text-ghost hover:bg-graphite/60'}`}
                            >
                                <m.icon className="w-4 h-4" />
                                <span className="font-medium">{m.label}</span>
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
                        <form onSubmit={handleSubmit} className="relative bg-graphite/60 backdrop-blur-xl border border-ghost/10 rounded-premium p-2 focus-within:border-plasma/50 transition-all duration-500 shadow-2xl group">
                            {liveTranscript && (
                                <div className="w-full bg-transparent text-plasma/80 pt-3 pb-1 px-4 italic text-sm">
                                    {liveTranscript}
                                    <span className="inline-block w-1.5 h-3 ml-1 bg-plasma/70 animate-pulse"></span>
                                </div>
                            )}
                            <textarea 
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder={isRecording ? "Đang lắng nghe..." : "Message Gateway..."}
                                className="w-full bg-transparent text-ghost placeholder-ghost/30 resize-none outline-none py-3 px-4 max-h-32 min-h-[60px]"
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        handleSubmit(e);
                                    }
                                }}
                                />
                            
                            {/* Audio Visualizer overlay */}
                            {isRecording && (
                                <div className="absolute inset-x-0 bottom-16 h-12 flex items-center justify-center gap-1 opacity-80 pointer-events-none">
                                    {[...Array(20)].map((_, i) => {
                                        // create a symmetric wave effect
                                        const symmetricIndex = Math.abs(i - 9.5); 
                                        const dropoff = Math.max(0.1, 1 - (symmetricIndex * 0.1));
                                        const height = Math.max(4, audioLevel * dropoff);
                                        return (
                                            <div 
                                                key={i} 
                                                className="w-1.5 bg-plasma rounded-full transition-all duration-75"
                                                style={{ height: `${height}px` }}
                                            />
                                        )
                                    })}
                                </div>
                            )}

                            <div className="flex justify-between items-center px-2 pb-1">
                                <button 
                                    type="button" 
                                    onClick={toggleRecording}
                                    className={`p-3 rounded-xl transition-all duration-300 magnetic-btn ${isRecording ? 'text-red-500 bg-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.3)] scale-110' : 'text-ghost/40 hover:text-ghost hover:bg-graphite'}`}
                                >
                                    <Mic className={`w-5 h-5 ${isRecording ? 'animate-pulse' : ''}`} />
                                </button>
                                <button 
                                    type="submit"
                                    disabled={!input.trim()}
                                    className="p-3 rounded-xl bg-plasma text-void disabled:opacity-30 disabled:cursor-not-allowed hover:bg-plasma/90 transition-all duration-300 magnetic-btn shadow-lg"
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

                {/* VIP Downgrade Toast */}
                {toast && (
                    <div className="absolute top-20 right-6 z-50 bg-yellow-500/10 border border-yellow-500/50 backdrop-blur-md text-yellow-200 px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-3 animate-fade-in">
                        <Zap className="w-5 h-5 text-yellow-500" />
                        <span className="font-mono text-sm">{toast}</span>
                        <button onClick={() => setToast(null)} className="ml-4 opacity-50 hover:opacity-100">
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                )}

                {/* Out of Credits Modal */}
                {showModal && (
                    <div className="absolute inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-xl animate-fade-in">
                        <div className="bg-void border border-plasma/30 p-10 rounded-[2.5rem] max-w-md w-full shadow-[0_0_80px_rgba(123,97,255,0.15)] relative overflow-hidden group/modal">
                            {/* Cinematic Glows */}
                            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-plasma via-plasma/50 to-transparent"></div>
                            <div className="absolute -top-20 -right-20 w-40 h-40 bg-plasma/20 blur-[60px] rounded-full pointer-events-none group-hover/modal:bg-plasma/30 transition-colors duration-700"></div>
                            
                            <div className="relative z-10">
                                <div className="w-16 h-16 rounded-2xl bg-plasma/10 flex items-center justify-center mb-8 border border-plasma/30 shadow-[0_0_30px_rgba(123,97,255,0.2)]">
                                    <Zap className="w-8 h-8 text-plasma animate-pulse" />
                                </div>
                                
                                <h2 className="text-3xl font-black text-ghost mb-3 tracking-tight font-sans">Access Restricted</h2>
                                <p className="text-ghost/50 mb-8 leading-relaxed text-sm font-sans">
                                    You have exhausted the general tier neural allocation. To restore uplink and access premium reasoning models (o1, Opus), please authenticate your identity.
                                </p>
                                
                                <div className="flex flex-col gap-3">
                                    <button 
                                        onClick={() => navigate('/login')}
                                        className="magnetic-btn group w-full relative overflow-hidden bg-plasma text-void font-bold rounded-2xl px-6 py-4 flex items-center justify-center gap-2 hover:scale-[1.03] transition-all duration-500 ease-[cubic-bezier(0.25,0.46,0.45,0.94)] shadow-[0_0_30px_rgba(123,97,255,0.2)]"
                                    >
                                        <span className="absolute inset-0 bg-white/20 -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out z-0"></span>
                                        <span className="relative z-10 flex items-center gap-2 tracking-widest uppercase text-sm">
                                            <Zap className="w-4 h-4" />
                                            Authenticate
                                        </span>
                                    </button>
                                    <button 
                                        onClick={() => setShowModal(false)}
                                        className="w-full py-4 px-6 rounded-2xl border border-ghost/10 text-ghost/40 hover:text-ghost hover:bg-ghost/5 hover:border-ghost/20 transition-all duration-300 font-bold uppercase tracking-widest text-xs"
                                    >
                                        Dismiss
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Chat;
