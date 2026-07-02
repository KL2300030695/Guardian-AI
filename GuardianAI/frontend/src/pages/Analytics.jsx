import { useState, useEffect, useCallback } from "react";
import { api } from "../api.js";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  AreaChart, Area, CartesianGrid, PieChart, Pie, Cell, Legend
} from "recharts";

const PIE_COLORS = ["#10b981", "#ef4444", "#3b82f6", "#f59e0b", "#8b5cf6", "#ec4899"];

export default function Analytics() {
  const [cameras,    setCameras]    = useState([]);
  const [selectedCam, setSelectedCam] = useState(""); // "" = all
  const [days,        setDays]        = useState(30);  // 7, 30, 0 (all)

  const [overview,   setOverview]   = useState(null);
  const [trends,     setTrends]     = useState([]);
  const [hourly,     setHourly]     = useState([]);
  const [camComp,    setCamComp]    = useState([]);
  const [identities, setIdentities] = useState([]);
  const [loading,    setLoading]    = useState(true);

  // Load camera options
  useEffect(() => {
    api.cameras().then(setCameras).catch(() => {});
  }, []);

  // Fetch analytics data based on filters
  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const camId = selectedCam ? parseInt(selectedCam, 10) : null;
      const daysVal = days > 0 ? days : null;

      const [ov, tr, hr, cc, idents] = await Promise.all([
        api.analyticsOverview(camId, daysVal),
        api.analyticsTrends(camId, days > 0 ? days : 999),
        api.analyticsHourlyBreakdown(camId),
        api.analyticsCamerasComparison(),
        api.analyticsIdentities(),
      ]);

      setOverview(ov);
      setTrends([...tr].reverse()); // oldest to newest for chart
      setHourly(hr);
      setCamComp(cc);
      setIdentities(idents);
    } catch (err) {
      console.error("Failed to load analytics:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedCam, days]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const TOOLTIP_STYLE = {
    contentStyle: { background: "#080e1a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, fontSize: 12 },
    itemStyle: { color: "#cbd5e1" },
    labelStyle: { color: "#00d4ff", fontWeight: 600 },
  };

  const pieData = overview ? [
    { name: "Known Visitors", value: overview.known_count ?? 0 },
    { name: "Unknown Visitors", value: overview.unknown_count ?? 0 },
  ] : [];

  const maxH = Math.max(...(hourly.map(h => h.total) || [1]), 1);

  return (
    <div className="page-enter space-y-6">

      {/* ── Header Filter Bar ────────────────────────────── */}
      <div className="card p-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <span>📊</span> AI Security Intelligence & Analytics
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time pattern analysis, visitor frequency, and camera comparison
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Camera Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Camera:</span>
            <select
              value={selectedCam}
              onChange={(e) => setSelectedCam(e.target.value)}
              className="inp text-xs py-1.5 px-3 w-44"
            >
              <option value="">All Cameras</option>
              {cameras.map((c) => (
                <option key={c.id || c.camera_id} value={c.id || c.camera_id}>
                  {c.name} {c.location ? `(${c.location})` : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Time Range Filter */}
          <div className="flex bg-guardian-900 border border-slate-700/50 rounded-lg p-0.5">
            {[
              { label: "7 Days", val: 7 },
              { label: "30 Days", val: 30 },
              { label: "All Time", val: 0 },
            ].map(({ label, val }) => (
              <button
                key={val}
                onClick={() => setDays(val)}
                className={`text-xs px-3 py-1 rounded-md font-medium transition-all ${
                  days === val
                    ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Refresh */}
          <button
            onClick={loadAnalytics}
            disabled={loading}
            className="btn-ghost text-xs py-1.5 px-3 flex items-center gap-1.5"
          >
            <span className={loading ? "animate-spin" : ""}>🔄</span> Refresh
          </button>
        </div>
      </div>

      {loading && !overview ? (
        <div className="flex flex-col items-center justify-center h-64 text-slate-500">
          <div className="w-8 h-8 border-2 border-cyan-500/40 border-t-cyan-400 rounded-full animate-spin mb-3" />
          <p className="text-sm font-medium">Computing AI Analytics…</p>
        </div>
      ) : (
        <>
          {/* ── Key Insight Cards Grid ──────────────────────── */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">

            {/* Known vs Unknown Ratio */}
            <div className="card p-4 border-l-2 border-emerald-500/40">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
                <span>Known Ratio</span>
                <span>🙂</span>
              </div>
              <p className="text-2xl font-bold text-white mt-1">
                {overview?.known_ratio ?? 0}%
              </p>
              <div className="w-full bg-slate-700/50 h-1.5 rounded-full mt-2 overflow-hidden flex">
                <div className="bg-emerald-500 h-full" style={{ width: `${overview?.known_ratio ?? 0}%` }} />
                <div className="bg-red-500 h-full" style={{ width: `${100 - (overview?.known_ratio ?? 0)}%` }} />
              </div>
              <p className="text-[11px] text-slate-500 mt-1.5">
                {overview?.known_count ?? 0} Known · {overview?.unknown_count ?? 0} Unknown
              </p>
            </div>

            {/* Avg Duration */}
            <div className="card p-4 border-l-2 border-cyan-500/40">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
                <span>Avg Duration</span>
                <span>⏱️</span>
              </div>
              <p className="text-2xl font-bold text-white mt-1">
                {overview?.avg_duration ?? 0}s
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Total: {Math.round((overview?.total_duration ?? 0) / 60)} mins recorded
              </p>
            </div>

            {/* Detection Accuracy */}
            <div className="card p-4 border-l-2 border-violet-500/40">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
                <span>Avg Accuracy</span>
                <span>🎯</span>
              </div>
              <p className="text-2xl font-bold text-white mt-1">
                {overview?.avg_confidence_pct ?? 0}%
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Across {overview?.total_events ?? 0} detections
              </p>
            </div>

            {/* Peak Hour */}
            <div className="card p-4 border-l-2 border-amber-500/40">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
                <span>Peak Hour</span>
                <span>🕐</span>
              </div>
              <p className="text-2xl font-bold text-white mt-1">
                {overview?.peak_hour !== undefined ? `${String(overview.peak_hour).padStart(2, '0')}:00` : "—"}
              </p>
              <p className="text-xs text-slate-500 mt-2">
                {overview?.peak_hour_count ?? 0} events recorded
              </p>
            </div>

            {/* Most Active Camera */}
            <div className="card p-4 border-l-2 border-sky-500/40 col-span-2 lg:col-span-1">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
                <span>Top Camera</span>
                <span>📹</span>
              </div>
              <p className="text-lg font-bold text-white mt-1 truncate">
                {overview?.most_active_camera?.name || "None"}
              </p>
              <p className="text-xs text-slate-500 mt-2">
                {overview?.most_active_camera?.count ?? 0} events
              </p>
            </div>

          </div>

          {/* ── Main Charts Grid ────────────────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Daily Trends (Stacked Bar: Known vs Unknown) */}
            <div className="card p-5 lg:col-span-2 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <span>📈</span> Visitor Activity Trends (Known vs. Unknown)
                </h3>
                <span className="text-xs text-slate-500">
                  {days > 0 ? `Last ${days} days` : "All records"}
                </span>
              </div>

              {trends.length === 0 ? (
                <EmptyChart />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} />
                    <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                    <Tooltip {...TOOLTIP_STYLE} />
                    <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                    <Bar dataKey="known" name="Known Visitors" stackId="a" fill="#10b981" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="unknown" name="Unknown Visitors" stackId="a" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Known vs Unknown Pie Distribution */}
            <div className="card p-5 space-y-4 flex flex-col justify-between">
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <span>🥧</span> Visitor Identity Split
              </h3>

              {overview?.total_events === 0 ? (
                <EmptyChart />
              ) : (
                <div className="flex flex-col items-center">
                  <ResponsiveContainer width="100%" height={180}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={75}
                        paddingAngle={4}
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip {...TOOLTIP_STYLE} />
                    </PieChart>
                  </ResponsiveContainer>

                  {/* Top Recognized Identities List */}
                  <div className="w-full space-y-1.5 mt-2 border-t border-slate-700/40 pt-3">
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Top Detected Individuals
                    </p>
                    {identities.slice(0, 4).map((id, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs">
                        <span className="flex items-center gap-1.5 text-slate-300">
                          <span>{id.is_known ? "🙂" : "⚠"}</span>
                          <span className="font-medium">{id.identity}</span>
                        </span>
                        <span className="font-mono text-slate-400">
                          {id.count} event{id.count > 1 ? "s" : ""} ({id.avg_confidence}%)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

          </div>

          {/* ── Second Charts Row: Camera Comparison & Hourly Distribution ── */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* Camera Activity Comparison */}
            <div className="card p-5 space-y-4">
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <span>📹</span> Camera Activity Comparison
              </h3>
              {camComp.length === 0 ? (
                <EmptyChart />
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={camComp} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} tickLine={false} />
                    <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                    <Tooltip {...TOOLTIP_STYLE} />
                    <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                    <Bar dataKey="known_events" name="Known" fill="#10b981" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="unknown_events" name="Unknown" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Hourly 24-hr Heatmap & Frequency */}
            <div className="card p-5 space-y-4">
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <span>🕐</span> 24-Hour Visitor Frequency
              </h3>
              {hourly.every(h => h.total === 0) ? (
                <EmptyChart />
              ) : (
                <>
                  <ResponsiveContainer width="100%" height={170}>
                    <AreaChart data={hourly} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="hourlyGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="hour_label" tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} />
                      <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                      <Tooltip {...TOOLTIP_STYLE} />
                      <Area type="monotone" dataKey="total" name="Total Events" stroke="#00d4ff" strokeWidth={2} fill="url(#hourlyGrad)" />
                    </AreaChart>
                  </ResponsiveContainer>

                  {/* Heatmap Bar Grid */}
                  <div className="space-y-1">
                    <div className="grid grid-cols-12 gap-1">
                      {hourly.map(({ hour, total }) => {
                        const intensity = total / maxH;
                        return (
                          <div
                            key={hour}
                            title={`${hour}:00 — ${total} event${total !== 1 ? "s" : ""}`}
                            className="h-4 rounded cursor-pointer transition-all hover:scale-110"
                            style={{
                              background: total === 0
                                ? "rgba(255,255,255,0.04)"
                                : `rgba(0,212,255,${0.2 + intensity * 0.8})`,
                              border: total === 0 ? "1px solid rgba(255,255,255,0.05)" : "1px solid rgba(0,212,255,0.4)",
                            }}
                          />
                        );
                      })}
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                      <span>00:00</span>
                      <span>06:00</span>
                      <span>12:00</span>
                      <span>18:00</span>
                      <span>23:00</span>
                    </div>
                  </div>
                </>
              )}
            </div>

          </div>
        </>
      )}

    </div>
  );
}

function EmptyChart() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-slate-500 gap-2">
      <span className="text-3xl">📭</span>
      <p className="text-xs">No activity records match the selected filter criteria.</p>
    </div>
  );
}
