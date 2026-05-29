import type { GameDetail, GameSummary, ReplayReport } from '@/types/game'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...init,
  })

  if (!response.ok) {
    let message = `请求失败: ${response.status}`
    try {
      const payload = (await response.json()) as { detail?: string }
      if (payload.detail) {
        message = payload.detail
      }
    } catch {
      // Ignore JSON parse failures and keep fallback message.
    }
    throw new Error(message)
  }

  return response.json() as Promise<T>
}

export const api = {
  listGames: () => request<GameSummary[]>('/api/games'),
  createAIGame: () => request<GameSummary>('/api/games/ai', { method: 'POST' }),
  getGame: (gameId: string) => request<GameDetail>(`/api/games/${gameId}`),
  stopGame: (gameId: string) => request<GameDetail>(`/api/games/${gameId}/stop`, { method: 'POST' }),
  getReplay: (gameId: string) => request<ReplayReport>(`/api/games/${gameId}/replay`),
}
