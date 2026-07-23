import { Clock } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import DynamicIcon from '@/components/ui/DynamicIcon';
import type { LessonDetail } from '@/types/learning';

const DIFFICULTY_LABEL: Record<string, string> = {
  beginner: 'למתחילים',
  intermediate: 'בינוני',
  advanced: 'מתקדם',
};

export default function LessonHeader({ lesson }: { lesson: LessonDetail }) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 text-sm text-slate-500 mb-3">
        <span>{lesson.category.name}</span>
      </div>

      <div className="flex items-start gap-4">
        <div className="w-14 h-14 shrink-0 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
          <DynamicIcon iconName={lesson.icon} className="w-7 h-7" />
        </div>
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 mb-1">{lesson.title}</h1>
          {lesson.description && <p className="text-slate-600">{lesson.description}</p>}
        </div>
      </div>

      <div className="flex items-center gap-2 mt-4">
        {lesson.difficulty_level && (
          <Badge variant="info">{DIFFICULTY_LABEL[lesson.difficulty_level] ?? lesson.difficulty_level}</Badge>
        )}
        {lesson.estimated_duration && (
          <Badge icon={<Clock className="w-3 h-3" />}>{lesson.estimated_duration} דקות</Badge>
        )}
      </div>
    </div>
  );
}
