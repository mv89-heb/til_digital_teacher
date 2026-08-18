'use client';

import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Brain, Filter, RefreshCw, Sparkles, Target, Zap, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import Alert from '@/components/ui/Alert';
import EmptyState from '@/components/ui/EmptyState';
import Skeleton from '@/components/ui/Skeleton';
import Card from '@/components/ui/Card';
import QuestionBlock from '@/components/practice/QuestionBlock';
import { getCategories, getPracticeQuestions, getDashboard } from '@/lib/api';
import { useAuthStore } from '@/store/useAuthStore';

type Difficulty = 'all' | 'easy' | 'medium' | 'exam';
type CategoryOption = { id: number; name: string; type: string };

const difficultyLabels: Record<Difficulty, string> = {
  all: 'כל הרמות', easy: 'קל', medium: 'בינוני', exam: 'רמת מבחן',
};

export default function PracticePage() {
  const { token } = useAuthStore();
  const [categoryId, setCategoryId] = useState<number | undefined>();
  const [difficulty, setDifficulty] = useState<Difficulty>('all');
  const [mode, setMode] = useState<'all' | 'adaptive'>('adaptive');
  const [refreshKey, setRefreshKey] = useState(0);

  const categoriesQuery = useQuery({ queryKey: ['categories'], queryFn: getCategories });
  const dashboardQuery = useQuery({ queryKey: ['dashboard'], queryFn: () => getDashboard(token as string), enabled: !!token, staleTime: 30_000 });
  const categories = useMemo<CategoryOption[]>(() => (categoriesQuery.data ?? []).map((category) => ({ id: category.id, name: category.name, type: category.type })), [categoriesQuery.data]);

  const questionsQuery = useQuery({
    queryKey: ['practice-questions', token, categoryId, difficulty, mode, refreshKey],
    queryFn: () => getPracticeQuestions(token as string, { categoryId, difficulty: difficulty === 'all' ? undefined : difficulty, limit: 50, mode }),
    enabled: !!token,
  });

  const selectedDifficulty = questionsQuery.data?.target_difficulty;
  const accuracy = dashboardQuery.data?.stats.overall_accuracy_percent ?? 0;
  const attempted = dashboardQuery.data?.stats.total_questions_attempted ?? 0;

  return (
    <div className="max-w-6xl mx-auto pb-12 space-y-6">
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-l from-slate-950 via-indigo-950 to-indigo-700 p-6 sm:p-8 text-white shadow-xl shadow-indigo-100">
        <div className="absolute -left-20 -top-20 h-56 w-56 rounded-full bg-indigo-400/20 blur-3xl" />
        <div className="absolute -right-10 -bottom-24 h-64 w-64 rounded-full bg-blue-400/20 blur-3xl" />
        <div className="relative flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-bold text-indigo-100 mb-4"><Brain className="w-3.5 h-3.5" /> אימון חכם</div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2">תרגול שאלות</h1>
            <p className="max-w-2xl text-indigo-100 leading-relaxed">תרגל מהמאגר המרכזי, קבל משוב מידי, וחזק בדיוק את התחומים שבהם אתה צריך להשתפר.</p>
          </div>
          <Link href="/learn#question-bank" className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-indigo-700 shadow-lg hover:bg-indigo-50 shrink-0"><Target className="w-4 h-4" /> עיון במאגר המלא <ArrowLeft className="w-4 h-4" /></Link>
        </div>
      </section>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <Card className="p-4 sm:p-5"><div className="text-xs font-bold text-slate-500">דיוק נוכחי</div><div className="mt-1 text-2xl font-black text-indigo-700">{accuracy}%</div></Card>
        <Card className="p-4 sm:p-5"><div className="text-xs font-bold text-slate-500">שאלות שנפתרו</div><div className="mt-1 text-2xl font-black text-slate-900">{attempted.toLocaleString('he-IL')}</div></Card>
        <Card className="p-4 sm:p-5"><div className="text-xs font-bold text-slate-500">מצב תרגול</div><div className="mt-1 text-lg font-black text-emerald-700">{mode === 'adaptive' ? 'אדפטיבי' : 'חופשי'}</div></Card>
        <Card className="p-4 sm:p-5"><div className="text-xs font-bold text-slate-500">יעד הסשן</div><div className="mt-1 text-lg font-black text-amber-700">50 שאלות</div></Card>
      </div>

      <Card className="p-4 md:p-5">
        <div className="flex items-center justify-between gap-3 mb-4"><div className="flex items-center gap-2 font-extrabold text-slate-900"><Filter className="w-4 h-4 text-indigo-600" /> בניית אימון</div><span className="text-xs text-slate-400">הסינון משפיע על הסשן הבא</span></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <label className="text-sm text-slate-600"><span className="block mb-1 font-medium">תחום</span><select value={categoryId ?? ''} onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : undefined)} className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-slate-800"><option value="">כל התחומים</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label>
          <label className="text-sm text-slate-600"><span className="block mb-1 font-medium">רמת קושי</span><select value={difficulty} onChange={(e) => setDifficulty(e.target.value as Difficulty)} className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-slate-800">{(Object.keys(difficultyLabels) as Difficulty[]).map((key) => <option key={key} value={key}>{difficultyLabels[key]}</option>)}</select></label>
          <label className="text-sm text-slate-600"><span className="block mb-1 font-medium">אסטרטגיית בחירה</span><select value={mode} onChange={(e) => setMode(e.target.value as 'all' | 'adaptive')} className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-slate-800"><option value="adaptive">אדפטיבי — התאמה לרמה</option><option value="all">חופשי — כל השאלות</option></select></label>
        </div>
        {mode === 'adaptive' && selectedDifficulty && <div className="mt-4 flex items-center gap-2 text-sm text-indigo-700 bg-indigo-50 rounded-xl px-3 py-2"><Sparkles className="w-4 h-4" /> רמת היעד שנבחרה: <strong>{difficultyLabels[selectedDifficulty]}</strong></div>}
      </Card>

      {questionsQuery.isLoading && <div className="space-y-5"><Skeleton className="h-72 w-full" /><Skeleton className="h-72 w-full" /></div>}
      {questionsQuery.isError && <Alert variant="error">לא הצלחנו לטעון את שאלות התרגול. נסו לרענן את הסשן.</Alert>}

      {questionsQuery.data && questionsQuery.data.questions.length === 0 && <EmptyState icon={<Brain className="w-7 h-7" />} title="לא נמצאו שאלות" description="אין כרגע שאלות התואמות את הסינון שבחרתם. נסו תחום או רמת קושי אחרת." />}

      {questionsQuery.data && questionsQuery.data.questions.length > 0 && (
        <section className="space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-2xl border border-indigo-100 bg-indigo-50/60 p-4">
            <div><div className="font-extrabold text-slate-900">סשן תרגול פעיל</div><div className="text-sm text-slate-500 mt-0.5">{questionsQuery.data.count} שאלות נטענו · הסבר יופיע לאחר בדיקת התשובה</div></div>
            <button onClick={() => setRefreshKey((value) => value + 1)} disabled={questionsQuery.isFetching} className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-bold text-white hover:bg-slate-800 disabled:opacity-50"><RefreshCw className={`w-4 h-4 ${questionsQuery.isFetching ? 'animate-spin' : ''}`} /> אימון חדש</button>
          </div>
          {questionsQuery.data.questions.map((question, index) => <section key={question.id} className="relative"><div className="absolute -right-3 top-5 z-10 w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center text-sm font-bold shadow-md">{index + 1}</div><QuestionBlock question={question} token={token} /></section>)}
        </section>
      )}

      <Card className="p-5 bg-gradient-to-l from-white to-slate-50">
        <div className="flex items-center gap-3"><div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center"><Zap className="w-5 h-5" /></div><div><div className="font-bold text-slate-900">טיפ לאימון</div><div className="text-sm text-slate-500">אל תחפש רק תשובה נכונה — אחרי כל טעות עצור להבין איזה כלל או דפוס היה חסר.</div></div></div>
      </Card>
    </div>
  );
}
