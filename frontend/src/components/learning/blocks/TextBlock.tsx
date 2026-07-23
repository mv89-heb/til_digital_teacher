import ReactMarkdown from 'react-markdown';
import type { TextBlockContent } from '@/types/learning';

export default function TextBlock({ content }: { content: TextBlockContent }) {
  return (
    <div className="markdown-content text-slate-700">
      <ReactMarkdown>{content.body}</ReactMarkdown>
    </div>
  );
}
