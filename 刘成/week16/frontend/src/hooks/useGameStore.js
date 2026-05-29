import { create } from 'zustand';

const useGameStore = create((set, get) => ({
  // 游戏列表
  games: [],

  // 当前游戏
  currentGame: null,
  gameId: null,
  gameState: null,
  gameLog: null,
  speeches: [],

  // UI状态
  loading: false,
  error: null,
  selectedPlayerId: 1,

  // WebSocket连接
  ws: null,

  // Actions
  setGames: (games) => set({ games }),

  setCurrentGame: (game) => set({ currentGame: game }),

  setGameId: (gameId) => set({ gameId }),

  setGameState: (state) => set({ gameState: state }),

  setGameLog: (log) => set({ gameLog: log }),

  setSpeeches: (speeches) => set({ speeches }),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),

  setSelectedPlayerId: (id) => set({ selectedPlayerId: id }),

  // 重置状态
  reset: () => set({
    currentGame: null,
    gameId: null,
    gameState: null,
    gameLog: null,
    speeches: [],
    error: null,
  }),
}));

export default useGameStore;