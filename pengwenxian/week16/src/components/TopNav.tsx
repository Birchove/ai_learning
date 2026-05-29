import { Activity, MoonStar, ShieldCheck } from 'lucide-react'
import { Link, NavLink } from 'react-router-dom'

import { cn } from '@/lib/utils'

const links = [
  { to: '/', label: '总览' },
]

export function TopNav() {
  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-slate-950/75 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-3 text-slate-50">
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl border border-sky-400/30 bg-sky-500/10">
            <MoonStar className="h-5 w-5 text-sky-200" />
          </span>
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-sky-200/70">Agent Team</p>
            <p className="font-serif text-lg text-slate-50">AI 狼人杀观战台</p>
          </div>
        </Link>

        <nav className="flex items-center gap-3">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                cn(
                  'rounded-full border px-4 py-2 text-sm transition',
                  isActive
                    ? 'border-sky-300/60 bg-sky-300/10 text-sky-50'
                    : 'border-white/10 bg-white/5 text-slate-300 hover:border-white/20 hover:bg-white/10',
                )
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <span className="flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-100">
            <ShieldCheck className="h-4 w-4" />
            规则可观测
          </span>
          <span className="flex items-center gap-2 rounded-full border border-fuchsia-400/20 bg-fuchsia-400/10 px-3 py-1 text-xs text-fuchsia-100">
            <Activity className="h-4 w-4" />
            复盘归因
          </span>
        </div>
      </div>
    </header>
  )
}
