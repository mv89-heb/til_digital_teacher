'use client';

import Link from 'next/link';
import { ArrowLeft, BookOpen, ListChecks, Trophy } from 'lucide-react';

const steps = [
  {
    number: '01',
    title: 'לומדים את השיטה',
    description: 'הסברים, דוגמאות פתורות, שיטות מהירות וטעויות נפוצות לפי תחום ורמה.',
    href: '#lessons',
    label: 'לשיעורים',
    icon: BookOpen,
    tone: 'indigo',
  },
  {
    number: '02',
    title: 'מתרגלים מהמאגר',
    description: 'תרגול ממוקד מתוך מאגר השאלות המרכזי, עם משוב ומעקב אחר הדיוק.',
    href: '/practice',
    label: 'להתחיל לתרגל',
    icon: ListChecks,
    tone: 'emerald',
  },
  {
    number: '03',
    title: 'בודקים מוכנות',
    description: 'סימולציה מלאה עם פרקים מתוזמנים, נעילה אוטומטית וציון 200–800.',
    href: '/exam',
    label: 'לסימולציות',
    icon: Trophy,
    tone: 'amber',
  },
] as const;

const toneClasses = {
  indigo: { box: 'bg-indigo-50 text-indigo-600', link: 'text-indigo-600' },
  emerald: { box: 'bg-emerald-50 text-emerald-600', link: 'text-emerald-600' },
  amber: { box: 'bg-amber-50 text-amber-600', link: 'text-amber-600' },
};

export default function LearningRoadmap() {
  return (
    <section id="roadmap" className="scroll-mt-24 space-y-4" dir="rtl">
      <div>
        <div className="text-xs font-bold text-indigo-600 mb-1">איך מתקדמים</div>
        <h2 className="text-2xl font-extrabold text-slate-900">מסלול הכנה למבחן</h2>
        <p className="text-sm text-slate-500 mt-1">הסדר המומלץ: ללמוד, לתרגל ורק אחר כך למדוד את עצמך בסימולציה.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {steps.map((step) => {
          const Icon = step.icon;
          const tone = toneClasses[step.tone];
          return (
            <Link key={step.number} href={step.href} className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md">
              <div className="flex items-center justify-between">
                <span className={`flex h-11 w-11 items-center justify-center rounded-xl ${tone.box}`}><Icon className="h-5 w-5" /></span>
                <span className="text-xs font-black text-slate-400">{step.number}</span>
              </div>
              <h3 className="mt-4 font-black text-slate-900">{step.title}</h3>
              <p className="mt-1 text-sm leading-6 text-slate-500">{step.description}</p>
              <span className={`mt-4 inline-flex items-center gap-1 text-sm font-bold ${tone.link}`}>{step.label} <ArrowLeft className="h-4 w-4 transition group-hover:-translate-x-1" /></span>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
