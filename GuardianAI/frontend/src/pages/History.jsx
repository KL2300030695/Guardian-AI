import { useState, useEffect } from "react";
import { api } from "../api.js";
import EventTable from "../components/EventTable.jsx";

const ROWS_PER_PAGE = 15;

export default function History() {
  const [events,   setEvents]   = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [date,     setDate]     = useState("");
  const [page,     setPage]     = useState(1);
  const [loading,  setLoading]  = useState(true);

  // Load events
  useEffect(() => {
    const load = async () => {
      try {
        const data = date
          ? await api.eventsByDate(date)
          : await api.events();
        setEvents(data);
        setFiltered(data);
        setPage(1);
      } catch { setEvents([]); }
      finally { setLoading(false); }
    };
    setLoading(true);
    load();
  }, [date]);

  // Pagination slice
  const total = filtered.length;
  const pages = Math.max(1, Math.ceil(total / ROWS_PER_PAGE));
  const slice = filtered.slice((page - 1) * ROWS_PER_PAGE, page * ROWS_PER_PAGE);

  return (
    <div className="page-enter space-y-5">

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-4">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex-1">
          📜 Event Log — {total} record{total !== 1 ? "s" : ""}
        </h2>

        {/* Date filter */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-500">Filter date:</label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="inp w-36 text-xs py-1.5"
          />
          {date && (
            <button onClick={() => setDate("")} className="btn-ghost text-xs py-1.5 px-2">
              Clear
            </button>
          )}
        </div>

        {/* Refresh */}
        <button
          onClick={() => setDate(d => d)} /* re-trigger effect */
          className="btn-ghost text-xs py-1.5 px-3"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16">
            <div className="w-6 h-6 border-2 border-cyan-500/40 border-t-cyan-400 rounded-full animate-spin" />
          </div>
        ) : (
          <EventTable events={slice} />
        )}
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className={`btn-ghost text-xs py-1.5 px-3 ${page === 1 ? "opacity-40 cursor-not-allowed" : ""}`}
          >
            ← Prev
          </button>

          {[...Array(pages)].map((_, i) => (
            <button
              key={i}
              onClick={() => setPage(i + 1)}
              className={`text-xs w-8 h-8 rounded-lg font-mono transition-all
                ${page === i + 1
                  ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/40"
                  : "text-slate-500 hover:text-slate-300 hover:bg-slate-700/30"}`}
            >
              {i + 1}
            </button>
          ))}

          <button
            onClick={() => setPage(p => Math.min(pages, p + 1))}
            disabled={page === pages}
            className={`btn-ghost text-xs py-1.5 px-3 ${page === pages ? "opacity-40 cursor-not-allowed" : ""}`}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
