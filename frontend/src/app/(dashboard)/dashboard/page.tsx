'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, BookOpen, CheckCircle2, Target, Zap } from 'lucide-react';
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

  const {
    data: dashboard,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => getDashboard(token as string),
    enabled: !!token,
  });

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-24 w-full" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (isError || !dashboard) {
    return (
      <div className="max-w-6xl mx-auto">
        <Alert variant="error">לא הצלחנו לטעון את לוח הבקרה. נסו לרענן את הדף.</Alert>
      </div>
    );
  }

  const hasCategories = dashboard.categories.length > 0;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 mb-2">
          שלום, {user?.email?.split('@')[0] || 'תלמיד'} 👋
        </h1>
        <p className="text-slate-600">הנה איך אתה מתקדם היום</p>
      </div>

      {!hasCategories ? (
        <EmptyState
          icon={<BookOpen className="w-7 h-7" />}
          title="עדיין לא התחלת ללמוד"
          description="עברו למרכז הלימוד כדי להתחיל את השיעור הראשון שלכם."
          action={
            <Link
              href="/learn"
              className="px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold hover:bg-indigo-700 transition-colors inline-block"
            >
              למרכז הלימוד
            </Link>
          }
        />
      ) : (
        <>
          {/* Progress track */}
          <Card className="p-5 sm:p-6">
            <ProgressTrack stats={dashboard.stats} />
          </Card>

          {/* Continue learning */}
          {dashboard.continue_learning && <ContinueLearningCard lesson={dashboard.continue_learning} />}

          {/* Stats cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatsCard icon={<Zap className="w-5 h-5" />} label="נקודות XP" value={dashboard.xp_total} accent="amber" />
            <StatsCard
              icon={<Target className="w-5 h-5" />}
              label="אחוז הצלחה כללי"
              value={`${dashboard.stats.overall_accuracy_percent}%`}
              accent="indigo"
            />
            <StatsCard
              icon={<CheckCircle2 className="w-5 h-5" />}
              label="שיעורים שהושלמו"
              value={`${dashboard.stats.total_lessons_completed}/${dashboard.stats.total_lessons_available}`}
              accent="emerald"
            />
            <StatsCard
              icon={<BarChart3 className="w-5 h-5" />}
              label="שאלות שנענו"
              value={dashboard.stats.total_questions_attempted}
              accent="rose"
            />
          </div>

          {/* Chart + category cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-5 sm:p-6">
              <h2 className="font-bold text-slate-900 mb-4">אחוזי הצלחה לפי תחום</h2>
              <ProgressChart categories={dashboard.categories} />
            </Card>

            <div className="space-y-4">
              <h2 className="font-bold text-slate-900">התקדמות לפי תחום</h2>
              {dashboard.categories.map((category) => (
                <CategoryProgressCard key={category.category_id} category={category} />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
