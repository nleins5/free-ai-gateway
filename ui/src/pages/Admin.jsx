import { useState, useEffect, useRef, useCallback } from 'react';
import gsap from 'gsap';
import { Activity, Zap, DollarSign, Server, RefreshCw, Terminal, Shield, Cpu, Binary, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const MagneticButton = ({ children, className = "", onClick, to, variant = "primary", disabled, type="button" }) => {
  const btnRef = useRef(null);

  const handleMouseMove = (e) => {
    if (disabled) return;
    const { clientX, clientY } = e;
    const { left, top, width, height } = btnRef.current.getBoundingClientRect();
    const x = clientX - (left + width / 2);
    const y = clientY - (top + height / 2);
    gsap.to(btnRef.current, {
      x: x * 0.2,
      y: y * 0.2,
      duration: 0.3,
      ease: "power2.out"
    });
  };

  const handleMouseLeave = () => {
    if (disabled) return;
    gsap.to(btnRef.current, {
      x: 0,
      y: 0,
      duration: 0.5,
      ease: "elastic.out(1, 0.3)"
    });
  };

  const variants = {
    primary: "bg-[var(--accent)] text-[var(--primary)] font-bold",
    glass: "glass text-white font-medium hover:bg-white/10",
  };

  const content = (
    <button 
      type={type}
      ref={btnRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`relative overflow-hidden px-8 py-4 rounded-full flex items-center justify-center gap-2 group cursor-pointer transition-transform duration-300 ease-out ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:scale-[1.03]'} ${variants[variant]} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {!disabled && <span className="absolute inset-0 bg-white/20 -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out"></span>}
      <span className="relative z-10 flex items-center gap-2 w-full justify-center">
        {children}
      </span>
    </button>
  );

  return to ? <Link to={to} className="inline-block w-full">{content}</Link> : content;
};

const MetricCard = ({ title, value, subValue, icon: Icon, trend }) => (
  <div className="glass rounded-premium p-6 relative overflow-hidden group hover-lift border border-white/5 transition-all duration-500 hover:border-[var(--accent)]/30">
    <div className="flex justify-between items-start mb-4 relative z-10">
      <div className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center group-hover:bg-[var(--accent)]/10 transition-colors">
        <Icon className="w-6 h-6 text-white group-hover:text-[var(--accent)] transition-colors" />
      </div>
      {trend !== null && (
        <div className={`data-mono text-[10px] px-2 py-1 rounded-full ${trend >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'} border border-current/20`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
        </div>
      )}
    </div>
    <div className="relative z-10">
      <div className="text-xs font-bold uppercase tracking-widest text-[var(--bg-light)]/40 mb-1">{title}</div>
      <div className="text-3xl font-black text-white tracking-tighter group-hover:text-[var(--accent)] transition-colors">{value}</div>
      {subValue && (
        <div className="data-mono text-[10px] text-[var(--bg-light)]/30 mt-2 flex items-center gap-2">
          <span className="w-1 h-1 rounded-full bg-[var(--accent)]/50"></span>
          {subValue}
        </div>
      )}
    </div>
  </div>
);

const ProviderRow = ({ name, status, latency, weight, usage, tasks }) => {
  const isHealthy = status === 'active';

  return (
    <div className="flex items-center justify-between py-5 border-b border-white/5 last:border-0 hover:bg-white/5 px-6 -mx-6 rounded-2xl transition-all group">
      <div className="flex items-center gap-4 w-1/4">
        <div className="relative">
          <div className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
          {isHealthy && <div className="absolute inset-0 w-2 h-2 rounded-full bg-emerald-500 animate-ping opacity-75"></div>}
        </div>
        <div className="flex flex-col">
          <span className="font-bold text-white group-hover:text-[var(--accent)] transition-colors tracking-tight">{name}</span>
          <div className="flex gap-1 mt-1">
            {tasks.slice(0, 2).map(t => (
              <span key={t} className="data-mono text-[8px] uppercase px-1 border border-white/10 text-[var(--bg-light)]/40 rounded bg-white/5">{t}</span>
            ))}
          </div>
        </div>
      </div>
      <div className="w-1/4 flex justify-center">
        <div className={`data-mono text-xs px-3 py-1 rounded-full border ${latency < 200 ? 'border-emerald-500/20 text-emerald-400' : latency < 500 ? 'border-yellow-500/20 text-yellow-400' : 'border-red-500/20 text-red-400'}`}>
          {latency}ms
        </div>
      </div>
      <div className="w-1/4 flex flex-col items-center gap-2">
        <div className="w-32 h-1 bg-black/50 rounded-full overflow-hidden border border-white/5">
          <div className="h-full bg-[var(--accent)] shadow-[0_0_8px_var(--accent)] transition-all duration-1000" style={{ width: `${weight * 100}%` }}></div>
        </div>
        <span className="data-mono text-[10px] text-[var(--bg-light)]/40">{Math.round(weight * 100)}% LOAD</span>
      </div>
      <div className="w-1/4 text-right">
        <div className="data-mono text-sm text-white/90">{usage.toLocaleString()}</div>
        <div className="data-mono text-[10px] text-[var(--bg-light)]/30 uppercase tracking-widest mt-1">Throughput</div>
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

  const containerRef = useRef(null);
  const loginRef = useRef(null);

  const fetchTelemetry = useCallback(async (currentSecret) => {
    if (!currentSecret) return;
    try {
      const headers = { 'X-Admin-Key': currentSecret };
      const [statsRes, providersRes] = await Promise.all([
        fetch(`${API_BASE}/admin/stats`, { headers }),
        fetch(`${API_BASE}/admin/providers`, { headers })
      ]);

      if (statsRes.status === 403 || providersRes.status === 403) {
        setIsAuthenticated(false);
        setAuthError('Invalid system protocol secret (Access Denied).');
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
      setAuthError('Cannot reach backend server. Make sure it is running.');
      setIsAuthenticated(false);
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

  // Entrance animations
  useEffect(() => {
    if (!isAuthenticated && loginRef.current) {
      gsap.fromTo(loginRef.current.children, 
        { y: 40, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, stagger: 0.1, ease: "power3.out" }
      );
    } else if (isAuthenticated && containerRef.current) {
      gsap.fromTo(".admin-reveal",
        { y: 40, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, stagger: 0.1, ease: "power3.out" }
      );
    }
  }, [isAuthenticated]);

  const handleLogin = (e) => {
    e.preventDefault();
    if (!secret.trim()) {
      setAuthError('Authentication key is required.');
      return;
    }
    setLoading(true);
    void fetchTelemetry(secret.trim());
  };

  const handleLogout = () => {
    localStorage.removeItem('adminSecret');
    setSecret('');
    setIsAuthenticated(false);
    setStats(null);
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[var(--primary)] flex items-center justify-center relative overflow-hidden p-6">
        {/* Cinematic Background */}
        <div className="absolute inset-0 z-0">
          <video autoPlay loop muted playsInline className="absolute inset-0 w-full h-full object-cover opacity-20 mix-blend-screen">
            <source src="https://videos.pexels.com/video-files/3129595/3129595-uhd_2560_1440_30fps.mp4" type="video/mp4" />
          </video>
          <div className="absolute inset-0 bg-gradient-to-t from-[var(--primary)] via-[var(--primary)]/60 to-[var(--primary)]/90"></div>
        </div>

        <div ref={loginRef} className="relative z-10 glass p-10 md:p-14 rounded-premium w-full max-w-md shadow-2xl border-white/10">
          <div className="mb-10 text-center">
            <div className="w-16 h-16 mx-auto bg-[var(--primary)] rounded-full flex items-center justify-center mb-6 border border-white/10 shadow-[0_0_30px_rgba(201,168,76,0.15)]">
              <Shield className="w-8 h-8 text-[var(--accent)]" />
            </div>
            <h1 className="text-4xl tracking-tighter mb-2">Nexus <span className="font-drama text-[var(--accent)]">Core.</span></h1>
            <p className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/40 mt-4">Restricted Telemetry Access</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-3">
              <label className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/60 ml-2">Authentication Key</label>
              <input
                type="password"
                value={secret}
                onChange={(e) => setSecret(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-black/40 border border-white/10 rounded-full px-6 py-4 outline-none focus:border-[var(--accent)] transition-all text-white data-mono placeholder:text-white/20 shadow-inner"
              />
            </div>
            {authError && <div className="data-mono text-red-400 text-xs text-center bg-red-500/10 py-3 rounded-full border border-red-500/20">{authError}</div>}
            
            <MagneticButton type="submit" disabled={loading} className="w-full mt-4">
              {loading ? 'DECRYPTING...' : 'INITIATE PROTOCOL'}
            </MagneticButton>
          </form>

          <div className="mt-10 text-center">
            <Link to="/" className="data-mono text-[var(--bg-light)]/40 hover:text-[var(--accent)] text-[10px] uppercase tracking-widest transition-all flex items-center justify-center gap-2">
              <ArrowLeft size={12} /> Return to Public Node
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--primary)] text-white relative overflow-hidden pb-20">
      {/* Abstract Background Elements */}
      <div className="absolute top-[-20%] right-[-10%] w-[800px] h-[800px] bg-[var(--accent)]/5 blur-[150px] rounded-full pointer-events-none"></div>
      
      {/* Navbar overlay */}
      <nav className="relative z-50 px-8 py-6 flex items-center justify-between border-b border-white/5 bg-[var(--primary)]/80 backdrop-blur-xl">
        <Link to="/" className="text-xl font-outfit font-black tracking-tighter flex items-center gap-2 hover:opacity-80 transition-opacity">
          <div className="w-8 h-8 rounded-full bg-[var(--accent)] flex items-center justify-center">
            <Shield size={16} className="text-[var(--primary)]" />
          </div>
          NEXUS CORE
        </Link>
        <div className="flex items-center gap-6">
          <div className="hidden md:flex items-center gap-2 bg-white/5 px-4 py-2 rounded-full border border-white/5">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/60">Global Routing: Optimal</span>
          </div>
          <button onClick={handleLogout} className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/60 hover:text-[var(--accent)] transition-colors">
            End Session
          </button>
        </div>
      </nav>

      <div ref={containerRef} className="max-w-7xl mx-auto px-8 pt-12 relative z-10">
        {/* Header */}
        <header className="admin-reveal flex flex-col md:flex-row justify-between items-start md:items-end mb-16 gap-6">
          <div>
            <h1 className="text-5xl md:text-7xl tracking-tighter mb-4">
              System <span className="font-drama text-[var(--accent)]">Telemetry.</span>
            </h1>
            <p className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/40 flex items-center gap-3">
              ROUTER_ID: NX-8000-PRIMARY <span className="w-1 h-1 rounded-full bg-white/20"></span> {currentTime.toLocaleTimeString([], { hour12: false })}
            </p>
          </div>
          <MagneticButton variant="glass" className="py-3 px-6 text-xs whitespace-nowrap">
            <RefreshCw size={14} className="animate-spin-slow opacity-50 mr-1" />
            Live Sync Active
          </MagneticButton>
        </header>

        {/* KPIs Grid */}
        <div className="admin-reveal grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          <MetricCard
            title="Neural Load"
            value={stats ? stats.summary.total_requests.toLocaleString() : "---"}
            subValue="Requests routed today"
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
        <div className="admin-reveal grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Routing Matrix Card */}
          <div className="lg:col-span-2 glass rounded-premium p-8 md:p-10 relative overflow-hidden">
            <div className="flex justify-between items-center mb-10 relative z-10">
              <div className="flex items-center gap-4">
                <Activity className="w-6 h-6 text-[var(--accent)]" />
                <h2 className="text-3xl tracking-tight">Provider Matrix</h2>
              </div>
            </div>

            <div className="flex data-mono text-[10px] text-[var(--bg-light)]/40 mb-4 px-6 uppercase tracking-widest relative z-10 border-b border-white/5 pb-4">
              <div className="w-1/4">Neural Node</div>
              <div className="w-1/4 text-center">Latency</div>
              <div className="w-1/4 text-center">Load Config</div>
              <div className="w-1/4 text-right">Throughput</div>
            </div>

            <div className="space-y-1 relative z-10">
              {loading && providersData.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 gap-4">
                  <div className="w-24 h-1 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-[var(--accent)] w-1/3 animate-[spin_2s_linear_infinite]"></div>
                  </div>
                  <div className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/40">Synchronizing...</div>
                </div>
              ) : (
                providersData.map((p, i) => (
                  <ProviderRow key={i} {...p} />
                ))
              )}
            </div>
          </div>

          {/* Console / System Logs */}
          <div className="glass rounded-premium p-8 flex flex-col relative overflow-hidden h-[600px]">
            <div className="flex items-center gap-3 mb-8">
              <Terminal className="w-6 h-6 text-[var(--accent)]" />
              <h2 className="text-3xl tracking-tight">Console</h2>
            </div>

            <div className="flex-1 bg-[#050505] rounded-[2rem] p-6 data-mono text-[10px] overflow-hidden relative border border-white/5">
              <div className="absolute top-0 left-0 w-full h-8 bg-gradient-to-b from-[#050505] to-transparent z-10 pointer-events-none"></div>
              <div className="space-y-4 text-[var(--bg-light)]/50 leading-relaxed overflow-y-auto h-full pr-2">
                <div className="flex gap-3">
                  <span className="text-[var(--accent)]/60 shrink-0">[14:42:01]</span>
                  <p><span className="text-[var(--accent)]">SYS_INIT:</span> Nexus Routing Protocol v2.4.0 active.</p>
                </div>
                <div className="flex gap-3">
                  <span className="text-[var(--accent)]/60 shrink-0">[14:42:05]</span>
                  <p><span className="text-[var(--accent)]">ROUTING:</span> Balanced to Groq_LLama_3.3_70b.</p>
                </div>
                <div className="flex gap-3">
                  <span className="text-yellow-500/60 shrink-0">[14:42:12]</span>
                  <p><span className="text-yellow-500">LATENCY:</span> Jitter on OpenRouter endpoint.</p>
                </div>
                <div className="flex gap-3">
                  <span className="text-[var(--accent)]/60 shrink-0">[14:42:13]</span>
                  <p><span className="text-[var(--accent)]">ADJUST:</span> Re-weighting provider chain.</p>
                </div>
                <div className="flex gap-3">
                  <span className="text-[var(--accent)]/60 shrink-0">[14:42:15]</span>
                  <p><span className="text-[var(--accent)]">SECURITY:</span> HMAC verified for session 9x8f.</p>
                </div>
                <div className="flex gap-3">
                  <span className="text-emerald-500/60 shrink-0">[14:42:21]</span>
                  <p><span className="text-emerald-500">HEALTH:</span> Heartbeat confirmed for all nodes.</p>
                </div>
                <div className="flex gap-3">
                  <span className="text-[var(--bg-light)]/20 shrink-0">[14:42:30]</span>
                  <p>Awaiting incoming neural signals...</p>
                </div>
              </div>
              <div className="absolute bottom-0 left-0 w-full h-8 bg-gradient-to-t from-[#050505] to-transparent z-10 pointer-events-none"></div>
            </div>

            <div className="mt-6 p-6 bg-white/5 border border-white/5 rounded-3xl">
              <div className="data-mono text-[10px] text-[var(--bg-light)]/40 uppercase tracking-widest mb-3 flex justify-between">
                <span>Matrix Integrity</span>
                <span className="text-emerald-400">99.9%</span>
              </div>
              <div className="h-1 bg-black/40 rounded-full overflow-hidden">
                <div className="h-full bg-[var(--accent)] w-full"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Admin;
