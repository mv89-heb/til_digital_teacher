import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[85vh] px-4 text-center">
      
      {/* תגית חדשנות קטנה למעלה */}
      <div className="bg-blue-50 text-blue-600 px-4 py-1.5 rounded-full text-sm font-semibold mb-8 border border-blue-100">
        🚀 גרסת בטא - המערכת בפיתוח
      </div>

      {/* כותרת ראשית */}
      <h1 className="text-5xl md:text-6xl font-extrabold text-slate-900 mb-6 tracking-tight">
        המורה הפרטי הדיגיטלי שלך <br />
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
          למבחני תיל
        </span>
      </h1>
      
      {/* תת כותרת */}
      <p className="text-xl text-slate-600 mb-10 max-w-2xl leading-relaxed">
        לא סתם עוד מאגר שאלות. פלטפורמה חכמה שתלמד אותך מאפס, תסביר לך בדיוק למה טעית, ותעניק לך את שיטות החשיבה המהירות ביותר להצלחה.
      </p>
      
      {/* כפתורי פעולה */}
      <div className="flex flex-col sm:flex-row gap-4">
        <Link 
          href="/login" 
          className="bg-blue-600 text-white px-8 py-3.5 rounded-xl font-bold text-lg hover:bg-blue-700 hover:-translate-y-0.5 transition-all shadow-lg hover:shadow-blue-500/30"
        >
          התחל ללמוד עכשיו
        </Link>
        <Link 
          href="#features" 
          className="bg-white text-slate-700 border border-slate-200 px-8 py-3.5 rounded-xl font-bold text-lg hover:bg-slate-50 transition-all shadow-sm"
        >
          איך זה עובד?
        </Link>
      </div>
      
      {/* סטטיסטיקות דמו למטה */}
      <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8 border-t border-slate-200 pt-10 w-full max-w-4xl text-slate-600">
        <div>
          <div className="text-3xl font-bold text-slate-900">4</div>
          <div className="text-sm mt-1">קטגוריות לימוד</div>
        </div>
        <div>
          <div className="text-3xl font-bold text-slate-900">100%</div>
          <div className="text-sm mt-1">הסברים מפורטים</div>
        </div>
        <div>
          <div className="text-3xl font-bold text-slate-900">⚡</div>
          <div className="text-sm mt-1">שיטות מהירות</div>
        </div>
        <div>
          <div className="text-3xl font-bold text-slate-900">24/7</div>
          <div className="text-sm mt-1">תרגול מכל מקום</div>
        </div>
      </div>
      
    </div>
  );
}
