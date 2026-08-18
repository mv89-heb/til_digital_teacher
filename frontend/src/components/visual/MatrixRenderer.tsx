"use client";

import { ShapeRenderer } from "./ShapeRenderer";

type Cell = { row: number; column: number; shapes: any[] };

type Props = {
  rows: number;
  columns: number;
  cells: Cell[];
  missingCell?: { row: number; column: number };
};

export function MatrixRenderer({ rows, columns, cells, missingCell }: Props) {
  const byPosition = new Map(cells.map((cell) => [`${cell.row}:${cell.column}`, cell]));
  return (
    <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>
      {Array.from({ length: rows * columns }, (_, index) => {
        const row = Math.floor(index / columns);
        const column = index % columns;
        const key = `${row}:${column}`;
        const cell = byPosition.get(key);
        const missing = missingCell?.row === row && missingCell?.column === column;
        return (
          <div key={key} className="aspect-square border p-1" aria-label={missing ? "תא חסר" : `שורה ${row + 1}, עמודה ${column + 1}`}>
            {missing ? <div className="flex h-full items-center justify-center text-2xl">?</div> : cell ? <ShapeRenderer shapes={cell.shapes} width={200} height={200} /> : null}
          </div>
        );
      })}
    </div>
  );
}
