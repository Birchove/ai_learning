import { Shield, Skull, Sparkles, Swords, UserRound } from 'lucide-react'

import { getCampLabel } from '@/lib/gameDisplay'
import { cn } from '@/lib/utils'
import type { PlayerSummary } from '@/types/game'

const campStyles = {
  werewolf: 'border-rose-400/30 bg-rose-400/10 text-rose-100',
  god: 'border-amber-400/30 bg-amber-400/10 text-amber-100',
  villager: 'border-cyan-400/30 bg-cyan-400/10 text-cyan-100',
}

const campIcons = {
  werewolf: Swords,
  god: Sparkles,
  villager: UserRound,
}

export function PlayerSeatCard({ player }: { player: PlayerSummary }) {
  const CampIcon = campIcons[player.camp]

  return (
    <div
      className={cn(
        'rounded-3xl border p-4 transition',
        player.alive ? 'border-white/10 bg-white/5' : 'border-white/5 bg-slate-900/70 opacity-75',
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">座位 {player.seat}</p>
          <h3 className="mt-2 text-lg text-white">{player.name}</h3>
          <p className="mt-1 text-sm text-slate-300">{player.role}</p>
        </div>
        <span
          className={cn(
            'inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs',
            campStyles[player.camp],
          )}
        >
          <CampIcon className="h-3.5 w-3.5" />
          {getCampLabel(player.camp)}
        </span>
      </div>

      <div className="mt-4 flex items-center justify-between rounded-2xl bg-slate-950/60 px-4 py-3 text-sm text-slate-200">
        <span className="inline-flex items-center gap-2">
          {player.alive ? <Shield className="h-4 w-4 text-emerald-300" /> : <Skull className="h-4 w-4 text-rose-300" />}
          {player.alive ? '存活' : '已死亡'}
        </span>
        <span>{player.tags.join(' / ') || '普通席位'}</span>
      </div>
    </div>
  )
}
