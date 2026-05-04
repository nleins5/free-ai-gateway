import { useState, useEffect, useRef, useMemo } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { 
  ArrowRight, 
  Terminal, 
  Zap, 
  ShieldCheck, 
  Activity, 
  Layers, 
  Cpu, 
  Globe, 
  CheckCircle2,
  ChevronRight,
  Send,
  Image as ImageIcon,
  Loader2,
  Lock,
  BarChart3,
  Search,
  MessageSquare,
  Sparkles,
  RefreshCcw,
  Clock,
  Database
} from 'lucide-react';
import { BrowserRouter, Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom';

gsap.registerPlugin(ScrollTrigger);

// --- UTILS ---
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// --- SHARED COMPONENTS ---

const NoiseOverlay = () => (
  <div className="noise-overlay">
    <svg width="100%" height="100%">
      <filter id="noise">
        <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/>
      </filter>
      <rect width="100%" height="100%" filter="url(#noise)"/>
    </svg>
  </div>
);

const MagneticButton = ({ children, className = "", onClick, to, variant = "primary" }) => {
  const btnRef = useRef(null);
  const hoverRef = useRef(null);

  const handleMouseMove = (e) => {
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
    organic: "bg-[var(--organic)] text-white font-bold"
  };

  const content = (
    <div 
      ref={btnRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`magnetic-btn px-8 py-4 rounded-premium flex items-center justify-center gap-2 group cursor-pointer ${variants[variant]} ${className}`}
      onClick={onClick}
    >
      <span ref={hoverRef} className="absolute inset-0 bg-white/20 -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out"></span>
      <span className="relative z-10 flex items-center gap-2">
        {children}
      </span>
    </div>
  );

  return to ? <Link to={to} className="inline-block">{content}</Link> : content;
};

// --- NAVIGATION ---

const Navbar = () => {
  const [scrolled, setScrolled] = useState(false);
  const navRef = useRef(null);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav 
      ref={navRef}
      className={`fixed top-8 left-1/2 -translate-x-1/2 z-[1000] w-[90%] max-w-5xl px-6 py-4 rounded-full transition-all duration-500 flex items-center justify-between ${
        scrolled ? "bg-[var(--primary)]/60 backdrop-blur-xl border border-white/10 shadow-2xl" : "bg-transparent"
      }`}
    >
      <Link to="/" className="text-xl font-outfit font-black tracking-tighter flex items-center gap-2">
        <div className="w-8 h-8 rounded-full bg-[var(--accent)] flex items-center justify-center">
          <Zap size={16} className="text-[var(--primary)]" />
        </div>
        AETHER GATEWAY
      </Link>
      
      <div className="hidden md:flex items-center gap-8 text-sm font-medium tracking-wide">
        {['Features', 'Protocol', 'Manifesto', 'Admin'].map((item) => (
          <a key={item} href={`#${item.toLowerCase()}`} className="hover:text-[var(--accent)] transition-colors opacity-80 hover:opacity-100">
            {item}
          </a>
        ))}
      </div>

      <MagneticButton variant="glass" className="py-2 px-6 text-xs" to="/playground">
        LAUNCH GATEWAY
      </MagneticButton>
    </nav>
  );
};

// --- HERO SECTION ---

const Hero = () => {
  const heroRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from(".hero-content > *", {
        y: 60,
        opacity: 0,
        stagger: 0.1,
        duration: 1.2,
        ease: "power3.out"
      });
    }, heroRef);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={heroRef} className="relative h-[100dvh] w-full overflow-hidden flex flex-col justify-end p-8 md:p-20">
      <div className="absolute inset-0 z-0">
        <img 
          src="https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=2070&auto=format&fit=crop" 
          alt="Organic Textures" 
          className="w-full h-full object-cover scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[var(--primary)] via-[var(--primary)]/60 to-transparent"></div>
      </div>

      <div className="hero-content relative z-10 max-w-4xl">
        <h1 className="text-4xl md:text-7xl leading-tight mb-4">
          Intelligence is the <br />
          <span className="font-drama text-7xl md:text-9xl text-[var(--accent)]">Atelier.</span>
        </h1>
        <p className="text-xl md:text-2xl text-[var(--bg-light)]/60 max-w-2xl mb-12 font-outfit">
          Unified Neural Routing for the next generation of autonomous agents. 
          Access the world's most powerful models through a single, resilient gateway.
        </p>
        <div className="flex flex-wrap gap-4">
          <MagneticButton to="/playground">
            Start Exploration <ArrowRight size={20} />
          </MagneticButton>
          <MagneticButton variant="glass" onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}>
            View Protocol
          </MagneticButton>
        </div>
      </div>
    </section>
  );
};

// --- FEATURES (Interactive Artifacts) ---

const DiagnosticShuffler = () => {
  const [items, setItems] = useState([
    { label: "NEURAL_LATENCY", value: "14ms", color: "var(--accent)" },
    { label: "ROUTING_WEIGHT", value: "0.85", color: "var(--organic)" },
    { label: "PACKET_INTEGRITY", value: "99.9%", color: "var(--clay)" }
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      setItems(prev => {
        const next = [...prev];
        next.unshift(next.pop());
        return next;
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative h-48 w-full flex items-center justify-center perspective-1000">
      {items.map((item, idx) => (
        <div 
          key={item.label}
          className="absolute glass p-4 rounded-2xl w-full transition-all duration-700 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
          style={{
            transform: `translateY(${(idx - 1) * 40}px) translateZ(${(1 - idx) * 50}px) scale(${1 - idx * 0.05})`,
            opacity: 1 - idx * 0.3,
            zIndex: 10 - idx
          }}
        >
          <div className="flex justify-between items-center">
            <span className="data-mono text-[10px] opacity-50 tracking-widest">{item.label}</span>
            <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: item.color }}></div>
          </div>
          <div className="text-2xl font-black mt-1 data-mono">{item.value}</div>
        </div>
      ))}
    </div>
  );
};

const TelemetryTypewriter = () => {
  const [text, setText] = useState("");
  const messages = useMemo(() => [
    "> INITIATING_ROUTING_PROTOCOL...",
    "> CONNECTING_TO_GEMINI_PRO...",
    "> ANALYZING_CONTEXT_VECTORS...",
    "> FAILOVER_TRIGGERED: RE-ROUTING...",
    "> SYSTEM_OPTIMAL. READY."
  ], []);
  const [msgIdx, setMsgIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);

  useEffect(() => {
    if (charIdx < messages[msgIdx].length) {
      const timeout = setTimeout(() => {
        setText(prev => prev + messages[msgIdx][charIdx]);
        setCharIdx(prev => prev + 1);
      }, 50);
      return () => clearTimeout(timeout);
    } else {
      const timeout = setTimeout(() => {
        setText("");
        setCharIdx(0);
        setMsgIdx(prev => (prev + 1) % messages.length);
      }, 2000);
      return () => clearTimeout(timeout);
    }
  }, [charIdx, msgIdx, messages]);

  return (
    <div className="bg-black/40 rounded-2xl p-6 h-48 border border-white/5 font-mono text-sm overflow-hidden flex flex-col justify-end">
      <div className="flex items-center gap-2 mb-auto opacity-40">
        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
        <span className="text-[10px] uppercase tracking-tighter">Live Neural Feed</span>
      </div>
      <div className="text-[var(--accent)] mb-2">
        {text}<span className="inline-block w-2 h-4 bg-[var(--accent)] animate-pulse ml-1 align-middle"></span>
      </div>
    </div>
  );
};

const ProtocolScheduler = () => {
  const [active, setActive] = useState(2);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setActive(prev => (prev + 1) % 7);
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="glass rounded-2xl p-6 h-48 flex flex-col justify-between">
      <div className="flex justify-between items-center mb-4">
        <span className="text-xs font-bold opacity-50 uppercase tracking-widest">Resource Allocation</span>
        <Clock size={14} className="opacity-30" />
      </div>
      <div className="flex gap-2 justify-between items-end h-full">
        {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, i) => (
          <div key={i} className="flex flex-col items-center gap-2 flex-1">
            <div 
              className={`w-full rounded-full transition-all duration-500 ${
                active === i ? "bg-[var(--accent)] h-20" : "bg-white/10 h-8 hover:bg-white/20"
              }`}
            ></div>
            <span className="text-[10px] font-bold opacity-40">{day}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const FeatureCard = ({ title, desc, icon: Icon, children }) => (
  <div className="glass rounded-premium p-8 flex flex-col gap-6 hover-lift border border-white/5 group">
    <div className="flex items-center gap-4">
      <div className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center group-hover:bg-[var(--accent)]/10 transition-colors">
        <Icon size={24} className="group-hover:text-[var(--accent)] transition-colors" />
      </div>
      <h3 className="text-2xl">{title}</h3>
    </div>
    <p className="text-[var(--bg-light)]/40 text-sm leading-relaxed">
      {desc}
    </p>
    <div className="mt-auto">
      {children}
    </div>
  </div>
);

const Features = () => (
  <section id="features" className="py-32 px-8 md:px-20 max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
    <FeatureCard 
      title="Dynamic Routing" 
      desc="Automated provider arbitration based on real-time latency and cost metrics. Zero-latency failover."
      icon={Activity}
    >
      <DiagnosticShuffler />
    </FeatureCard>
    <FeatureCard 
      title="Neural Telemetry" 
      desc="Live tracing of every inference cycle. Direct visibility into the black box of model interactions."
      icon={Terminal}
    >
      <TelemetryTypewriter />
    </FeatureCard>
    <FeatureCard 
      title="Auto-Scaling" 
      desc="Intelligent resource scheduling that adapts to usage bursts. Maximum throughput, minimum waste."
      icon={Cpu}
    >
      <ProtocolScheduler />
    </FeatureCard>
  </section>
);

// --- PHILOSOPHY ---

const Philosophy = () => {
  const philRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from(".reveal-text", {
        scrollTrigger: {
          trigger: ".reveal-text",
          start: "top 80%",
        },
        y: 40,
        opacity: 0,
        duration: 1,
        stagger: 0.2
      });
    }, philRef);
    return () => ctx.revert();
  }, []);

  return (
    <section id="manifesto" ref={philRef} className="relative py-40 px-8 md:px-20 overflow-hidden bg-black">
      <div className="absolute inset-0 opacity-20 pointer-events-none">
        <img 
          src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop" 
          alt="Abstract Network" 
          className="w-full h-full object-cover grayscale opacity-30"
        />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto text-center md:text-left">
        <p className="reveal-text text-[var(--accent)] font-bold tracking-widest uppercase text-xs mb-8">THE MANIFESTO</p>
        <div className="reveal-text text-2xl md:text-4xl leading-relaxed mb-12 opacity-40 font-outfit">
          Most AI infrastructure focuses on: <br />
          <span className="text-white opacity-100 font-bold">Monolithic lock-in and vendor reliance.</span>
        </div>
        <div className="reveal-text text-4xl md:text-7xl leading-tight font-black">
          We focus on: <br />
          <span className="font-drama italic text-[var(--accent)]">Fluid Intelligence.</span>
        </div>
      </div>
    </section>
  );
};

// --- PROTOCOL (Stacking Cards) ---

const Protocol = () => {
  const sectionRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const cards = gsap.utils.toArray('.protocol-card');
      cards.forEach((card, i) => {
        if (i === cards.length - 1) return;
        
        ScrollTrigger.create({
          trigger: card,
          start: "top top",
          endTrigger: sectionRef.current,
          end: "bottom bottom",
          pin: true,
          pinSpacing: false,
          scrub: true,
          onUpdate: (self) => {
            gsap.to(card, {
              scale: 1 - self.progress * 0.1,
              filter: `blur(${self.progress * 10}px)`,
              opacity: 1 - self.progress * 0.5,
              duration: 0.1
            });
          }
        });
      });
    }, sectionRef);
    return () => ctx.revert();
  }, []);

  const steps = [
    {
      num: "01",
      title: "Discovery Protocol",
      desc: "Automatically map your organizational data into neural vectors with high-precision RAG stores.",
      img: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1964&auto=format&fit=crop"
    },
    {
      num: "02",
      title: "Provider Arbitration",
      desc: "Real-time auctioning of tasks to the provider that offers the best balance of accuracy and speed.",
      img: "https://images.unsplash.com/photo-1614850523296-d8c1af93d400?q=80&w=2070&auto=format&fit=crop"
    },
    {
      num: "03",
      title: "Continuous Synthesis",
      desc: "Unified output generation that blends results from multiple models into a single, cohesive intelligence stream.",
      img: "https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?q=80&w=1974&auto=format&fit=crop"
    }
  ];

  return (
    <section id="protocol" ref={sectionRef} className="relative py-20 px-8 md:px-20 bg-[var(--primary)]">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-4xl md:text-6xl mb-20 text-center">The Stacking Protocol</h2>
        <div className="flex flex-col gap-[30vh]">
          {steps.map((step, i) => (
            <div key={i} className="protocol-card relative w-full h-[80vh] rounded-[3rem] overflow-hidden flex items-center bg-[var(--primary)] border border-white/10">
              <div className="absolute inset-0 z-0">
                <img src={step.img} alt={step.title} className="w-full h-full object-cover opacity-40 scale-110" />
                <div className="absolute inset-0 bg-gradient-to-r from-[var(--primary)] via-[var(--primary)]/80 to-transparent"></div>
              </div>
              
              <div className="relative z-10 p-12 md:p-24 max-w-2xl">
                <span className="data-mono text-[var(--accent)] text-lg mb-4 block opacity-50 tracking-widest">{step.num} // ARCHIVE</span>
                <h3 className="text-4xl md:text-6xl mb-8 leading-tight">{step.title}</h3>
                <p className="text-xl text-[var(--bg-light)]/60 font-outfit mb-12">
                  {step.desc}
                </p>
                <MagneticButton variant="glass" className="px-10">
                  Detailed Documentation
                </MagneticButton>
              </div>
              
              <div className="hidden md:flex absolute right-24 bottom-24 items-center gap-12">
                 <div className="flex flex-col gap-2">
                    <div className="w-64 h-1 bg-white/10 rounded-full overflow-hidden">
                       <div className="h-full bg-[var(--accent)] w-1/3 animate-pulse"></div>
                    </div>
                    <span className="data-mono text-[10px] opacity-40">PROCESSING_STREAM_{step.num}</span>
                 </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// --- PLAYGROUND (The Interactive Element) ---

const Playground = () => {
  const [activeTab, setActiveTab] = useState('chat');
  const [prompt, setPrompt] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAction = async () => {
    if (!prompt) return;
    setLoading(true);
    try {
      if (activeTab === 'chat') {
        const res = await fetch(`${API_BASE}/v1/chat/unified`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: prompt })
        });
        const data = await res.json();
        setResponse(data.answer);
      } else {
        const res = await fetch(`${API_BASE}/v1/images/generations`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt })
        });
        const data = await res.json();
        setResponse(data.data[0].url);
      }
    } catch (err) {
      setResponse("Error connecting to neural gateway.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="min-h-screen pt-40 pb-20 px-8 md:px-20 max-w-7xl mx-auto">
      <div className="flex flex-col gap-12">
        <div className="text-center">
          <h2 className="text-5xl md:text-7xl mb-6">Neural Workbench</h2>
          <p className="text-[var(--bg-light)]/40 max-w-2xl mx-auto">
            Directly interface with the Aether Protocol. Switch between semantic reasoning and visual synthesis.
          </p>
        </div>

        <div className="glass rounded-[3rem] p-4 md:p-8 flex flex-col gap-8 shadow-3xl">
          <div className="flex justify-center gap-4">
            <button 
              onClick={() => setActiveTab('chat')}
              className={`px-8 py-3 rounded-full transition-all flex items-center gap-2 ${activeTab === 'chat' ? "bg-[var(--accent)] text-[var(--primary)] font-bold" : "hover:bg-white/5"}`}
            >
              <MessageSquare size={18} /> Chat Interface
            </button>
            <button 
              onClick={() => setActiveTab('image')}
              className={`px-8 py-3 rounded-full transition-all flex items-center gap-2 ${activeTab === 'image' ? "bg-[var(--accent)] text-[var(--primary)] font-bold" : "hover:bg-white/5"}`}
            >
              <ImageIcon size={18} /> Visual Synthesis
            </button>
          </div>

          <div className="relative">
            <textarea 
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder={activeTab === 'chat' ? "Ask the unified intelligence..." : "Describe a visual concept..."}
              className="w-full h-32 md:h-48 bg-black/40 rounded-[2rem] p-8 text-xl font-outfit border border-white/10 focus:border-[var(--accent)] focus:outline-none transition-all placeholder:opacity-20 resize-none"
            />
            <button 
              onClick={handleAction}
              disabled={loading}
              className="absolute bottom-6 right-6 w-14 h-14 rounded-full bg-[var(--accent)] text-[var(--primary)] flex items-center justify-center hover:scale-110 active:scale-95 transition-all shadow-xl disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin" /> : <Send size={24} />}
            </button>
          </div>

          {response && (
            <div className="p-8 bg-white/5 rounded-[2rem] border border-white/10 animate-fade-in overflow-hidden">
               {activeTab === 'chat' ? (
                 <div className="prose prose-invert max-w-none text-lg leading-relaxed opacity-80 whitespace-pre-wrap">
                   {response}
                 </div>
               ) : (
                 <img src={response} alt="Generated" className="w-full h-auto rounded-xl shadow-2xl" />
               )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

// --- FOOTER ---

const Footer = () => (
  <footer className="bg-black rounded-t-[4rem] px-8 md:px-20 py-24 mt-20">
    <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between gap-12">
      <div className="max-w-sm">
        <Link to="/" className="text-3xl font-black tracking-tighter mb-6 block">AETHER</Link>
        <p className="text-[var(--bg-light)]/40 leading-relaxed mb-8">
          The universal intelligence gateway for the next generation of digital agents. 
          Performance, resilience, and scale by design.
        </p>
        <div className="flex items-center gap-3 glass py-2 px-4 rounded-full w-fit">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
          <span className="data-mono text-[10px] uppercase tracking-widest">System Operational</span>
        </div>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-3 gap-12">
        <div>
          <h4 className="text-sm font-bold uppercase tracking-widest mb-6 text-[var(--accent)]">Protocol</h4>
          <ul className="flex flex-col gap-4 text-sm opacity-50">
            <li><a href="#features">Features</a></li>
            <li><a href="#protocol">Stacking</a></li>
            <li><a href="#manifesto">Manifesto</a></li>
          </ul>
        </div>
        <div>
          <h4 className="text-sm font-bold uppercase tracking-widest mb-6 text-[var(--accent)]">Resources</h4>
          <ul className="flex flex-col gap-4 text-sm opacity-50">
            <li><Link to="/admin">Admin Console</Link></li>
            <li><a href="#">API Specs</a></li>
            <li><a href="#">Network Stats</a></li>
          </ul>
        </div>
        <div>
          <h4 className="text-sm font-bold uppercase tracking-widest mb-6 text-[var(--accent)]">Legal</h4>
          <ul className="flex flex-col gap-4 text-sm opacity-50">
            <li><a href="#">Privacy</a></li>
            <li><a href="#">Terms</a></li>
            <li><a href="#">Security</a></li>
          </ul>
        </div>
      </div>
    </div>
    <div className="max-w-7xl mx-auto pt-12 mt-24 border-t border-white/5 text-[10px] data-mono opacity-20 text-center uppercase tracking-[0.5em]">
      © 2026 AETHER PROTOCOL // ALL NEURAL RIGHTS RESERVED.
    </div>
  </footer>
);

// --- MAIN APP ---

const LandingPage = () => (
  <main>
    <Hero />
    <Features />
    <Philosophy />
    <Protocol />
    <section className="py-20 text-center bg-[var(--primary)]">
       <h2 className="text-4xl md:text-6xl mb-12">Join the Waitlist.</h2>
       <div className="max-w-xl mx-auto px-8">
          <div className="relative group">
             <input type="email" placeholder="Enter your email" className="w-full bg-white/5 border border-white/10 rounded-full px-8 py-5 focus:outline-none focus:border-[var(--accent)] transition-all" />
             <button className="absolute right-2 top-2 bottom-2 bg-[var(--accent)] text-[var(--primary)] px-8 rounded-full font-bold hover:scale-105 active:scale-95 transition-all">
                Submit
             </button>
          </div>
       </div>
    </section>
  </main>
);

const App = () => {
  return (
    <BrowserRouter>
      <div className="relative overflow-x-hidden">
        <NoiseOverlay />
        <Navbar />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/playground" element={<Playground />} />
          {/* Admin and other routes would go here */}
        </Routes>
        <Footer />
      </div>
    </BrowserRouter>
  );
};

export default App;
