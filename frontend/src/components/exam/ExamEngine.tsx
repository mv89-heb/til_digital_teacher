"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useExamStore } from "../../stores/examStore";
import { ExamTimer } from "./ExamTimer";
import { QuestionRenderer } from "./QuestionRenderer";

type ExamQuestion = {
  id: number;
  question_id: number;
  question_version_id: number;
  sequence_number: number;
  status: string;
  total_time_ms: number;
  prompt: unknown;
  visual_data?: any;
  question_type?: string | null;
  difficulty?: string | null;
  answers: { id: number; answer_text: unknown; order: number }[];
};

type ExamSession = {
  id: number;
  expires_at: string;
  status: string;
  current_question_index: number;
  questions: ExamQuestion[];
};

type Props = {
  session: ExamSession;
  onAnswer: (sessionQuestionId: number, answerId: number, elapsedMs: number) => Promise<void>;
  onSubmit: () => Promise<void>;
  onViewQuestion?: (sessionQuestionId: number) => Promise<void>;
};

export function ExamEngine({ session, onAnswer, onSubmit, onViewQuestion }: Props) {
  const { currentIndex, questions, initialize, next, previous, goTo } = useExamStore();
  const [selected, setSelected] = useState<Record<number, number>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    initialize(session.id, session.questions, session.current_question_index);
  }, [initialize, session.id, session.questions, session.current_question_index]);

  const question = useMemo(() => {
    const fromStore = questions[currentIndex];
    return session.questions.find((item) => item.id === fromStore?.id) ?? session.questions[currentIndex];
  }, [currentIndex, questions, session.questions]);

  useEffect(() => {
    if (question && onViewQuestion) void onViewQuestion(question.id);
  }, [question, onViewQuestion]);

  const submit = useCallback(async () => {
    if (submitting) return;
    setSubmitting(true);
    try {
      await onSubmit();
    } finally {
      setSubmitting(false);
    }
  }, [onSubmit, submitting]);

  if (!question) return <div dir="rtl">לא נמצאה שאלה.</div>;

  const isLast = currentIndex >= session.questions.length - 1;

  const selectAnswer = async (answerId: number) => {
    if (submitting) return;
    setSelected((state) => ({ ...state, [question.id]: answerId }));
    await onAnswer(question.id, answerId, question.total_time_ms);
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 p-4" dir="rtl">
      <header className="flex items-center justify-between rounded-2xl border bg-white p-4 shadow-sm">
        <div className="font-semibold">
          שאלה {currentIndex + 1} מתוך {session.questions.length}
        </div>
        <ExamTimer sessionId={session.id} expiresAt={session.expires_at} onExpire={() => void submit()} />
      </header>

      <div className="flex-1 rounded-2xl border bg-white p-6 shadow-sm">
        <QuestionRenderer
          question={question}
          selectedAnswerId={selected[question.id] ?? null}
          disabled={submitting}
          onSelect={(answerId) => void selectAnswer(answerId)}
        />
      </div>

      <nav className="flex flex-wrap items-center justify-between gap-3">
        <button type="button" onClick={previous} disabled={currentIndex === 0} className="rounded-lg border px-4 py-2 disabled:opacity-40">
          הקודם
        </button>
        <div className="flex flex-wrap gap-2">
          {session.questions.map((item, index) => (
            <button
              key={item.id}
              type="button"
              onClick={() => goTo(index)}
              aria-label={`עבור לשאלה ${index + 1}`}
              className={`h-9 w-9 rounded-full border ${index === currentIndex ? "border-blue-600 bg-blue-600 text-white" : ""}`}
            >
              {index + 1}
            </button>
          ))}
        </div>
        {isLast ? (
          <button type="button" onClick={() => void submit()} disabled={submitting} className="rounded-lg bg-blue-600 px-5 py-2 font-semibold text-white disabled:opacity-50">
            {submitting ? "מגיש..." : "סיום והגשה"}
          </button>
        ) : (
          <button type="button" onClick={next} className="rounded-lg bg-slate-900 px-4 py-2 text-white">
            הבא
          </button>
        )}
      </nav>
    </main>
  );
}
