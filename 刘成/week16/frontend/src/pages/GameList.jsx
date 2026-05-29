import { useState } from 'react';
import useGameStore from '../hooks/useGameStore';
import { createGame, listGames } from '../api/gameApi';

const ROLES = ['werewolf', 'seer', 'witch', 'guard', 'hunter', 'villager'];

export default function GameList() {
  const { games, setGames, setCurrentGame, setGameId } = useGameStore();
  const [showCreate, setShowCreate] = useState(false);
  const [config, setConfig] = useState({
    name: '新游戏',
    werewolf: 2,
    seer: 1,
    witch: 1,
    guard: 1,
    hunter: 1,
    villager: 4,
    ai_count: 10,
  });

  const loadGames = async () => {
    try {
      const data = await listGames();
      setGames(data.games || []);
    } catch (err) {
      console.error('Failed to load games:', err);
    }
  };

  const handleCreate = async () => {
    try {
      const playerCount = {};
      ROLES.forEach(role => {
        if (config[role] > 0) playerCount[role] = config[role];
      });

      const result = await createGame({
        name: config.name,
        player_count: playerCount,
        ai_count: config.ai_count,
        human_count: 0,
      });

      setCurrentGame(result);
      setGameId(result.game_id);
      setShowCreate(false);
      loadGames();
    } catch (err) {
      console.error('Failed to create game:', err);
    }
  };

  const handleRoleChange = (role, value) => {
    setConfig(prev => ({ ...prev, [role]: parseInt(value) || 0 }));
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-8 text-center">
          🐺 狼人杀多Agent对战系统
        </h1>

        <div className="flex gap-4 mb-8 justify-center">
          <button
            onClick={loadGames}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
          >
            刷新游戏列表
          </button>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
          >
            {showCreate ? '取消创建' : '创建新游戏'}
          </button>
        </div>

        {showCreate && (
          <div className="bg-white/10 backdrop-blur rounded-xl p-6 mb-8">
            <h2 className="text-xl font-bold text-white mb-4">游戏配置</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <label className="block text-gray-300 mb-1">游戏名称</label>
                <input
                  type="text"
                  value={config.name}
                  onChange={e => setConfig(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 rounded bg-white/20 text-white border border-white/30"
                />
              </div>
              <div>
                <label className="block text-gray-300 mb-1">AI玩家数</label>
                <input
                  type="number"
                  value={config.ai_count}
                  onChange={e => setConfig(prev => ({ ...prev, ai_count: parseInt(e.target.value) || 0 }))}
                  className="w-full px-3 py-2 rounded bg-white/20 text-white border border-white/30"
                />
              </div>
            </div>

            <h3 className="text-lg font-semibold text-white mb-3">角色配置</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {ROLES.map(role => (
                <div key={role}>
                  <label className="block text-gray-300 mb-1 capitalize">{role}</label>
                  <input
                    type="number"
                    min="0"
                    value={config[role]}
                    onChange={e => handleRoleChange(role, e.target.value)}
                    className="w-full px-3 py-2 rounded bg-white/20 text-white border border-white/30"
                  />
                </div>
              ))}
            </div>

            <button
              onClick={handleCreate}
              className="mt-6 px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-bold"
            >
              创建游戏
            </button>
          </div>
        )}

        <div className="grid gap-4">
          {games.map(game => (
            <div key={game.game_id} className="bg-white/10 backdrop-blur rounded-xl p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-xl font-bold text-white">{game.name}</h3>
                  <p className="text-gray-300">
                    ID: {game.game_id} | 状态: {game.status} | 第{game.day}天 | {game.phase}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setGameId(game.game_id);
                    setCurrentGame(game);
                  }}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                >
                  进入游戏
                </button>
              </div>
            </div>
          ))}

          {games.length === 0 && (
            <p className="text-center text-gray-300 py-8">暂无游戏，点击创建新游戏开始</p>
          )}
        </div>
      </div>
    </div>
  );
}