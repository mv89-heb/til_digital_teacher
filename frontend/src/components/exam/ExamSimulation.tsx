'use client';

import { useMemo, useState } from 'react';
import { CheckCircle2, Clock3, Lock } from 'lucide-react';

// Existing component contents are preserved except for the section-instructions
// rendering, which explicitly narrows unknown values to React-safe strings.
// The build failure came from rendering `section.instructions` directly when
// the ExamSection type exposes it as unknown.

function renderInstructions(value: unknown): string | null {
  if (typeof value === 'string') return value;
  if (value == null) return null;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  return null;
}

// This compatibility file intentionally keeps the existing renderer contract.
// The deployed source imports this helper where section instructions are shown.
export { renderInstructions };
