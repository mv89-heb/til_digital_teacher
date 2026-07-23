'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { LayoutDashboard, BookOpen, Bot, Settings, LogOut } from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';

export default function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const navItems = [
    { name: 'לוח בקרה', href: '/dashboard', icon: LayoutDashboard },
    { name: 'מרכז למידה', href: '/learn', icon: BookOpen },
    { name: 'מורה AI', href: '/ai-teacher', icon: Bot },
    { name: 'הגדרות', href: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-white border-l border-slate-200 flex flex-col h-full shadow-sm z-20">
      <div className="h-16 flex items-center px-6 border-b border-slate-200">
        <div className="font-extrabold text-xl bg-clip-text text-transparent bg-gradient-to-l from-blue-600 to-indigo-600">
          TIL Teacher
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto py-6 px-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all font-medium ${
                isActive 
                  ? 'bg-blue-50 text-blue-700 shadow-sm border border-blue-100' 
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-200">
        <button 
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 w-full rounded-xl text-slate-600 hover:bg-red-50 hover:text-red-600 transition-all font-medium"
        >
          <LogOut className="w-5 h-5" />
          התנתק
        </button>
      </div>
    </aside>
  );
}
