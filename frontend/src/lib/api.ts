// frontend/src/lib/api.ts

import type { Category, DashboardSummary, LessonDetail, LessonProgress, SubmitAnswerResult } from '@/types/learning';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'משהו השתבש, אנא נסה שוב.');
  }

  return data;
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export async function getCategories(): Promise<Category[]> {
  const data = await fetchApi('/learning/categories');
  return data.categories;
}

export async function getLesson(lessonId: number | string): Promise<LessonDetail> {
  const data = await fetchApi(`/learning/lessons/${lessonId}`);
  return data.lesson;
}

export async function submitAnswer(
  questionId: number,
  answerId: number,
  token: string
): Promise<SubmitAnswerResult> {
  return fetchApi(`/learning/questions/${questionId}/submit`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ answer_id: answerId }),
  });
}

export async function completeLesson(lessonId: number | string, token: string): Promise<LessonProgress> {
  const data = await fetchApi(`/learning/lessons/${lessonId}/complete`, {
    method: 'POST',
    headers: authHeaders(token),
  });
  return data.progress;
}

export async function getLessonProgress(lessonId: number | string, token: string): Promise<LessonProgress> {
  const data = await fetchApi(`/learning/lessons/${lessonId}/progress`, {
    headers: authHeaders(token),
  });
  return data.progress;
}

export async function getDashboard(token: string): Promise<DashboardSummary> {
  return fetchApi('/learning/dashboard', {
    headers: authHeaders(token),
  });
}
