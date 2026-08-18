import type { ExamQuestion, ExamSession } from '@/types/exam';

export type ExamClientState = {
  phase: 'LOADING' | 'RUNNING' | 'SECTION_EXPIRED' | 'SUBMITTING' | 'FINISHED' | 'ERROR';
  currentSectionIndex: number;
  currentQuestionIndex: number;
  selectedAnswers: Record<number, number>;
  viewedQuestionIds: number[];
  serverNowOffsetMs: number;
};

export type ExamEvent =
  | { type: 'HYDRATE'; session: ExamSession; clientNowMs: number }
  | { type: 'SELECT_ANSWER'; questionId: number; answerId: number }
  | { type: 'VIEWED'; questionId: number }
  | { type: 'GO_TO_QUESTION'; questionIndex: number }
  | { type: 'NEXT_QUESTION'; nextQuestionIndex: number }
  | { type: 'SECTION_EXPIRED' }
  | { type: 'SECTION_SYNCED'; session: ExamSession; clientNowMs: number }
  | { type: 'SUBMIT_STARTED' }
  | { type: 'FINISHED' }
  | { type: 'ERROR' };

export const initialExamState: ExamClientState = {
  phase: 'LOADING',
  currentSectionIndex: 0,
  currentQuestionIndex: 0,
  selectedAnswers: {},
  viewedQuestionIds: [],
  serverNowOffsetMs: 0,
};

export function hydrateExam(session: ExamSession, clientNowMs = Date.now()): ExamClientState {
  const firstQuestion = firstQuestionForSection(session, session.current_section_index);
  return {
    ...initialExamState,
    phase: session.status === 'SUBMITTED' || session.status === 'EXPIRED' ? 'FINISHED' : 'RUNNING',
    currentSectionIndex: session.current_section_index,
    currentQuestionIndex: firstQuestion?.sequence_number ?? session.current_question_index,
    serverNowOffsetMs: session.started_at ? Date.parse(session.started_at) - clientNowMs : 0,
  };
}

export function reduceExamState(state: ExamClientState, event: ExamEvent): ExamClientState {
  switch (event.type) {
    case 'HYDRATE':
      return hydrateExam(event.session, event.clientNowMs);
    case 'SELECT_ANSWER':
      return { ...state, selectedAnswers: { ...state.selectedAnswers, [event.questionId]: event.answerId } };
    case 'VIEWED':
      return state.viewedQuestionIds.includes(event.questionId)
        ? state
        : { ...state, viewedQuestionIds: [...state.viewedQuestionIds, event.questionId] };
    case 'GO_TO_QUESTION':
    case 'NEXT_QUESTION':
      return { ...state, currentQuestionIndex: event.questionIndex ?? event.nextQuestionIndex };
    case 'SECTION_EXPIRED':
      return { ...state, phase: 'SECTION_EXPIRED' };
    case 'SECTION_SYNCED':
      return hydrateExam(event.session, event.clientNowMs);
    case 'SUBMIT_STARTED':
      return { ...state, phase: 'SUBMITTING' };
    case 'FINISHED':
      return { ...state, phase: 'FINISHED' };
    case 'ERROR':
      return { ...state, phase: 'ERROR' };
    default:
      return state;
  }
}

export function currentQuestion(session: ExamSession, state: ExamClientState): ExamQuestion | undefined {
  return session.questions.find((q) => q.sequence_number === state.currentQuestionIndex && q.section_id === session.sections[state.currentSectionIndex]?.id);
}

export function questionsForCurrentSection(session: ExamSession): ExamQuestion[] {
  const sectionId = session.sections[session.current_section_index]?.id;
  return session.questions.filter((q) => q.section_id === sectionId).sort((a, b) => a.sequence_number - b.sequence_number);
}

export function remainingSectionMs(session: ExamSession, clientNowMs = Date.now()): number {
  if (!session.current_section_expires_at) return 0;
  return Math.max(0, Date.parse(session.current_section_expires_at) - clientNowMs);
}

function firstQuestionForSection(session: ExamSession, sectionIndex: number): ExamQuestion | undefined {
  const sectionId = session.sections[sectionIndex]?.id;
  return session.questions
    .filter((q) => q.section_id === sectionId)
    .sort((a, b) => a.sequence_number - b.sequence_number)[0];
}
