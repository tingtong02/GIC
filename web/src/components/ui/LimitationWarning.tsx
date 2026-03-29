import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface LimitationWarningProps {
  level?: 'caution' | 'critical';
  title: string;
  children: React.ReactNode;
  className?: string;
}

export function LimitationWarning({ level = 'caution', title, children, className }: LimitationWarningProps) {
  const isCritical = level === 'critical';
  
  return (
    <div className={cn(
      "relative border-l-4 p-5 rounded-r overflow-hidden flex",
      isCritical ? "bg-rose-50 border-rose-700" : "bg-amber-50 border-amber-700",
      className
    )}>
      <div className="mr-4 mt-0.5">
        <AlertTriangle className={cn(
          "w-5 h-5",
          isCritical ? "text-rose-700" : "text-amber-700"
        )} />
      </div>
      <div>
        <h4 className={cn(
          "font-bold text-sm uppercase tracking-wider mb-2",
          isCritical ? "text-rose-900" : "text-amber-900"
        )}>
          {title}
        </h4>
        <div className="text-slate-800 text-sm leading-relaxed">
          {children}
        </div>
      </div>
    </div>
  );
}
