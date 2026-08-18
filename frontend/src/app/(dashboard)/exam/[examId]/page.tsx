'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, Brain, CheckCircle2, Clock3, FileText, Lock, Play, ShieldCheck, TimerReset } from 'lucide-react';
import { getExams } from '@/lib/api';
import { useAuthStore } from '@/store/useAuthStore';
import ExamSimulation from '@/components/exam/ExamSimulation';
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

export default function ExamPage() {
  const params = useParams<{ examId: string }>();
  const examId = Number(params?.examId);
  const token = useAuthStore((state) => state.token);
  const [started, setStarted] = useState(false);

  const query = useQuery({
    queryKey: ['exam-catalog'],
    queryFn: () => getExams(token as string),
    enabled: !!token && Number.isInteger(examId) && examId > 0,
  });

  if (!Number.isInteger(examId) || examId <= 0) {
    return <div className="p-8 text-center text-rose-600">מזהה סימולציה לא תקין.</div>;
  }

  if (started) return <ExamSimulation examId={examId} />;

  if (query.isLoading) {
    return <div className="mx-auto max-w-5xl space-y-5 p-6"><Skeleton className="h-28 w-full rounded-3xl" /><Skeleton className="h-[520px] w-full rounded-3xl" /></div>;
  }

  if (query.isError) {
    return <div className="mx-auto max-w-5xl p-6"><Alert variant="error">לא הצלחנו לטעון את פרטי הסימולציה. נסה לרענן את הדף.</Alert></div>;
  }

  const exam = (query.data ?? []).find((item) => item.id === examId);

  if (!exam) {
    return <div className="mx-auto max-w-3xl p-6" dir="rtl"><Card className="p-10 text-center"><FileText className="mx-auto h-10 w-10 text-slate-300" /><h1 className="mt-4 text-2xl font-black">הסימולציה לא נמצאה</h1><p className="mt-2 text-slate-500">ייתכן שהיא עדיין לא פורסמה או שאינה זמינה כרגע.</p><Link href="/exam" className="mt-6 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 font-bold text-white">חזרה לסימולציות <ArrowRight className="h-4 w-4" /></Link></Card></div>;
  }

  return (
    <main className="mx-auto max-w-5xl space-y-6 p-4 pb-12 md:p-6" dir="rtl">
      <div className="flex items-center justify-between gap-3">
        <Link href="/exam" className="inline-flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-indigo-600"><ArrowRight className="h-4 w-4" /> חזרה לסימולציות</Link>
      </div>

      <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-slate-950 via-indigo-950 to-blue-900 p-7 text-white shadow-xl md:p-9">
        <div className="absolute -left-20 -top-24 h-64 w-64 rounded-full bg-indigo-400/10 blur-3xl" />
        <div className="absolute -bottom-24 right-20 h-72 w-72 rounded-full bg-blue-400/10 blur-3xl" />
        <div className="relative">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-xs font-bold text-indigo-100"><Brain className="h-3.5 w-3.5" /> סימולציה מלאה</div>
          <h1 className="mt-4 text-3xl font-black tracking-tight md:text-4xl">{exam.name}</h1>
          {exam.description && <p className="mt-3 max-w-3xl leading-7 text-indigo-100">{exam.description}</p>}
          <div className="mt-7 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-2xl border border-white/10 bg-white/10 p-4"><Clock3 className="h-5 w-5" /><div className="mt-2 text-xs text-indigo-200">זמן כולל</div><div className="text-lg font-black">{formatMinutes(exam.duration_seconds)} דק׳</div></div>
            <div className="rounded-2xl border border-white/10 bg-white/10 p-4"><FileText className="h-5 w-5" /><div className="mt-2 text-xs text-indigo-200">שאלות</div><div className="text-lg font-black">{exam.question_count}</div></div>
            <div className="rounded-2xl border border-white/10 bg-white/10 p-4"><TimerReset className="h-5 w-5" /><div className="mt-2 text-xs text-indigo-200">פרקים</div><div className="text-lg font-black">{exam.section_count}</div></div>
            <div className="rounded-2xl border border-white/10 bg-white/10 p-4"><ShieldCheck className="h-5 w-5" /><div className="mt-2 text-xs text-indigo-200">שמירה</div><div className="text-lg font-black">בשרת</div></div>
          </div>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <Card className="p-6 md:p-7">
          <div className="flex items-center justify-between gap-3"><div><h2 className="text-xl font-black text-slate-900">מבנה הסימולציה</h2><p className="mt-1 text-sm text-slate-500">כל פרק מתוזמן וננעל לאחר שהזמן שלו מסתיים.</p></div><Lock className="h-5 w-5 text-slate-300" /></div>
          <div className="mt-6 space-y-3">
            {exam.sections.map((section, index) => (
              <div key={`${exam.id}-${section.name}`} className="rounded-2xl border border-slate-200 p-4 transition hover:border-indigo-200 hover:bg-indigo-50/30">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-50 font-black text-indigo-700">{index + 1}</div>
                  <div className="min-w-0 flex-1"><div className="font-black text-slate-900">{categoryLabels[section.category] ?? section.name}</div><div className="mt-1 text-xs text-slate-500">{section.question_count} שאלות · {formatMinutes(section.duration_seconds)} דקות</div></div>
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="h-fit p-6 md:p-7">
          <div className="rounded-2xl bg-amber-50 p-4 text-sm leading-6 text-amber-900">
            <div className="font-black">לפני שמתחילים</div>
            <ul className="mt-2 list-disc space-y-1 pr-5">
              <li>ודא שיש לך זמן רצוף לכל הסימולציה.</li>
              <li>בסיום פרק לא ניתן לחזור אליו.</li>
              <li>התשובות נשמרות בצד השרת.</li>
              <li>אפשר לנווט בין שאלות בתוך הפרק.</li>
            </ul>
          </div>
          <button onClick={() => setStarted(true)} className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-indigo-600 px-5 py-4 text-base font-black text-white shadow-lg shadow-indigo-200 transition hover:-translate-y-0.5 hover:bg-indigo-700">
            <Play className="h-5 w-5 fill-current" /> אני מוכן — התחל סימולציה
          </button>
          <p className="mt-3 text-center text-xs leading-5 text-slate-400">הטיימר מתחיל רק לאחר הלחיצה על הכפתור.</p>
        </Card>
      </div>
    </main>
  );
}
