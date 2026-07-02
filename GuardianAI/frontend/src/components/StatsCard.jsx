/**
 * StatsCard — a glassmorphism metric card.
 *
 * Props:
 *   icon    string  — emoji or svg
 *   label   string  — metric name
 *   value   any     — metric value
 *   accent  string  — tailwind color name: "cyan" | "emerald" | "amber" | "violet" | "rose"
 *   sub     string  — optional sub-label below value
 */

const ACCENT = {
  cyan:    { border: "border-cyan-500/30",    bg: "bg-cyan-500/10",    text: "text-cyan-400"    },
  emerald: { border: "border-emerald-500/30", bg: "bg-emerald-500/10", text: "text-emerald-400" },
  amber:   { border: "border-amber-500/30",   bg: "bg-amber-500/10",   text: "text-amber-400"   },
  violet:  { border: "border-violet-500/30",  bg: "bg-violet-500/10",  text: "text-violet-400"  },
  rose:    { border: "border-rose-500/30",    bg: "bg-rose-500/10",    text: "text-rose-400"    },
};

export default function StatsCard({ icon, label, value, accent = "cyan", sub }) {
  const c = ACCENT[accent] ?? ACCENT.cyan;

  return (
    <div className={`card p-5 flex items-start gap-4 border-l-2 ${c.border} hover:border-opacity-60 transition-all duration-300`}>

      {/* Icon bubble */}
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center text-xl shrink-0 ${c.bg} ${c.border} border`}>
        {icon}
      </div>

      {/* Text */}
      <div className="min-w-0">
        <p className="stat-value">{value ?? "—"}</p>
        <p className="stat-label">{label}</p>
        {sub && <p className="text-xs text-slate-600 mt-1">{sub}</p>}
      </div>
    </div>
  );
}
