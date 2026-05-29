import { useEffect } from 'react'
import { BrainCircuit, Drama, FlaskConical, Plus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { GameSummaryCard } from '@/components/GameSummaryCard'
import { useGameStore } from '@/store/gameStore'

const featureCards = [
  {
    title: '规则驱动引擎',
    description: '基于 9 人标准局样例，对阶段推进、胜负判定和技能结算进行结构化编排。',
    icon: Drama,
  },
  {
    title: 'Agent 协作视角',
    description: '展示狼人协作、神职信息链和公共投票节奏，便于后续接入多模型策略。',
    icon: BrainCircuit,
  },
  {
    title: '复盘归因系统',
    description: '输出关键转折点、胜负原因和协作观察，为后续评测与排行榜做准备。',
    icon: FlaskConical,
  },
]

export default function Home() {
  const navigate = useNavigate()
  const { games, listStatus, error, fetchGames, createAIGame } = useGameStore()

  useEffect(() => {
    void fetchGames()
  }, [fetchGames])

  useEffect(() => {
    const timer = window.setInterval(() => {
      void fetchGames(true)
    }, 4000)

    return () => window.clearInterval(timer)
  }, [fetchGames])

  const handleCreateAIGame = async () => {
    const createdId = await createAIGame()
    if (createdId) {
      navigate(`/games/${createdId}`)
    }
  }

  return (
    <div className="space-y-10">
      <section className="overflow-hidden rounded-[36px] border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.18),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(192,38,211,0.18),_transparent_22%),linear-gradient(135deg,rgba(15,23,42,0.98),rgba(30,41,59,0.88))] p-8 shadow-[0_30px_120px_rgba(14,165,233,0.12)] lg:p-12">
        <div className="max-w-3xl">
          <p className="text-xs uppercase tracking-[0.45em] text-sky-200/70">AI Werewolf Agent Team</p>
          <h1 className="mt-4 font-serif text-4xl leading-tight text-white lg:text-6xl">
            多智能体狼人杀观战台与复盘实验场
          </h1>
          <p className="mt-6 max-w-2xl text-sm leading-7 text-slate-300 lg:text-base">
            当前版本支持以千问模型驱动 9 人标准局，让不同角色基于各自身份与可见信息自主决策，并在赛后自动生成 AI 复盘总结。
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <button
              type="button"
              onClick={() => void handleCreateAIGame()}
              className="inline-flex items-center gap-2 rounded-full border border-sky-300/30 bg-sky-300/10 px-5 py-3 text-sm text-sky-50 transition hover:border-sky-200/50 hover:bg-sky-300/20"
            >
              <Plus className="h-4 w-4" />
              {listStatus === 'loading' ? '正在启动 AI 对局...' : '启动 AI 对局'}
            </button>
            <div className="rounded-full border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-200">
              当前状态：{listStatus === 'loading' ? '模型决策中' : '可发起对局'}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-3">
        {featureCards.map((item) => (
          <article key={item.title} className="rounded-[28px] border border-white/10 bg-white/5 p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-sky-100">
              <item.icon className="h-5 w-5" />
            </div>
            <h2 className="mt-4 font-serif text-2xl text-white">{item.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-300">{item.description}</p>
          </article>
        ))}
      </section>

      <section className="space-y-5">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-sky-200/70">观战入口</p>
            <h2 className="mt-2 font-serif text-3xl text-white">AI 对局列表</h2>
          </div>
          <span className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300">
            共 {games.length} 局
          </span>
        </div>

        {error ? <div className="rounded-3xl border border-rose-300/20 bg-rose-300/10 p-5 text-sm text-rose-100">{error}</div> : null}

        {games.length === 0 ? (
          <div className="rounded-[28px] border border-dashed border-white/15 bg-white/5 p-8 text-center text-sm leading-7 text-slate-300">
            当前还没有生成过 AI 对局。点击上方按钮后，系统会调用千问模型驱动各角色完成整局博弈，并自动生成复盘。
          </div>
        ) : (
          <div className="space-y-5">
            {games.map((game) => (
              <GameSummaryCard key={game.id} game={game} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
