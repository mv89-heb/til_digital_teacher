import QuestionBlock from '@/components/practice/QuestionBlock';
import FormulaBlock from '@/components/learning/blocks/FormulaBlock';
import ImageBlock from '@/components/learning/blocks/ImageBlock';
import TableBlock from '@/components/learning/blocks/TableBlock';
import TextBlock from '@/components/learning/blocks/TextBlock';
import type {
  ContentBlock,
  FormulaBlockContent,
  ImageBlockContent,
  TableBlockContent,
  TextBlockContent,
} from '@/types/learning';

const SECTION_LABEL: Record<string, string> = {
  simple_explanation: 'הסבר פשוט',
  normal_explanation: 'הסבר מעמיק',
  solved_example: 'דוגמה פתורה',
  normal_method: 'שיטת פתרון',
  fast_method: '⚡ שיטה מהירה למבחן',
  common_mistakes: 'טעויות נפוצות',
  guided_practice: 'תרגול מודרך',
  summary: 'סיכום',
};

interface ContentBlockRendererProps {
  block: ContentBlock;
  token: string | null;
  onCorrect?: (xpEarned: number) => void;
}

export default function ContentBlockRenderer({ block, token, onCorrect }: ContentBlockRendererProps) {
  return (
    <div>
      <h3 className="text-sm font-bold text-indigo-600 mb-3 tracking-wide">
        {SECTION_LABEL[block.section] ?? block.section}
      </h3>

      {block.type === 'text' && <TextBlock content={block.content as TextBlockContent} />}
      {block.type === 'image' && <ImageBlock content={block.content as ImageBlockContent} />}
      {block.type === 'table' && <TableBlock content={block.content as TableBlockContent} />}
      {block.type === 'formula' && <FormulaBlock content={block.content as FormulaBlockContent} />}

      {block.type === 'embedded_question' &&
        (block.question ? (
          <QuestionBlock question={block.question} token={token} onCorrect={onCorrect} />
        ) : (
          <p className="text-slate-400 text-sm italic">שאלה זו אינה זמינה כרגע.</p>
        ))}

      {block.type === 'video' && <p className="text-slate-400 text-sm italic">וידאו — בקרוב.</p>}
      {block.type === 'interactive' && (
        <p className="text-slate-400 text-sm italic">תוכן אינטראקטיבי — בקרוב.</p>
      )}
    </div>
  );
}
