'use client';

import { FormEvent, useState } from 'react';
import { Bot, Send, Sparkles } from 'lucide-react';
import Card from '@/components/ui/Card';

type Message = { role: 'user' | 'assistant'; text: string };

function basicTutorReply(question: string): string {
  const normalized = question.trim().toLowerCase();
  if (!normalized) return 'כתוב שאלה ואעזור לך לפרק אותה לשלבים.';
  if (normalized.includes('לא מבין') || normalized.includes('תסביר')) {
    return 'בשמחה. נתחיל מהרעיון המרכזי, נפרק אותו לחלקים קטנים, ואז נפתור דוגמה יחד. כתוב גם איזה חלק בדיוק לא ברור לך.';
  }
  if (normalized.includes('מתמט') || normalized.includes('חשבון')) {
    return 'בוא נעבוד שלב־שלב: כתוב את התרגיל, מה ניסית עד עכשיו, ובאיזה שלב נתקעת. כך אוכל להסביר את הדרך ולא רק לתת תשובה.';
  }
  return 'אני כאן כמורה: כתוב את השאלה, הכיתה או הנושא, ומה כבר ניסית. נבנה יחד הסבר ברור שלב־אחר־שלב.';
}

export default function AITeacherPage() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', text: 'שלום! אני מורה AI. שאל אותי על חומר הלימוד ואעזור לך להבין אותו שלב־אחר־שלב.' },
  ]);

  const send = (event: FormEvent) => {
    event.preventDefault();
    const question = input.trim();
    if (!question) return;
    setMessages((current) => [...current, { role: 'user', text: question }, { role: 'assistant', text: basicTutorReply(question) }]);
    setInput('');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <div className="rounded-xl bg-indigo-600 p-3 text-white"><Bot className="w-6 h-6" /></div>
          <h1 className="text-3xl font-bold text-slate-900">מורה AI</h1>
        </div>
        <p className="text-slate-600">עזרה לימודית אינטראקטיבית, עם דגש על הסבר ולא רק על תשובה.</p>
      </div>

      <Card className="overflow-hidden">
        <div className="min-h-[420px] max-h-[520px] overflow-y-auto p-5 space-y-4 bg-slate-50">
          {messages.map((message, index) => (
            <div key={index} className={`flex ${message.role === 'user' ? 'justify-start' : 'justify-end'}`}>
              <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${message.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-white border border-slate-200 text-slate-800 shadow-sm'}`}>
                {message.text}
              </div>
            </div>
          ))}
        </div>

        <form onSubmit={send} className="border-t border-slate-200 p-4 bg-white flex gap-3">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="כתוב שאלה..."
            className="flex-1 rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
          />
          <button type="submit" className="rounded-xl bg-indigo-600 text-white px-5 hover:bg-indigo-700" aria-label="שלח">
            <Send className="w-5 h-5" />
          </button>
        </form>
      </Card>

      <div className="flex items-start gap-3 rounded-xl border border-indigo-100 bg-indigo-50 p-4 text-sm text-indigo-800">
        <Sparkles className="w-5 h-5 shrink-0" />
        <span>זהו מנגנון בסיסי שעובד ללא תלות בספק AI חיצוני. שכבת מודל אמיתית תוכל להתחבר אליו בהמשך בלי לשנות את הניווט או את חוויית המשתמש.</span>
      </div>
    </div>
  );
}
