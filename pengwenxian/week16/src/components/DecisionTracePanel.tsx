import { Brain, MessageSquareQuote, Target } from 'lucide-react'

import { getCampLabel, getPhaseLabel } from '@/lib/gameDisplay'
import type { DecisionTrace } from '@/types/game'

export function DecisionTracePanel({ traces }: { traces: DecisionTrace[] }) {
  const orderedTraces = [...traces].reverse()

  return (
    <div className="space-y-4">
      {traces.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-white/15 bg-white/5 p-6 text-sm text-slate-300">
          对局刚刚开始，角色决策轨迹会随着模型推理逐步出现在这里。
        </div>
      ) : null}

      {orderedTraces.map((trace) => (
        <article key={trace.id} className="rounded-3xl border border-white/10 bg-white/5 p-5">
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full border border-sky-300/20 bg-sky-300/10 px-3 py-1 text-xs text-sky-100">
              第 {trace.day} 天
            </span>
            <span className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300">
              {getPhaseLabel(trace.phase)}
            </span>
            <span className="rounded-full border border-fuchsia-300/20 bg-fuchsia-300/10 px-3 py-1 text-xs text-fuchsia-100">
              {trace.player_name} · {trace.role} · {getCampLabel(trace.camp)}
            </span>
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
              <p className="flex items-center gap-2 text-xs text-slate-400">
                <Target className="h-4 w-4 text-amber-300" />
                动作选择
              </p>
              <p className="mt-2 text-sm leading-6 text-white">{trace.action_type}：{trace.choice}</p>
              {trace.target_seat ? <p className="mt-2 text-xs text-slate-400">目标座位：{trace.target_seat} 号</p> : null}
            </div>

            <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
              <p className="flex items-center gap-2 text-xs text-slate-400">
                <Brain className="h-4 w-4 text-sky-300" />
                决策路径
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-100">{trace.thought}</p>
              {trace.raw_reason ? <p className="mt-2 text-xs leading-5 text-slate-400">原因补充：{trace.raw_reason}</p> : null}
            </div>

            <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
              <p className="flex items-center gap-2 text-xs text-slate-400">
                <MessageSquareQuote className="h-4 w-4 text-emerald-300" />
                对外表达
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-100">{trace.public_message ?? '当前动作不产生公开发言。'}</p>
            </div>
          </div>
        </article>
      ))}
    </div>
  )
}
