'use client';

import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react';
import { CheckCircle2, ChevronLeft, ChevronRight, Clock3, Loader2, Lock, Send, ShieldAlert } from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { getExamSession, markExamQuestionViewed, startExam, submitExam, submitExamAnswer } from '@/lib/api';
import { currentQuestion, hydrateExam, initialExamState, questionsForCurrentSection, reduceExamState, remainingSectionMs } from '@/lib/examEngine';
import type { ExamResult, ExamSession } from '@/types/exam';

function promptText(prompt: unknown): string {
  if (typeof prompt === 'string') return prompt;
  if (prompt && typeof prompt === 'object') {
    const value = prompt as Record<string, unknown>;
    for (const key of ['text', 'content', 'question', 'body']) {
      if (typeof value[key] === 'string') return String(value[key]);
    }
    try { return JSON.stringify(prompt); } catch { return ''; }
  }
  return '';
}

function instructionText(value: unknown): string | null {
  if (typeof value === 'string') return value;
  if (value === null || value === undefined) return null;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (value && typeof value === 'object') {
    const obj = value as Record<string, unknown>;
    for (const key of ['text', 'content', 'instructions']) {
      if (typeof obj[key] === 'string') return String(obj[key]);
    }
  }
  return null;
}

function Visual({ value }: { value: unknown }) {
  if (!value || typeof value !== 'object') return null;
  const visual = value as Record<string, unknown>;
  if (visual.format === 'matrix' && Array.isArray(visual.cells)) {
    const rows = visual.cells as unknown[][];
    const columns = Math.max(1, ...rows.map((r) => r.length));
    return <div className="my-5 flex justify-center" dir="ltr"><div className="grid gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-4" style={{ gridTemplateColumns: `repeat(${columns}, minmax(58px, 1fr))` }}>{rows.flatMap((row, r) => row.map((cell, c) => <div key={`${r}-${c}`} className="flex h-14 w-14 items-center justify-center rounded-xl border-2 border-slate-300 bg-white text-lg font-bold shadow-sm">{cell == null ? '?' : String(cell)}</div>))}</div></div>;
  }
  if (visual.format === 'svg' && typeof visual.svg === 'string') {
    const safeSvg = visual.svg.replace(/<script[\s\S]*?<\/script>/gi, '').replace(/\son[a-z]+\s*=\s*(["']).*?\1/gi, '').replace(/javascript:/gi, '');
    return <div className="my-5 overflow-hidden rounded-2xl border border-slate-200 bg-white p-4" dir="ltr" dangerouslySetInnerHTML={{ __html: safeSvg }} />;
  }
  return null;
}

function formatTime(ms: number) {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000));
  return `${String(Math.floor(totalSeconds / 60)).padStart(2, '0')}:${String(totalSeconds % 60).padStart(2, '0')}`;
}

function Stat({ label, value }: { label: string; value: string }) {
  return <div className="rounded-2xl bg-slate-50 p-4 text-center"><div className="text-xs text-slate-500">{label}</div><div className="mt-1 text-xl font-black text-slate-900">{value}</div></div>;
}

export default function ExamSimulation({ examId }: { examId: number }) {
  const token = useAuthStore((s) => s.token);
  const [session, setSession] = useState<ExamSession | null>(null);
  const [result, setResult] = useState<ExamResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [state, dispatch] = useReducer(reduceExamState, initialExamState);
  const [submittingAnswer, setSubmittingAnswer] = useState(false);
  const questionStartedAt = useRef(Date.now());
  const syncingRef = useRef(false);

  const syncSession = useCallback(async () => {
    if (!token || !session || syncingRef.current) return;
    syncingRef.current = true;
    try {
      const fresh = await getExamSession(session.id, token);
      setSession(fresh);
      dispatch({ type: 'SECTION_SYNCED', session: fresh, clientNowMs: Date.now() });
      if (fresh.status === 'EXPIRED' || fresh.status === 'SUBMITTED') {
        setResult(await submitExam(fresh.id, token));
        dispatch({ type: 'FINISHED' });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'לא ניתן לסנכרן את הבחינה.');
    } finally {
      syncingRef.current = false;
    }
  }, [session, token]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const started = await startExam(examId, token);
        if (!cancelled) {
          setSession(started);
          dispatch({ type: 'HYDRATE', session: started, clientNowMs: Date.now() });
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'לא ניתן להתחיל את הבחינה.');
      }
    })();
    return () => { cancelled = true; };
  }, [examId, token]);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 250);
    return () => window.clearInterval(timer);
  }, []);

  const questions = useMemo(() => session ? questionsForCurrentSection(session) : [], [session, state.currentSectionIndex]);
  const question = session ? currentQuestion(session, state) : undefined;
  const remaining = session ? remainingSectionMs(session, now) : 0;
  const currentPosition = Math.max(0, questions.findIndex((q) => q.sequence_number === state.currentQuestionIndex));
  const selectedAnswer = question ? state.selectedAnswers[question.id] : undefined;
  const section = session?.sections[state.currentSectionIndex];
  const instructions = instructionText(section?.instructions);

  useEffect(() => {
    if (!session || !question || !token) return;
    questionStartedAt.current = Date.now();
    dispatch({ type: 'VIEWED', questionId: question.id });
    void markExamQuestionViewed(session.id, question.id, token).catch(() => undefined);
  }, [session?.id, question?.id, token]);

  useEffect(() => {
    if (!session || state.phase !== 'RUNNING' || remaining > 0 || syncingRef.current) return;
    dispatch({ type: 'SECTION_EXPIRED' });
    void syncSession();
  }, [remaining, session, state.phase, syncSession]);

  const chooseAnswer = async (answerId: number) => {
    if (!session || !question || !token || submittingAnswer || state.phase !== 'RUNNING') return;
    setSubmittingAnswer(true);
    dispatch({ type: 'SELECT_ANSWER', questionId: question.id, answerId });
    try {
      await submitExamAnswer(session.id, question.id, answerId, Math.max(0, Date.now() - questionStartedAt.current), token);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'לא ניתן לשמור את התשובה.');
    } finally {
      setSubmittingAnswer(false);
    }
  };

  const finish = async () => {
    if (!session || !token || state.phase === 'SUBMITTING' || state.phase === 'FINISHED') return;
    dispatch({ type: 'SUBMIT_STARTED' });
    try {
      setResult(await submitExam(session.id, token));
      dispatch({ type: 'FINISHED' });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'לא ניתן לסיים את הבחינה.');
      dispatch({ type: 'ERROR' });
    }
  };

  if (!token) return <div className="p-8 text-center">יש להתחבר כדי להתחיל סימולציה.</div>;
  if (error) return <div className="mx-auto max-w-3xl p-8"><div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-800"><ShieldAlert className="mb-3" />{error}</div></div>;
  if (!session) return <div className="flex min-h-[60vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin" /></div>;

  if (result || state.phase === 'FINISHED') {
    const score = Number(result?.normalized_score ?? 200);
    const categoryScores = result?.metadata.category_scores ? Object.entries(result.metadata.category_scores) : [];
    return <main className="mx-auto max-w-5xl p-6" dir="rtl"><div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm"><div className="text-center"><div className="text-sm font-semibold text-indigo-600">הסימולציה הסתיימה</div><div className="mt-2 text-6xl font-black text-slate-900">{Math.round(score)}</div><div className="text-slate-500">ציון סימולציה · סולם 200–800</div></div><div className="mt-8 grid gap-4 md:grid-cols-4"><Stat label="נכונות" value={`${result?.correct_answers ?? 0}/${result?.total_questions ?? 0}`} /><Stat label="נענו" value={String(result?.answered_questions ?? 0)} /><Stat label="דולגו" value={String(result?.skipped_questions ?? 0)} /><Stat label="זמן" value={`${Math.round((result?.total_time_ms ?? 0) / 60000)} דק׳`} /></div><div className="mt-8 grid gap-3 md:grid-cols-3">{categoryScores.map(([category, data]) => <div key={category} className="rounded-2xl bg-slate-50 p-5"><div className="font-bold">{category}</div><div className="mt-2 text-3xl font-black">{Math.round(data.score)}</div><div className="text-sm text-slate-500">{data.accuracy}% דיוק · {data.average_time_ms ? Math.round(data.average_time_ms / 1000) : '—'} שנ׳ ממוצע</div></div>)}</div></div></main>;
  }

  const isLastQuestion = currentPosition === questions.length - 1;
  const isLastSection = state.currentSectionIndex === session.sections.length - 1;
  const goPrevious = () => {
    if (currentPosition <= 0) return;
    const previous = questions[currentPosition - 1];
    if (previous) dispatch({ type: 'GO_TO_QUESTION', questionIndex: previous.sequence_number });
  };
  const goNext = () => {
    if (currentPosition >= questions.length - 1) return;
    const next = questions[currentPosition + 1];
    if (next) dispatch({ type: 'GO_TO_QUESTION', questionIndex: next.sequence_number });
  };

  return <main className="mx-auto max-w-7xl p-4 md:p-6" dir="rtl"><header className="sticky top-0 z-20 mb-5 rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-sm backdrop-blur"><div className="flex flex-wrap items-center justify-between gap-4"><div><div className="text-xs font-semibold text-slate-500">סימולציית מבחן תיל</div><h1 className="text-xl font-black text-slate-900">{section?.name}</h1></div><div className={`flex items-center gap-2 rounded-xl px-4 py-2 font-mono text-xl font-black ${remaining <= 30000 ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-900'}`}><Clock3 className="h-5 w-5" />{formatTime(remaining)}</div></div><div className="mt-4 flex gap-2 overflow-x-auto pb-1">{session.sections.map((item, index) => <div key={item.id} className={`flex min-w-fit items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold ${index < state.currentSectionIndex ? 'bg-slate-100 text-slate-400' : index === state.currentSectionIndex ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-50 text-slate-500'}`}>{index < state.currentSectionIndex && <Lock className="h-3.5 w-3.5" />}{index + 1}. {item.name}</div>)}</div></header><div className="grid gap-5 lg:grid-cols-[1fr_280px]"><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="mb-6 flex items-center justify-between gap-3"><div className="text-sm text-slate-500">שאלה {currentPosition + 1} מתוך {questions.length}</div><div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">ללא מחשבון</div></div>{instructions && <div className="mb-5 rounded-2xl bg-amber-50 p-4 text-sm text-amber-900">{instructions}</div>}{question ? <><Visual value={question.visual_data} /><div className="text-lg font-semibold leading-8 text-slate-900">{promptText(question.prompt)}</div><div className="mt-7 grid gap-3">{question.answers.map((answer, index) => { const selected = selectedAnswer === answer.id; return <button key={answer.id} onClick={() => void chooseAnswer(answer.id)} disabled={submittingAnswer} className={`flex items-center gap-4 rounded-2xl border-2 p-4 text-right transition ${selected ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:border-indigo-300 hover:bg-slate-50'} disabled:opacity-60`}><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-100 font-black">{String.fromCharCode(65 + index)}</span><span className="flex-1 font-medium">{answer.answer_text}</span>{selected && <CheckCircle2 className="h-5 w-5 text-indigo-600" />}</button>; })}</div></> : <div className="py-20 text-center text-slate-500">אין שאלות זמינות בפרק.</div>}<div className="mt-8 flex items-center justify-between gap-3 border-t border-slate-100 pt-5"><button disabled={currentPosition === 0} onClick={goPrevious} className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 font-semibold disabled:opacity-30"><ChevronRight className="h-4 w-4" /> הקודם</button>{isLastQuestion && isLastSection ? <button onClick={() => void finish()} className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 font-bold text-white hover:bg-indigo-700"><Send className="h-4 w-4" /> סיום ושליחת מבחן</button> : <button disabled={isLastQuestion} onClick={goNext} className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 font-bold text-white disabled:opacity-30">הבא <ChevronLeft className="h-4 w-4" /></button>}</div></section><aside className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="mb-3 font-black">מפת השאלות</div><div className="grid grid-cols-5 gap-2">{questions.map((q, index) => { const selected = state.selectedAnswers[q.id] != null; const active = q.sequence_number === state.currentQuestionIndex; return <button key={q.id} onClick={() => dispatch({ type: 'GO_TO_QUESTION', questionIndex: q.sequence_number })} className={`h-10 rounded-lg text-sm font-bold ${active ? 'bg-indigo-600 text-white' : selected ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}>{index + 1}</button>; })}</div><div className="mt-5 rounded-2xl bg-slate-50 p-4 text-xs text-slate-500">המעבר בין פרקים נעול. כאשר הזמן של פרק מסתיים, הוא נסגר ולא ניתן לחזור אליו.</div></aside></div></main>;
}
