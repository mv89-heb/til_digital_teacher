'use client';

import { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Database, Filter, Search } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getQuestionBank } from '@/lib/api';
import { useAuthStore } from '@/store/useAuthStore';
import type { Category, Question } from '@/types/learning';
import Card from '@/components/ui/Card';
import Skeleton from '@/components/ui/Skeleton';
import Alert from '@/components/ui/Alert';

function difficultyLabel(value: Question['difficulty']) {
  return value === 'easy' ? 'קל' : value === 'medium' ? 'בינוני' : 'בחינה';
}

export default function QuestionBankBrowser({ categories }: { categories: Category[] }) {
  const { token } = useAuthStore();
  const [page, setPage] = useState(1);
  const [categoryId, setCategoryId] = useState<number | undefined>();
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'exam' | undefined>();
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const query = useQuery({
    queryKey: ['question-bank', token, categoryId, difficulty, page, search],
    queryFn: () => getQuestionBank(token as string, { categoryId, difficulty, page, perPage: 24, search }),
    enabled: !!token,
    placeholderData: (previous) => previous,
  });

  const data = query.data;

  return (
    <section className="space-y-4">
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1.5 text-xs font-bold text-indigo-700 mb-2">
            <Database className="w-3.5 h-3.5" /> מאגר השאלות המלא
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900">כל השאלות שהמערכת מכירה</h2>
          <p className="text-sm text-slate-500 mt-1">עיון בכל השאלות, לפי קטגוריה ורמת קושי. התשובה הנכונה אינה חשופה מראש.</p>
        </div>
        {data && <div className="text-sm font-bold text-slate-600">{data.total} שאלות זמינות</div>}
      </div>

      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <label className="relative md:col-span-1">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input value={searchInput} onChange={(e) => setSearchInput(e.target.value)} placeholder="חיפוש בשאלה, נושא או מיומנות" className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pr-9 pl-3 text-sm outline-none focus:border-indigo-500" />
          </label>
          <label className="relative">
            <Filter className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <select value={categoryId ?? ''} onChange={(e) => { setCategoryId(e.target.value ? Number(e.target.value) : undefined); setPage(1); }} className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pr-9 pl-3 text-sm">
              <option value="">כל הקטגוריות</option>
              {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
            </select>
          </label>
          <select value={difficulty ?? ''} onChange={(e) => { setDifficulty((e.target.value || undefined) as typeof difficulty); setPage(1); }} className="w-full rounded-xl border border-slate-200 bg-white py-2.5 px-3 text-sm">
            <option value="">כל הרמות</option>
            <option value="easy">קל</option>
            <option value="medium">בינוני</option>
            <option value="exam">בחינה</option>
          </select>
        </div>
      </Card>

      {query.isLoading && <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-56 w-full" />)}</div>}
      {query.isError && <Alert variant="error">לא הצלחנו לטעון את מאגר השאלות. נסה לרענן.</Alert>}

      {data && data.questions.length === 0 && <Card className="p-10 text-center text-slate-500">לא נמצאו שאלות לפי הסינון שבחרת.</Card>}

      {data && data.questions.length > 0 && (
        <>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {data.questions.map((question, index) => (
              <QuestionCard key={question.id} question={question} number={(data.page - 1) * data.per_page + index + 1} />
            ))}
          </div>

          <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-3">
            <button disabled={!data.has_previous} onClick={() => setPage((p) => p - 1)} className="inline-flex items-center gap-1 rounded-xl px-3 py-2 text-sm font-bold disabled:opacity-40 hover:bg-slate-50"><ChevronRight className="w-4 h-4" /> הקודם</button>
            <div className="text-sm font-bold text-slate-600">עמוד {data.page} מתוך {data.total_pages}</div>
            <button disabled={!data.has_next} onClick={() => setPage((p) => p + 1)} className="inline-flex items-center gap-1 rounded-xl px-3 py-2 text-sm font-bold disabled:opacity-40 hover:bg-slate-50">הבא <ChevronLeft className="w-4 h-4" /></button>
          </div>
        </>
      )}
    </section>
  );
}

function QuestionCard({ question, number }: { question: Question; number: number }) {
  return (
    <Card className="p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-lg bg-slate-100 px-2 py-1 text-xs font-extrabold text-slate-600">#{number}</span>
          {question.bank_key && <span className="rounded-lg bg-indigo-50 px-2 py-1 text-xs font-bold text-indigo-700">{question.bank_key}</span>}
          <span className="rounded-lg bg-amber-50 px-2 py-1 text-xs font-bold text-amber-700">{difficultyLabel(question.difficulty)}</span>
        </div>
        <span className="text-xs text-slate-400">{question.recommended_time_seconds ?? '—'} שנ׳</span>
      </div>
      <div className="flex flex-wrap gap-2 mb-3 text-xs text-slate-500">
        {question.subcategory && <span>{question.subcategory}</span>}
        {question.skill && <span>• {question.skill}</span>}
      </div>
      <p className="text-base font-semibold leading-7 text-slate-900 whitespace-pre-wrap">{question.body?.body ?? 'שאלה ללא טקסט'}</p>
      {question.visual_data && <div className="mt-3 rounded-xl bg-slate-50 p-3 text-xs text-slate-600 overflow-auto">{typeof question.visual_data === 'string' ? question.visual_data : JSON.stringify(question.visual_data)}</div>}
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2">
        {question.answers.map((answer, i) => <div key={answer.id} className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm text-slate-700"><span className="font-bold ml-2">{String.fromCharCode(1488 + i)}.</span>{answer.answer_text}</div>)}
      </div>
    </Card>
  );
}
