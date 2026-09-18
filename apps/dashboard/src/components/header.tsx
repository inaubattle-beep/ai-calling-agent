'use client';

import React, { useState } from 'react';
import { Play, Zap, PhoneIncoming, CheckCircle2, Wifi, ShieldAlert } from 'lucide-react';
import { simulateCall } from '@/lib/api';

interface HeaderProps {
  wsConnected?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ wsConnected = true }) => {
  const [isSimulating, setIsSimulating] = useState(false);

  const handleSimulate = async (lang: string, bargeIn: boolean = false) => {
    try {
      setIsSimulating(true);
      await simulateCall({
        phone_number: '+8801819203040',
        language: lang,
        barge_in: bargeIn,
      });
    } catch (e) {
      console.error(e);
    } finally {
      setTimeout(() => setIsSimulating(false), 800);
    }
  };

  return (
    <header className="h-16 border-b border-border bg-[#0a0d14]/70 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <h1 className="text-base font-semibold text-slate-100">Bilingual AI Contact Center</h1>
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>System Healthy</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* WebSocket Connectivity status */}
        <div className="flex items-center gap-1.5 text-xs text-slate-400 mr-2">
          <Wifi className={`w-3.5 h-3.5 ${wsConnected ? 'text-emerald-400' : 'text-amber-400 animate-pulse'}`} />
          <span>{wsConnected ? 'Real-Time Sync' : 'Connecting...'}</span>
        </div>

        {/* Quick Simulated Call Actions */}
        <button
          onClick={() => handleSimulate('bn-BD', false)}
          disabled={isSimulating}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 transition-all shadow-sm active:scale-95 disabled:opacity-50"
        >
          <PhoneIncoming className="w-3.5 h-3.5 text-emerald-400" />
          <span>Simulate Call (Bangla)</span>
        </button>

        <button
          onClick={() => handleSimulate('en-US', false)}
          disabled={isSimulating}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 transition-all shadow-sm active:scale-95 disabled:opacity-50"
        >
          <PhoneIncoming className="w-3.5 h-3.5 text-blue-400" />
          <span>Simulate Call (English)</span>
        </button>

        <button
          onClick={() => handleSimulate('bn-BD', true)}
          disabled={isSimulating}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 transition-all shadow-sm active:scale-95 disabled:opacity-50"
        >
          <Zap className="w-3.5 h-3.5 text-purple-400" />
          <span>Test Barge-In</span>
        </button>
      </div>
    </header>
  );
};
