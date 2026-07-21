'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Lock, Mail, Eye, EyeOff, ShieldCheck, Terminal, ArrowRight, CheckCircle2 } from 'lucide-react';

const REQUIRED_EMAIL = 'astraventahq@gmail.com';
const REQUIRED_PASSWORD = 'AstraVenta#2026!Secured';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);
  const [email, setEmail] = useState(REQUIRED_EMAIL);
  const [password, setPassword] = useState(REQUIRED_PASSWORD);
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const isAuth = sessionStorage.getItem('astra_auth') === 'true';
    setAuthenticated(isAuth);
  }, []);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setSubmitting(true);

    setTimeout(() => {
      if (
        email.trim().toLowerCase() === REQUIRED_EMAIL.toLowerCase() &&
        password === REQUIRED_PASSWORD
      ) {
        sessionStorage.setItem('astra_auth', 'true');
        setAuthenticated(true);
      } else {
        setErrorMsg('Invalid enterprise credentials. Please check email and password.');
      }
      setSubmitting(false);
    }, 400);
  };

  // Prevent layout jump while checking session storage
  if (authenticated === null) {
    return (
      <div className="min-h-screen w-full bg-[#090d16] flex items-center justify-center font-mono text-zinc-500 text-xs">
        Initializing Developer Portal Session...
      </div>
    );
  }

  if (!authenticated) {
    return (
      <div className="min-h-screen w-full bg-[#090d16] flex flex-col items-center justify-center p-4 selection:bg-emerald-500/30 selection:text-emerald-300 relative overflow-hidden font-sans">
        {/* Subtle Background Radial Gradient */}
        <div className="absolute w-[600px] h-[600px] bg-emerald-500/5 rounded-full blur-3xl pointer-events-none -top-40 -left-40"></div>
        <div className="absolute w-[500px] h-[500px] bg-cyan-500/5 rounded-full blur-3xl pointer-events-none -bottom-20 -right-20"></div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="dev-card w-full max-w-md p-6 rounded-xl border border-zinc-800 shadow-2xl relative z-10 space-y-5"
        >
          {/* Header Brand */}
          <div className="flex flex-col items-center text-center space-y-2 pb-2 border-b border-zinc-800/80">
            <div className="w-12 h-12 rounded-xl bg-zinc-900 border border-zinc-700/80 flex items-center justify-center shadow-inner">
              <img src="/logo.png" alt="Astraventa Logo" className="w-9 h-9 object-contain rounded-md" />
            </div>
            <div className="space-y-0.5">
              <h1 className="text-sm font-bold text-white font-mono tracking-tight flex items-center justify-center gap-1.5">
                ASTRAVENTA ENTERPRISE PORTAL
              </h1>
              <p className="text-[11px] text-zinc-400">
                Secure AI Developer Console & Telemetry Engine
              </p>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            {errorMsg && (
              <div className="p-2.5 rounded bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-mono text-center">
                {errorMsg}
              </div>
            )}

            {/* Email Field */}
            <div className="space-y-1">
              <label className="block text-[10px] font-mono uppercase tracking-wider text-zinc-400 font-semibold">
                Admin Email Address
              </label>
              <div className="relative">
                <Mail className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-2.5" strokeWidth={1.5} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="astraventahq@gmail.com"
                  required
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-md pl-9 pr-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500/60 font-mono"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1">
              <label className="block text-[10px] font-mono uppercase tracking-wider text-zinc-400 font-semibold">
                Developer Password
              </label>
              <div className="relative">
                <Lock className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-2.5" strokeWidth={1.5} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••••••"
                  required
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-md pl-9 pr-9 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500/60 font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-zinc-500 hover:text-zinc-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-3.5 h-3.5" strokeWidth={1.5} /> : <Eye className="w-3.5 h-3.5" strokeWidth={1.5} />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 rounded-md bg-emerald-500 text-black font-bold text-xs hover:bg-emerald-400 transition-colors flex items-center justify-center gap-2 font-mono shadow-md disabled:opacity-50"
            >
              <span>{submitting ? 'Authenticating...' : 'Sign In to Developer Console'}</span>
              <ArrowRight className="w-3.5 h-3.5" strokeWidth={2} />
            </button>
          </form>

          {/* Footer Encryption Badge */}
          <div className="pt-3 border-t border-zinc-800/80 text-[10px] font-mono text-zinc-500 flex items-center justify-between">
            <span className="flex items-center gap-1 text-emerald-400">
              <ShieldCheck className="w-3 h-3" strokeWidth={1.5} /> 256-Bit SSL Encrypted
            </span>
            <span>v2.5.0-PROD</span>
          </div>
        </motion.div>
      </div>
    );
  }

  return <>{children}</>;
}
