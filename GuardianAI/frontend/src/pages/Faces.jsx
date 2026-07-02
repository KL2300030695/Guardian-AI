import { useState, useEffect, useRef, useCallback } from "react";
import { api } from "../api.js";

const REGISTER_POLL_MS = 800;

export default function Faces() {
  const [faces,       setFaces]      = useState([]);
  const [regName,     setRegName]    = useState("");
  const [regStatus,   setRegStatus]  = useState(null);
  const [loading,     setLoading]    = useState(true);
  const [msg,         setMsg]        = useState("");
  const [confirmDel,  setConfirmDel] = useState(null);
  const [history,     setHistory]    = useState({ name: null, events: [] });
  const pollRef = useRef(null);

  // ── Load known faces ──────────────────────────────
  const loadFaces = useCallback(async () => {
    try { setFaces(await apiFaces()); }
    catch { setMsg("Could not load faces from server."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    loadFaces();
    return () => clearInterval(pollRef.current);
  }, [loadFaces]);

  // ── Registration polling ───────────────────────────
  const startPolling = () => {
    clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const st = await apiRegStatus();
        setRegStatus(st);
        if (!st.active) {
          clearInterval(pollRef.current);
          if (st.completed) {
            setMsg(`✅ ${st.name} registered successfully!`);
            loadFaces();
          }
        }
      } catch { clearInterval(pollRef.current); }
    }, REGISTER_POLL_MS);
  };

  // ── Start registration ────────────────────────────
  const handleRegister = async () => {
    if (!regName.trim()) { setMsg("Enter a name first."); return; }
    try {
      const res = await apiRegStart(regName.trim());
      if (!res.ok) { setMsg(`Error: ${res.message}`); return; }
      setMsg("");
      setRegStatus({ active: true, name: regName.trim(), progress: 0, total: 20, completed: false });
      startPolling();
    } catch { setMsg("Failed to start registration. Is the camera running?"); }
  };

  // ── Cancel registration ───────────────────────────
  const handleCancel = async () => {
    clearInterval(pollRef.current);
    try { await apiRegCancel(); } catch {}
    setRegStatus(null);
  };

  // ── Delete face ───────────────────────────────────
  const handleDelete = async (id) => {
    try {
      await apiDeleteFace(id);
      setFaces(f => f.filter(x => x.id !== id));
      setConfirmDel(null);
      setMsg("Face deleted.");
    } catch { setMsg("Delete failed."); }
  };

  // ── View history ──────────────────────────────────
  const handleHistory = async (name) => {
    try {
      const evts = await apiFaceHistory(name);
      setHistory({ name, events: evts });
    } catch {}
  };

  const pct = regStatus
    ? Math.round((regStatus.progress / regStatus.total) * 100)
    : 0;

  return (
    <div className="page-enter space-y-6">

      {/* Message toast */}
      {msg && (
        <div className={`text-sm px-4 py-2 rounded-lg border ${
          msg.startsWith("✅")
            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
            : "bg-amber-500/10 border-amber-500/30 text-amber-400"
        }`}>
          {msg}
          <button onClick={() => setMsg("")} className="ml-3 opacity-60 hover:opacity-100">×</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* ── Registration panel ──────────────────── */}
        <div className="card p-5 space-y-4 lg:col-span-1">
          <h3 className="text-sm font-semibold text-slate-300 border-b border-slate-700/40 pb-2">
            👤 Register New Face
          </h3>

          <div className="space-y-3">
            <label className="text-xs text-slate-500">Full name</label>
            <input
              value={regName}
              onChange={e => setRegName(e.target.value)}
              placeholder="e.g. Subhash"
              className="inp"
              disabled={regStatus?.active}
            />
          </div>

          {/* Progress bar */}
          {regStatus?.active && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">
                  Capturing for <strong className="text-cyan-400">{regStatus.name}</strong>
                </span>
                <span className="font-mono text-slate-500">
                  {regStatus.progress}/{regStatus.total}
                </span>
              </div>
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-cyan-500 rounded-full transition-all duration-300"
                  style={{ width: `${pct}%` }}
                />
              </div>
              <p className="text-xs text-slate-600">
                🟢 Stand still, face the camera…
              </p>
            </div>
          )}

          <div className="flex gap-2">
            {!regStatus?.active ? (
              <button onClick={handleRegister} className="btn-primary flex-1 text-sm">
                📸 Start Capture ({20} frames)
              </button>
            ) : (
              <button onClick={handleCancel} className="btn-danger flex-1 text-sm">
                ✕ Cancel
              </button>
            )}
          </div>

          <div className="text-xs text-slate-600 bg-guardian-900/60 rounded-lg p-3 border border-slate-700/30">
            <p>1. Type the person's name above.</p>
            <p className="mt-1">2. Make sure the camera is <strong className="text-slate-500">running</strong>.</p>
            <p className="mt-1">3. Have the person face the camera and press Start.</p>
            <p className="mt-1">4. System captures {20} frames automatically.</p>
          </div>
        </div>

        {/* ── Known people grid ───────────────────── */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
            🧑‍🤝‍🧑 Known People — {faces.length} registered
          </h3>

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="w-6 h-6 border-2 border-cyan-500/40 border-t-cyan-400 rounded-full animate-spin" />
            </div>
          ) : faces.length === 0 ? (
            <div className="card p-10 text-center text-slate-600">
              <p className="text-4xl mb-2">👤</p>
              <p className="text-sm">No known faces registered yet.</p>
              <p className="text-xs mt-1">Use the panel on the left to add someone.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {faces.map(face => (
                <FaceCard
                  key={face.id}
                  face={face}
                  onDelete={() => setConfirmDel(face)}
                  onHistory={() => handleHistory(face.name)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── History drawer ───────────────────────── */}
      {history.name && (
        <div className="card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-300">
              📜 Event History — <span className="text-cyan-400">{history.name}</span>
            </h3>
            <button onClick={() => setHistory({ name: null, events: [] })}
                    className="text-slate-500 hover:text-slate-300 text-xl">×</button>
          </div>
          {history.events.length === 0 ? (
            <p className="text-sm text-slate-600">No events recorded for this person yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50 text-xs text-slate-500 uppercase tracking-wider">
                    <th className="px-3 py-2 text-left">ID</th>
                    <th className="px-3 py-2 text-left">Date</th>
                    <th className="px-3 py-2 text-left">Time</th>
                    <th className="px-3 py-2 text-left">Persons</th>
                    <th className="px-3 py-2 text-left">Confidence</th>
                    <th className="px-3 py-2 text-left">Telegram</th>
                  </tr>
                </thead>
                <tbody>
                  {history.events.map(ev => (
                    <tr key={ev.id} className="border-b border-slate-700/20 hover:bg-slate-700/10">
                      <td className="px-3 py-2 font-mono text-xs text-slate-500">#{ev.id}</td>
                      <td className="px-3 py-2 text-xs text-slate-400">{ev.date}</td>
                      <td className="px-3 py-2 font-mono text-xs">{ev.time}</td>
                      <td className="px-3 py-2">👤 {ev.persons}</td>
                      <td className="px-3 py-2 font-mono text-xs text-slate-400">
                        {Math.round(ev.confidence * 100)}%
                      </td>
                      <td className="px-3 py-2">
                        {ev.telegram
                          ? <span className="badge-green text-xs">✅ Sent</span>
                          : <span className="badge-yellow text-xs">— Not sent</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── Delete confirm modal ─────────────────── */}
      {confirmDel && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
             onClick={() => setConfirmDel(null)}>
          <div className="card max-w-sm w-full p-6 space-y-4" onClick={e => e.stopPropagation()}>
            <h4 className="text-base font-semibold text-slate-200">Delete Face?</h4>
            <p className="text-sm text-slate-400">
              Remove <strong className="text-white">{confirmDel.name}</strong> from the known persons list?
              This cannot be undone.
            </p>
            <div className="flex gap-3">
              <button onClick={() => handleDelete(confirmDel.id)} className="btn-danger flex-1">
                🗑 Delete
              </button>
              <button onClick={() => setConfirmDel(null)} className="btn-ghost flex-1">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Face card component ─────────────────────────────
function FaceCard({ face, onDelete, onHistory }) {
  const imgSrc = `http://localhost:8000/faces/${face.id}/image`;

  return (
    <div className="card p-4 flex flex-col items-center gap-3 hover:border-cyan-500/30 transition-all group">
      {/* Photo */}
      <div className="w-16 h-16 rounded-full overflow-hidden border-2 border-cyan-500/30 bg-guardian-900 shrink-0">
        <img
          src={imgSrc}
          alt={face.name}
          className="w-full h-full object-cover"
          onError={e => {
            e.target.style.display = "none";
            e.target.nextSibling.style.display = "flex";
          }}
        />
        <div className="w-full h-full items-center justify-center text-2xl hidden">🙂</div>
      </div>

      {/* Info */}
      <div className="text-center">
        <p className="font-semibold text-sm text-white">{face.name}</p>
        <p className="text-xs text-slate-500 mt-0.5">{face.image_count} training frames</p>
        <p className="text-xs text-slate-600">{face.created_at}</p>
      </div>

      {/* Actions */}
      <div className="flex gap-1.5 w-full">
        <button
          onClick={onHistory}
          className="flex-1 text-xs py-1 px-2 rounded-lg bg-sky-500/10 border border-sky-500/20
                     text-sky-400 hover:bg-sky-500/20 transition-colors"
        >
          📜 History
        </button>
        <button
          onClick={onDelete}
          className="text-xs py-1 px-2 rounded-lg bg-red-500/10 border border-red-500/20
                     text-red-400 hover:bg-red-500/20 transition-colors"
        >
          🗑
        </button>
      </div>
    </div>
  );
}

// ── API helpers ──────────────────────────────────────
const B = "http://localhost:8000";
const apiFaces        = ()     => fetch(`${B}/faces`).then(r => r.json());
const apiRegStart     = (name) => fetch(`${B}/faces/register/start`,
  { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }) }).then(r => r.json());
const apiRegStatus    = ()     => fetch(`${B}/faces/register/status`).then(r => r.json());
const apiRegCancel    = ()     => fetch(`${B}/faces/register/cancel`, { method: "POST" }).then(r => r.json());
const apiDeleteFace   = (id)   => fetch(`${B}/faces/${id}`, { method: "DELETE" }).then(r => r.json());
const apiFaceHistory  = (name) => fetch(`${B}/faces/${encodeURIComponent(name)}/history`).then(r => r.json());
