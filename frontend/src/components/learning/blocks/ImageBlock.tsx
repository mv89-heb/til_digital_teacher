import type { ImageBlockContent } from '@/types/learning';

export default function ImageBlock({ content }: { content: ImageBlockContent }) {
  return (
    <figure className="my-2">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={content.url}
        alt={content.alt || content.caption || ''}
        className="rounded-xl border border-slate-200 max-w-full"
      />
      {content.caption && (
        <figcaption className="text-sm text-slate-500 mt-2 text-center">{content.caption}</figcaption>
      )}
    </figure>
  );
}
