import React from 'react';
import { Globe } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LanguageBadgeProps {
  language: string;
  className?: string;
}

export const LanguageBadge: React.FC<LanguageBadgeProps> = ({ language, className }) => {
  let label = language;
  let style = 'bg-slate-800 text-slate-300 border-slate-700';

  if (language.startsWith('bn')) {
    label = 'Bangla (বাংলা)';
    style = 'bg-emerald-950/40 text-emerald-300 border-emerald-800/40';
  } else if (language.startsWith('en')) {
    label = 'English (US)';
    style = 'bg-blue-950/40 text-blue-300 border-blue-800/40';
  } else if (language === 'mixed') {
    label = 'Banglish (Mixed)';
    style = 'bg-violet-950/40 text-violet-300 border-violet-800/40';
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium border',
        style,
        className
      )}
    >
      <Globe className="w-2.5 h-2.5 opacity-70" />
      <span>{label}</span>
    </span>
  );
};
