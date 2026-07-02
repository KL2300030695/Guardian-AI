import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { api } from "../api.js";

const PAGE_TITLES = {
  "/dashboard": "Dashboard",
  "/history":   "Event History",
  "/analytics": "Analytics",
  "/faces":     "Face Recognition",
  "/settings":  "Settings",
};

export default function Navbar() {
  const [time, setTime]   = useState(new Date());
  const [online, setOnline] = useState(false);
  const location = useLocation();

  // Clock tick
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // Health check every 5 s
  useEffect(() => {
    const check = async () => {
      try {
        await api.health();
        setOnline(true);
      } catch {
        setOnline(false);
      }
    };
    check();
    const t = setInterval(check, 5000);
    return () => clearInterval(t);
  }, []);

  const title = PAGE_TITLES[location.pathname] ?? "Guardian AI";

  return (
    <header className="h-14 shrink-0 flex items-center justify-between px-6 bg-guardian-900/60 backdrop-blur-md border-b border-slate-700/40">

      {/* Page title */}
      <h1 className="text-sm font-semibold text-slate-300 tracking-wide">
        {title}
      </h1>

      {/* Right cluster */}
      <div className="flex items-center gap-5">

        {/* Clock */}
        <span className="font-mono text-xs text-slate-500">
          {time.toLocaleTimeString()}
        </span>

        {/* System status */}
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium
          ${online
            ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
            : "border-red-500/30 bg-red-500/10 text-red-400"
          }`}
        >
          <span className={`pulse-dot ${online ? "bg-emerald-400 text-emerald-400" : "bg-red-400 text-red-400"}`} />
          {online ? "System Online" : "Offline"}
        </div>
      </div>
    </header>
  );
}
