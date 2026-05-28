import { create } from 'zustand'

import { api } from '@/utils/api'
import type { GameDetail, GameSummary, ReplayReport } from '@/types/game'

type AsyncStatus = 'idle' | 'loading' | 'success' | 'error'

interface GameStore {
  games: GameSummary[]
  currentGame: GameDetail | null
  currentReplay: ReplayReport | null
  listStatus: AsyncStatus
  detailStatus: AsyncStatus
  replayStatus: AsyncStatus
  error: string | null
  fetchGames: (silent?: boolean) => Promise<void>
  createAIGame: () => Promise<string | null>
  stopGame: (gameId: string) => Promise<void>
  fetchGameDetail: (gameId: string, silent?: boolean) => Promise<void>
  fetchReplay: (gameId: string) => Promise<void>
}

export const useGameStore = create<GameStore>((set) => ({
  games: [],
  currentGame: null,
  currentReplay: null,
  listStatus: 'idle',
  detailStatus: 'idle',
  replayStatus: 'idle',
  error: null,

  fetchGames: async (silent = false) => {
    if (!silent) {
      set({ listStatus: 'loading', error: null })
    }
    try {
      const games = await api.listGames()
      set({ games, listStatus: 'success' })
    } catch (error) {
      set({ listStatus: 'error', error: error instanceof Error ? error.message : '获取对局失败' })
    }
  },

  createAIGame: async () => {
    set({ error: null, listStatus: 'loading' })
    try {
      const game = await api.createAIGame()
      const games = await api.listGames()
      set({ games, listStatus: 'success' })
      return game.id
    } catch (error) {
      set({ listStatus: 'error', error: error instanceof Error ? error.message : '启动 AI 对局失败' })
      return null
    }
  },

  stopGame: async (gameId: string) => {
    set({ error: null })
    try {
      const currentGame = await api.stopGame(gameId)
      const games = await api.listGames()
      set({ currentGame, games, detailStatus: 'success', listStatus: 'success' })
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '中止对局失败' })
    }
  },

  fetchGameDetail: async (gameId: string, silent = false) => {
    if (!silent) {
      set({ detailStatus: 'loading', error: null })
    }
    try {
      const currentGame = await api.getGame(gameId)
      set({ currentGame, detailStatus: 'success' })
    } catch (error) {
      set({ detailStatus: 'error', error: error instanceof Error ? error.message : '获取对局详情失败' })
    }
  },

  fetchReplay: async (gameId: string) => {
    set({ replayStatus: 'loading', error: null })
    try {
      const currentReplay = await api.getReplay(gameId)
      set({ currentReplay, replayStatus: 'success' })
    } catch (error) {
      set({ replayStatus: 'error', error: error instanceof Error ? error.message : '获取复盘失败' })
    }
  },
}))
