import { useState, useEffect, useRef, useMemo } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { 
  ArrowRight, 
  Terminal, 
  Zap, 
  Activity, 
  Cpu, 
  Clock
} from 'lucide-react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Chat from './pages/Chat';
import Login from './pages/Login';
import Admin from './pages/Admin';

gsap.registerPlugin(ScrollTrigger);

// --- SHARED COMPONENTS ---


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
        {['Features', 'Protocol', 'Manifesto'].map((item) => (
          <a key={item} href={`#${item.toLowerCase()}`} className="hover:text-[var(--accent)] transition-colors opacity-80 hover:opacity-100">
            {item}
          </a>
        ))}
        <Link to="/admin" className="hover:text-[var(--accent)] transition-colors opacity-80 hover:opacity-100">
          Admin
        </Link>
      </div>

      <MagneticButton variant="glass" className="py-2 px-6 text-xs" to="/playground">
        LAUNCH GATEWAY
      </MagneticButton>
    </nav>
  );
};

// --- HERO SECTION ---

const CinematicHeroBackground = () => (
  <div className="absolute inset-0 z-0 bg-[#0D0D12] overflow-hidden">
    {/* Cinematic Video Background */}
    <video 
      autoPlay 
      loop 
      muted 
      playsInline 
      className="absolute inset-0 w-full h-full object-cover opacity-60 mix-blend-screen"
    >
      <source src="https://videos.pexels.com/video-files/3129595/3129595-uhd_2560_1440_30fps.mp4" type="video/mp4" />
    </video>
    
    {/* Vignette Overlays for readability and fading edges */}
    <div className="absolute inset-0 bg-gradient-to-t from-[#0D0D12] via-[#0D0D12]/40 to-transparent opacity-90"></div>
    <div className="absolute inset-0 bg-gradient-to-r from-[#0D0D12] via-transparent to-transparent opacity-80"></div>
    <div className="absolute inset-0 bg-gradient-to-b from-[#0D0D12]/60 via-transparent to-transparent opacity-60"></div>
  </div>
);

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
        <CinematicHeroBackground />
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

const RotatingMotif = () => (
  <div className="w-full h-full flex items-center justify-end md:justify-center overflow-hidden opacity-50 md:pr-24">
    <svg viewBox="0 0 800 800" className="w-[800px] h-[800px] md:w-[1200px] md:h-[1200px] animate-[spin_40s_linear_infinite] opacity-60">
      <defs>
        <radialGradient id="grad1" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.2" />
          <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="400" cy="400" r="300" stroke="var(--accent)" strokeWidth="1" fill="url(#grad1)" strokeDasharray="4 12" />
      <circle cx="400" cy="400" r="250" stroke="var(--accent)" strokeWidth="0.5" fill="none" className="animate-[spin_20s_linear_infinite_reverse]" style={{ transformOrigin: 'center' }} />
      <circle cx="400" cy="400" r="200" stroke="var(--accent)" strokeWidth="2" fill="none" strokeDasharray="1 6" strokeLinecap="round" />
      <path d="M 100 400 L 700 400 M 400 100 L 400 700" stroke="var(--accent)" strokeWidth="0.5" className="opacity-30" />
      <g className="animate-[spin_60s_linear_infinite]" style={{ transformOrigin: 'center' }}>
        <polygon points="400,100 660,250 660,550 400,700 140,550 140,250" stroke="var(--accent)" strokeWidth="1" fill="none" opacity="0.5" />
        <polygon points="400,150 616,275 616,525 400,650 184,525 184,275" stroke="var(--accent)" strokeWidth="0.5" fill="none" opacity="0.3" className="animate-[spin_30s_linear_infinite_reverse]" style={{ transformOrigin: 'center' }} />
      </g>
    </svg>
  </div>
);

const LaserGrid = () => (
  <div className="w-full h-full relative overflow-hidden opacity-50 bg-[#0a0a0f]">
    <div 
      className="absolute inset-0 opacity-20"
      style={{
        backgroundImage: 'radial-gradient(var(--accent) 1px, transparent 1px)',
        backgroundSize: '40px 40px'
      }}
    />
    <div 
      className="absolute left-0 w-full h-[2px] bg-[var(--accent)] shadow-[0_0_15px_var(--accent)] opacity-80"
      style={{
        animation: 'scan-vertical 4s ease-in-out infinite alternate'
      }}
    />
    <div 
      className="absolute inset-0 opacity-10"
      style={{
        background: 'linear-gradient(45deg, transparent 40%, var(--accent) 45%, transparent 50%)',
        backgroundSize: '200% 200%',
        animation: 'shimmer 8s linear infinite'
      }}
    />
    <style dangerouslySetInnerHTML={{__html: `
      @keyframes scan-vertical {
        0% { top: -10%; }
        100% { top: 110%; }
      }
      @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
      }
    `}} />
  </div>
);

const PulsingWaveform = () => (
  <div className="w-full h-full flex items-center justify-end overflow-hidden opacity-60">
    <svg viewBox="0 0 1000 300" className="w-full h-[300px] md:h-[600px] scale-150 md:scale-100">
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation="5" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>
      <line x1="0" y1="150" x2="1000" y2="150" stroke="var(--accent)" strokeWidth="1" opacity="0.3" strokeDasharray="5 5" />
      <path
        d="M 0 150 L 200 150 L 250 50 L 300 250 L 350 100 L 400 200 L 450 150 L 600 150 L 650 20 L 700 280 L 750 150 L 1000 150"
        fill="none"
        stroke="var(--accent)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        filter="url(#glow)"
        style={{
          strokeDasharray: '1500',
          animation: 'draw-path 3s linear infinite'
        }}
      />
      <path
        d="M 0 150 L 200 150 L 250 50 L 300 250 L 350 100 L 400 200 L 450 150 L 600 150 L 650 20 L 700 280 L 750 150 L 1000 150"
        fill="none"
        stroke="var(--accent)"
        strokeWidth="1"
        opacity="0.3"
      />
    </svg>
    <style dangerouslySetInnerHTML={{__html: `
      @keyframes draw-path {
        0% { stroke-dashoffset: 1500; }
        100% { stroke-dashoffset: 0; }
      }
    `}} />
  </div>
);

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
      Visual: RotatingMotif
    },
    {
      num: "02",
      title: "Provider Arbitration",
      desc: "Real-time auctioning of tasks to the provider that offers the best balance of accuracy and speed.",
      Visual: LaserGrid
    },
    {
      num: "03",
      title: "Continuous Synthesis",
      desc: "Unified output generation that blends results from multiple models into a single, cohesive intelligence stream.",
      Visual: PulsingWaveform
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
                <step.Visual />
                <div className="absolute inset-0 bg-gradient-to-r from-[var(--primary)] via-[var(--primary)]/90 to-transparent"></div>
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

// --- PLAYGROUND MOVED TO PAGES/CHAT.JSX ---

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
  <div className="relative overflow-x-hidden">
    <Navbar />
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
    <Footer />
  </div>
);

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/playground" element={<Chat />} />
        <Route path="/login" element={<Login />} />
        <Route path="/admin" element={<Admin />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
