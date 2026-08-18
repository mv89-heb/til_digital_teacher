'use client';

import { useEffect, useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight, Filter, Search } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getQuestionBank } from '@/lib/api';
import { useAuthStore } from '@/store/useAuthStore';
import type { Category, Question } from '@/types/learning';
import Card from '@/components/ui/Card';
import Skeleton from '@/components/ui/Skeleton';
import Alert from '@/components/ui/Alert';

const PAGE_SIZE_OPTIONS = [24, 60];

function difficultyLabel(value: Question['difficulty']) {
  return value === 'easy' ? 'קל' : value === 'medium' ? 'בינוני' : 'בחינה';
}

function difficultyClass(value: Question['difficulty']) {
  return value === 'easy'
    ? 'bg-emerald-50 text-emerald-700'
    : value === 'medium'
      ? 'bg-amber-50 text-amber-700'
      : 'bg-violet-50 text-violet-700';
}

export default function QuestionBankBrowser({ categories }: { categories: Category[] }) {
  const { token } = useAuthStore();
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(60);
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
    queryKey: ['question-bank', token, categoryId, difficulty, page, perPage, search],
    queryFn: () => getQuestionBank(token as string, { categoryId, difficulty, page, perPage, search }),
    enabled: !!token,
    placeholderData: (previous) => previous,
  });

  const data = query.data;
  const currentCategory = useMemo(() => categories.find((category) => category.id === categoryId), [categories, categoryId]);

  return (
    <section className="space-y-4" dir="rtl">
      <Card className="p-4">
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-black text-slate-900">מאגר השאלות המלא</h2>
              <p className="mt-1 text-sm text-slate-500">עיון בכל השאלות שפורסמו במערכת, עם חיפוש וסינון.</p>
            </div>
            {data && (
              <div className="rounded-xl bg-indigo-50 px-3 py-2 text-sm font-extrabold text-indigo-700">
                {data.total.toLocaleString('he-IL')} שאלות נמצאו
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
            <label className="relative md:col-span-2">
              <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="חיפוש בשאלה, מזהה, נושא או מיומנות"
                className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-3 pr-9 text-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              />
            </label>

            <label className="relative">
              <Filter className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <select
                value={categoryId ?? ''}
                onChange={(e) => {
                  setCategoryId(e.target.value ? Number(e.target.value) : undefined);
                  setPage(1);
                }}
                className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-3 pr-9 text-sm"
              >
                <option value="">כל הקטגוריות</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>{category.name}</option>
                ))}
              </select>
            </label>

            <select
              value={difficulty ?? ''}
              onChange={(e) => {
                setDifficulty((e.target.value || undefined) as typeof difficulty);
                setPage(1);
              }}
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm"
            >
              <option value="">כל הרמות</option>
              <option value="easy">קל</option>
              <option value="medium">בינוני</option>
              <option value="exam">בחינה</option>
            </select>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-3 text-xs text-slate-500">
            <div className="flex flex-wrap items-center gap-2">
              {currentCategory && <span className="rounded-lg bg-slate-100 px-2.5 py-1.5 font-bold">{currentCategory.name}</span>}
              {search && <span className="rounded-lg bg-slate-100 px-2.5 py-1.5 font-bold">חיפוש: {search}</span>}
              <span>הצגה לעיון בלבד — התשובה הנכונה אינה נחשפת.</span>
            </div>
            <label className="flex items-center gap-2 font-bold text-slate-600">
              שאלות בעמוד:
              <select
                value={perPage}
                onChange={(e) => {
                  setPerPage(Number(e.target.value));
                  setPage(1);
                }}
                className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs"
              >
                {PAGE_SIZE_OPTIONS.map((size) => <option key={size} value={size}>{size}</option>)}
              </select>
            </label>
          </div>
        </div>
      </Card>

      {query.isLoading && (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-64 w-full" />)}
        </div>
      )}

      {query.isError && <Alert variant="error">לא הצלחנו לטעון את מאגר השאלות. נסה לרענן.</Alert>}

      {data && data.questions.length === 0 && (
        <Card className="p-10 text-center text-slate-500">לא נמצאו שאלות לפי הסינון שבחרת.</Card>
      )}

      {data && data.questions.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            {data.questions.map((question, index) => (
              <QuestionCard
                key={question.id}
                question={question}
                number={(data.page - 1) * data.per_page + index + 1}
              />
            ))}
          </div>

          <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-3 sm:flex-row sm:items-center sm:justify-between">
            <button
              disabled={!data.has_previous}
              onClick={() => setPage((p) => p - 1)}
              className="inline-flex items-center justify-center gap-1 rounded-xl px-4 py-2 text-sm font-bold transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronRight className="h-4 w-4" /> הקודם
            </button>
            <div className="text-center text-sm font-bold text-slate-600">
              עמוד {data.page} מתוך {data.total_pages || 1}
              <span className="mr-2 font-normal text-slate-400">• {data.total.toLocaleString('he-IL')} שאלות</span>
            </div>
            <button
              disabled={!data.has_next}
              onClick={() => setPage((p) => p + 1)}
              className="inline-flex items-center justify-center gap-1 rounded-xl px-4 py-2 text-sm font-bold transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              הבא <ChevronLeft className="h-4 w-4" />
            </button>
          </div>
        </>
      )}
    </section>
  );
}

function QuestionCard({ question, number }: { question: Question; number: number }) {
  return (
    <Card className="p-5 transition-shadow hover:shadow-md">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-lg bg-slate-100 px-2 py-1 text-xs font-extrabold text-slate-600">#{number}</span>
          {question.bank_key && (
            <span className="rounded-lg bg-indigo-50 px-2 py-1 text-xs font-bold text-indigo-700">{question.bank_key}</span>
          )}
          <span className={`rounded-lg px-2 py-1 text-xs font-bold ${difficultyClass(question.difficulty)}`}>
            {difficultyLabel(question.difficulty)}
          </span>
          {question.main_category && (
            <span className="rounded-lg bg-slate-50 px-2 py-1 text-xs font-bold text-slate-600">{question.main_category}</span>
          )}
        </div>
        <span className="shrink-0 text-xs text-slate-400">{question.recommended_time_seconds ?? '—'} שנ׳</span>
      </div>

      <div className="mb-3 flex flex-wrap gap-2 text-xs text-slate-500">
        {question.subcategory && <span>{question.subcategory}</span>}
        {question.skill && <span>• {question.skill}</span>}
        {question.difficulty_level && <span>• רמה {question.difficulty_level}/5</span>}
      </div>

      <p className="text-base font-semibold leading-7 text-slate-900 whitespace-pre-wrap">
        {question.body?.body ?? 'שאלה ללא טקסט'}
      </p>

      {question.visual_data && <VisualQuestionData data={question.visual_data} />}

      <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
        {question.answers.map((answer, i) => (
          <div key={answer.id} className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm text-slate-700">
            <span className="ml-2 font-bold">{String.fromCharCode(1488 + i)}.</span>
            {answer.answer_text}
          </div>
        ))}
      </div>
    </Card>
  );
}

function VisualQuestionData({ data }: { data: Record<string, unknown> | string }) {
  const parsed = typeof data === 'string' ? parseJson(data) : data;
  if (!parsed) return null;

  const format = String(parsed.format ?? '');
  const items = Array.isArray(parsed.items) ? parsed.items : [];

  if (format === 'sequence' && items.length > 0) {
    return (
      <div className="mt-4 rounded-2xl border border-indigo-100 bg-indigo-50/40 p-4">
        <div className="mb-3 text-xs font-extrabold uppercase tracking-wide text-indigo-700">תצוגה חזותית</div>
        <div className="flex flex-wrap items-center gap-2" dir="ltr">
          {items.map((item, index) => (
            <div key={`${String(item)}-${index}`} className="flex items-center gap-2">
              <span className={`flex h-12 min-w-12 items-center justify-center rounded-xl border bg-white px-3 text-2xl shadow-sm ${item == null ? 'border-dashed border-indigo-300 text-indigo-500' : 'border-slate-200 text-slate-900'}`}>
                {item == null ? '?' : String(item)}
              </span>
              {index < items.length - 1 && <span className="text-slate-400">→</span>}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <details className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
      <summary className="cursor-pointer font-bold">נתונים חזותיים</summary>
      <pre className="mt-2 overflow-auto whitespace-pre-wrap">{JSON.stringify(parsed, null, 2)}</pre>
    </details>
  );
}

function parseJson(value: string): Record<string, unknown> | null {
  try {
    const parsed = JSON.parse(value) as unknown;
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed as Record<string, unknown> : null;
  } catch {
    return null;
  }
}
