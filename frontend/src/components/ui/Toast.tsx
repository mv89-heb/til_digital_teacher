'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';

type ToastVariant = 'success' | 'info' | 'error';

const VARIANT_CLASSES: Record<ToastVariant, string> = {
  success: 'bg-emerald-600',
  info: 'bg-indigo-600',
  error: 'bg-rose-600',
};

export function Toast({
  icon,
  children,
  variant = 'success',
}: {
  icon?: ReactNode;
  children: ReactNode;
  variant?: ToastVariant;
}) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -10, scale: 0.9 }}
      transition={{ duration: 0.2 }}
      className={`flex items-center gap-2 text-white font-semibold px-4 py-3 rounded-xl shadow-lg pointer-events-auto ${VARIANT_CLASSES[variant]}`}
    >
      {icon}
      {children}
    </motion.div>
  );
}
