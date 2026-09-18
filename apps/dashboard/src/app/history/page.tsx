'use client';

import React, { useEffect, useState } from 'react';
import { History, Search, Filter, PhoneIncoming, PhoneOutgoing, MessageSquare, ArrowRight } from 'lucide-react';
import { Header } from '@/components/header';
import { CallStatusBadge } from '@/components/call-status-badge';
import { LanguageBadge } from '@/components/language-badge';
import { fetchCalls, fetchCallDetail, Call, CallDetail } from '@/lib/api';
import { formatDuration, formatTime } from '@/lib/utils';
import { useWebSocket } from '@/lib/websocket';

export default function HistoryPage() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [search, setSearch] = useState('');
  const [filterLang, setFilterLang] = useState('ALL');
  const [selectedCall, setSelectedCall] = useState<CallDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const loadHistory = async () => {
    try {
      const data = await fetchCalls();
      setCalls(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const { isConnected } = useWebSocket({
    url: '/ws/dashboard',
    onMessage: (msg) => {
      if (msg.event === 'call.ended') {
        loadHistory();
      }
    },
  });

  const handleInspectTranscript = async (callId: string) => {
    try {
      const detail = await fetchCallDetail(callId);
      setSelectedCall(detail);
    } catch (e) {
      console.error(e);
    }
  };

  const filteredCalls = calls.filter((c) => {
    const matchPhone = c.phone_number.includes(search) || c.id.includes(search);
    const matchLang = filterLang === 'ALL' || c.language.startsWith(filterLang);
    return matchPhone && matchLang;
  });

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#090d16]">
      <Header wsConnected={isConnected} />

      <main className="p-6 space-y-6 max-w-7xl w-full mx-auto">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Call History & Transcripts</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Archived telephone interactions with full conversation records
          </p>
        </div>

        {/* Filter Toolbar */}
        <div className="glass-panel p-4 rounded-xl border border-border flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1 min-w-[260px]">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search phone number or call ID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-background border border-border text-xs text-white focus:outline-none focus:border-cyan-500"
              />
            </div>

            <select
              value={filterLang}
              onChange={(e) => setFilterLang(e.target.value)}
              className="px-3 py-1.5 rounded-lg bg-background border border-border text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Languages</option>
              <option value="bn">Bangla (bn-BD)</option>
              <option value="en">English (en-US)</option>
              <option value="mixed">Banglish (Mixed)</option>
            </select>
          </div>

          <span className="text-xs text-slate-400 font-mono">{filteredCalls.length} calls logged</span>
        </div>

        {/* Calls Table */}
        <div className="glass-panel rounded-2xl border border-border/80 overflow-hidden">
          {filteredCalls.length === 0 ? (
            <div className="p-12 text-center text-slate-400 text-xs">No calls match your search criteria.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#0e1424] text-slate-400 uppercase tracking-wider font-semibold border-b border-border text-[11px]">
                  <tr>
                    <th className="p-4">Time</th>
                    <th className="p-4">Phone Number</th>
                    <th className="p-4">Direction</th>
                    <th className="p-4">Language</th>
                    <th className="p-4">Duration</th>
                    <th className="p-4">Final Status</th>
                    <th className="p-4 text-right">Transcript</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredCalls.map((call) => (
                    <tr key={call.id} className="hover:bg-surfaceLight/30 transition-colors">
                      <td className="p-4 font-mono text-slate-400">{formatTime(call.started_at)}</td>
                      <td className="p-4 font-mono font-bold text-white">{call.phone_number}</td>
                      <td className="p-4 text-slate-300 font-semibold">{call.direction}</td>
                      <td className="p-4">
                        <LanguageBadge language={call.language} />
                      </td>
                      <td className="p-4 font-mono text-slate-300">{formatDuration(call.duration)}</td>
                      <td className="p-4">
                        <CallStatusBadge status={call.status} />
                      </td>
                      <td className="p-4 text-right">
                        <button
                          onClick={() => handleInspectTranscript(call.id)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-surfaceLight hover:bg-cyan-600/20 text-slate-300 hover:text-cyan-300 border border-border transition-all"
                        >
                          <MessageSquare className="w-3.5 h-3.5" />
                          <span>View Transcript</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* Transcript Modal */}
      {selectedCall && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#101626] border border-border rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-5 border-b border-border flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>Call Transcript #{selectedCall.id}</span>
                  <LanguageBadge language={selectedCall.language} />
                </h3>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Caller: {selectedCall.phone_number} • Duration: {formatDuration(selectedCall.duration)}
                </p>
              </div>
              <button
                onClick={() => setSelectedCall(null)}
                className="p-1.5 rounded-lg hover:bg-surface text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto flex-1 space-y-3">
              {selectedCall.transcripts.length === 0 ? (
                <div className="text-center py-12 text-slate-500 text-xs">No speech transcribed for this call.</div>
              ) : (
                selectedCall.transcripts.map((msg) => {
                  const isCustomer = msg.speaker === 'customer';
                  return (
                    <div
                      key={msg.id}
                      className={`p-3.5 rounded-xl text-xs leading-relaxed ${
                        isCustomer
                          ? 'bg-[#151d30] border border-border text-slate-200 ml-0 mr-12'
                          : 'bg-gradient-to-tr from-cyan-950/60 to-emerald-950/60 border border-cyan-800/40 text-emerald-100 ml-12 mr-0'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                        <span className="font-bold">{isCustomer ? 'CUSTOMER' : 'AI RECEPTIONIST'}</span>
                        <span>{formatTime(msg.timestamp)}</span>
                      </div>
                      <p>{msg.text}</p>
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
