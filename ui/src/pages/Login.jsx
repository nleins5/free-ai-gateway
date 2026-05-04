import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import { ArrowLeft, Fingerprint, Zap, Loader2 } from 'lucide-react';

const Login = () => {
    const containerRef = useRef(null);
    const [loading, setLoading] = useState(false);
    const [email, setEmail] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const ctx = gsap.context(() => {
            gsap.from(".reveal-item", {
                y: 40,
                opacity: 0,
                stagger: 0.1,
                duration: 1,
                ease: "power3.out"
            });
        }, containerRef);
        return () => ctx.revert();
    }, []);

    const handleLogin = (e) => {
        e.preventDefault();
        if (!email) return;
        setLoading(true);
        // Simulate authentication and VIP status granting
        setTimeout(() => {
            // Generate a fresh user ID for the VIP session to reset limits
            const newUserId = crypto.randomUUID();
            localStorage.setItem('user_id', newUserId);
            // Optional: store auth token or VIP flag if the frontend relies on it
            localStorage.setItem('auth_token', 'vip_token_' + newUserId);
            localStorage.setItem('prompt_count', '0'); // Reset prompt count for VIP workflow
            
            navigate('/playground'); // Return to chat
        }, 1500);
    };

    return (
        <div ref={containerRef} className="min-h-screen bg-[var(--primary)] flex flex-col relative overflow-hidden font-sans">
            {/* Background Texture & Glow */}
            <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none noise-overlay"></div>
            <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
                <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-[var(--accent)]/10 blur-[120px]"></div>
                <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-[var(--accent)]/10 blur-[150px]"></div>
                <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=2070&auto=format&fit=crop')] mix-blend-overlay opacity-[0.15] object-cover w-full h-full grayscale"></div>
            </div>

            {/* Header */}
            <div className="relative z-10 p-8">
                <Link to="/" className="inline-flex items-center gap-3 text-[var(--bg-light)]/60 hover:text-[var(--bg-light)] transition-colors group reveal-item">
                    <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                    <span className="font-bold tracking-widest text-xs uppercase">Return to Node</span>
                </Link>
            </div>

            {/* Login Form Container */}
            <div className="relative z-10 flex-1 flex flex-col justify-center items-center p-6">
                <div className="w-full max-w-md">
                    <div className="text-center mb-10">
                        <div className="reveal-item w-16 h-16 rounded-full bg-[var(--accent)]/20 flex items-center justify-center mx-auto mb-6 border border-[var(--accent)]/30 shadow-[0_0_30px_var(--accent)]">
                            <Fingerprint className="w-8 h-8 text-[var(--accent)]" />
                        </div>
                        <h1 className="reveal-item text-4xl md:text-5xl font-black text-[var(--bg-light)] mb-3 tracking-tight font-outfit">Authenticate</h1>
                        <p className="reveal-item text-[var(--bg-light)]/50 font-mono text-sm tracking-widest uppercase">Acquire unrestricted neural access</p>
                    </div>

                    <form onSubmit={handleLogin} className="space-y-6">
                        <div className="reveal-item space-y-2">
                            <label className="text-xs font-bold text-[var(--bg-light)]/60 uppercase tracking-widest ml-1">Identity Vector (Email)</label>
                            <input 
                                type="email" 
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="operator@aether.net"
                                className="w-full glass rounded-2xl px-6 py-4 text-[var(--bg-light)] focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] transition-all placeholder:text-[var(--bg-light)]/20 font-mono text-sm"
                                required
                            />
                        </div>
                        
                        <div className="reveal-item">
                            <button 
                                type="submit" 
                                disabled={loading || !email}
                                className="magnetic-btn w-full relative group overflow-hidden bg-[var(--accent)] text-[var(--primary)] font-bold rounded-2xl px-6 py-4 flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:hover:scale-100"
                            >
                                <span className="absolute inset-0 bg-white/20 -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out"></span>
                                <span className="relative z-10 flex items-center gap-2">
                                    {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : (
                                        <>
                                            <Zap className="w-5 h-5" />
                                            INITIALIZE VIP UPLINK
                                        </>
                                    )}
                                </span>
                            </button>
                        </div>
                    </form>

                    <div className="reveal-item mt-10 p-6 glass rounded-2xl">
                        <h3 className="text-[var(--accent)] font-bold text-sm uppercase tracking-widest mb-2">Premium Perks</h3>
                        <ul className="text-[var(--bg-light)]/60 text-sm space-y-2 font-mono">
                            <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]"></div> Unlimited Reasoning Models (o1, Opus)</li>
                            <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]"></div> Zero-latency priority routing</li>
                            <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]"></div> Dedicated compute clusters</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            {/* Footer */}
            <div className="relative z-10 p-8 text-center">
                <span className="text-[var(--bg-light)]/30 text-xs font-mono tracking-widest uppercase">Aether Protocol • SECURE CONNECTION</span>
            </div>
        </div>
    );
};

export default Login;
