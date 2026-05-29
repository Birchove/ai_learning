import type { Camp, GameStatus } from '@/types/game'

export function getPhaseLabel(phase: string) {
  const labels: Record<string, string> = {
    init: '初始化',
    night: '夜晚阶段',
    day_announce: '白天公布',
    speech: '发言阶段',
    vote: '投票阶段',
    last_words: '遗言/技能',
    summarizing: '生成总结',
    game_over: '对局结束',
  }

  return labels[phase] ?? phase
}

export function getStatusLabel(status: GameStatus) {
  const labels: Record<GameStatus, string> = {
    pending: '等待中',
    running: '进行中',
    summarizing: '总结中',
    completed: '已完成',
    failed: '失败',
    stopped: '已中止',
  }

  return labels[status]
}

export function getWinnerLabel(winner: string | null) {
  const labels: Record<string, string> = {
    villager: '好人胜利',
    werewolf: '狼人胜利',
    god: '神职胜利',
  }

  if (!winner) {
    return '尚未决出'
  }

  return labels[winner] ?? winner
}

export function getCampLabel(camp: Camp) {
  const labels: Record<Camp, string> = {
    werewolf: '狼人阵营',
    god: '神职阵营',
    villager: '平民阵营',
  }

  return labels[camp]
}
