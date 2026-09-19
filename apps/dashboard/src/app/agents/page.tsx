'use client';

import React, { useEffect, useState } from 'react';
import { Bot, Radio, Cpu, Clock, CheckCircle2, Zap, ShieldCheck } from 'lucide-react';
import { Header } from '@/components/header';
import { fetchAgents, Agent } from '@/lib/api';
import { useWebSocket } from '@/lib/websocket';

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  const loadAgents = async () => {
    try {
      const data = await fetchAgents();
      setAgents(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
    const interval = setInterval(loadAgents, 3000);
    return () => clearInterval(interval);
  }, []);

  const { isConnected } = useWebSocket({
    url: '/ws/dashboard',
    onMessage: () => loadAgents(),
  });

  const agent = agents[0] || {
    id: 'ai-receptionist-01',
    name: 'AI Receptionist',
    status: 'ONLINE',
    model: 'bilingual-receptionist-v1',
    primary_language: 'bn-BD',
    stt_latency_ms: 140,
    llm_latency_ms: 220,
    tts_latency_ms: 180,
    description: 'AI voice agent',
    greeting: '',
    system_prompt: '',
    supported_languages: ['bn-BD', 'en-US', 'mixed'],
    enabled: true,
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#090d16]">
      <Header wsConnected={isConnected} />

      <main className="p-6 space-y-6 max-w-5xl w-full mx-auto">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">AI Voice Agents</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Voice Runtime intelligence models and latency metrics
          </p>
        </div>

        {/* Agent Card */}
        <div className="glass-panel rounded-2xl border border-border/80 p-6 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-border">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-600 to-emerald-600 flex items-center justify-center text-white shadow-xl shadow-cyan-600/20">
                <Bot className="w-7 h-7" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-white">{agent.name}</h2>
                  <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    {agent.status}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Extension 7000 • Inbound / Outbound Call Handler
                </p>
              </div>
            </div>

            {agent.current_call_id && (
              <a
                href={`/calls/${agent.current_call_id}`}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-600/20 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-600/30 transition-all font-mono"
              >
                Handling Active Call: #{agent.current_call_id}
              </a>
            )}
          </div>

          {/* Latency Breakdown Grid */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
              Real-Time Latency Breakdown
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-[#0b101e] p-4 rounded-xl border border-border">
                <div className="text-xs text-slate-400 mb-1">STT Latency (Whisper)</div>
                <div className="text-2xl font-bold font-mono text-cyan-400">{agent.stt_latency_ms} ms</div>
                <div className="text-[11px] text-slate-500 mt-1">Streaming VAD detection</div>
              </div>

              <div className="bg-[#0b101e] p-4 rounded-xl border border-border">
                <div className="text-xs text-slate-400 mb-1">LLM Response Latency</div>
                <div className="text-2xl font-bold font-mono text-purple-400">{agent.llm_latency_ms} ms</div>
                <div className="text-[11px] text-slate-500 mt-1">1-3 sentence conciseness</div>
              </div>

              <div className="bg-[#0b101e] p-4 rounded-xl border border-border">
                <div className="text-xs text-slate-400 mb-1">TTS First-Byte Latency</div>
                <div className="text-2xl font-bold font-mono text-emerald-400">{agent.tts_latency_ms} ms</div>
                <div className="text-[11px] text-slate-500 mt-1">Streaming PCM synthesize</div>
              </div>
            </div>
          </div>

          {/* Agent Configuration Details */}
          <div className="pt-4 border-t border-border grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Supported Dialects & Code-Switching
              </h4>
              <ul className="text-xs text-slate-300 space-y-2">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span><strong>Bangla (bn-BD):</strong> Native understanding and respectful Bengali phrasing.</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span><strong>English (en-US):</strong> Fluent conversational support.</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span><strong>Banglish:</strong> Natural code-switching tolerance.</span>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Telephone Safety Rules
              </h4>
              <ul className="text-xs text-slate-300 space-y-2">
                <li className="flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  <span>Instant Barge-In (interruption aborts TTS).</span>
                </li>
                <li className="flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  <span>Zero Markdown syntax (no asterisks or URLs in voice).</span>
                </li>
                <li className="flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  <span>No OS shell access permitted for LLM.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
