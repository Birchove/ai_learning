export default function PlayerCard({ player, isSelected, onClick, roleColors }) {
  const role = player.role || 'unknown';
  const borderClass = roleColors[role] || 'border-gray-500';

  return (
    <div
      onClick={onClick}
      className={`
        p-3 rounded-lg border-2 cursor-pointer transition-all
        ${isSelected ? 'ring-2 ring-yellow-400' : ''}
        ${player.is_alive ? 'bg-white/90' : 'bg-gray-800/50 opacity-60'}
        ${borderClass}
      `}
    >
      <div className="text-center">
        <div className="text-lg font-bold text-gray-800">
          {player.name}
        </div>
        <div className="text-sm text-gray-600">
          ID: {player.player_id}
        </div>
        {!player.is_alive && (
          <div className="text-xs text-red-500 mt-1">死亡</div>
        )}
        {player.is_alive === false && player.role && (
          <div className="text-xs text-red-600 mt-1 capitalize">身份: {role}</div>
        )}
      </div>
    </div>
  );
}