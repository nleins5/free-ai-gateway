import { useState, useEffect, useRef, useCallback } from 'react';
import gsap from 'gsap';
import { Activity, Zap, DollarSign, Server, RefreshCw, Terminal, Shield, Cpu, ArrowLeft, Users, TrendingUp, Eye, ChevronDown, ChevronUp, Plus, Trash2, Settings, Check, X, AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';

const API_BASE = import.meta.env.VITE_API_BASE || '';

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

const UserRow = ({ user, maxRequests }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const usagePercent = maxRequests > 0 ? (user.request_count / maxRequests) * 100 : 0;
  const totalTokens = (user.tokens_in || 0) + (user.tokens_out || 0);
  const lastActive = user.last_active ? new Date(user.last_active) : null;
  const now = new Date();
  const minutesAgo = lastActive ? Math.round((now - lastActive) / 60000) : null;

  const getTimeAgo = () => {
    if (!minutesAgo && minutesAgo !== 0) return 'Never';
    if (minutesAgo < 1) return 'Just now';
    if (minutesAgo < 60) return `${minutesAgo}m ago`;
    if (minutesAgo < 1440) return `${Math.round(minutesAgo / 60)}h ago`;
    return `${Math.round(minutesAgo / 1440)}d ago`;
  };

  const isOnline = minutesAgo !== null && minutesAgo < 5;

  return (
    <div className="border-b border-white/5 last:border-0 -mx-6 px-6 transition-all">
      <div 
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between py-4 hover:bg-white/5 rounded-2xl transition-all group cursor-pointer"
      >
        <div className="flex items-center gap-4 w-[22%]">
          <div className="relative">
            <div className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-black uppercase ${user.role === 'admin' ? 'bg-[var(--accent)]/20 text-[var(--accent)] border border-[var(--accent)]/30' : 'bg-white/10 text-white/60 border border-white/10'}`}>
              {user.username?.slice(0, 2) || '??'}
            </div>
            <div className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-[var(--primary)] ${isOnline ? 'bg-emerald-500' : user.is_active ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
          </div>
          <div className="flex flex-col min-w-0">
            <span className="font-bold text-white group-hover:text-[var(--accent)] transition-colors tracking-tight truncate">{user.username}</span>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`data-mono text-[8px] uppercase px-1.5 py-0.5 rounded border ${user.role === 'admin' ? 'border-[var(--accent)]/30 text-[var(--accent)] bg-[var(--accent)]/5' : 'border-white/10 text-white/40 bg-white/5'}`}>{user.role}</span>
              {!user.is_active && <span className="data-mono text-[8px] uppercase px-1.5 py-0.5 rounded border border-red-500/30 text-red-400 bg-red-500/5">Suspended</span>}
            </div>
          </div>
        </div>

        <div className="w-[15%] text-center">
          <div className="data-mono text-sm text-white/90 font-bold">{user.request_count.toLocaleString()}</div>
          <div className="data-mono text-[9px] text-white/30 uppercase tracking-wider mt-0.5">Requests</div>
        </div>

        <div className="w-[18%] text-center">
          <div className="data-mono text-sm text-white/90">{totalTokens.toLocaleString()}</div>
          <div className="data-mono text-[9px] text-white/30 uppercase tracking-wider mt-0.5">
            <span className="text-emerald-400/60">↓{(user.tokens_in || 0).toLocaleString()}</span>
            <span className="mx-1 text-white/10">|</span>
            <span className="text-blue-400/60">↑{(user.tokens_out || 0).toLocaleString()}</span>
          </div>
        </div>

        <div className="w-[15%] text-center">
          <div className={`data-mono text-sm font-bold ${user.total_cost_usd > 1 ? 'text-[var(--accent)]' : user.total_cost_usd > 0 ? 'text-white/90' : 'text-white/30'}`}>
            ${user.total_cost_usd.toFixed(4)}
          </div>
          <div className="data-mono text-[9px] text-white/30 uppercase tracking-wider mt-0.5">Revenue</div>
        </div>

        <div className="w-[15%] flex flex-col items-center gap-1.5">
          <div className="w-full h-1.5 bg-black/40 rounded-full overflow-hidden border border-white/5">
            <div
              className={`h-full rounded-full transition-all duration-1000 ${
                usagePercent > 80 ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]' :
                usagePercent > 50 ? 'bg-[var(--accent)] shadow-[0_0_8px_var(--accent)]' :
                'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]'
              }`}
              style={{ width: `${Math.min(usagePercent, 100)}%` }}
            ></div>
          </div>
          <span className="data-mono text-[9px] text-white/30">{Math.round(usagePercent)}% load</span>
        </div>

        <div className="w-[10%] text-right flex items-center justify-end gap-3">
          <div className="flex flex-col items-end">
            <div className={`data-mono text-xs ${isOnline ? 'text-emerald-400' : 'text-white/40'}`}>{getTimeAgo()}</div>
            <div className="data-mono text-[9px] text-white/20 uppercase tracking-wider mt-0.5">Last seen</div>
          </div>
          {isExpanded ? <ChevronUp size={16} className="text-white/40" /> : <ChevronDown size={16} className="text-white/40" />}
        </div>
      </div>
      
      {/* Expandable Models Sub-panel */}
      <div className={`overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.25,0.46,0.45,0.94)] ${isExpanded ? 'max-h-[500px] opacity-100 mb-4' : 'max-h-0 opacity-0'}`}>
        <div className="glass rounded-xl p-5 border border-white/5 bg-white/[0.02] ml-16 mr-4 relative">
          <div className="absolute top-0 left-6 w-[1px] h-full bg-gradient-to-b from-white/10 to-transparent -ml-10"></div>
          
          <h4 className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/40 mb-4 flex items-center gap-2">
            <Cpu size={12} className="text-[var(--accent)]" />
            Models Utilized
          </h4>
          
          {user.models_used && user.models_used.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {user.models_used.map((item, idx) => (
                <span key={item.model || idx} className="data-mono text-xs px-3 py-1.5 rounded-full border border-[var(--accent)]/20 text-[var(--accent)] bg-[var(--accent)]/5 hover:bg-[var(--accent)]/15 transition-colors cursor-default flex items-center gap-1.5">
                  {item.model || 'Unknown'}
                  <span className="bg-[var(--accent)]/20 text-[var(--accent)] px-1.5 py-0.5 rounded text-[10px] font-bold">
                    {item.count}
                  </span>
                </span>
              ))}
            </div>
          ) : (
            <div className="data-mono text-xs text-white/30 italic">No models utilized yet.</div>
          )}
        </div>
      </div>
    </div>
  );
};

const Admin = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [stats, setStats] = useState(null);
  const [providersData, setProvidersData] = useState([]);
  const [usersData, setUsersData] = useState([]);
  const [logsData, setLogsData] = useState([]);
  const [userSortField, setUserSortField] = useState('request_count');
  const [userSortDir, setUserSortDir] = useState('desc');
  const [secret, setSecret] = useState(() => localStorage.getItem('adminSecret') || '');
  const [loading, setLoading] = useState(() => Boolean(localStorage.getItem('adminSecret')));
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authError, setAuthError] = useState('');

  // Provider Manager state
  const [showAddProvider, setShowAddProvider] = useState(false);
  const [providerForm, setProviderForm] = useState({
    key: '', name: '', base_url: '', api_key: '', default_model: '', weight: 2, tasks: []
  });
  const [providerMsg, setProviderMsg] = useState({ type: '', text: '' });
  const [removingProvider, setRemovingProvider] = useState(null);

  const containerRef = useRef(null);
  const loginRef = useRef(null);

  const fetchTelemetry = useCallback(async (currentSecret) => {
    if (!currentSecret) return;
    try {
      const headers = { 'X-Admin-Key': currentSecret };
      const [statsRes, providersRes, usersRes, logsRes] = await Promise.all([
        fetch(`${API_BASE}/v1/admin/stats`, { headers }),
        fetch(`${API_BASE}/v1/admin/providers`, { headers }),
        fetch(`${API_BASE}/v1/admin/users`, { headers }),
        fetch(`${API_BASE}/v1/admin/logs?per_page=50`, { headers })
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
          const pState = statsData.providers[p.key] || {};
          const pUsage = statsData.daily_usage[p.key] || {};
          
          const latency = pState.latency_ewma_ms || 0;
          const requests = pUsage.requests || 0;
          const weight = p.in_chain ? 1.0 / providersList.chain_order.length : 0;

          return {
            name: p.name,
            status: pState.on_cooldown ? 'cooldown' : (p.active ? 'active' : 'inactive'),
            latency: Math.round(latency),
            weight: weight,
            usage: requests,
            tasks: p.tasks || []
          };
        });

        setProvidersData(mappedProviders);

        // Fetch users data
        if (usersRes && usersRes.ok) {
          const usersJson = await usersRes.json();
          setUsersData(usersJson.users || []);
        }
        if (logsRes && logsRes.ok) {
          const logsJson = await logsRes.json();
          setLogsData(logsJson.logs || []);
        }
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

  const addProvider = async () => {
    const { key, name, base_url, api_key, default_model, weight, tasks } = providerForm;
    if (!key || !name || !base_url || !api_key || !default_model) {
      setProviderMsg({ type: 'error', text: 'All fields are required.' });
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/v1/admin/providers/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Admin-Key': secret },
        body: JSON.stringify({ key, name, base_url, api_key, default_model, weight: Number(weight), tasks }),
      });
      const data = await res.json();
      if (data.status === 'success') {
        setProviderMsg({ type: 'success', text: data.message });
        setProviderForm({ key: '', name: '', base_url: '', api_key: '', default_model: '', weight: 2, tasks: [] });
        setShowAddProvider(false);
        void fetchTelemetry(secret);
        setTimeout(() => setProviderMsg({ type: '', text: '' }), 4000);
      } else {
        setProviderMsg({ type: 'error', text: data.message });
      }
    } catch (e) {
      setProviderMsg({ type: 'error', text: 'Failed to reach backend.' });
    }
  };

  const removeProvider = async (providerKey) => {
    if (!confirm(`Remove provider "${providerKey}" from the routing chain?`)) return;
    setRemovingProvider(providerKey);
    try {
      const res = await fetch(`${API_BASE}/v1/admin/providers/${providerKey}`, {
        method: 'DELETE',
        headers: { 'X-Admin-Key': secret },
      });
      const data = await res.json();
      if (data.status === 'success') {
        setProviderMsg({ type: 'success', text: data.message });
        void fetchTelemetry(secret);
        setTimeout(() => setProviderMsg({ type: '', text: '' }), 4000);
      } else {
        setProviderMsg({ type: 'error', text: data.message });
      }
    } catch (e) {
      setProviderMsg({ type: 'error', text: 'Failed to reach backend.' });
    } finally {
      setRemovingProvider(null);
    }
  };

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
            <span className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/60">Routing: {stats?.providers ? Object.values(stats.providers).filter(p => !p.on_cooldown).length : 0} active</span>
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
              MODE: {stats?.providers ? 'WEIGHTED' : '---'} <span className="w-1 h-1 rounded-full bg-white/20"></span> {currentTime.toLocaleTimeString([], { hour12: false })}
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
            value={stats ? (stats.total_requests_alltime || 0).toLocaleString() : "---"}
            subValue="Requests routed all-time"
            icon={Cpu}
            trend={null}
          />
          <MetricCard
            title="Token Volume"
            value={stats ? (stats.total_tokens_alltime || 0).toLocaleString() : "---"}
            subValue="Total tokens processed"
            icon={TrendingUp}
            trend={null}
          />
          <MetricCard
            title="Token Economy"
            value={stats ? `$${stats.total_cost_usd.toFixed(4)}` : "---"}
            subValue={stats && stats.budget_limit_usd > 0 ? `Quota: $${stats.budget_limit_usd}` : "Unlimited Tier"}
            icon={DollarSign}
            trend={null}
          />
          <MetricCard
            title="Active Nodes"
            value={stats ? `${providersData.filter(p => p.status === 'active').length}/${providersData.length}` : "0/0"}
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

          {/* Console / Real Request Logs */}
          <div className="glass rounded-premium p-8 flex flex-col relative overflow-hidden h-[600px]">
            <div className="flex items-center gap-3 mb-8">
              <Terminal className="w-6 h-6 text-[var(--accent)]" />
              <h2 className="text-3xl tracking-tight">Request Log</h2>
            </div>

            <div className="flex-1 bg-[#050505] rounded-[2rem] p-6 data-mono text-[10px] overflow-hidden relative border border-white/5">
              <div className="absolute top-0 left-0 w-full h-8 bg-gradient-to-b from-[#050505] to-transparent z-10 pointer-events-none"></div>
              <div className="space-y-3 text-[var(--bg-light)]/50 leading-relaxed overflow-y-auto h-full pr-2">
                {(logsData || []).length === 0 ? (
                  <div className="text-center py-20 text-white/20">No request logs yet</div>
                ) : (logsData || []).map((log, i) => (
                  <div key={log.id || i} className="flex gap-3">
                    <span className="text-[var(--bg-light)]/20 shrink-0">[{log.created_at ? new Date(log.created_at).toLocaleTimeString([], {hour12: false}) : '--:--'}]</span>
                    <p>
                      <span className={log.status === 'success' ? 'text-emerald-400' : 'text-red-400'}>{(log.provider || '?').toUpperCase()}:</span>
                      {' '}{log.model || 'unknown'} — {log.tokens_in || 0}↓ {log.tokens_out || 0}↑ — {Math.round(log.latency_ms || 0)}ms — ${(log.cost_usd || 0).toFixed(4)}
                      {log.status !== 'success' && log.error_msg && <span className="text-red-400/60 ml-2">[{log.error_msg.slice(0, 50)}]</span>}
                    </p>
                  </div>
                ))}
              </div>
              <div className="absolute bottom-0 left-0 w-full h-8 bg-gradient-to-t from-[#050505] to-transparent z-10 pointer-events-none"></div>
            </div>

            <div className="mt-6 p-6 bg-white/5 border border-white/5 rounded-3xl">
              <div className="data-mono text-[10px] text-[var(--bg-light)]/40 uppercase tracking-widest mb-3 flex justify-between">
                <span>Success Rate</span>
                <span className="text-emerald-400">{(() => { const fb = stats?.failover_breakdown || {}; let s = 0, t = 0; Object.values(fb).forEach(v => { s += v.success; t += v.success + v.error; }); return t > 0 ? (s / t * 100).toFixed(1) + '%' : 'N/A'; })()}</span>
              </div>
              <div className="h-1 bg-black/40 rounded-full overflow-hidden">
                <div className="h-full bg-[var(--accent)] transition-all duration-1000" style={{width: (() => { const fb = stats?.failover_breakdown || {}; let s = 0, t = 0; Object.values(fb).forEach(v => { s += v.success; t += v.success + v.error; }); return t > 0 ? `${(s / t * 100)}%` : '0%'; })()}}></div>
              </div>
            </div>
          </div>
        </div>

        {/* ═══════ USER BILLING TRACKER ═══════ */}
        <div className="admin-reveal mt-12">
          {/* Section Header */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
            <div>
              <h2 className="text-4xl md:text-5xl tracking-tighter mb-2">
                User <span className="font-drama text-[var(--accent)]">Billing.</span>
              </h2>
              <p className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/40">
                Revenue Tracking & Usage Monitoring
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 bg-white/5 px-4 py-2 rounded-full border border-white/5">
                <Users size={14} className="text-[var(--accent)] opacity-60" />
                <span className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/60">
                  {usersData.length} Registered
                </span>
              </div>
            </div>
          </div>

          {/* User Billing KPIs */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <MetricCard
              title="Total Users"
              value={usersData.length.toString()}
              subValue={`${usersData.filter(u => u.is_active).length} active accounts`}
              icon={Users}
              trend={null}
            />
            <MetricCard
              title="Total Revenue"
              value={`$${usersData.reduce((acc, u) => acc + (u.total_cost_usd || 0), 0).toFixed(4)}`}
              subValue="All-time accumulated"
              icon={TrendingUp}
              trend={null}
            />
            <MetricCard
              title="Avg Cost/User"
              value={usersData.length > 0 ? `$${(usersData.reduce((acc, u) => acc + (u.total_cost_usd || 0), 0) / usersData.length).toFixed(4)}` : '$0.0000'}
              subValue="Per-user average spend"
              icon={DollarSign}
              trend={null}
            />
          </div>

          {/* Users Table */}
          <div className="glass rounded-premium p-8 md:p-10 relative overflow-hidden">
            <div className="flex justify-between items-center mb-8 relative z-10">
              <div className="flex items-center gap-4">
                <Eye className="w-6 h-6 text-[var(--accent)]" />
                <h3 className="text-3xl tracking-tight">Usage Ledger</h3>
              </div>
              <div className="flex items-center gap-2">
                <span className="data-mono text-[9px] text-white/30 uppercase tracking-widest mr-2">Sort:</span>
                {[
                  { key: 'request_count', label: 'Requests' },
                  { key: 'total_cost_usd', label: 'Revenue' },
                  { key: 'tokens', label: 'Tokens' },
                ].map(s => (
                  <button
                    key={s.key}
                    onClick={() => {
                      if (userSortField === s.key) {
                        setUserSortDir(d => d === 'desc' ? 'asc' : 'desc');
                      } else {
                        setUserSortField(s.key);
                        setUserSortDir('desc');
                      }
                    }}
                    className={`data-mono text-[9px] uppercase tracking-widest px-3 py-1.5 rounded-full border transition-all flex items-center gap-1 ${
                      userSortField === s.key
                        ? 'border-[var(--accent)]/40 text-[var(--accent)] bg-[var(--accent)]/10'
                        : 'border-white/10 text-white/40 hover:border-white/20 hover:text-white/60'
                    }`}
                  >
                    {s.label}
                    {userSortField === s.key && (
                      userSortDir === 'desc' ? <ChevronDown size={10} /> : <ChevronUp size={10} />
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Table Header */}
            <div className="flex data-mono text-[10px] text-[var(--bg-light)]/40 mb-4 px-6 uppercase tracking-widest relative z-10 border-b border-white/5 pb-4">
              <div className="w-[22%]">User</div>
              <div className="w-[15%] text-center">Requests</div>
              <div className="w-[18%] text-center">Tokens (In/Out)</div>
              <div className="w-[15%] text-center">Revenue</div>
              <div className="w-[15%] text-center">Usage</div>
              <div className="w-[15%] text-right">Last Active</div>
            </div>

            {/* Table Body */}
            <div className="space-y-1 relative z-10 max-h-[500px] overflow-y-auto pr-2">
              {usersData.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 gap-4">
                  <Users className="w-12 h-12 text-white/10" />
                  <div className="text-center">
                    <div className="text-white/30 text-sm mb-1">No users registered yet</div>
                    <div className="data-mono text-[10px] uppercase tracking-widest text-white/15">
                      Users will appear here once they interact with the gateway
                    </div>
                  </div>
                </div>
              ) : (
                [...usersData]
                  .sort((a, b) => {
                    let aVal, bVal;
                    if (userSortField === 'tokens') {
                      aVal = (a.tokens_in || 0) + (a.tokens_out || 0);
                      bVal = (b.tokens_in || 0) + (b.tokens_out || 0);
                    } else {
                      aVal = a[userSortField] || 0;
                      bVal = b[userSortField] || 0;
                    }
                    return userSortDir === 'desc' ? bVal - aVal : aVal - bVal;
                  })
                  .map(user => (
                    <UserRow
                      key={user.id}
                      user={user}
                      maxRequests={Math.max(...usersData.map(u => u.request_count || 1), 1)}
                    />
                  ))
              )}
            </div>

            {/* Summary Footer */}
            {usersData.length > 0 && (
              <div className="mt-8 pt-6 border-t border-white/5 grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <div className="data-mono text-[9px] text-white/30 uppercase tracking-widest mb-1">Total Requests</div>
                  <div className="text-xl font-black text-white tracking-tight">
                    {usersData.reduce((acc, u) => acc + (u.request_count || 0), 0).toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="data-mono text-[9px] text-white/30 uppercase tracking-widest mb-1">Total Tokens</div>
                  <div className="text-xl font-black text-white tracking-tight">
                    {usersData.reduce((acc, u) => acc + (u.tokens_in || 0) + (u.tokens_out || 0), 0).toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="data-mono text-[9px] text-white/30 uppercase tracking-widest mb-1">Total Revenue</div>
                  <div className="text-xl font-black text-[var(--accent)] tracking-tight">
                    ${usersData.reduce((acc, u) => acc + (u.total_cost_usd || 0), 0).toFixed(4)}
                  </div>
                </div>
                <div>
                  <div className="data-mono text-[9px] text-white/30 uppercase tracking-widest mb-1">Active Now</div>
                  <div className="text-xl font-black text-emerald-400 tracking-tight flex items-center gap-2">
                    {usersData.filter(u => {
                      if (!u.last_active) return false;
                      return (new Date() - new Date(u.last_active)) < 300000;
                    }).length}
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ═══════ MODEL BREAKDOWN ═══════ */}
        <div className="admin-reveal mt-12">
          <div className="mb-8">
            <h2 className="text-4xl md:text-5xl tracking-tighter mb-2">Model <span className="font-drama text-[var(--accent)]">Breakdown.</span></h2>
            <p className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/40">Per-model token usage and cost</p>
          </div>
          <div className="glass rounded-premium p-8 md:p-10 overflow-hidden">
            <div className="flex data-mono text-[10px] text-[var(--bg-light)]/40 mb-4 px-6 uppercase tracking-widest border-b border-white/5 pb-4">
              <div className="w-[25%]">Model</div>
              <div className="w-[15%] text-center">Provider</div>
              <div className="w-[10%] text-center">Reqs</div>
              <div className="w-[15%] text-center">Tok In</div>
              <div className="w-[15%] text-center">Tok Out</div>
              <div className="w-[10%] text-center">Latency</div>
              <div className="w-[10%] text-right">Cost</div>
            </div>
            <div className="space-y-1 max-h-[400px] overflow-y-auto pr-2">
              {(stats?.model_breakdown || []).length === 0 ? (
                <div className="text-center py-16 text-white/20 data-mono text-xs">No model data yet</div>
              ) : (stats?.model_breakdown || []).map((m, i) => (
                <div key={i} className="flex items-center py-4 border-b border-white/5 last:border-0 hover:bg-white/5 px-6 -mx-6 rounded-2xl transition-all group">
                  <div className="w-[25%] font-bold text-white group-hover:text-[var(--accent)] transition-colors text-sm truncate">{m.model || 'unknown'}</div>
                  <div className="w-[15%] text-center"><span className="data-mono text-[9px] uppercase px-2 py-1 rounded-full border border-white/10 text-white/50 bg-white/5">{m.provider}</span></div>
                  <div className="w-[10%] text-center data-mono text-sm text-white/80">{m.requests.toLocaleString()}</div>
                  <div className="w-[15%] text-center data-mono text-xs text-emerald-400/70">{m.tokens_in.toLocaleString()}</div>
                  <div className="w-[15%] text-center data-mono text-xs text-blue-400/70">{m.tokens_out.toLocaleString()}</div>
                  <div className="w-[10%] text-center"><span className={`data-mono text-xs px-2 py-0.5 rounded-full border ${m.avg_latency_ms < 300 ? 'border-emerald-500/20 text-emerald-400' : m.avg_latency_ms < 800 ? 'border-yellow-500/20 text-yellow-400' : 'border-red-500/20 text-red-400'}`}>{Math.round(m.avg_latency_ms)}ms</span></div>
                  <div className={`w-[10%] text-right data-mono text-sm font-bold ${m.cost_usd > 0.01 ? 'text-[var(--accent)]' : 'text-white/50'}`}>${m.cost_usd.toFixed(4)}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ═══════ QUOTA & COST RATES ═══════ */}
        <div className="admin-reveal mt-12">
          <div className="mb-8">
            <h2 className="text-4xl md:text-5xl tracking-tighter mb-2">Quota <span className="font-drama text-[var(--accent)]">Monitor.</span></h2>
            <p className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/40">Daily budget and cost rate per provider</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass rounded-premium p-8">
              <div className="flex items-center gap-3 mb-6"><DollarSign className="w-6 h-6 text-[var(--accent)]" /><h3 className="text-2xl tracking-tight">Daily Budget</h3></div>
              <div>
                <div className="flex justify-between mb-3">
                  <span className="data-mono text-xs text-white/50">Spent Today</span>
                  <span className="data-mono text-xs text-white/50">{(stats?.budget_limit_usd || 0) > 0 ? `Limit: $${(stats?.budget_limit_usd || 0).toFixed(2)}` : 'Unlimited'}</span>
                </div>
                <div className="text-4xl font-black text-[var(--accent)] mb-4">${(stats?.total_cost_usd || 0).toFixed(4)}</div>
                {(stats?.budget_limit_usd || 0) > 0 && (
                  <div>
                    <div className="h-2 bg-black/40 rounded-full overflow-hidden border border-white/5">
                      <div className={`h-full rounded-full transition-all duration-1000 ${Math.min(((stats?.total_cost_usd || 0) / (stats?.budget_limit_usd || 1)) * 100, 100) > 80 ? 'bg-red-500' : 'bg-emerald-500'}`} style={{width: `${Math.min(((stats?.total_cost_usd || 0) / (stats?.budget_limit_usd || 1)) * 100, 100)}%`}}></div>
                    </div>
                    <div className="data-mono text-[9px] text-white/30 mt-2 text-right">{Math.min(((stats?.total_cost_usd || 0) / (stats?.budget_limit_usd || 1)) * 100, 100).toFixed(1)}% used</div>
                  </div>
                )}
              </div>
            </div>
            <div className="glass rounded-premium p-8">
              <div className="flex items-center gap-3 mb-6"><Zap className="w-6 h-6 text-[var(--accent)]" /><h3 className="text-2xl tracking-tight">Cost Rates (/1M tokens)</h3></div>
              <div className="space-y-2 max-h-[220px] overflow-y-auto pr-2">
                {Object.entries(stats?.cost_rates || {}).filter(([,v]) => v.input > 0 || v.output > 0).map(([key, rate]) => (<div key={key} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0"><span className="font-bold text-white text-sm">{key}</span><div className="data-mono text-[10px] text-white/50"><span className="text-emerald-400/70">↓${rate.input}</span><span className="mx-2 text-white/10">|</span><span className="text-blue-400/70">↑${rate.output}</span></div></div>))}
                {Object.entries(stats?.cost_rates || {}).filter(([,v]) => v.input > 0 || v.output > 0).length === 0 && (<div className="text-center py-8 text-white/20 data-mono text-xs">All providers are free-tier</div>)}
              </div>
            </div>
          </div>
        </div>

        {/* ═══════ FAILOVER TRACE ═══════ */}
        <div className="admin-reveal mt-12">
          <div className="mb-8">
            <h2 className="text-4xl md:text-5xl tracking-tighter mb-2">Failover <span className="font-drama text-[var(--accent)]">Trace.</span></h2>
            <p className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/40">Success vs failure ratio — identifies weak links in the chain</p>
          </div>
          <div className="glass rounded-premium p-8 md:p-10">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(stats?.failover_breakdown || {}).map(([provider, data]) => { const total = data.success + data.error; const sr = total > 0 ? (data.success / total) * 100 : 0; const isCore = ['groq','nvidia','github','gemini'].includes(provider); return (<div key={provider} className="bg-white/5 rounded-3xl p-6 border border-white/5 hover:border-[var(--accent)]/20 transition-all relative group"><div className="flex justify-between items-center mb-4"><span className="font-bold text-white tracking-tight">{provider}</span><div className="flex items-center gap-2"><span className={`data-mono text-xs font-bold ${sr > 90 ? 'text-emerald-400' : sr > 60 ? 'text-yellow-400' : 'text-red-400'}`}>{sr.toFixed(1)}%</span>{!isCore && <button onClick={() => removeProvider(provider)} disabled={removingProvider === provider} className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-full hover:bg-red-500/20 text-red-400/60 hover:text-red-400"><Trash2 size={12} /></button>}</div></div><div className="h-2 bg-black/40 rounded-full overflow-hidden border border-white/5 mb-3"><div className={`h-full rounded-full ${sr > 90 ? 'bg-emerald-500' : sr > 60 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{width: `${sr}%`}}></div></div><div className="flex justify-between data-mono text-[9px] text-white/30"><span className="text-emerald-400/60">✓ {data.success}</span><span className="text-red-400/60">✗ {data.error}</span></div>{isCore && <div className="absolute top-3 right-3"><span className="data-mono text-[7px] uppercase tracking-widest px-1.5 py-0.5 rounded border border-[var(--accent)]/20 text-[var(--accent)]/40 bg-[var(--accent)]/5">Core</span></div>}</div>); })}
              {Object.keys(stats?.failover_breakdown || {}).length === 0 && (<div className="col-span-full text-center py-16 text-white/20 data-mono text-xs">No failover data recorded yet</div>)}
            </div>
          </div>
        </div>

        {/* ═══════ PROVIDER MANAGER ═══════ */}
        <div className="admin-reveal mt-12">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
            <div>
              <h2 className="text-4xl md:text-5xl tracking-tighter mb-2">
                Provider <span className="font-drama text-[var(--accent)]">Manager.</span>
              </h2>
              <p className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/40">
                Add or remove AI providers from the routing chain at runtime
              </p>
            </div>
            <button
              onClick={() => { setShowAddProvider(!showAddProvider); setProviderMsg({ type: '', text: '' }); }}
              className={`flex items-center gap-2 px-6 py-3 rounded-full font-bold text-sm transition-all duration-300 ${showAddProvider ? 'bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30' : 'bg-[var(--accent)] text-[var(--primary)] hover:scale-[1.03]'}`}
            >
              {showAddProvider ? <><X size={16} /> Cancel</> : <><Plus size={16} /> Add Provider</>}
            </button>
          </div>

          {/* Feedback Toast */}
          {providerMsg.text && (
            <div className={`mb-6 flex items-center gap-3 px-6 py-4 rounded-2xl border data-mono text-xs transition-all duration-500 ${providerMsg.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
              {providerMsg.type === 'success' ? <Check size={16} /> : <AlertTriangle size={16} />}
              {providerMsg.text}
            </div>
          )}

          {/* Add Provider Form */}
          <div className={`overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.25,0.46,0.45,0.94)] ${showAddProvider ? 'max-h-[1500px] opacity-100 mb-8' : 'max-h-0 opacity-0'}`}>
            <div className="glass rounded-premium p-8 md:p-10 border border-[var(--accent)]/20">
              <div className="flex items-center gap-3 mb-8">
                <Settings className="w-6 h-6 text-[var(--accent)]" />
                <h3 className="text-2xl tracking-tight">Register New Provider</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div className="space-y-2">
                  <label className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/60 ml-2">Provider Key (slug)</label>
                  <input type="text" placeholder="e.g. mistral" value={providerForm.key} onChange={e => setProviderForm({...providerForm, key: e.target.value})} className="w-full bg-black/40 border border-white/10 rounded-2xl px-5 py-3.5 outline-none focus:border-[var(--accent)] transition-all text-white data-mono placeholder:text-white/20" />
                </div>
                <div className="space-y-2">
                  <label className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/60 ml-2">Display Name</label>
                  <input type="text" placeholder="e.g. Mistral AI" value={providerForm.name} onChange={e => setProviderForm({...providerForm, name: e.target.value})} className="w-full bg-black/40 border border-white/10 rounded-2xl px-5 py-3.5 outline-none focus:border-[var(--accent)] transition-all text-white data-mono placeholder:text-white/20" />
                </div>
                <div className="space-y-2">
                  <label className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/60 ml-2">Base URL</label>
                  <input type="text" placeholder="e.g. https://api.mistral.ai/v1" value={providerForm.base_url} onChange={e => setProviderForm({...providerForm, base_url: e.target.value})} className="w-full bg-black/40 border border-white/10 rounded-2xl px-5 py-3.5 outline-none focus:border-[var(--accent)] transition-all text-white data-mono placeholder:text-white/20" />
                </div>
                <div className="space-y-2">
                  <label className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/60 ml-2">API Key</label>
                  <input type="password" placeholder="sk-..." value={providerForm.api_key} onChange={e => setProviderForm({...providerForm, api_key: e.target.value})} className="w-full bg-black/40 border border-white/10 rounded-2xl px-5 py-3.5 outline-none focus:border-[var(--accent)] transition-all text-white data-mono placeholder:text-white/20" />
                </div>
                <div className="space-y-2">
                  <label className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/60 ml-2">Default Model</label>
                  <input type="text" placeholder="e.g. mistral-large-latest" value={providerForm.default_model} onChange={e => setProviderForm({...providerForm, default_model: e.target.value})} className="w-full bg-black/40 border border-white/10 rounded-2xl px-5 py-3.5 outline-none focus:border-[var(--accent)] transition-all text-white data-mono placeholder:text-white/20" />
                </div>
                <div className="space-y-2">
                  <label className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/60 ml-2">Routing Weight (1-10)</label>
                  <input type="number" min={1} max={10} value={providerForm.weight} onChange={e => setProviderForm({...providerForm, weight: e.target.value})} className="w-full bg-black/40 border border-white/10 rounded-2xl px-5 py-3.5 outline-none focus:border-[var(--accent)] transition-all text-white data-mono placeholder:text-white/20" />
                </div>
              </div>

              {/* Task Tier Checkboxes */}
              <div className="mb-8">
                <label className="data-mono text-[10px] uppercase tracking-widest text-[var(--bg-light)]/60 ml-2 block mb-3">Assign to Task Tiers</label>
                <div className="flex flex-wrap gap-2">
                  {['general', 'chat', 'research', 'code', 'reasoning', 'translate', 'summarize', 'rewrite'].map(task => {
                    const isSelected = providerForm.tasks.includes(task);
                    return (
                      <button
                        key={task}
                        onClick={() => {
                          setProviderForm(prev => ({
                            ...prev,
                            tasks: isSelected ? prev.tasks.filter(t => t !== task) : [...prev.tasks, task]
                          }));
                        }}
                        className={`data-mono text-[10px] uppercase tracking-widest px-4 py-2 rounded-full border transition-all ${isSelected ? 'border-[var(--accent)]/50 text-[var(--accent)] bg-[var(--accent)]/10' : 'border-white/10 text-white/40 hover:border-white/20 hover:text-white/60'}`}
                      >
                        {isSelected && <Check size={10} className="inline mr-1 -mt-0.5" />}
                        {task}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Submit */}
              <div className="flex justify-end">
                <button
                  onClick={addProvider}
                  className="bg-[var(--accent)] text-[var(--primary)] font-bold px-10 py-4 rounded-full hover:scale-[1.03] transition-transform flex items-center gap-2"
                >
                  <Plus size={18} />
                  Register Provider
                </button>
              </div>
            </div>
          </div>

          {/* Current Provider Chain */}
          <div className="glass rounded-premium p-8 md:p-10">
            <div className="flex items-center gap-3 mb-8">
              <Server className="w-6 h-6 text-[var(--accent)]" />
              <h3 className="text-2xl tracking-tight">Active Routing Chain</h3>
              <span className="data-mono text-[10px] text-white/30 ml-auto">{providersData.length} providers registered</span>
            </div>
            <div className="flex flex-wrap gap-3">
              {(stats ? Object.keys(stats.providers || {}) : []).concat(
                providersData.map(p => p.name.toLowerCase().replace(/\s+/g, '_'))
              ).filter((v, i, a) => a.indexOf(v) === i).length === 0 ? (
                <div className="text-center py-12 text-white/20 data-mono text-xs w-full">No providers in chain</div>
              ) : providersData.map((p, i) => {
                const isCore = ['Groq', 'Nvidia', 'Github', 'Gemini', 'NVIDIA NIM', 'GitHub Models', 'Google Gemini'].some(c => p.name.toLowerCase().includes(c.toLowerCase()));
                return (
                  <div key={i} className="relative group flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-[var(--accent)]/30 rounded-2xl px-4 py-3 transition-all">
                    <div className={`w-2 h-2 rounded-full ${p.status === 'active' ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                    <span className="font-bold text-white text-sm">{p.name}</span>
                    <span className="data-mono text-[9px] text-white/30">{p.latency}ms</span>
                    {!isCore && (
                      <button
                        onClick={() => removeProvider(p.name.toLowerCase().replace(/[\s()]/g, '_'))}
                        disabled={removingProvider !== null}
                        className="opacity-0 group-hover:opacity-100 transition-opacity ml-1 p-1 rounded-full hover:bg-red-500/20 text-red-400/50 hover:text-red-400"
                        title="Remove from chain"
                      >
                        <Trash2 size={12} />
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Admin;
