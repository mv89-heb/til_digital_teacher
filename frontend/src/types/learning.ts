export interface RichContent {
  format: 'markdown';
  body: string;
  media?: unknown[];
}

export interface Answer {
  id: number;
  question_id: number;
  answer_text: string;
  order: number;
  // Present only in admin contexts (never on the public /learning/* fetch —
  // the server decides correctness via POST /questions/<id>/submit).
  is_correct?: boolean;
  explanation_if_selected?: RichContent | null;
}

export interface SubmitAnswerResult {
  is_correct: boolean;
  correct_answer_id: number | null;
  explanation: RichContent | null;
  solution_text: RichContent | null;
  xp_earned: number;
  xp_total: number | null;
}

export interface LessonProgress {
  user_id: number;
  lesson_id: number;
  completed: boolean;
  completed_at: string | null;
  xp_earned: number;
  last_viewed_at: string | null;
}

export interface Question {
  id: number;
  category_id: number;
  lesson_id: number | null;
  question_type: string;
  difficulty: 'easy' | 'medium' | 'exam';
  status: string;
  body: RichContent;
  solution_text: RichContent | null; // null on the public fetch until answered
  recommended_time_seconds: number | null;
  metadata: Record<string, unknown>;
  answers: Answer[];
}

export type BlockType =
  | 'text'
  | 'image'
  | 'video'
  | 'table'
  | 'formula'
  | 'interactive'
  | 'embedded_question';

export type TextBlockContent = RichContent;
export interface ImageBlockContent {
  url: string;
  alt?: string;
  caption?: string;
}
export interface TableBlockContent {
  headers: string[];
  rows: (string | number)[][];
}
export interface FormulaBlockContent {
  latex: string;
}
export interface EmbeddedQuestionBlockContent {
  question_id: number;
}

export interface ContentBlock {
  id: number;
  lesson_id: number;
  section: string;
  type: BlockType;
  order: number;
  content:
    | TextBlockContent
    | ImageBlockContent
    | TableBlockContent
    | FormulaBlockContent
    | EmbeddedQuestionBlockContent
    | Record<string, unknown>;
  metadata: Record<string, unknown>;
  question?: Question | null; // present (and resolved) only on embedded_question blocks
}

export interface LessonSummary {
  id: number;
  title: string;
  slug: string;
  description: string | null;
  status: string;
  difficulty_level: 'beginner' | 'intermediate' | 'advanced' | null;
  estimated_duration: number | null;
  icon: string | null;
  thumbnail_url: string | null;
  order: number;
  total_blocks: number;
  category: { id: number; name: string; type: string };
}

export interface LessonDetail extends LessonSummary {
  content_blocks: ContentBlock[];
}

export interface Category {
  id: number;
  name: string;
  description: string | null;
  type: string;
  icon: string | null;
  thumbnail_url: string | null;
  order: number;
  status: string;
  lesson_count: number;
  lessons: LessonSummary[];
}

export type StudentLevelName = 'beginner' | 'basic' | 'intermediate' | 'exam_ready' | 'advanced';

export interface CategoryProgress {
  category_id: number;
  name: string;
  icon: string | null;
  type: string;
  questions_attempted: number;
  questions_correct: number;
  accuracy_percent: number;
  lessons_completed: number;
  lessons_total: number;
  xp_earned: number;
  level: StudentLevelName;
}

export interface LessonProgressEntry {
  lesson_id: number;
  title: string;
  category_name: string;
  last_viewed_at: string | null;
  completed_at?: string;
}

export interface DashboardSummary {
  xp_total: number;
  categories: CategoryProgress[];
  in_progress_lessons: LessonProgressEntry[];
  completed_lessons: LessonProgressEntry[];
  continue_learning: LessonProgressEntry | null;
  stats: {
    total_questions_attempted: number;
    total_questions_correct: number;
    overall_accuracy_percent: number;
    total_lessons_completed: number;
    total_lessons_available: number;
  };
}
