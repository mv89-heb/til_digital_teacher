import { HTMLAttributes, ReactNode } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  hoverable?: boolean;
}

export default function Card({ children, hoverable = false, className = '', ...rest }: CardProps) {
  return (
    <div
      className={`bg-white rounded-2xl border border-slate-200 shadow-sm ${
        hoverable ? 'hover:shadow-md hover:border-indigo-200 transition-all' : ''
      } ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}
