'use client';

import { useCallback, useState } from 'react';

export interface ToastItem {
  id: number;
  message: string;
  variant?: 'success' | 'info' | 'error';
}

let nextToastId = 0;

export function useToast() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const showToast = useCallback((message: string, variant: ToastItem['variant'] = 'success') => {
    const id = ++nextToastId;
    setToasts((prev) => [...prev, { id, message, variant }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 2500);
  }, []);

  return { toasts, showToast };
}
