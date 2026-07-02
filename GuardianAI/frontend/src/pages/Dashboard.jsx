import { useState, useEffect, useCallback } from "react";
import { api } from "../api.js";
import LiveCamera from "../components/LiveCamera.jsx";
import StatsCard  from "../components/StatsCard.jsx";
import EventTable from "../components/EventTable.jsx";

export default function Dashboard() {
  const [status,  setStatus]  = useState({ running: false, recording: false, person_count: 0, fps: 0, total_events: 0 });
  const [stats,   setStats]   = useState({});
  const [recent,  setRecent]  = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    try { setStatus(await api.cameraStatus()); } catch {}
  }, []);

  const fetchStats  = useCallback(async () => {
    try { setStats(await api.eventsStats()); } catch {}
  }, []);

  const fetchRecent = useCallback(async () => {
    try { setRecent(await api.eventsRecent()); } catch {}
  }, []);

  useEffect(() => {
    Promise.all([fetchStatus(), fetchStats(), fetchRecent()]).finally(() => setLoading(false));

    const t1 = setInterval(fetchStatus,  1000);
    const t2 = setInterval(fetchStats,  10000);
    const t3 = setInterval(fetchRecent,  5000);
    return () => { clearInterval(t1); clearInterval(t2); clearInterval(t3); };
  }, [fetchStatus, fetchStats, fetchRecent]);

  const handleStart = async () => {
    await api.cameraStart();
    fetchStatus();
  };
  const handleStop = async () => {
    await api.cameraStop();
    fetchStatus();
  };

  const fmt = (v) => (v !== undefined && v !== null ? v : "—");
  const fmtMin = (s) => s > 0 ? `${Math.round(s / 60)} min` : "0 min";

  if (loading) return <LoadingScreen />;

  return (
    <div className="page-enter space-y-6">

      {/* Live Camera */}
      <section>
        <SectionTitle icon="📹" title="Live Camera" />
        <LiveCamera status={status} onStart={handleStart} onStop={handleStop} />
      </section>

      {/* Stats row */}
      <section>
        <SectionTitle icon="📊" title="Statistics" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard icon="🎯" label="Today's Events"   value={fmt(stats.total_events)}    accent="cyan" />
          <StatsCard icon="👤" label="Total Persons"    value={fmt(stats.total_persons)}   accent="amber" />
          <StatsCard icon="📱" label="Telegram Alerts"  value={fmt(stats.telegram_sent)}   accent="emerald" />
          <StatsCard icon="⏱"  label="Recording Time"  value={fmtMin(stats.total_duration ?? 0)} accent="violet" />
        </div>
      </section>

      {/* Recent events */}
      <section>
        <SectionTitle icon="🕒" title="Recent Events" />
        <div className="card overflow-hidden">
          <EventTable events={recent.slice(0, 5)} compact />
        </div>
      </section>
    </div>
  );
}

function SectionTitle({ icon, title }) {
  return (
    <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
      <span>{icon}</span> {title}
    </h2>
  );
}

function LoadingScreen() {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4 text-slate-600">
      <div className="w-8 h-8 border-2 border-cyan-500/50 border-t-cyan-400 rounded-full animate-spin" />
      <p className="text-sm">Connecting to Guardian AI…</p>
    </div>
  );
}
