// Central API client — all calls go to FastAPI on port 8000
const BASE = "http://localhost:8000";

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

async function post(path, body) {
  const opts = { method: "POST" };
  if (body) {
    opts.headers = { "Content-Type": "application/json" };
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
  return res.json();
}

async function put(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`PUT ${path} → ${res.status}`);
  return res.json();
}

async function del(path) {
  const res = await fetch(`${BASE}${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`DELETE ${path} → ${res.status}`);
  return res.json();
}

export const api = {
  // Health
  health:            () => get("/health"),

  // Multi-Camera Management
  cameras:           () => get("/cameras"),
  addCamera:         (cam) => post("/cameras", cam),
  updateCamera:      (id, cam) => put(`/cameras/${id}`, cam),
  deleteCamera:      (id) => del(`/cameras/${id}`),
  cameraStart:       (id = 1) => post(`/cameras/${id}/start`),
  cameraStop:        (id = 1) => post(`/cameras/${id}/stop`),
  cameraStatus:      (id = 1) => get(`/cameras/${id}/status`),

  // Events
  events:            () => get("/events"),
  eventsRecent:      () => get("/events/recent"),
  eventsStats:       (camId) => get(camId ? `/events/stats?camera_id=${camId}` : "/events/stats"),
  eventsByDate:      (d) => get(`/events/date/${d}`),
  eventsByCamera:    (camId) => get(`/events/camera/${camId}`),

  // Analytics
  analyticsDaily:            (camId) => get(camId ? `/events/analytics/daily?camera_id=${camId}` : "/events/analytics/daily"),
  analyticsHourly:           (camId) => get(camId ? `/events/analytics/hourly?camera_id=${camId}` : "/events/analytics/hourly"),
  analyticsCameras:          () => get("/events/analytics/cameras"),
  analyticsOverview:         (camId, days) => {
    const q = new URLSearchParams();
    if (camId) q.append("camera_id", camId);
    if (days) q.append("days", days);
    const str = q.toString();
    return get(`/events/analytics/overview${str ? '?' + str : ''}`);
  },
  analyticsTrends:           (camId, days = 30) => {
    const q = new URLSearchParams({ days });
    if (camId) q.append("camera_id", camId);
    return get(`/events/analytics/trends?${q.toString()}`);
  },
  analyticsHourlyBreakdown:  (camId) => get(camId ? `/events/analytics/hourly-breakdown?camera_id=${camId}` : "/events/analytics/hourly-breakdown"),
  analyticsCamerasComparison:() => get("/events/analytics/cameras-comparison"),
  analyticsIdentities:       () => get("/events/analytics/identities"),

  // Settings
  settings:          () => get("/settings"),

  // Media URLs
  screenshotUrl:     (p) => p ? `${BASE}/${p}` : null,
  recordingUrl:      (p) => p ? `${BASE}/${p}` : null,
  videoFeed:         `${BASE}/video_feed`,
  videoFeedById:     (id) => `${BASE}/video_feed/${id}`,
};
