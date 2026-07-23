'use client';

import { useQuery } from '@tanstack/react-query';
import { BookOpen } from 'lucide-react';
import { getCategories } from '@/lib/api';
import CategoryCard from '@/components/learning/CategoryCard';
import LessonCard from '@/components/learning/LessonCard';
import Skeleton from '@/components/ui/Skeleton';
import Alert from '@/components/ui/Alert';
import EmptyState from '@/components/ui/EmptyState';

export default function LearnPage() {
  const {
    data: categories,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
  });

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">מרכז הלימוד</h1>
        <p className="text-slate-600">בחרו נושא כדי להתחיל ללמוד</p>
      </div>

      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      )}

      {isError && <Alert variant="error">לא הצלחנו לטעון את התוכן. נסו לרענן את הדף.</Alert>}

      {categories && categories.length === 0 && (
        <EmptyState
          icon={<BookOpen className="w-7 h-7" />}
          title="אין עדיין תוכן זמין ללמידה"
          description="בקרוב יתווספו כאן קטגוריות ושיעורים חדשים."
        />
      )}

      {categories && categories.length > 0 && (
        <div className="space-y-8">
          {categories.map((category, index) => (
            <div key={category.id}>
              <CategoryCard category={category} index={index} />
              {category.lessons.length > 0 && (
                <div className="mt-4 space-y-2 pr-2">
                  {category.lessons.map((lesson, i) => (
                    <LessonCard key={lesson.id} lesson={lesson} index={i} />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
