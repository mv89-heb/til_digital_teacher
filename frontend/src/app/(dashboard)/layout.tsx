'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/layout/Sidebar';
import Topbar from '@/components/layout/Topbar';
import Spinner from '@/components/ui/Spinner';
import { fetchApi } from '@/lib/api';
import { useAuthStore } from '@/store/useAuthStore';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { token, login, logout } = useAuthStore();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!token) {
      router.replace('/login');
      return;
    }

    fetchApi('/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => {
        login(res.user, token);
        setChecked(true);
      })
      .catch(() => {
        logout();
        router.replace('/login');
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  if (!checked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Spinner className="w-8 h-8" />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden text-right" dir="rtl">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
