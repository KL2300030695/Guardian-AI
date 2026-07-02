import { useState } from "react";
import { api } from "../api.js";

/**
 * EventTable — displays detection events.
 * Props:
 *   events  array  — list of event objects from the API
 *   compact bool   — if true, hide some columns (for Dashboard preview)
 */
export default function EventTable({ events = [], compact = false }) {
  const [modal, setModal] = useState(null);   // screenshot URL to show in modal

  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-slate-600">
        <span className="text-4xl mb-3">📭</span>
        <p className="text-sm">No events recorded yet</p>
      </div>
    );
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="tbl-head">ID</th>
              <th className="tbl-head">Time</th>
              <th className="tbl-head">Persons</th>
              <th className="tbl-head">Identity</th>
              {!compact && <th className="tbl-head">Confidence</th>}
              <th className="tbl-head">Screenshot</th>
              <th className="tbl-head">Recording</th>
              <th className="tbl-head">Telegram</th>
              {!compact && <th className="tbl-head">Duration</th>}
            </tr>
          </thead>
          <tbody>
            {events.map((ev) => (
              <tr key={ev.id} className="tbl-row">

                {/* ID */}
                <td className="tbl-cell">
                  <span className="font-mono text-slate-500 text-xs">#{ev.id}</span>
                </td>

                {/* Time */}
                <td className="tbl-cell">
                  <p className="text-xs text-slate-400">{ev.date}</p>
                  <p className="font-mono text-xs text-slate-300">{ev.time}</p>
                </td>

                {/* Persons */}
                <td className="tbl-cell">
                  <span className={`badge-${ev.persons > 1 ? "yellow" : "blue"}`}>
                    👤 {ev.persons}
                  </span>
                </td>

                {/* Identity */}
                <td className="tbl-cell">
                  {ev.is_known
                    ? <span className="badge-green">🙂 {ev.identity ?? "Known"}</span>
                    : <span className="badge-red">⚠ {ev.identity ?? "Unknown"}</span>
                  }
                </td>

                {/* Confidence */}
                {!compact && (
                  <td className="tbl-cell">
                    <ConfBar value={ev.confidence} />
                  </td>
                )}

                {/* Screenshot */}
                <td className="tbl-cell">
                  {ev.screenshot ? (
                    <button
                      onClick={() => setModal(api.screenshotUrl(ev.screenshot))}
                      className="badge-blue cursor-pointer hover:bg-sky-500/25 transition-colors"
                    >
                      🖼 View
                    </button>
                  ) : (
                    <span className="text-slate-600 text-xs">—</span>
                  )}
                </td>

                {/* Recording */}
                <td className="tbl-cell">
                  {ev.recording ? (
                    <a
                      href={api.recordingUrl(ev.recording)}
                      download
                      className="badge-green hover:bg-emerald-500/25 transition-colors"
                    >
                      📥 Download
                    </a>
                  ) : (
                    <span className="text-slate-600 text-xs">—</span>
                  )}
                </td>

                {/* Telegram */}
                <td className="tbl-cell">
                  {ev.telegram ? (
                    <span className="badge-green">✅ Sent</span>
                  ) : (
                    <span className="badge-red">✗ Failed</span>
                  )}
                </td>

                {/* Duration */}
                {!compact && (
                  <td className="tbl-cell font-mono text-xs text-slate-400">
                    {ev.duration > 0 ? `${ev.duration}s` : "—"}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Screenshot modal */}
      {modal && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setModal(null)}
        >
          <div
            className="card max-w-3xl w-full overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/40">
              <span className="text-sm font-semibold text-slate-300">Screenshot</span>
              <button onClick={() => setModal(null)} className="text-slate-500 hover:text-slate-300 text-xl leading-none">×</button>
            </div>
            <img src={modal} alt="Detection screenshot" className="w-full object-contain max-h-[70vh]" />
            <div className="p-3 flex justify-end">
              <a href={modal} download className="btn-primary text-xs py-1.5 px-3">📥 Download</a>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function ConfBar({ value }) {
  const pct = Math.round((value ?? 0) * 100);
  const color = pct >= 80 ? "bg-emerald-500" : pct >= 60 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 rounded-full bg-slate-700">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 font-mono">{pct}%</span>
    </div>
  );
}
