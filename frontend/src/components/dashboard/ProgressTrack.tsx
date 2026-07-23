'use client';

import { motion } from 'framer-motion';
import type { DashboardSummary } from '@/types/learning';

const STAGES = [
  { icon: '🟢', label: 'התחלה' },
  { icon: '📚', label: 'לומד' },
  { icon: '✏️', label: 'מתרגל' },
  { icon: '⚡', label: 'משפר מהירות' },
  { icon: '🏆', label: 'מוכן למבחן' },
];

function getStageIndex(stats: DashboardSummary['stats']): number {
  if (stats.total_questions_attempted === 0) return 0;
  if (stats.overall_accuracy_percent < 50) return 1;
  if (stats.overall_accuracy_percent < 70) return 2;
  if (stats.overall_accuracy_percent < 90) return 3;
  return 4;
}

export default function ProgressTrack({ stats }: { stats: DashboardSummary['stats'] }) {
  const currentIndex = getStageIndex(stats);

  return (
    <div className="flex items-center justify-between overflow-x-auto pb-1 gap-1 sm:gap-2">
      {STAGES.map((stage, index) => {
        const reached = index <= currentIndex;
        const isCurrent = index === currentIndex;
        return (
          <div key={stage.label} className="flex items-center flex-1 min-w-[64px]">
            <div className="flex flex-col items-center gap-1.5 flex-1">
              <motion.div
                initial={false}
                animate={{ scale: isCurrent ? 1.15 : 1 }}
                className={`w-10 h-10 sm:w-12 sm:h-12 rounded-2xl flex items-center justify-center text-lg sm:text-xl shrink-0 transition-colors ${
                  reached
                    ? 'bg-gradient-to-tr from-indigo-500 to-blue-500 shadow-md shadow-indigo-200'
                    : 'bg-slate-100'
                } ${!reached ? 'opacity-40' : ''}`}
              >
                {stage.icon}
              </motion.div>
              <span
                className={`text-[10px] sm:text-xs font-semibold text-center leading-tight ${
                  reached ? 'text-slate-700' : 'text-slate-400'
                }`}
              >
                {stage.label}
              </span>
            </div>
            {index < STAGES.length - 1 && (
              <div
                className={`h-0.5 flex-1 -mt-5 mx-0.5 sm:mx-1 rounded-full ${
                  index < currentIndex ? 'bg-indigo-400' : 'bg-slate-200'
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
