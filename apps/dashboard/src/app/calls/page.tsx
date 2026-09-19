'use client';

import React, { useEffect, useState } from 'react';
import { PhoneCall, Plus, RefreshCw, Radio, PhoneOff, ArrowRight } from 'lucide-react';
import { Header } from '@/components/header';
import { CallStatusBadge } from '@/components/call-status-badge';
import { LanguageBadge } from '@/components/language-badge';
import { fetchCalls, createCall, fetchSettings, Call, AppSettings } from '@/lib/api';
import { formatDuration } from '@/lib/utils';
import { useWebSocket } from '@/lib/websocket';

export default function CallsPage() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewCallModal, setShowNewCallModal] = useState(false);
  const [newPhoneNumber, setNewPhoneNumber] = useState('+8801712345678');
  const [newLanguage, setNewLanguage] = useState('bn-BD');
  const [settings, setSettings] = useState<AppSettings | null>(null);

  const loadCalls = async () => {
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
    loadCalls();
    fetchSettings().then((saved) => {
      if (saved) {
        setSettings(saved);
        setNewPhoneNumber(saved.default_phone_number);
        setNewLanguage(saved.default_language);
      }
    });
  }, []);

  const { isConnected } = useWebSocket({
    url: '/ws/dashboard',
    onMessage: (msg) => {
      if (msg.event && (msg.event.startsWith('call.') || msg.event.startsWith('agent.'))) {
        loadCalls();
      }
    },
  });

  const handleStartCall = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createCall({
        phone_number: newPhoneNumber,
        direction: 'OUTBOUND',
        language: newLanguage,
        agent_id: settings?.default_agent_id,
      });
      setShowNewCallModal(false);
      loadCalls();
    } catch (e) {
      console.error(e);
    }
  };

  const activeCalls = calls.filter((c) => c.status !== 'ENDED' && c.status !== 'ERROR');

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#090d16]">
      <Header wsConnected={isConnected} />

      <main className="p-6 space-y-6 max-w-7xl w-full mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Live Calls Management</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Monitor active phone sessions and SIP Extension 7000 channels
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadCalls}
              className="p-2 rounded-lg bg-surface hover:bg-surfaceLight text-slate-300 border border-border transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>

            <button
              onClick={() => setShowNewCallModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-600/20 transition-all"
            >
              <Plus className="w-4 h-4" />
              <span>Make Outbound Call</span>
            </button>
          </div>
        </div>

        {/* Live Calls Table / Cards */}
        <div className="glass-panel rounded-2xl border border-border/80 overflow-hidden">
          <div className="p-4 border-b border-border bg-surface/40 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-semibold text-slate-200">Active Real-Time Calls ({activeCalls.length})</span>
            </div>
          </div>

          {activeCalls.length === 0 ? (
            <div className="p-12 text-center text-slate-400">
              <p className="text-sm font-medium text-slate-300">No active calls right now</p>
              <p className="text-xs text-slate-500 mt-1">
                Start an outbound call or simulate an inbound call from the header.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#0e1424] text-slate-400 uppercase tracking-wider font-semibold border-b border-border text-[11px]">
                  <tr>
                    <th className="p-4">Call ID</th>
                    <th className="p-4">Phone Number</th>
                    <th className="p-4">Direction</th>
                    <th className="p-4">Language</th>
                    <th className="p-4">Agent</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Duration</th>
                    <th className="p-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {activeCalls.map((call) => (
                    <tr key={call.id} className="hover:bg-surfaceLight/30 transition-colors">
                      <td className="p-4 font-mono font-medium text-slate-400">#{call.id}</td>
                      <td className="p-4 font-mono font-bold text-white">{call.phone_number}</td>
                      <td className="p-4 font-semibold text-slate-300">{call.direction}</td>
                      <td className="p-4">
                        <LanguageBadge language={call.language} />
                      </td>
                      <td className="p-4 text-slate-200">AI Receptionist</td>
                      <td className="p-4">
                        <CallStatusBadge status={call.status} />
                      </td>
                      <td className="p-4 font-mono text-slate-300">{formatDuration(call.duration)}</td>
                      <td className="p-4 text-right">
                        <a
                          href={`/calls/${call.id}`}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg font-medium text-xs bg-cyan-600/20 text-cyan-300 hover:bg-cyan-600/30 border border-cyan-500/30 transition-all"
                        >
                          <span>Open Console</span>
                          <ArrowRight className="w-3 h-3" />
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* Outbound Call Modal */}
      {showNewCallModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#101626] border border-border rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-base font-bold text-white mb-1">Make Outbound Call</h3>
            <p className="text-xs text-slate-400 mb-4">
              AI Receptionist will originate a call via Asterisk PJSIP / Mock Telephony
            </p>

            <form onSubmit={handleStartCall} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Destination Phone Number</label>
                <input
                  type="text"
                  value={newPhoneNumber}
                  onChange={(e) => setNewPhoneNumber(e.target.value)}
                  placeholder="+8801XXXXXXXXX"
                  className="w-full px-3 py-2 rounded-lg bg-background border border-border text-white text-xs font-mono focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Conversation Language</label>
                <select
                  value={newLanguage}
                  onChange={(e) => setNewLanguage(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-background border border-border text-white text-xs focus:outline-none focus:border-cyan-500"
                >
                  <option value="bn-BD">Bangla (bn-BD)</option>
                  <option value="en-US">English (en-US)</option>
                  <option value="mixed">Banglish (Mixed)</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewCallModal(false)}
                  className="px-3 py-1.5 text-xs text-slate-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white transition-all shadow-md shadow-cyan-600/20"
                >
                  Dial Number
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
