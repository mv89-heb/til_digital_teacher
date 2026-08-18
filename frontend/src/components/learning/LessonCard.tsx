'use client';

import { motion } from 'framer-motion';
import { CheckCircle2, Clock, PlayCircle } from 'lucide-react';
import Link from 'next/link';
import Badge from '@/components/ui/Badge';
import DynamicIcon from '@/components/ui/DynamicIcon';
import type { LessonProgressEntry, LessonSummary } from '@/types/learning';

const DIFFICULTY_LABEL: Record<string, string> = {
  beginner: 'למתחילים',
  intermediate: 'בינוני',
  advanced: 'מתקדם',
};

const DIFFICULTY_VARIANT: Record<string, 'success' | 'warning' | 'danger'> = {
  beginner: 'success',
  intermediate: 'warning',
  advanced: 'danger',
};

interface LessonCardProps {
  lesson: LessonSummary;
  index?: number;
  progress?: LessonProgressEntry;
}

export default function LessonCard({ lesson, index = 0, progress }: LessonCardProps) {
  const completed = !!progress?.completed_at;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: Math.min(index, 10) * 0.03 }}
    >
      <Link
        href={`/lesson/${lesson.id}`}
        className="flex items-center gap-4 p-4 rounded-2xl border border-slate-200 bg-white hover:border-indigo-300 hover:shadow-md transition-all group"
      >
        <div className={`w-11 h-11 shrink-0 rounded-xl flex items-center justify-center transition-transform group-hover:scale-105 ${completed ? 'bg-emerald-50 text-emerald-600' : 'bg-indigo-50 text-indigo-600'}`}>
          {completed ? <CheckCircle2 className="w-5 h-5" /> : <DynamicIcon iconName={lesson.icon} className="w-5 h-5" />}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <h4 className="font-bold text-slate-900 truncate">{lesson.title}</h4>
            {completed && <span className="text-[10px] font-bold text-emerald-600 shrink-0">הושלם</span>}
          </div>
          {lesson.description && <p className="text-sm text-slate-500 truncate">{lesson.description}</p>}
        </div>

        <div className="hidden sm:flex items-center gap-2 shrink-0">
          {lesson.difficulty_level && (
            <Badge variant={DIFFICULTY_VARIANT[lesson.difficulty_level] ?? 'neutral'}>
              {DIFFICULTY_LABEL[lesson.difficulty_level] ?? lesson.difficulty_level}
            </Badge>
          )}
          {lesson.estimated_duration && (
            <Badge icon={<Clock className="w-3 h-3" />}>{lesson.estimated_duration} דק&apos;</Badge>
          )}
        </div>

        <PlayCircle className="w-5 h-5 text-slate-300 group-hover:text-indigo-500 shrink-0 transition-colors" />
      </Link>
    </motion.div>
  );
}
