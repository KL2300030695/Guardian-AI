import { useState, useEffect } from "react";
import { api } from "../api.js";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  AreaChart, Area, CartesianGrid, Cell,
} from "recharts";

export default function Analytics() {
  const [daily,  setDaily]  = useState([]);
  const [hourly, setHourly] = useState([]);
  const [stats,  setStats]  = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [d, h, s] = await Promise.all([
          api.analyticsDaily(),
          api.analyticsHourly(),
          api.eventsStats(),
        ]);
        setDaily([...d].reverse());     // oldest first for chart
        setHourly(h);
        setStats(s);
      } catch {}
      finally { setLoading(false); }
    };
    load();
  }, []);

  if (loading) return <Spinner />;

  // Most active hour
  const peakHour = hourly.reduce(
    (best, h) => (h.count > (best?.count ?? 0) ? h : best),
    null
  );

  // Avg duration in minutes
  const avgDur = stats.total_events > 0
    ? Math.round(stats.total_duration / stats.total_events / 60 * 10) / 10
    : 0;

  // Max count for heatmap scaling
  const maxH = Math.max(...hourly.map(h => h.count), 1);

  const TOOLTIP_STYLE = {
    contentStyle: { background: "#0d1421", border: "1px solid rgba(99,102,241,0.3)", borderRadius: 8, fontSize: 12 },
    itemStyle: { color: "#94a3b8" },
    labelStyle: { color: "#e2e8f0", fontWeight: 600 },
  };

  return (
    <div className="page-enter space-y-6">

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <InfoCard label="Total Events"  value={stats.total_events ?? 0}  icon="🎯" />
        <InfoCard label="Total Persons" value={stats.total_persons ?? 0}  icon="👤" />
        <InfoCard label="Avg Duration"  value={`${avgDur} min`}           icon="⏱" />
        <InfoCard label="Peak Hour"     value={peakHour ? `${peakHour.hour}:00` : "—"} icon="🕐" />
      </div>

      {/* Daily bar chart */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">📅 Events Per Day</h3>
        {daily.length === 0 ? (
          <Empty />
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={daily} margin={{ top: 4, right: 8, left: -24, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} />
              <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip {...TOOLTIP_STYLE} />
              <Bar dataKey="count" name="Events" radius={[4, 4, 0, 0]} fill="#0ea5e9" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Hourly heatmap */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">🕐 Hourly Detection Heatmap</h3>
        {hourly.every(h => h.count === 0) ? (
          <Empty />
        ) : (
          <>
            <div className="grid grid-cols-12 gap-1 mb-2">
              {hourly.map(({ hour, count }) => {
                const intensity = count / maxH;
                return (
                  <div
                    key={hour}
                    title={`${hour}:00 — ${count} event${count !== 1 ? "s" : ""}`}
                    className="aspect-square rounded cursor-default transition-all hover:scale-110"
                    style={{
                      background: count === 0
                        ? "rgba(99,102,241,0.05)"
                        : `rgba(14,165,233,${0.15 + intensity * 0.75})`,
                      border: count === 0 ? "1px solid rgba(99,102,241,0.1)" : "1px solid rgba(14,165,233,0.3)",
                    }}
                  />
                );
              })}
            </div>
            <div className="flex items-center justify-between text-xs text-slate-600 font-mono">
              <span>00:00</span>
              <span>06:00</span>
              <span>12:00</span>
              <span>18:00</span>
              <span>23:00</span>
            </div>
            <div className="flex items-center gap-2 mt-3 text-xs text-slate-600">
              <span>Low</span>
              <div className="flex gap-0.5">
                {[0.1, 0.25, 0.45, 0.65, 0.85].map((a, i) => (
                  <div key={i} className="w-4 h-3 rounded-sm" style={{ background: `rgba(14,165,233,${a})` }} />
                ))}
              </div>
              <span>High</span>
            </div>
          </>
        )}
      </div>

      {/* Area chart for hourly trend */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">📈 Hourly Trend</h3>
        <ResponsiveContainer width="100%" height={180}>
          <AreaChart data={hourly} margin={{ top: 4, right: 8, left: -24, bottom: 4 }}>
            <defs>
              <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#0ea5e9" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="hour" tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false}
                   tickFormatter={(v) => `${v}h`} />
            <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
            <Tooltip {...TOOLTIP_STYLE} labelFormatter={(v) => `${v}:00`} />
            <Area type="monotone" dataKey="count" name="Events" stroke="#0ea5e9"
                  strokeWidth={2} fill="url(#grad)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

    </div>
  );
}

function InfoCard({ icon, label, value }) {
  return (
    <div className="card p-4">
      <p className="text-xl mb-1">{icon}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-xs text-slate-500 mt-0.5 uppercase tracking-wide">{label}</p>
    </div>
  );
}

function Spinner() {
  return (
    <div className="flex justify-center items-center h-64">
      <div className="w-6 h-6 border-2 border-cyan-500/40 border-t-cyan-400 rounded-full animate-spin" />
    </div>
  );
}

function Empty() {
  return (
    <div className="flex flex-col items-center py-10 text-slate-600 text-sm gap-2">
      <span className="text-3xl">📊</span>
      <p>No data yet — start monitoring to see analytics</p>
    </div>
  );
}
