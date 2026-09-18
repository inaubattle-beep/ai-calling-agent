'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  PhoneOff, 
  Zap, 
  ArrowLeft, 
  User, 
  Bot, 
  Clock, 
  Radio, 
  Activity, 
  Volume2
} from 'lucide-react';
import { Header } from '@/components/header';
import { CallStatusBadge } from '@/components/call-status-badge';
import { LanguageBadge } from '@/components/language-badge';
import { AudioVisualizer } from '@/components/audio-visualizer';
import { fetchCallDetail, hangupCall, interruptCall, CallDetail, TranscriptMessage } from '@/lib/api';
import { formatDuration, formatTime } from '@/lib/utils';
import { useWebSocket } from '@/lib/websocket';

export default function CallDetailPage() {
  const params = useParams();
  const router = useRouter();
  const callId = params?.id as string;

  const [call, setCall] = useState<CallDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const transcriptBottomRef = useRef<HTMLDivElement>(null);

  const loadDetail = async () => {
    if (!callId) return;
    try {
      const data = await fetchCallDetail(callId);
      setCall(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetail();
    const interval = setInterval(loadDetail, 2500);
    return () => clearInterval(interval);
  }, [callId]);

  // Scroll to bottom of transcripts on new messages
  useEffect(() => {
    transcriptBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [call?.transcripts]);

  // Dedicated Call WebSocket channel
  const { isConnected } = useWebSocket({
    url: `/ws/calls/${callId}`,
    onMessage: (msg) => {
      if (msg.event === 'transcript.created' || msg.event === 'call.state_changed' || msg.event === 'agent.interrupted') {
        loadDetail();
      }
    },
  });

  const handleHangup = async () => {
    if (!callId) return;
    try {
      await hangupCall(callId);
      loadDetail();
    } catch (e) {
      console.error(e);
    }
  };

  const handleInterrupt = async () => {
    if (!callId) return;
    try {
      await interruptCall(callId);
      loadDetail();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading && !call) {
    return (
      <div className="flex-1 flex flex-col min-h-screen bg-[#090d16]">
        <Header wsConnected={isConnected} />
        <div className="p-12 text-center text-slate-400">Loading call details...</div>
      </div>
    );
  }

  if (!call) {
    return (
      <div className="flex-1 flex flex-col min-h-screen bg-[#090d16]">
        <Header wsConnected={isConnected} />
        <div className="p-12 text-center text-slate-400">
          <p className="text-base font-semibold text-white">Call not found</p>
          <button
            onClick={() => router.push('/calls')}
            className="mt-4 px-4 py-2 rounded-lg bg-surface text-xs text-cyan-400 hover:text-cyan-300"
          >
            Back to Calls
          </button>
        </div>
      </div>
    );
  }

  const isLive = call.status !== 'ENDED' && call.status !== 'ERROR';

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#090d16]">
      <Header wsConnected={isConnected} />

      <main className="p-6 space-y-6 max-w-5xl w-full mx-auto flex-1 flex flex-col">
        {/* Top Navigation & Controls */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => router.push('/calls')}
            className="flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Live Calls</span>
          </button>

          {/* Action buttons */}
          <div className="flex items-center gap-3">
            {isLive && (
              <>
                <button
                  onClick={handleInterrupt}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-purple-600/20 text-purple-300 hover:bg-purple-600/30 border border-purple-500/30 transition-all shadow-sm"
                  title="Simulate customer speech while AI is speaking"
                >
                  <Zap className="w-3.5 h-3.5 text-purple-400" />
                  <span>Simulate Caller Barge-In</span>
                </button>

                <button
                  onClick={handleHangup}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-rose-600/20 text-rose-300 hover:bg-rose-600/30 border border-rose-500/30 transition-all shadow-sm"
                >
                  <PhoneOff className="w-3.5 h-3.5 text-rose-400" />
                  <span>End Call</span>
                </button>
              </>
            )}
          </div>
        </div>

        {/* Call Meta Overview Card */}
        <div className="glass-panel p-6 rounded-2xl border border-border/80">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-3">
                <span className="text-xl font-bold font-mono text-white">{call.phone_number}</span>
                <span className="text-xs font-mono text-slate-500">#{call.id}</span>
                <LanguageBadge language={call.language} />
                <CallStatusBadge status={call.status} />
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-400 pt-1">
                <span>Direction: <strong className="text-slate-200">{call.direction}</strong></span>
                <span>•</span>
                <span>SIP Extension: <strong className="text-emerald-400 font-mono">7000</strong></span>
                <span>•</span>
                <span>Duration: <strong className="text-white font-mono">{formatDuration(call.duration)}</strong></span>
              </div>
            </div>

            {/* Live Audio Visualizer */}
            <div className="bg-[#0b101d] px-4 py-2 rounded-xl border border-border flex items-center gap-3">
              <span className="text-xs font-semibold text-slate-400">Audio Stream:</span>
              <AudioVisualizer isActive={call.status === 'SPEAKING' || call.status === 'LISTENING'} />
            </div>
          </div>
        </div>

        {/* Live Conversation Transcript Feed */}
        <div className="glass-panel rounded-2xl border border-border/80 flex-1 flex flex-col overflow-hidden min-h-[420px]">
          <div className="p-4 border-b border-border bg-surface/50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-cyan-400" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Live Bilingual Transcript Stream
              </h2>
            </div>
            <span className="text-xs text-slate-400 font-mono">Auto-transcribed</span>
          </div>

          <div className="p-6 flex-1 overflow-y-auto space-y-4">
            {call.transcripts.length === 0 ? (
              <div className="text-center py-16 text-slate-500 text-xs">
                Waiting for speech events...
              </div>
            ) : (
              call.transcripts.map((msg) => {
                const isCustomer = msg.speaker === 'customer';
                const isSystem = msg.speaker === 'system';

                if (isSystem) {
                  return (
                    <div key={msg.id} className="text-center my-2">
                      <span className="text-[11px] font-mono px-3 py-1 rounded-full bg-purple-950/40 text-purple-300 border border-purple-800/40">
                        ⚡ {msg.text}
                      </span>
                    </div>
                  );
                }

                return (
                  <div
                    key={msg.id}
                    className={`flex items-start gap-3 ${isCustomer ? 'justify-start' : 'justify-end'}`}
                  >
                    {isCustomer && (
                      <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0">
                        <User className="w-4 h-4" />
                      </div>
                    )}

                    <div
                      className={`max-w-[75%] p-4 rounded-2xl text-sm leading-relaxed shadow-md ${
                        isCustomer
                          ? 'bg-[#151d30] border border-border text-slate-200 rounded-tl-sm'
                          : 'bg-gradient-to-tr from-cyan-950/70 to-emerald-950/70 border border-cyan-800/40 text-emerald-100 rounded-tr-sm'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-4 mb-1 text-[11px]">
                        <span className="font-semibold text-slate-400">
                          {isCustomer ? 'CUSTOMER' : 'AI RECEPTIONIST'}
                        </span>
                        <span className="text-slate-500 font-mono">{formatTime(msg.timestamp)}</span>
                      </div>
                      <p className="font-sans whitespace-pre-wrap">{msg.text}</p>
                      {msg.latency_ms && (
                        <div className="mt-2 text-[10px] text-slate-400 font-mono text-right">
                          Latency: {msg.latency_ms}ms
                        </div>
                      )}
                    </div>

                    {!isCustomer && (
                      <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-600 to-emerald-600 flex items-center justify-center text-white shrink-0 shadow-lg shadow-cyan-600/20">
                        <Bot className="w-4 h-4" />
                      </div>
                    )}
                  </div>
                );
              })
            )}
            <div ref={transcriptBottomRef} />
          </div>
        </div>
      </main>
    </div>
  );
}
