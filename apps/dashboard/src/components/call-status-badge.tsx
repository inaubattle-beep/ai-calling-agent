import React from 'react';
import { PhoneCall, Radio, Brain, Volume2, PhoneOff, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CallStatusBadgeProps {
  status: string;
  className?: string;
  showIcon?: boolean;
}

export const CallStatusBadge: React.FC<CallStatusBadgeProps> = ({ status, className, showIcon = true }) => {
  const s = status.toUpperCase();

  let colorClasses = 'bg-slate-800/80 text-slate-300 border-slate-700';
  let Icon = PhoneCall;
  let pulse = false;

  switch (s) {
    case 'RINGING':
    case 'DIALING':
      colorClasses = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      Icon = PhoneCall;
      pulse = true;
      break;
    case 'CONNECTED':
      colorClasses = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      Icon = Radio;
      break;
    case 'LISTENING':
      colorClasses = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      Icon = Radio;
      pulse = true;
      break;
    case 'THINKING':
      colorClasses = 'bg-purple-500/10 text-purple-400 border-purple-500/30';
      Icon = Brain;
      pulse = true;
      break;
    case 'SPEAKING':
      colorClasses = 'bg-emerald-500/15 text-emerald-300 border-emerald-400/40';
      Icon = Volume2;
      pulse = true;
      break;
    case 'ON_HOLD':
      colorClasses = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      break;
    case 'ENDED':
    case 'TRANSFERRED':
      colorClasses = 'bg-slate-800 text-slate-400 border-slate-700';
      Icon = PhoneOff;
      break;
    case 'ERROR':
      colorClasses = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      Icon = AlertCircle;
      break;
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border backdrop-blur-sm',
        colorClasses,
        className
      )}
    >
      {pulse && <span className="w-1.5 h-1.5 rounded-full bg-current animate-ping" />}
      {!pulse && <span className="w-1.5 h-1.5 rounded-full bg-current" />}
      {showIcon && <Icon className="w-3 h-3" />}
      <span>{status}</span>
    </span>
  );
};
