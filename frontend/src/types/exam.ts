export type ExamAnswer = {
  id: number;
  answer_text: string;
  order: number;
};

export type ExamQuestion = {
  id: number;
  question_id: number;
  question_version_id: number;
  section_id: number;
  sequence_number: number;
  status: string;
  total_time_ms: number;
  prompt: unknown;
  visual_data?: unknown;
  question_type?: string | null;
  difficulty?: string | null;
  solution: null;
  answers: ExamAnswer[];
};

export type ExamSection = {
  id: number;
  name: string;
  category: string;
  display_order: number;
  duration_seconds: number;
  question_count: number | null;
  instructions: unknown;
  scoring_configuration: Record<string, unknown>;
  locked: boolean;
  active: boolean;
};

export type ExamSession = {
  id: number;
  exam_id: number;
  status: 'CREATED' | 'IN_PROGRESS' | 'PAUSED' | 'SUBMITTED' | 'EXPIRED';
  started_at: string | null;
  expires_at: string | null;
  current_question_index: number;
  current_section_index: number;
  section_started_at: string | null;
  current_section_expires_at: string | null;
  locked_before_section_index: number;
  completed_section_indices: number[];
  sections: ExamSection[];
  questions: ExamQuestion[];
};

export type ExamAnswerResult = {
  id: number;
  is_correct: boolean;
  score: string | null;
};

export type ExamCategoryResult = {
  category: string;
  total_questions: number;
  answered_questions: number;
  correct_answers: number;
  accuracy: string | null;
  average_time_ms: number | null;
};

export type ExamResult = {
  id: number;
  raw_score: string;
  weighted_score: string;
  normalized_score: string | null;
  total_questions: number;
  answered_questions: number;
  correct_answers: number;
  skipped_questions: number;
  total_time_ms: number;
  metadata: {
    scoring_version?: string;
    category_scores?: Record<string, {
      score: number;
      accuracy: number;
      completion: number;
      average_time_ms: number | null;
    }>;
    [key: string]: unknown;
  };
  categories: ExamCategoryResult[];
};
