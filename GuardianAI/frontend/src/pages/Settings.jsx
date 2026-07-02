import { useState, useEffect } from "react";
import { api } from "../api.js";

const LS_KEY = "guardian_settings";

const DEFAULTS = {
  camera_url:     "http://10.123.34.14:8080/video",
  confidence:     0.5,
  record_timeout: 10,
  bot_token:      "",
  chat_id:        "",
};

export default function Settings() {
  const [form,    setForm]    = useState(DEFAULTS);
  const [saved,   setSaved]   = useState(false);
  const [camStat, setCamStat] = useState(null);
  const [restarting, setRestarting] = useState(false);

  // Load from server defaults + localStorage overrides
  useEffect(() => {
    const load = async () => {
      try {
        const srv = await api.settings();
        const ls  = JSON.parse(localStorage.getItem(LS_KEY) || "{}");
        setForm({ ...DEFAULTS, ...srv, ...ls });
      } catch {
        const ls = JSON.parse(localStorage.getItem(LS_KEY) || "{}");
        setForm({ ...DEFAULTS, ...ls });
      }
    };
    load();
    api.cameraStatus().then(setCamStat).catch(() => {});
  }, []);

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSave = () => {
    localStorage.setItem(LS_KEY, JSON.stringify(form));
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const handleRestart = async () => {
    setRestarting(true);
    try {
      await api.cameraStop();
      await new Promise(r => setTimeout(r, 1000));
      await api.cameraStart();
      const st = await api.cameraStatus();
      setCamStat(st);
    } catch {}
    setRestarting(false);
  };

  return (
    <div className="page-enter max-w-2xl space-y-6">

      {/* Camera config */}
      <Section title="📹 Camera" subtitle="Connection and detection settings">
        <Field label="Camera URL" hint="IP Webcam or RTSP stream address">
          <input value={form.camera_url} onChange={set("camera_url")} className="inp" placeholder="http://..." />
        </Field>

        <Field label={`Confidence Threshold — ${Math.round(form.confidence * 100)}%`}
               hint="Minimum confidence to count a person (0 = anything, 1 = very strict)">
          <input
            type="range" min="0.1" max="0.95" step="0.05"
            value={form.confidence} onChange={set("confidence")}
            className="w-full accent-cyan-500 cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-600 mt-0.5">
            <span>Loose (10%)</span><span>Strict (95%)</span>
          </div>
        </Field>

        <Field label="Recording Timeout (seconds)"
               hint="Seconds of no detection before recording stops">
          <input type="number" min="3" max="120" value={form.record_timeout}
                 onChange={set("record_timeout")} className="inp" />
        </Field>
      </Section>

      {/* Telegram */}
      <Section title="📱 Telegram" subtitle="Alert notification settings">
        <Field label="Bot Token" hint="From @BotFather — keep this secret!">
          <input type="password" value={form.bot_token} onChange={set("bot_token")}
                 className="inp font-mono" placeholder="123456:ABC-..." />
        </Field>
        <Field label="Chat ID" hint="Your Telegram user or group ID">
          <input value={form.chat_id} onChange={set("chat_id")}
                 className="inp font-mono" placeholder="1234567890" />
        </Field>
      </Section>

      {/* System */}
      <Section title="⚙️ System" subtitle="Engine control">
        <div className="flex items-center justify-between p-4 bg-guardian-900/60 rounded-xl border border-slate-700/40">
          <div>
            <p className="text-sm font-medium text-slate-300">Camera Engine</p>
            <p className="text-xs text-slate-600 mt-0.5">
              {camStat
                ? (camStat.running ? `Running · FPS ${camStat.fps}` : "Stopped")
                : "Status unknown"}
            </p>
          </div>
          <button
            onClick={handleRestart}
            disabled={restarting}
            className={`btn-danger text-xs py-2 px-4 ${restarting ? "opacity-60 cursor-wait" : ""}`}
          >
            {restarting ? "Restarting…" : "🔄 Restart AI"}
          </button>
        </div>
      </Section>

      {/* Save */}
      <div className="flex items-center gap-3 pt-2">
        <button onClick={handleSave} className="btn-primary">
          💾 Save Settings
        </button>
        {saved && (
          <span className="text-xs text-emerald-400 badge-green">
            ✅ Saved to local storage
          </span>
        )}
      </div>

      {/* Note */}
      <div className="text-xs text-slate-600 border border-slate-700/30 rounded-lg p-3 bg-guardian-900/40">
        <strong className="text-slate-500">Note:</strong> Settings are stored in your browser.
        Camera URL, confidence, and timeout require editing <code className="font-mono">config.py</code> and
        restarting the server to take full effect.
      </div>
    </div>
  );
}

function Section({ title, subtitle, children }) {
  return (
    <div className="card p-5 space-y-4">
      <div className="border-b border-slate-700/40 pb-3">
        <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
        {subtitle && <p className="text-xs text-slate-600 mt-0.5">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

function Field({ label, hint, children }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-slate-400">{label}</label>
      {children}
      {hint && <p className="text-xs text-slate-600">{hint}</p>}
    </div>
  );
}
