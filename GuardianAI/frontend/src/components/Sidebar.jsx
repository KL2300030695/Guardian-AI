import { NavLink } from "react-router-dom";

const NAV = [
  { to: "/dashboard", icon: "🏠", label: "Dashboard" },
  { to: "/history",   icon: "📜", label: "Event History" },
  { to: "/analytics", icon: "📊", label: "Analytics" },
  { to: "/faces",     icon: "🙂", label: "Faces" },
  { to: "/settings",  icon: "⚙️", label: "Settings" },
];

export default function Sidebar() {
  return (
    <aside className="w-60 shrink-0 flex flex-col h-screen bg-guardian-900/80 backdrop-blur-md border-r border-slate-700/40">

      {/* Logo */}
      <div className="px-5 py-5 border-b border-slate-700/40">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-lg">
            🛡️
          </div>
          <div>
            <p className="text-sm font-bold text-white leading-none">Guardian AI</p>
            <p className="text-xs text-slate-500 mt-0.5">Security System</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <p className="px-3 mb-2 text-[10px] font-semibold text-slate-600 uppercase tracking-widest">
          Navigation
        </p>
        {NAV.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `nav-link ${isActive ? "active" : ""}`
            }
          >
            <span className="text-base w-5 text-center">{icon}</span>
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-slate-700/40">
        <p className="text-[10px] text-slate-600 text-center">
          Phase 9 · FastAPI + React
        </p>
      </div>
    </aside>
  );
}
