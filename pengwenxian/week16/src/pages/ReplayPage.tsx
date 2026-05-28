import { useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ReplayInsightCard } from '@/components/ReplayInsightCard'
import { useGameStore } from '@/store/gameStore'

export default function ReplayPage() {
  const { gameId = '' } = useParams()
  const { currentReplay, replayStatus, error, fetchReplay } = useGameStore()

  useEffect(() => {
    if (gameId) {
      void fetchReplay(gameId)
    }
  }, [fetchReplay, gameId])

  if (replayStatus === 'loading') {
    return <div className="rounded-3xl border border-white/10 bg-white/5 p-8 text-slate-200">正在加载复盘报告...</div>
  }

  if (!currentReplay) {
    return (
      <div className="space-y-5">
        <div className="rounded-3xl border border-white/10 bg-white/5 p-8 text-slate-200">当前对局尚未完成，复盘会在实时对局结束后自动生成。</div>
        {error ? <div className="rounded-3xl border border-rose-300/20 bg-rose-300/10 p-5 text-sm text-rose-100">{error}</div> : null}
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <section className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-sky-200/70">Replay Report</p>
          <h1 className="mt-2 font-serif text-4xl text-white">对局复盘与归因</h1>
        </div>
        <Link
          to={`/games/${gameId}`}
          className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200 transition hover:bg-white/10"
        >
          返回对局详情
        </Link>
      </section>

      {error ? <div className="rounded-3xl border border-rose-300/20 bg-rose-300/10 p-5 text-sm text-rose-100">{error}</div> : null}

      <ReplayInsightCard replay={currentReplay} />

      <section className="grid gap-5 lg:grid-cols-[1.4fr,0.8fr]">
        <article className="rounded-[30px] border border-white/10 bg-white/5 p-6">
          <p className="text-xs uppercase tracking-[0.35em] text-sky-200/70">关键转折点</p>
          <div className="mt-5 space-y-4">
            {currentReplay.key_turning_points.map((point, index) => (
              <div key={point} className="rounded-3xl border border-white/10 bg-slate-950/50 p-5">
                <p className="text-xs text-slate-400">Turning Point {index + 1}</p>
                <p className="mt-2 text-sm leading-7 text-slate-100">{point}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="rounded-[30px] border border-white/10 bg-white/5 p-6">
          <p className="text-xs uppercase tracking-[0.35em] text-sky-200/70">基础指标</p>
          <div className="mt-5 space-y-3">
            {Object.entries(currentReplay.metrics).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/50 px-4 py-3">
                <span className="text-sm text-slate-300">{key}</span>
                <span className="text-sm text-white">{String(value)}</span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  )
}
