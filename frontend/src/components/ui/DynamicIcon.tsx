import type { LucideProps } from 'lucide-react';
import { resolveIcon } from '@/lib/icons';

interface DynamicIconProps extends Omit<LucideProps, 'name'> {
  iconName: string | null | undefined;
}

// Icon names come from backend content data (Category.icon / Lesson.icon),
// so the concrete component can only be resolved at render time via lookup.
// lucide-react icons are stateless pure SVG components, so re-resolving the
// same name always yields the same rendered output — safe despite the lint
// heuristic below, which can't know that.
export default function DynamicIcon({ iconName, ...rest }: DynamicIconProps) {
  const IconComponent = resolveIcon(iconName);
  // eslint-disable-next-line react-hooks/static-components
  return <IconComponent {...rest} />;
}
