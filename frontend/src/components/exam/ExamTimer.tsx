"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type Props = {
  sessionId: number;
  expiresAt: string;
  onExpire: () => void;
};

const keyFor = (sessionId: number) => `exam-session:${sessionId}`;

export function ExamTimer({ sessionId, expiresAt, onExpire }: Props) {
  const expiryMs = useMemo(() => new Date(expiresAt).getTime(), [expiresAt]);
  const [now, setNow] = useState(() => Date.now());
  const expiredRef = useRef(false);

  useEffect(() => {
    const key = keyFor(sessionId);
    // LocalStorage is only a UI recovery aid. The server expiry remains authoritative.
    localStorage.setItem(key, JSON.stringify({ expiresAt, savedAt: Date.now() }));
  }, [sessionId, expiresAt]);

  useEffect(() => {
    const interval = window.setInterval(() => setNow(Date.now()), 250);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    if (now >= expiryMs && !expiredRef.current) {
      expiredRef.current = true;
      onExpire();
    }
  }, [now, expiryMs, onExpire]);

  const remaining = Math.max(0, expiryMs - now);
  const totalSeconds = Math.ceil(remaining / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  return (
    <div
      aria-live="polite"
      aria-label="זמן שנותר"
      className={remaining <= 60_000 ? "font-bold text-red-600" : "font-semibold"}
    >
      {minutes}:{seconds.toString().padStart(2, "0")}
    </div>
  );
}
