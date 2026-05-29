import { ArrowRight, CalendarDays, Crown, Swords } from 'lucide-react'
import { Link } from 'react-router-dom'

import { getPhaseLabel, getStatusLabel, getWinnerLabel } from '@/lib/gameDisplay'
import type { GameSummary } from '@/types/game'

export function GameSummaryCard({ game }: { game: GameSummary }) {
  const statusLabel = getStatusLabel(game.status)
  const winnerLabel = getWinnerLabel(game.winner)

  return (
    <article className="rounded-[28px] border border-white/10 bg-white/5 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.35)] transition hover:-translate-y-1 hover:border-sky-300/30 hover:bg-white/10">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-sky-200/60">AI 对局</p>
          <h3 className="mt-2 font-serif text-2xl text-white">{game.title}</h3>
          <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">{game.description}</p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <span className="rounded-full border border-fuchsia-300/30 bg-fuchsia-300/10 px-3 py-1 text-xs text-fuchsia-100">
            {winnerLabel}
          </span>
          <span className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300">{statusLabel}</span>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
          <p className="flex items-center gap-2 text-xs text-slate-400">
            <CalendarDays className="h-4 w-4 text-sky-300" />
            当前天数
          </p>
          <p className="mt-2 text-2xl text-white">第 {game.day} 天</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
          <p className="flex items-center gap-2 text-xs text-slate-400">
            <Swords className="h-4 w-4 text-rose-300" />
            当前阶段
          </p>
          <p className="mt-2 text-lg text-white">{getPhaseLabel(game.current_phase)}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
          <p className="flex items-center gap-2 text-xs text-slate-400">
            <Crown className="h-4 w-4 text-amber-300" />
            结果
          </p>
          <p className="mt-2 text-lg text-white">{winnerLabel}</p>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Link
          to={`/games/${game.id}`}
          className="inline-flex items-center gap-2 rounded-full border border-sky-300/30 bg-sky-300/10 px-5 py-2.5 text-sm text-sky-50 transition hover:border-sky-200/50 hover:bg-sky-300/20"
        >
          查看对局详情
          <ArrowRight className="h-4 w-4" />
        </Link>
        <Link
          to={`/games/${game.id}/replay`}
          className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-5 py-2.5 text-sm text-slate-200 transition hover:border-white/20 hover:bg-white/10"
        >
          查看复盘归因
        </Link>
      </div>
    </article>
  )
}
