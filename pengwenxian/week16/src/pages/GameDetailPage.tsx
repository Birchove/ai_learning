import { Square, Ban } from 'lucide-react'
import { useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'

import { DecisionTracePanel } from '@/components/DecisionTracePanel'
import { PlayerSeatCard } from '@/components/PlayerSeatCard'
import { TimelinePanel } from '@/components/TimelinePanel'
import { getPhaseLabel, getStatusLabel, getWinnerLabel } from '@/lib/gameDisplay'
import { useGameStore } from '@/store/gameStore'

export default function GameDetailPage() {
  const { gameId = '' } = useParams()
  const { currentGame, detailStatus, error, fetchGameDetail, stopGame } = useGameStore()

  useEffect(() => {
    if (gameId) {
      void fetchGameDetail(gameId)
    }
  }, [fetchGameDetail, gameId])

  useEffect(() => {
    if (!gameId || !currentGame || currentGame.id !== gameId) {
      return
    }

    if (currentGame.status === 'completed' || currentGame.status === 'failed' || currentGame.status === 'stopped') {
      return
    }

    const timer = window.setInterval(() => {
      void fetchGameDetail(gameId, true)
    }, 2000)

    return () => window.clearInterval(timer)
  }, [currentGame, fetchGameDetail, gameId])

  if (detailStatus === 'loading' || !currentGame) {
    return <div className="rounded-3xl border border-white/10 bg-white/5 p-8 text-slate-200">正在加载对局详情...</div>
  }

  const isRunning = currentGame.status === 'running' || currentGame.status === 'summarizing'

  return (
    <div className="space-y-8">
      <section className="rounded-[34px] border border-white/10 bg-white/5 p-8">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-sky-200/70">实时观战详情</p>
            <h1 className="mt-3 font-serif text-4xl text-white">{currentGame.title}</h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">{currentGame.description}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <span className="rounded-full border border-white/10 bg-slate-950/60 px-4 py-2 text-sm text-slate-200">
              当前阶段：{getPhaseLabel(currentGame.current_phase)}
            </span>
            <span className="rounded-full border border-sky-300/20 bg-sky-300/10 px-4 py-2 text-sm text-sky-100">
              对局状态：{getStatusLabel(currentGame.status)}
            </span>
            <span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-4 py-2 text-sm text-emerald-100">
              获胜阵营：{getWinnerLabel(currentGame.winner)}
            </span>
            {isRunning ? (
              <button
                type="button"
                onClick={() => void stopGame(currentGame.id)}
                className="inline-flex items-center gap-2 rounded-full border border-rose-300/30 bg-rose-300/10 px-4 py-2 text-sm text-rose-100 transition hover:bg-rose-300/20"
              >
                <Square className="h-4 w-4" />
                停止对局
              </button>
            ) : null}
            {currentGame.status === 'stopped' ? (
              <span className="inline-flex items-center gap-2 rounded-full border border-amber-300/30 bg-amber-300/10 px-4 py-2 text-sm text-amber-100">
                <Ban className="h-4 w-4" />
                本局已中止
              </span>
            ) : null}
          </div>
        </div>
        <div className="mt-5 rounded-3xl border border-white/10 bg-slate-950/50 p-5 text-sm leading-7 text-slate-200">
          实时进度：{currentGame.progress_message}
          {currentGame.error_message ? <span className="mt-2 block text-rose-300">错误信息：{currentGame.error_message}</span> : null}
        </div>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-3xl border border-white/10 bg-slate-950/50 p-5">
            <p className="text-xs text-slate-400">游戏日数</p>
            <p className="mt-2 text-3xl text-white">第 {currentGame.day} 天</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-slate-950/50 p-5">
            <p className="text-xs text-slate-400">狼人数量</p>
            <p className="mt-2 text-3xl text-white">{currentGame.camps_status.werewolf}</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-slate-950/50 p-5">
            <p className="text-xs text-slate-400">神职数量</p>
            <p className="mt-2 text-3xl text-white">{currentGame.camps_status.god}</p>
          </div>
        </div>
      </section>

      {error ? <div className="rounded-3xl border border-rose-300/20 bg-rose-300/10 p-5 text-sm text-rose-100">{error}</div> : null}

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <h2 className="font-serif text-3xl text-white">玩家席位</h2>
          {currentGame.replay_ready ? (
            <Link
              to={`/games/${currentGame.id}/replay`}
              className="rounded-full border border-sky-300/30 bg-sky-300/10 px-4 py-2 text-sm text-sky-50 transition hover:bg-sky-300/20"
            >
              查看复盘归因
            </Link>
          ) : (
            <span className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300">复盘会在对局结束后自动生成</span>
          )}
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {currentGame.players.map((player) => (
            <PlayerSeatCard key={player.id} player={player} />
          ))}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]">
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <h2 className="font-serif text-3xl text-white">左侧时间线</h2>
            <span className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300">
              实时记录公共发言与阶段事件
            </span>
          </div>
          <TimelinePanel events={currentGame.timeline} />
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <h2 className="font-serif text-3xl text-white">右侧决策路径</h2>
            <span className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300">
              实时记录每位玩家的推理与动作
            </span>
          </div>
          <div className="xl:sticky xl:top-6">
            <DecisionTracePanel traces={currentGame.decision_traces} />
          </div>
        </div>
      </section>
    </div>
  )
}
