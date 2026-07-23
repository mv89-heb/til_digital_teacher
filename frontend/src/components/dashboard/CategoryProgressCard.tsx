import Badge from '@/components/ui/Badge';
import Card from '@/components/ui/Card';
import DynamicIcon from '@/components/ui/DynamicIcon';
import ProgressBar from '@/components/ui/ProgressBar';
import type { CategoryProgress, StudentLevelName } from '@/types/learning';

const LEVEL_LABEL: Record<StudentLevelName, string> = {
  beginner: 'מתחיל',
  basic: 'בסיסי',
  intermediate: 'בינוני',
  exam_ready: 'מוכן למבחן',
  advanced: 'מתקדם',
};

const LEVEL_VARIANT: Record<StudentLevelName, 'neutral' | 'warning' | 'info' | 'success'> = {
  beginner: 'neutral',
  basic: 'warning',
  intermediate: 'info',
  exam_ready: 'success',
  advanced: 'success',
};

export default function CategoryProgressCard({ category }: { category: CategoryProgress }) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <DynamicIcon iconName={category.icon} className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900">{category.name}</h3>
            <p className="text-xs text-slate-500">
              {category.lessons_completed}/{category.lessons_total} שיעורים הושלמו
            </p>
          </div>
        </div>
        <Badge variant={LEVEL_VARIANT[category.level]}>{LEVEL_LABEL[category.level]}</Badge>
      </div>

      <ProgressBar
        current={category.accuracy_percent}
        total={100}
        label={`${category.accuracy_percent}% הצלחה · ${category.questions_attempted} שאלות`}
      />
    </Card>
  );
}
