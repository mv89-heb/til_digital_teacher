'use client';

import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Brain, Filter, RefreshCw, Sparkles } from 'lucide-react';
import Alert from '@/components/ui/Alert';
import EmptyState from '@/components/ui/EmptyState';
import Skeleton from '@/components/ui/Skeleton';
import QuestionBlock from '@/components/practice/QuestionBlock';
import { getCategories, getPracticeQuestions } from '@/lib/api';
import { useAuthStore } from '@/store/useAuthStore';

type Difficulty = 'all' | 'easy' | 'medium' | 'exam';

type CategoryOption = { id: number; name: string; type: string };

const difficultyLabels: Record<Difficulty, string> = {
  all: 'כל הרמות',
  easy: 'קל',
  medium: 'בינוני',
  exam: 'רמת מבחן',
};

export default function PracticePage() {
  const { token } = useAuthStore();
  const [categoryId, setCategoryId] = useState<number | undefined>();
  const [difficulty, setDifficulty] = useState<Difficulty>('all');
  const [mode, setMode] = useState<'all' | 'adaptive'>('all');
  const [refreshKey, setRefreshKey] = useState(0);

  const categoriesQuery = useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
  });

  const categories = useMemo<CategoryOption[]>(() => {
    return (categoriesQuery.data ?? []).map((category) => ({
      id: category.id,
      name: category.name,
      type: category.type,
    }));
  }, [categoriesQuery.data]);

  const questionsQuery = useQuery({
    queryKey: ['practice-questions', token, categoryId, difficulty, mode, refreshKey],
    queryFn: () =>
      getPracticeQuestions(token as string, {
        categoryId,
        difficulty: difficulty === 'all' ? undefined : difficulty,
        limit: 50,
        mode,
      }),
    enabled: !!token,
  });

  const selectedDifficulty = questionsQuery.data?.target_difficulty;

  return (
    <div className="max-w-5xl mx-auto pb-12">
      <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-7 h-7 text-indigo-600" />
            <h1 className="text-3xl font-bold text-slate-900">מאגר השאלות</h1>
          </div>
          <p className="text-slate-600">
            כאן נמצאות השאלות הזמינות לתרגול במערכת. אפשר לפתור אותן אחת אחרי השנייה ולקבל הסבר מיד לאחר הבדיקה.
          </p>
        </div>
        <button
          onClick={() => setRefreshKey((value) => value + 1)}
          disabled={questionsQuery.isFetching}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold hover:bg-indigo-700 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${questionsQuery.isFetching ? 'animate-spin' : ''}`} />
          רענן שאלות
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl p-4 md:p-5 mb-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4 font-bold text-slate-800">
          <Filter className="w-4 h-4 text-indigo-600" />
          סינון ותרגול
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <label className="text-sm text-slate-600">
            <span className="block mb-1 font-medium">תחום</span>
            <select
              value={categoryId ?? ''}
              onChange={(event) => setCategoryId(event.target.value ? Number(event.target.value) : undefined)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-slate-800"
            >
              <option value="">כל התחומים</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>{category.name}</option>
              ))}
            </select>
          </label>

          <label className="text-sm text-slate-600">
            <span className="block mb-1 font-medium">רמת קושי</span>
            <select
              value={difficulty}
              onChange={(event) => setDifficulty(event.target.value as Difficulty)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-slate-800"
            >
              {(Object.keys(difficultyLabels) as Difficulty[]).map((key) => (
                <option key={key} value={key}>{difficultyLabels[key]}</option>
              ))}
            </select>
          </label>

          <label className="text-sm text-slate-600">
            <span className="block mb-1 font-medium">מצב</span>
            <select
              value={mode}
              onChange={(event) => setMode(event.target.value as 'all' | 'adaptive')}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-slate-800"
            >
              <option value="all">הצג את כל השאלות</option>
              <option value="adaptive">תרגול אדפטיבי</option>
            </select>
          </label>
        </div>

        {mode === 'adaptive' && selectedDifficulty && (
          <div className="mt-4 flex items-center gap-2 text-sm text-indigo-700 bg-indigo-50 rounded-xl px-3 py-2">
            <Sparkles className="w-4 h-4" />
            המערכת בחרה כרגע רמת יעד: <strong>{difficultyLabels[selectedDifficulty]}</strong>
          </div>
        )}
      </div>

      {questionsQuery.isLoading && (
        <div className="space-y-5">
          <Skeleton className="h-72 w-full" />
          <Skeleton className="h-72 w-full" />
        </div>
      )}

      {questionsQuery.isError && (
        <Alert variant="error">לא הצלחנו לטעון את מאגר השאלות. נסו לרענן את הדף.</Alert>
      )}

      {questionsQuery.data && questionsQuery.data.questions.length === 0 && (
        <EmptyState
          icon={<Brain className="w-7 h-7" />}
          title="לא נמצאו שאלות"
          description="אין כרגע שאלות התואמות את הסינון שבחרתם. נסו תחום או רמת קושי אחרת."
        />
      )}

      {questionsQuery.data && questionsQuery.data.questions.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>{questionsQuery.data.count} שאלות נטענו</span>
            <span>{mode === 'all' ? 'כל השאלות הזמינות' : 'בחירה אדפטיבית'}</span>
          </div>
          {questionsQuery.data.questions.map((question, index) => (
            <section key={question.id} className="relative">
              <div className="absolute -right-3 top-5 z-10 w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center text-sm font-bold shadow-md">
                {index + 1}
              </div>
              <QuestionBlock question={question} token={token} />
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
