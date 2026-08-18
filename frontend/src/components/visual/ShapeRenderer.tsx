"use client";

type Shape =
  | { type: "circle"; cx: number; cy: number; r: number; rotation?: number }
  | { type: "rectangle"; x: number; y: number; width: number; height: number; rotation?: number }
  | { type: "triangle"; x: number; y: number; size: number; rotation?: number }
  | { type: "line"; x1: number; y1: number; x2: number; y2: number };

export function ShapeRenderer({ shapes, width = 400, height = 300 }: { shapes: Shape[]; width?: number; height?: number }) {
  return (
    <svg viewBox={`0 0 ${width} ${height}`} role="img" className="h-auto w-full">
      {shapes.map((shape, index) => {
        const transform = "rotation" in shape && shape.rotation ? `rotate(${shape.rotation})` : undefined;
        if (shape.type === "circle") return <circle key={index} cx={shape.cx} cy={shape.cy} r={shape.r} transform={transform} fill="none" stroke="currentColor" strokeWidth="3" />;
        if (shape.type === "rectangle") return <rect key={index} x={shape.x} y={shape.y} width={shape.width} height={shape.height} transform={transform} fill="none" stroke="currentColor" strokeWidth="3" />;
        if (shape.type === "triangle") {
          const { x, y, size } = shape;
          return <polygon key={index} points={`${x},${y - size / 2} ${x - size / 2},${y + size / 2} ${x + size / 2},${y + size / 2}`} transform={transform} fill="none" stroke="currentColor" strokeWidth="3" />;
        }
        return <line key={index} x1={shape.x1} y1={shape.y1} x2={shape.x2} y2={shape.y2} stroke="currentColor" strokeWidth="3" />;
      })}
    </svg>
  );
}
