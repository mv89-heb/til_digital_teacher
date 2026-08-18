'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, BookOpen, CheckCircle2, Target, Zap, ArrowLeft, ClipboardCheck, Brain, Sparkles } from 'lucide-react';
import { getDashboard } from '@/lib/api';
import { useAuthStore } from '@/store/useAuthStore';
import Card from '@/components/ui/Card';
import Skeleton from '@/components/ui/Skeleton';
import Alert from '@/components/ui/Alert';
import EmptyState from '@/components/ui/EmptyState';
import ProgressTrack from '@/components/dashboard/ProgressTrack';
import StatsCard from '@/components/dashboard/StatsCard';
import CategoryProgressCard from '@/components/dashboard/CategoryProgressCard';
import ContinueLearningCard from '@/components/dashboard/ContinueLearningCard';
import ProgressChart from '@/components/dashboard/ProgressChart';

export default function DashboardPage() {
  const { token, user } = useAuthStore();

  const { data: dashboard, isLoading, isError } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => getDashboard(token as string),
    enabled: !!token,
  });

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <Skeleton className="h-32 w-full rounded-3xl" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-28 w-full rounded-2xl" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-72 w-full rounded-3xl" />
          <Skeleton className="h-72 w-full rounded-3xl" />
        </div>
      </div>
    );
  }

  if (isError || !dashboard) {
    return (
      <div className="max-w-7xl mx-auto">
        <Alert variant="error">לא הצלחנו לטעון את לוח הבקרה. נסו לרענן את הדף.</Alert>
      </div>
    );
  }

  const hasCategories = dashboard.categories.length > 0;
  const accuracy = dashboard.stats.overall_accuracy_percent;
  const readiness = Math.min(100, Math.round(accuracy * 0.85 + Math.min(dashboard.stats.total_questions_attempted / 2, 15)));

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-8">
      <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-slate-950 via-indigo-950 to-blue-900 p-6 md:p-8 text-white shadow-xl shadow-indigo-100">
        <div className="absolute -top-20 -left-20 w-64 h-64 rounded-full bg-blue-400/10 blur-3xl" />
        <div className="absolute -bottom-24 right-20 w-72 h-72 rounded-full bg-indigo-400/10 blur-3xl" />
        <div className="relative flex flex-col lg:flex-row lg:items-center lg:justify-between gap-7">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 border border-white/10 px-3 py-1.5 text-xs font-bold text-indigo-100 mb-4">
              <Sparkles className="w-3.5 h-3.5" />
              מסלול ההכנה האישי שלך
            </div>
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-2">
              שלום, {user?.email?.split('@')[0] || 'תלמיד'} 👋
            </h1>
            <p className="text-indigo-100 leading-relaxed">
              {hasCategories ? 'המשך מהנקודה האחרונה וחזק את התחומים שיתנו לך את השיפור הגדול ביותר.' : 'התחל את המסלול שלך ונתאים את התרגול לרמה שלך.'}
            </p>
          </div>

          <div className="w-full lg:w-80 rounded-3xl bg-white/10 border border-white/10 backdrop-blur p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-indigo-100">מוכנות משוערת למבחן</span>
              <span className="text-2xl font-extrabold">{readiness}%</span>
            </div>
            <div className="h-2.5 rounded-full bg-white/10 overflow-hidden">
              <div className="h-full rounded-full bg-white transition-all" style={{ width: `${readiness}%` }} />
            </div>
            <p className="text-xs text-indigo-200 mt-3">המדד משתפר ככל שאתה מתרגל שאלות ומסיים שיעורים.</p>
          </div>
        </div>
      </section>

      {!hasCategories ? (
        <EmptyState
          icon={<BookOpen className="w-7 h-7" />}
          title="עדיין לא התחלת ללמוד"
          description="עברו למרכז הלימוד כדי להתחיל את השיעור הראשון שלכם."
          action={
            <Link href="/learn" className="px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold hover:bg-indigo-700 transition-colors inline-block">
              למרכז הלימוד
            </Link>
          }
        />
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Link href="/practice" className="group rounded-2xl bg-white border border-slate-200 p-5 shadow-sm hover:-translate-y-1 hover:shadow-lg hover:border-indigo-200 transition-all">
              <div className="flex items-start justify-between">
                <span className="w-11 h-11 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center"><Brain className="w-5 h-5" /></span>
                <ArrowLeft className="w-5 h-5 text-slate-300 group-hover:text-indigo-500 group-hover:-translate-x-1 transition-all" />
              </div>
              <h3 className="font-extrabold text-slate-900 mt-4">תרגול חכם</h3>
              <p className="text-sm text-slate-500 mt-1">שאלות לפי הרמה וההתקדמות שלך.</p>
            </Link>

            <Link href="/exam" className="group rounded-2xl bg-white border border-slate-200 p-5 shadow-sm hover:-translate-y-1 hover:shadow-lg hover:border-blue-200 transition-all">
              <div className="flex items-start justify-between">
                <span className="w-11 h-11 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center"><ClipboardCheck className="w-5 h-5" /></span>
                <ArrowLeft className="w-5 h-5 text-slate-300 group-hover:text-blue-500 group-hover:-translate-x-1 transition-all" />
              </div>
              <h3 className="font-extrabold text-slate-900 mt-4">סימולציה</h3>
              <p className="text-sm text-slate-500 mt-1">תרגל בתנאי זמן ובמבנה של מבחן.</p>
            </Link>

            <Link href="/learn" className="group rounded-2xl bg-white border border-slate-200 p-5 shadow-sm hover:-translate-y-1 hover:shadow-lg hover:border-emerald-200 transition-all">
              <div className="flex items-start justify-between">
                <span className="w-11 h-11 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center"><BookOpen className="w-5 h-5" /></span>
                <ArrowLeft className="w-5 h-5 text-slate-300 group-hover:text-emerald-500 group-hover:-translate-x-1 transition-all" />
              </div>
              <h3 className="font-extrabold text-slate-900 mt-4">המשך ללמוד</h3>
              <p className="text-sm text-slate-500 mt-1">חזור לשיעור הבא במסלול שלך.</p>
            </Link>
          </div>

          <Card className="p-5 sm:p-6">
            <ProgressTrack stats={dashboard.stats} />
          </Card>

          {dashboard.continue_learning && <ContinueLearningCard lesson={dashboard.continue_learning} />}

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatsCard icon={<Zap className="w-5 h-5" />} label="נקודות XP" value={dashboard.xp_total} accent="amber" />
            <StatsCard icon={<Target className="w-5 h-5" />} label="אחוז הצלחה כללי" value={`${accuracy}%`} accent="indigo" />
            <StatsCard icon={<CheckCircle2 className="w-5 h-5" />} label="שיעורים שהושלמו" value={`${dashboard.stats.total_lessons_completed}/${dashboard.stats.total_lessons_available}`} accent="emerald" />
            <StatsCard icon={<BarChart3 className="w-5 h-5" />} label="שאלות שנענו" value={dashboard.stats.total_questions_attempted} accent="rose" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-5 sm:p-6 rounded-3xl">
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h2 className="font-extrabold text-slate-900">הביצועים שלך</h2>
                  <p className="text-sm text-slate-500 mt-0.5">הצלחה לפי תחום</p>
                </div>
                <BarChart3 className="w-5 h-5 text-slate-300" />
              </div>
              <ProgressChart categories={dashboard.categories} />
            </Card>

            <Card className="p-5 sm:p-6 rounded-3xl">
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h2 className="font-extrabold text-slate-900">התקדמות לפי תחום</h2>
                  <p className="text-sm text-slate-500 mt-0.5">איפה כדאי להשקיע עכשיו</p>
                </div>
                <Target className="w-5 h-5 text-slate-300" />
              </div>
              <div className="space-y-3">
                {dashboard.categories.map((category) => (
                  <CategoryProgressCard key={category.category_id} category={category} />
                ))}
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
