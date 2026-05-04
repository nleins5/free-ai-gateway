import { useState, useEffect, useCallback } from 'react';
import { Activity, Zap, DollarSign, Server, RefreshCw, Terminal, Shield, Cpu, Binary } from 'lucide-react';
import { Link } from 'react-router-dom';

const MetricCard = ({ title, value, subValue, icon: Icon, trend }) => (
    <div className="bg-graphite/40 border border-plasma/10 rounded-[2rem] p-6 relative overflow-hidden group hover:border-plasma/40 transition-all duration-500 hover:shadow-[0_0_30px_rgba(123,97,255,0.15)]">
        <div className="flex justify-between items-start mb-4 relative z-10">
            <div className="p-3 bg-void rounded-2xl border border-plasma/20 group-hover:border-plasma/50 transition-colors">
                <Icon className="w-5 h-5 text-plasma" />
            </div>
            {trend !== null && (
                <div className={`text-[10px] font-mono px-2 py-1 rounded-full ${trend >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'} border border-current/20`}>
                    {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
                </div>
            )}
        </div>
        <div className="relative z-10">
            <div className="text-xs font-mono uppercase tracking-widest text-ghost/40 mb-1">{title}</div>
            <div className="text-3xl font-sans font-bold text-ghost tracking-tighter group-hover:text-plasma transition-colors">{value}</div>
            {subValue && <div className="text-[10px] font-mono text-ghost/30 mt-2 flex items-center gap-2">
                <span className="w-1 h-1 rounded-full bg-plasma/50"></span>
                {subValue}
            </div>}
        </div>

        {/* Abstract background motif */}
        <div className="absolute -bottom-6 -right-6 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity">
            <Icon className="w-24 h-24 text-plasma" />
        </div>
    </div>
);

const ProviderRow = ({ name, status, latency, weight, usage, tasks }) => {
    const isHealthy = status === 'active';

    return (
        <div className="flex items-center justify-between py-5 border-b border-ghost/5 last:border-0 hover:bg-plasma/5 px-6 -mx-6 rounded-2xl transition-all group">
            <div className="flex items-center gap-4 w-1/4">
                <div className="relative">
                    <div className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                    {isHealthy && <div className="absolute inset-0 w-2 h-2 rounded-full bg-emerald-500 animate-ping opacity-75"></div>}
                </div>
                <div className="flex flex-col">
                    <span className="font-sans font-bold text-ghost group-hover:text-plasma transition-colors">{name}</span>
                    <div className="flex gap-1 mt-1">
                        {tasks.slice(0, 2).map(t => (
                            <span key={t} className="text-[8px] font-mono uppercase px-1 border border-ghost/10 text-ghost/30 rounded">{t}</span>
                        ))}
                    </div>
                </div>
            </div>
            <div className="w-1/4 flex justify-center">
                <div className={`text-xs font-mono px-3 py-1 rounded-full border ${latency < 200 ? 'border-emerald-500/20 text-emerald-400' : latency < 500 ? 'border-yellow-500/20 text-yellow-400' : 'border-red-500/20 text-red-400'}`}>
                    {latency}ms
                </div>
            </div>
            <div className="w-1/4 flex flex-col items-center gap-2">
                <div className="w-32 h-1 bg-void rounded-full overflow-hidden border border-ghost/5">
                    <div className="h-full bg-plasma shadow-[0_0_8px_rgba(123,97,255,0.6)] transition-all duration-1000" style={{ width: `${weight * 100}%` }}></div>
                </div>
                <span className="text-[10px] font-mono text-ghost/30">{Math.round(weight * 100)}% load</span>
            </div>
            <div className="w-1/4 text-right">
                <div className="font-mono text-sm text-ghost/80">{usage.toLocaleString()}</div>
                <div className="text-[10px] font-mono text-ghost/20 uppercase tracking-tighter">Throughput</div>
            </div>
        </div>
    );
};

const Admin = () => {
    const [currentTime, setCurrentTime] = useState(new Date());
    const [stats, setStats] = useState(null);
    const [providersData, setProvidersData] = useState([]);
    const [secret, setSecret] = useState(() => localStorage.getItem('adminSecret') || '');
    const [loading, setLoading] = useState(() => Boolean(localStorage.getItem('adminSecret')));
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [authError, setAuthError] = useState('');

    const fetchTelemetry = useCallback(async (currentSecret) => {
        if (!currentSecret) return;

        try {
            const headers = { 'X-Admin-Secret': currentSecret };
            const [statsRes, providersRes] = await Promise.all([
                fetch('/admin/stats', { headers }),
                fetch('/admin/providers', { headers })
            ]);

            if (statsRes.status === 403 || providersRes.status === 403) {
                setIsAuthenticated(false);
                setAuthError('Invalid system protocol secret');
                localStorage.removeItem('adminSecret');
                setLoading(false);
                return;
            }

            if (statsRes.ok && providersRes.ok) {
                setIsAuthenticated(true);
                setAuthError('');
                localStorage.setItem('adminSecret', currentSecret);

                const statsData = await statsRes.json();
                const providersList = await providersRes.json();

                setStats(statsData);

                const mappedProviders = providersList.providers.map(p => {
                    const pStats = statsData.providers[p.key] || {};
                    const latency = pStats.latency_ewma_ms || 0;
                    const requests = (pStats.today && pStats.today.requests) || 0;
                    const weight = p.in_chain ? 1.0 / providersList.chain_order.length : 0;

                    return {
                        name: p.name,
                        status: p.active ? 'active' : 'inactive',
                        latency: Math.round(latency),
                        weight: weight,
                        usage: requests,
                        tasks: p.tasks || []
                    };
                });

                setProvidersData(mappedProviders);
            }
        } catch (error) {
            console.error("Telemetry failure:", error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        const timer = setInterval(() => setCurrentTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    useEffect(() => {
        if (!secret || isAuthenticated) return undefined;

        const initialFetchTimer = setTimeout(() => {
            void fetchTelemetry(secret);
        }, 0);

        return () => clearTimeout(initialFetchTimer);
    }, [fetchTelemetry, isAuthenticated, secret]);

    useEffect(() => {
        if (!isAuthenticated) return undefined;

        const dataTimer = setInterval(() => {
            void fetchTelemetry(secret);
        }, 5000);

        return () => clearInterval(dataTimer);
    }, [fetchTelemetry, isAuthenticated, secret]);

    const handleLogin = (e) => {
        e.preventDefault();
        if (!secret.trim()) {
            setAuthError('Authentication key is required');
            return;
        }
        setLoading(true);
        void fetchTelemetry(secret.trim());
    };

    if (!isAuthenticated) {
        return (
            <div className="min-h-screen bg-void text-ghost flex items-center justify-center relative overflow-hidden font-sans">
                {/* Cyberpunk background effect */}
                <div className="absolute inset-0 z-0">
                    <div className="absolute inset-0 bg-gradient-to-br from-plasma/5 to-transparent"></div>
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-plasma/5 blur-[120px] rounded-full"></div>
                </div>

                <div className="z-10 bg-graphite/40 border border-plasma/10 p-10 rounded-[3rem] w-full max-w-md backdrop-blur-3xl shadow-2xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-plasma to-transparent opacity-50"></div>

                    <div className="mb-10 flex flex-col items-center">
                        <div className="p-4 bg-void border border-plasma/30 rounded-3xl mb-6 shadow-[0_0_20px_rgba(123,97,255,0.2)]">
                            <Shield className="w-8 h-8 text-plasma" />
                        </div>
                        <h1 className="text-3xl font-bold tracking-tighter">Nexus <span className="text-plasma">Core</span></h1>
                        <p className="text-ghost/40 text-[10px] uppercase tracking-[0.2em] mt-2 font-mono">Restricted Access Telemetry</p>
                    </div>

                    <form onSubmit={handleLogin} className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-[10px] font-mono uppercase text-ghost/30 ml-1">Authentication Key</label>
                            <input
                                type="password"
                                value={secret}
                                onChange={(e) => setSecret(e.target.value)}
                                placeholder="••••••••••••"
                                className="w-full bg-void border border-plasma/10 rounded-2xl px-5 py-4 outline-none focus:border-plasma/50 transition-all text-ghost font-mono placeholder:text-ghost/10 shadow-inner"
                            />
                        </div>
                        {authError && <div className="text-red-400 text-xs font-mono text-center bg-red-500/5 py-2 rounded-lg border border-red-500/10">{authError}</div>}
                        <button type="submit" disabled={loading} className="group relative w-full bg-plasma text-void font-bold rounded-2xl py-4 overflow-hidden transition-all hover:shadow-[0_0_30px_rgba(123,97,255,0.4)] active:scale-95">
                            <span className="relative z-10 flex items-center justify-center gap-2">
                                {loading ? 'DECRYPTING...' : 'INITIATE PROTOCOL'}
                                {!loading && <Binary className="w-4 h-4" />}
                            </span>
                            <div className="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-in-out"></div>
                        </button>
                    </form>

                    <div className="mt-10 text-center">
                        <Link to="/" className="text-ghost/30 hover:text-plasma text-[10px] font-mono uppercase tracking-widest transition-all">
                            &larr; Exit to Public Node
                        </Link>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-void text-ghost relative overflow-hidden font-sans">
            {/* Ambient Lighting */}
            <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-plasma/5 blur-[150px] rounded-full -mr-48 -mt-48"></div>
            <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-plasma/5 blur-[150px] rounded-full -ml-32 -mb-32"></div>

            <div className="max-w-7xl mx-auto px-8 py-10 relative z-10">
                {/* Header */}
                <header className="flex justify-between items-start mb-16">
                    <div>
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-2 h-2 rounded-full bg-plasma shadow-[0_0_10px_rgba(123,97,255,0.8)]"></div>
                            <span className="text-[10px] font-mono uppercase tracking-[0.3em] text-plasma/60">Operational Matrix</span>
                        </div>
                        <h1 className="text-5xl font-bold tracking-tighter mb-2 italic">System <span className="text-plasma">Telemetry</span></h1>
                        <div className="flex items-center gap-4">
                            <p className="text-ghost/30 font-mono text-[10px] uppercase tracking-widest">Router ID: NX-8000-PRIMARY</p>
                            <span className="text-ghost/10">|</span>
                            <div className="flex items-center gap-2">
                                <div className="w-1 h-1 rounded-full bg-emerald-500"></div>
                                <span className="text-emerald-500/60 text-[10px] font-mono uppercase">Node Health: Optimal</span>
                            </div>
                        </div>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                        <div className="p-4 bg-graphite/40 border border-plasma/20 rounded-3xl backdrop-blur-xl">
                            <div className="text-3xl font-mono text-ghost tracking-tighter">{currentTime.toLocaleTimeString([], { hour12: false })}</div>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] font-mono text-plasma/40 uppercase tracking-widest mr-2">
                            <RefreshCw className="w-3 h-3 animate-spin-slow" /> Real-time Link Active
                        </div>
                    </div>
                </header>

                {/* KPIs Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
                    <MetricCard
                        title="Neural Load (Today)"
                        value={stats ? stats.summary.total_requests.toLocaleString() : "---"}
                        subValue="Requests routed"
                        icon={Cpu}
                        trend={12.4}
                    />
                    <MetricCard
                        title="Signal Latency"
                        value={stats ? `${Math.round(Object.values(stats.providers).reduce((acc, p) => acc + p.latency_ewma_ms, 0) / Math.max(1, Object.keys(stats.providers).length))}ms` : "---"}
                        subValue="Network weighted avg"
                        icon={Zap}
                        trend={-8.2}
                    />
                    <MetricCard
                        title="Token Economy"
                        value={stats ? `$${stats.summary.total_cost_usd.toFixed(4)}` : "---"}
                        subValue={stats && stats.summary.budget_limit_usd > 0 ? `Quota: $${stats.summary.budget_limit_usd}` : "Unlimited Tier"}
                        icon={DollarSign}
                        trend={2.1}
                    />
                    <MetricCard
                        title="Active Nodes"
                        value={stats ? `${stats.config.active_providers.length}/${Object.keys(stats.providers).length}` : "0/0"}
                        subValue="Current chain density"
                        icon={Server}
                        trend={null}
                    />
                </div>

                {/* Main Content */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    {/* Routing Matrix Card */}
                    <div className="lg:col-span-2 bg-graphite/30 border border-plasma/10 rounded-[3rem] p-10 backdrop-blur-2xl relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-8 opacity-5">
                            <Binary className="w-40 h-40" />
                        </div>

                        <div className="flex justify-between items-center mb-10 relative z-10">
                            <div className="flex items-center gap-3">
                                <Activity className="w-5 h-5 text-plasma" />
                                <h2 className="text-2xl font-bold tracking-tight">Provider Matrix</h2>
                            </div>
                            <button className="px-5 py-2 rounded-xl bg-void border border-plasma/30 text-plasma text-[10px] font-mono uppercase tracking-widest hover:bg-plasma hover:text-void transition-all duration-300">
                                Re-sync Chain
                            </button>
                        </div>

                        <div className="flex text-[10px] font-mono text-ghost/20 mb-6 px-6 uppercase tracking-[0.2em] relative z-10">
                            <div className="w-1/4">Neural Node</div>
                            <div className="w-1/4 text-center">Signal Latency</div>
                            <div className="w-1/4 text-center">Load Config</div>
                            <div className="w-1/4 text-right">Throughput</div>
                        </div>

                        <div className="space-y-2 relative z-10">
                            {loading && providersData.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-20 gap-4">
                                    <div className="w-12 h-1 bg-void rounded-full overflow-hidden">
                                        <div className="w-full h-full bg-plasma animate-loading-bar"></div>
                                    </div>
                                    <div className="text-ghost/30 font-mono text-[10px] uppercase tracking-widest">Awaiting Neural Link...</div>
                                </div>
                            ) : (
                                providersData.map((p, i) => (
                                    <ProviderRow key={i} {...p} />
                                ))
                            )}
                        </div>
                    </div>

                    {/* Console / System Logs */}
                    <div className="bg-void border border-plasma/10 rounded-[3rem] p-8 flex flex-col relative overflow-hidden shadow-2xl">
                        <div className="flex items-center gap-3 mb-8">
                            <Terminal className="w-5 h-5 text-plasma" />
                            <h2 className="text-2xl font-bold tracking-tight text-ghost">Neural Console</h2>
                        </div>

                        <div className="flex-1 bg-black/40 rounded-3xl p-6 font-mono text-[10px] overflow-hidden relative border border-ghost/5">
                            <div className="absolute top-0 left-0 w-full h-12 bg-gradient-to-b from-black/80 to-transparent z-10"></div>
                            <div className="space-y-4 text-ghost/50 leading-relaxed overflow-y-auto h-full pr-2 scrollbar-hide">
                                <div className="flex gap-3">
                                    <span className="text-plasma/60 shrink-0">[14:42:01]</span>
                                    <p><span className="text-plasma">SYS_INIT:</span> Nexus Routing Protocol v2.4.0 activated.</p>
                                </div>
                                <div className="flex gap-3">
                                    <span className="text-plasma/60 shrink-0">[14:42:05]</span>
                                    <p><span className="text-plasma">ROUTING:</span> Load balanced to Groq_LLama_3.3_70b.</p>
                                </div>
                                <div className="flex gap-3">
                                    <span className="text-yellow-500/60 shrink-0">[14:42:12]</span>
                                    <p><span className="text-yellow-500">LATENCY:</span> Jitter detected on OpenRouter endpoint.</p>
                                </div>
                                <div className="flex gap-3">
                                    <span className="text-plasma/60 shrink-0">[14:42:13]</span>
                                    <p><span className="text-plasma">ADJUST:</span> Re-weighting provider chain based on EWMA.</p>
                                </div>
                                <div className="flex gap-3">
                                    <span className="text-plasma/60 shrink-0">[14:42:15]</span>
                                    <p><span className="text-plasma">SECURITY:</span> HMAC verification successful for session 9x8f.</p>
                                </div>
                                <div className="flex gap-3">
                                    <span className="text-emerald-500/60 shrink-0">[14:42:21]</span>
                                    <p><span className="text-emerald-500">HEALTH:</span> Heartbeat confirmed for all 8 active nodes.</p>
                                </div>
                                <div className="flex gap-3">
                                    <span className="text-plasma/60 shrink-0">[14:42:25]</span>
                                    <p><span className="text-plasma">INGEST:</span> RAG chunking complete for manual-doc-v2.</p>
                                </div>
                                <div className="flex gap-3">
                                    <span className="text-ghost/20 shrink-0">[14:42:30]</span>
                                    <p>Awaiting incoming neural signals...</p>
                                </div>
                            </div>
                            <div className="absolute bottom-0 left-0 w-full h-12 bg-gradient-to-t from-black/80 to-transparent z-10"></div>
                        </div>

                        <div className="mt-8 p-6 bg-plasma/5 border border-plasma/10 rounded-2xl">
                            <div className="text-[10px] font-mono text-plasma/60 uppercase tracking-widest mb-1">Matrix Integrity</div>
                            <div className="h-1 bg-void rounded-full overflow-hidden mt-2">
                                <div className="h-full bg-plasma animate-pulse w-[98%]"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Global scanline effect */}
            <div className="pointer-events-none fixed inset-0 z-50 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.1)_50%),linear-gradient(90deg,rgba(255,0,0,0.02),rgba(0,255,0,0.01),rgba(0,0,255,0.02))] bg-[length:100%_2px,3px_100%]"></div>
        </div>
    );
};

export default Admin;
