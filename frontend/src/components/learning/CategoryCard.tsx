'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowLeft, BookOpen } from 'lucide-react';
import Card from '@/components/ui/Card';
import DynamicIcon from '@/components/ui/DynamicIcon';
import type { Category } from '@/types/learning';

interface CategoryCardProps {
  category: Category;
  index?: number;
  compact?: boolean;
}

export default function CategoryCard({ category, index = 0, compact = false }: CategoryCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: Math.min(index, 10) * 0.05 }}
    >
      <Card hoverable className={compact ? 'p-5 h-full' : 'p-6 flex flex-col gap-4'}>
        <div className="flex items-start justify-between gap-3">
          <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <DynamicIcon iconName={category.icon} className="w-6 h-6" />
          </div>
          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 bg-slate-50 px-2.5 py-1 rounded-full">
            <BookOpen className="w-3.5 h-3.5" />
            {category.lesson_count} שיעורים
          </span>
        </div>

        <div>
          <h3 className="font-bold text-lg text-slate-900 mb-1">{category.name}</h3>
          {category.description && (
            <p className="text-sm text-slate-500 leading-relaxed line-clamp-2">{category.description}</p>
          )}
        </div>

        {compact && category.lessons.length > 0 && (
          <div className="mt-auto pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>השיעור הראשון: {category.lessons[0].title}</span>
            <Link
              href={`/lesson/${category.lessons[0].id}`}
              className="inline-flex items-center gap-1 text-indigo-600 font-bold hover:text-indigo-700 shrink-0"
              onClick={(event) => event.stopPropagation()}
            >
              התחל <ArrowLeft className="w-3.5 h-3.5" />
            </Link>
          </div>
        )}
      </Card>
    </motion.div>
  );
}
