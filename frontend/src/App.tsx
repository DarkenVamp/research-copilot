import { Route, Routes } from "react-router-dom";
import { SessionList } from "./components/SessionList";
import { HomePage } from "./pages/HomePage";
import { SessionDetailPage } from "./pages/SessionDetailPage";

export default function App() {
  return (
    <div className="flex h-screen flex-col md:flex-row">
      <aside className="max-h-[42vh] overflow-y-auto border-b border-slate-200 bg-white md:max-h-none md:h-screen md:w-72 md:flex-shrink-0 md:overflow-hidden md:border-b-0 md:border-r">
        <SessionList />
      </aside>
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/sessions/:id" element={<SessionDetailPage />} />
        </Routes>
      </main>
    </div>
  );
}
