import { ArrowUpRight, MessagesSquare, Target } from 'lucide-react'

import type { ReplayReport } from '@/types/game'

export function ReplayInsightCard({ replay }: { replay: ReplayReport }) {
  return (
    <div className="space-y-6">
      <section className="rounded-[30px] border border-white/10 bg-white/5 p-6">
        <p className="text-xs uppercase tracking-[0.35em] text-sky-200/70">复盘摘要</p>
        <h2 className="mt-3 font-serif text-3xl text-white">关键归因</h2>
        <p className="mt-4 text-sm leading-7 text-slate-300">{replay.summary}</p>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <article className="rounded-3xl border border-emerald-300/20 bg-emerald-300/10 p-5">
          <p className="flex items-center gap-2 text-sm text-emerald-100">
            <Target className="h-4 w-4" />
            胜利原因
          </p>
          <p className="mt-3 text-sm leading-6 text-emerald-50">{replay.attribution.winning_reason}</p>
        </article>
        <article className="rounded-3xl border border-rose-300/20 bg-rose-300/10 p-5">
          <p className="flex items-center gap-2 text-sm text-rose-100">
            <ArrowUpRight className="h-4 w-4" />
            失败原因
          </p>
          <p className="mt-3 text-sm leading-6 text-rose-50">{replay.attribution.losing_reason}</p>
        </article>
        <article className="rounded-3xl border border-sky-300/20 bg-sky-300/10 p-5">
          <p className="flex items-center gap-2 text-sm text-sky-100">
            <MessagesSquare className="h-4 w-4" />
            协作观察
          </p>
          <p className="mt-3 text-sm leading-6 text-sky-50">{replay.attribution.collaboration_note}</p>
        </article>
      </section>
    </div>
  )
}
