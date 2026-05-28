import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

import App from '@/App'

const { mockGames } = vi.hoisted(() => ({
  mockGames: [
    {
      id: 'game_ai_001',
      title: 'AI 对局 001',
      description: '测试用样例',
      current_phase: 'game_over',
      day: 3,
      winner: 'villager',
      status: 'completed',
    },
  ],
}))

vi.mock('@/utils/api', () => ({
  api: {
    listGames: vi.fn().mockResolvedValue(mockGames),
    createAIGame: vi.fn().mockResolvedValue(mockGames[0]),
    getGame: vi.fn(),
    getReplay: vi.fn(),
  },
}))

describe('App', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders home page and loaded game cards', async () => {
    render(<App />)

    expect(screen.getByText('多智能体狼人杀观战台与复盘实验场')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getAllByText('AI 对局 001').length).toBeGreaterThan(0)
    })
  })
})
