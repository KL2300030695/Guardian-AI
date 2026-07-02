import { Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar.jsx";
import Navbar  from "./components/Navbar.jsx";
import Dashboard  from "./pages/Dashboard.jsx";
import History    from "./pages/History.jsx";
import Analytics  from "./pages/Analytics.jsx";
import Settings   from "./pages/Settings.jsx";
import Faces      from "./pages/Faces.jsx";

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar />
        <main className="flex-1 overflow-y-auto p-6">
          <Routes>
            <Route path="/"          element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/history"   element={<History />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/faces"     element={<Faces />} />
            <Route path="/settings"  element={<Settings />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
