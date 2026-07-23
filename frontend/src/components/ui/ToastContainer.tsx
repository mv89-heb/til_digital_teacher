'use client';

import { AnimatePresence } from 'framer-motion';
import { Toast } from './Toast';
import type { ToastItem } from '@/lib/useToast';

export function ToastContainer({ toasts }: { toasts: ToastItem[] }) {
  return (
    <div className="fixed bottom-6 inset-x-0 flex flex-col items-center gap-2 z-50 pointer-events-none px-4">
      <AnimatePresence>
        {toasts.map((toast) => (
          <Toast key={toast.id} variant={toast.variant}>
            {toast.message}
          </Toast>
        ))}
      </AnimatePresence>
    </div>
  );
}
