export default function ChatPanel({ speeches, players }) {
  const getPlayerName = (playerId) => {
    const player = players.find(p => p.player_id === playerId);
    return player?.name || `Player ${playerId}`;
  };

  return (
    <div className="bg-white/10 backdrop-blur rounded-xl p-4 h-[600px] flex flex-col">
      <h2 className="text-xl font-bold text-white mb-4">💬 发言记录</h2>

      <div className="flex-1 overflow-y-auto space-y-3">
        {speeches.length === 0 ? (
          <p className="text-gray-400 text-center py-8">暂无发言记录</p>
        ) : (
          speeches.map((speech, index) => (
            <div key={index} className="bg-white/5 rounded-lg p-3">
              <div className="flex justify-between items-start mb-1">
                <span className="font-bold text-white">
                  {getPlayerName(speech.player_id)}
                </span>
                <span className="text-xs text-gray-400">
                  第{speech.day}天
                </span>
              </div>
              <p className="text-gray-200 text-sm">{speech.content}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}