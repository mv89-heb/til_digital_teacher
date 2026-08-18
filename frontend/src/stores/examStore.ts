"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

type ExamQuestion = {
  id: number;
  question_id: number;
  sequence_number: number;
  status: string;
  total_time_ms: number;
};

type ExamState = {
  sessionId: number | null;
  currentIndex: number;
  skipped: number[];
  flagged: number[];
  questions: ExamQuestion[];
  hydrated: boolean;
  initialize: (sessionId: number, questions: ExamQuestion[], currentIndex?: number) => void;
  next: () => void;
  previous: () => void;
  goTo: (index: number) => void;
  toggleSkipped: (questionId: number) => void;
  toggleFlagged: (questionId: number) => void;
  clear: () => void;
};

export const useExamStore = create<ExamState>()(
  persist(
    (set) => ({
      sessionId: null,
      currentIndex: 0,
      skipped: [],
      flagged: [],
      questions: [],
      hydrated: false,
      initialize: (sessionId, questions, currentIndex = 0) =>
        set({ sessionId, questions, currentIndex, hydrated: true }),
      next: () =>
        set((state) => ({ currentIndex: Math.min(state.currentIndex + 1, Math.max(0, state.questions.length - 1)) })),
      previous: () =>
        set((state) => ({ currentIndex: Math.max(0, state.currentIndex - 1) })),
      goTo: (index) =>
        set((state) => ({ currentIndex: Math.max(0, Math.min(index, state.questions.length - 1)) })),
      toggleSkipped: (questionId) =>
        set((state) => ({
          skipped: state.skipped.includes(questionId)
            ? state.skipped.filter((id) => id !== questionId)
            : [...state.skipped, questionId],
        })),
      toggleFlagged: (questionId) =>
        set((state) => ({
          flagged: state.flagged.includes(questionId)
            ? state.flagged.filter((id) => id !== questionId)
            : [...state.flagged, questionId],
        })),
      clear: () => set({ sessionId: null, currentIndex: 0, skipped: [], flagged: [], questions: [], hydrated: true }),
    }),
    {
      name: "exam-engine-state",
      partialize: (state) => ({
        sessionId: state.sessionId,
        currentIndex: state.currentIndex,
        skipped: state.skipped,
        flagged: state.flagged,
        questions: state.questions,
      }),
      onRehydrateStorage: () => () => {
        // Kept intentionally side-effect free; API/session state is authoritative.
      },
    },
  ),
);
