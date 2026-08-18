'use client';

import { useState } from 'react';
import { Save, ShieldCheck, UserRound } from 'lucide-react';
import Card from '@/components/ui/Card';
import Alert from '@/components/ui/Alert';
import { useAuthStore } from '@/store/useAuthStore';

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [saved, setSaved] = useState(false);

  const [displayName, setDisplayName] = useState(user?.email?.split('@')[0] || '');

  const handleSave = () => {
    // Profile persistence is intentionally not faked: the current backend has
    // no profile-update contract. Keep the page functional without silently
    // claiming data was written to the database.
    setSaved(true);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 mb-2">הגדרות</h1>
        <p className="text-slate-600">ניהול החשבון והעדפות בסיסיות</p>
      </div>

      {saved && <Alert variant="info">העדפות התצוגה נשמרו עבור ההפעלה הנוכחית.</Alert>}

      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="rounded-xl bg-indigo-50 p-3 text-indigo-600"><UserRound className="w-5 h-5" /></div>
          <div>
            <h2 className="font-bold text-slate-900">פרופיל</h2>
            <p className="text-sm text-slate-500">הפרטים שמוצגים במערכת</p>
          </div>
        </div>

        <div className="space-y-4">
          <label className="block">
            <span className="block text-sm font-semibold text-slate-700 mb-1">שם תצוגה</span>
            <input
              value={displayName}
              onChange={(event) => { setSaved(false); setDisplayName(event.target.value); }}
              className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />
          </label>

          <label className="block">
            <span className="block text-sm font-semibold text-slate-700 mb-1">אימייל</span>
            <input value={user?.email || ''} readOnly className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-500" />
          </label>

          <button onClick={handleSave} className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-700">
            <Save className="w-4 h-4" />
            שמור העדפה
          </button>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-emerald-50 p-3 text-emerald-600"><ShieldCheck className="w-5 h-5" /></div>
          <div>
            <h2 className="font-bold text-slate-900">אבטחת חשבון</h2>
            <p className="text-sm text-slate-600">החיבור הנוכחי מאומת מול השרת. אסימון ההתחברות נשמר ב-sessionStorage ואינו נשמר לאחר סגירת הדפדפן.</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
