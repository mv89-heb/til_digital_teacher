'use client';

import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, PartyPopper, Zap } from 'lucide-react';
import { completeLesson, fetchApi, getLesson, getLessonProgress } from '@/lib/api';
import { useAuthStore } from '@/store/useAuthStore';
import { useToast } from '@/lib/useToast';
import LessonHeader from '@/components/learning/LessonHeader';
import ContentBlockRenderer from '@/components/learning/ContentBlockRenderer';
import ProgressBar from '@/components/ui/ProgressBar';
import Card from '@/components/ui/Card';
import Skeleton from '@/components/ui/Skeleton';
import Badge from '@/components/ui/Badge';
import { ToastContainer } from '@/components/ui/ToastContainer';

export default function LessonPage() {
  const params = useParams();
  const router = useRouter();
  const lessonId = params.id as string;
  const [currentIndex, setCurrentIndex] = useState(0);
  const { token, updateXp } = useAuthStore();
  const { toasts, showToast } = useToast();
  const queryClient = useQueryClient();

  const {
    data: lesson,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['lesson', lessonId],
    queryFn: () => getLesson(lessonId),
  });

  const { data: progress } = useQuery({
    queryKey: ['lesson-progress', lessonId],
    queryFn: () => getLessonProgress(lessonId, token as string),
    enabled: !!token,
  });

  const completeMutation = useMutation({
    mutationFn: () => completeLesson(lessonId, token as string),
    onSuccess: (newProgress) => {
      queryClient.setQueryData(['lesson-progress', lessonId], newProgress);
      showToast(`🏆 שיעור הושלם! (+${newProgress.xp_earned} XP)`, 'success');
      fetchApi('/auth/me', { headers: { Authorization: `Bearer ${token}` } })
        .then((data) => updateXp(data.user.xp_total))
        .catch(() => {});
    },
  });

  const handleCorrectAnswer = (xpEarned: number) => {
    showToast(`+${xpEarned} XP`, 'success');
    getLessonProgress(lessonId, token as string).then((p) => {
      queryClient.setQueryData(['lesson-progress', lessonId], p);
    });
    fetchApi('/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then((data) => updateXp(data.user.xp_total))
      .catch(() => {});
  };

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !lesson) {
    return <div className="text-center text-slate-500 py-20">לא הצלחנו לטעון את השיעור.</div>;
  }

  const blocks = lesson.content_blocks;
  const currentBlock = blocks[currentIndex];
  const isFirst = currentIndex === 0;
  const isLast = currentIndex === blocks.length - 1;
  const isCompleted = progress?.completed ?? false;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-start justify-between">
        <LessonHeader lesson={lesson} />
        {isCompleted && (
          <Badge variant="success" icon={<PartyPopper className="w-3 h-3" />}>
            הושלם
          </Badge>
        )}
      </div>

      <div className="mb-6">
        <ProgressBar
          current={currentIndex + 1}
          total={blocks.length}
          label={`שלב ${currentIndex + 1} מתוך ${blocks.length}`}
        />
      </div>

      <Card className="p-6 min-h-[280px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentBlock.id}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 12 }}
            transition={{ duration: 0.25 }}
          >
            <ContentBlockRenderer block={currentBlock} token={token} onCorrect={handleCorrectAnswer} />
          </motion.div>
        </AnimatePresence>
      </Card>

      <div className="flex items-center justify-between mt-6">
        <button
          onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
          disabled={isFirst}
          className="flex items-center gap-1 px-4 py-2.5 rounded-xl border border-slate-300 text-slate-700 font-medium disabled:opacity-30 hover:bg-slate-50 transition-colors"
        >
          <ChevronRight className="w-4 h-4" />
          הקודם
        </button>

        {!isLast ? (
          <button
            onClick={() => setCurrentIndex((i) => Math.min(blocks.length - 1, i + 1))}
            className="flex items-center gap-1 px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold hover:bg-indigo-700 transition-colors"
          >
            הבא
            <ChevronLeft className="w-4 h-4" />
          </button>
        ) : isCompleted ? (
          <button
            onClick={() => router.push('/learn')}
            className="flex items-center gap-1 px-5 py-2.5 rounded-xl bg-emerald-100 text-emerald-700 font-semibold hover:bg-emerald-200 transition-colors"
          >
            🏆 חזרה למרכז הלימוד
          </button>
        ) : (
          <button
            onClick={() => completeMutation.mutate()}
            disabled={completeMutation.isPending}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 text-white font-semibold hover:bg-emerald-700 transition-colors disabled:opacity-50"
          >
            <Zap className="w-4 h-4" />
            {completeMutation.isPending ? 'שומר...' : 'סיימתי את השיעור 🎉'}
          </button>
        )}
      </div>

      <AnimatePresence>
        {completeMutation.isSuccess && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-6 text-center bg-gradient-to-l from-emerald-50 to-indigo-50 border border-emerald-100 rounded-2xl p-6"
          >
            <div className="text-4xl mb-2">🎉</div>
            <h3 className="font-bold text-slate-900 text-lg mb-1">כל הכבוד! סיימת את השיעור</h3>
            <p className="text-slate-600 text-sm">
              צברת {completeMutation.data?.xp_earned ?? 50} XP בשיעור הזה
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      <ToastContainer toasts={toasts} />
    </div>
  );
}
