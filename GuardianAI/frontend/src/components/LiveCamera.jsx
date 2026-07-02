import { useState } from "react";
import { api } from "../api.js";

/**
 * LiveCamera — MJPEG stream + controls
 * Props: status { running, recording, person_count, fps, total_events }
 *        onStart / onStop callbacks
 */
export default function LiveCamera({ status, onStart, onStop }) {
  const [imgError, setImgError] = useState(false);

  return (
    <div className="card overflow-hidden">

      {/* Camera stream */}
      <div className="relative bg-black" style={{ aspectRatio: "16/9" }}>
        {status.running && !imgError ? (
          <img
            key={status.running}            /* remount when camera restarts */
            src={api.videoFeed}
            alt="Live detection stream"
            className="w-full h-full object-contain"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-3 text-slate-600">
            <span className="text-5xl">📹</span>
            <p className="text-sm font-medium">
              {status.running ? "Stream unavailable" : "Camera is stopped"}
            </p>
            <p className="text-xs">
              {status.running ? "Check camera connection" : "Press Start to begin monitoring"}
            </p>
          </div>
        )}

        {/* Live badge */}
        {status.running && (
          <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1
                          bg-black/60 backdrop-blur rounded-full border border-red-500/40">
            <span className="pulse-dot bg-red-500 text-red-500 w-1.5 h-1.5" />
            <span className="text-xs font-semibold text-red-400 tracking-wide">LIVE</span>
          </div>
        )}

        {/* Recording badge */}
        {status.recording && (
          <div className="absolute top-3 right-3 flex items-center gap-1.5 px-2.5 py-1
                          bg-black/60 backdrop-blur rounded-full border border-red-500/40">
            <span className="text-xs font-semibold text-red-400">⏺ REC</span>
          </div>
        )}
      </div>

      {/* Stats strip */}
      <div className="px-5 py-3 flex flex-wrap gap-x-6 gap-y-2 border-t border-slate-700/40 bg-guardian-900/40">

        <Stat icon="👤" label="Persons"   value={status.person_count ?? 0} color={status.person_count > 0 ? "text-amber-400" : "text-slate-400"} />
        <Stat icon="🎥" label="Recording" value={status.recording ? "YES" : "NO"} color={status.recording ? "text-red-400" : "text-slate-400"} />
        <Stat icon="⚡" label="FPS"       value={status.fps ?? 0} color="text-cyan-400" />
        <Stat icon="📦" label="Events"    value={status.total_events ?? 0} color="text-violet-400" />

        {/* Controls */}
        <div className="ml-auto flex gap-2">
          <button
            onClick={onStart}
            disabled={status.running}
            className={`btn-primary text-xs py-1.5 px-3 ${status.running ? "opacity-40 cursor-not-allowed" : ""}`}
          >
            ▶ Start
          </button>
          <button
            onClick={onStop}
            disabled={!status.running}
            className={`btn-danger text-xs py-1.5 px-3 ${!status.running ? "opacity-40 cursor-not-allowed" : ""}`}
          >
            ⏹ Stop
          </button>
        </div>
      </div>
    </div>
  );
}

function Stat({ icon, label, value, color }) {
  return (
    <div className="flex items-center gap-1.5 text-sm">
      <span>{icon}</span>
      <span className="text-slate-500">{label}:</span>
      <span className={`font-semibold ${color}`}>{value}</span>
    </div>
  );
}
