import { AlertTriangle, CheckCircle2, Info, XCircle } from 'lucide-react';
import { ReactNode } from 'react';

type AlertVariant = 'error' | 'success' | 'info' | 'warning';

const ICONS: Record<AlertVariant, typeof Info> = {
  error: XCircle,
  success: CheckCircle2,
  info: Info,
  warning: AlertTriangle,
};

const CLASSES: Record<AlertVariant, string> = {
  error: 'bg-rose-50 text-rose-700 border-rose-200',
  success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  info: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  warning: 'bg-amber-50 text-amber-700 border-amber-200',
};

export default function Alert({
  variant = 'info',
  children,
}: {
  variant?: AlertVariant;
  children: ReactNode;
}) {
  const Icon = ICONS[variant];
  return (
    <div className={`flex items-start gap-2 border rounded-xl px-4 py-3 text-sm ${CLASSES[variant]}`}>
      <Icon className="w-4 h-4 mt-0.5 shrink-0" />
      <div>{children}</div>
    </div>
  );
}
