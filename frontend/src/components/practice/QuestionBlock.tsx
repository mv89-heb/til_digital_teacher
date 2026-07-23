'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'framer-motion';
import { Brain, CheckCircle2, Clock, Loader2, XCircle } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import Card from '@/components/ui/Card';
import TextBlock from '@/components/learning/blocks/TextBlock';
import { submitAnswer } from '@/lib/api';
import type { Question, SubmitAnswerResult } from '@/types/learning';

const DIFFICULTY_LABEL: Record<string, string> = {
  easy: 'קל',
  medium: 'בינוני',
  exam: 'רמת מבחן',
};

const DIFFICULTY_VARIANT: Record<string, 'success' | 'warning' | 'danger'> = {
  easy: 'success',
  medium: 'warning',
  exam: 'danger',
};

interface QuestionBlockProps {
  question: Question;
  token: string | null;
  onCorrect?: (xpEarned: number) => void;
}

export default function QuestionBlock({ question, token, onCorrect }: QuestionBlockProps) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [showSolution, setShowSolution] = useState(false);

  const mutation = useMutation({
    mutationFn: (answerId: number) => {
      if (!token) throw new Error('יש להתחבר כדי לתרגל.');
      return submitAnswer(question.id, answerId, token);
    },
    onSuccess: (result) => {
      if (result.is_correct && result.xp_earned > 0) {
        onCorrect?.(result.xp_earned);
      }
    },
  });

  const result: SubmitAnswerResult | undefined = mutation.data;
  const checked = mutation.isSuccess;

  const handleReset = () => {
    setSelectedId(null);
    setShowSolution(false);
    mutation.reset();
  };

  return (
    <Card className="p-6">
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <Badge variant="info" icon={<Brain className="w-3 h-3" />}>
          תרגול
        </Badge>
        <Badge variant={DIFFICULTY_VARIANT[question.difficulty] ?? 'neutral'}>
          {DIFFICULTY_LABEL[question.difficulty] ?? question.difficulty}
        </Badge>
        {question.recommended_time_seconds && (
          <Badge icon={<Clock className="w-3 h-3" />}>{question.recommended_time_seconds} שניות</Badge>
        )}
      </div>

      <TextBlock content={question.body} />

      <div className="space-y-2 mt-4">
        {question.answers.map((answer) => {
          const isSelected = selectedId === answer.id;
          const revealCorrect = checked && result?.correct_answer_id === answer.id;
          const revealWrong = checked && isSelected && result?.correct_answer_id !== answer.id;

          return (
            <button
              key={answer.id}
              disabled={checked || mutation.isPending}
              onClick={() => setSelectedId(answer.id)}
              className={[
                'w-full text-right px-4 py-3 rounded-xl border-2 font-medium transition-all disabled:cursor-default',
                !checked && isSelected ? 'border-indigo-500 bg-indigo-50' : '',
                !checked && !isSelected ? 'border-slate-200 hover:border-indigo-300 hover:bg-slate-50' : '',
                revealCorrect ? 'border-emerald-500 bg-emerald-50 text-emerald-800' : '',
                revealWrong ? 'border-rose-400 bg-rose-50 text-rose-800' : '',
                checked && !isSelected && result?.correct_answer_id !== answer.id ? 'border-slate-200 opacity-50' : '',
              ].join(' ')}
            >
              <div className="flex items-center justify-between">
                <span>{answer.answer_text}</span>
                {revealCorrect && <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />}
                {revealWrong && <XCircle className="w-5 h-5 text-rose-500 shrink-0" />}
              </div>
            </button>
          );
        })}
      </div>

      {mutation.isError && (
        <p className="text-sm text-rose-600 mt-3">{(mutation.error as Error).message}</p>
      )}

      <AnimatePresence>
        {checked && result && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className={`mt-4 rounded-xl p-4 ${result.is_correct ? 'bg-emerald-50' : 'bg-amber-50'}`}>
              <p className={`font-bold mb-1 ${result.is_correct ? 'text-emerald-700' : 'text-amber-800'}`}>
                {result.is_correct
                  ? `🎉 מעולה! זיהית נכון${result.xp_earned ? ` (+${result.xp_earned} XP)` : ''}`
                  : 'החשיבה הייתה קרובה, אבל...'}
              </p>
              {result.explanation && <TextBlock content={result.explanation} />}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex items-center gap-3 mt-4">
        {!checked ? (
          <button
            onClick={() => selectedId !== null && mutation.mutate(selectedId)}
            disabled={selectedId === null || mutation.isPending}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold disabled:opacity-40 hover:bg-indigo-700 transition-colors"
          >
            {mutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
            בדיקה
          </button>
        ) : (
          <>
            <button
              onClick={() => setShowSolution((v) => !v)}
              className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 font-medium hover:bg-slate-50 transition-colors text-sm"
            >
              📖 {showSolution ? 'הסתר הסבר מלא' : 'הסבר פתרון מלא'}
            </button>
            <button
              onClick={handleReset}
              className="px-4 py-2 rounded-xl text-slate-500 font-medium hover:bg-slate-50 transition-colors text-sm"
            >
              נסה שוב
            </button>
          </>
        )}
      </div>

      <AnimatePresence>
        {showSolution && result?.solution_text && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-3 rounded-xl p-4 bg-slate-50 border border-slate-200">
              <TextBlock content={result.solution_text} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}
