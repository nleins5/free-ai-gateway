import { useState, useRef, useEffect } from 'react';
import { Send, Mic, Sparkles, Code2, Image as ImageIcon, Search, Settings, ArrowLeft, Zap, X, Box, Plus, Activity, Brain, Database, Palette, CreditCard, HelpCircle, Pencil, Check } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

const API_BASE = import.meta.env.VITE_API_BASE || '';

const TIER_CONFIG = {
    vip: { label: 'VIP', color: 'text-amber-400', bg: 'bg-amber-400/10 border-amber-400/20' },
    standard: { label: 'Standard', color: 'text-sky-400', bg: 'bg-sky-400/10 border-sky-400/20' },
    free: { label: 'Free', color: 'text-ghost/40', bg: 'bg-ghost/5 border-ghost/10' },
};

const ChatMessage = ({ msg }) => {
    const isAi = msg.role === 'assistant';
    
    let htmlContent = null;
    let cleanContent = msg.content;
    
    if (isAi && msg.content && typeof msg.content === 'string') {
        const htmlMatch = msg.content.match(/```html\n([\s\S]*?)```/);
        if (htmlMatch) {
            htmlContent = htmlMatch[1];
            cleanContent = msg.content.replace(/```html\n[\s\S]*?```/, '').trim();
        }
    }
    
    return (
        <div className={`flex gap-4 p-6 ${isAi ? 'bg-void' : ''}`}>
            <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${isAi ? 'bg-plasma/20 text-plasma' : 'bg-graphite text-ghost/60'}`}>
                {isAi ? <Sparkles className="w-5 h-5" /> : <div className="w-3 h-3 bg-ghost/40 rounded-full" />}
            </div>
            <div className="flex-1 space-y-4 overflow-hidden">
                <div className="font-sans font-semibold text-ghost/80">
                    {isAi ? 'AI Gateway' : 'You'}
                </div>
                {msg.isImage ? (
                    <img src={msg.content} alt="Generated" className="rounded-xl shadow-2xl max-w-full h-auto mt-2" />
                ) : (
                    <div className="font-sans text-ghost/90 leading-relaxed whitespace-pre-wrap">
                        {cleanContent}
                        {htmlContent && (
                            <div className="mt-4 rounded-xl overflow-hidden border border-graphite shadow-2xl bg-white w-full" style={{ height: '450px' }}>
                                <iframe
                                    srcDoc={htmlContent}
                                    style={{ width: '100%', height: '100%', border: 'none' }}
                                    sandbox="allow-scripts allow-same-origin"
                                    title="3D Render"
                                />
                            </div>
                        )}
                    </div>
                )}
                {msg.latency && (
                    <div className="flex items-center gap-3 mt-2 flex-wrap">
                        {msg.tierLabel && (
                            <span className={`font-mono text-xs px-2 py-0.5 rounded-full border ${TIER_CONFIG[msg.tierKey]?.bg || ''} ${TIER_CONFIG[msg.tierKey]?.color || 'text-ghost/50'}`}>
                                {msg.tierLabel}
                            </span>
                        )}
                        <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-plasma"></div>
                            <span className="font-mono text-xs text-plasma/70">{msg.provider} • {msg.latency}ms</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

const Chat = () => {
    const defaultMessage = { role: 'assistant', content: 'Xin chào. Hệ thống định tuyến đã sẵn sàng. Bạn muốn thực hiện tác vụ nào hôm nay?', provider: 'Groq (Llama 3)', latency: 120 };
    
    const [sessions, setSessions] = useState(() => {
        try {
            const saved = localStorage.getItem('chat_sessions');
            if (saved) return JSON.parse(saved);
        } catch (e) { console.error("Failed to parse sessions", e); }
        return [{ id: Date.now(), title: 'New Chat', messages: [defaultMessage] }];
    });
    
    const [activeSessionId, setActiveSessionId] = useState(() => {
        try {
            const saved = localStorage.getItem('chat_sessions');
            if (saved) return JSON.parse(saved)[0]?.id;
        } catch (e) {}
        return sessions[0]?.id;
    });
    
    const [messages, setMessages] = useState(() => {
        const active = sessions.find(s => s.id === activeSessionId);
        return active ? active.messages : [defaultMessage];
    });

    useEffect(() => {
        setSessions(prev => {
            const updated = prev.map(s => {
                if (s.id === activeSessionId) {
                    let title = s.title;
                    if (title === 'New Chat' && messages.length > 1) {
                        const firstUserMsg = messages.find(m => m.role === 'user');
                        if (firstUserMsg) {
                            title = firstUserMsg.content.slice(0, 30) + (firstUserMsg.content.length > 30 ? '...' : '');
                        }
                    }
                    return { ...s, title, messages };
                }
                return s;
            });
            localStorage.setItem('chat_sessions', JSON.stringify(updated));
            return updated;
        });
    }, [messages, activeSessionId]);

    const handleNewChat = () => {
        const newSession = {
            id: Date.now(),
            title: 'New Chat',
            messages: [defaultMessage]
        };
        setSessions(prev => [newSession, ...prev]);
        setActiveSessionId(newSession.id);
        setMessages(newSession.messages);
    };

    const switchSession = (id) => {
        if (editingSessionId === id) return;
        const session = sessions.find(s => s.id === id);
        if (session) {
            setActiveSessionId(id);
            setMessages(session.messages);
        }
    };

    const startRename = (id, currentTitle, e) => {
        e.stopPropagation();
        setEditingSessionId(id);
        setEditTitle(currentTitle);
    };

    const saveRename = (id, e) => {
        if (e) e.stopPropagation();
        setSessions(prev => {
            const updated = prev.map(s => {
                if (s.id === id) {
                    return { ...s, title: editTitle.trim() || 'Untitled' };
                }
                return s;
            });
            localStorage.setItem('chat_sessions', JSON.stringify(updated));
            return updated;
        });
        setEditingSessionId(null);
    };

    const handleRenameKeyDown = (e, id) => {
        if (e.key === 'Enter') {
            saveRename(id, e);
        } else if (e.key === 'Escape') {
            setEditingSessionId(null);
        }
    };
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const [editingSessionId, setEditingSessionId] = useState(null);
    const [editTitle, setEditTitle] = useState('');
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
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [userPlan, setUserPlan] = useState('free'); // 'free' | 'vip'
    const [showModal, setShowModal] = useState(false);
    const [showLoginGate, setShowLoginGate] = useState(false);
    const [toast, setToast] = useState(null);
    const [promptCount, setPromptCount] = useState(0);

    // Derive userTier from login status + plan
    const getUserTier = (loggedIn, plan, count) => {
        if (loggedIn && plan === 'vip') return 'vip';
        if (loggedIn) return 'free';
        // Guest: tier depends on prompt count
        if (count === 0) return 'vip';
        if (count === 1) return 'standard';
        return 'free';
    };

    const [showSettingsModal, setShowSettingsModal] = useState(false);
    const [activeSettingsTab, setActiveSettingsTab] = useState('activity');
    
    // New Settings States
    const [themeSetting, setThemeSetting] = useState('dark');
    const [intelligenceSettings, setIntelligenceSettings] = useState({ professional: true, autoModel: true });


    const handleSettingsClick = (tabId) => {
        setActiveSettingsTab(tabId);
        setShowSettingsModal(true);
        setShowSettings(false);
    };
    
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

        // Detect login state
        const token = localStorage.getItem('auth_token');
        const plan = localStorage.getItem('user_plan') || 'free';
        if (token) {
            setIsLoggedIn(true);
            setUserPlan(plan);
        }

        // Warmup ping — wakes up Render before user sends first message
        fetch(`${API_BASE}/health`, { method: 'GET' }).catch(() => {});
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

    // Helper: fetch with timeout + retry for Render cold start
    const fetchWithRetry = async (url, options, maxRetries = 2, timeoutMs = 30000) => {
        let lastError;
        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            const controller = new AbortController();
            const timer = setTimeout(() => controller.abort(), timeoutMs);
            try {
                const res = await fetch(url, { ...options, signal: controller.signal });
                clearTimeout(timer);
                return res;
            } catch (err) {
                clearTimeout(timer);
                lastError = err;
                // Only retry on network/abort errors, not on HTTP errors
                if (err.name === 'AbortError') {
                    lastError = new Error('Request timed out — backend có thể đang khởi động. Thử lại...');
                }
                if (attempt < maxRetries) {
                    // Show retry notice
                    setToast(`Đang kết nối lại (lần ${attempt + 1}/${maxRetries})...`);
                    await new Promise(r => setTimeout(r, 2000 * (attempt + 1)));
                }
            }
        }
        throw lastError;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || !userId) return;

        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        const currentInput = input;
        setInput('');
        setIsLoading(true);

        const gatewayKey = import.meta.env.VITE_GATEWAY_SECRET || '';
        const standardHeaders = { 'Content-Type': 'application/json' };
        if (gatewayKey) standardHeaders['X-Gateway-Key'] = gatewayKey;

        try {
            // ── Image mode: regular fetch (no streaming) ──────────────
            if (mode === 'image') {
                const res = await fetchWithRetry(`${API_BASE}/v1/images/generations`, {
                    method: 'POST',
                    headers: standardHeaders,
                    body: JSON.stringify({ prompt: currentInput })
                }, 1, 60000);

                if (res.status === 402) { setMessages(prev => prev.slice(0, -1)); setShowModal(true); return; }
                if (!res.ok) {
                    let msg = `Server Error ${res.status}`;
                    try { const e = await res.json(); msg = e.detail || e.error || msg; } catch {}
                    setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ ${msg}`, provider: 'System', latency: 0 }]);
                    return;
                }
                const data = await res.json();
                const imgData = data.data[0];
                const imgSrc = imgData.url || (imgData.b64_json ? `data:image/png;base64,${imgData.b64_json}` : '');
                setMessages(prev => [...prev, { role: 'assistant', content: imgSrc, isImage: true, provider: data.provider || 'AI Image Generator', latency: 1500 }]);
                return;
            }

            // ── Chat/Code/Omniverse/Research: SSE Streaming ───────────
            const history = messages
                .filter(m => !m.isImage && m.content)
                .map(m => ({ role: m.role, content: m.content }));

            const currentTierKey = getUserTier(isLoggedIn, userPlan, promptCount);
            const body = JSON.stringify({
                query: currentInput,
                user_id: userId,
                task: mode,
                use_rag: mode === 'research',
                user_tier: isLoggedIn ? (userPlan === 'vip' ? 'vip' : 'free') : 'guest',
                guest_prompt_count: promptCount,  // client tracks this — survives backend cold starts
                history
            });

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000);

            const res = await fetch(`${API_BASE}/v1/chat/unified/stream`, {
                method: 'POST',
                headers: standardHeaders,
                body,
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            if (res.status === 402) { setMessages(prev => prev.slice(0, -1)); setShowModal(true); return; }
            if (res.status === 403) {
                setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Lỗi xác thực (403). Liên hệ admin.', provider: 'System', latency: 0 }]);
                return;
            }
            if (!res.ok) {
                let msg = `Server Error ${res.status}`;
                try { const e = await res.json(); msg = e.detail || e.error || msg; } catch {}
                setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ ${msg}`, provider: 'System', latency: 0 }]);
                return;
            }

            // Create streaming message placeholder
            const streamingId = Date.now();
            setMessages(prev => [...prev, { role: 'assistant', content: '', provider: '', latency: null, _streamingId: streamingId }]);

            // Read SSE stream
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let fullContent = '';
            let finalProvider = '';
            const startTime = Date.now();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    const raw = line.slice(6).trim();
                    if (!raw) continue;

                    let parsed;
                    try { parsed = JSON.parse(raw); } catch { continue; }

                    if (parsed.error) {
                        if (parsed.error === 'NeedLogin') {
                            // Remove streaming placeholder, show login gate
                            setMessages(prev => prev.filter(m => !m._streamingId));
                            setShowLoginGate(true);
                            break;
                        }
                        const errMsg = parsed.error === 'FreeLimitReached'
                            ? null
                            : `${parsed.message || parsed.error}`;
                        if (errMsg) {
                            setMessages(prev => prev.map(m =>
                                m._streamingId === streamingId
                                    ? { ...m, content: errMsg, provider: 'System' }
                                    : m
                            ));
                        }
                        break;
                    }

                    if (parsed.info) {
                        setToast(parsed.message);
                        continue;
                    }

                    if (parsed.token) {
                        fullContent += parsed.token;
                        if (parsed.provider) finalProvider = parsed.provider;
                        setMessages(prev => prev.map(m =>
                            m._streamingId === streamingId
                                ? { ...m, content: fullContent, provider: parsed.provider || m.provider }
                                : m
                        ));
                    }

                    if (parsed.done) {
                        finalProvider = parsed.provider || finalProvider;
                        const latencyMs = Date.now() - startTime;
                        const tierKey = getUserTier(isLoggedIn, userPlan, promptCount);
                        setMessages(prev => prev.map(m =>
                            m._streamingId === streamingId
                                ? {
                                    ...m,
                                    content: fullContent,
                                    provider: finalProvider,
                                    latency: latencyMs,
                                    tierKey,
                                    tierLabel: TIER_CONFIG[tierKey]?.label,
                                    _streamingId: undefined
                                }
                                : m
                        ));

                        const newCount = promptCount + 1;
                        setPromptCount(newCount);
                        localStorage.setItem('prompt_count', newCount.toString());
                        break;
                    }
                }
            }

        } catch (error) {
            const isColdStart = error.message?.includes('Load failed') || error.message?.includes('Failed to fetch') || error.name === 'AbortError';
            const msg = isColdStart
                ? '🔌 Không kết nối được server. Backend có thể đang ngủ — thử lại sau 30 giây.'
                : `⚠️ Lỗi kết nối: ${error.message}`;
            // Replace streaming placeholder if exists, else add new msg
            setMessages(prev => {
                const hasStreaming = prev.some(m => m._streamingId);
                if (hasStreaming) return prev.map(m => m._streamingId ? { ...m, content: msg, provider: 'System', latency: 0, _streamingId: undefined } : m);
                return [...prev, { role: 'assistant', content: msg, provider: 'System', latency: 0 }];
            });
            setToast(error.message);
        } finally {
            setIsLoading(false);
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
                        
                        const gatewayKey = import.meta.env.VITE_GATEWAY_SECRET || '';
                        const audioHeaders = {};
                        if (gatewayKey) {
                            audioHeaders['X-Gateway-Key'] = gatewayKey;
                        }

                        const res = await fetch(`${API_BASE}/v1/audio/transcriptions`, {
                            method: 'POST',
                            headers: audioHeaders,
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
        { id: 'omniverse', icon: Box, label: 'Omniverse 3D' },
    ];

    const isLightMode = themeSetting === 'light' || (themeSetting === 'system' && window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches);

    return (
        <div className={`flex h-screen bg-void font-sans ${isLightMode ? 'light-mode' : ''}`}>
            {/* Sidebar */}
            <div className="w-64 border-r border-graphite bg-sidebar hidden md:flex flex-col">
                <div className="p-6 border-b border-graphite flex items-center gap-3">
                    <Link to="/" className="text-ghost/60 hover:text-ghost transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div className="font-bold text-ghost tracking-tight">Gateway<span className="text-plasma">.</span></div>
                </div>
                <div className="p-4 flex-1 overflow-y-auto">
                    <div className="flex items-center justify-between mb-4 px-2">
                        <div className="text-xs font-mono text-ghost/40">HISTORY</div>
                        <button onClick={handleNewChat} className="text-ghost/60 hover:text-ghost transition-colors p-1 rounded-md hover:bg-graphite/40">
                            <Plus className="w-4 h-4" />
                        </button>
                    </div>
                    <div className="flex flex-col gap-1">
                        {sessions.map(s => (
                            <div 
                                key={s.id}
                                onClick={() => switchSession(s.id)}
                                className={`group flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors cursor-pointer ${activeSessionId === s.id ? 'bg-graphite/40 text-ghost/80' : 'text-ghost/60 hover:bg-graphite/40'}`}
                            >
                                {editingSessionId === s.id ? (
                                    <div className="flex items-center gap-2 w-full" onClick={e => e.stopPropagation()}>
                                        <input
                                            type="text"
                                            value={editTitle}
                                            onChange={e => setEditTitle(e.target.value)}
                                            onKeyDown={e => handleRenameKeyDown(e, s.id)}
                                            onBlur={(e) => saveRename(s.id, e)}
                                            autoFocus
                                            className="bg-void border border-graphite rounded px-2 py-0.5 text-ghost w-full text-sm outline-none focus:border-plasma/50"
                                        />
                                    </div>
                                ) : (
                                    <>
                                        <span className="truncate flex-1">{s.title}</span>
                                        <button 
                                            onClick={(e) => startRename(s.id, s.title, e)}
                                            className={`p-1.5 rounded-md opacity-0 group-hover:opacity-100 transition-opacity hover:bg-graphite hover:text-ghost ${activeSessionId === s.id ? 'opacity-100 text-ghost/60' : ''}`}
                                            title="Rename chat"
                                        >
                                            <Pencil className="w-3 h-3" />
                                        </button>
                                    </>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
                <div className="p-4 border-t border-graphite relative">
                    {showSettings && (
                        <div className="absolute bottom-full left-4 w-[240px] mb-2 bg-[#1A1A24] border border-graphite rounded-2xl shadow-2xl py-2 z-50 overflow-hidden flex flex-col font-sans">
                            <button onClick={() => handleSettingsClick('activity')} className="flex items-center gap-3 px-4 py-2.5 text-sm text-ghost/80 hover:bg-graphite/50 transition-colors w-full text-left">
                                <Activity className="w-4 h-4" /> Hoạt động
                            </button>
                            <button onClick={() => handleSettingsClick('intelligence')} className="flex items-center gap-3 px-4 py-2.5 text-sm text-ghost/80 hover:bg-graphite/50 transition-colors w-full text-left">
                                <Brain className="w-4 h-4" /> Trí thông minh cá nhân
                            </button>
                            <button onClick={() => handleSettingsClick('memory')} className="flex items-center justify-between px-4 py-2.5 text-sm text-ghost/80 hover:bg-graphite/50 transition-colors w-full text-left">
                                <div className="flex items-center gap-3">
                                    <Database className="w-4 h-4" /> Nhập bộ nhớ
                                </div>
                                <span className="text-[10px] bg-plasma/20 text-plasma px-2 py-0.5 rounded-full font-medium">Mới</span>
                            </button>
                            
                            <div className="h-px bg-graphite/50 my-1.5"></div>
                            
                            <button onClick={() => handleSettingsClick('theme')} className="flex items-center justify-between px-4 py-2.5 text-sm text-ghost/80 hover:bg-graphite/50 transition-colors w-full text-left">
                                <div className="flex items-center gap-3">
                                    <Palette className="w-4 h-4" /> Giao diện
                                </div>
                                <span className="text-xs text-ghost/40">▶</span>
                            </button>
                            <button onClick={() => handleSettingsClick('billing')} className="flex items-center gap-3 px-4 py-2.5 text-sm text-ghost/80 hover:bg-graphite/50 transition-colors w-full text-left">
                                <CreditCard className="w-4 h-4" /> Quản lý gói thuê bao
                            </button>
                            
                            <div className="h-px bg-graphite/50 my-1.5"></div>
                            
                            <button onClick={() => handleSettingsClick('help')} className="flex items-center justify-between px-4 py-2.5 text-sm text-ghost/80 hover:bg-graphite/50 transition-colors w-full text-left">
                                <div className="flex items-center gap-3">
                                    <HelpCircle className="w-4 h-4" /> Trợ giúp
                                </div>
                                <span className="text-xs text-ghost/40">▶</span>
                            </button>
                        </div>
                    )}
                    <button 
                        onClick={() => setShowSettings(!showSettings)}
                        className={`flex items-center gap-3 transition-colors w-full px-3 py-2.5 rounded-xl ${showSettings ? 'bg-graphite/40 text-ghost' : 'text-ghost/60 hover:text-ghost hover:bg-graphite/20'}`}
                    >
                        <Settings className="w-4 h-4" />
                        <span className="text-sm font-medium">Cài đặt</span>
                    </button>
                </div>
            </div>

            {/* Main Chat Area */}
            <div className={`flex-1 flex flex-col relative overflow-hidden ${!isLightMode ? "bg-[url('https://images.unsplash.com/photo-1518423238622-0e363674dcfc?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center" : "bg-void"}`}>
                {!isLightMode && <div className="absolute inset-0 bg-void/95 backdrop-blur-3xl z-0"></div>}
                
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
                        {isLoading && (
                            <div className="flex gap-4 p-6 bg-void">
                                <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 bg-plasma/20 text-plasma">
                                    <Sparkles className="w-5 h-5 animate-pulse" />
                                </div>
                                <div className="flex-1 space-y-4">
                                    <div className="font-sans font-semibold text-ghost/80">AI Gateway</div>
                                    <div className="flex items-center gap-2 h-6">
                                        <div className="w-2 h-2 bg-plasma/60 rounded-full animate-bounce"></div>
                                        <div className="w-2 h-2 bg-plasma/60 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                        <div className="w-2 h-2 bg-plasma/60 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {/* Input Area */}
                <div className="relative z-10 p-6 bg-gradient-to-t from-void to-transparent">
                    <div className="max-w-3xl mx-auto">
                        <form onSubmit={handleSubmit} className={`relative backdrop-blur-xl border border-ghost/10 rounded-premium p-2 focus-within:border-plasma/50 transition-all duration-500 shadow-2xl group ${isLightMode ? 'bg-input' : 'bg-graphite/60'}`}>
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
                                    disabled={!input.trim() || isLoading}
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

                {/* Settings Modal */}
                {showSettingsModal && (
                    <div className="absolute inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-xl animate-fade-in font-sans">
                        <div className="bg-void border border-graphite rounded-3xl w-full max-w-4xl h-[600px] flex overflow-hidden shadow-2xl relative">
                            {/* Close Button */}
                            <button 
                                onClick={() => setShowSettingsModal(false)}
                                className="absolute top-4 right-4 p-2 rounded-full text-ghost/50 hover:text-ghost hover:bg-graphite/50 transition-colors z-20"
                            >
                                <X className="w-5 h-5" />
                            </button>

                            {/* Sidebar Tabs */}
                            <div className="w-64 bg-graphite/20 border-r border-graphite p-4 flex flex-col gap-1 overflow-y-auto">
                                <h3 className="text-xs font-bold tracking-widest text-ghost/40 uppercase mb-4 px-3 pt-2">Cài đặt</h3>
                                
                                <button onClick={() => setActiveSettingsTab('activity')} className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium transition-all ${activeSettingsTab === 'activity' ? 'bg-plasma/10 text-plasma shadow-[inset_4px_0_0_0_rgba(123,97,255,1)]' : 'text-ghost/60 hover:text-ghost hover:bg-graphite/40'}`}>
                                    <Activity className="w-4 h-4" /> Hoạt động
                                </button>
                                <button onClick={() => setActiveSettingsTab('intelligence')} className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium transition-all ${activeSettingsTab === 'intelligence' ? 'bg-plasma/10 text-plasma shadow-[inset_4px_0_0_0_rgba(123,97,255,1)]' : 'text-ghost/60 hover:text-ghost hover:bg-graphite/40'}`}>
                                    <Brain className="w-4 h-4" /> Trí thông minh cá nhân
                                </button>
                                <button onClick={() => setActiveSettingsTab('memory')} className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium transition-all ${activeSettingsTab === 'memory' ? 'bg-plasma/10 text-plasma shadow-[inset_4px_0_0_0_rgba(123,97,255,1)]' : 'text-ghost/60 hover:text-ghost hover:bg-graphite/40'}`}>
                                    <Database className="w-4 h-4" /> Nhập bộ nhớ
                                </button>
                                <div className="h-px bg-graphite/50 my-2 mx-3"></div>
                                <button onClick={() => setActiveSettingsTab('theme')} className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium transition-all ${activeSettingsTab === 'theme' ? 'bg-plasma/10 text-plasma shadow-[inset_4px_0_0_0_rgba(123,97,255,1)]' : 'text-ghost/60 hover:text-ghost hover:bg-graphite/40'}`}>
                                    <Palette className="w-4 h-4" /> Giao diện
                                </button>
                                <button onClick={() => setActiveSettingsTab('billing')} className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium transition-all ${activeSettingsTab === 'billing' ? 'bg-plasma/10 text-plasma shadow-[inset_4px_0_0_0_rgba(123,97,255,1)]' : 'text-ghost/60 hover:text-ghost hover:bg-graphite/40'}`}>
                                    <CreditCard className="w-4 h-4" /> Quản lý gói thuê bao
                                </button>
                                <div className="h-px bg-graphite/50 my-2 mx-3"></div>
                                <button onClick={() => setActiveSettingsTab('help')} className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium transition-all ${activeSettingsTab === 'help' ? 'bg-plasma/10 text-plasma shadow-[inset_4px_0_0_0_rgba(123,97,255,1)]' : 'text-ghost/60 hover:text-ghost hover:bg-graphite/40'}`}>
                                    <HelpCircle className="w-4 h-4" /> Trợ giúp
                                </button>
                            </div>

                            {/* Tab Content Area */}
                            <div className="flex-1 p-8 overflow-y-auto relative bg-[url('https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center">
                                <div className="absolute inset-0 bg-void/90 backdrop-blur-3xl z-0"></div>
                                
                                <div className="relative z-10 max-w-2xl">
                                    {activeSettingsTab === 'activity' && (
                                        <div className="animate-fade-up">
                                            <h2 className="text-2xl font-bold text-ghost mb-6">Hoạt động gần đây</h2>
                                            <div className="space-y-4">
                                                {sessions.flatMap(s => s.messages).filter(m => m.role === 'user').reverse().slice(0, 3).map((msg, idx) => (
                                                    <div key={idx} className="p-4 rounded-2xl bg-graphite/30 border border-graphite/50">
                                                        <div className="text-sm text-ghost mb-1">{msg.content.length > 50 ? msg.content.substring(0, 50) + '...' : msg.content}</div>
                                                        <div className="text-xs text-ghost/40">Gần đây • Câu hỏi</div>
                                                    </div>
                                                ))}
                                                {sessions.flatMap(s => s.messages).filter(m => m.role === 'user').length === 0 && (
                                                    <div className="text-sm text-ghost/50 italic">Chưa có hoạt động nào.</div>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {activeSettingsTab === 'intelligence' && (
                                        <div className="animate-fade-up">
                                            <h2 className="text-2xl font-bold text-ghost mb-6">Trí thông minh cá nhân</h2>
                                            <p className="text-sm text-ghost/60 mb-8">Tinh chỉnh cách AI Gateway phản hồi với bạn dựa trên sở thích và hành vi trò chuyện.</p>
                                            
                                            <div className="space-y-6">
                                                <div className="flex items-center justify-between p-4 rounded-2xl bg-graphite/30 border border-graphite/50">
                                                    <div>
                                                        <div className="text-sm font-medium text-ghost mb-1">Phong cách phản hồi chuyên nghiệp</div>
                                                        <div className="text-xs text-ghost/50">Giảm bớt từ ngữ cảm thán, tập trung vào dữ liệu và giải pháp.</div>
                                                    </div>
                                                    <div 
                                                        onClick={() => {
                                                            setIntelligenceSettings(prev => ({...prev, professional: !prev.professional}));
                                                            setToast('Đã lưu thay đổi.');
                                                        }}
                                                        className={`w-10 h-6 rounded-full relative cursor-pointer border transition-colors ${intelligenceSettings.professional ? 'bg-plasma/30 border-plasma' : 'bg-graphite border-graphite/50'}`}>
                                                        <div className={`w-4 h-4 rounded-full absolute top-1 transition-all ${intelligenceSettings.professional ? 'bg-plasma right-1' : 'bg-ghost/50 left-1'}`}></div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center justify-between p-4 rounded-2xl bg-graphite/30 border border-graphite/50">
                                                    <div>
                                                        <div className="text-sm font-medium text-ghost mb-1">Tự động chọn Model tối ưu</div>
                                                        <div className="text-xs text-ghost/50">Hệ thống sẽ tự động switch giữa Claude, GPT và Gemini dựa vào độ phức tạp của câu hỏi.</div>
                                                    </div>
                                                    <div 
                                                        onClick={() => {
                                                            setIntelligenceSettings(prev => ({...prev, autoModel: !prev.autoModel}));
                                                            setToast('Đã lưu thay đổi.');
                                                        }}
                                                        className={`w-10 h-6 rounded-full relative cursor-pointer border transition-colors ${intelligenceSettings.autoModel ? 'bg-plasma/30 border-plasma' : 'bg-graphite border-graphite/50'}`}>
                                                        <div className={`w-4 h-4 rounded-full absolute top-1 transition-all ${intelligenceSettings.autoModel ? 'bg-plasma right-1' : 'bg-ghost/50 left-1'}`}></div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {activeSettingsTab === 'memory' && (
                                        <div className="animate-fade-up">
                                            <div className="flex items-center gap-3 mb-6">
                                                <h2 className="text-2xl font-bold text-ghost">Bộ nhớ ngữ cảnh</h2>
                                                <span className="text-xs bg-plasma/20 text-plasma px-2 py-1 rounded-full font-medium uppercase tracking-wider">Beta</span>
                                            </div>
                                            <div className="p-6 rounded-2xl bg-gradient-to-br from-plasma/10 to-transparent border border-plasma/30 mb-8">
                                                <Database className="w-8 h-8 text-plasma mb-4" />
                                                <div className="text-lg font-medium text-ghost mb-2">AI đang ghi nhớ {sessions.reduce((acc, s) => acc + s.messages.length, 0)} sự kiện</div>
                                                <p className="text-sm text-ghost/60">Bộ nhớ liên kết liên tục cập nhật sở thích, dự án đang làm, và văn phong của bạn để cung cấp trải nghiệm liền mạch giữa các phiên chat.</p>
                                                <button onClick={() => setToast('Tính năng quản lý dữ liệu chi tiết đang được phát triển.')} className="mt-4 text-xs font-medium bg-plasma text-void px-4 py-2 rounded-lg hover:bg-plasma/90 transition-colors shadow-lg shadow-plasma/20">
                                                    Quản lý dữ liệu bộ nhớ
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {activeSettingsTab === 'theme' && (
                                        <div className="animate-fade-up">
                                            <h2 className="text-2xl font-bold text-ghost mb-6">Giao diện (Theme)</h2>
                                            <div className="grid grid-cols-3 gap-4">
                                                <div onClick={() => setThemeSetting('dark')} className={`cursor-pointer border-2 rounded-xl overflow-hidden relative transition-colors ${themeSetting === 'dark' ? 'border-plasma' : 'border-transparent'}`}>
                                                    <div className="h-24 bg-[#0A0A0F] flex flex-col p-2 gap-2">
                                                        <div className="w-full h-4 bg-[#1A1A24] rounded"></div>
                                                        <div className="w-2/3 h-4 bg-plasma/20 rounded"></div>
                                                    </div>
                                                    <div className={`py-2 text-center text-xs font-medium border-t ${themeSetting === 'dark' ? 'bg-graphite/40 text-ghost border-graphite' : 'bg-graphite/20 text-ghost/50 border-transparent'}`}>Midnight Luxe {themeSetting === 'dark' && '(Active)'}</div>
                                                </div>
                                                <div onClick={() => setThemeSetting('light')} className={`cursor-pointer border transition-colors rounded-xl overflow-hidden ${themeSetting === 'light' ? 'border-plasma opacity-100 grayscale-0' : 'border-graphite opacity-50 grayscale hover:grayscale-0 hover:border-ghost/30'}`}>
                                                    <div className="h-24 bg-white flex flex-col p-2 gap-2">
                                                        <div className="w-full h-4 bg-gray-100 rounded"></div>
                                                        <div className="w-2/3 h-4 bg-blue-100 rounded"></div>
                                                    </div>
                                                    <div className={`py-2 text-center text-xs font-medium border-t ${themeSetting === 'light' ? 'bg-gray-100 text-gray-800 border-gray-200' : 'bg-gray-200/50 text-gray-500 border-transparent'}`}>Light Mode {themeSetting === 'light' && '(Active)'}</div>
                                                </div>
                                                <div onClick={() => setThemeSetting('system')} className={`cursor-pointer border transition-colors rounded-xl overflow-hidden ${themeSetting === 'system' ? 'border-plasma opacity-100 grayscale-0' : 'border-graphite opacity-50 grayscale hover:grayscale-0 hover:border-ghost/30'}`}>
                                                    <div className="h-24 bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
                                                        <Settings className={`w-8 h-8 ${themeSetting === 'system' ? 'text-plasma' : 'text-gray-500'}`} />
                                                    </div>
                                                    <div className={`py-2 text-center text-xs font-medium border-t ${themeSetting === 'system' ? 'bg-gray-800 text-gray-200 border-gray-700' : 'bg-gray-800/50 text-gray-500 border-transparent'}`}>Theo hệ thống {themeSetting === 'system' && '(Active)'}</div>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {activeSettingsTab === 'billing' && (
                                        <div className="animate-fade-up">
                                            <h2 className="text-2xl font-bold text-ghost mb-6">Quản lý gói thuê bao</h2>
                                            
                                            <div className="p-6 rounded-3xl bg-graphite/40 border border-plasma/30 relative overflow-hidden mb-6 group">
                                                <div className="absolute -right-10 -top-10 w-40 h-40 bg-plasma/20 blur-3xl rounded-full group-hover:bg-plasma/30 transition-all duration-700"></div>
                                                <div className="relative z-10 flex items-center justify-between mb-4">
                                                    <div>
                                                        <div className="text-plasma font-bold uppercase tracking-widest text-xs mb-1">Gói hiện tại</div>
                                                        <div className="text-3xl font-black text-ghost">{currentTier === 'vip' ? 'Gateway VIP' : 'Gateway Free'}</div>
                                                    </div>
                                                    <div className="text-right">
                                                        <div className="text-2xl font-bold text-ghost">{currentTier === 'vip' ? '$20' : '$0'}<span className="text-sm text-ghost/50 font-normal">/tháng</span></div>
                                                    </div>
                                                </div>
                                                <ul className="space-y-2 mb-6">
                                                    <li className="flex items-center gap-2 text-sm text-ghost/80"><Check className="w-4 h-4 text-plasma" /> Quyền truy cập GPT-4o, Claude 3.5 Sonnet</li>
                                                    <li className="flex items-center gap-2 text-sm text-ghost/80"><Check className="w-4 h-4 text-plasma" /> {currentTier === 'vip' ? 'Fallback & Orchestration không giới hạn' : `Sử dụng ${10 - promptCount} lượt gọi còn lại`}</li>
                                                    <li className="flex items-center gap-2 text-sm text-ghost/80"><Check className="w-4 h-4 text-plasma" /> API nội bộ tốc độ cao</li>
                                                </ul>
                                                <button onClick={() => setToast('Tính năng quản lý thanh toán đang được tích hợp.')} className="w-full py-3 rounded-xl border border-ghost/20 text-ghost hover:bg-ghost/5 transition-colors text-sm font-bold">
                                                    Hủy gia hạn
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {activeSettingsTab === 'help' && (
                                        <div className="animate-fade-up">
                                            <h2 className="text-2xl font-bold text-ghost mb-6">Trợ giúp & Tài liệu</h2>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div onClick={() => window.open('http://127.0.0.1:8000/docs', '_blank')} className="p-5 rounded-2xl bg-graphite/30 border border-graphite/50 hover:bg-graphite/50 transition-colors cursor-pointer">
                                                    <Box className="w-6 h-6 text-ghost/80 mb-3" />
                                                    <div className="font-bold text-ghost mb-1">Tài liệu API</div>
                                                    <div className="text-xs text-ghost/50 leading-relaxed">Hướng dẫn tích hợp Gateway vào hệ thống của bạn qua endpoint /v1/chat/completions.</div>
                                                </div>
                                                <div onClick={() => setToast('Cửa sổ hỗ trợ sẽ sớm được ra mắt.')} className="p-5 rounded-2xl bg-graphite/30 border border-graphite/50 hover:bg-graphite/50 transition-colors cursor-pointer">
                                                    <HelpCircle className="w-6 h-6 text-ghost/80 mb-3" />
                                                    <div className="font-bold text-ghost mb-1">Hỗ trợ kỹ thuật</div>
                                                    <div className="text-xs text-ghost/50 leading-relaxed">Chat trực tiếp với đội ngũ kĩ sư hoặc tạo ticket để báo lỗi hệ thống.</div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

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

                {/* Login Gate — shown after 3 guest prompts */}
                {showLoginGate && (
                    <div className="absolute inset-0 z-[100] flex items-center justify-center p-4 bg-black/85 backdrop-blur-xl">
                        <div className="bg-void border border-graphite p-10 rounded-[2.5rem] max-w-md w-full shadow-2xl relative overflow-hidden">
                            <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-plasma/40 to-transparent" />

                            <div className="relative z-10">
                                <p className="font-mono text-xs text-ghost/30 uppercase tracking-widest mb-6">Session limit reached</p>

                                <h2 className="text-3xl font-black text-ghost mb-3 tracking-tight">Continue with an account</h2>
                                <p className="text-ghost/50 text-sm leading-relaxed mb-8">
                                    You've used your 3 trial prompts. Sign in to keep going — free accounts get unlimited access on our free-tier models.
                                </p>

                                {/* Tier comparison */}
                                <div className="space-y-2 mb-8">
                                    <div className="flex items-center justify-between py-3 px-4 rounded-xl border border-graphite bg-graphite/30">
                                        <div>
                                            <span className="text-ghost/90 font-semibold text-sm">Free account</span>
                                            <p className="text-ghost/40 text-xs mt-0.5">Unlimited prompts · Free models</p>
                                        </div>
                                        <span className="font-mono text-xs text-ghost/40">$0 / mo</span>
                                    </div>
                                    <div className="flex items-center justify-between py-3 px-4 rounded-xl border border-plasma/30 bg-plasma/5">
                                        <div>
                                            <span className="text-plasma font-semibold text-sm">VIP</span>
                                            <p className="text-ghost/40 text-xs mt-0.5">Unlimited · Best models · Priority routing</p>
                                        </div>
                                        <span className="font-mono text-xs text-plasma">$9 / mo</span>
                                    </div>
                                </div>

                                <div className="flex flex-col gap-3">
                                    <button
                                        onClick={() => navigate('/login')}
                                        className="magnetic-btn group w-full relative overflow-hidden bg-plasma text-void font-bold rounded-2xl px-6 py-4 flex items-center justify-center tracking-widest uppercase text-sm hover:scale-[1.02] transition-all duration-300 shadow-[0_0_30px_rgba(123,97,255,0.15)]"
                                    >
                                        <span className="absolute inset-0 bg-white/10 -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out" />
                                        <span className="relative z-10">Sign in</span>
                                    </button>
                                    <button
                                        onClick={() => setShowLoginGate(false)}
                                        className="w-full py-3 px-6 rounded-2xl text-ghost/30 hover:text-ghost/60 transition-colors text-xs uppercase tracking-widest"
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
