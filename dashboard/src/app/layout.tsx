import './globals.css';
import Link from 'next/link';
import { LayoutDashboard, MessageSquareText, Database, PhoneCall, Cpu, ArrowUpRight, Inbox, Mic, Radio, Zap } from 'lucide-react';
import AuthGuard from '@/components/AuthGuard';

export const metadata = {
  title: 'Astraventa Voice AI & RAG Control Center',
  description: 'Enterprise Voice Agent & Vector RAG Telemetry Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#080c14] text-slate-100 min-h-screen antialiased selection:bg-cyan-500/30 selection:text-cyan-300">
        <AuthGuard>
          <div className="flex flex-col min-h-screen">
            {/* Top Global Status Banner for Astraventa Company Phone Line */}
            <header className="bg-[#0b101b] border-b border-zinc-800/80 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs z-30">
              {/* Brand Info */}
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  <img src="/logo.png" alt="Astraventa Logo" className="w-6 h-6 object-contain rounded-md" />
                  <span className="font-bold tracking-tight text-white font-mono text-sm">
                    ASTRAVENTA <span className="text-cyan-400 font-normal text-xs">VOICE ENGINE</span>
                  </span>
                </div>
                <span className="hidden sm:inline-block text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 font-mono">
                  v3.2.0-ULTRA-LOW-LATENCY
                </span>
              </div>

              {/* Astraventa Company Phone Line Status */}
              <div className="flex items-center space-x-2 sm:space-x-4 bg-zinc-900/90 border border-zinc-700/60 rounded-full px-3 py-1">
                <div className="flex items-center space-x-2">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                  <PhoneCall className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="font-mono text-emerald-300 font-semibold tracking-wide">
                    +1 (925) 504-0101
                  </span>
                  <span className="text-[10px] text-zinc-400 hidden md:inline">
                    (Inbound Agent Live)
                  </span>
                </div>

                <div className="hidden lg:flex items-center space-x-2 pl-3 border-l border-zinc-800">
                  <Zap className="w-3 h-3 text-amber-400" />
                  <span className="text-[11px] font-mono text-zinc-300">
                    Groq Llama-3.3 + Cartesia Sonic (~320ms)
                  </span>
                </div>
              </div>

              {/* Quick Links */}
              <div className="flex items-center space-x-3">
                <span className="hidden xl:inline-flex items-center gap-1.5 text-[11px] font-mono text-zinc-400">
                  <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
                  Telnyx / LiveKit SIP Active
                </span>
                <a
                  href="https://astraventa.com"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-[11px] text-zinc-400 hover:text-white transition-colors font-mono"
                >
                  <span>astraventa.com</span>
                  <ArrowUpRight className="w-3 h-3" />
                </a>
              </div>
            </header>

            {/* Main App Container: Sidebar + Content */}
            <div className="flex flex-col md:flex-row flex-1 text-xs">
              {/* Sleek Modern Developer Sidebar */}
              <aside className="w-full md:w-60 bg-[#0a0e18] border-r border-zinc-800/80 p-3.5 flex flex-col justify-between z-20 flex-shrink-0">
                <div className="space-y-5">
                  {/* Primary Navigation */}
                  <div>
                    <div className="text-[10px] uppercase font-mono tracking-wider text-zinc-500 px-2.5 mb-2 font-semibold">
                      Control Center
                    </div>
                    <nav className="space-y-1">
                      {/* Voice AI Studio - Primary Hero */}
                      <Link
                        href="/admin/studio"
                        className="flex items-center justify-between px-3 py-2 rounded-lg text-[13px] font-medium text-pink-300 hover:text-white hover:bg-pink-500/10 transition-all group border border-pink-500/20 bg-pink-500/5 shadow-sm"
                      >
                        <div className="flex items-center space-x-2.5">
                          <Mic className="w-4 h-4 text-pink-400 group-hover:scale-110 transition-transform" />
                          <span className="font-semibold text-white">Voice Agent Hub</span>
                        </div>
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-pink-500/20 text-pink-300 font-mono font-bold">
                          Live Mic
                        </span>
                      </Link>

                      {/* Voice Calls (Inbound & Outbound) */}
                      <Link
                        href="/admin/calls"
                        className="flex items-center justify-between px-3 py-2 rounded-lg text-[13px] font-medium text-emerald-300 hover:text-white hover:bg-emerald-500/10 transition-all group border border-emerald-500/20 bg-emerald-500/5 shadow-sm"
                      >
                        <div className="flex items-center space-x-2.5">
                          <PhoneCall className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
                          <span className="font-semibold text-white">Voice Calls & Dialer</span>
                        </div>
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold">
                          In/Out
                        </span>
                      </Link>

                      {/* RAG Knowledge Base */}
                      <Link
                        href="/admin/knowledge-base"
                        className="flex items-center justify-between px-3 py-2 rounded-lg text-[13px] font-medium text-zinc-300 hover:text-white hover:bg-zinc-800/60 transition-colors group border border-transparent hover:border-zinc-700/40"
                      >
                        <div className="flex items-center space-x-2.5">
                          <Database className="w-4 h-4 text-violet-400 group-hover:scale-110 transition-transform" />
                          <span>RAG Knowledge Base</span>
                        </div>
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-violet-500/10 text-violet-400 font-mono">
                          Vector
                        </span>
                      </Link>

                      {/* Overview Telemetry */}
                      <Link
                        href="/admin/overview"
                        className="flex items-center justify-between px-3 py-2 rounded-lg text-[13px] font-medium text-zinc-300 hover:text-white hover:bg-zinc-800/60 transition-colors group border border-transparent hover:border-zinc-700/40"
                      >
                        <div className="flex items-center space-x-2.5">
                          <LayoutDashboard className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
                          <span>System Overview</span>
                        </div>
                      </Link>

                      {/* WhatsApp / SMS Inbox */}
                      <Link
                        href="/admin/inbox"
                        className="flex items-center justify-between px-3 py-2 rounded-lg text-[13px] font-medium text-zinc-300 hover:text-white hover:bg-zinc-800/60 transition-colors group border border-transparent hover:border-zinc-700/40"
                      >
                        <div className="flex items-center space-x-2.5">
                          <Inbox className="w-4 h-4 text-orange-400 group-hover:scale-110 transition-transform" />
                          <span>WhatsApp Inbox & Manual</span>
                        </div>
                      </Link>

                      {/* Realtime Stream */}
                      <Link
                        href="/admin/chats"
                        className="flex items-center justify-between px-3 py-2 rounded-lg text-[13px] font-medium text-zinc-300 hover:text-white hover:bg-zinc-800/60 transition-colors group border border-transparent hover:border-zinc-700/40"
                      >
                        <div className="flex items-center space-x-2.5">
                          <MessageSquareText className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
                          <span>WhatsApp Live Stream</span>
                        </div>
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 font-mono">
                          WS
                        </span>
                      </Link>
                    </nav>
                  </div>

                  {/* Active Voice Pipeline Status Card */}
                  <div className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3 space-y-2">
                    <div className="text-[10px] uppercase font-mono tracking-wider text-zinc-400 font-semibold flex items-center justify-between">
                      <span>Live Pipeline</span>
                      <span className="text-emerald-400 font-bold">READY</span>
                    </div>
                    <div className="space-y-1.5 font-mono text-[11px] text-zinc-400">
                      <div className="flex justify-between items-center">
                        <span className="text-zinc-500">STT:</span>
                        <span className="text-zinc-200">Deepgram Nova-3</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-zinc-500">LLM:</span>
                        <span className="text-cyan-300 font-semibold">Groq Llama-3.3-70B</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-zinc-500">TTS:</span>
                        <span className="text-pink-300">Cartesia Sonic-2</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-zinc-500">RAG:</span>
                        <span className="text-violet-300">Supabase pgvector</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Footer Info */}
                <div className="pt-3 border-t border-zinc-800/80 px-1 font-mono text-[11px] text-zinc-500 flex items-center justify-between">
                  <span>Astraventa Voice Bot</span>
                  <span className="text-emerald-400">● Live</span>
                </div>
              </aside>

              {/* Main Content Area */}
              <main className="flex-1 p-4 md:p-6 overflow-y-auto max-w-[1600px] mx-auto w-full">
                {children}
              </main>
            </div>
          </div>
        </AuthGuard>
      </body>
    </html>
  );
}
