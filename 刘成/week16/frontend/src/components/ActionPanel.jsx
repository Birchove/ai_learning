import { useState } from 'react';

export default function ActionPanel({
  actionType,
  setActionType,
  content,
  setContent,
  targetId,
  setTargetId,
  players,
  onSubmit,
  disabled,
}) {
  const alivePlayers = players.filter(p => p.is_alive);

  return (
    <div className="bg-white/10 backdrop-blur rounded-xl p-4">
      <h2 className="text-xl font-bold text-white mb-4">🎮 行动面板</h2>

      <div className="space-y-4">
        {/* 行动类型选择 */}
        <div>
          <label className="block text-gray-300 mb-2">行动类型</label>
          <div className="flex gap-2">
            <button
              onClick={() => setActionType('speak')}
              className={`px-4 py-2 rounded-lg transition ${
                actionType === 'speak'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              发言
            </button>
            <button
              onClick={() => setActionType('vote')}
              className={`px-4 py-2 rounded-lg transition ${
                actionType === 'vote'
                  ? 'bg-red-600 text-white'
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              投票
            </button>
            <button
              onClick={() => setActionType('kill')}
              className={`px-4 py-2 rounded-lg transition ${
                actionType === 'kill'
                  ? 'bg-red-800 text-white'
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              击杀(狼人)
            </button>
            <button
              onClick={() => setActionType('check')}
              className={`px-4 py-2 rounded-lg transition ${
                actionType === 'check'
                  ? 'bg-blue-800 text-white'
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              查验(预言家)
            </button>
          </div>
        </div>

        {/* 目标选择 */}
        <div>
          <label className="block text-gray-300 mb-2">目标玩家</label>
          <select
            value={targetId || ''}
            onChange={e => setTargetId(parseInt(e.target.value) || null)}
            className="w-full px-3 py-2 rounded bg-white/20 text-white border border-white/30"
          >
            <option value="">请选择目标</option>
            {alivePlayers.map(p => (
              <option key={p.player_id} value={p.player_id}>
                {p.name} (ID: {p.player_id})
              </option>
            ))}
          </select>
        </div>

        {/* 发言内容 */}
        {actionType === 'speak' && (
          <div>
            <label className="block text-gray-300 mb-2">发言内容</label>
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder="输入你的发言..."
              className="w-full px-3 py-2 rounded bg-white/20 text-white border border-white/30 h-24 resize-none"
            />
          </div>
        )}

        {/* 提交按钮 */}
        <button
          onClick={onSubmit}
          disabled={disabled}
          className={`w-full py-3 rounded-lg font-bold transition ${
            disabled
              ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
              : 'bg-green-600 text-white hover:bg-green-700'
          }`}
        >
          提交行动
        </button>
      </div>
    </div>
  );
}