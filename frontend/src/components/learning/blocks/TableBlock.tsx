import type { TableBlockContent } from '@/types/learning';

export default function TableBlock({ content }: { content: TableBlockContent }) {
  return (
    <div className="overflow-x-auto my-2 rounded-xl border border-slate-200">
      <table className="w-full text-sm text-right">
        <thead className="bg-slate-50">
          <tr>
            {content.headers.map((header, i) => (
              <th key={i} className="px-4 py-2.5 font-bold text-slate-700 border-b border-slate-200">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {content.rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-b border-slate-100 last:border-0">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-4 py-2.5 text-slate-600">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
