'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  BookOpen,
  Brain,
  Bot,
  Settings,
  LogOut,
  ClipboardCheck,
  Sparkles,
  ChevronLeft,
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';

export default function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const primaryItems = [
    { name: 'לוח בקרה', href: '/dashboard', icon: LayoutDashboard },
    { name: 'מרכז למידה', href: '/learn', icon: BookOpen },
    { name: 'תרגול שאלות', href: '/practice', icon: Brain },
    { name: 'סימולציות', href: '/exam', icon: ClipboardCheck },
    { name: 'מורה AI', href: '/ai-teacher', icon: Bot },
  ];

  const secondaryItems = [
    { name: 'הגדרות', href: '/settings', icon: Settings },
  ];

  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);

  return (
    <aside className="w-64 bg-white border-l border-slate-200/80 flex flex-col h-full shadow-[0_0_30px_rgba(15,23,42,0.04)] z-20">
      <div className="h-20 flex items-center px-5 border-b border-slate-100">
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-600 to-blue-500 text-white flex items-center justify-center shadow-lg shadow-indigo-200 group-hover:scale-105 transition-transform">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="font-extrabold text-lg tracking-tight text-slate-900">TIL Teacher</div>
            <div className="text-[11px] text-slate-400 font-medium">הכנה חכמה למבחני תיל</div>
          </div>
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto py-5 px-3">
        <div className="px-3 mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">למידה</div>
        <div className="space-y-1">
          {primaryItems.map((item) => {
            const active = isActive(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`group flex items-center gap-3 px-3 py-3 rounded-2xl transition-all font-semibold ${
                  active
                    ? 'bg-indigo-50 text-indigo-700 shadow-sm'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-950'
                }`}
              >
                <span className={`w-9 h-9 rounded-xl flex items-center justify-center transition-colors ${active ? 'bg-white text-indigo-600 shadow-sm' : 'bg-slate-50 text-slate-400 group-hover:text-slate-600'}`}>
                  <Icon className="w-5 h-5" />
                </span>
                <span className="flex-1">{item.name}</span>
                {active && <ChevronLeft className="w-4 h-4 text-indigo-400" />}
              </Link>
            );
          })}
        </div>

        <div className="px-3 mb-2 mt-7 text-[11px] font-bold uppercase tracking-wider text-slate-400">מערכת</div>
        <div className="space-y-1">
          {secondaryItems.map((item) => {
            const active = isActive(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-3 rounded-2xl transition-all font-medium ${
                  active ? 'bg-slate-100 text-slate-900' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.name}
              </Link>
            );
          })}
        </div>

        <Link href="/practice" className="block mt-7 mx-1 rounded-2xl bg-gradient-to-br from-indigo-600 to-blue-600 p-4 text-white shadow-lg shadow-indigo-200 hover:-translate-y-0.5 transition-transform">
          <div className="flex items-center gap-2 mb-1">
            <Brain className="w-4 h-4" />
            <span className="font-bold text-sm">תרגול מהיר</span>
          </div>
          <p className="text-xs text-indigo-100 leading-relaxed">קפוץ ישר לשאלות שמתאימות לרמה שלך.</p>
        </Link>
      </nav>

      <div className="p-3 border-t border-slate-100">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-3 w-full rounded-2xl text-slate-500 hover:bg-red-50 hover:text-red-600 transition-all font-medium"
        >
          <LogOut className="w-5 h-5" />
          התנתק
        </button>
      </div>
    </aside>
  );
}
