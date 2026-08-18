'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Brain, CheckCircle2, Clock3, FileText, ShieldCheck, Sparkles, TimerReset } from 'lucide-react';
import { getExams } from '@/lib/api';
import { useAuthStore } from '@/store/useAuthStore';
import Card from '@/components/ui/Card';
import Skeleton from '@/components/ui/Skeleton';
import Alert from '@/components/ui/Alert';

function formatMinutes(seconds: number) {
  return Math.max(1, Math.round(seconds / 60));
}

const categoryLabels: Record<string, string> = {
  quantitative: 'כמותי',
  verbal: 'מילולי',
  figural: 'מרחבי וצורני',
  english: 'אנגלית',
  technical: 'טכני',
};

export default function ExamsPage() {
  const token = useAuthStore((state) => state.token);
  const query = useQuery({
    queryKey: ['exam-catalog'],
    queryFn: () => getExams(token as string),
    enabled: !!token,
  });

  if (query.isLoading) {
    return <div className="mx-auto max-w-6xl space-y-5"><Skeleton className="h-56 w-full rounded-3xl" /><Skeleton className="h-80 w-full rounded-3xl" /></div>;
  }

  if (query.isError) {
    return <div className="mx-auto max-w-6xl"><Alert variant="error">לא הצלחנו לטעון את הסימולציות. נסה לרענן את הדף.</Alert></div>;
  }

  const exams = query.data ?? [];

  return (
    <div className="mx-auto max-w-6xl space-y-6 pb-12" dir="rtl">
      <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-slate-950 via-indigo-950 to-blue-900 p-7 text-white shadow-xl">
        <div className="absolute -left-16 -top-20 h-56 w-56 rounded-full bg-indigo-400/10 blur-3xl" />
        <div className="absolute -bottom-24 right-20 h-64 w-64 rounded-full bg-blue-400/10 blur-3xl" />
        <div className="relative grid gap-7 lg:grid-cols-[1fr_360px] lg:items-end">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-xs font-bold text-indigo-100"><Sparkles className="h-3.5 w-3.5" /> מצב סימולציה</div>
            <h1 className="text-3xl font-black tracking-tight md:text-4xl">סימולציות מבחן תיל</h1>
            <p className="mt-3 max-w-2xl leading-7 text-indigo-100">תרגול מלא בתנאי זמן, עם פרקים נפרדים, נעילה אוטומטית של פרקים שהסתיימו וציון מסכם בסולם 200–800.</p>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div className="rounded-2xl border border-white/10 bg-white/10 p-4 text-center"><TimerReset className="mx-auto h-5 w-5" /><div className="mt-2 text-xs text-indigo-100">טיימר</div><div className="font-black">לכל פרק</div></div>
            <div className="rounded-2xl border border-white/10 bg-white/10 p-4 text-center"><ShieldCheck className="mx-auto h-5 w-5" /><div className="mt-2 text-xs text-indigo-100">שמירה</div><div className="font-black">בשרת</div></div>
            <div className="rounded-2xl border border-white/10 bg-white/10 p-4 text-center"><Brain className="mx-auto h-5 w-5" /><div className="mt-2 text-xs text-indigo-100">מבנה</div><div className="font-black">תיל</div></div>
          </div>
        </div>
      </section>

      <div className="flex items-center justify-between gap-3">
        <div><h2 className="text-2xl font-black text-slate-900">בחר סימולציה</h2><p className="mt-1 text-sm text-slate-500">התחל רק כשיש לך זמן רצוף לעבוד לפי מגבלת הזמן.</p></div>
        <Link href="/learn#question-bank" className="hidden items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 hover:bg-slate-50 sm:inline-flex">תרגול לפני מבחן <ArrowLeft className="h-4 w-4" /></Link>
      </div>

      {exams.length === 0 ? (
        <Card className="p-10 text-center">
          <FileText className="mx-auto h-10 w-10 text-slate-300" />
          <h2 className="mt-4 text-xl font-black text-slate-900">אין כרגע סימולציות זמינות</h2>
          <p className="mt-2 text-sm text-slate-500">ברגע שסימולציה תפורסם היא תופיע כאן אוטומטית.</p>
        </Card>
      ) : (
        <div className="grid gap-5 lg:grid-cols-2">
          {exams.map((exam) => (
            <Card key={exam.id} className="overflow-hidden p-0 transition hover:-translate-y-0.5 hover:shadow-lg">
              <div className="border-b border-slate-100 bg-gradient-to-l from-indigo-50 to-white p-6">
                <div className="flex items-start justify-between gap-3"><div><div className="text-xs font-bold text-indigo-600">סימולציה מלאה</div><h3 className="mt-1 text-xl font-black text-slate-900">{exam.name}</h3></div><div className="rounded-xl bg-white p-2.5 text-indigo-600 shadow-sm"><FileText className="h-5 w-5" /></div></div>
                {exam.description && <p className="mt-3 text-sm leading-6 text-slate-600">{exam.description}</p>}
              </div>
              <div className="space-y-5 p-6">
                <div className="grid grid-cols-3 gap-2">
                  <div className="rounded-xl bg-slate-50 p-3 text-center"><Clock3 className="mx-auto h-4 w-4 text-slate-400" /><div className="mt-1 text-lg font-black text-slate-900">{formatMinutes(exam.duration_seconds)}</div><div className="text-[11px] text-slate-500">דקות</div></div>
                  <div className="rounded-xl bg-slate-50 p-3 text-center"><FileText className="mx-auto h-4 w-4 text-slate-400" /><div className="mt-1 text-lg font-black text-slate-900">{exam.question_count}</div><div className="text-[11px] text-slate-500">שאלות</div></div>
                  <div className="rounded-xl bg-slate-50 p-3 text-center"><CheckCircle2 className="mx-auto h-4 w-4 text-slate-400" /><div className="mt-1 text-lg font-black text-slate-900">{exam.section_count}</div><div className="text-[11px] text-slate-500">פרקים</div></div>
                </div>
                <div className="space-y-2">
                  {exam.sections.map((section) => <div key={`${exam.id}-${section.name}`} className="flex items-center justify-between rounded-xl border border-slate-100 px-3 py-2.5 text-sm"><span className="font-bold text-slate-700">{categoryLabels[section.category] ?? section.name}</span><span className="text-slate-500">{section.question_count} שאלות · {formatMinutes(section.duration_seconds)} דק׳</span></div>)}
                </div>
                <Link href={`/exam/${exam.id}`} className="flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-black text-white transition hover:bg-indigo-700">התחל סימולציה <ArrowLeft className="h-4 w-4" /></Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
