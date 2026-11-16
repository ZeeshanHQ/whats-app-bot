'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PhoneCall,
  PhoneIncoming,
  PhoneOutgoing,
  PhoneForwarded,
  Clock,
  User,
  Bot,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  ChevronRight,
  MessageSquare,
  ShieldCheck,
  Zap,
  Plus,
  X,
  Loader2,
  Sparkles,
  ArrowRight,
  Radio,
} from 'lucide-react';

interface CallTranscriptTurn {
  speaker: 'caller' | 'agent';
  text: string;
  time?: string;
}

interface CallSession {
  id: string;
  room_name: string;
  session_type: string;
  destination_phone: string;
  status: string;
  duration_seconds: number;
  transcript: CallTranscriptTurn[] | any;
  created_at: string;
}

const CAMPAIGN_PRESETS = [
  {
    id: 'lead_discovery',
    name: 'B2B Lead Discovery & Qualification',
    prompt:
      "Hi there! This is Sophia from Astraventa. I'm following up regarding your interest in AI automation solutions. Did I catch you at an okay time for a 2-minute chat?",
  },
  {
    id: 'meeting_confirmation',
    name: 'Meeting & Demo Confirmation',
    prompt:
      "Hi! This is Sophia calling from Astraventa to confirm your upcoming scheduled consultation with Zeeshan. Are you still good for that time?",
  },
  {
    id: 'customer_followup',
    name: 'Customer Follow-up & Feedback',
    prompt:
      "Hello! Sophia here from Astraventa. Reaching out to see how everything is performing with your recent setup and whether you need any extra support today.",
  },
  {
    id: 'custom_pitch',
    name: 'Custom Outbound Script',
    prompt:
      "Hi there! This is Sophia from Astraventa reaching out regarding our automated voice and WhatsApp agents.",
  },
];

export default function VoiceCallsPage() {
  const [sessions, setSessions] = useState<CallSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [directionFilter, setDirectionFilter] = useState<'all' | 'inbound' | 'outbound'>('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedCall, setSelectedCall] = useState<CallSession | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>('');

  // Outbound Call Modal State
  const [showDialerModal, setShowDialerModal] = useState(false);
  const [dialNumber, setDialNumber] = useState('');
  const [selectedCampaign, setSelectedCampaign] = useState(CAMPAIGN_PRESETS[0].id);
  const [customPrompt, setCustomPrompt] = useState(CAMPAIGN_PRESETS[0].prompt);
  const [dialing, setDialing] = useState(false);
  const [dialSuccess, setDialSuccess] = useState<any>(null);
  const [dialError, setDialError] = useState<string | null>(null);

  const fetchCalls = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.engine.astraventa.com';
      const res = await fetch(`${apiUrl}/api/kb/call-sessions`);
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
        setLastRefreshed(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
      }
    } catch (err) {
      console.error('Error fetching call sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalls();
    if (!autoRefresh) return;
    const interval = setInterval(fetchCalls, 5000); // 5s live polling
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleCampaignChange = (id: string) => {
    setSelectedCampaign(id);
    const preset = CAMPAIGN_PRESETS.find((p) => p.id === id);
    if (preset) {
      setCustomPrompt(preset.prompt);
    }
  };

  const handleInitiateCall = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dialNumber.trim() || dialing) return;

    setDialing(true);
    setDialError(null);
    setDialSuccess(null);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.engine.astraventa.com';
    try {
      const res = await fetch(`${apiUrl}/api/calls/outbound`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to_number: dialNumber.trim(),
          campaign_name: CAMPAIGN_PRESETS.find((p) => p.id === selectedCampaign)?.name || 'Direct Outbound',
          custom_prompt: customPrompt.trim(),
        }),
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.detail || data.error || 'Failed to initiate outbound call.');
      }

      setDialSuccess(data);
      await fetchCalls();
    } catch (err: any) {
      console.error('Outbound call error:', err);
      setDialError(err.message || 'Error initiating outbound call.');
    } finally {
      setDialing(false);
    }
  };

  const filteredSessions = sessions.filter((session) => {
    const phone = session.destination_phone || '';
    const room = session.room_name || '';
    const matchesSearch =
      searchTerm === '' ||
      phone.toLowerCase().includes(searchTerm.toLowerCase()) ||
      room.toLowerCase().includes(searchTerm.toLowerCase());

    const isOutbound =
      session.session_type?.includes('outbound') || session.room_name?.toLowerCase().includes('outbound');
    const matchesDirection =
      directionFilter === 'all' ||
      (directionFilter === 'outbound' && isOutbound) ||
      (directionFilter === 'inbound' && !isOutbound);

    const matchesStatus = statusFilter === 'all' || session.status === statusFilter;

    return matchesSearch && matchesDirection && matchesStatus;
  });

  // KPI calculations
  const totalCalls = sessions.length;
  const outboundCalls = sessions.filter(
    (s) => s.session_type?.includes('outbound') || s.room_name?.toLowerCase().includes('outbound')
  ).length;
  const inboundCalls = totalCalls - outboundCalls;
  const transferredCalls = sessions.filter((s) => s.status === 'transferred').length;
  const avgDuration =
    totalCalls > 0
      ? Math.round(sessions.reduce((acc, s) => acc + (s.duration_seconds || 0), 0) / totalCalls)
      : 0;

  const formatDuration = (seconds: number) => {
    if (!seconds) return '0s';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  };

  return (
    <div className="space-y-5">
      {/* ── Top Header Bar ─────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-zinc-800/80 pb-3">
        <div>
          <div className="flex items-center space-x-2.5 mb-0.5">
            <h1 className="text-base font-bold tracking-tight text-white font-mono flex items-center gap-2">
              VOICE CALLS & OUTBOUND DIALER
            </h1>
            <span className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono font-medium tracking-wide uppercase">
              SIP Active
            </span>
          </div>
          <p className="text-[11px] text-zinc-400 font-sans">
            Inbound & Outbound AI voice telemetry for line{' '}
            <span className="text-emerald-300 font-mono font-semibold">+1 (925) 504-0101</span> with Deepgram Nova STT & Groq LPU turnaround.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {/* Outbound Call Trigger Button */}
          <button
            onClick={() => {
              setDialError(null);
              setDialSuccess(null);
              setShowDialerModal(true);
            }}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-500 text-black hover:bg-cyan-400 transition-all font-mono font-bold text-xs shadow-sm hover:scale-[1.02]"
          >
            <PhoneOutgoing className="w-3.5 h-3.5" />
            <span>Make Outbound Call</span>
          </button>

          {/* Auto Refresh Toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all flex items-center space-x-1.5 border ${
              autoRefresh
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                : 'bg-zinc-900 border-zinc-800 text-zinc-400'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${autoRefresh ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-600'}`} />
            <span className="text-[11px]">Sync (5s)</span>
          </button>

          <button
            onClick={fetchCalls}
            className="p-1.5 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-300 transition-colors"
            title="Refresh now"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* ── KPI Stats Grid ─────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-[#0b101b] border border-zinc-800/80 rounded-xl p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-zinc-400 mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider">Total Calls</span>
            <PhoneCall className="w-3.5 h-3.5 text-zinc-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">{totalCalls}</div>
          <div className="text-[10px] text-zinc-500 font-mono mt-0.5">Inbound & Outbound combined</div>
        </div>

        <div className="bg-[#0b101b] border border-zinc-800/80 rounded-xl p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-zinc-400 mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider">Inbound Calls</span>
            <PhoneIncoming className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-300">{inboundCalls}</div>
          <div className="text-[10px] text-emerald-400/80 font-mono mt-0.5">To +1 (925) 504-0101</div>
        </div>

        <div className="bg-[#0b101b] border border-zinc-800/80 rounded-xl p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-zinc-400 mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider">Outbound Calls</span>
            <PhoneOutgoing className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-cyan-300">{outboundCalls}</div>
          <div className="text-[10px] text-cyan-400/80 font-mono mt-0.5">AI Outreach & Discovery</div>
        </div>

        <div className="bg-[#0b101b] border border-zinc-800/80 rounded-xl p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-zinc-400 mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider">Avg Talk Time</span>
            <Clock className="w-3.5 h-3.5 text-violet-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">{formatDuration(avgDuration)}</div>
          <div className="text-[10px] text-zinc-500 font-mono mt-0.5">Sync: {lastRefreshed || 'Live'}</div>
        </div>
      </div>

      {/* ── Search & Filter Control Bar ────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2.5 bg-[#0b101b] border border-zinc-800/80 p-2.5 rounded-xl">
        <div className="relative w-full sm:w-72">
          <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search phone number or call ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-cyan-500 font-mono"
          />
        </div>

        {/* Direction Filter Tabs */}
        <div className="flex items-center space-x-1 bg-zinc-950 p-0.5 rounded-lg border border-zinc-800 text-[11px] font-mono">
          <button
            onClick={() => setDirectionFilter('all')}
            className={`px-2.5 py-1 rounded transition-colors ${
              directionFilter === 'all' ? 'bg-zinc-800 text-white font-medium' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            All Calls
          </button>
          <button
            onClick={() => setDirectionFilter('inbound')}
            className={`px-2.5 py-1 rounded transition-colors flex items-center gap-1 ${
              directionFilter === 'inbound'
                ? 'bg-emerald-500/20 text-emerald-300 font-medium'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <PhoneIncoming className="w-3 h-3 text-emerald-400" />
            <span>Inbound</span>
          </button>
          <button
            onClick={() => setDirectionFilter('outbound')}
            className={`px-2.5 py-1 rounded transition-colors flex items-center gap-1 ${
              directionFilter === 'outbound'
                ? 'bg-cyan-500/20 text-cyan-300 font-medium'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <PhoneOutgoing className="w-3 h-3 text-cyan-400" />
            <span>Outbound</span>
          </button>
        </div>
      </div>

      {/* ── Main Call Logs Table ────────────────────────────────────── */}
      <div className="bg-[#0b101b] border border-zinc-800/80 rounded-xl overflow-hidden shadow-sm">
        {filteredSessions.length === 0 ? (
          <div className="py-16 text-center text-zinc-500 text-xs font-mono space-y-2">
            <Radio className="w-8 h-8 mx-auto text-zinc-600 animate-pulse" />
            <div>No matching voice call sessions recorded.</div>
            <p className="text-[11px] text-zinc-600">
              Inbound calls to +1 (925) 504-0101 and outbound AI calls will display here in real-time.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="text-zinc-500 border-b border-zinc-800/80 bg-zinc-950/60 text-[10px] uppercase tracking-wider">
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Party Phone</th>
                  <th className="py-2.5 px-3">Call ID</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Duration</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/40">
                {filteredSessions.map((session) => {
                  const isOutbound =
                    session.session_type?.includes('outbound') ||
                    session.room_name?.toLowerCase().includes('outbound');

                  return (
                    <tr key={session.id} className="hover:bg-zinc-900/40 transition-colors">
                      {/* Direction Pill */}
                      <td className="py-3 px-3">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${
                            isOutbound
                              ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
                              : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          }`}
                        >
                          {isOutbound ? (
                            <>
                              <PhoneOutgoing className="w-2.5 h-2.5" /> OUTBOUND
                            </>
                          ) : (
                            <>
                              <PhoneIncoming className="w-2.5 h-2.5" /> INBOUND
                            </>
                          )}
                        </span>
                      </td>

                      {/* Phone Number */}
                      <td className="py-3 px-3 text-white font-semibold">
                        {session.destination_phone || 'Private Number'}
                      </td>

                      {/* Room / Call ID */}
                      <td className="py-3 px-3 text-zinc-400">{session.room_name}</td>

                      {/* Status */}
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-medium border ${
                            session.status === 'completed'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : session.status === 'transferred'
                              ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                              : 'bg-zinc-800 text-zinc-300 border-zinc-700'
                          }`}
                        >
                          {session.status}
                        </span>
                      </td>

                      {/* Duration */}
                      <td className="py-3 px-3 text-zinc-300">{formatDuration(session.duration_seconds)}</td>

                      {/* Created At */}
                      <td className="py-3 px-3 text-zinc-500 text-[11px]">
                        {session.created_at ? new Date(session.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : 'Recent'}
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-3 text-right space-x-2">
                        <button
                          onClick={() => setSelectedCall(session)}
                          className="px-2.5 py-1 rounded bg-zinc-900 border border-zinc-700 hover:border-zinc-500 text-zinc-200 text-[11px] font-mono transition-colors"
                        >
                          Transcript
                        </button>

                        <button
                          onClick={() => {
                            setDialNumber(session.destination_phone || '');
                            setShowDialerModal(true);
                          }}
                          className="px-2 py-1 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20 text-[11px] font-mono transition-colors"
                          title="Dial this number again"
                        >
                          Call Back
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Outbound Dialer Modal ──────────────────────────────────── */}
      {showDialerModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#0c1019] border border-zinc-800 rounded-xl p-5 w-full max-w-lg shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
              <div className="flex items-center space-x-2">
                <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  <PhoneOutgoing className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-white font-mono">INITIATE OUTBOUND AI CALL</h2>
                  <p className="text-[10px] text-zinc-400">Powered by Telnyx Voice + Deepgram + Groq</p>
                </div>
              </div>

              <button
                onClick={() => setShowDialerModal(false)}
                className="text-zinc-500 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {dialError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{dialError}</span>
              </div>
            )}

            {dialSuccess && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-mono space-y-1">
                <div className="flex items-center gap-2 font-bold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Call Dialed Successfully!</span>
                </div>
                <div className="text-[11px] text-zinc-400">
                  Dialing <span className="text-white font-semibold">{dialSuccess.to}</span> from{' '}
                  <span className="text-white">{dialSuccess.from}</span>. Media stream connecting on answer.
                </div>
              </div>
            )}

            <form onSubmit={handleInitiateCall} className="space-y-3.5">
              {/* Phone Number Input */}
              <div>
                <label className="block text-[11px] font-mono text-zinc-300 mb-1">
                  Recipient Phone Number (with Country Code)
                </label>
                <div className="relative">
                  <PhoneCall className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    placeholder="+923001234567 or +19255040101"
                    value={dialNumber}
                    onChange={(e) => setDialNumber(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-700 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
                <p className="text-[10px] text-zinc-500 font-mono mt-1">
                  Include international format prefix (+92, +1, +44, etc.).
                </p>
              </div>

              {/* Campaign Preset Selector */}
              <div>
                <label className="block text-[11px] font-mono text-zinc-300 mb-1">
                  Campaign / Scenario Objective
                </label>
                <select
                  value={selectedCampaign}
                  onChange={(e) => handleCampaignChange(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                >
                  {CAMPAIGN_PRESETS.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Opening Pitch / Prompt */}
              <div>
                <label className="block text-[11px] font-mono text-zinc-300 mb-1 flex items-center justify-between">
                  <span>AI Opening Pitch (Spoken upon Answer)</span>
                  <span className="text-[10px] text-zinc-500">Customizable</span>
                </label>
                <textarea
                  rows={3}
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-lg p-2.5 text-xs text-zinc-200 focus:outline-none focus:border-cyan-500 font-sans resize-none"
                />
              </div>

              {/* Submit Buttons */}
              <div className="flex gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setShowDialerModal(false)}
                  className="flex-1 py-2 rounded-lg border border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-900 transition-colors text-xs font-mono"
                >
                  Close
                </button>

                <button
                  type="submit"
                  disabled={dialing || !dialNumber.trim()}
                  className="flex-1 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-xs font-mono transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center space-x-1.5"
                >
                  {dialing ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Dialing via Telnyx...</span>
                    </>
                  ) : (
                    <>
                      <PhoneOutgoing className="w-3.5 h-3.5" />
                      <span>Dial Call Now</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Call Transcript Drawer ─────────────────────────────────── */}
      {selectedCall && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-sm">
          <div className="bg-[#0b101b] border-l border-zinc-800 w-full max-w-xl h-full flex flex-col shadow-2xl p-4 font-mono">
            {/* Drawer Header */}
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3 mb-3">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-sm font-bold text-white">Call Conversation Transcript</h3>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-300">
                    {selectedCall.destination_phone}
                  </span>
                </div>
                <p className="text-[10px] text-zinc-500 mt-0.5">
                  Duration: {formatDuration(selectedCall.duration_seconds)} | Status: {selectedCall.status}
                </p>
              </div>

              <button
                onClick={() => setSelectedCall(null)}
                className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Transcript Stream */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-1 font-sans">
              {!selectedCall.transcript || selectedCall.transcript.length === 0 ? (
                <div className="py-12 text-center text-zinc-500 text-xs font-mono">
                  No transcript records captured for this session.
                </div>
              ) : (
                selectedCall.transcript.map((turn: any, index: number) => {
                  const isAgent = turn.speaker === 'agent';
                  return (
                    <div key={index} className={`flex ${isAgent ? 'justify-end' : 'justify-start'}`}>
                      <div className={`flex items-start max-w-[85%] space-x-2 ${isAgent ? 'flex-row-reverse space-x-reverse' : 'flex-row'}`}>
                        <div
                          className={`w-6 h-6 rounded flex items-center justify-center flex-shrink-0 text-[10px] ${
                            isAgent
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                              : 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                          }`}
                        >
                          {isAgent ? <Bot className="w-3 h-3" /> : <User className="w-3 h-3" />}
                        </div>

                        <div
                          className={`p-2.5 rounded-lg text-[12px] leading-relaxed ${
                            isAgent
                              ? 'bg-zinc-950 border border-zinc-800 text-zinc-200'
                              : 'bg-zinc-900 border border-zinc-700/60 text-white'
                          }`}
                        >
                          <div className="whitespace-pre-wrap">{turn.text}</div>
                          {turn.time && (
                            <div className="text-[9px] font-mono text-zinc-500 mt-1 text-right">
                              {turn.time}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
