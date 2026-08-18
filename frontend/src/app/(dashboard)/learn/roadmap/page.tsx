'use client';

import Link from 'next/link';
import { ArrowRight, Sparkles } from 'lucide-react';
import LearningRoadmap from '@/components/learning/LearningRoadmap';

export default function LearningRoadmapPage() {
  return (
    <main className="mx-auto max-w-6xl space-y-6 pb-12" dir="rtl">
      <div className="flex items-center gap-3 text-sm text-slate-500">
        <Link href="/learn" className="font-bold hover:text-indigo-600">מרכז הלימוד</Link>
        <ArrowRight className="h-4 w-4" />
        <span>מסלול הכנה</span>
      </div>
      <section className="rounded-3xl bg-gradient-to-l from-slate-950 via-indigo-950 to-blue-900 p-7 text-white shadow-xl">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-xs font-bold text-indigo-100"><Sparkles className="h-3.5 w-3.5" /> מסלול הכנה</div>
        <h1 className="mt-4 text-3xl font-black tracking-tight">כך מתכוננים נכון למבחן תיל</h1>
        <p className="mt-3 max-w-3xl leading-7 text-indigo-100">במקום לקפוץ ישר לסימולציות, המערכת בנויה סביב שלושה שלבים: בניית ידע, תרגול ממוקד ומדידת מוכנות בתנאי מבחן.</p>
      </section>
      <LearningRoadmap />
      <div className="rounded-2xl border border-indigo-100 bg-indigo-50 p-5 text-sm leading-7 text-indigo-950">
        <strong>המלצה:</strong> אחרי כל שיעור עבור לכמה שאלות מאותו תחום. כאשר הדיוק מתייצב, עבור לסימולציה מלאה כדי לבדוק גם מהירות וגם עמידה בזמני הפרקים.
      </div>
    </main>
  );
}
