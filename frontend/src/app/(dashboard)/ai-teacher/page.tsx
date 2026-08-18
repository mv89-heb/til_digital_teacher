'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Brain, CheckCircle2, HelpCircle, Lightbulb, RotateCcw, Search, Send, Sparkles, Target, Trophy, BookOpen } from 'lucide-react';
import Card from '@/components/ui/Card';
import { getCategories, getTeacherLesson } from '@/lib/api';
import { useAuthStore } from '@/store/useAuthStore';
import type { Category } from '@/types/learning';

type Message = { role: 'user' | 'assistant'; text: string };
type TeacherMode = 'learn' | 'guided' | 'practice' | 'mistake';

const QUICK_PROMPTS = [
  { label: 'למד אותי נושא', icon: BookOpen, prompt: 'למד אותי את הנושא הזה מהבסיס, עם דוגמאות ותרגול.' },
  { label: 'איך פותרים?', icon: Lightbulb, prompt: 'איך פותרים שאלות מהסוג הזה? תן לי שיטת עבודה ברורה.' },
  { label: 'תרגל אותי', icon: Target, prompt: 'תרגל אותי עם שאלה אחת בכל פעם ואל תגלה מיד את התשובה.' },
  { label: 'למה טעיתי?', icon: RotateCcw, prompt: 'הסבר לי איך מנתחים טעות ומה הייתי צריך לזהות.' },
];

const cleanText = (value: unknown): string => {
  if (!value) return '';
  if (typeof value === 'string') return value;
  if (typeof value === 'object' && value !== null && 'body' in value) return String((value as { body?: unknown }).body ?? '');
  return '';
};
const lessonTopic = (q: any) => q?.subcategory || q?.skill || q?.main_category || q?.question_type || 'הנושא הנוכחי';

export default function AITeacherPage() {
  const token = useAuthStore((state) => state.token);
  const [categories, setCategories] = useState<Category[]>([]);
  const [mode, setMode] = useState<TeacherMode>('learn');
  const [input, setInput] = useState('');
  const [selectedQuestionId, setSelectedQuestionId] = useState<number | null>(null);
  const [search, setSearch] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({ categories: 0, lessons: 0, questions: 0 });
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', text: 'שלום! אני המורה האישי שלך. אני עובד ללא API חיצוני, ומכיר את חומרי הלימוד ואת מאגר השאלות דרך השרת. אפשר לבקש ממני ללמד נושא, להסביר שאלה, לתת רמז, לתרגל או לנתח טעות.' },
  ]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const categoryData = await getCategories();
        if (cancelled) return;
        setCategories(categoryData);
        setStats((current) => ({ ...current, categories: categoryData.length, lessons: categoryData.reduce((sum, c) => sum + c.lesson_count, 0) }));
      } catch (loadError) {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : 'לא ניתן לטעון את קטלוג הלימוד.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!token || !search.trim()) {
      setSearchResults([]);
      return;
    }
    const timer = window.setTimeout(async () => {
      try {
        const result = await getTeacherLesson(search.trim(), token, { mode: 'learn' });
        setSearchResults(result?.question ? [result.question] : []);
        if (result?.stats) setStats((current) => ({ ...current, questions: result.stats.total_questions, lessons: result.stats.total_lessons }));
      } catch {
        setSearchResults([]);
      }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [search, token]);

  const selectedQuestion = useMemo(() => searchResults.find((question) => question.id === selectedQuestionId) || null, [searchResults, selectedQuestionId]);

  const send = async (event: FormEvent) => {
    event.preventDefault();
    const prompt = input.trim();
    if (!prompt || sending || !token) return;
    setSending(true);
    setMessages((current) => [...current, { role: 'user', text: prompt }]);
    setInput('');
    try {
      const result = await getTeacherLesson(prompt, token, { mode, questionId: selectedQuestionId ?? undefined });
      const text = result?.answer || 'לא הצלחתי לבנות תשובה כרגע.';
      if (result?.stats) setStats((current) => ({ ...current, questions: result.stats.total_questions, lessons: result.stats.total_lessons }));
      setMessages((current) => [...current, { role: 'assistant', text }]);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'הבקשה למורה נכשלה.';
      setMessages((current) => [...current, { role: 'assistant', text: `לא הצלחתי להשלים את ההסבר כרגע. ${message}` }]);
    } finally {
      setSending(false);
    }
  };

  const ask = (prompt: string) => {
    setInput(prompt);
    window.setTimeout(() => document.getElementById('ai-teacher-input')?.focus(), 0);
  };

  const clearChat = () => {
    setSelectedQuestionId(null);
    setSearch('');
    setSearchResults([]);
    setMessages([{ role: 'assistant', text: 'התחלנו מחדש. בחר מצב לימוד או כתוב לי מה אתה רוצה ללמוד.' }]);
  };

  return (
    <div dir="rtl" className="mx-auto max-w-7xl space-y-6 pb-8">
      <header className="rounded-3xl bg-gradient-to-l from-indigo-700 via-indigo-600 to-violet-600 p-6 text-white shadow-lg md:p-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="mb-3 flex items-center gap-3"><div className="rounded-2xl bg-white/15 p-3 backdrop-blur"><Brain className="h-7 w-7" /></div><div><p className="text-sm font-medium text-indigo-100">מרכז ההוראה החכם</p><h1 className="text-3xl font-black md:text-4xl">המורה האישי שלך</h1></div></div>
            <p className="max-w-2xl text-indigo-50">מורה מקומי שמכיר את תוכן הלימוד ואת מאגר השאלות של המערכת. הוא מסביר, נותן רמזים ומלמד שיטת פתרון — בלי API חיצוני ובלי להוריד את כל המאגר לדפדפן.</p>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center text-sm md:min-w-[310px]">
            <div className="rounded-2xl bg-white/10 p-3 backdrop-blur"><div className="text-2xl font-black">{stats.categories}</div><div className="text-indigo-100">תחומים</div></div>
            <div className="rounded-2xl bg-white/10 p-3 backdrop-blur"><div className="text-2xl font-black">{stats.lessons}</div><div className="text-indigo-100">שיעורים</div></div>
            <div className="rounded-2xl bg-white/10 p-3 backdrop-blur"><div className="text-2xl font-black">{stats.questions || '—'}</div><div className="text-indigo-100">שאלות במאגר</div></div>
          </div>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="space-y-4">
          <Card className="p-4">
            <div className="mb-3 flex items-center justify-between"><h2 className="font-bold text-slate-900">מצב הוראה</h2><Sparkles className="h-4 w-4 text-indigo-600" /></div>
            <div className="space-y-2">{([['learn','למד אותי','הסבר מסודר מהבסיס'],['guided','פתרון מודרך','רמזים לפני תשובה'],['practice','תרגול','שאלה אחת בכל פעם'],['mistake','ניתוח טעות','להבין למה טעינו']] as const).map(([value,title,subtitle]) => <button key={value} type="button" onClick={() => setMode(value)} className={`w-full rounded-xl border p-3 text-right transition ${mode===value?'border-indigo-300 bg-indigo-50 text-indigo-900':'border-slate-200 bg-white hover:bg-slate-50'}`}><div className="font-semibold">{title}</div><div className="mt-0.5 text-xs text-slate-500">{subtitle}</div></button>)}</div>
          </Card>
          <Card className="p-4">
            <div className="mb-3 flex items-center gap-2 font-bold text-slate-900"><Search className="h-4 w-4 text-indigo-600" /> חיפוש חכם במאגר</div>
            <input value={search} onChange={(event)=>setSearch(event.target.value)} placeholder="שברים, אנלוגיות, מטריצות..." className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
            <div className="mt-3 max-h-72 space-y-2 overflow-y-auto">{searchResults.map((question)=><button key={question.id} type="button" onClick={()=>{setSelectedQuestionId(question.id);setMode('guided');ask('תסביר לי את השאלה שבחרתי שלב־אחר־שלב.')}} className={`w-full rounded-xl border p-3 text-right text-sm hover:border-indigo-300 hover:bg-indigo-50 ${selectedQuestionId===question.id?'border-indigo-300 bg-indigo-50':'border-slate-200'}`}><div className="mb-1 flex items-center gap-2 text-xs text-indigo-600"><HelpCircle className="h-3.5 w-3.5" /> {lessonTopic(question)}</div><div className="line-clamp-3 text-slate-700">{cleanText(question.body)}</div></button>)}{!searchResults.length&&!search.trim()&&<p className="py-4 text-center text-xs text-slate-500">הקלד נושא או מילת מפתח כדי לחפש.</p>}{!searchResults.length&&search.trim()&&<p className="py-4 text-center text-xs text-slate-500">אין התאמה כרגע. נסה ניסוח אחר.</p>}</div>
          </Card>
        </aside>

        <main className="min-w-0 space-y-4">
          <Card className="overflow-hidden">
            <div className="border-b border-slate-200 bg-white p-4"><div className="flex flex-wrap gap-2">{QUICK_PROMPTS.map(({label,icon:Icon,prompt})=><button key={label} type="button" onClick={()=>ask(prompt)} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700"><Icon className="h-4 w-4" />{label}</button>)}<button type="button" onClick={clearChat} className="mr-auto inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-slate-500 hover:bg-slate-100"><RotateCcw className="h-4 w-4" /> נקה שיחה</button></div></div>
            <div className="min-h-[500px] max-h-[620px] space-y-4 overflow-y-auto bg-slate-50 p-4 md:p-6">{messages.map((message,index)=><div key={`${index}-${message.role}`} className={`flex ${message.role==='user'?'justify-start':'justify-end'}`}><div className={`max-w-[88%] rounded-2xl px-4 py-3 shadow-sm md:max-w-[78%] ${message.role==='user'?'bg-indigo-600 text-white':'border border-slate-200 bg-white text-slate-800'}`}><div className="mb-1 flex items-center gap-2 text-xs font-bold opacity-70">{message.role==='user'?'אתה':<><Brain className="h-3.5 w-3.5" /> המורה</>}</div><div className="whitespace-pre-wrap leading-7">{message.text}</div></div></div>)}{sending&&<div className="flex justify-end"><div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500">המורה טוען ידע רלוונטי...</div></div>}</div>
            <form onSubmit={send} className="border-t border-slate-200 bg-white p-4"><div className="flex gap-3"><input id="ai-teacher-input" value={input} onChange={(event)=>setInput(event.target.value)} placeholder="שאל את המורה כל דבר על הלמידה..." className="min-w-0 flex-1 rounded-2xl border border-slate-300 px-4 py-3 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" /><button type="submit" disabled={sending||!input.trim()||!token} className="rounded-2xl bg-indigo-600 px-5 text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50" aria-label="שלח"><Send className="h-5 w-5" /></button></div><p className="mt-2 text-xs text-slate-500">אין חיבור ל־OpenAI/Gemini/Claude. המורה משתמש בידע המקומי ובמאגר השאלות דרך השרת.</p></form>
          </Card>
          {selectedQuestionId&&<Card className="border-indigo-100 bg-indigo-50/50 p-5"><div className="mb-3 flex items-center gap-2 font-bold text-indigo-900"><Trophy className="h-5 w-5" /> השאלה שנבחרה</div><p className="leading-7 text-slate-800">{selectedQuestion?cleanText(selectedQuestion.body):`שאלה #${selectedQuestionId} נטענה למורה.`}</p><div className="mt-4 flex flex-wrap gap-2"><button type="button" onClick={()=>{setMode('guided');ask('תן לי רמז בלבד לשאלה הזו, בלי לגלות את התשובה.')}} className="inline-flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-sm font-semibold text-indigo-700 shadow-sm"><Lightbulb className="h-4 w-4" /> תן רמז</button><button type="button" onClick={()=>{setMode('learn');ask('הסבר לי את הפתרון המלא לשאלה הזו ולמה כל שלב נכון.')}} className="inline-flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-sm font-semibold text-indigo-700 shadow-sm"><CheckCircle2 className="h-4 w-4" /> הסבר פתרון</button></div></Card>}
          {error&&<div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">לא הצלחתי לטעון את קטלוג הלימוד: {error}</div>}
          {loading&&<div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-500">טוען קטלוג לימוד...</div>}
        </main>
      </div>
    </div>
  );
}
