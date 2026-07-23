import { ReactNode } from 'react';
import Card from '@/components/ui/Card';

interface StatsCardProps {
  icon: ReactNode;
  label: string;
  value: string | number;
  accent?: 'indigo' | 'emerald' | 'amber' | 'rose';
}

const ACCENT_CLASSES: Record<NonNullable<StatsCardProps['accent']>, string> = {
  indigo: 'bg-indigo-50 text-indigo-600',
  emerald: 'bg-emerald-50 text-emerald-600',
  amber: 'bg-amber-50 text-amber-600',
  rose: 'bg-rose-50 text-rose-600',
};

export default function StatsCard({ icon, label, value, accent = 'indigo' }: StatsCardProps) {
  return (
    <Card className="p-5 flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${ACCENT_CLASSES[accent]}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <div className="text-2xl font-bold text-slate-900 leading-none mb-1">{value}</div>
        <div className="text-sm text-slate-500 truncate">{label}</div>
      </div>
    </Card>
  );
}
