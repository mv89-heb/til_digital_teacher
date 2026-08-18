'use client';

import { Search, SlidersHorizontal, X } from 'lucide-react';

export type LearningDifficultyFilter = 'all' | 'beginner' | 'intermediate' | 'advanced';

interface LearningCenterToolbarProps {
  query: string;
  difficulty: LearningDifficultyFilter;
  onQueryChange: (value: string) => void;
  onDifficultyChange: (value: LearningDifficultyFilter) => void;
  resultCount: number;
}

export default function LearningCenterToolbar({
  query,
  difficulty,
  onQueryChange,
  onDifficultyChange,
  resultCount,
}: LearningCenterToolbarProps) {
  const hasFilters = query.trim().length > 0 || difficulty !== 'all';

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-3 sm:p-4 shadow-sm">
      <div className="flex flex-col lg:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="חיפוש שיעור או נושא..."
            aria-label="חיפוש שיעור או נושא"
            className="w-full h-11 rounded-xl border border-slate-200 bg-slate-50 pr-10 pl-10 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100"
          />
          {query && (
            <button
              type="button"
              onClick={() => onQueryChange('')}
              aria-label="נקה חיפוש"
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1 lg:pb-0">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 shrink-0 px-1">
            <SlidersHorizontal className="w-4 h-4" />
            רמה
          </div>
          {([
            ['all', 'הכול'],
            ['beginner', 'מתחילים'],
            ['intermediate', 'בינוני'],
            ['advanced', 'מתקדם'],
          ] as const).map(([value, label]) => (
            <button
              key={value}
              type="button"
              onClick={() => onDifficultyChange(value)}
              className={`h-9 px-3 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
                difficulty === value
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-3 text-xs text-slate-400">
        {hasFilters ? `${resultCount} שיעורים נמצאו` : `${resultCount} שיעורים זמינים`}
      </div>
    </div>
  );
}
