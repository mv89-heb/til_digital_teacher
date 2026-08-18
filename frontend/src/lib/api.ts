import type { Category, DashboardSummary, LessonDetail, LessonProgress, PracticeQuestionPool, SubmitAnswerResult } from '@/types/learning';
import type { ExamSession, ExamAnswerResult, ExamResult } from '@/types/exam';
import { useAuthStore } from '@/store/useAuthStore';

const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
const API_URL = configuredApiUrl || (process.env.NODE_ENV === 'development' ? 'http://localhost:5000/api' : 'https://til-digital-teacher.onrender.com/api');

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers } });
  const text = await response.text();
  let data: any = {};
  if (text) { try { data = JSON.parse(text); } catch { data = { error: text.slice(0, 500) }; } }
  if (response.status === 401 && typeof window !== 'undefined') useAuthStore.getState().logout();
  if (!response.ok) throw new Error(data.error || `בקשת השרת נכשלה (${response.status}).`);
  return data;
}

function authHeaders(token: string) { return { Authorization: `Bearer ${token}` }; }

export async function getCategories(): Promise<Category[]> {
  const data = await fetchApi('/learning/categories');
  return data.categories;
}

export async function getLesson(lessonId: number | string): Promise<LessonDetail> {
  const data = await fetchApi(`/learning/lessons/${lessonId}`);
  return data.lesson;
}

export async function getPracticeQuestions(token: string, options: { categoryId?: number; difficulty?: 'easy' | 'medium' | 'exam'; limit?: number; mode?: 'adaptive' | 'all' } = {}): Promise<PracticeQuestionPool> {
  const params = new URLSearchParams();
  if (options.categoryId) params.set('category_id', String(options.categoryId));
  if (options.difficulty) params.set('difficulty', options.difficulty);
  if (options.limit) params.set('limit', String(options.limit));
  if (options.mode) params.set('mode', options.mode);
  const query = params.toString();
  return fetchApi(`/learning/practice/questions${query ? `?${query}` : ''}`, { headers: authHeaders(token) });
}

export async function getPracticeQuestion(questionId: number, token: string) {
  const data = await fetchApi(`/learning/practice/questions/${questionId}`, { headers: authHeaders(token) });
  return data.question;
}

export async function submitAnswer(questionId: number, answerId: number, token: string): Promise<SubmitAnswerResult> {
  return fetchApi(`/learning/questions/${questionId}/submit`, { method: 'POST', headers: authHeaders(token), body: JSON.stringify({ answer_id: answerId }) });
}

export async function completeLesson(lessonId: number | string, token: string): Promise<LessonProgress> {
  const data = await fetchApi(`/learning/lessons/${lessonId}/complete`, { method: 'POST', headers: authHeaders(token) });
  return data.progress;
}

export async function getLessonProgress(lessonId: number | string, token: string): Promise<LessonProgress> {
  const data = await fetchApi(`/learning/lessons/${lessonId}/progress`, { headers: authHeaders(token) });
  return data.progress;
}

export async function getDashboard(token: string): Promise<DashboardSummary> {
  return fetchApi('/learning/dashboard', { headers: authHeaders(token) });
}

export async function startExam(examId: number, token: string): Promise<ExamSession> {
  const data = await fetchApi(`/exams/${examId}/sessions`, { method: 'POST', headers: authHeaders(token) });
  return data.session;
}

export async function getExamSession(sessionId: number, token: string): Promise<ExamSession> {
  const data = await fetchApi(`/exams/sessions/${sessionId}`, { headers: authHeaders(token) });
  return data.session;
}

export async function advanceExamSection(sessionId: number, token: string): Promise<ExamSession> {
  const data = await fetchApi(`/exams/sessions/${sessionId}/advance-section`, { method: 'POST', headers: authHeaders(token) });
  return data.session;
}

export async function markExamQuestionViewed(sessionId: number, sessionQuestionId: number, token: string) {
  return fetchApi(`/exams/sessions/${sessionId}/questions/${sessionQuestionId}/view`, { method: 'POST', headers: authHeaders(token) });
}

export async function submitExamAnswer(sessionId: number, sessionQuestionId: number, answerId: number, elapsedMs: number, token: string): Promise<ExamAnswerResult> {
  const data = await fetchApi(`/exams/sessions/${sessionId}/answers`, {
    method: 'POST', headers: authHeaders(token),
    body: JSON.stringify({ session_question_id: sessionQuestionId, answer_id: answerId, elapsed_ms: elapsedMs }),
  });
  return data.answer;
}

export async function submitExam(sessionId: number, token: string): Promise<ExamResult> {
  const data = await fetchApi(`/exams/sessions/${sessionId}/submit`, { method: 'POST', headers: authHeaders(token) });
  return data.result;
}
