import { useState, useEffect } from 'react';
import useGameStore from '../hooks/useGameStore';
import { createGame, listGames, startGame, autoRunGame, getGame } from '../api/gameApi';
import PlayerCard from '../components/PlayerCard';
import ChatPanel from '../components/ChatPanel';
import GameHeader from '../components/GameHeader';

const ROLE_COLORS = {
  werewolf: 'border-red-500 bg-red-900/50',
  seer: 'border-blue-500 bg-blue-900/50',
  witch: 'border-purple-500 bg-purple-900/50',
  guard: 'border-yellow-500 bg-yellow-900/50',
  hunter: 'border-orange-500 bg-orange-900/50',
  villager: 'border-green-500 bg-green-900/50',
};

export default function GameRoom() {
  const {
    gameId,
    gameState,
    setGameState,
    speeches,
    setSpeeches,
    selectedPlayerId,
    setSelectedPlayerId,
    setError,
    setCurrentGame,
  } = useGameStore();

  const [refreshKey, setRefreshKey] = useState(0);
  const [loading, setLoading] = useState(false);
  const [autoRunning, setAutoRunning] = useState(false);

  useEffect(() => {
    if (gameId) {
      loadGameData();
      const interval = setInterval(loadGameData, 2000);
      return () => clearInterval(interval);
    }
  }, [gameId, refreshKey]);

  const loadGameData = async () => {
    try {
      const [gameData, stateRes, speechesRes] = await Promise.all([
        getGame(gameId),
        getGameState(gameId, selectedPlayerId),
        getSpeeches(gameId),
      ]);
      setCurrentGame(gameData);
      setGameState(stateRes);
      setSpeeches(speechesRes.speeches || []);

      // Check if game ended
      if (gameData.status === 'ended') {
        setAutoRunning(false);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const getGameState = async (gameId, playerId) => {
    const response = await fetch(`/api/games/${gameId}/state?player_id=${playerId}`);
    return response.json();
  };

  const getSpeeches = async (gameId) => {
    const response = await fetch(`/api/games/${gameId}/speeches`);
    return response.json();
  };

  const handleStart = async () => {
    try {
      setLoading(true);
      await startGame(gameId);
      setRefreshKey(k => k + 1);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAutoRun = async () => {
    try {
      setLoading(true);
      setAutoRunning(true);
      await autoRunGame(gameId);
      setRefreshKey(k => k + 1);
    } catch (err) {
      setError(err.message);
      setAutoRunning(false);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setRefreshKey(k => k + 1);
  };

  if (!gameState) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-white text-xl">加载中...</p>
      </div>
    );
  }

  const myRole = gameState.my_role;
  const myIsAlive = gameState.my_is_alive;
  const players = gameState.players || [];
  const gameData = useGameStore.getState().currentGame || {};

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-7xl mx-auto">
        <GameHeader
          gameState={gameState}
          winner={gameData.winner}
          onBack={() => useGameStore.getState().reset()}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 玩家列表 */}
          <div className="lg:col-span-2">
            <div className="bg-white/10 backdrop-blur rounded-xl p-4 mb-4">
              <h2 className="text-xl font-bold text-white mb-4">
                玩家列表
                <span className="ml-4 text-sm">
                  (你是: <span className="capitalize">{myRole}</span> - {myIsAlive ? '存活' : '死亡'})
                </span>
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                {players.map(player => (
                  <PlayerCard
                    key={player.player_id}
                    player={player}
                    isSelected={player.player_id === selectedPlayerId}
                    onClick={() => setSelectedPlayerId(player.player_id)}
                    roleColors={ROLE_COLORS}
                  />
                ))}
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="bg-white/10 backdrop-blur rounded-xl p-4">
              <h2 className="text-xl font-bold text-white mb-4">🎮 游戏控制</h2>
              <div className="flex flex-wrap gap-4">
                {gameState.phase === 'waiting' && (
                  <button
                    onClick={handleStart}
                    disabled={loading}
                    className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50"
                  >
                    {loading ? '处理中...' : '开始游戏'}
                  </button>
                )}

                {gameData.status === 'running' && (
                  <button
                    onClick={handleAutoRun}
                    disabled={loading || autoRunning}
                    className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
                  >
                    {autoRunning ? 'AI对战中...' : 'AI自动对战'}
                  </button>
                )}

                <button
                  onClick={handleRefresh}
                  disabled={loading}
                  className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition disabled:opacity-50"
                >
                  刷新状态
                </button>
              </div>

              {autoRunning && (
                <p className="mt-4 text-yellow-400">
                  AI正在对战中，请等待游戏结束...
                </p>
              )}

              {gameData.status === 'ended' && gameData.winner && (
                <div className="mt-4 p-4 bg-yellow-600/30 rounded-lg">
                  <h3 className="text-xl font-bold text-yellow-400">
                    游戏结束！
                  </h3>
                  <p className="text-white mt-2">
                    胜利阵营：
                    {gameData.winner === 'good' && '好人胜利 🧑‍🌾'}
                    {gameData.winner === 'werewolf' && '狼人胜利 🐺'}
                    {gameData.winner === 'neutral' && '平局'}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* 聊天/发言区域 */}
          <div className="lg:col-span-1">
            <ChatPanel speeches={speeches} players={players} />
          </div>
        </div>
      </div>
    </div>
  );
}