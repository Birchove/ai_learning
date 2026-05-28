import { Eye, Moon, SunMedium } from 'lucide-react'

import { getPhaseLabel } from '@/lib/gameDisplay'
import type { TimelineEvent } from '@/types/game'

function getPhaseIcon(phase: string) {
  if (phase.includes('night')) {
    return Moon
  }
  if (phase.includes('day')) {
    return SunMedium
  }
  return Eye
}

export function TimelinePanel({ events }: { events: TimelineEvent[] }) {
  return (
    <div className="space-y-4">
      {events.map((event) => {
        const Icon = getPhaseIcon(event.phase)
        return (
          <article key={event.id} className="rounded-3xl border border-white/10 bg-white/5 p-5">
            <div className="flex items-start gap-4">
              <div className="mt-1 flex h-12 w-12 items-center justify-center rounded-2xl border border-sky-300/20 bg-sky-300/10 text-sky-100">
                <Icon className="h-5 w-5" />
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300">
                    第 {event.day} 天
                  </span>
                  <span className="rounded-full border border-fuchsia-300/20 bg-fuchsia-300/10 px-3 py-1 text-xs text-fuchsia-100">
                    {getPhaseLabel(event.phase)}
                  </span>
                </div>
                <h3 className="mt-3 text-lg text-white">{event.title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-300">{event.summary}</p>
              </div>
            </div>
          </article>
        )
      })}
    </div>
  )
}
