import React from 'react';
import { cn } from '@/lib/utils';

interface AudioVisualizerProps {
  isActive: boolean;
  color?: 'emerald' | 'cyan' | 'purple';
  barCount?: number;
  className?: string;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
  isActive,
  color = 'cyan',
  barCount = 18,
  className,
}) => {
  const bars = Array.from({ length: barCount });

  const colorMap = {
    emerald: 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]',
    cyan: 'bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.5)]',
    purple: 'bg-purple-400 shadow-[0_0_8px_rgba(192,132,252,0.5)]',
  };

  return (
    <div className={cn('flex items-center gap-[3px] h-8 px-2', className)}>
      {bars.map((_, i) => {
        // Pseudo-random staggered delays for natural organic speech wave
        const delay = (i % 6) * 0.18;
        const baseHeight = isActive ? `${25 + ((i * 17) % 65)}%` : '15%';

        return (
          <div
            key={i}
            style={{
              height: isActive ? undefined : '12%',
              animationDelay: `${delay}s`,
              animationDuration: `${0.8 + ((i * 13) % 7) * 0.1}s`,
            }}
            className={cn(
              'w-[3px] rounded-full transition-all duration-150',
              colorMap[color],
              isActive ? 'animate-wave-bar' : 'opacity-20'
            )}
          />
        );
      })}
    </div>
  );
};
