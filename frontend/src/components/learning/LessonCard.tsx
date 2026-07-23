'use client';

import { motion } from 'framer-motion';
import { Clock } from 'lucide-react';
import Link from 'next/link';
import Badge from '@/components/ui/Badge';
import DynamicIcon from '@/components/ui/DynamicIcon';
import type { LessonSummary } from '@/types/learning';

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

export default function LessonCard({ lesson, index = 0 }: { lesson: LessonSummary; index?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25, delay: index * 0.04 }}
    >
      <Link
        href={`/lesson/${lesson.id}`}
        className="flex items-center gap-4 p-4 rounded-xl border border-slate-200 bg-white hover:border-indigo-300 hover:shadow-sm transition-all group"
      >
        <div className="w-10 h-10 shrink-0 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:scale-105 transition-transform">
          <DynamicIcon iconName={lesson.icon} className="w-5 h-5" />
        </div>

        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-slate-900 truncate">{lesson.title}</h4>
          {lesson.description && (
            <p className="text-sm text-slate-500 truncate">{lesson.description}</p>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {lesson.difficulty_level && (
            <Badge variant={DIFFICULTY_VARIANT[lesson.difficulty_level] ?? 'neutral'}>
              {DIFFICULTY_LABEL[lesson.difficulty_level] ?? lesson.difficulty_level}
            </Badge>
          )}
          {lesson.estimated_duration && (
            <Badge icon={<Clock className="w-3 h-3" />}>{lesson.estimated_duration} דק&apos;</Badge>
          )}
        </div>
      </Link>
    </motion.div>
  );
}
