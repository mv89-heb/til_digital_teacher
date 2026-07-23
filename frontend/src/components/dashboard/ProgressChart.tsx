'use client';

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { CategoryProgress } from '@/types/learning';

export default function ProgressChart({ categories }: { categories: CategoryProgress[] }) {
  const data = categories.map((c) => ({
    name: c.name,
    'אחוז הצלחה': c.accuracy_percent,
  }));

  return (
    <div className="h-64 w-full" dir="ltr">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} reversed />
          <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: '#64748b' }} />
          <Tooltip
            contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 13 }}
            formatter={(value) => [`${value}%`, 'אחוז הצלחה']}
          />
          <Bar dataKey="אחוז הצלחה" fill="#6366f1" radius={[8, 8, 0, 0]} maxBarSize={48} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
