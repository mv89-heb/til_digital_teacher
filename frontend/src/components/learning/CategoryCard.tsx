'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowLeft, BookOpen, CheckCircle2, Target, TrendingUp } from 'lucide-react';
import Card from '@/components/ui/Card';
import DynamicIcon from '@/components/ui/DynamicIcon';
import type { Category, CategoryProgress } from '@/types/learning';

interface CategoryCardProps {
  category: Category;
  progress?: CategoryProgress;
  index?: number;
  compact?: boolean;
}

const LEVEL_LABEL: Record<string, string> = {
  beginner: 'מתחיל',
  basic: 'בסיסי',
  intermediate: 'בינוני',
  exam_ready: 'מוכן למבחן',
  advanced: 'מתקדם',
};

export default function CategoryCard({ category, progress, index = 0, compact = false }: CategoryCardProps) {
  const lessonPercent = progress && progress.lessons_total > 0
    ? Math.round((progress.lessons_completed / progress.lessons_total) * 100)
    : 0;
  const practicePercent = progress && progress.questions_attempted > 0
    ? Math.min(100, Math.round((progress.questions_attempted / Math.max(progress.questions_attempted, 20)) * 100))
    : 0;
  const hasPractice = !!progress && progress.questions_attempted > 0;
  const nextLessonIndex = Math.min(progress?.lessons_completed ?? 0, Math.max(0, category.lessons.length - 1));
  const nextLesson = category.lessons[nextLessonIndex];

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: Math.min(index, 10) * 0.05 }}>
      <Card hoverable className={compact ? 'p-5 h-full' : 'p-6 flex flex-col gap-4'}>
        <div className="flex items-start justify-between gap-3">
          <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center"><DynamicIcon iconName={category.icon} className="w-6 h-6" /></div>
          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 bg-slate-50 px-2.5 py-1 rounded-full"><BookOpen className="w-3.5 h-3.5" />{category.lesson_count} שיעורים</span>
        </div>

        <div>
          <h3 className="font-bold text-lg text-slate-900 mb-1">{category.name}</h3>
          {category.description && <p className="text-sm text-slate-500 leading-relaxed line-clamp-2">{category.description}</p>}
        </div>

        {progress && (
          <div className="space-y-3 rounded-xl bg-slate-50 p-3">
            <div className="flex items-center justify-between text-xs font-bold text-slate-600"><span>התקדמות בשיעורים</span><span>{progress.lessons_completed}/{progress.lessons_total}</span></div>
            <div className="h-2 rounded-full bg-slate-200 overflow-hidden"><div className="h-full rounded-full bg-indigo-500 transition-all" style={{ width: `${lessonPercent}%` }} /></div>

            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-lg bg-white border border-slate-100 p-2.5">
                <div className="text-[10px] font-bold text-slate-400">תרגול</div>
                <div className="mt-0.5 text-sm font-extrabold text-slate-800">{progress.questions_attempted}</div>
                <div className="text-[10px] text-slate-400">שאלות</div>
              </div>
              <div className="rounded-lg bg-white border border-slate-100 p-2.5">
                <div className="text-[10px] font-bold text-slate-400">דיוק</div>
                <div className="mt-0.5 text-sm font-extrabold text-slate-800">{hasPractice ? `${progress.accuracy_percent}%` : '—'}</div>
                <div className="text-[10px] text-slate-400">{progress.questions_correct} נכונות</div>
              </div>
            </div>

            <div className="flex items-center justify-between gap-2 text-xs">
              <span className="inline-flex items-center gap-1 text-slate-500"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />{hasPractice ? 'יש נתוני תרגול' : 'טרם תרגלת'}</span>
              <span className="inline-flex items-center gap-1 font-bold text-indigo-600"><Target className="w-3.5 h-3.5" />{LEVEL_LABEL[progress.level] ?? progress.level}</span>
            </div>
            {hasPractice && (
              <div className="pt-1">
                <div className="flex items-center justify-between text-[10px] font-semibold text-slate-400 mb-1"><span>נפח תרגול</span><span>{progress.questions_attempted}+</span></div>
                <div className="h-1.5 rounded-full bg-slate-200 overflow-hidden"><div className="h-full rounded-full bg-emerald-500" style={{ width: `${practicePercent}%` }} /></div>
              </div>
            )}
          </div>
        )}

        {!progress && <div className="rounded-xl border border-dashed border-indigo-200 bg-indigo-50/50 p-3 text-sm text-indigo-700"><div className="font-bold">עדיין לא התחלת את התחום</div><div className="text-xs mt-1 text-indigo-600">בחר שיעור, למד את השיטה ואז עבור לתרגול.</div></div>}

        {compact && category.lessons.length > 0 && nextLesson && (
          <div className="mt-auto pt-3 border-t border-slate-100 flex items-center justify-between gap-3 text-xs text-slate-500">
            <div className="min-w-0">
              <div className="font-semibold text-slate-700">{progress && progress.lessons_completed > 0 ? 'השלב הבא' : 'מתחילים כאן'}</div>
              <div className="truncate mt-0.5">{nextLesson.title}</div>
            </div>
            <Link href={`/lesson/${nextLesson.id}`} className="inline-flex items-center gap-1 text-indigo-600 font-bold hover:text-indigo-700 shrink-0" onClick={(event) => event.stopPropagation()}>
              {progress && progress.lessons_completed > 0 ? 'המשך' : 'התחל'} <ArrowLeft className="w-3.5 h-3.5" />
            </Link>
          </div>
        )}

        {progress?.questions_attempted ? (
          <Link href="/practice" className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-700 hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700 transition-colors">
            <TrendingUp className="w-3.5 h-3.5" /> לתרגול בתחום
          </Link>
        ) : null}
      </Card>
    </motion.div>
  );
}
