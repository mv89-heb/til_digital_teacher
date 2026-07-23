'use client';

import { useAuthStore } from '@/store/useAuthStore';
import { Bell, Zap } from 'lucide-react';

export default function Topbar() {
  const { user } = useAuthStore();

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 sticky top-0 z-10 shadow-sm">
      <div>
        <h2 className="text-lg font-bold text-slate-800">
          שלום, {user?.email?.split('@')[0] || 'תלמיד'} 👋
        </h2>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5 bg-amber-50 text-amber-700 font-bold text-sm px-3 py-1.5 rounded-full">
          <Zap className="w-4 h-4 fill-amber-500 text-amber-500" />
          {user?.xp_total ?? 0} XP
        </div>

        <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-full transition-colors relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
        </button>

        <div className="h-8 w-px bg-slate-200 mx-1"></div>

        <div className="flex items-center gap-3">
          <div className="text-sm font-medium text-slate-700 hidden sm:block">
            {user?.email}
          </div>
          <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-500 to-indigo-500 text-white flex items-center justify-center font-bold text-sm shadow-sm border-2 border-white ring-2 ring-slate-100">
            {user?.email?.charAt(0).toUpperCase() || 'U'}
          </div>
        </div>
      </div>
    </header>
  );
}
