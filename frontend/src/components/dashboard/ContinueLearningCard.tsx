'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { ChevronLeft, PlayCircle } from 'lucide-react';
import type { LessonProgressEntry } from '@/types/learning';

export default function ContinueLearningCard({ lesson }: { lesson: LessonProgressEntry }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <Link
        href={`/lesson/${lesson.lesson_id}`}
        className="flex items-center gap-4 bg-gradient-to-l from-indigo-600 to-blue-500 text-white rounded-3xl p-6 shadow-lg shadow-indigo-200 hover:shadow-xl transition-shadow group"
      >
        <div className="w-14 h-14 rounded-2xl bg-white/15 flex items-center justify-center shrink-0">
          <PlayCircle className="w-7 h-7" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold text-indigo-100 mb-0.5">המשך מהנקודה האחרונה</div>
          <div className="font-bold truncate">{lesson.title}</div>
          <div className="text-sm text-indigo-100 truncate">{lesson.category_name}</div>
        </div>
        <ChevronLeft className="w-5 h-5 shrink-0 group-hover:-translate-x-1 transition-transform" />
      </Link>
    </motion.div>
  );
}
