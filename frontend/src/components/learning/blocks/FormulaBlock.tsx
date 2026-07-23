'use client';

import katex from 'katex';
import 'katex/dist/katex.min.css';
import { useMemo } from 'react';
import type { FormulaBlockContent } from '@/types/learning';

export default function FormulaBlock({ content }: { content: FormulaBlockContent }) {
  const html = useMemo(() => {
    try {
      return katex.renderToString(content.latex, { throwOnError: false, displayMode: true });
    } catch {
      return content.latex;
    }
  }, [content.latex]);

  return (
    <div
      className="my-2 py-3 px-4 bg-slate-50 rounded-xl border border-slate-200 overflow-x-auto text-center"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
