"use client";

import { MatrixRenderer } from "../visual/MatrixRenderer";
import { ShapeRenderer } from "../visual/ShapeRenderer";

type Answer = {
  id: number;
  answer_text: unknown;
  order: number;
};

type ExamQuestion = {
  id: number;
  question_type?: string | null;
  prompt: unknown;
  visual_data?: any;
  answers: Answer[];
};

type Props = {
  question: ExamQuestion;
  selectedAnswerId?: number | null;
  disabled?: boolean;
  onSelect: (answerId: number) => void;
};

function richText(value: unknown): string {
  if (typeof value === "string") return value;
  if (value && typeof value === "object" && "body" in value) {
    const body = (value as { body?: unknown }).body;
    return typeof body === "string" ? body : JSON.stringify(body);
  }
  return value == null ? "" : JSON.stringify(value);
}

export function QuestionRenderer({ question, selectedAnswerId, disabled, onSelect }: Props) {
  const visual = question.visual_data;

  return (
    <section className="space-y-6" dir="rtl" aria-label="שאלה במבחן">
      <div className="text-lg leading-8 whitespace-pre-wrap">{richText(question.prompt)}</div>

      {visual?.type === "matrix" ? (
        <MatrixRenderer
          rows={visual.rows}
          columns={visual.columns}
          cells={visual.cells ?? []}
          missingCell={visual.missingCell}
        />
      ) : null}

      {visual?.type === "shapes" ? (
        <ShapeRenderer shapes={visual.shapes ?? []} width={visual.width ?? 400} height={visual.height ?? 300} />
      ) : null}

      <div className="grid gap-3" role="radiogroup" aria-label="אפשרויות תשובה">
        {question.answers
          .slice()
          .sort((a, b) => a.order - b.order)
          .map((answer, index) => {
            const selected = selectedAnswerId === answer.id;
            return (
              <button
                key={answer.id}
                type="button"
                disabled={disabled}
                role="radio"
                aria-checked={selected}
                onClick={() => onSelect(answer.id)}
                className={`rounded-xl border p-4 text-right transition ${
                  selected ? "border-blue-600 bg-blue-50 ring-2 ring-blue-200" : "hover:border-slate-400"
                } disabled:cursor-not-allowed disabled:opacity-60`}
              >
                <span className="me-3 font-bold">{String.fromCharCode(65 + index)}.</span>
                {richText(answer.answer_text)}
              </button>
            );
          })}
      </div>
    </section>
  );
}
