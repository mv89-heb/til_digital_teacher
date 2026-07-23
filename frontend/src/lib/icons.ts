import { BookOpen, Calculator, LucideIcon, MessageSquare, Shapes, Brain, TrendingUp } from 'lucide-react';

const ICON_MAP: Record<string, LucideIcon> = {
  calculator: Calculator,
  'trending-up': TrendingUp,
  verbal: MessageSquare,
  figural: Shapes,
  logic: Brain,
};

export function resolveIcon(name: string | null | undefined): LucideIcon {
  if (!name) return BookOpen;
  return ICON_MAP[name] || BookOpen;
}
