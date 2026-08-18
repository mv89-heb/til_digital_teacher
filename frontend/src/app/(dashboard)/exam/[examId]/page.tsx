'use client';

import { useParams } from 'next/navigation';
import ExamSimulation from '@/components/exam/ExamSimulation';

export default function ExamPage() {
  const params = useParams<{ examId: string }>();
  const examId = Number(params?.examId);

  if (!Number.isInteger(examId) || examId <= 0) {
    return <div className="p-8 text-center text-rose-600">מזהה סימולציה לא תקין.</div>;
  }

  return <ExamSimulation examId={examId} />;
}
