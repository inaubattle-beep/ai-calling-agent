'use client';

import React, { useEffect, useState } from 'react';
import { 
  PhoneCall, 
  PhoneIncoming, 
  Bot, 
  Activity, 
  Clock, 
  ArrowUpRight,
  Radio,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { Header } from '@/components/header';
import { CallStatusBadge } from '@/components/call-status-badge';
import { LanguageBadge } from '@/components/language-badge';
import { AudioVisualizer } from '@/components/audio-visualizer';
import { fetchCalls, fetchAgents, fetchEvents, Call, Agent, SystemEvent } from '@/lib/api';
import { formatDuration, formatTime } from '@/lib/utils';
import { useWebSocket } from '@/lib/websocket';

export default function DashboardPage() {
  const [activeCalls, setActiveCalls] = useState<Call[]>([]);
  const [allCalls, setAllCalls] = useState<Call[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [events, setEvents] = useState<SystemEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [callsData, agentsData, eventsData] = await Promise.all([
        fetchCalls(),
        fetchAgents(),
        fetchEvents(),
      ]);
      setAllCalls(callsData);
      setActiveCalls(callsData.filter((c) => c.status !== 'ENDED' && c.status !== 'ERROR'));
      setAgents(agentsData);
      setEvents(eventsData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, []);

  // Listen for real-time WebSocket events
  const { isConnected } = useWebSocket({
    url: '/ws/dashboard',
    onMessage: (msg) => {
      // Reload calls on state changes
      if (msg.event && (msg.event.startsWith('call.') || msg.event.startsWith('agent.'))) {
        loadData();
      }
    },
  });

  const receptionist = agents.find((a) => a.id === 'ai-receptionist-01');

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#090d16]">
      <Header wsConnected={isConnected} />

      <main className="p-6 space-y-6 max-w-7xl w-full mx-auto">
        {/* Metric Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Active Calls Card */}
          <div className="glass-panel p-5 rounded-2xl border border-border/80 relative overflow-hidden group">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider text-slate-400 uppercase">Active Calls</span>
              <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
                <PhoneCall className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight text-white font-mono">
                {activeCalls.length}
              </span>
              <span className="text-xs text-slate-400 font-medium">on PJSIP 7000</span>
            </div>
            <div className="mt-3 flex items-center gap-1.5 text-xs text-cyan-400">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
              <span>Voice Runtime Active</span>
            </div>
          </div>

          {/* Calls Today Card */}
          <div className="glass-panel p-5 rounded-2xl border border-border/80 relative overflow-hidden group">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider text-slate-400 uppercase">Total Calls</span>
              <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
                <PhoneIncoming className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight text-white font-mono">
                {allCalls.length}
              </span>
              <span className="text-xs text-slate-400 font-medium">processed</span>
            </div>
            <div className="mt-3 flex items-center gap-1.5 text-xs text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>100% Inbound Handled</span>
            </div>
          </div>

          {/* AI Receptionist Status Card */}
          <div className="glass-panel p-5 rounded-2xl border border-border/80 relative overflow-hidden group">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider text-slate-400 uppercase">AI Receptionist</span>
              <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400">
                <Bot className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight text-white">
                {receptionist?.status || 'ONLINE'}
              </span>
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
              <span className="text-slate-300 font-mono">STT: {receptionist?.stt_latency_ms || 140}ms</span>
              <span>•</span>
              <span className="text-slate-300 font-mono">LLM: {receptionist?.llm_latency_ms || 220}ms</span>
            </div>
          </div>

          {/* System Health Card */}
          <div className="glass-panel p-5 rounded-2xl border border-border/80 relative overflow-hidden group">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider text-slate-400 uppercase">PBX & Core</span>
              <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
                <Activity className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight text-emerald-400">HEALTHY</span>
            </div>
            <div className="mt-3 flex items-center gap-1.5 text-xs text-slate-400">
              <span>Bilingual (bn-BD / en-US)</span>
            </div>
          </div>
        </div>

        {/* Live Active Calls Section */}
        <div className="glass-panel rounded-2xl border border-border/80 overflow-hidden">
          <div className="p-5 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h2 className="text-sm font-semibold text-slate-200">Active Live Calls</h2>
              <span className="px-2 py-0.5 rounded-full text-xs font-mono font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                {activeCalls.length} Live
              </span>
            </div>
            <a
              href="/calls"
              className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium transition-colors"
            >
              <span>View all in Live Console</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          </div>

          {activeCalls.length === 0 ? (
            <div className="p-12 text-center text-slate-400">
              <div className="w-12 h-12 rounded-2xl bg-surfaceLight/50 flex items-center justify-center mx-auto mb-3 text-slate-500">
                <Radio className="w-6 h-6 opacity-40" />
              </div>
              <p className="text-sm font-medium text-slate-300">No calls active right now</p>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Click &quot;Simulate Call (Bangla)&quot; in the header above to launch an automated conversation test.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {activeCalls.map((call) => (
                <div
                  key={call.id}
                  className="p-4 flex items-center justify-between hover:bg-surfaceLight/30 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                      <PhoneCall className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-mono font-bold text-white">{call.phone_number}</span>
                        <span className="text-xs font-mono text-slate-500">#{call.id}</span>
                        <LanguageBadge language={call.language} />
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                        <span>Agent: <strong className="text-slate-200">AI Receptionist</strong></span>
                        <span>•</span>
                        <span>Direction: <span className="font-semibold text-slate-300">{call.direction}</span></span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <AudioVisualizer isActive={call.status === 'SPEAKING' || call.status === 'LISTENING'} />
                    <CallStatusBadge status={call.status} />
                    <a
                      href={`/calls/${call.id}`}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-surfaceLight hover:bg-cyan-600/20 hover:text-cyan-300 border border-border hover:border-cyan-500/30 transition-all text-slate-300"
                    >
                      Open Detail
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Live System Events Stream */}
        <div className="glass-panel rounded-2xl border border-border/80 overflow-hidden">
          <div className="p-5 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-semibold text-slate-200">Real-Time Event Stream</h2>
            </div>
            <span className="text-xs text-slate-500 font-mono">WebSocket Telemetry</span>
          </div>

          <div className="p-4 max-h-72 overflow-y-auto font-mono text-xs space-y-2">
            {events.length === 0 ? (
              <p className="text-slate-500 text-center py-4">Waiting for event signals...</p>
            ) : (
              events.slice(0, 15).map((ev, i) => (
                <div key={ev.id || i} className="flex items-center gap-3 text-slate-400 py-1 border-b border-border/40 last:border-0">
                  <span className="text-slate-500 select-none">{formatTime(ev.timestamp)}</span>
                  <span className="text-cyan-400 font-semibold">{ev.event}</span>
                  {ev.call_id && (
                    <span className="text-slate-300 bg-surfaceLight px-1.5 py-0.5 rounded text-[10px]">
                      {ev.call_id}
                    </span>
                  )}
                  <span className="text-slate-400 truncate">
                    {ev.data?.text || ev.data?.status || JSON.stringify(ev.data)}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
