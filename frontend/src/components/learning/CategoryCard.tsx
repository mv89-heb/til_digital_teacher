'use client';

import { motion } from 'framer-motion';
import Card from '@/components/ui/Card';
import DynamicIcon from '@/components/ui/DynamicIcon';
import type { Category } from '@/types/learning';

export default function CategoryCard({ category, index = 0 }: { category: Category; index?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <Card hoverable className="p-6 flex flex-col gap-4">
        <div className="flex items-start justify-between">
          <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <DynamicIcon iconName={category.icon} className="w-6 h-6" />
          </div>
          <span className="text-xs font-bold text-slate-400 bg-slate-50 px-2.5 py-1 rounded-full">
            {category.lesson_count} שיעורים
          </span>
        </div>

        <div>
          <h3 className="font-bold text-lg text-slate-900 mb-1">{category.name}</h3>
          {category.description && (
            <p className="text-sm text-slate-500 leading-relaxed line-clamp-2">{category.description}</p>
          )}
        </div>
      </Card>
    </motion.div>
  );
}
