import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { TopNav } from '@/components/TopNav'
import GameDetailPage from '@/pages/GameDetailPage'
import Home from '@/pages/Home'
import ReplayPage from '@/pages/ReplayPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <div className="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.18),_transparent_24%),radial-gradient(circle_at_top_right,_rgba(192,38,211,0.14),_transparent_26%),linear-gradient(180deg,_#020617,_#0f172a_48%,_#111827)]" />
        <TopNav />
        <main className="mx-auto max-w-7xl px-6 py-10">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/games/:gameId" element={<GameDetailPage />} />
            <Route path="/games/:gameId/replay" element={<ReplayPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
