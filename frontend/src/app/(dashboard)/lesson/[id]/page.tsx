'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, PartyPopper, Zap, CheckCircle2, List, ArrowRight, Clock3 } from 'lucide-react';
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

const STORAGE_PREFIX = 'til-lesson-position:';

export default function LessonPage() {
  const params = useParams();
  const router = useRouter();
  const lessonId = params.id as string;
  const { token, updateXp } = useAuthStore();
  const { toasts, showToast } = useToast();
  const queryClient = useQueryClient();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showOutline, setShowOutline] = useState(false);

  const { data: lesson, isLoading, isError } = useQuery({ queryKey: ['lesson', lessonId], queryFn: () => getLesson(lessonId) });
  const { data: progress } = useQuery({ queryKey: ['lesson-progress', lessonId], queryFn: () => getLessonProgress(lessonId, token as string), enabled: !!token });

  useEffect(() => {
    if (!lesson || typeof window === 'undefined') return;
    if (progress?.completed) { window.localStorage.removeItem(`${STORAGE_PREFIX}${lessonId}`); return; }
    const saved = Number(window.localStorage.getItem(`${STORAGE_PREFIX}${lessonId}`));
    if (Number.isInteger(saved) && saved >= 0 && saved < lesson.content_blocks.length) setCurrentIndex(saved);
  }, [lesson, lessonId, progress?.completed]);

  useEffect(() => {
    if (lesson && typeof window !== 'undefined') window.localStorage.setItem(`${STORAGE_PREFIX}${lessonId}`, String(currentIndex));
  }, [currentIndex, lesson, lessonId]);

  const completeMutation = useMutation({
    mutationFn: () => completeLesson(lessonId, token as string),
    onSuccess: (newProgress) => {
      queryClient.setQueryData(['lesson-progress', lessonId], newProgress);
      if (typeof window !== 'undefined') window.localStorage.removeItem(`${STORAGE_PREFIX}${lessonId}`);
      showToast(`🏆 שיעור הושלם! (+${newProgress.xp_earned} XP)`, 'success');
      fetchApi('/auth/me', { headers: { Authorization: `Bearer ${token}` } }).then((data) => updateXp(data.user.xp_total)).catch(() => {});
    },
  });

  const handleCorrectAnswer = (xpEarned: number) => {
    showToast(`+${xpEarned} XP`, 'success');
    getLessonProgress(lessonId, token as string).then((p) => queryClient.setQueryData(['lesson-progress', lessonId], p));
    fetchApi('/auth/me', { headers: { Authorization: `Bearer ${token}` } }).then((data) => updateXp(data.user.xp_total)).catch(() => {});
  };

  const blocks = lesson?.content_blocks ?? [];
  const currentBlock = blocks[currentIndex];
  const isFirst = currentIndex === 0;
  const isLast = blocks.length > 0 && currentIndex === blocks.length - 1;
  const isCompleted = progress?.completed ?? false;
  const progressPercent = blocks.length ? Math.round(((currentIndex + 1) / blocks.length) * 100) : 0;

  const outline = useMemo(() => blocks.map((block, index) => ({
    index,
    label: ({ simple_explanation: 'הסבר פשוט', normal_explanation: 'הסבר מעמיק', solved_example: 'דוגמה פתורה', normal_method: 'שיטת פתרון', fast_method: 'שיטה מהירה', common_mistakes: 'טעויות נפוצות', guided_practice: 'תרגול מודרך', summary: 'סיכום' } as Record<string, string>)[block.section] ?? block.section,
  })), [blocks]);

  if (isLoading) return <div className="max-w-4xl mx-auto space-y-4"><Skeleton className="h-24 w-full" /><Skeleton className="h-64 w-full" /></div>;
  if (isError || !lesson) return <div className="text-center text-slate-500 py-20">לא הצלחנו לטעון את השיעור.</div>;

  if (!blocks.length) return <div className="max-w-3xl mx-auto text-center py-16"><Card className="p-10"><BookOpenFallback /><h2 className="text-xl font-bold text-slate-900 mt-4">השיעור עדיין בבנייה</h2><p className="text-slate-500 mt-2">התוכן של השיעור הזה טרם נוסף למערכת.</p><button onClick={() => router.push('/learn')} className="mt-6 px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold">חזרה למרכז הלמידה</button></Card></div>;

  return (
    <div className="max-w-5xl mx-auto pb-12">
      <div className="mb-4 flex items-center justify-between gap-3">
        <Link href="/learn#lessons" className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"><ArrowRight className="w-4 h-4" /> מרכז הלמידה</Link>
        <div className="flex items-center gap-2 text-xs text-slate-400"><Clock3 className="w-3.5 h-3.5" /> למידה בקצב שלך · נשמר אוטומטית</div>
      </div>

      <div className="flex items-start justify-between gap-4"><LessonHeader lesson={lesson} />{isCompleted && <Badge variant="success" icon={<PartyPopper className="w-3 h-3" />}>הושלם</Badge>}</div>

      <div className="mt-4 grid grid-cols-1 lg:grid-cols-[1fr_240px] gap-6">
        <main className="min-w-0">
          <Card className="p-4 sm:p-5 mb-5 border-indigo-100 bg-gradient-to-l from-white to-indigo-50/50">
            <div className="flex items-center justify-between gap-3 mb-3"><div><div className="text-xs font-bold text-indigo-600">התקדמות</div><div className="text-sm font-semibold text-slate-700">שלב {currentIndex + 1} מתוך {blocks.length}</div></div><div className="text-xl font-black text-indigo-600">{progressPercent}%</div></div>
            <ProgressBar current={currentIndex + 1} total={blocks.length} label={`שלב ${currentIndex + 1} מתוך ${blocks.length}`} />
          </Card>

          <button onClick={() => setShowOutline((v) => !v)} className="lg:hidden mb-4 flex items-center gap-2 text-sm font-semibold text-slate-700 px-4 py-2 rounded-xl border border-slate-200 bg-white"><List className="w-4 h-4" /> תוכן השיעור</button>
          {showOutline && <LessonOutline outline={outline} currentIndex={currentIndex} onSelect={(i) => { setCurrentIndex(i); setShowOutline(false); }} />}

          <Card className="p-6 sm:p-8 min-h-[320px] shadow-sm">
            <AnimatePresence mode="wait"><motion.div key={currentBlock.id} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 12 }} transition={{ duration: 0.25 }}><ContentBlockRenderer block={currentBlock} token={token} onCorrect={handleCorrectAnswer} /></motion.div></AnimatePresence>
          </Card>

          <div className="flex items-center justify-between mt-6 gap-3">
            <button onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))} disabled={isFirst} className="flex items-center gap-1 px-4 py-2.5 rounded-xl border border-slate-300 text-slate-700 font-medium disabled:opacity-30 hover:bg-slate-50 transition-colors"><ChevronRight className="w-4 h-4" /> הקודם</button>
            {!isLast ? <button onClick={() => setCurrentIndex((i) => Math.min(blocks.length - 1, i + 1))} className="flex items-center gap-1 px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold hover:bg-indigo-700 transition-colors">הבא <ChevronLeft className="w-4 h-4" /></button> : isCompleted ? <button onClick={() => router.push('/learn')} className="flex items-center gap-1 px-5 py-2.5 rounded-xl bg-emerald-100 text-emerald-700 font-semibold">🏆 חזרה למרכז הלימוד</button> : <button onClick={() => completeMutation.mutate()} disabled={completeMutation.isPending} className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 text-white font-semibold hover:bg-emerald-700 disabled:opacity-50"><Zap className="w-4 h-4" />{completeMutation.isPending ? 'שומר...' : 'סיימתי את השיעור 🎉'}</button>}
          </div>

          {completeMutation.isSuccess && <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="mt-6 text-center bg-gradient-to-l from-emerald-50 to-indigo-50 border border-emerald-100 rounded-2xl p-6"><div className="text-4xl mb-2">🎉</div><h3 className="font-bold text-slate-900 text-lg mb-1">כל הכבוד! סיימת את השיעור</h3><p className="text-slate-600 text-sm">צברת {completeMutation.data?.xp_earned ?? 50} XP בשיעור הזה</p><Link href="/learn" className="inline-flex mt-4 items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-bold text-white hover:bg-indigo-700">להמשיך לשיעור הבא <ArrowLeft className="w-4 h-4" /></Link></motion.div>}
        </main>
        <aside className="hidden lg:block"><LessonOutline outline={outline} currentIndex={currentIndex} onSelect={setCurrentIndex} /></aside>
      </div>
      <ToastContainer toasts={toasts} />
    </div>
  );
}

function LessonOutline({ outline, currentIndex, onSelect }: { outline: { index: number; label: string }[]; currentIndex: number; onSelect: (index: number) => void }) {
  return <Card className="p-4 sticky top-4"><div className="flex items-center gap-2 font-bold text-slate-900 mb-3"><List className="w-4 h-4 text-indigo-600" /> תוכן השיעור</div><div className="space-y-1">{outline.map((item) => <button key={item.index} onClick={() => onSelect(item.index)} className={`w-full text-right flex items-center gap-2 p-2.5 rounded-lg text-sm transition-colors ${item.index === currentIndex ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'text-slate-600 hover:bg-slate-50'}`}>{item.index < currentIndex ? <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" /> : <span className="w-4 h-4 rounded-full border border-slate-300 text-[10px] flex items-center justify-center shrink-0">{item.index + 1}</span>}<span className="truncate">{item.label}</span></button>)}</div></Card>;
}

function BookOpenFallback() { return <div className="mx-auto w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center"><List className="w-7 h-7" /></div>; }
