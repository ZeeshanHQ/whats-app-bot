import './globals.css';
import Link from 'next/link';
import { LayoutDashboard, MessageSquareText, Database, Terminal, Cpu, ArrowUpRight } from 'lucide-react';

export const metadata = {
  title: 'Astraventa AI Engine | Developer Portal',
  description: 'High-Density Realtime Telemetry & Vector RAG Control Panel',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090d16] text-slate-100 min-h-screen antialiased flex flex-col md:flex-row text-xs selection:bg-emerald-500/30 selection:text-emerald-300">
        {/* OpenRouter / Vercel Ultra-Dense Developer Sidebar */}
        <aside className="w-full md:w-56 bg-[#0c1019] border-r border-zinc-800/70 p-3.5 flex flex-col justify-between z-20 flex-shrink-0">
          <div>
            {/* Header Brand */}
            <div className="flex items-center justify-between mb-5 px-1 pt-1">
              <div className="flex items-center space-x-2.5">
                <img src="/logo.png" alt="Astraventa Logo" className="w-7 h-7 object-contain rounded-md" />
                <div className="flex flex-col">
                  <span className="font-bold text-xs tracking-tight text-white font-mono">
                    ASTRAVENTA
                  </span>
                  <span className="text-[10px] text-zinc-500 font-mono tracking-wider">v2.5.0-PROD</span>
                </div>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono font-medium tracking-wide uppercase">
                API Live
              </span>
            </div>

            {/* Navigation Section */}
            <div className="space-y-4">
              <div>
                <div className="text-[10px] uppercase font-mono tracking-wider text-zinc-500 px-2.5 mb-1.5 font-semibold">
                  Telemetry & Controls
                </div>
                <nav className="space-y-0.5">
                  <Link
                    href="/admin/overview"
                    className="flex items-center justify-between px-2.5 py-1.5 rounded-md text-[13px] font-medium text-zinc-400 hover:text-white hover:bg-zinc-800/60 transition-colors group"
                  >
                    <div className="flex items-center space-x-2">
                      <LayoutDashboard className="w-3.5 h-3.5 text-emerald-400" strokeWidth={1.5} />
                      <span>Overview</span>
                    </div>
                  </Link>
                  <Link
                    href="/admin/chats"
                    className="flex items-center justify-between px-2.5 py-1.5 rounded-md text-[13px] font-medium text-zinc-400 hover:text-white hover:bg-zinc-800/60 transition-colors group"
                  >
                    <div className="flex items-center space-x-2">
                      <MessageSquareText className="w-3.5 h-3.5 text-cyan-400" strokeWidth={1.5} />
                      <span>Realtime Stream</span>
                    </div>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-cyan-500/10 text-cyan-400 font-mono">
                      WS
                    </span>
                  </Link>
                  <Link
                    href="/admin/knowledge-base"
                    className="flex items-center justify-between px-2.5 py-1.5 rounded-md text-[13px] font-medium text-zinc-400 hover:text-white hover:bg-zinc-800/60 transition-colors group"
                  >
                    <div className="flex items-center space-x-2">
                      <Database className="w-3.5 h-3.5 text-violet-400" strokeWidth={1.5} />
                      <span>Knowledge Base</span>
                    </div>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-violet-500/10 text-violet-400 font-mono">
                      768d
                    </span>
                  </Link>
                </nav>
              </div>

              <div>
                <div className="text-[10px] uppercase font-mono tracking-wider text-zinc-500 px-2.5 mb-1.5 font-semibold">
                  Engine Model
                </div>
                <div className="mx-1 p-2 rounded-md bg-zinc-900/80 border border-zinc-800 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Cpu className="w-3.5 h-3.5 text-emerald-400" strokeWidth={1.5} />
                    <span className="text-[11px] font-mono text-zinc-200">Gemini 2.5 Flash</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Footer WebSocket Telemetry */}
          <div className="pt-3 border-t border-zinc-800/80 mt-4 px-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="text-[11px] font-mono text-zinc-400">Meta Cloud v25.0</span>
              </div>
              <a
                href="https://astraventa.com"
                target="_blank"
                rel="noreferrer"
                className="text-zinc-500 hover:text-zinc-300 transition-colors"
              >
                <ArrowUpRight className="w-3.5 h-3.5" strokeWidth={1.5} />
              </a>
            </div>
          </div>
        </aside>

        {/* Dense Main Viewport */}
        <main className="flex-1 p-4 md:p-6 overflow-y-auto max-w-[1600px] mx-auto w-full">
          {children}
        </main>
      </body>
    </html>
  );
}
