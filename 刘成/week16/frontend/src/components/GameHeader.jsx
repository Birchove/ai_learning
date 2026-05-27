import useGameStore from '../hooks/useGameStore';

export default function GameHeader({ gameState, winner, onBack }) {
  const phaseColors = {
    night: 'bg-indigo-900 text-indigo-200',
    day: 'bg-amber-500 text-amber-900',
    vote: 'bg-red-600 text-white',
    waiting: 'bg-gray-600 text-white',
  };

  const phaseText = {
    night: '🌙 夜间',
    day: '☀️ 白天发言',
    vote: '🗳️ 投票',
    waiting: '⏳ 等待开始',
  };

  return (
    <div className="bg-white/10 backdrop-blur rounded-xl p-4 mb-6">
      <div className="flex justify-between items-center">
        <button
          onClick={onBack}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
        >
          返回大厅
        </button>

        <div className="text-center">
          <h1 className="text-2xl font-bold text-white">
            第 {gameState.day || 1} 天
          </h1>
          <div className={`mt-2 px-4 py-1 rounded-full font-bold ${phaseColors[gameState.phase] || phaseColors.waiting}`}>
            {phaseText[gameState.phase] || phaseText.waiting}
          </div>
          {winner && (
            <div className="mt-2 text-yellow-400 font-bold">
              胜负已分: {winner === 'good' ? '好人胜' : winner === 'werewolf' ? '狼人胜' : winner}
            </div>
          )}
        </div>

        <div className="text-white">
          <div>游戏ID: {gameState.game_id}</div>
        </div>
      </div>
    </div>
  );
}