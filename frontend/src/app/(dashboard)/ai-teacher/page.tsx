'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  BookOpen,
  Brain,
  CheckCircle2,
  ChevronLeft,
  HelpCircle,
  Lightbulb,
  MessageCircle,
  RotateCcw,
  Search,
  Send,
  Sparkles,
  Target,
  Trophy,
} from 'lucide-react';
import Card from '@/components/ui/Card';
import { getCategories, getQuestionBank } from '@/lib/api';
import { useAuthStore } from '@/store/useAuthStore';
import type { Category, Question } from '@/types/learning';

type Message = {
  role: 'user' | 'assistant';
  text: string;
};

type TeacherMode = 'learn' | 'guided' | 'practice' | 'mistake';

type Intent =
  | 'greeting'
  | 'explain'
  | 'practice'
  | 'mistake'
  | 'question'
  | 'topic'
  | 'strategy'
  | 'difficulty'
  | 'fallback';

const QUICK_PROMPTS = [
  { label: 'למד אותי נושא', icon: BookOpen, prompt: 'למד אותי את הנושא הזה מהבסיס, עם דוגמאות ותרגול.' },
  { label: 'איך פותרים?', icon: Lightbulb, prompt: 'איך פותרים שאלות מהסוג הזה? תן לי שיטת עבודה ברורה.' },
  { label: 'תרגל אותי', icon: Target, prompt: 'תרגל אותי עם שאלה אחת בכל פעם ואל תגלה מיד את התשובה.' },
  { label: 'למה טעיתי?', icon: RotateCcw, prompt: 'הסבר לי איך מנתחים טעות ומה הייתי צריך לזהות.' },
];

const normalize = (value: string) =>
  value
    .toLowerCase()
    .replace(/[\u200f\u200e]/g, '')
    .replace(/[.,!?;:()\[\]{}"']/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const cleanRichText = (value: unknown): string => {
  if (!value) return '';
  if (typeof value === 'string') return value;
  if (typeof value === 'object' && value !== null && 'body' in value) {
    return String((value as { body?: unknown }).body ?? '');
  }
  return '';
};

const questionText = (question: Question) => cleanRichText(question.body);

function classifyIntent(input: string): Intent {
  const text = normalize(input);
  if (!text) return 'fallback';
  if (/^(שלום|היי|הי|אהלן|בוקר טוב|ערב טוב)/.test(text)) return 'greeting';
  if (/(תרגל|תרגול|שאלה נוספת|תן לי שאלה|בוא נתרגל)/.test(text)) return 'practice';
  if (/(טעיתי|טעות|למה זה לא נכון|למה טעיתי|שגיאה)/.test(text)) return 'mistake';
  if (/(איך פותרים|איך לפתור|שיטת פתרון|אסטרטגיה|טיפ|טכניקה)/.test(text)) return 'strategy';
  if (/(קשה|לא מבין|לא הבנתי|תסביר|הסבר|מה זה|מה הכוונה)/.test(text)) return 'explain';
  if (/(שאלה|תשובה|אפשרות|מסיח|נכון|נכונה)/.test(text)) return 'question';
  if (/(נושא|ללמוד|לימוד|למד אותי|שיעור|פרק)/.test(text)) return 'topic';
  if (/(רמה|קושי|קל|בינוני|קשה|בחינה|מבחן)/.test(text)) return 'difficulty';
  return 'fallback';
}

function findRelevantQuestions(input: string, questions: Question[], limit = 4): Question[] {
  const tokens = normalize(input).split(' ').filter((token) => token.length > 2);
  if (!tokens.length) return questions.slice(0, limit);

  const scored = questions.map((question) => {
    const haystack = normalize(
      [
        questionText(question),
        question.main_category,
        question.subcategory,
        question.skill,
        question.question_type,
        ...(question.tags ?? []),
      ]
        .filter(Boolean)
        .join(' '),
    );
    const score = tokens.reduce((total, token) => total + (haystack.includes(token) ? 1 : 0), 0);
    return { question, score };
  });

  return scored
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((item) => item.question);
}

function topicLabel(question?: Question | null) {
  return question?.subcategory || question?.skill || question?.main_category || question?.question_type || 'הנושא הנוכחי';
}

function buildLocalTeacherReply(
  input: string,
  mode: TeacherMode,
  categories: Category[],
  questions: Question[],
  selectedQuestion?: Question | null,
): string {
  const intent = classifyIntent(input);
  const relevant = selectedQuestion ? [selectedQuestion] : findRelevantQuestions(input, questions);
  const current = relevant[0];
  const availableTopics = categories.flatMap((category) => category.lessons.map((lesson) => lesson.title)).slice(0, 8);

  if (intent === 'greeting') {
    return 'שלום! אני המורה המקומי של המערכת. אני מכיר את קטלוג הלימוד והשאלות שנטענו למערכת, ויכול ללמד נושא, לפרק שאלה, לתת רמזים, לתרגל איתך ולנתח טעויות.\n\nאפשר להתחיל ב״למד אותי נושא״ או לשלוח לי שאלה ספציפית.';
  }

  if (intent === 'practice' || mode === 'practice') {
    if (current) {
      return `מצוין. נתרגל עכשיו את ${topicLabel(current)}.\n\nאני לא אגלה את התשובה מיד. קודם נסה לזהות מה השאלה בודקת ומה הצעד הראשון שהיית עושה. אם תרצה, כתוב את האפשרות שבחרת ואבדוק אותה איתך.`;
    }
    return 'מעולה. בחר נושא או רמת קושי מהמערכת, ואני אבנה לך תרגול מדורג מתוך מאגר השאלות הקיים. המטרה היא לא רק לצבור תשובות נכונות אלא להבין את שיטת הפתרון.';
  }

  if (intent === 'mistake' || mode === 'mistake') {
    if (current) {
      const solution = cleanRichText(current.solution_text);
      return `בוא ננתח את הטעות בשאלה הזו.\n\nהשאלה שייכת ל: ${topicLabel(current)}.\n\nהצעד הראשון הוא לא לשאול רק "מה התשובה?", אלא "איזה כלל או קשר השאלה דורשת לזהות?".\n${solution ? `\nפתרון המערכת: ${solution}` : '\nלשאלה הזו אין כרגע פתרון טקסטואלי מלא במידע שהתקבל מהמערכת.'}\n\nאם תכתוב לי איזו אפשרות בחרת, אוכל להסביר מה גרם לטעות ומה כדאי לבדוק בפעם הבאה.`;
    }
    return 'כדי לנתח טעות בצורה מקצועית אני צריך את השאלה ואת האפשרות שבחרת. פתח שאלה ממאגר השאלות ושלח אותה למורה, או כתוב את נוסח השאלה כאן.';
  }

  if (intent === 'strategy') {
    if (current) {
      return `בשאלה הזו כדאי לעבוד לפי סדר קבוע:\n\n1. לזהות מה בדיוק מבקשים.\n2. לזהות את סוג השאלה: ${current.question_type || 'סוג השאלה'}.\n3. להגדיר את הקשר/הכלל המרכזי לפני שמסתכלים על המסיחים.\n4. לפסול אפשרויות שאינן עומדות בכלל.\n5. לבדוק את התשובה פעם נוספת מול נוסח השאלה.\n\nהמיומנות המרכזית כאן היא: ${topicLabel(current)}.`;
    }
    return 'שיטת העבודה של המורה היא: קודם להבין מה השאלה בודקת, אחר כך לזהות את סוג המשימה, לאחר מכן לבנות כלל או דרך פתרון, ורק בסוף להשתמש באפשרויות התשובה כדי לאמת את המסקנה. כך נמנעים מניחוש בין מסיחים.';
  }

  if (intent === 'question' && current) {
    const answers = current.answers
      .slice()
      .sort((a, b) => a.order - b.order)
      .map((answer, index) => `${index + 1}. ${answer.answer_text}`)
      .join('\n');
    const solution = cleanRichText(current.solution_text);
    return `מצאתי שאלה רלוונטית במאגר.\n\n${questionText(current)}\n\nאפשרויות:\n${answers || 'אין אפשרויות זמינות'}\n\nאני מציע לא לבחור מיד. נסה להסביר לי מה הקשר או הכלל שאתה רואה. ${solution ? `\n\nלאחר הניסיון שלך, אוכל להשוות לפתרון המערכת: ${solution}` : ''}`;
  }

  if (intent === 'difficulty') {
    return 'אפשר ללמוד בהדרגה: קל → בינוני → בחינה. אני ממליץ להתחיל ברמה שבה אתה מצליח להסביר את דרך הפתרון, לא רק לסמן תשובה נכונה, ואז לעלות רמה. אם תרצה, בחר רמת קושי באזור התרגול ואמשיך משם.';
  }

  if (intent === 'topic' || intent === 'explain') {
    const lessonMatch = availableTopics.find((topic) => normalize(topic).split(' ').some((token) => normalize(input).includes(token)));
    if (lessonMatch) {
      return `בשמחה. נתחיל מ־${lessonMatch}.\n\nהמטרה שלי היא ללמד בשלושה שלבים: להבין את הרעיון, לראות דוגמה, ואז לפתור שאלה בעצמך.\n\nבשלב הראשון אסביר את העיקרון בשפה פשוטה. בשלב השני נפרק שאלה לדוגמה. בשלב השלישי אתן לך לנסות, ואספק רמזים לפני שאגלה את הפתרון.`;
    }
    if (current) {
      return `בוא נלמד דרך השאלה שמצאתי. היא עוסקת ב־${topicLabel(current)}.\n\nאל תתחיל מהתשובות. קודם נסח במילים שלך מה מבקשים ממך. אחר כך נזהה את הכלל המתאים ונבדוק כל אפשרות מולו.\n\nאם תרצה, כתוב "תן רמז" ואעבור איתך שלב אחד בכל פעם.`;
    }
    return `בשמחה. המורה מחובר לקטלוג הלימוד המקומי ולכן הוא יכול ללמד רק מתוך התוכן שקיים במערכת, בלי API חיצוני.\n\nהנושאים הזמינים כרגע כוללים למשל: ${availableTopics.join(', ') || 'הקטלוג נטען כעת'}.\n\nכתוב את שם הנושא ואסביר אותו מהבסיס ועד תרגול.`;
  }

  if (current) {
    return `אני מזהה שאלה רלוונטית בנושא ${topicLabel(current)}.\n\nבוא נפתור אותה כמו בכיתה: קודם נבין מה מבקשים, אחר כך נבחר אסטרטגיה, ורק אז נבדוק את התשובות.\n\nאם אתה רוצה הסבר מלא, כתוב "תסביר". אם אתה רוצה ללמוד לבד, כתוב "תן רמז".`;
  }

  return 'אני איתך כמורה ולא כמנוע תשובות. כתוב נושא, שאלה, או משהו שלא הבנת, ואני אפרק אותו להסבר → דוגמה → תרגול → משוב. אפשר גם לבחור אחד מהכפתורים למעלה.';
}

export default function AITeacherPage() {
  const token = useAuthStore((state) => state.token);
  const [categories, setCategories] = useState<Category[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
  const [mode, setMode] = useState<TeacherMode>('learn');
  const [input, setInput] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      text: 'שלום! אני המורה האישי שלך. אני עובד ללא API חיצוני ומבוסס על חומרי הלימוד והשאלות שקיימים במערכת. אפשר לבקש ממני ללמד נושא, להסביר שאלה, לתת רמז, לתרגל או לנתח טעות.',
    },
  ]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        setLoading(true);
        const categoryData = await getCategories();
        if (cancelled) return;
        setCategories(categoryData);

        if (token) {
          const firstPage = await getQuestionBank(token, { page: 1, perPage: 100, search: search || undefined });
          if (!cancelled) setQuestions(firstPage.questions);
        }
      } catch (loadError) {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : 'לא ניתן לטעון את מאגר הלימוד.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [token]);

  useEffect(() => {
    if (!token) return;
    const timer = window.setTimeout(async () => {
      try {
        const data = await getQuestionBank(token, { page: 1, perPage: 100, search: search || undefined });
        setQuestions(data.questions);
      } catch {
        // Keep the already loaded local knowledge if a subsequent search fails.
      }
    }, 350);
    return () => window.clearTimeout(timer);
  }, [search, token]);

  const stats = useMemo(() => {
    const lessonCount = categories.reduce((sum, category) => sum + category.lesson_count, 0);
    return { categories: categories.length, lessons: lessonCount, questions: questions.length };
  }, [categories, questions]);

  const send = async (event: FormEvent) => {
    event.preventDefault();
    const question = input.trim();
    if (!question || sending) return;

    setSending(true);
    setMessages((current) => [...current, { role: 'user', text: question }]);
    setInput('');

    try {
      const reply = buildLocalTeacherReply(question, mode, categories, questions, selectedQuestion);
      await new Promise((resolve) => window.setTimeout(resolve, 220));
      setMessages((current) => [...current, { role: 'assistant', text: reply }]);
    } finally {
      setSending(false);
    }
  };

  const ask = (prompt: string) => {
    setInput(prompt);
    window.setTimeout(() => document.getElementById('ai-teacher-input')?.focus(), 0);
  };

  const clearChat = () => {
    setSelectedQuestion(null);
    setMessages([
      {
        role: 'assistant',
        text: 'התחלנו מחדש. בחר מצב לימוד או כתוב לי מה אתה רוצה ללמוד.',
      },
    ]);
  };

  return (
    <div dir="rtl" className="mx-auto max-w-7xl space-y-6 pb-8">
      <header className="rounded-3xl bg-gradient-to-l from-indigo-700 via-indigo-600 to-violet-600 p-6 text-white shadow-lg md:p-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="mb-3 flex items-center gap-3">
              <div className="rounded-2xl bg-white/15 p-3 backdrop-blur"><Brain className="h-7 w-7" /></div>
              <div>
                <p className="text-sm font-medium text-indigo-100">מרכז ההוראה החכם</p>
                <h1 className="text-3xl font-black md:text-4xl">המורה האישי שלך</h1>
              </div>
            </div>
            <p className="max-w-2xl text-indigo-50">
              מורה מקומי שמכיר את תוכן הלימוד ואת מאגר השאלות של המערכת. הוא מסביר, שואל שאלות נגדיות, נותן רמזים ומלמד שיטת פתרון — בלי API חיצוני.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center text-sm md:min-w-[310px]">
            <div className="rounded-2xl bg-white/10 p-3 backdrop-blur"><div className="text-2xl font-black">{stats.categories}</div><div className="text-indigo-100">תחומים</div></div>
            <div className="rounded-2xl bg-white/10 p-3 backdrop-blur"><div className="text-2xl font-black">{stats.lessons}</div><div className="text-indigo-100">שיעורים</div></div>
            <div className="rounded-2xl bg-white/10 p-3 backdrop-blur"><div className="text-2xl font-black">{stats.questions}</div><div className="text-indigo-100">שאלות נטענו</div></div>
          </div>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="space-y-4">
          <Card className="p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-bold text-slate-900">מצב הוראה</h2>
              <Sparkles className="h-4 w-4 text-indigo-600" />
            </div>
            <div className="space-y-2">
              {([
                ['learn', 'למד אותי', 'הסבר מסודר מהבסיס'],
                ['guided', 'פתרון מודרך', 'רמזים לפני תשובה'],
                ['practice', 'תרגול', 'שאלה אחת בכל פעם'],
                ['mistake', 'ניתוח טעות', 'להבין למה טעינו'],
              ] as const).map(([value, title, subtitle]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setMode(value)}
                  className={`w-full rounded-xl border p-3 text-right transition ${mode === value ? 'border-indigo-300 bg-indigo-50 text-indigo-900' : 'border-slate-200 bg-white hover:bg-slate-50'}`}
                >
                  <div className="font-semibold">{title}</div>
                  <div className="mt-0.5 text-xs text-slate-500">{subtitle}</div>
                </button>
              ))}
            </div>
          </Card>

          <Card className="p-4">
            <div className="mb-3 flex items-center gap-2 font-bold text-slate-900"><Search className="h-4 w-4 text-indigo-600" /> חיפוש במאגר השאלות</div>
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="חפש שאלה או נושא..."
              className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />
            <div className="mt-3 max-h-72 space-y-2 overflow-y-auto">
              {questions.slice(0, 12).map((question) => (
                <button
                  key={question.id}
                  type="button"
                  onClick={() => { setSelectedQuestion(question); setMode('guided'); ask('תסביר לי את השאלה שבחרתי שלב־אחר־שלב.'); }}
                  className={`w-full rounded-xl border p-3 text-right text-sm hover:border-indigo-300 hover:bg-indigo-50 ${selectedQuestion?.id === question.id ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200'}`}
                >
                  <div className="mb-1 flex items-center gap-2 text-xs text-indigo-600"><HelpCircle className="h-3.5 w-3.5" /> {topicLabel(question)}</div>
                  <div className="line-clamp-2 text-slate-700">{questionText(question)}</div>
                </button>
              ))}
              {!loading && !questions.length && <p className="py-4 text-center text-xs text-slate-500">לא נמצאו שאלות במאגר הזמין.</p>}
            </div>
          </Card>
        </aside>

        <main className="min-w-0 space-y-4">
          <Card className="overflow-hidden">
            <div className="border-b border-slate-200 bg-white p-4">
              <div className="flex flex-wrap gap-2">
                {QUICK_PROMPTS.map(({ label, icon: Icon, prompt }) => (
                  <button key={label} type="button" onClick={() => ask(prompt)} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700">
                    <Icon className="h-4 w-4" /> {label}
                  </button>
                ))}
                <button type="button" onClick={clearChat} className="mr-auto inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-slate-500 hover:bg-slate-100"><RotateCcw className="h-4 w-4" /> נקה שיחה</button>
              </div>
            </div>

            <div className="min-h-[500px] max-h-[620px] space-y-4 overflow-y-auto bg-slate-50 p-4 md:p-6">
              {messages.map((message, index) => (
                <div key={`${index}-${message.role}`} className={`flex ${message.role === 'user' ? 'justify-start' : 'justify-end'}`}>
                  <div className={`max-w-[88%] rounded-2xl px-4 py-3 shadow-sm md:max-w-[78%] ${message.role === 'user' ? 'bg-indigo-600 text-white' : 'border border-slate-200 bg-white text-slate-800'}`}>
                    <div className="mb-1 flex items-center gap-2 text-xs font-bold opacity-70">
                      {message.role === 'user' ? 'אתה' : <><Brain className="h-3.5 w-3.5" /> המורה</>}
                    </div>
                    <div className="whitespace-pre-wrap leading-7">{message.text}</div>
                  </div>
                </div>
              ))}
              {sending && <div className="flex justify-end"><div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500">המורה חושב על דרך ההסבר...</div></div>}
            </div>

            <form onSubmit={send} className="border-t border-slate-200 bg-white p-4">
              <div className="flex gap-3">
                <input
                  id="ai-teacher-input"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  placeholder="שאל את המורה כל דבר על הלמידה..."
                  className="min-w-0 flex-1 rounded-2xl border border-slate-300 px-4 py-3 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                />
                <button type="submit" disabled={sending || !input.trim()} className="rounded-2xl bg-indigo-600 px-5 text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50" aria-label="שלח">
                  <Send className="h-5 w-5" />
                </button>
              </div>
              <p className="mt-2 text-xs text-slate-500">הסברים מבוססים על תוכן הלימוד והמידע שנטען מהמערכת. אין חיבור לספק AI חיצוני.</p>
            </form>
          </Card>

          {selectedQuestion && (
            <Card className="border-indigo-100 bg-indigo-50/50 p-5">
              <div className="mb-3 flex items-center gap-2 font-bold text-indigo-900"><Trophy className="h-5 w-5" /> השאלה שנבחרה</div>
              <p className="leading-7 text-slate-800">{questionText(selectedQuestion)}</p>
              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                <span className="rounded-full bg-white px-3 py-1.5 text-slate-600">{topicLabel(selectedQuestion)}</span>
                <span className="rounded-full bg-white px-3 py-1.5 text-slate-600">{selectedQuestion.difficulty}</span>
                {selectedQuestion.skill && <span className="rounded-full bg-white px-3 py-1.5 text-slate-600">מיומנות: {selectedQuestion.skill}</span>}
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <button type="button" onClick={() => { setMode('guided'); ask('תן לי רמז בלבד לשאלה הזו, בלי לגלות את התשובה.'); }} className="inline-flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-sm font-semibold text-indigo-700 shadow-sm"><Lightbulb className="h-4 w-4" /> תן רמז</button>
                <button type="button" onClick={() => { setMode('learn'); ask('הסבר לי את הפתרון המלא לשאלה הזו ולמה כל שלב נכון.'); }} className="inline-flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-sm font-semibold text-indigo-700 shadow-sm"><CheckCircle2 className="h-4 w-4" /> הסבר פתרון</button>
              </div>
            </Card>
          )}

          {error && <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">לא הצלחתי לטעון את כל מאגר הלימוד: {error}</div>}
          {loading && <div className="flex items-center justify-center gap-2 py-2 text-sm text-slate-500"><MessageCircle className="h-4 w-4 animate-pulse" /> טוען את הידע המקומי של המורה...</div>}
        </main>
      </div>
    </div>
  );
}
