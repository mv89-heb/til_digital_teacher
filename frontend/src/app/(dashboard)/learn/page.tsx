'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, BookOpen, CheckCircle2, Database, Flame, PlayCircle, Sparkles, Target, Trophy } from 'lucide-react';
import { getCategories, getDashboard } from '@/lib/api';
import { useAuthStore } from '@/store/useAuthStore';
import CategoryCard from '@/components/learning/CategoryCard';
import LessonCard from '@/components/learning/LessonCard';
import LearningCenterToolbar, { type LearningDifficultyFilter } from '@/components/learning/LearningCenterToolbar';
import QuestionBankBrowser from '@/components/learning/QuestionBankBrowser';
import Skeleton from '@/components/ui/Skeleton';
import Alert from '@/components/ui/Alert';
import EmptyState from '@/components/ui/EmptyState';
import Card from '@/components/ui/Card';
import type { LessonProgressEntry } from '@/types/learning';

export default function LearnPage() {
  const { token } = useAuthStore();
  const [query, setQuery] = useState('');
  const [difficulty, setDifficulty] = useState<LearningDifficultyFilter>('all');

  const categoriesQuery = useQuery({ queryKey: ['categories'], queryFn: getCategories });
  const dashboardQuery = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => getDashboard(token as string),
    enabled: !!token,
    staleTime: 30_000,
  });

  const categories = categoriesQuery.data ?? [];
  const progressLessons = useMemo(() => {
    const dashboard = dashboardQuery.data;
    return [...(dashboard?.in_progress_lessons ?? []), ...(dashboard?.completed_lessons ?? [])] as LessonProgressEntry[];
  }, [dashboardQuery.data]);
  const progressMap = useMemo(() => new Map(progressLessons.map((item) => [item.lesson_id, item])), [progressLessons]);
  const allLessons = useMemo(() => categories.flatMap((category) => category.lessons.map((lesson) => ({ ...lesson, categoryName: category.name }))), [categories]);
  const filteredLessons = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return allLessons.filter((lesson) => {
      const matchesQuery = !normalized || [lesson.title, lesson.description ?? '', lesson.categoryName].join(' ').toLowerCase().includes(normalized);
      const matchesDifficulty = difficulty === 'all' || lesson.difficulty_level === difficulty;
      return matchesQuery && matchesDifficulty;
    });
  }, [allLessons, query, difficulty]);

  const continueLesson = dashboardQuery.data?.continue_learning;
  const completedCount = dashboardQuery.data?.stats.total_lessons_completed ?? 0;
  const totalLessons = dashboardQuery.data?.stats.total_lessons_available ?? allLessons.length;
  const accuracy = dashboardQuery.data?.stats.overall_accuracy_percent ?? 0;
  const isLoading = categoriesQuery.isLoading;
  const isError = categoriesQuery.isError;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-10">
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-l from-indigo-700 via-indigo-600 to-blue-500 p-6 sm:p-8 text-white shadow-xl shadow-indigo-100">
        <div className="absolute -left-16 -top-20 h-48 w-48 rounded-full bg-white/10 blur-2xl" />
        <div className="absolute -right-20 -bottom-24 h-56 w-56 rounded-full bg-blue-300/20 blur-3xl" />
        <div className="relative flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-bold text-indigo-50 mb-4"><Sparkles className="w-3.5 h-3.5" />מסלול הלמידה שלך</div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2">מרכז הלימוד</h1>
            <p className="text-indigo-100 max-w-2xl leading-relaxed">שיעורים מסודרים, תרגול ממוקד ומאגר שאלות מלא — הכול במקום אחד.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="#question-bank" className="inline-flex items-center justify-center gap-2 rounded-xl bg-white/15 border border-white/20 px-5 py-3 text-sm font-bold text-white hover:bg-white/20 transition-colors"><Database className="w-4 h-4" />מאגר השאלות</Link>
            <Link href="/practice" className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-indigo-700 shadow-lg hover:bg-indigo-50 transition-colors"><Target className="w-4 h-4" />התחל תרגול<ArrowLeft className="w-4 h-4" /></Link>
          </div>
        </div>
      </section>

      {!isLoading && !isError && allLessons.length > 0 && (
        <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <Card className="p-4 sm:p-5"><div className="flex items-center gap-3"><div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center"><BookOpen className="w-5 h-5" /></div><div><div className="text-xl font-extrabold text-slate-900">{totalLessons}</div><div className="text-xs text-slate-500">שיעורים</div></div></div></Card>
          <Card className="p-4 sm:p-5"><div className="flex items-center gap-3"><div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center"><CheckCircle2 className="w-5 h-5" /></div><div><div className="text-xl font-extrabold text-slate-900">{completedCount}</div><div className="text-xs text-slate-500">הושלמו</div></div></div></Card>
          <Card className="p-4 sm:p-5"><div className="flex items-center gap-3"><div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center"><Trophy className="w-5 h-5" /></div><div><div className="text-xl font-extrabold text-slate-900">{dashboardQuery.data?.xp_total ?? 0}</div><div className="text-xs text-slate-500">XP שנצברו</div></div></div></Card>
          <Card className="p-4 sm:p-5"><div className="flex items-center gap-3"><div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center"><Flame className="w-5 h-5" /></div><div><div className="text-xl font-extrabold text-slate-900">{accuracy}%</div><div className="text-xs text-slate-500">דיוק בתרגול</div></div></div></Card>
        </section>
      )}

      {continueLesson && <Link href={`/lesson/${continueLesson.lesson_id}`} className="group flex items-center gap-4 rounded-2xl border border-indigo-100 bg-indigo-50/70 p-4 sm:p-5 hover:bg-indigo-50 transition-colors"><div className="w-12 h-12 rounded-xl bg-white text-indigo-600 flex items-center justify-center shadow-sm shrink-0"><PlayCircle className="w-6 h-6" /></div><div className="flex-1 min-w-0"><div className="text-xs font-bold text-indigo-600 mb-0.5">המשך מהנקודה האחרונה</div><div className="font-bold text-slate-900 truncate">{continueLesson.title}</div><div className="text-xs text-slate-500 truncate">{continueLesson.category_name}</div></div><ArrowLeft className="w-5 h-5 text-indigo-500 group-hover:-translate-x-1 transition-transform" /></Link>}

      {isLoading && <div className="space-y-4"><Skeleton className="h-14 w-full" /><Skeleton className="h-44 w-full" /><Skeleton className="h-44 w-full" /></div>}
      {isError && <Alert variant="error">לא הצלחנו לטעון את התוכן. נסו לרענן את הדף.</Alert>}
      {categories.length === 0 && !isLoading && !isError && <EmptyState icon={<BookOpen className="w-7 h-7" />} title="אין עדיין תוכן זמין ללמידה" description="בקרוב יתווספו כאן קטגוריות ושיעורים חדשים." />}

      {categories.length > 0 && <>
        <section>
          <LearningCenterToolbar query={query} difficulty={difficulty} onQueryChange={setQuery} onDifficultyChange={setDifficulty} resultCount={filteredLessons.length} />
          {filteredLessons.length > 0 && <section className="mt-5"><div className="flex items-center justify-between mb-4"><div><h2 className="text-xl font-extrabold text-slate-900">השיעורים</h2><p className="text-sm text-slate-500 mt-1">בחר שיעור והתקדם בקצב שלך</p></div></div><div className="grid grid-cols-1 xl:grid-cols-2 gap-3">{filteredLessons.map((lesson, index) => <LessonCard key={lesson.id} lesson={lesson} index={index} progress={progressMap.get(lesson.id)} />)}</div></section>}
          {filteredLessons.length === 0 && <EmptyState icon={<BookOpen className="w-7 h-7" />} title="לא מצאנו שיעורים מתאימים" description="נסו לשנות את החיפוש או את רמת הקושי." action={<button type="button" onClick={() => { setQuery(''); setDifficulty('all'); }} className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700">נקה סינון</button>} />}
        </section>

        {!query && difficulty === 'all' && <section className="pt-2"><div className="flex items-end justify-between mb-4"><div><h2 className="text-xl font-extrabold text-slate-900">תחומי הלמידה</h2><p className="text-sm text-slate-500 mt-1">העמק לפי התחום שמעניין אותך</p></div></div><div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">{categories.map((category, index) => <CategoryCard key={category.id} category={category} index={index} compact />)}</div></section>}

        <div id="question-bank" className="pt-6"><QuestionBankBrowser categories={categories} /></div>
      </>}
    </div>
  );
}
