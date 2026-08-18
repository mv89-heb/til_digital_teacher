'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import { Bell, Zap, ChevronLeft } from 'lucide-react';

const pageTitles: Record<string, string> = {
  '/dashboard': 'לוח הבקרה',
  '/learn': 'מרכז הלמידה',
  '/practice': 'תרגול שאלות',
  '/exam': 'סימולציות',
  '/ai-teacher': 'המורה האישי',
  '/settings': 'הגדרות',
};

export default function Topbar() {
  const { user } = useAuthStore();
  const pathname = usePathname();
  const title = Object.entries(pageTitles).find(([path]) => pathname === path || pathname.startsWith(`${path}/`))?.[1] ?? 'TIL Teacher';

  return (
    <header className="h-20 bg-white/95 backdrop-blur border-b border-slate-200/80 flex items-center justify-between px-5 md:px-8 sticky top-0 z-10">
      <div className="min-w-0">
        <div className="text-xs font-medium text-slate-400 mb-0.5">TIL Teacher</div>
        <h2 className="text-xl font-extrabold text-slate-900 truncate">{title}</h2>
      </div>

      <div className="flex items-center gap-2 md:gap-4">
        <Link href="/practice" className="hidden sm:flex items-center gap-2 rounded-xl bg-indigo-50 text-indigo-700 px-3 py-2 text-sm font-bold hover:bg-indigo-100 transition-colors">
          <Zap className="w-4 h-4" />
          תרגול עכשיו
          <ChevronLeft className="w-3.5 h-3.5" />
        </Link>

        <div className="flex items-center gap-1.5 bg-amber-50 border border-amber-100 text-amber-700 font-bold text-sm px-3 py-2 rounded-xl">
          <Zap className="w-4 h-4 fill-amber-500 text-amber-500" />
          {user?.xp_total ?? 0} XP
        </div>

        <button aria-label="התראות" className="p-2.5 text-slate-400 hover:text-slate-700 hover:bg-slate-50 rounded-xl transition-colors relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
        </button>

        <div className="h-9 w-px bg-slate-200 hidden md:block"></div>

        <div className="flex items-center gap-3">
          <div className="text-sm font-medium text-slate-600 hidden lg:block max-w-48 truncate">
            {user?.email}
          </div>
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-500 text-white flex items-center justify-center font-extrabold text-sm shadow-md shadow-indigo-100 border-2 border-white">
            {user?.email?.charAt(0).toUpperCase() || 'U'}
          </div>
        </div>
      </div>
    </header>
  );
}
