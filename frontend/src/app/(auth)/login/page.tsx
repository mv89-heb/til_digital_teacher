// frontend/src/app/(auth)/login/page.tsx

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Eye, EyeOff, GraduationCap, Loader2, Lock, Mail } from 'lucide-react';
import { fetchApi } from '@/lib/api';
import { useAuthStore } from '@/store/useAuthStore';
import Alert from '@/components/ui/Alert';

function isValidEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [touched, setTouched] = useState({ email: false, password: false });
  const [error, setError] = useState('');
  const [shake, setShake] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const router = useRouter();
  const login = useAuthStore((state) => state.login);

  const emailError = touched.email && !isValidEmail(email) ? 'כתובת אימייל לא תקינה' : '';
  const passwordError = touched.password && password.length < 1 ? 'יש להזין סיסמה' : '';
  const canSubmit = isValidEmail(email) && password.length > 0 && !isLoading;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched({ email: true, password: true });
    if (!isValidEmail(email) || password.length === 0) return;

    setError('');
    setIsLoading(true);

    try {
      const response = await fetchApi('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      login(response.data.user, response.data.token);
      setSuccess(true);
      setTimeout(() => router.push('/dashboard'), 400);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'משהו השתבש, אנא נסה שוב.');
      setShake(true);
      setTimeout(() => setShake(false), 500);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden bg-slate-50">
      {/* subtle animated gradient background */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-[-10%] right-[-10%] w-[420px] h-[420px] rounded-full bg-indigo-200/40 blur-3xl" />
        <div className="absolute bottom-[-15%] left-[-10%] w-[420px] h-[420px] rounded-full bg-blue-200/40 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="w-full max-w-md"
      >
        {/* branding */}
        <div className="flex flex-col items-center mb-6">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-blue-500 text-white flex items-center justify-center shadow-lg shadow-indigo-200 mb-3">
            <GraduationCap className="w-7 h-7" />
          </div>
          <span className="font-extrabold text-lg text-slate-900">TIL Teacher</span>
        </div>

        <motion.div
          animate={shake ? { x: [0, -8, 8, -8, 8, 0] } : {}}
          transition={{ duration: 0.4 }}
          className="bg-white/80 backdrop-blur-xl p-8 rounded-3xl shadow-xl border border-white/60"
        >
          <h2 className="text-2xl font-bold text-center text-slate-900 mb-1">ברוך שובך!</h2>
          <p className="text-center text-slate-500 mb-7 text-sm">הזן את פרטיך כדי להמשיך בלמידה</p>

          {error && (
            <div className="mb-5">
              <Alert variant="error">{error}</Alert>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">דואר אלקטרוני</label>
              <div className="relative">
                <Mail className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onBlur={() => setTouched((t) => ({ ...t, email: true }))}
                  className={`w-full pr-10 pl-4 py-3 rounded-xl border outline-none transition-all text-left ${
                    emailError
                      ? 'border-rose-300 focus:ring-2 focus:ring-rose-200'
                      : 'border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
                  }`}
                  dir="ltr"
                  placeholder="name@example.com"
                />
              </div>
              {emailError && <p className="text-xs text-rose-600 mt-1">{emailError}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">סיסמה</label>
              <div className="relative">
                <Lock className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onBlur={() => setTouched((t) => ({ ...t, password: true }))}
                  className={`w-full pr-10 pl-10 py-3 rounded-xl border outline-none transition-all text-left ${
                    passwordError
                      ? 'border-rose-300 focus:ring-2 focus:ring-rose-200'
                      : 'border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
                  }`}
                  dir="ltr"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {passwordError && <p className="text-xs text-rose-600 mt-1">{passwordError}</p>}
            </div>

            <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer select-none pt-1">
              <input type="checkbox" className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500" />
              זכור אותי
            </label>

            <button
              type="submit"
              disabled={!canSubmit}
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white font-bold py-3 rounded-xl hover:bg-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
              {success ? 'התחברת בהצלחה!' : isLoading ? 'מתחבר...' : 'התחבר'}
            </button>
          </form>

          <p className="text-center mt-6 text-sm text-slate-600">
            עדיין אין לך חשבון?{' '}
            <Link href="/register" className="text-indigo-600 font-bold hover:underline">
              הירשם עכשיו
            </Link>
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}
