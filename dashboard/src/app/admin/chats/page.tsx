'use client';

import { useEffect, useState, useRef } from 'react';
import { supabase } from '@/lib/supabase';
import { motion, AnimatePresence } from 'framer-motion';
import { Phone, User, Bot, Radio, Send, RefreshCw, Terminal, Loader2 } from 'lucide-react';

interface ChatLog {
  id: string;
  wa_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export default function RealtimeChatsPage() {
  const [messages, setMessages] = useState<ChatLog[]>([]);
  const [activeWaId, setActiveWaId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [testInput, setTestInput] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchLogs = async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from('chat_logs')
      .select('*')
      .order('created_at', { ascending: true });

    if (error) {
      console.error('Error fetching chat logs:', error);
    } else if (data) {
      setMessages(data as ChatLog[]);
      if (data.length > 0 && !activeWaId) {
        const lastMsg = data[data.length - 1];
        setActiveWaId(lastMsg.wa_id);
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchLogs();

    const channel = supabase
      .channel('realtime-chat-stream')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'chat_logs',
        },
        (payload) => {
          const newMsg = payload.new as ChatLog;
          setMessages((prev) => {
            // Deduplicate if already present optimistically
            if (prev.some((m) => m.id === newMsg.id || (m.role === newMsg.role && m.content === newMsg.content && Math.abs(new Date(m.created_at).getTime() - new Date(newMsg.created_at).getTime()) < 3000))) {
              return prev;
            }
            return [...prev, newMsg];
          });

          if (!activeWaId) {
            setActiveWaId(newMsg.wa_id);
          }
        }
      )
      .subscribe((status) => {
        console.log('Supabase Realtime Channel Status:', status);
      });

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeWaId, sending]);

  const contactsMap: { [key: string]: { lastMsg: string; time: string; count: number } } = {};
  messages.forEach((msg) => {
    if (!contactsMap[msg.wa_id]) {
      contactsMap[msg.wa_id] = { lastMsg: msg.content, time: msg.created_at, count: 1 };
    } else {
      contactsMap[msg.wa_id].lastMsg = msg.content;
      contactsMap[msg.wa_id].time = msg.created_at;
      contactsMap[msg.wa_id].count += 1;
    }
  });

  const contactsList = Object.keys(contactsMap)
    .filter((wa_id) => !wa_id.includes('test_user'))
    .map((wa_id) => ({
      wa_id,
      ...contactsMap[wa_id],
    }));

  const activeThread = messages.filter((m) => m.wa_id === activeWaId);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testInput.trim() || !activeWaId) return;

    const userMsg = testInput.trim();
    setTestInput('');
    setSending(true);

    // 1. Optimistically append user message instantly to screen
    const userLog: ChatLog = {
      id: `user-${Date.now()}`,
      wa_id: activeWaId,
      role: 'user',
      content: userMsg,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userLog]);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ wa_id: activeWaId, message: userMsg }),
      });

      const data = await res.json();
      
      // 2. Append AI response instantly to screen when returned
      if (data.ai_reply) {
        const botLog: ChatLog = {
          id: `bot-${Date.now()}`,
          wa_id: activeWaId,
          role: 'assistant',
          content: data.ai_reply,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, botLog]);
      }
    } catch (err) {
      console.error('Error sending message:', err);
    } finally {
      setSending(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="h-[calc(100vh-4rem)] flex flex-col space-y-3"
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
        <div>
          <h1 className="text-base font-bold text-white flex items-center gap-2 font-mono -tracking-tight">
            REALTIME WHATSAPP STREAM
            <span className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono font-medium tracking-wide uppercase flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              WS Stream Active
            </span>
          </h1>
          <p className="text-[11px] text-zinc-400">
            Realtime message logs and conversation threads
          </p>
        </div>

        <button
          onClick={fetchLogs}
          className="px-2.5 py-1 rounded-md bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white hover:border-zinc-700 transition-colors text-xs font-mono flex items-center gap-1.5"
        >
          <RefreshCw className="w-3 h-3 text-emerald-400" strokeWidth={1.5} /> Re-Sync
        </button>
      </div>

      {/* Main Grid */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-3 overflow-hidden">
        {/* Contact List Sidebar */}
        <div className="md:col-span-4 dev-card p-3 flex flex-col h-full overflow-hidden">
          <div className="flex items-center justify-between pb-2 border-b border-zinc-800/80 mb-2 font-mono">
            <span className="text-[10px] uppercase font-semibold text-zinc-400 tracking-wider">
              Active Contacts ({contactsList.length})
            </span>
            <Radio className="w-3 h-3 text-emerald-400 animate-pulse" strokeWidth={1.5} />
          </div>

          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
            {contactsList.length === 0 ? (
              <div className="text-center py-12 text-zinc-500 text-xs font-mono">
                No active WhatsApp sessions.
              </div>
            ) : (
              contactsList.map((contact) => {
                const isActive = contact.wa_id === activeWaId;
                return (
                  <button
                    key={contact.wa_id}
                    onClick={() => setActiveWaId(contact.wa_id)}
                    className={`w-full text-left p-2.5 rounded-md transition-all border ${
                      isActive
                        ? 'bg-zinc-900 border-emerald-500/40 text-white shadow-sm'
                        : 'bg-zinc-950/40 border-zinc-800/60 hover:bg-zinc-900/60 text-zinc-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center space-x-1.5">
                        <Phone className="w-3 h-3 text-emerald-400" strokeWidth={1.5} />
                        <span className="text-xs font-semibold font-mono">
                          +{contact.wa_id}
                        </span>
                      </div>
                      <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400">
                        {contact.count} msgs
                      </span>
                    </div>
                    <p className="text-[11px] text-zinc-400 line-clamp-1 truncate font-sans">
                      {contact.lastMsg}
                    </p>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Conversation Stream Viewport */}
        <div className="md:col-span-8 dev-card flex flex-col h-full overflow-hidden">
          {/* Header */}
          <div className="p-3 border-b border-zinc-800/80 bg-zinc-950/70 flex items-center justify-between font-mono">
            <div className="flex items-center space-x-2">
              <div className="w-5 h-5 rounded bg-zinc-900 border border-zinc-700 flex items-center justify-center">
                <User className="w-3 h-3 text-emerald-400" strokeWidth={1.5} />
              </div>
              <span className="text-xs font-bold text-white">
                {activeWaId ? `+${activeWaId}` : 'Select contact'}
              </span>
            </div>
            <span className="text-[10px] text-zinc-400 font-mono">
              {activeThread.length} turns
            </span>
          </div>

          {/* Stream Feed */}
          <div className="flex-1 p-3.5 overflow-y-auto space-y-3 font-sans">
            {activeThread.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-zinc-500 text-xs font-mono space-y-1">
                <Terminal className="w-6 h-6 text-zinc-600 animate-pulse" strokeWidth={1.5} />
                <span>Select a contact session to monitor stream</span>
              </div>
            ) : (
              <AnimatePresence>
                {activeThread.map((msg) => {
                  const isUser = msg.role === 'user';
                  return (
                    <motion.div
                      key={msg.id || `${msg.wa_id}-${msg.created_at}-${Math.random()}`}
                      initial={{ opacity: 0, scale: 0.98, y: 4 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      transition={{ duration: 0.15 }}
                      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`flex items-start max-w-[85%] space-x-2 ${isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'}`}>
                        <div
                          className={`w-6 h-6 rounded flex items-center justify-center flex-shrink-0 text-[10px] ${
                            isUser
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                              : 'bg-zinc-800 text-zinc-300 border border-zinc-700'
                          }`}
                        >
                          {isUser ? <User className="w-3 h-3" strokeWidth={1.5} /> : <Bot className="w-3 h-3" strokeWidth={1.5} />}
                        </div>

                        <div
                          className={`p-2.5 rounded-lg text-[12px] leading-normal ${
                            isUser
                              ? 'bg-zinc-900 border border-emerald-500/30 text-emerald-100'
                              : 'bg-zinc-950 border border-zinc-800 text-zinc-200'
                          }`}
                        >
                          <div className="whitespace-pre-wrap font-sans">{msg.content}</div>
                          <div
                            className={`mt-1 text-[9px] font-mono ${
                              isUser ? 'text-emerald-300/60 text-right' : 'text-zinc-500'
                            }`}
                          >
                            {msg.created_at ? new Date(msg.created_at).toLocaleTimeString() : 'Just now'}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            )}

            {/* AI Generation Loading Indicator */}
            {sending && (
              <motion.div
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start items-center space-x-2"
              >
                <div className="w-6 h-6 rounded bg-zinc-800 text-emerald-400 border border-zinc-700 flex items-center justify-center">
                  <Bot className="w-3 h-3 animate-spin text-emerald-400" strokeWidth={1.5} />
                </div>
                <div className="p-2.5 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-400 text-xs font-mono flex items-center gap-2">
                  <Loader2 className="w-3 h-3 animate-spin text-emerald-400" />
                  <span>Astraventa AI is searching vector knowledge base & generating response...</span>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Test Input Form */}
          <form onSubmit={handleSendMessage} className="p-2.5 bg-zinc-950 border-t border-zinc-800 flex gap-2">
            <input
              type="text"
              value={testInput}
              onChange={(e) => setTestInput(e.target.value)}
              placeholder={activeWaId ? `Send test message as +${activeWaId}...` : 'Select contact session...'}
              disabled={!activeWaId || sending}
              className="flex-1 bg-zinc-900 border border-zinc-800 rounded-md px-3 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500/50 font-sans"
            />
            <button
              type="submit"
              disabled={!activeWaId || sending || !testInput.trim()}
              className="px-3.5 py-1.5 rounded-md bg-emerald-500 text-black font-semibold text-xs disabled:opacity-50 hover:bg-emerald-400 transition-colors flex items-center gap-1 font-mono"
            >
              <Send className="w-3 h-3" strokeWidth={1.5} />
              <span>{sending ? 'Sending...' : 'Test'}</span>
            </button>
          </form>
        </div>
      </div>
    </motion.div>
  );
}
