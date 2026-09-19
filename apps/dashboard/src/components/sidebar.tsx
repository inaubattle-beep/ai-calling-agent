'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/navigation';
import { usePathname } from 'next/navigation';
import { 
  PhoneCall, 
  LayoutDashboard, 
  Bot, 
  History, 
  Settings, 
  Radio, 
  Zap,
  Activity
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { AppSettings, fetchSettings } from '@/lib/api';

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const [settings, setSettings] = useState<AppSettings | null>(null);

  useEffect(() => {
    fetchSettings().then(setSettings).catch(() => undefined);
  }, []);

  const navItems = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Live Calls', href: '/calls', icon: PhoneCall },
    { name: 'AI Agents', href: '/agents', icon: Bot },
    { name: 'Call History', href: '/history', icon: History },
    { name: 'Admin Settings', href: '/admin', icon: Settings },
  ];

  return (
    <aside className="w-64 border-r border-border bg-[#0d121f]/90 backdrop-blur-md flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div>
        {/* Brand Header */}
        <div className="h-16 flex items-center px-6 border-b border-border gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Radio className="w-4 h-4 text-white" />
          </div>
          <div>
            <span className="font-bold tracking-tight text-white block text-sm leading-tight">{settings?.business_name || 'Voice Platform'}</span>
            <span className="text-[11px] text-cyan-400 font-medium">Bilingual MVP</span>
          </div>
        </div>

        {/* Navigation Items */}
        <div className="p-3 space-y-1">
          <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
            Platform
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || (item.href !== '/' && pathname?.startsWith(item.href));
            return (
              <a
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all group',
                  active
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-surfaceLight/50'
                )}
              >
                <Icon className={cn('w-4 h-4 transition-colors', active ? 'text-cyan-400' : 'text-slate-500 group-hover:text-slate-300')} />
                <span>{item.name}</span>
              </a>
            );
          })}
        </div>
      </div>

      {/* PBX & Runtime Status Footer Card */}
      <div className="p-4 border-t border-border">
        <div className="bg-surface p-3 rounded-xl border border-border/80">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-300">PJSIP Extension</span>
            <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">7000</span>
          </div>
          <div className="space-y-1.5 text-[11px] text-slate-400">
            <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                {settings?.default_agent_id || 'Default agent'}
              </span>
              <span className="text-emerald-400 font-medium">ONLINE</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Languages</span>
              <span className="text-slate-300 font-mono">{settings?.supported_languages.join(' / ') || 'Loading'}</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
